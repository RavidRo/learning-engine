---
name: spec-ticket
description: Read a Linear ticket, interrogate unclear requirements with grill-me, and create an OpenSpec proposal/design/spec/tasks change. Use when the user says /spec-ticket, asks to plan/spec a Linear ticket, or wants the read Linear, grill me, OpenSpec propose workflow.
---

# Spec Ticket

## Overview

Turn a Linear issue into an implementation-ready OpenSpec change. This skill composes the Linear plugin, `grill-me`, and `openspec-propose` into one ticket-planning workflow.

## Workflow

1. Resolve the ticket.
   - If the user provided a Linear key such as `RAV-17`, fetch it with the Linear plugin.
   - If no ticket is provided, ask for the ticket key.
   - Use the ticket title, description, labels, attachments, and project/milestone context.

2. Explore the codebase before asking questions.
   - Search for existing code, specs, docs, and tests related to the ticket.
   - Answer anything discoverable locally without asking the user.
   - Use project guidance from `AGENTS.md`, `.contextive/definitions.yml`, and relevant docs when the change touches architecture, APIs, persistence, security, deployment, or public UX.

3. Grill the ticket.
   - Use `grill-me` behavior: ask one question at a time.
   - Provide a recommended answer for every question.
   - Only ask questions that cannot be answered from Linear or the codebase.
   - Stop grilling once decisions are sufficient for an OpenSpec proposal.

4. Propose the OpenSpec change.
   - Derive a concise kebab-case change name from the ticket.
   - Use `openspec-propose` to create all required planning artifacts.
   - Make the proposal explicitly reference the Linear ticket key when useful.
   - Include architectural trade-offs for public API, persistence, cross-cutting, service, datastore, or integration changes.

5. Finish with a short summary.
   - Report the change name and artifact paths.
   - State the key decisions made during grilling.
   - State whether the change is ready for implementation.

## Guardrails

- Do not implement code in this workflow unless the user explicitly asks to continue into implementation.
- Do not invent acceptance criteria when Linear/code context is insufficient; ask a focused question instead.
- Do not skip `grill-me` unless the ticket is already fully specified and the user explicitly asks to skip it.
- If the Linear plugin is unavailable, say so and proceed only if the user supplies the ticket text.
