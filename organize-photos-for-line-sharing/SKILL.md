---
name: organize-photos-for-line-sharing
description: "Organize Apple Photos into outbound LINE-sharing monthly albums. Use for source classification, source-aware date and orientation correction, exact album verification, and visual reporting without deleting media."
---

# Organize Photos for LINE Sharing

Treat the Photos library as the irreplaceable source. Build outbound sharing albums; do not treat inbound LINE downloads as photos to send back.

## Non-negotiable contract

- Never delete a photo or video. Never invoke Photos `delete` on a media item, Recently Deleted, direct Photos-library database writes, or filesystem mutation inside a `.photoslibrary` bundle.
- Never use a removal operation whose effect on the library is uncertain. Rebuild an album and retain its old version under a backup name instead.
- Never change a date from filename, dimensions, or a search result alone. Use dimensions only to find orientation candidates, then judge visible content before rotating.
- Never change the date of a self-captured or otherwise trusted non-LINE original. Date correction is exclusively for confirmed LINE downloads.
- Never apply the landscape preference for self-captured originals to confirmed LINE downloads. Rotate LINE media only when visible content is clearly sideways.
- Never change the date or orientation of an item whose source classification is unresolved.
- Never delete exported review copies unless the user explicitly approves deleting those exact temporary copies.
- Stop immediately if the library media count decreases. Investigate before any further mutation.
- For audit, explanation, or feasibility requests, remain read-only.

## Establish the contract

Confirm or infer only when unambiguous:

1. Set the inclusive date range and monthly album naming convention, normally `YYYYMM`.
2. Determine whether albums contain still images only. Default to still images when the user says photos or images; report excluded videos.
3. Record that the album purpose is outbound LINE sharing. Classify each item before mutation as `outbound_original`, `confirmed_line`, or `unresolved_or_other`. Only `outbound_original` items belong in the monthly albums.
4. Record the requested date policy. Treat dates on `outbound_original` items as trusted and immutable. For `confirmed_line` items only, prefer an exact day, fall back to the month's last day, place them in the 23:50 band, and preserve source order.
5. Record the source-aware rotation policy. Actively review `outbound_original` portrait images with landscape as the default intent. Review `confirmed_line` orientation conservatively without a landscape preference.
6. Leave `unresolved_or_other` items out of the albums and make no date or orientation change until their source and purpose are resolved.
7. Use a deterministic backup suffix such as `_LINE_INCLUDED_BACKUP_YYYYMMDD`. Never overwrite an existing backup.

Ask before mutation when any item above would materially change the result.

## Use the supported surfaces

- Read the active Computer Use tool instructions before inspecting or operating the Photos UI; use a matching installed skill when available.
- Prefer Photos AppleScript for read-only metadata, album creation, album addition, and album renaming when the user permits programmatic work.
- Use the Photos UI for visual judgment and rotation because Photos AppleScript does not expose rotation.
- Read [references/photos-automation.md](references/photos-automation.md) before composing Photos AppleScript or changing an album.

## Execute the selected work

For library inventory, source classification, date/orientation review, album
updates, or final reconciliation, read [run workflow](references/run-workflow.md).
Keep its before/after evidence and exact-set verification. For explanation-only
requests, describe the relevant behavior without starting a library inventory.
Read-only audits may inventory and prepare reports but must not apply the
workflow's mutation steps.

## Generate the visual HTML report

Generate a visual HTML report after every completed run, including read-only or no-change runs. If the run is blocked after collecting evidence, generate a blocked report instead of omitting the report.

1. Create `run-report.json` following [references/report-schema.md](references/report-schema.md).
2. Keep the report outside every `.photoslibrary` bundle. Use a user-requested output directory, a task artifact directory, or a task-specific temporary directory.
3. Generate the self-contained report:

```bash
python3 scripts/generate_html_report.py work/run-report.json work/photos-line-sharing-report.html
```

4. Render or open the HTML at a normal desktop width and a narrow width. Fix clipped labels, unreadable bars, missing sections, or unescaped content.
5. Present the HTML report to the user and retain the JSON beside it so a future run can compare results.

The report must make these values visually scannable:

- final count for each monthly album;
- confirmed LINE downloads excluded by month and in total;
- unresolved candidates omitted from sharing albums;
- self-captured portrait candidates, active rotations, clearly retained portrait images, and unresolved orientation items;
- confirmed LINE items reviewed conservatively, rotations of clearly sideways LINE media, unchanged LINE items, and unresolved LINE orientation items;
- confirmed LINE date corrections and an explicit non-LINE date-change count of zero;
- total rotations, split between self-captured originals and confirmed LINE downloads;
- missing, extra, and duplicate verification results;
- library count before and after, explaining any synchronized arrivals;
- backup album names;
- the explicit statement `写真・動画の削除: 0件`.

Never claim the library count was unchanged when iCloud synchronization added media during the task.

## Resources

- Use [scripts/analyze_inventory.py](scripts/analyze_inventory.py) for deterministic candidate classification and monthly-set planning. It never writes to Photos.
- Use [scripts/make_photo_contact_sheets.swift](scripts/make_photo_contact_sheets.swift) to create review sheets from exported copies. It never modifies input images.
- Use [scripts/generate_html_report.py](scripts/generate_html_report.py) to create the required self-contained post-run report.
- Use [references/photos-automation.md](references/photos-automation.md) for Photos scripting patterns, API limitations, and failure recovery.
- Use [references/report-schema.md](references/report-schema.md) when assembling the post-run report manifest.
