# Xcode Project-Format Verification

Use this guidance when format-dependent checks or a requested migration touch
`project.pbxproj` and `project.xcproj`. Verification does not authorize
conversion, publication, or changes to the repository's release policy.

## Conversion and Recovery

[Apple's guide][conversion] documents JSON conversion in Xcode 27.2 and later
and reading either format in Xcode 27 and later. Distinguish this documented
floor from the oldest toolchain actually used to build the candidate. A
successful local conversion does not qualify a beta toolchain for release.

Use Xcode's Project Format control or the converter exposed by the selected
Xcode's help. The selector observed in Xcode 27.2 was:

```sh
xcodebuild -project App.xcodeproj -convert-project 'Xcode Project'
```

Preserve the original configuration in Git, try conversion on a disposable
copy when needed, and retain the generated output. Keep format replacement in
its own commit, separate from compatible tooling changes. Reverting that commit
restores the exact original file and removes the replacement. A reverse
conversion can regenerate identifiers and normalize declarations; it is useful
for comparison, but is not exact restoration. Preserve later project changes
before applying an old conversion revert. Never retain both configuration files.

## Readers and Local Consumers

Audit filename assumptions separately from object-model assumptions in local
checks, lint evidence, receipt matchers, test-posture checks, dependency guards,
and optional analysis tools. Bundle-level scheme or Cloud references do not
alone imply a dependency on either internal format. Validate optional tool
configuration against its supported options and actual schemes/targets; static
configuration review does not establish that its external parser or scan works.

Xcode output can contain comments and trailing commas. The shared adapters use
`plutil -convert json -o - <configuration>` before strict JSON parsing. This
native normalization read the actual Stally, Cookle, and Incomes converter
output and preserved escaped strings and URL content in local probes. It avoids
custom text repair, extra parser dependencies, and Swift interpreter caches.
If it fails on a future format or environment, retain the original input and
diagnostic and report the unsupported boundary; do not strip syntax with regex
or silently fall back to an unrelated file. Reject missing or ambiguous files
and malformed data. The filename selects the expected object model.

The optional [lint and receipt adapters](push-verification.md) preserve both
formats. Repository-specific package-adoption rules remain with their owner.
Resolve canonical package ownership and actual Frameworks links, including
the owning build phase, rather than accepting product-name declarations alone.
Follow legacy references from the project root: unattached objects do not prove
adoption. Keep direct framework references in scope when enforcing a boundary.

## Comparison and Evidence Limits

Compare native evaluated settings on the same toolchain and destination, plus
targets, Debug/Release configurations, package requirements and owners, shared
schemes, synchronized-folder membership exceptions, sources, resources, build
phases, embedding, signing, entitlements, and deployment targets. Review
regenerated IDs through their references and preserve IDs used by schemes.

Separate declaration or navigator normalization from ordered build behavior.
Incomes conversion changed Frameworks input order even though membership and
evaluated settings matched. Do not sort executable build phases, scripts, or
linker inputs merely to eliminate a diff. State the actual comparison scope and
use relevant app/companion builds and tests to bound the observed behavior.

Distinguish converter failures from permission/cache errors, service connection
errors, inherited SDK selection, shell-wrapper failures, and package-plugin
build-layout assumptions. Verify an ambiguous invocation's output before
retrying. Follow the existing [native result review](xcode-result-review.md)
for SDK context, full result exports, and exact negative-test diagnostic review.

A response timeout is not a completed native result. Recover complete official
exports when possible and report the producing command's status separately.
Parameterized cases and device/configuration executions can have different
totals; compare like-for-like fields and never add those aggregation levels.
Passed tests do not erase build warnings or expected negative-operation logs.

Tooling fixtures, ordinary lint, evidence-mode lint, app builds, library/system
tests, signed archives, and candidate Cloud runs establish different boundaries.
Run the repository's actual required checks, honor explicitly deferred work,
and report remaining gaps. Do not introduce Archive or Cloud as a new universal
gate, or turn historical builds into a current-source publication receipt.

[conversion]: https://developer.apple.com/documentation/xcode/updating-your-xcode-project-configuration-file-format
