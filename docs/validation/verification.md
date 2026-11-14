# Implementation verification — 2026-11-13

Checks were run on macOS with Python 3.11.18 and requirements.lock.txt. The sections below follow the work in order: initial offline validation, live pilot and formal run. AI assistance is recorded in [the project disclosure](../collaboration/ai-usage.md).

Initial offline checks, executed from the project root:

- `python -m pytest -q`: 20 passed, including Streamlit AppTest refresh/session checks, mocked HTTP retries and real Chroma queries using test vectors.
- `python -m compileall -q src app`: passed.
- `uv pip check --python .venv/bin/python`: 111 installed packages compatible.
- `memory-lab prepare` and `memory-lab validate`: 100 synthetic memories, 30 cases, invariant checks passed.
- `memory-lab index`: downloaded local all-MiniLM-L6-v2 model into the project and indexed 100 records.
- `memory-lab run --offline --output results/offline/final-verification`: 300 unique slots complete, zero errors, 75 per condition.
- `memory-lab analyze results/offline/final-verification`: CSV/JSON tables and security/utility/latency PNGs exported; offline labels visible.
- Streamlit local health endpoint returned `ok`.
- Local Markdown links and git-ignore rules checked; local environments, key files, budget ledger, vector index, model files and offline outputs are excluded from Git.

The offline provider deliberately echoes retrieved records. Its apparent disclosure rates are fixture behaviour, not measured DeepSeek behaviour. Offline files remain locally under the ignored results/offline directory and can be regenerated using the commands above.

At this stage the environment had no DEEPSEEK_API_KEY, so the initial checks did not make real API calls. The live runs were completed later, as recorded below.

## Live follow-up

[The live pilot record](live-pilot.md) describes the protocol failure, correction, 22 passing tests and the successful 24/24 repeat pilot. Pilot and formal results use separate directories.

## Formal live completion

The formal live run completed 300/300 first-attempt slots, 340 user turns and 680 paired requests/responses, with zero errors. Frozen provenance and every enforced owner constraint were checked. See [formal results](../formal-results.md) and the saved validation.json for exact rates and costs.

## Readability and journal refactor — 2026-11-14

26 tests passed after consolidating journal reading and cost aggregation. Scratch replays of formal/v1, pilot/v1 and pilot/v2 matched every saved summary value and denominator. The archived files, prompt/tool definitions, experiment inputs and existing cost ledger were unchanged. No paid API run was needed for this check.
