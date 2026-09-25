# Photos run workflow

Read the parent SKILL.md first. Commands below run from the loaded skill directory;
`work/` refers to its ignored task artifacts. Follow only the operations requested
by the user, and retain source classification before every mutation.


### 1. Capture a preflight snapshot

1. Read the Photos footer totals and iCloud sync status through Computer Use.
2. Record `count of every media item` through Photos AppleScript.
3. Record exact names, counts, and media IDs for target monthly albums and any pre-existing backup albums.
4. Wait for active synchronization to settle when practical. Treat count increases during the task as possible new iCloud arrivals, never as automatic evidence of an error.
5. Create a task-specific temporary directory with `mktemp -d`. If retaining artifacts under this skill, use its Git-ignored `work/` directory. Keep inventories, media IDs, exports, contact sheets, and run reports out of version control. Do not target a broad directory for cleanup.

### 2. Inventory without mutation

Export these tab-separated fields for each item: year, month, day, hour, minute, second, filename, Photos media ID, width, and height. Filter the requested date range outside Photos; Photos date predicates can be unreliable.

Run the deterministic analyzer first with UUID names treated as candidates:

The examples use `work/`; create it before use or substitute the task-specific temporary directory.

```bash
python3 scripts/analyze_inventory.py work/inventory.tsv \
  --start-year 2026 \
  --uuid-policy candidate \
  --output work/plan.json
```

Use filename evidence as follows:

- Treat an explicit `LINE_` prefix as strong LINE-download evidence.
- Treat a UUID-style filename as a candidate, not proof. Inspect representative originals or contact sheets and correlate date clusters, source order, file type, and nearby non-LINE originals.
- UUID-style names and a 23:50 timestamp cluster are not specific to LINE. Confirm the source convention for the current library from independent visual and contextual evidence on every run.
- Keep generated assets, screenshots, and other downloads separate when visual evidence shows they are not from LINE.
- Exclude unresolved possible LINE downloads from outbound sharing albums while leaving them untouched in the library.
- Treat the analyzer's non-LINE `outbound` IDs as candidates until visual and contextual evidence confirms that they are self-captured originals intended for sharing. Do not add generated assets, unrelated downloads, or unresolved sources merely because they are not LINE files.

After validating the convention, rerun with `--uuid-policy line`, or pass reviewed IDs through `--line-id-file`. Preserve the resulting JSON manifest as the dry-run evidence.

### 3. Review dates and sequence for confirmed LINE downloads only

Only plan a date write for confirmed LINE downloads.

1. First require that every proposed date-change ID is present in the confirmed LINE set and absent from the outbound-original set. A proposed date change for an outbound original is a blocking error.
2. Infer the target day from visually similar, correctly dated non-LINE photos and surrounding sequences without modifying those reference photos.
3. If only the month is defensible, use that month's final calendar day.
4. Preserve the original minute ones digit and seconds where that maintains order: set the hour to `23` and replace only the minute tens digit with `5`.
5. Verify that the proposed timestamps remain strictly nondecreasing in the confirmed source order. Resolve collisions with the smallest permitted adjustment; otherwise skip the ambiguous item.
6. Produce a before/after manifest before applying any date change. Explicitly record `non_line_date_changes: 0`.
7. Re-read every changed date after applying it. Do not infer success from the dialog closing.

LINE date correction is independent from outbound album assignment. A corrected LINE date must never determine an outbound album destination; album assignment uses only the unchanged capture dates of confirmed outbound originals.

### 4. Review orientation according to source

Export review copies, never originals out of the library, into the task-specific temporary directory. Generate contact sheets with:

```bash
swift scripts/make_photo_contact_sheets.swift work/exported-images work/contact-sheets
```

#### Self-captured outbound originals: active correction

Inspect every self-captured still image in scope whose displayed dimensions are portrait, plus any landscape-dimension image whose content appears sideways. Treat portrait dimensions as a review trigger and landscape as the user's normal intended result, not as sufficient evidence for a blind rotation.

Classify each portrait candidate:

- `rotate`: one 90-degree direction makes people, horizons, architecture, or text naturally upright and yields the intended composition. Choose clockwise or counterclockwise from visible content. For portrait-aspect originals, prefer the credible landscape result.
- `keep_portrait`: positive visual evidence shows intentional portrait composition, such as a deliberate full-height subject, vertical artwork, or a sequence consistently framed upright.
- `unresolved`: neither direction is defensible. Leave it unchanged, but report it prominently for manual review.

Do not preserve portrait merely because the content is currently upright; require positive evidence that the composition is intended to remain vertical. Do not rotate merely because Photos accessibility text says `90度回転`; that can describe valid metadata orientation.

#### Confirmed LINE downloads: conservative correction

Do not use portrait dimensions alone as a review trigger or assume that landscape was intended. The sender may have deliberately created a portrait photo, screenshot, document, illustration, or graphic.

- Review a confirmed LINE item for rotation only when visible content or its surrounding sequence gives concrete evidence that it is sideways.
- Rotate only when one 90-degree direction clearly restores the intended upright view. Do not rotate merely to make the result landscape.
- If the current orientation is plausible or the direction is uncertain, leave it unchanged.

Do not rotate `unresolved_or_other` items. After any rotation, refresh the Photos UI and verify that the displayed result is visibly upright before continuing. Record the source class, media ID, original dimensions, chosen direction, final dimensions, and decision evidence. Count self-captured and LINE rotation decisions separately.

### 5. Build outbound monthly albums

Compute each album's expected set as:

`confirmed self-captured outbound originals in their unchanged capture-date month`

Confirmed LINE downloads, unresolved LINE candidates, generated assets, other downloads, and unresolved sources remain outside the outbound albums. LINE date correction must never cause an item to enter an outbound album.

Then apply conservatively:

1. Leave an existing monthly album unchanged when its exact ID set already matches.
2. For a changed month, create a uniquely named temporary album.
3. Add expected media IDs in batches of at most 50. Newly created albums may need a small first batch before larger additions.
4. Verify exact ID equality: expected count, actual count, missing `0`, extra `0`, duplicate `0`, confirmed LINE `0`, unresolved LINE candidate `0`.
5. Abort if the intended backup name already exists.
6. Rename the old album to `YYYYMM_LINE_INCLUDED_BACKUP_YYYYMMDD`.
7. Rename the verified temporary album to the original `YYYYMM` name.
8. Retain the backup. Do not delete it as part of this skill unless the user separately and explicitly asks to remove only the album container.

Do not rebuild unaffected months merely for consistency.

### 6. Reconcile synchronization and verify

1. Re-read the library total and Photos footer after album changes.
2. If the library count increased, identify the new items individually. Add only newly confirmed self-captured originals to the applicable outbound month, using their existing capture dates.
3. If the library count decreased, stop and investigate immediately.
4. Re-read every requested monthly album ID set.
5. Require missing `0`, extra `0`, duplicate `0`, confirmed LINE `0`, and unresolved LINE candidate `0` for every outbound album.
6. Confirm that no media date or rotation changed beyond the approved, source-classified manifest. Require zero date changes for non-LINE originals.
7. Confirm the final Photos sync status through Computer Use.
