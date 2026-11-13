# Implementation verification — 2026-11-13

Environment: macOS, Python 3.11.18, dependencies pinned in requirements.lock.txt. AI-assisted implementation requested by Yang Lingfeng. Independent human review was not performed, as explicitly waived by the leader.

Executed from the project root:

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

Not executed: real DeepSeek calls, live pilot, live 300-trial research experiment. DEEPSEEK_API_KEY was not configured in the execution environment. No real-model security or cost findings are claimed. The next step is to configure the key locally, run the pilot, inspect the evidence, and start a new frozen formal run directory.

## Live follow-up

Real API access is now configured. See [the live pilot record](live-pilot.md) for the initial protocol failure, fix, 22 passing tests and the corrected 24/24 real pilot. Historical offline evidence above remains separately labelled. Formal experiment results must be read from their own frozen run directory.

## Formal live completion

The formal live run completed 300/300 first-attempt slots, 340 user turns and 680 paired requests/responses, with zero errors. Frozen provenance and every enforced owner constraint were checked. See [formal results](formal-results.md) and the saved validation.json for exact rates and costs.
