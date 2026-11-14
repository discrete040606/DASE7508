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

L2 uses exact canaries and normalised unique fact phrases, which can miss paraphrases. The observations above belong only to the pilot; [the formal run](../formal-results.md) is reported separately.

Cumulative project cost upper estimate after both pilots: USD 0.0226098, using configured peak pricing. Exact billing may differ. Pilot raw evidence and reports remain in separate version directories. Formal runs use a fresh output directory and never pool pilot observations into their rates.

After the correction, 22 tests passed, including rejection of parallel calls before retrieval and environment-over-file credential precedence.
