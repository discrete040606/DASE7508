# Team collaboration

The course manual asks the team to keep an issue, a branch, a pull request, an independent teammate review, verification evidence, and the eventual merge.

## 1. Agree a checkable task

Use the task issue template. Describe current and desired behaviour, relevant paths, constraints, acceptance criteria and expected/invalid inputs. Record a human owner and a different proposed reviewer. Confirm the reviewer before requesting their GitHub review. Use [the team plan](docs/team-plan.md) for the initial allocation.

## 2. Work on a branch

From a clean checkout, replace 2 and the short description with your actual issue:

```bash
git switch main
git pull --ff-only
git switch -c issue-2-agent-loop
```

Preserve unrelated local work before switching branches. Ask the coding agent to read the issue and existing files, stay in scope, run relevant checks, report limitations, and prepare a PR. Do not ask it to invent missing commands or successful results.

## 3. Verify, commit and open a PR

Inspect `git status` and `git diff`, run checks appropriate to the change, and stage only reviewed files. Push the work branch and open a PR targeting `main`. Use `Closes #2` for the actual issue being completed; do not close another member's implementation issue with documentation alone.

Use the PR template to record exact commands and outcomes, limitations, AI assistance and human verification. Use draft status while work is incomplete. Credentials, student IDs, real private data and local memory databases must not enter commits.

## 4. Request independent review

The owner first checks the agent output. A different teammate reads the issue and diff, follows the documented preparation/run steps from a fresh checkout of the PR branch, checks expected and invalid cases, and submits a GitHub review. Agent self-checking does not count as teammate review. Record the reviewer's name, environment, commands and observed results.

When reproducing a PR, clone into a new directory, then switch to the actual source branch shown in the PR header. Do not assume the unmerged changes are on main.

## 5. Merge and preserve evidence

Address blocking feedback, rerun affected checks, and request another review after substantive changes. Merge only after the latest changes have a teammate review and the issue checks are complete. Confirm the Merged status and linked issue closure, then update main with `git pull --ff-only`.

Branch protection is a repository setting, not something these documents enable. If configured later, require an independent approval and appropriate implemented checks; never invent CI checks or bypass a blocking result. An absent CI configuration is not test evidence.
