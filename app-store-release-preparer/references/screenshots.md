# Screenshot Preparation

## Choose Coverage

Inventory existing sets within the authorized scope and review available images
for composition, ordering, representative content, and language. Record their
actual provenance; a Store-rendered reference is not necessarily the original
upload bytes.
For local-only work, use saved resources/configuration and defer remote checks.
Use the smallest device/display coverage that satisfies current Apple rules
for the app's supported families. Do not assume one iPhone size also covers
iPad or companion platforms. Record any retained older size sets that may
continue to show the previous design. Omission must not imply deletion.

When the user asks to reproduce a previous version, freeze its per-device screen
identity, order, orientation, count, presentation, selection, and scroll region
before capture. A screen name alone does not identify the same composition.
Record exact requirements separately from best-effort sample-data matching;
apply the same composition to added locales.

Choose a concise set of real product screens that explains the current app.
Use the existing photos and fixtures as references when suitable. Localize
visible UI and sample content for each selected Store locale; translated file
names or captions alone do not establish language coverage.

## Reproducible Capture State

Repeatability comes from controlled fixtures and initial state, not from Preview
or Simulator alone. Reuse a small app-local capture setup with production views;
share its data and state definitions across capture methods when useful:

- Explicit screen identity and initial tab, navigation, sheet, and selection state;
  preserve the real screen hierarchy, navigation controls, and surrounding chrome.
- Isolated data, such as an in-memory store or capture-only temporary container,
  disabled cloud synchronization, and isolated preferences or session snapshots.
  Neither Preview mode nor a simulator alone establishes this isolation.
- Representative, localized records with deterministic ordering and stable visible
  dates. Control the clock where relative dates matter; avoid random identifiers
  or hashes that affect visible content. Recreate locale-dependent fixtures when
  changing language rather than reusing cached source-language records.
- Local photo assets with known provenance, using existing Store photos when
  suitable. Avoid capture-time downloads and symbol placeholders in photo-led
  screens. Keep development-only assets out of the shipping bundle when practical.
- Controlled services with no production sync, real purchase flow, test ads,
  debug overlays, or unrelated network side effects. Represent a real supported
  product state; do not hide shipping behavior solely to improve its Store image.

Keep fixtures and screenshot composition in the repository, not duplicated in
this skill. Reuse existing injection points and sample data before introducing
a framework. When preparation requires source changes, route scoped, authorized
changes through suitable available platform specialists; otherwise hand off
concrete gaps. Do not
silently broaden capture work into app architecture or shared-package changes.

## Select and Qualify a Capture Method

Retain an existing, verified capture route unless there is evidence that a change
helps the requested work. Do not prescribe Preview-first or Simulator-first for
every repository, require both implementations, or introduce UI test targets
solely because this skill is in use.

- **SwiftUI Preview:** Useful when existing screen-level previews accept the
  desired state directly and reproduce the production hierarchy and environment.
  It can avoid navigation, but still executes code and needs a compatible runtime;
  iOS previews use simulator devices. Use `xcode-preview-auditor` when available.
- **Normal app execution:** Useful when existing capture automation is reliable
  or the image depends on actual app presentation, system UI, or lifecycle state.
  Fixtures, launch arguments, or existing routes can avoid repeated manual data
  entry and navigation here too. Use `xcode-ui-smoke-auditor` and active device
  guidance when available for Simulator or device capture.

When choosing a new route or proposing a switch, run a bounded pilot on the
representative screens, device families, and locales required by the task.
Check repeated end-to-end success, visual fidelity, actual output dimensions,
and the available export automation. Compare equivalent fixture-backed routes,
not a prepared Preview against an unnecessarily manual Simulator workflow.
Include setup, cold/warm rendering, switching, export, inspection, failure
recovery, and expected maintenance in the decision. Distinguish observed costs
from estimates; a single successful render does not establish a speed advantage.
Existing applicable evidence can replace a new comparison. If the evidence is
insufficient, retain the verified route or mark the candidate provisional.

Verify the actual rendered device, orientation, locale, and surrounding chrome.
For Preview, the Canvas device can differ from Xcode's run destination, and a
view-only hierarchy can omit navigation or presentation supplied by the app.
Check localized sample records as well as labels: a locale override may not
recreate strings resolved during cached fixture initialization.

