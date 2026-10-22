---
name: sync-xcode-skills
description: "Export skills from the newest usable local Xcode and install managed copies in the shared user skill root. Use to discover, import, refresh, or synchronize bundled Apple guidance."
---

# Sync Xcode Skills

## Overview

Use this skill to keep Codex's local skill set aligned with the Skills that the
newest usable local Xcode exposes through its agent integration, including beta
releases. Honor an explicitly requested source Xcode.
Use the conversation's language for explanations.

The default installation root is `~/.agents/skills/external/xcode`, inside the
ignored external area of Codex's user skill location. Codex discovers these
nested skill folders without top-level links. Use `--skills-root` for an
explicit alternate managed installation directory; the argument remains the
actual destination, not the parent discovery root. Changing `CODEX_HOME` does
not redirect shared user skills. Keep the managed destination separate from
upstream repositories stored directly under `external/` and runtime-owned
plugin caches.

Migrate an existing top-level installation with the repository's
`scripts/migrate_skill_data.py --only external-skills` dry-run, then `--apply`
when authorized. It moves managed directories and regenerates catalog paths;
do not manually relocate generated content or edit the catalog.

Discover installed Xcodes from this skill directory before exporting:

```bash
python3 scripts/sync_xcode_skills.py --list-xcodes
```

The inventory checks `/Applications`, `~/Applications`, Spotlight, and the
current developer directory. It sorts by numeric Xcode version, then numeric
bundle build, newest first; app names, modification dates, the globally selected
Xcode, and which app is already running do not determine priority. For an
unindexed installation elsewhere, verify it and use `--developer-dir` explicitly.

Prefer a standalone export command in Codex; nested Python or shell wrappers
have failed to connect in some environments. Select both the command's developer
directory and the intended running Xcode; a bridge binary's path alone does not
establish which Xcode answered. Keep all selection local to the invocation.

## Workflow

1. Choose the first inventory entry unless the user requests another Xcode.
   Verify its version with per-command `DEVELOPER_DIR` and `xcodebuild -version`.
   Open that exact app if needed and allow initialization to finish. Do not change
   global `xcode-select` or switch the app build toolchain for this guidance sync.
2. Inspect that installation's bridge help and identify its live application
   process. Set `xcode_developer_dir` to its verified `Contents/Developer` path,
   `xcode_pid` to its current PID, and `xcode_export_dir` to a fresh temporary
   directory for this attempt. With the supported per-process selector, run the
   export as a standalone command:

   ```bash
   DEVELOPER_DIR="$xcode_developer_dir" MCP_XCODE_PID="$xcode_pid" xcrun mcpbridge run-agent skills export --output-dir "$xcode_export_dir" --replace-existing
   ```

   If export cannot find a running Xcode while the native integration can list
   its workspaces, distinguish shell access from an application failure. Use the
   current approval mechanism for the same standalone export when additional
   access is required; do not invent wrappers or persistent permission exceptions.
3. If the newest installation cannot export after resolving ordinary startup or
   access requirements, record the reason and try the next newest usable entry.
   Missing export support, an unusable installation, or a persistent connection
   failure can justify fallback; an older app already running cannot. Use a fresh
   export directory for each attempt. Do not silently substitute another version
   for an explicitly requested Xcode. If none succeeds, preserve installed skills.
4. Install only the successful, complete export with the same verified source:

   ```bash
   python3 scripts/sync_xcode_skills.py --install-only --developer-dir "$xcode_developer_dir" --export-dir "$xcode_export_dir"
   ```

   The installer requires an explicit source (`--developer-dir` or per-command
   `DEVELOPER_DIR`) for existing exports, verifies its version, and records that
   version consistently. Never infer an existing export's source from whichever
   Xcode is newest or globally selected. If provenance cannot be established,
   keep the export for inspection without installing it.
5. Report the source app, Xcode version/build, any fallback reason, exported and
   installed skill names, and the generated catalog path.

For Python-driven export, the script selects the newest discovered Xcode by
default, verifies its running process, and pins both `DEVELOPER_DIR` and
`MCP_XCODE_PID`. It stops on failure so fallback remains an explicit, reported
workflow decision. `--developer-dir` accepts an app or developer directory to
override discovery. By default, installed skill names are prefixed with
`xcode-skill-` to avoid collisions with local custom skills.
Treat the `xcode-skill-*` namespace within the managed destination as reserved
for this sync output. Update and prune only that directory; manually installed
repositories remain separate as siblings under `external/`.

