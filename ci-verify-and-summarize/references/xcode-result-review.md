# Complete Xcode Result Review

Resolve native capabilities from the active runtime before selecting a command.
When the Apple development skill permits the official CLI fallback, retain the
actual `xcodebuild` command with an explicit, new `-resultBundlePath` using the
execution helper. Use a clean committed source snapshot, the repository's full
required test plan, assigned device, pinned dependencies, and selected Xcode.
Keep autofix separate. This procedure does not launch or exercise an app UI.

Check inherited SDK selection before an official CLI fallback. An ambient
`SDKROOT` for macOS can conflict with an iOS Simulator package-test destination.
When present, remove it for the verification command only, for example
`--tool env -u SDKROOT xcrun xcodebuild <explicit repository arguments>`, so
Xcode selects the SDK for that destination. Retain that literal argv, inspect
actual SDK paths in the complete output, and rerun clean tests. Do not alter
global SDK settings or suppress incompatible-sysroot warnings.

Bind retained output to the producing native result:

```sh
python3 /path/to/ci-verify-and-summarize/scripts/review_xcode_evidence.py \
  --evidence /private/captured-test-run --repo /path/to/verified-snapshot \
  --output /private/new-reviewed-run \
  --required-test-target RequiredTests
```

The adapter exports full native build issues, test summary, and test tree with
the selected Xcode's `xcresulttool`. It requires successful execution, zero native
build/analyzer issues, zero captured warnings, successful required unit or UI test bundles,
positive matching test totals, zero failures/skips/expected failures, and no
native runtime warnings. The original execution record and full output remain
unchanged as hash-bound artifacts in the new private directory. No result is
issued when exports, required scope, or exact source evidence are unavailable.

## Expected Negative-Test Output

Error words in a deliberately failing operation are candidates for review, not
a blanket exemption for a framework, suite, or diagnostic code. Inspect each
candidate against the test source, complete progress output, and passed native
test case. A real warning or runtime lifecycle fault cannot be exempted here.

Provide `--review /private/exact-negative-output-review.json` only after that
inspection. Its `source_head` must match the producing source. Its `errors` array
must cover every captured candidate exactly once, with `artifact`, one-based
`line`, `text_sha256` of the exact raw line, native `test_id` URL, tracked Swift
test `source_path`, Git blob `source_sha256`, and a concrete `reason`. Package test sources use
`Tests/`; an Xcode-owned test directory must match a required native target. Record the
test's start/pass `progress_span` as supporting review context. The adapter checks
line/source hashes, complete coverage, and the passed native case. It preserves
the original candidate count and records the explicit classifications separately.
Never regenerate a ledger solely to make changed output pass without reviewing it.

## Persistent Fixture Lifetime

Do not unlink a persistent SQLite fixture while Core Data still owns its store
handles. For Incomes' marked fixtures, retain the roots until the test process
has exited. After confirming ownership and shutting down only its assigned
Simulator, optionally add `--cleanup-fixture-device <producing-device-UUID>`.
The adapter compares that UUID with the actual destination and native device
inventory, requires `Shutdown`, and handles only the exact emitted
`data/tmp/IncomesLibraryTests-<UUID>` directories. It rejects links and unrelated
paths. Roots already removed by Simulator temporary-directory cleanup are
recorded separately. It never erases the device or sweeps other temporary data.
Cleanup is an explicit implementation task, not a side effect of ordinary review.

For a library/test route with no App Intents implementation, Apple's task producer
supports `LM_SKIP_METADATA_EXTRACTION=YES` to omit the irrelevant extraction task.
Establish that scope from current source before using it; do not set it globally
or on the normal app build. Reassess if the library adopts App Intents. Do not use
`LM_FILTER_WARNINGS` or quiet-warning options to clear real warnings. The primary
implementation is Apple's [App Intents metadata task producer](https://github.com/swiftlang/swift-build/blob/main/Sources/SWBApplePlatform/AppIntentsMetadataTaskProducer.swift).

Same-user artifacts and hashes detect missing or mismatched evidence; they do
not prove authenticity against their owner. Publication review remains separate.