Use a verified original-resolution exporter. For Preview this may be Canvas
Export Screenshot; an integration's inspection snapshot can instead be resized
or transparent. Do not substitute a desktop/canvas crop or assume an ordinary
Simulator screenshot captures the Preview framebuffer. Inspect the exact file.

Choose per screen when warranted and record the mechanism and rationale. Keep
app, fixture, and tooling failures distinct; retry after a relevant change and
do not generalize one project's timeout into a method-wide reliability claim.
A substitute route must reproduce the same intended state faithfully.

Report image export, repeated capture reliability, comparative efficiency, and
remote acceptance as separate claims. A local export needs no trial upload;
Store processing remains deferred until the authorized upload phase. Preview
captures do not prove live navigation or lifecycle behavior, and neither capture
method alone establishes release readiness.

## Control Data and Capture

Inspect existing data before reuse: simulators may contain prior test records,
personal content, debug labels, or stale installations. Prefer an isolated
capture simulator and existing representative fixture route when appropriate.
Creating bounded sample data on that isolated device is part of a requested
screenshot-preparation task. Do not erase or reseed a shared/user container.
Avoid production account synchronization and real purchases for staging images.

Set language, region, orientation, appearance, and text size explicitly where
needed, preferably before first launch. Confirm what rendered, including sample
content, rather than trusting configuration alone. Record the installed build
or source revision; recapture affected screens after visible code changes.
Serialize shared Xcode and device state, close sessions started for capture,
and restore selections according to the repository's verification contract.

Keep original captures and review the exact upload files after any conversion.
Check the intended screen, representative data, language, legibility, clipped
or truncated important text, overlap, debug/private content, image format,
pixel dimensions, alpha restrictions, order, duplicates, and per-set count.
Do not enlarge a low-resolution inspection thumbnail to satisfy Store sizes.
Before reporting a missing control or clipped text from a thumbnail, inspect
the original-resolution file or a lossless detail crop. If still uncertain,
compare the same screen reached through normal navigation. Distinguish capture
state defects from shipping layout defects, and recapture affected images
after an authorized source correction.
Use content-preserving conversion if required. Do not generate replacement UI
or alter product behavior in an image to hide a rendering defect.

## Upload and Resume

Retain locale/display/screen identity, source revision, capture method/device,
fixture state, file paths, dimensions, and checksums in the private ledger.
Use the current Apogee directory format and retain exact source upload bytes
so a later replacement can satisfy its recovery requirements.
For local-only work, stop with reviewed artifacts and the remaining capture or
acceptance gaps; do not use an upload as a prerequisite for completing that task.

Inspect the dry-run for both intended replacements and preserved remote sets.
Follow the installed version's recovery policy; processed/resized Store images
cannot be treated as verified originals merely because they look identical.
Missing originals may leave a replacement deferred while new locales proceed.
If the installed tool supports upload-first replacement without originals,
identify the exact affected sets and irreversible loss of the old composition.
A CLI acknowledgement does not override the active approval controls. Honor
existing explicit consent to that loss; if approval review rejects the action,
finish recoverable sets and request the missing consent for the concrete plan.
After consent, refresh the plan and require new-image verification before deletion.
Keep private recovery state across retries. Use fresh plans after remote
changes, and verify completion, checksums and order before claiming success.

## Retain Useful Artifacts

Keep reproducible fixture code and capture instructions in version control.
Keep the exact uploaded files, manifest, source revision, comparison gallery,
verification results, and recovery originals/journals in durable private storage.
An ignored directory is not a backup; report its location and backup limits.
Remove only task-owned disposable intermediates after checking gallery and
manifest references. Do not delete recovery material merely because apply passed.
If capture exposed a production fix, report whether the selected distribution
build actually contains it separately from screenshot acceptance.

## Official Guidance

- [Canvas interaction and screenshot export](https://developer.apple.com/documentation/xcode/interacting-with-previews-in-the-canvas)
- [Preview device](https://developer.apple.com/documentation/swiftui/previewdevice)
- [Shared Preview context](https://developer.apple.com/documentation/swiftui/previewmodifier/)
- [Previewing localizations](https://developer.apple.com/documentation/xcode/previewing-localizations)
- [Device screenshot capture](https://developer.apple.com/documentation/xcode/capturing-screenshots-and-videos-from-devices)
- [UI automation across configurations](https://developer.apple.com/videos/play/wwdc2025/344/)
