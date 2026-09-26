## Script

Use `scripts/audit_xcstrings.py` to audit catalogs, apply safe catalog-local fixes, and separate code-side stale follow-ups from deletable stale entries.

```bash
python3 scripts/audit_xcstrings.py   --project-root /path/to/repo   --required-locales en,ja,es,fr,zh-Hans   --format markdown
```

Useful options:

- `--catalog`: Limit the run to specific catalogs.
- `--source-root`: Limit static-reference analysis to the owning target directories.
- `--required-locales`: Override expected locale set for selected catalogs.
- `--seed-missing-locales`: Create missing locale entries from source-locale structure.
- `--prune-unused`: Remove keys with zero static literal matches.
- `--prune-stale-unused`: Remove only stale keys with zero static literal matches.
- `--normalize-stale-referenced`: Clear stale markers from keys that still have valid static references.
- `--translation-patch <json>`: Validate a Codex-generated translation patch file or inline JSON.
- `--apply-translations`: Apply a validated translation patch and mark patched payloads translated.
- `--apply`: Write changes in place (without this flag, mutations are dry run).
- `--format json`: Emit machine-readable output.
