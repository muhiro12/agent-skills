# Returned Work and Closure

## Apply the Refinement Skill

Confirm that Claude has stopped edits and stateful verification and that the
returned checkout and brief revision match the task record. Keep the returned
commit range or dirty-diff artifacts identifiable before Codex takes ownership.
Set `Stage: review` and `Next owner: Codex`.

Read and apply
[refine-development-changes](../../refine-development-changes/SKILL.md) to the
returned work, carrying the agreed outcome, governing sources, exact input,
existing evidence, and user authority from the brief. Reuse the current handoff;
do not ask the user to invoke another skill or create a separate task record.
The refinement skill is the source of review, correction, and verification
requirements. Record its result instead of maintaining another review checklist
here. A successful runner return alone does not complete this step.

## Coordinate Follow-up Work

Codex can finish local corrections directly. When substantial rework benefits
from Claude's implementation context, group the refinement findings, desired
outcome, evidence, and any Codex edits into one follow-up within the agreed
session and attempt limits. Resolve material scope or product decisions before
dependent work; the return does not expand the original authority.

After another Claude return, confirm it has released write ownership and apply
the refinement skill to the new result. Avoid automatic correction loops: explain
why an additional exchange is needed and revise the remaining plan. Codex may take over
when Claude is unavailable or limits are exhausted; record the reason and
remaining work without weakening acceptance or increasing the limits silently.

## Close the Coordinated Task

Record the refinement result, final revision, correction routing, and remaining
limitations in the handoff. Set `Stage: done` only when all requested items and
their integration are accepted through refinement, including any explicitly
accepted limitations. A later change requires reassessment of the affected
result. Keep actual agent work and coordination evidence separate from the
development result, following the usage reference when applicable.
