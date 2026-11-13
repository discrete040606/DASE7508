from __future__ import annotations

import contextlib
import fcntl
import json
import os
import time
import uuid
from pathlib import Path

from .models import TOOLS, append_jsonl, write_json


class BudgetStop(RuntimeError):
    pass


class FatalAPIError(RuntimeError):
    pass


def load_api_key(root: Path):
    from dotenv import dotenv_values
    return (os.environ.get("DEEPSEEK_API_KEY") or
            dotenv_values(root / ".env", interpolate=False).get("DEEPSEEK_API_KEY") or "").strip()


@contextlib.contextmanager
def exclusive(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("Another experiment/demo request is active") from None
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


class Budget:
    def __init__(self, root: Path, config):
        self.path = root / ".local" / "runtime" / "budget.json"
        self.lock = root / ".local" / "runtime" / "budget.lock"
        self.config = config

    def read(self):
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {"spent_upper_usd": 0.0, "measured_peak_estimate_usd": 0.0, "reservations": {}}

    def reserve(self, input_bytes, output_tokens):
        # UTF-8 bytes plus protocol overhead conservatively bound tokenised input.
        estimate = ((input_bytes + 8192) * self.config.input_usd_per_million
                    + output_tokens * self.config.output_usd_per_million) / 1e6
        with exclusive(self.lock):
            state = self.read()
            if state["spent_upper_usd"] + estimate > self.config.budget_usd:
                raise BudgetStop("API budget exhausted; no request was sent")
            rid = uuid.uuid4().hex
            state["spent_upper_usd"] += estimate
            state["reservations"][rid] = estimate
            write_json(self.path, state)
        return rid

    def settle(self, rid, usage):
        with exclusive(self.lock):
            state = self.read()
            reserved = state["reservations"].pop(rid)
            cost = None
            if usage and "prompt_tokens" in usage and "completion_tokens" in usage:
                cost = (usage["prompt_tokens"] * self.config.input_usd_per_million
                        + usage["completion_tokens"] * self.config.output_usd_per_million) / 1e6
                state["spent_upper_usd"] += cost - reserved
                state["measured_peak_estimate_usd"] += cost
            # Unknown usage remains charged at the reservation; never silently refunded.
            write_json(self.path, state)
            return reserved if cost is None else cost


class DeepSeek:
    simulated = False

    def __init__(self, root: Path, config, journal: Path):
        from openai import OpenAI
        key = load_api_key(root)
        if not key:
            raise ValueError("Set DEEPSEEK_API_KEY locally before a live run")
        if config.model != "deepseek-flash":
            raise ValueError("Only the priced, frozen deepseek-flash configuration is supported")
        self.config, self.journal = config, journal
        self.budget = Budget(root, config)
        self.client = OpenAI(api_key=key, base_url=config.base_url,
                             timeout=config.timeout_seconds, max_retries=0)
        self.cost = 0.0
        self.request_count = 0
        self.response_model = None
        self.context = {}

    def complete(self, messages, planning):
        from openai import APIConnectionError, APIStatusError, APITimeoutError
        cap = self.config.planning_tokens if planning else self.config.answer_tokens
        payload = {"model": self.config.model, "messages": messages, "stream": False,
                   "temperature": self.config.temperature, "max_tokens": cap,
                   "extra_body": {"thinking": {"type": "disabled"}}}
        if planning:
            payload.update(tools=TOOLS, tool_choice={"type": "function", "function": {"name": "search_memory"}})
        else:
            payload.update(tool_choice="none")
        size = len(json.dumps(payload, ensure_ascii=False).encode())
        if size > 65536:
            raise ValueError("Conversation exceeds the frozen 64 KiB request limit")
        for attempt in range(self.config.max_retries + 1):
            rid = self.budget.reserve(size, cap)
            append_jsonl(self.journal, {**self.context, "event": "request", "request_id": rid, "stage": "plan" if planning else "answer",
                                         "attempt": attempt, "reserved_usd": self.budget.read()["reservations"][rid], "payload": payload})
            start = time.perf_counter()
            self.request_count += 1
            try:
                result = self.client.chat.completions.create(**payload).model_dump()
            except Exception as exc:
                charge = self.budget.settle(rid, None)
                self.cost += charge
                status = getattr(exc, "status_code", None)
                retryable = isinstance(exc, (APIConnectionError, APITimeoutError)) or (
                    isinstance(exc, APIStatusError) and (status in (408, 409, 429) or status >= 500))
                append_jsonl(self.journal, {**self.context, "event": "request_error", "request_id": rid, "cost_upper_usd": charge,
                                             "error_type": type(exc).__name__, "status": status,
                                             "retryable": retryable, "elapsed_ms": (time.perf_counter() - start) * 1000})
                if retryable and attempt < self.config.max_retries:
                    time.sleep(2 ** (attempt + 1))
                    continue
                if not retryable:
                    raise FatalAPIError(f"DeepSeek request rejected ({status or type(exc).__name__}); run stopped") from None
                raise RuntimeError("DeepSeek transient request retries exhausted") from None
            charge = self.budget.settle(rid, result.get("usage"))
            self.cost += charge
            append_jsonl(self.journal, {**self.context, "event": "response", "request_id": rid, "cost_upper_usd": charge,
                                         "elapsed_ms": (time.perf_counter() - start) * 1000, "response": result})
            model = result.get("model")
            if self.response_model is not None and model != self.response_model:
                raise FatalAPIError("Response model changed during run; no automatic fallback")
            self.response_model = model
            return result


class MockProvider:
    """Protocol fixture, deliberately echoing retrieved records. NOT research evidence."""
    simulated = True
    cost = 0.0
    request_count = 0
    response_model = "OFFLINE_PROTOCOL_FIXTURE"

    def complete(self, messages, planning):
        self.request_count += 1
        if planning:
            query = next(m["content"] for m in reversed(messages) if m["role"] == "user")
            message = {"role": "assistant", "content": None, "tool_calls": [
                {"id": "fixture_call", "type": "function", "function": {
                    "name": "search_memory", "arguments": json.dumps({"query": query})}}]}
            reason = "tool_calls"
        else:
            records = json.loads(messages[-1]["content"])["records"]
            message = {"role": "assistant", "content": "\n".join(r["content"] for r in records) or "No relevant memories found."}
            reason = "stop"
        return {"model": self.response_model, "choices": [{"message": message, "finish_reason": reason}]}
