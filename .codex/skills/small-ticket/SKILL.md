---
name: small-ticket
description: Spec, implement, verify, and open a PR for a small Linear ticket in one continuous workflow. Use when the user says /small-ticket, /quick-ticket, asks to handle a small ticket end-to-end, or wants the spec-ticket workflow followed immediately by applying the OpenSpec change and opening a PR without waiting for confirmation.
---

# Small Ticket

## Overview

Handle a small Linear ticket through proposal, implementation, verification, and PR creation without pausing between planning and coding. This skill composes `spec-ticket`, `openspec-apply-change`, and the PR preparation parts of `ship-ticket`.

## Workflow

1. Resolve the ticket.
   - If the user provided a Linear key such as `RAV-17`, fetch it with the Linear plugin.
   - If no ticket is provided, ask for the ticket key.
   - Use the ticket title, description, labels, attachments, and project/milestone context.

2. Confirm the ticket is small enough for this workflow.
   - Proceed when the ticket is narrow, localized, and can reasonably be planned and implemented in the current branch.
   - Use the full `spec-ticket` workflow instead if the ticket needs unresolved product decisions, materially different architectures, security-sensitive choices, a new service/datastore, or a public API contract decision.
   - If project instructions require user input for the kind of change being made, ask before proceeding.

3. Spec the ticket.
   - Follow `spec-ticket`: explore the codebase, answer discoverable questions locally, and create an OpenSpec proposal/design/spec/tasks change.
   - Skip grilling when the Linear ticket and codebase provide enough information for a small change.
   - Ask only focused blocking questions that cannot be answered from Linear, docs, specs, or code.
   - Include architectural trade-offs for public API, persistence, cross-cutting, service, datastore, integration, security, deployment, or public UX changes.

4. Apply the change immediately.
   - Use `openspec-apply-change` after the OpenSpec artifacts are created.
   - Do not ask for confirmation between proposal creation and implementation unless a guardrail requires it.
   - Keep edits scoped to the ticket and follow established project patterns.
   - Add or update focused tests when the project has a relevant test layer.

5. Verify readiness.
   - Run the narrowest useful task during development.
   - Run `openspec instructions apply --change "<name>" --json` and confirm all tasks are complete.
   - Run `task check` before opening the PR when feasible.
   - If verification cannot run, report exactly why and include the best substitute evidence.

6. Prepare and open the PR.
   - Inspect `git status -sb` and the diff before staging.
   - Stage only files belonging to the ticket.
   - Commit with a terse message if there are uncommitted changes.
   - Push the branch.
   - Open a ready-for-review PR unless the user explicitly asks for draft.
   - Include screenshots in the PR description for visual UI changes. If screenshots cannot be produced locally, explain why in the PR description and include the best available substitute.
   - Explicitly state when no screenshots are needed.

7. Finish with a concise summary.
   - Include the Linear ticket key, OpenSpec change name, PR URL, commit, and verification performed.
   - Note any skipped verification, screenshot limitations, or follow-up needed before merge.

## Guardrails

- Do not use this workflow for large, ambiguous, cross-cutting, security-sensitive, or architecture-heavy tickets; switch to `spec-ticket` and stop after planning.
- Do not bypass project boundaries or hide failures with quiet fallbacks.
- Do not stage unrelated changes silently.
- Do not merge the PR or move the Linear ticket to Done; use `ship-ticket` after review and CI are ready for shipping.
- If a command fails because of permissions or sandboxing, request escalation rather than working around the repository boundary.
