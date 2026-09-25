---
name: app-store-release-preparer
description: Prepare an App Store release with Apogee by creating or reusing the version, entering localized What's New, and updating descriptions and screenshots when warranted. Use for Store resource preparation; submission and publication require their own task scope.
---

# App Store Release Preparer

Coordinate Store resource preparation through Apogee. Produce reviewable local
resources and verify authorized remote updates. This is an initial workflow:
choose the smallest useful scope and record unresolved choices or tool gaps.

For screenshot-only or local feasibility work, follow only the relevant resource
path. Do not require authentication, a live Store inventory, version creation,
or upload trials when the user has excluded them. Use available local references
and mark remote state and acceptance as unverified.

## Establish the Target

Read repository instructions, current Git state, release configuration, and
existing Store resources. Resolve app identity, platform, target version,
candidate revision, previous release baseline, and supported Store locales.
Use existing locale mappings; do not infer regional Store identifiers solely
from language codes in a string catalog. Ask only about material ambiguities
that existing configuration and the user's instructions do not resolve.

Inspect the repository's Apogee integration, resolved version, command help,
and matching documentation. Assume Apogee is available, but verify each needed
capability in the actual executable. Do not assume a local patched dependency
is equivalent to a published release. Use configured authentication without
printing credentials or signed URLs.

Read the live target version and metadata before planning remote changes. Preserve
unrelated fields, local edits, and remote resources outside the selected scope.
Keep a compact, private preparation ledger with a row for the version and each
locale/resource: proposed action, local artifact, remote verification, and any
blocker. Use `prepared`, `applied and verified`, `unchanged`, or `deferred`.
Store short-lived plans, captures, and recovery material outside public files.

## Prepare the Resources

1. **Version:** Reuse the matching remote version when present. Otherwise use
   Apogee's version-creation plan and apply within the user's authorization,
   then read back the app, platform, version, and state. A local version setting
   or successful authentication does not establish a remote version record.
2. **What's New:** Use the available `app-store-release-notes-writer` skill for
   the resolved Git range and locale coverage. Review user-visible claims
   against the actual candidate. Write finalized text into the repository's
   Apogee resource layout; a generated draft or source-language copy is not a
   completed translation. Do not invent a release date when it is undecided.
3. **App description:** Compare existing localized copy with current behavior.
   Update when features, positioning, or a major redesign make it stale; retain
   accurate copy otherwise. Keep the evergreen product introduction distinct
   from What's New. Preserve established feature names and accurately state
   paid, device, OS, or regional limitations. Check current field limits and
   localize every changed field for the selected Store locales.
4. **Screenshots:** Refresh when visible changes make the Store imagery stale,
   language coverage is missing, or the user requests it. Otherwise document
   the decision to retain them. Prioritize reproducible capture state; select
   Preview or normal app execution using repository-specific evidence rather
   than a universal method preference. Read [screenshot preparation](references/screenshots.md)
   before choosing coverage, capturing, or replacing images.

If a specialist skill is unavailable, perform its bounded task using repository
conventions and current official guidance. Do not require a broad app audit,
source refactor, or full release qualification merely to edit Store resources.
Use relevant available platform specialists for necessary source fixes when
already authorized; otherwise preserve the finding and finish independent work.

## Apply and Verify

A request to perform release preparation authorizes the named preparation
operations; a draft-only or review-only request does not authorize remote writes.
Honor authorization already given in the conversation. Before each write,
inspect the concrete dry-run for the intended app, version, fields, locales,
and screenshot sets. Use the current CLI's explicit apply and confirmation
mechanisms. Ask only when the plan requires a material choice or authority
not already supplied. Do not add a blanket approval checkpoint to every step.

Apply in dependency order: version first, then eligible text and image changes.
Read back changed text exactly across the selected locales. For screenshots,
verify processing completion, checksums, count, and order. Run a fresh dry-run
and require zero differences for each completed resource. Report completion
only for the verified scope; excluded or blocked locales remain visible.

After an error, inspect remote state and retained recovery records before
retrying. Preserve completed writes and owned reservations; do not assume
rollback or infer reservation ownership from a filename. Follow the current
Apogee recovery and destructive-change requirements. A missing original or an
upload failure does not authorize weakening those requirements.

For a matching tool failure, consult [bounded Apogee incident notes](references/apogee-incidents.md).
Recheck the installed version and linked Issue before treating an old incident
as a current blocker. Defer only the affected operation, retain its artifacts,
and continue independent resources. Report a reproducible Apogee bug or request
to an existing or new Issue when authorized, excluding private account data.
Apogee repair, dependency upgrades, and public publication are distinct work;
do not silently make disposable dependency patches the normal preparation path.

## Handoff

Return a concise summary of the version, revision/range, locales,
text changes, screenshot coverage and capture method, actual remote verification,
and deferred work with its next concrete step. Link reviewable local assets.
Use a small status table when several locales or resources differ.

Store preparation does not itself attach a build, submit for review, release the
app, change pricing, or complete privacy declarations. Perform those only when
the user's task includes them. Distinguish asset acceptance from archive,
TestFlight, device, purchase/restore, and distribution evidence.

## Official References

Consult current requirements when the target's eligibility or asset rules matter:

- [Create a new version](https://developer.apple.com/help/app-store-connect/update-your-app/create-a-new-version/)
- [Upload previews and screenshots](https://developer.apple.com/help/app-store-connect/manage-app-information/upload-app-previews-and-screenshots/)
- [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications)

SwiftUI Preview rendering below is a capture option, not App Store preview video.
