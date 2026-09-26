---
name: string-catalog-maintainer
description: "Audit and repair Xcode string catalogs (.xcstrings). Use for stale-key cleanup, missing locale coverage, or validated translation patches; preserve placeholders and distinguish dynamic references before pruning."
---

# String Catalog Maintainer

Audit and maintain selected `.xcstrings` files within the requested scope.
A read-only audit stays read-only; a repair request authorizes the corresponding
catalog fixes after validation. Source-code changes require their own scope.
Apply the repository's locale policy and established product terminology.

## Select the Work

Find catalogs with `rg --files <repo> | rg '\.xcstrings$'`. Derive required
locales from target behavior, explicit policy, or the script's sibling-catalog
inference. Prefer relevant Xcode guidance already selected from the active skill
inventory. Consult the generated Xcode catalog only if discovery remains
unresolved; do not repeat a current lookup through each specialist.

Run the repository's catalog auditor when available, otherwise:

```sh
python3 /path/to/string-catalog-maintainer/scripts/audit_xcstrings.py --project-root <repo> --format json
```

Scope static reference analysis with `--source-root` for target-owned catalogs;
use `--required-locales` for an explicit policy. Treat unused matches as candidates,
not proof that runtime-generated keys can be deleted.

Read only the procedure needed for the requested operation:

- For stale or unused key deletion, read [pruning](references/pruning.md) before
  mutating. It covers count cross-checks and strong versus weak references.
- For missing locales or translation repair, read
  [translations](references/translations.md) before creating or applying patches.
  Seeding source strings alone does not complete translation work.
- For invocation options, consult [script options](references/script-options.md).
  Audit-only work needs neither mutation procedure.

## Safety / Guardrails

- Keep diffs minimal; do not rewrite unrelated tables.
- Keep selected catalogs and source roots inside the resolved project root. Reject symbolic links in selected or discovered paths instead of following them outside the repository.
- Validate every selected catalog and every translation patch before committing any file. Stage all changed catalogs first and treat a multi-catalog update as one transaction: either every catalog is atomically replaced or the original set is restored.
- Preserve existing JSON whitespace conventions when rewriting catalogs, including indentation style, line ending style, and whether the file ends with a trailing newline.
- Preserve placeholders, plural structure, punctuation, and `shouldTranslate: false` semantics.
- Preserve proper nouns and established feature names unless an official localized name is known or the user explicitly asks for a translation.
- Never auto-prune keys known to depend on generated/runtime composition without source verification.
- Keep source-code fixes out of scope for this skill unless the user explicitly asks to expand beyond catalog maintenance.
- When a `stale` key still has references, report it for later code-side repair instead of changing source files here.
- When a stale key has only weak interpolation-derived references, report it separately; do not normalize or delete it automatically.
- Avoid scanning generated directories recursively unless explicitly required.

## Verify and Report

After edits, rerun the audit and the repository's applicable verification.
Confirm intended key/locale/task count changes, preserved formatting and
placeholders, and that referenced stale keys were not deleted. For pruning,
resolve any mismatch between raw stale markers and parsed stale-key counts
before proceeding.

Report the selected catalogs, relevant findings or actions, checks performed,
and unresolved dynamic-key or source-side follow-ups. Include translation tasks
only for locale work and deletion evidence only for cleanup; omit empty sections.
