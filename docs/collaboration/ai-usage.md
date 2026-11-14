# AI assistance and human verification

Yang Lingfeng requested the implementation and experiment runs through OpenAI Codex. This record separates that assistance from the members’ own confirmed work; supporting commands and outcomes are linked from the PRs.

## Repository preparation

Codex read the course manual, proposal and repository, then prepared the README, collaboration templates and task issues. The setup PR records the checks performed at that stage. Independent teammate review was waived by Yang Lingfeng. Human review and course submission are recorded separately.

## Record future assistance

For further work, record the date, member, issue/PR, AI task and checks actually performed. Keep each member’s confirmed contribution in [the team record](team-plan.md).

## Full software implementation

Yang Lingfeng requested Codex to implement all software in the specified Agent project folder. Codex implemented synthetic data generation, validated schemas, server-side simulated sessions, database-level ownership filtering, DeepSeek integration, budget accounting, separate L1/L2 evaluation, resumable schedules, analysis, tests, local Streamlit UI and reproduction documentation.

The first validation used protocol/HTTP fixtures and local Chroma/embedding execution. Those offline outputs remain separate from the later real API runs.

## Real API experiments

After local credential setup, Codex ran the pilot and corrected duplicate planning calls. Both pilot versions were retained. The subsequent frozen 300-trial run produced the tables, figures and result summary under results/formal/v1. Codex checked completeness and credential exclusion.

## Readability maintenance (2026-11-14)

Codex consolidated repeated documentation and refactored journal reading and cost aggregation. The experiment protocol and archived evidence were retained. Verification for this maintenance change is recorded in its PR.
