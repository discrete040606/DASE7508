# Team tasks and review plan

Responsibilities follow the project proposal. The team leader confirmed the GitHub handles below. Check invitation acceptance and each person's actual access before relying on collaboration. Reviewer names below are optional suggestions under the leader decision; no cross-review is required before merge.

| Member | GitHub handle | Work issue | First deliverable | Proposed reviewer |
| --- | --- | --- | --- | --- |
| Yang Lingfeng / 杨凌峰 | discrete040606 | [#2](https://github.com/discrete040606/DASE7508/issues/2) | Agent skeleton, architecture, validated interface proposal | Xi Muzhe |
| He Chenyuan | xudeshendedad | [#3](https://github.com/discrete040606/DASE7508/issues/3) | Threat boundaries and pilot attacks, then 15 malicious cases covering M1-M8 | Zhang Shengxuan |
| Xi Muzhe | x-m-z | [#4](https://github.com/discrete040606/DASE7508/issues/4) | Filter module and tests for own-user, foreign-user, spoofed and invalid identities | Yang Lingfeng |
| Zhang Shengxuan | congkun666-spec | [#5](https://github.com/discrete040606/DASE7508/issues/5) | 100 synthetic memories, 15 legitimate cases and evaluator prototype | He Chenyuan |
| Hou Dianqi | 000Crystal | [#6](https://github.com/discrete040606/DASE7508/issues/6) | Report/slide structure, fresh-checkout reproduction and evidence checklist | Yang Lingfeng |

Repository setup is tracked separately in [#1](https://github.com/discrete040606/DASE7508/issues/1), owned by Yang Lingfeng, with Hou Dianqi as an optional reviewer. It was merged without independent review at the leader's instruction. Do not treat this table as a submitted GitHub review or a completed contribution record.

## Dependency order

1. Yang Lingfeng proposes memory/session/query/retrieval/log schemas; Xi Muzhe and Zhang Shengxuan agree the integration points.
2. He Chenyuan and Zhang Shengxuan align attack queries with synthetic target records, keeping secrets out of attack inputs.
3. Integrate a small pilot with filter off/on and separate retrieval/disclosure observations.
4. Freeze the dataset, cases, prompts, model IDs, top_k and reset rules; then run the 300-trial plan.
5. Each owner supplies verified methods and evidence for their own report section. Hou Dianqi coordinates consistency and reproduction.

## Milestones from the proposal

| Target course week | Planned outcome |
| --- | --- |
| W7 | Freeze definitions; build prototype and dataset |
| W8 | Pilot, freeze attack set, validate filter |
| W9 | Run 300 trials |
| W10 | Analyse results and write report |
| W11 | Prepare presentation |

These are proposal targets, not confirmed calendar dates or completion claims. Check Moodle for actual deadlines.

## Actual contribution record

Update this table from merged PRs and retained evidence, not planned responsibilities.

| Member | Verified contribution | Evidence |
| --- | --- | --- |
| Yang Lingfeng | Pending human confirmation | Pending |
| He Chenyuan | Pending | Pending |
| Xi Muzhe | Pending | Pending |
| Zhang Shengxuan | Pending | Pending |
| Hou Dianqi | Pending | Pending |

## Unified implementation

Yang Lingfeng requested the entire software implementation through Codex. Planned responsibilities above remain historical allocation; they are not proof of each member's actual contribution. Live API runs and final report/presentation remain pending.
