---
name: refine-development-changes
description: "Inspect and actively improve existing commits and working-tree changes against applicable development rules and intended behavior. Use when asked to audit changes against AGENTS.md, skills, or developer principles, or to finish existing work through refactoring, reimplementation, and verification; honor review-only requests."
---

# Refine Development Changes

Bring the selected work to a correct, verified state under the current development
contracts. This workflow owns inspection, active correction, and completion;
platform specialists supply the implementation and verification methods.

When called by another workflow, inherit its agreed outcome, scope,
authorization, input revisions, and valid evidence. Reuse its existing brief or
task record. The calling workflow retains responsibility for dispatch, session
management, and correction routing.

## Resolve the Requested Outcome

A refinement or finish request includes necessary fixes, cleanup, refactoring,
and reimplementation within the agreed product intent. Explicit invocation
without a read-only constraint requests this full workflow. Continue from
findings into implementation and verification without another approval for
already-authorized work. A request limited to review or findings stays read-only;
automatic skill selection alone does not expand the user's authority.

Keep commit, history-rewrite, publication, and release authority tied to the
actual request and governing contracts. Discussion of this skill does not
authorize changes. Ask only for a material missing decision, permission, or scope
boundary; continue independent work while resolving it.

## Establish the Actual Input

Resolve the repository, checkout, branch, and exact selected base/head commits,
including whether the named boundary commit is included. Inventory staged and
unstaged changes and relevant untracked deliverables separately from history.
Preserve unrelated work. Identify the intended behavior from the request,
accepted issue or design, and current code rather than guessing from the author.

Inspect each selected commit's full patch and message as well as the combined
result; a later deletion does not remove earlier content from history. Review
author/committer metadata and semantic commit boundaries against the applicable
policy. For uncommitted work, assess useful commit units without inventing prior
commits. Confirm write ownership before modifying a checkout another writer may
be using. Keep a compact record of the input and existing evidence. For a long
task, track the selected changes, applicable rules, review results, corrections,
verification, and unverified work with its reason. Reuse a private scratch note
or the caller's task record as useful; no fixed template or new handoff scaffold
is required.

## Judge Against Applicable Sources

Read the applicable global and local instructions and the task-relevant owning
documents. When repository AGENTS.md is absent, start at its README and durable
contracts; absence alone is not drift. Consult principle records and specialist
skills selected by the request or those contracts. A general workflow does not
choose an owner's private profile or recursively load every installed skill.

Evaluate behavior and failure paths, architecture and ownership, native platform
guidance, source style, naming, useful documentation, verification, and public
artifact hygiene in proportion to the change. For persistence, settings, files,
routes, external identifiers, or public APIs, check actual producers, consumers,
stored representations, and compatibility rather than only renamed symbols.

Tie a finding to the concrete behavior or rule, code/commit location, practical
impact, and governing source. Distinguish required rules, preferences,
intentional divergence, and uncertainty. Evaluate the result's current
compliance; missing historical tool or skill-read evidence is unverified
process, not proof of misconduct. Keep private records out of public artifacts.

## Make the Necessary Improvements

In a refinement request, actively correct confirmed problems and evidence-backed
maintenance drift. Choose the smallest complete solution, which may still
replace an unsuitable implementation. Do not limit authorized work to cosmetic
or low-risk edits, or return only recommendations because the fix is substantial.
Preserve the product outcome and established contracts; do not impose a personal
style where the governing sources allow several valid approaches.

Use the relevant implementation workflow and specialists when available; honor
any personal orchestration selected by the user's contracts. This skill itself
requires no particular provider, second agent, or external implementation session.
Resolve routine implementation choices independently. A materially unsettled
product decision, destructive operation, or change beyond the authorized scope
needs resolution before dependent work; difficulty alone is not such a boundary.

Keep corrections in meaningful functional units and commit them as authorized,
following the repository's branch and message conventions. Prefer follow-up
commits over rewriting existing history. Before an authorized rewrite, verify
publication and other-writer status against current upstream evidence, retain a
recovery reference and original attribution, and protect unrelated work. An
"unpushed" label or stale tracking ref does not establish private history.

## Verify the Selected Changes and the Corrections

Choose evidence for the important original changes as well as the new fixes.
Relate the changed behavior and failure paths to checks that actually exercise
them. Repair missing behavior coverage where it is needed; do not add tests
that only mirror implementation or impose exhaustive UI testing on a small edit.

Before expensive checks, confirm that required tools and runtimes are available,
identify a usable verification route, and assess whether existing evidence is
reusable for the current inputs and environment. Distinguish environment
failures from failures in the changed behavior. Use the relevant specialists
for platform-specific preflight and fallback procedures.

Follow the real repository contract and relevant platform guidance. Separate
logic tests, affected consumer/surface builds, repository rules, runtime/UI
observations, and production or release evidence. Use the actual supported
toolchain and relevant runtime versions. A large passing test total does not
establish coverage of every changed behavior, and a build does not prove visible
or lifecycle behavior. `ci-verify-and-summarize`, when available, can execute and
retain the existing checks without introducing another verification wrapper.

After a correction, reassess the resulting diff and repeat checks invalidated
by the change. Reuse credible evidence for matching inputs and environment.
Separate introduced failures from existing failures; do not hide either through
test exclusions, warning suppression, or weaker assertions. Record important
changes that remain untested and the reason instead of implying full coverage.

## Finish the Requested Work

Reconcile findings, corrections, and verification against the final revision.
Report the selected range and dirty-diff scope, meaningful improvements, actual
checks and their coverage limits, and unresolved work. Close only when required
in-scope work is complete or a remaining boundary is explicitly reported.

When publication is requested, use `git-publication-review` if available for the
final outgoing history, destination, push, and remote read-back. Keep that range
distinct from the development-review range and reassess after any new commit.
Review acceptance and local fixes alone do not authorize push, merge, or release.
