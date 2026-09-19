# Verifying SwiftData behavior

Choose evidence for the framework behavior being changed or investigated.
These are diagnostic methods, not an application architecture or a requirement
to introduce a backup feature, a shared library, or a particular test layout.

| Behavior | Evidence that addresses it |
| --- | --- |
| Predicate translation and matching | Execute the descriptor against the intended store; compiling the macro alone is insufficient |
| Pending inserts, updates, deletes, and rollback | Inspect the graph before and after the exact operation, including unrelated pending changes if the context is shared |
| Disk durability and relationship recovery | Save to a temporary disk store, release its owners, reopen, and inspect required values and links |
| Schema migration | Open synthetic stores made from supported historical definitions through the new migration path |
| External binary storage | Reopen and read the actual payload, not just the parent record or byte-count metadata |
| Synced attribute rename | Inspect exported field keys and fresh imports, then test supported old/new clients; successful export alone is insufficient |
| Another process or CloudKit | Observe the affected reader or device; a local save or in-memory test does not prove propagation |

## Attribute evidence to each changed path

For a multi-part persistence change, map each change to the operation actually
exercised and the remaining gap. A fresh-store cloud round trip can exercise the
new container and current relationships without exercising an old-store upgrade,
store relocation, extension access, or sync re-enablement. Do not transfer a
passing result to another path merely because both use the same factory.

Record whether historical fixtures were reconstructed and compiled with today's
SDK or produced by the shipped executable. The former verifies schema-shape
recognition; it does not reproduce historical framework metadata or an existing
CloudKit synchronization history. Keep both kinds of evidence distinguishable.

Choose non-default synthetic values when checking scalar fidelity, plus shared
relationships when checking graph identity. A zero-value round trip does not
establish decimal precision, and an identifier attribute surviving sync does not
make a store-local `PersistentIdentifier` portable across devices.

For extension ownership changes, test missing-store and old-store startup before
the host, then reading after host migration. A local read-only container test is
not a signed Widget or App Intent runtime test. Apple's
[WWDC26 group lab](https://developer.apple.com/videos/play/wwdc2026/8017/)
recommends leaving the migration plan out of extensions and handling the error
path so the host app can perform migration.

## Reproduce a failure before generalizing it

Capture the failing operation, error/stack, model declarations, store type,
configuration, and Xcode/OS versions. Reduce the reproduction without removing
the relationships or save sequence that triggers it. Keep suspected causes
separate from facts demonstrated by the reproduction.

Use synthetic data and a disposable store with `cloudKitDatabase: .none` unless
cloud behavior itself is under test. Test the original and changed operation
against equivalent fixtures. A successful run of the changed code alone does
not establish that the old code failed, or why it failed.

The [graph replacement rollback case](known-issues.md#rollback-snapshot-crash-during-graph-replacement)
illustrates why a simple graph or an in-memory-only test can miss a failure
found with a populated disk-backed graph. Its record includes a before/after
result; the other cases have weaker evidence and are labeled accordingly.

## Failure injection and reopen checks

Injecting an error at the save boundary can exercise the caller's rollback
path. It is not a simulation of every error inside `save()`, actual disk
exhaustion, process termination, or CloudKit conflict. Name the injected
boundary and avoid claiming those other failures were tested.

When the operation promises to preserve existing data, compare the affected
fields, relationship membership, required ordering, and binary payloads in the
recovered context and a fresh container. Counts alone cannot show that a graph
was restored correctly. Use the application's existing representation for the
comparison; no particular archive format is required.

`@Attribute(.externalStorage)` can place a binary payload outside the main
store file. A SQLite-only copy is therefore not sufficient evidence of a
complete store transfer. Check payload readability after the actual transfer
and reopen. See
[externalStorage](https://developer.apple.com/documentation/swiftdata/schema/attribute/option/externalstorage).

## Record the result and its limits

State which symptom changed, what still fails, and which configurations were
tested. Distinguish a current reproduction from an earlier report or source
inspection. Do not mark an incident fixed for newer SDKs without retesting, or
recommend abandoning a design merely because an old commit reverted it.

Retain the original error and recoverable store when initialization fails.
Separate entitlement/location problems, schema incompatibility, and runtime
failures. A successful preview, fresh empty store, or build cannot substitute
for the failing persistence path.


## Scoped cloud-backed upgrade and relocation observation

On 2026-09-19, a signed iOS 27.0 simulator with Xcode 27.0 (`27A266a`)
exercised a two-record synthetic CloudKit development store. The previous
release's unmodified source was built with that toolchain, imported the records,
and edited/exported a value. Installing the candidate over its existing store
adopted an explicit versioned schema while retaining stored attribute names.
Values, shared many-to-many tags, store UUID, and cloud record names survived;
cloud setup, import, and export completed successfully.

The same synced store was then placed at the application's legacy location.
Its relocation path copied SQLite sidecars, validated locally with CloudKit
disabled, and reopened with sync enabled. A subsequent decimal-value edit was
exported and matched both a resumed older synchronized snapshot and a fresh
cloud import. No duplicate records or broken shared-tag membership were found.
The resumed snapshot check exercised later imports using existing sync history,
which a fresh-store check alone could not cover.

Some overlapping automatic export requests were cancelled with Cocoa `134417`
because another export was pending; subsequent operations succeeded and pending
record flags cleared. Diagnose the eventual operation and data state rather
than treating every cancellation as corruption or ignoring all sync errors.

This supports those specific unchanged-field upgrade and relocation paths; it
is not blanket CloudKit compatibility. It did not exercise production, original
release binaries/toolchains, older runtimes, simultaneous device conflicts, or
external blob relocation. The store's support/cache directories were empty.
Private account identifiers and raw logs are not needed to reuse this method.


Cloud metadata pending flags are diagnostic details, not a public convergence
contract. In the same scoped test, a local deletion left zero pending flags
before its export was observed; a subsequent app restart exported the deletion.
Require completed operations and an independent import/value comparison before
claiming delivery. Record any restart needed, and inspect orphan relationships
separately from financial-record loss or duplication.
