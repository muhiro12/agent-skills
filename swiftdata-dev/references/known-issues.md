# Diagnostic Scenarios and Community Reports

Use the methods below to investigate a matching symptom. Proposed checks are
not completed reproductions or universal workarounds. The separately attributed
community report retains its historical limits. Follow linked Apple guidance
and verify the actual schema, store, SDK, and runtime.

## Store selection during Core Data adoption

When records appear absent, compare the old and new resolved store URLs before
assuming migration lost data. Confirm the intended store and schema compatibility;
do not hard-code another application's filename. Test with a preserved historical
store and verify values and relationships after opening it. See [Apple's adoption
guidance](https://developer.apple.com/videos/play/wwdc2023/10189/).

## CloudKit startup during migration

**Observed problem.** A [January 2024 report](https://developer.apple.com/forums/thread/744491)
describes failure after adding CloudKit when users skipped older app releases.
Validation complained about attributes without optionality or defaults despite
the destination schema supplying them. The proposed startup-order cause was
the reporter's diagnosis, not an Apple-confirmed explanation.

**Attempts and limits.** The author reported that retrying initialization with
CloudKit disabled permitted migration, then enabling sync on the next launch
worked. In March 2024 the same author reported that this workaround crashed
with custom migration on iOS 17.4 (`FB13694972`). Later participants reported
mixed results from migrating locally before creating the synced container.
No current resolution or before/after verification is established here.

**When investigating.** Match the historical schema, skipped upgrade, custom
stage, runtime, and cloud configuration. Treat two-phase startup as a candidate
requiring verification, not standard bootstrap code. Check container lifetimes,
local migration completion, and subsequent sync. Do not swallow migration
errors, silently disable expected sync, or move required data transformation
into a view task merely because a forum workaround did so.

## Rollback snapshot crash during graph replacement

Reproduce the failing sequence with a disposable disk-backed related graph,
including external binary payloads if relevant. Record deletion rules, explicit
deletions, autosave, and the exact failure/rollback boundary. Compare the graph
before and after rollback and after reopening the store.

If both parents and owned children are explicitly deleted, compare deletion
orders as a controlled diagnostic experiment. Do not assume child-first deletion
is a confirmed framework fix or replace every cascade with manual deletion.
Preserve unrelated pending changes and measure the cost of loading larger graphs.
An injected pre-save error does not reproduce every disk or CloudKit failure.
See [failure injection](verification.md#failure-injection-and-reopen-checks).

## Implicit identifier predicate crash

For a failing identifier predicate, establish whether the parameter represents
an application-owned ID or a store-local `PersistentIdentifier`. Reduce the
expression and compare an explicit `persistentModelID` lookup when store-local
identity is intended. Execute matching and nonmatching fetches against the actual
store; account for temporary identifiers before the first save.

This is a diagnostic comparison, not a claim that `.id` generally crashes.
Preserve application-owned identifiers where that is the query's meaning; do not
use a store-local identifier as a cross-device or archive ID. See [identity](modeling.md).

## Protocol-constrained predicate construction

A [Swift Forums discussion](https://forums.swift.org/t/swiftdata-predicate-does-not-handle-protocol-witness/68256)
reports key-path failures with protocol-constrained model predicates and proposes
concrete-model expressions. These are community reports, not an Apple-confirmed
root cause or a guarantee for the current SDK.

If the symptom matches, compare the generic expression with a concrete-model
expression at the fetch boundary. Preserve filtering semantics and execute the
actual descriptor, including the failing Preview, Debug, or Release mode.
A successful in-memory predicate evaluation does not establish store translation.
Do not remove generic abstractions unrelated to the reproduced failure.

## CloudKit field name after a local attribute rename

Compare local schema migration and cloud field compatibility separately. Follow
Apple's [attribute-to-field mapping](https://developer.apple.com/documentation/coredata/reading-cloudkit-records-for-core-data)
and [migration guidance](https://developer.apple.com/videos/play/wwdc2022/10120/).
A successful local migration or export alone does not establish that older
clients and fresh imports see compatible field names and values.

In an isolated development setup, compare a renamed stored property using
`originalName` with retaining the stored name and exposing a computed API name.
Inspect exported fields and fresh imports, then exercise supported old/new
clients. Record the actual result without claiming a universal framework defect.
See [rename decisions](cloudkit-and-surfaces.md#renaming-a-synced-property).

## Adding evidence

Retain only task-relevant technical evidence with public, retrievable provenance
or a self-contained synthetic reproduction. Record conditions, attempted change,
observed result, and limits. Do not introduce owner-specific application histories,
private logs, account identifiers, local paths, or unrelated product decisions.
Do not anonymize an unverified personal report into an apparently established
framework fact. Omit claims whose supporting evidence cannot be retained.
