# First-pass Apple verification

Use this reference only when establishing a new contract from Apple project and
Swift package surfaces. Existing contracts normally need only the entrypoint.

Inspect the current repository before choosing a shape: `AGENTS.md`, Xcode
projects/workspaces, `Package.swift`, CI, test plans, companion targets, and any
retained lint or repository rules. Discover actual schemes and eligible destinations
through available native capabilities; do not infer them from folder names.

Map shared behavior tests separately from app/extension builds. Identify which
runtime or visual checks are needed for lifecycle, data, or UI integration and
which can be deferred until that boundary changes. Avoid a full device matrix
when representative targeted evidence proves the requested work.

Write a concise repository-local contract containing:

- Concrete project/package paths and the relevant schemes, destination families,
  test plans or identifiers.
- Which boundary each check proves, with source/build/runtime distinctions.
- Selection capture and restoration requirements from the parent skill.
- Any retained shell checks and how to invoke them from a fresh clone.

Use a sibling repository read-only only when requested or a missing pattern
actually needs a reference. Adapt reusable intent; do not copy app-specific targets,
finance semantics, local paths, or obsolete build wrappers. The current repository
and current official guidance remain the baseline.

Add helpers only for responsibilities the active native integration does not
cover. Preserve existing formatter/linter choices. If heavy checks are attached
to commit hooks, move them only within the authorized workflow change, keeping
the resulting checks directly runnable and documenting the behavior change.

Run the new checks and restore any changed Xcode selection. If a required capability
is unavailable, document the concrete gap and a justified official/repository fallback;
do not call an unexecuted contract verified. Bootstrap does not authorize signing,
account changes, release operations, or global tool installation.
