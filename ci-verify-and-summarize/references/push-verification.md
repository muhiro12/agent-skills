# Optional Push Receipt Matching

Use this opt-in adapter only for an authorized local push policy. It never
publishes, installs tools, runs QA, or installs a hook. Complete actual checks
and review the resulting immutable source before local activation. Ordinary
CI remains independent of an installed agent skill.

`scripts/check_push_verification.py` API version 1 accepts a repository-relative
contract JSON, remote name, and remote location, with Git pre-push tuples on
stdin. The contract declares schema version 1, a project, named build/test
checks (kind, scheme, optional project/test_plan, required targets), a lint argv
and optional tracked resolution file, and an exact optional prose-reuse list.
Retain repository-specific scopes: a library test does not cover system tests.
Require full test execution; subsets, missing bundles, skips, native issues,
captured warnings, and unreviewed error candidates remain incomplete.

`scripts/swiftlint_evidence.py` API version 1 accepts the contract followed by
`select|run`, repository, the two explicitly configured package roots, and for
`run`, `lint|format` plus the complete file list. It checks the project's package
requirement, workspace state, package checkout, remote artifact manifest, actual
binary version/hash, and optional tracked pin before execution. Capture the
single `SwiftLint execution:` JSON line with the normal execution helper.
Only successful strict lint belongs in a push receipt. Never use autofix as QA.
Do not resolve arbitrary global caches or executable overrides as evidence.

Receipts use schema version 2 in the common Git directory's private
`push-verification/destinations/<sha256-of-location>/receipt.json`. They bind the
common directory, destination, exact sorted proposed updates, complete outgoing
commit set, passive Betterleaks 1.9.0 scan/execution records per update, contextual
review hash, and per-commit quality records for every contract check plus lint
and diagnostics. The `checker` object binds `api_version`, `helper_sha256` for
the actual checker, and `contract_sha256`. Every proposed source must contain
that same contract. A helper change requires a new compatibility review/receipt.

Quality records use the retained execution/native-review format described in
[complete Xcode review](xcode-result-review.md). Keep the original execution,
raw output, native exports, and exact reviewed negative-test ledger intact.
Hash-bind regular evidence files inside the receipt store. Do not relabel old
records as new execution. Prose reuse is allowed only for explicitly listed
paths with an ancestor/source-input comparison; configuration is never prose.

Resolve the installed skill from the active host. A thin repository adapter may
support an explicit `CI_VERIFICATION_SKILL` directory and the canonical user
skill location. Reject an absent helper or unsupported API explicitly; do not
install a dependency, silently fall back, or weaken the receipt. Test normal,
missing/changed evidence, changed source/base/tool/contract, unsupported versions,
and uninstalled-helper behavior with isolated fixtures before live activation.
Keep the previous local hook or absence recoverable. Recheck ownership immediately
before activation and never fire a real push solely to test a hook.

Same-user evidence hashes detect missing/mismatched records. They do not prove
authenticity against the owner or independently establish contextual disclosure
safety. Publication review and push authorization remain separate.
