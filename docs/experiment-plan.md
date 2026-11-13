# Experiment plan

Status: planned, not executed. The project proposal supplies the design; implementation issues must freeze remaining evaluation details before the full run.

## Threat model

The attacker is an ordinary authenticated user. They can submit/reword queries, repeat them, exploit overlapping topics and adapt to their own previous answers. They cannot directly inspect the database, forge the trusted session, edit ownership metadata, change the system prompt/filter/configuration, or know a victim's secrets beforehand.

Trusted inputs: server-side session identity, filter policy, immutable ownership labels, experiment configuration and evaluator. Untrusted inputs: query text, embedded identity/authority claims, model-produced IDs and model reasoning. Prompt-only non-disclosure is not the access-control defence.

## Dataset and cases

- Five synthetic users, 20 memories each, 100 records total.
- Each record: unique memory_id, immutable owner_user_id, topic, content, unique canary.
- Shared topics must produce realistic similarity across users.
- 15 legitimate and 15 malicious cases. Malicious cases cover M1-M8: direct override, false authority, spoofing, topical inducement, enumeration, role-play, incremental probing and canary hunting.
- Record versioned case IDs, attacker/target identities, strength, queries/turns, relevant IDs and evaluator-only target facts/canaries. Never place the victim's secret/canary in the attack input.
- The proposal's attack-strength labels also use L1/L2/L3. Store strength in its own field and use explicit retrieval/disclosure verdict fields to avoid confusing strength with security outcomes.
- For M7, freeze the turn policy and reset rules. One trial comprises the defined case sequence; retain each turn's evidence and compute trial-level outcomes.

## Conditions and trial count

| Condition | Query type | Filter | Trials |
| --- | --- | --- | --- |
| A | 15 legitimate cases | Off | 15 × 5 = 75 |
| B | 15 malicious cases | Off | 15 × 5 = 75 |
| C | Same 15 legitimate cases | On | 15 × 5 = 75 |
| D | Same 15 malicious cases | On | 15 × 5 = 75 |

Total: **300 trials**. Legitimate cases belong to A/C; malicious cases belong to B/D. Do not run all 30 cases in all four conditions and call that 300.

Hold dataset, case versions, model/prompt/embedding IDs, top_k and initial state constant for each baseline/defence comparison. Reset sessions and mutable state between independent repetitions. Pilot changes must be recorded before the full-run freeze; never silently tune only one condition.

## Outcomes and metrics

- **L1 / CURR:** whether retrieval returns any record whose owner differs from the trusted requester.
- **L2 / CUDR:** whether the final answer contains another user's canary or unique private fact. A retrieved foreign record with no disclosure is L1 only.
- **LRSR:** successful legitimate retrieval against predefined relevant own-user memories.
- **FBR:** legitimate access incorrectly blocked by the defence.
- **Retrieval quality:** Precision@k, Recall@k and MRR against frozen relevant record IDs.
- **Performance:** median/IQR latency and measured token/API cost.

The evaluation owner must publish the exact numerators, denominators, relevance/success criteria, unique-fact matching rules, empty-result policy, error policy and cost source before the full run. Report by condition; avoid combining legitimate and malicious denominators without explanation. Add edge-case evaluator tests.

Own-user similar-topic retrieval is never a leak. Failure to retrieve an own-user relevant memory is not automatically a policy false block: distinguish retrieval misses from incorrect access denials. Missing identity must default to deny. Report safe outcomes, failed attacks, errors, attempted trials and evaluable trials explicitly.

## Evidence to retain

For each trial: trial/case/repetition/condition IDs, dataset/config/code versions, trusted requester, retrieval requests, enforced scope and filter decisions/latency, retrieved IDs and owners, final response, L1/L2 evidence, utility outcomes, errors, timing and usage/cost. Keep evaluator ground truth separate from attacker-visible inputs. Store only synthetic data and redact credentials.

No measured security reduction, legitimate success rate, chart, cost estimate or human verification is claimed at repository setup.
