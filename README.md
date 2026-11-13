# DASE7508: Cross-User Memory Disclosure in Multi-User LLM Agents

**Threat Model, Attack Design and an Identity-Based Retrieval Filter**

Controlled evaluation of cross-user memory leakage and identity-based retrieval filtering in multi-user LLM agents. This repository is the team's shared source of code, configurations, synthetic inputs, results, and collaboration evidence.

## Current status

Repository preparation only. The agent, filter, dataset, experiment runner, dependency lockfile, and reported results are **not implemented yet**. The linked issues describe planned work; they are not completion claims.

## Research question and security boundary

Can an authenticated user retrieve or receive another user's memories when a shared memory store has no user-level access control? Can a mandatory identity-based retrieval constraint reduce this while preserving legitimate retrieval?

- **L1 / cross-user retrieval:** the retrieval tool returns a record belonging to another user.
- **L2 / cross-user disclosure:** the final answer contains another user's canary or unique private fact.
- Authorisation comes only from the trusted server-side session. Query text and model-generated identity arguments are untrusted.
- In defence mode, apply `owner_user_id == authenticated_user_id` inside the database query. Missing or invalid identity must default to deny.

Planned flow: trusted session + user query → agent → retrieval tool → identity filter (defence mode) → shared synthetic memory database → retrieved records → agent answer. Record retrieval and final-answer evidence separately.

## Preparation

Prerequisites: Git, repository access, and Python **3.11** for the planned implementation.

```bash
git clone https://github.com/discrete040606/DASE7508.git
cd DASE7508
python3.11 --version
python3.11 -m venv .venv
source .venv/bin/activate
python --version
```

Expected preparation result: a local checkout and an active Python 3.11.x virtual environment. On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`. For a private repository, authenticate with your own GitHub account using a supported Git credential manager or SSH; do not paste tokens into tracked files.

**Install/run/reproduce:** pending implementation in [issue #2](https://github.com/discrete040606/DASE7508/issues/2) and [issue #5](https://github.com/discrete040606/DASE7508/issues/5). No application command or dependency-install command is available yet. Add tested commands, pinned dependencies, a small synthetic example with expected output, and actual verification evidence when those issues are implemented.

The proposal plans the OpenAI Responses API, GPT-5 mini, text-embedding-3-small, local Chroma, Pydantic, JSON/YAML configuration, JSONL logs, and pandas/matplotlib. Exact supported model IDs, versions, costs, and availability must be verified during implementation. API calls may incur cost; no cost or runtime result is claimed here.

## Repository map

| Path | Purpose |
| --- | --- |
| [src/](src/README.md) | Agent, trusted-session interfaces, retrieval and defence implementation |
| [tests/](tests/README.md) | Interface, policy, evaluator and integration checks |
| [data/](data/README.md) | Versioned synthetic memories and query cases |
| [configs/](configs/README.md) | Reproducible experiment settings and prompts |
| [results/](results/README.md) | Retained synthetic trial evidence, metrics and figures |
| [reports/](reports/README.md) | Report, architecture diagrams and presentation |
| [docs/team-plan.md](docs/team-plan.md) | Members, tasks, proposed reviewers and milestones |
| [docs/experiment-plan.md](docs/experiment-plan.md) | Threat model, four conditions, metrics and evidence |
| [docs/ai-usage.md](docs/ai-usage.md) | AI assistance and human-verification records |
| [docs/submission-checklist.md](docs/submission-checklist.md) | Access, submission and assessment-commit checklist |

## Team and collaboration

| Member | Responsibility | Task |
| --- | --- | --- |
| Yang Lingfeng / 杨凌峰 | Architecture, agent, interfaces and integration | [#2](https://github.com/discrete040606/DASE7508/issues/2) |
| He Chenyuan | Threat model and M1-M8 attacks | [#3](https://github.com/discrete040606/DASE7508/issues/3) |
| Xi Muzhe | Identity-based retrieval defence | [#4](https://github.com/discrete040606/DASE7508/issues/4) |
| Zhang Shengxuan | Synthetic data, experiments and evaluation | [#5](https://github.com/discrete040606/DASE7508/issues/5) |
| Hou Dianqi | Documentation, reproduction and presentation | [#6](https://github.com/discrete040606/DASE7508/issues/6) |

Follow [CONTRIBUTING.md](CONTRIBUTING.md): **issue → branch → agent-assisted work → PR → independent teammate review → merge**. The task owner and reviewer must be different people. Preserve checks, limitations, AI assistance and actual human verification in each PR.

## Data handling

Use only synthetic research data. Keep credentials, API keys, private datasets and student IDs out of commits and agent prompts. Student IDs belong in the private course submission email. Do not upload the original proposal unchanged: it contains student IDs. See the [submission checklist](docs/submission-checklist.md) for course delivery requirements.
