---
name: ship-ticket
description: Finish an implemented OpenSpec/Linear ticket by syncing specs, archiving the change, opening a PR, fixing review or CI issues, merging after all checks pass, and moving the Linear ticket to done. Use when the user says /ship-ticket, /finish-ticket, asks to ship a completed ticket, or wants the sync, archive, PR, checks, merge, done workflow.
---

# Ship Ticket

## Overview

Ship a completed ticket end-to-end. This skill composes `openspec-sync-specs`, `openspec-archive-change`, GitHub PR workflows, CI/comment handling, and Linear status updates.

## Workflow

1. Identify the change and ticket.
   - Infer the OpenSpec change from the current conversation or branch only when unambiguous.
   - If the change is unclear, list active OpenSpec changes and ask the user to choose.
   - Infer the Linear ticket from the branch, PR title/body, commit messages, or conversation. If unclear, ask for the ticket key.

2. Verify implementation readiness.
   - Run `openspec instructions apply --change "<name>" --json`.
   - Confirm all tasks are complete; if not, stop and report what remains.
   - Run `task check` before publishing unless it already passed after the final code/spec changes.

3. Sync and archive OpenSpec.
   - Use `openspec-sync-specs` to apply delta specs to `openspec/specs`.
   - Use `openspec-archive-change` to move the completed change into the dated archive.
   - Re-run `task check` after sync/archive if files changed.

4. Prepare the PR.
   - Inspect `git status -sb` and the diff before staging.
   - Stage only files belonging to the completed ticket.
   - Commit with a terse message if there are uncommitted changes.
   - Push the branch.
   - Open a ready-for-review PR unless the user explicitly asks for draft.
   - If visual UI changed, include a screenshot in the PR description. If local screenshot capture is impossible, explain why and include the best available substitute.

5. Wait for PR feedback and checks.
   - Wait for all PR checks to complete.
   - If any GitHub Actions check fails, inspect logs with the GitHub CI workflow, fix the issue, run local checks, commit, push, and wait again.
   - Inspect actionable PR comments/review feedback with the GitHub review workflow. Fix actionable comments, run checks, commit, push, and wait again.
   - Do not merge while checks are pending or failing.

6. Merge and close the ticket.
   - When all checks pass and review blockers are resolved, merge the PR using the repository's normal merge strategy.
   - Delete the remote branch when safe.
   - Move the Linear ticket to Done using the Linear plugin. If the exact done status is ambiguous, discover statuses for the team or ask the user.

7. Finish with a concise shipping summary.
   - Include PR URL, merge commit, checks, OpenSpec archive path, and Linear ticket status.
   - Note any cleanup not performed, such as a local branch that cannot be deleted because it is checked out.

## Guardrails

- Never stage unrelated changes silently.
- Never merge before all checks are complete and successful.
- Never skip PR screenshots for visual changes; include them or explicitly explain why they could not be produced.
- Do not close or move a Linear ticket until the PR has merged.
- If a command fails because of permissions or sandboxing, request escalation rather than working around the repository boundary.
