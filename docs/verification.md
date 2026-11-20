# Implementation verification — 2026-11-13

Checks were run on macOS with Python 3.11.18 and requirements.lock.txt. The sections below follow the work in order: initial offline validation, live pilot and formal run. AI assistance is recorded in [the project disclosure](ai-usage.md).

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

[The live pilot record](verification.md) describes the protocol failure, correction, 22 passing tests and the successful 24/24 repeat pilot. Pilot and formal results use separate directories.

## Formal live completion

The formal live run completed 300/300 first-attempt slots, 340 user turns and 680 paired requests/responses, with zero errors. Frozen provenance and every enforced owner constraint were checked. See [formal results](formal-results.md) and the saved validation.json for exact rates and costs.

## Readability and journal refactor — 2026-11-14

26 tests passed after consolidating journal reading and cost aggregation. Scratch replays of formal/v1, pilot/v1 and pilot/v2 matched every saved summary value and denominator. The archived files, prompt/tool definitions, experiment inputs and existing cost ledger were unchanged. No paid API run was needed for this check.

---

# Real API pilot — 2026-11-13

The pilot used the real DeepSeek API with the frozen synthetic dataset. The credential was read locally and kept out of the saved evidence.

## Initial pilot (v1)

All 24 scheduled slots were attempted. Only 1 completed; 23 encountered protocol errors. Inspection showed that named tool choice returned two alternative search_memory calls in many planning responses. The strict Agent guard rejected them before retrieval. All errors, partial outcomes and API charges remain under results/pilot/v1; this run must not be silently combined with v2 or the formal experiment.

## Protocol correction

The correction added an explicit instruction to issue one combined search query per user turn. The runtime guard still rejects responses with multiple calls. Both experimental modes use the same instruction; the ownership filter itself was unchanged.

The CLI and UI now load the API key from the environment first, then the ignored project .env, with interpolation disabled. Key contents are never printed or added to experiment manifests.

## Corrected pilot (v2)

- 24 scheduled slots completed; zero errors; 56 real API requests.
- Actual response model: deepseek-flash; thinking disabled.
- A: 4 legitimate unfiltered trials, CURR 4/4, CUDR 4/4, LRSR 4/4.
- B: 8 malicious unfiltered trials, CURR 8/8, CUDR 7/8.
- C: 4 legitimate filtered trials, CURR 0/4, CUDR 0/4, LRSR 4/4, FBR 0/4.
- D: 8 malicious filtered trials, CURR 0/8, CUDR 0/8.

L2 uses exact canaries and normalised unique fact phrases, which can miss paraphrases. The observations above belong only to the pilot; [the formal run](formal-results.md) is reported separately.

Cumulative project cost upper estimate after both pilots: USD 0.0226098, using configured peak pricing. Exact billing may differ. Pilot raw evidence and reports remain in separate version directories. Formal runs use a fresh output directory and never pool pilot observations into their rates.

After the correction, 22 tests passed, including rejection of parallel calls before retrieval and environment-over-file credential precedence.

## Student reading layout — 2026-11-20

- 27 automated tests passed, including the existing UI refresh/session-reset checks and a new check that the frozen manifest covers the relocated package and demo entry.
- Editable installation, CLI dataset validation, the existing 100-record Chroma index, Python compilation and launcher syntax checks passed with the new layout.
- 72 existing data/result/configuration/ledger files matched their pre-change SHA-256 hashes. Reanalysis of scratch copies of formal/v1, pilot/v1 and pilot/v2 reproduced every saved summary value exactly.
- Runtime syntax trees outside the explicitly updated path handling and removed unused import were compared after excluding docstrings; executable behaviour was unchanged. Local Markdown links were checked.
- The earlier src/app commands above describe historical checks. Current commands use memory_lab/ and demo.py, as documented in README.
- A new offline run completed two slots, then resumed to four unique completed slots without duplicate attempts.
- No paid API call was made, and a live browser walkthrough was not performed for this maintenance. Streamlit behaviour was checked using AppTest.
