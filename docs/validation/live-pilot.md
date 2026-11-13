# Real API pilot — 2026-11-13

These runs used the real DeepSeek API and the frozen synthetic dataset, not the offline echo provider. Authentication was loaded locally and is excluded from logs and Git.

## Initial pilot (v1)

All 24 scheduled slots were attempted. Only 1 completed; 23 encountered protocol errors. Inspection showed that named tool choice returned two alternative search_memory calls in many planning responses. The strict Agent guard rejected them before retrieval. All errors, partial outcomes and API charges remain under results/pilot/v1; this run must not be silently combined with v2 or the formal experiment.

## Protocol correction

The shared system prompt now explicitly requests one combined search query per user turn, without parallel or alternative tool calls. Runtime still rejects any response with more than one call; it does not select a convenient call or hide protocol errors. The instruction is identical across all conditions and governs call count, not disclosure or access control. The database ownership filter is unchanged.

The CLI and UI now load the API key from the environment first, then the ignored project .env, with interpolation disabled. Key contents are never printed or added to experiment manifests.

## Corrected pilot (v2)

- 24 scheduled slots completed; zero errors; 56 real API requests.
- Actual response model: deepseek-flash; thinking disabled.
- A: 4 legitimate unfiltered trials, CURR 4/4, CUDR 4/4, LRSR 4/4.
- B: 8 malicious unfiltered trials, CURR 8/8, CUDR 7/8.
- C: 4 legitimate filtered trials, CURR 0/4, CUDR 0/4, LRSR 4/4, FBR 0/4.
- D: 8 malicious filtered trials, CURR 0/8, CUDR 0/8.

L2 uses exact canaries and normalised unique fact phrases; it may miss semantic paraphrases. These are pilot observations on synthetic data, not the final experiment or a general security guarantee.

Cumulative project cost upper estimate after both pilots: USD 0.0226098, using configured peak pricing. Exact billing may differ. Pilot raw evidence and reports remain in separate version directories. Formal runs use a fresh output directory and never pool pilot observations into their rates.

Automated checks after the correction: 22 tests passed, including parallel-call rejection without retrieval and environment-over-file credential precedence. Independent human review was not performed, per the leader's instruction.
