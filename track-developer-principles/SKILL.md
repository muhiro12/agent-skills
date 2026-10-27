---
name: track-developer-principles
description: Consult and automatically maintain durable developer judgment expressed by the user for product, architecture, Swift, and workflow decisions. Keep active principles, provisional signals, and raw history distinct.
---

# Track Developer Principles

Consult and maintain reusable judgment about development, product, architecture, code quality, and repository workflow.
Use `track-personal-principles` for the other domain. Keep private context outside product
repositories. Explain only material influences and actual record changes.

## Consult

Read the relevant `records/principles/<domain>/current.md`. Use
`records/current-principles.md` as the index when the domain is unclear.
Domains: meta, product-business, architecture-system-design, implementation-code-quality, workflow-collaboration.

Consult during judgment-heavy work when a stored preference can change the
decision. Skip mechanical work that needs no personal judgment. Read only the
relevant domains and do not reload them without a reason.

- `settled`: confirmed active judgment.
- `strong-default`: guidance with task-specific exceptions.
- `emerging`: provisional context, not a binding rule.
- `deprecated` / `discarded`: history, not active guidance.

Read relevant `signals.md` for unsettled questions and `records/evolution-log.md`
when a change in stance matters. Current user instructions and hard constraints
override older records. Missing records do not block ordinary work; report the
gap and use current evidence. Do not search legacy paths or migrate data merely
because records are missing.

## Capture and Revise

During relevant work, automatically record new reusable judgment the user
expresses, without asking for a separate save instruction. Respect read-only,
no-record, and narrower host or task instructions. Pure consultation with no
new judgment needs no write, and repeating an existing principle needs no copy.

Distinguish retention from endorsement: a clear general stance can update
`current.md`; an unresolved but useful thought belongs in `signals.md` as
`emerging`. Preserve rationale, applicability, exceptions, and changes in stance.
Do not turn an implementation detail, temporary task instruction, or the model's
own suggestion into a user-endorsed principle. Do not infer psychology or retain
raw conversation, secrets, or unnecessary identifying third-party details.

Before a write, read [references/record-workflow.md](references/record-workflow.md).
Preserve the existing skill-relative record paths and format. This workflow
requires no Git repository, README, sync configuration, or external service in
`records/`. Definition maintenance does not authorize bulk record rewrites.

Automatic capture covers local principle maintenance only. Raw archive capture,
migration, copying records to another environment or provider memory, and
external synchronization or publication require their own authorization. Do not
silently add those operations to a local record update.

## Report

When records change, briefly name the files and summarize the saved judgment so
the user can correct it. For consultation, mention a principle only when it
materially affected the decision. Do not report an unsaved candidate as saved.
