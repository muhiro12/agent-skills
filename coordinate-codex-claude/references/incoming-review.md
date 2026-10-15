# Incoming work review

Use this entry when the user explicitly invokes the coordination skill for work
already produced by Claude or by hand. Start with
[shared development-change refinement](../../refine-development-changes/SKILL.md)
for the actual input, governing sources, behavior and commit review, corrections,
verification, and history safeguards. Honor the user's review-only or finish
scope. An original Codex brief, Claude session, or runner result is not required.

## Establish Coordination State

Confirm the prior writer has stopped edits and stateful verification before
Codex takes ownership. Start the task record at `Stage: review` and
`Next owner: Codex`. Preserve the exact selected commits, dirty patches, unrelated work, and
existing evidence established by the shared workflow.

Mark the brief as reconstructed incoming scope, not retrospective Codex design
approval. If the original Claude session or usage is unknown, say so; do not
invent identities, prior approvals, or historical usage measurements. The user
remains the source of authority; an implementer's report does not expand it.

## Route Corrections and Close

Follow [review and closure](review-and-close.md) for Codex acceptance, bounded
final adjustments, and grouped Claude rework. In a finish request, complete the
needed changes and verification; the incoming entry is not a findings-only gate.

For substantial reimplementation or a broad verification impact, prepare one
grouped correction brief when delegation is justified. Follow the automatic
dispatch reference for session identity and preflight; never adopt an unrelated
recent session or manufacture runner state. Manual authorship does not prevent
delegating a new correction when this coordination workflow is authorized.
If dispatch is unavailable, follow the existing Codex takeover and limit policy.

Record which agent made each adjustment and why substantial work was delegated
or taken over. Reconcile the final revision, verification, commit changes, and
remaining limitations in the handoff. The shared workflow owns publication
routing and history safeguards; coordination acceptance supplies no additional
push, merge, release, or rewrite authority.
