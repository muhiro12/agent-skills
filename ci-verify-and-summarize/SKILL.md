---
name: ci-verify-and-summarize
description: Run the repository's documented verification checks and review the current diff. Summarize actual shell or Xcode-native evidence, current-run artifacts, and verification gaps, including on a clean worktree.
---

# CI Verify and Summarize

Run the current repository's verification contract and review staged and unstaged
diffs. Release-risk judgment belongs to `release-risk-analyzer`, and publication
judgment belongs to `git-publication-review` when that work is requested; neither
is a mandatory extra step for ordinary verification. Explicit invocation applies
even when the worktree is clean. Keep explanations concise. Verification readiness
does not authorize a commit or push.

## Resolve the Real Contract

Read applicable repository instructions when present, README verification
guidance, actual build/test configuration, and relevant repository CI.
Resolve the repository root from Git rather than assuming the current directory.
Prefer the documented checks over filename conventions or obsolete wrappers.
Do not require `ci_scripts`, an aggregate shell, or `.build/ci/runs` when the
repository's current contract uses another coherent workflow.

For Xcode-native contracts, resolve the actual capabilities and required evidence
from the runtime inventory. Follow the repository's project/scheme/destination/
test-plan contract; preserve and restore changed Xcode selection. Use
available platform guidance when Apple evidence selection needs clarification.
A retained static-rule script is only one part of a mixed contract.
For Simulator runtime checks, follow [device-session ownership](../xcode-ui-smoke-auditor/references/device-session-ownership.md);
build-only checks do not need an interaction session.

For long-running checks, prefer completion notifications or 30-60 second waits
within host/tool limits. Do not poll unchanged status every second or repeatedly
read full logs. Keep raw output local and inspect failed-check excerpts and final
results; widen the excerpt when the diagnosis needs more context.

For a documented repository-relative bash check, pass its exact arguments to the
bundled helper from the target repository:

```bash
bash /path/to/ci-verify-and-summarize/scripts/run_verify_and_summarize.sh \
  -- bash scripts/check.sh --profile rules
```

Resolve the helper relative to the loaded skill rather than assuming the default
Codex home. Replace the example with an actual check selected from the repository
contract; do not infer it from the first README code block. Arguments are passed
literally, without shell evaluation. Explicit checks must be regular, non-symlink
repository scripts. Do not select a migration, formatter, or deployment as a check.
A broken selected command is a failure, not permission to choose another silently.

For compatibility, invocation without arguments still reads retained root
`AGENTS.md` for verify/check script names and known `ci_scripts` fallbacks.
That legacy parser does not preserve arguments, so prefer explicit argv. When
`AGENTS.md` is absent, default invocation executes no command, even if conventional
CI scripts exist. It reports unexecuted diff evidence; this is a valid repository
layout, not a request to recreate AGENTS or add a wrapper.

The helper creates and removes a temporary output file and executes the selected
repository command, whose own cache or artifact writes still apply. `--diff-only`
skips command execution and artifact inspection; use it after native checks or
another command form to collect the diff inventory. It reports shell verification
as unexecuted and never substitutes for native evidence. With no supported shell
entrypoint, the default also reports diff-only evidence rather than inventing a gate.

If the repository uses another command form, run the documented command directly
and perform the same evidence/diff review. Do not create a compatibility wrapper
just for this skill. If no reliable verification can be derived, report that
limit and continue the useful diff review instead of inventing a gate.

## Current Execution Evidence

Keep shell exit status/output, Xcode build/test results, and runtime/UI evidence
separate. Report only checks that actually ran; prior results need their exact
revision and context before reuse.

The shell helper compares direct child RUN directories before and after execution.
Only one new regular directory may supply current-run artifacts. Do not select
an old successful run when the current command failed or produced no artifacts.
Multiple new runs or symlinked roots/entries are ambiguous and must be reported.

For a valid current run, read `summary.md`, `meta.json`, the failed log only when
needed, and `commands.txt` only for diagnosis. Artifacts must be regular,
non-symlink files contained in that run. Never follow an artifact path outside it
or scan older `.build/ci/runs/<RUN_ID>` directories. Successful checks need no
artifact directory when output is the contract's evidence.

## Review and Report

Review both current diff and staged diff for introduced failures, unintended
behavior, persistence/identifier changes, missing behavioral checks, and scope
creep. Preserve unrelated edits. The helper collects a diff inventory; it does not
perform a semantic code review.

Report the actual commands/capabilities and result, important diff findings,
current-change versus pre-existing failures, and remaining limitations. Include
current-run paths only when such artifacts exist. A clean worktree is valid
context, not a reason to skip requested verification. Do not claim that required
verification completed when a boundary remains unverified.
The helper preserves command failure exits and rejects ambiguous or unsafe current-run
evidence. Paths, keywords, diff size, unstaged work, and warning samples alone do not
change a successful command into a failed gate. Report warnings as evidence for scoped
review; they do not automatically prohibit publication.

Do not edit source/configuration or run formatting as a side effect of this
verification-only workflow. If a user also asked for fixes, perform that authorized
implementation separately and verify the resulting change.
