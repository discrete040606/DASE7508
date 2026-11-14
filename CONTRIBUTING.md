# Collaboration and verification

On 2026-11-13, the team leader chose to merge checked changes without waiting for independent cross-review. Keep the issue, PR, commands and observed outcomes. The course manual asks for teammate review, so the submission record must distinguish this workflow from that requirement.

1. Open a bounded issue with acceptance criteria and a human owner.
2. Implement on a branch, inspect the diff, and run relevant tests including invalid-input and trust-boundary cases.
3. Open a PR linked to the issue. Record commands, outcomes, AI assistance and unverified limitations.
4. Merge after checks pass, then confirm main and linked issue status. Teammate review is optional under the leader's instruction.

Never commit API keys, student IDs, virtual environments, local databases or real private data. Commit validated synthetic inputs and intentionally retained live research evidence. Offline protocol fixtures belong under results/offline and cannot support model-security claims.
