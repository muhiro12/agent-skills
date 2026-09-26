# Stale and Unused Key Cleanup

3. Cross-check stale markers.
- Independently run `rg -n '"extractionState"\\s*:\\s*"stale"' <catalogs-or-repo>` when stale cleanup is requested.
- Confirm the raw `rg` count matches each catalog's `raw_stale_marker_count` and that `raw_stale_marker_count == stale_key_count`.
- Stop and investigate before pruning if the counts disagree.

4. Protect against dynamic-key false positives.
- Treat unused keys as candidates only.
- Validate call sites for dynamic key construction before deletion.
- Treat `stale_weak_referenced_keys` as report-only unless the user explicitly asks for deeper source-code investigation.

5. Apply candidate -> verification -> delete flow.
- Default to applying catalog-only fixes within this skill once verification is complete.
- Candidate: identify deletable keys with zero static references.
- Verification: inspect affected call sites and large diff areas.
- Delete: run `--prune-unused --apply` only after verification.
- For `stale` cleanup, prefer `--prune-stale-unused --apply` so only stale keys with zero scoped references are removed.
- If a key is in `stale_strong_referenced_keys` or `stale_weak_referenced_keys`, do not delete it in this skill. Report it as a code-side follow-up, leave source files untouched, and use `--normalize-stale-referenced --apply` only after the separate code fix when the catalog should keep that key.