## Design Position

Use the `xcode-skill-` prefix as a low-risk namespace boundary, not as a lower authority level. Xcode-provided guidance remains the preferred Apple/Xcode guidance when it matches the task.

The generated copies need Codex-compatible frontmatter, so the script rewrites installed `SKILL.md` metadata to the prefixed `name` and a Codex-readable `description`; the upstream body and bundled references remain unchanged. Reviewed discovery
summaries are keyed to the exact upstream metadata; the full original selection
guidance is retained in the installed body whenever a summary is used. The original Xcode skill name is preserved in each managed skill marker and in the central catalog.

After every install, the script writes a generated catalog under `state/` beside this skill:

```text
state/catalog.md
state/catalog.json
```

Apple-platform workflows should select matching Xcode guidance from the active
skill inventory. Use the catalog when discovery remains unresolved, and reuse a
current selection rather than reopening the catalog through every specialist.

## Important Behavior

- Prefer direct `xcrun mcpbridge run-agent skills export`. The older `xcrun agent skills export` wrapper can fail from Codex's embedded shell by trying to launch Xcode instead of connecting to the running instance.
- Prefer standalone export in Codex. Treat connection failures as evidence about
  that invocation, not a universal ban on selectors documented by the installed
  bridge. Verify the requested application and version before retrying.
- Xcode-exported frontmatter can contain fields Codex does not need, such as `when_to_use` or `effort`. The script rewrites installed `SKILL.md` frontmatter to `name` and `description`, preserving `when_to_use` in the full selection guidance.
- [Discovery summaries](references/discovery-summaries.json) contain concise, reviewed triggers and source metadata fingerprints. Update an entry only after reviewing the current exported description and triggers. Changed or unknown upstream metadata falls back to its full description, without mechanical truncation; changed reviewed entries emit a warning. Original names remain in the marker and catalog.
- Exported `name` values and `--name-prefix` must be filesystem-safe slugs. The installer rejects traversal-like values, duplicate installed names (including case-only duplicates), symbolic links in exported trees or install targets, and any resolved install target outside the skills root before changing managed skills.
- The script writes `agents/openai.yaml` and `.xcode-skill-sync.json` into each installed managed skill.
- Every exported skill is copied, normalized, and validated in a same-filesystem staging directory under the skills root before any existing managed skill is moved. Existing skills are moved to a transaction backup before staged copies are swapped into place; any staging, swap, prune, or catalog failure rolls the managed set back.
- The script writes a generated central catalog for surrounding skills to discover the current Xcode-provided skill set without depending on stable external Xcode naming.
- Stale managed skills are moved into the transaction backup only after all staged installs have swapped successfully. `state/catalog.json` and `state/catalog.md` are prepared together and installed with atomic file replacements; a failure restores both catalogs and the prior managed skill set before backups are removed.
- The Xcode version is captured once at the start of a run and reused for every managed marker and both catalog representations so one sync cannot report mixed toolchain versions.
- When copying exported skill directories, the script ignores generated or local-only directories and files such as `.build`, `build`, `DerivedData`, `.git`, `.swiftpm`, `Pods`, `Carthage`, `.DS_Store`, and `__pycache__`.
- A successful export is treated as the desired Xcode-provided skill set. Managed `xcode-skill-*` directories that are absent from the current export are pruned so Xcode-side deletions and renames are reflected locally.
- If the export returns no skills, the script exits with an error instead of pruning installed skills.
- Any unmanaged `xcode-skill-*` path, including a directory with a missing, malformed, non-object, symlinked, or identity-mismatched marker, causes an error before install or prune begins. This keeps the reserved namespace easy to reason about: every `xcode-skill-*` directory is either managed by `sync-xcode-skills` or must be resolved manually before syncing.

## Useful Options

```bash
python3 scripts/sync_xcode_skills.py --list-xcodes
python3 scripts/sync_xcode_skills.py --install-only --developer-dir "$xcode_developer_dir" --export-dir "$xcode_export_dir"
python3 scripts/sync_xcode_skills.py --name-prefix xcode-skill-
python3 scripts/sync_xcode_skills.py --state-dir state
```

Use `--export-only` when diagnosing Xcode's export output without installing anything into Codex.
Use Python-driven export options such as `--export-only` only outside Codex or when specifically diagnosing why Python subprocess export differs from top-level `xcrun mcpbridge`.
