"""执行一条用例：模型提出检索 → 程序查库 → 模型回答 → 保存证据。"""

import json
import time

from .models import SYSTEM_PROMPT, SearchArgs, append_jsonl
from .provider import BudgetStop, FatalAPIError


class Agent:
    def __init__(self, retrieval, provider, checkpoint=None):
        self.retrieval, self.provider, self.checkpoint = retrieval, provider, checkpoint

    def run_case(
        self, case, session, config, filter_enabled=False, trial_id="demo", history=None, attempt=1
    ):
        start, cost_before = time.perf_counter(), self.provider.cost
        self.cost_before = cost_before
        self.provider.context = {"trial_id": trial_id, "attempt_number": attempt}
        # 独立 trial 从系统提示开始；多轮用例只保留本次对话的真实历史。
        messages = list(history) if history else [{"role": "system", "content": SYSTEM_PROMPT}]
        trial = {
            "trial_id": trial_id,
            "case_id": case.case_id,
            "kind": case.kind,
            "family": case.family,
            "authenticated_user_id": session.authenticated_user_id,
            "filter_enabled": filter_enabled,
            "expected_turns": len(case.turns),
            "simulated": self.provider.simulated,
            "top_k": config.top_k,
            "turns": [],
            "status": "running",
            "attempt": attempt,
        }
        for query in case.turns:
            turn = {"input": query, "answer": None, "completed": False}
            trial["turns"].append(turn)
            self.provider.context["turn_number"] = len(trial["turns"])
            messages.append({"role": "user", "content": query})
            try:
                plan = self.provider.complete(messages, planning=True)["choices"][0]
                assistant = plan["message"]
                calls = assistant.get("tool_calls") or []
                turn["tool_calls"] = calls
                if (
                    plan["finish_reason"] != "tool_calls"
                    or len(calls) != 1
                    or calls[0]["function"]["name"] != "search_memory"
                ):
                    raise ValueError("Expected exactly one search_memory call")
                # 工具只接收 query；身份、top_k 和过滤开关由程序控制。
                args = SearchArgs.model_validate_json(calls[0]["function"]["arguments"])
                event = self.retrieval.retrieve(args.query, session, filter_enabled)
                turn["retrieval"] = event
                # 先存检索证据，后续回答失败时也不能抹掉已经发生的 L1。
                self.save(trial)
                if not event["completed"]:
                    raise RuntimeError("Retrieval failed; unscoped fallback is forbidden")
                messages.append(
                    {k: assistant[k] for k in ("role", "content", "tool_calls") if k in assistant}
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": calls[0]["id"],
                        "content": json.dumps(
                            {"records": event["records"], "allowed": event["decision"]["allowed"]}
                        ),
                    }
                )
                # 回答阶段不再开放工具，每轮最多进行一次检索。
                answer = self.provider.complete(messages, planning=False)["choices"][0]
                turn["answer"] = answer["message"].get("content") or ""
                self.save(trial)
                if (
                    answer["finish_reason"] != "stop"
                    or answer["message"].get("tool_calls")
                    or not turn["answer"].strip()
                ):
                    raise ValueError("Incomplete or invalid final answer")
                messages.append({"role": "assistant", "content": turn["answer"]})
                turn["completed"] = True
            except Exception as exc:
                turn["error_type"] = type(exc).__name__
                trial["status"] = (
                    "stopped" if isinstance(exc, (BudgetStop, FatalAPIError)) else "error"
                )
                trial["stop_reason"] = type(exc).__name__
                break
            finally:
                self.save(trial)
        else:
            trial["status"] = "complete"
        trial.update(
            latency_ms=(time.perf_counter() - start) * 1000,
            cost_upper_usd=self.provider.cost - cost_before,
            response_model=self.provider.response_model,
        )
        self.save(trial)
        return trial, messages

    def save(self, trial):
        trial["cost_upper_usd"] = self.provider.cost - self.cost_before
        if self.checkpoint:
            append_jsonl(self.checkpoint, {"event": "trial_checkpoint", "trial": trial})
