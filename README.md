# Agent Skills

Reusable agent skills for development and personal workflows.
System-managed skills, runtime assets, generated artifacts, and private local data are excluded.

## Local Installation

Use `~/.agents/skills` for user skills shared across repositories. Keep one
maintained checkout there; Codex discovers the top-level skill directories.
For an alternate checkout, link selected skill directories into that discovery
root instead of keeping separately maintained copies.

Codex settings and global instructions remain in `~/.codex/config.toml` and
`~/.codex/AGENTS.md`. Bundled system skills and plugin caches are owned by Codex
and should remain in their provider-managed locations.

## Included Skills

- `app-store-release-notes-writer`: Generates App Store Connect-ready release notes across supported locales from a git range and project localization settings.
- `app-store-release-preparer`: Prepares versions, localized release notes, descriptions, and screenshots through Apogee with read-back verification and resumable deferred work.
- `apple-hig-ui-guardian`: Audits and repairs Apple-platform UI work against Apple's Human Interface Guidelines.
- `apple-intelligence-dev`: Builds and evaluates Apple Intelligence features with current Apple guidance, grounded generation, lifecycle safety, and platform-specific evidence.
- `apple-ios-dev-flow`: Orchestrates the owner's Apple development workflow using personal principles, MH Swift style, reference architecture, and reusable platform specialists.
- `apple-sample-code-advisor`: Finds and applies Apple Developer sample code as official implementation guidance for Apple-platform work.
- `ci-verify-and-summarize`: Runs the repository's standard verify flow, reviews only the newest CI run artifacts, and summarizes push readiness from the current diff.
- `context-capture`: On explicit `$context-capture` invocation, saves user-provided material as near-raw local Markdown evidence.
- `context-consult`: On explicit `$context-consult` invocation, searches local context archives and returns cited context packs.
- `coordinate-codex-claude`: Explicitly delegates implementation to Claude or reviews existing unpushed Claude or manual work in Codex, including development contracts and commit quality.
- `git-publication-review`: Checks destination visibility and outgoing Git history for public disclosure risks, with an evidence-scoped publication assessment.
- `issue-implementation-planner`: Turns existing issues into code-grounded implementation plans, dependency ordering, and acceptance criteria, with verified posting when requested.
- `mh-swift-style`: Applies this repository owner's established Swift formatting and code-organization preferences to Apple-platform code.
- `organize-photos-for-line-sharing`: Applies the owner's source-aware monthly Photos workflow to build outbound LINE-sharing albums from self-captured originals, preserves their dates, actively corrects their orientation, normalizes dates only for confirmed LINE downloads, rotates LINE media conservatively, never deletes media, and produces a visual HTML report.
- `product-overview-syncer`: Conservatively syncs an existing product or architecture overview Markdown document with the current codebase reality.
- `release-risk-analyzer`: Assesses whether the range from the latest release tag to `HEAD` contains release-blocking changes on durable-risk surfaces.
- `repo-agent-contract-maintainer`: Maintains concise, clone-ready repository `AGENTS.md` contracts and routes longer guidance to the correct durable layer.
- `repo-and-app-footprint-inspector`: Diagnoses repository and app size, concentration, maintenance burden, and structural hotspots without modifying source code.
- `repo-consistency-refiner`: Audits one repository at a time for structural, architectural, workflow, and documentation drift, then proposes low-risk refinements.
- `repo-momentum-driver`: Continues the agreed repository objective or chooses bounded next work backed by current evidence.
- `respect-incomes-architecture`: Resolves a local Incomes checkout and uses it as a read-only architectural reference for repository and tooling alignment.
- `skills-batch-auditor`: Reviews custom skills against current usage and tools, fixes deterministic drift, and applies portfolio changes when authorized.
- `string-catalog-maintainer`: Audits and repairs Xcode string catalogs such as `Localizable.xcstrings` and related localization assets.
- `swift-code-guardian`: Audits and repairs Swift code against official Swift guidance, API design conventions, and concurrency safety expectations.
- `swiftdata-dev`: Implements and troubleshoots SwiftData using Apple guidance, scoped incident reports, and persistence verification.
- `swiftdata-schema-auditor`: Reviews SwiftData schema definitions and explains entities, relationships, persistence, and migration risk.
- `sync-xcode-skills`: Exports Xcode-provided agent Skills and installs Codex-compatible local copies.
- `track-developer-principles`: Maintains a personal cross-repository principle system; the private record files themselves are intentionally not tracked here.
- `track-personal-principles`: Maintains private weighted personal operating principles while keeping the record files out of git.
- `verify-contract-maintainer`: Creates, audits, and maintains minimal verification contracts, with Apple bootstrap guidance and compatible existing-entrypoint maintenance.
- `xcode-preview-auditor`: Audits SwiftUI `#Preview` coverage and capture results screen-by-screen, with audit-first reporting.
- `xcode-ui-smoke-auditor`: Runs safe Simulator UI smoke audits for Apple-platform apps and reports visual or interaction risks without auto-fixing by default.

## Reuse and Personal Profiles

Platform or tool requirements such as Xcode, SwiftData, or Apogee define the
intended audience; they do not imply dependence on one owner's environment.
General specialists receive constraints from the current task and repository.
They must not select a particular owner's personal profile or private records.

`mh-swift-style`, `respect-incomes-architecture`, `apple-ios-dev-flow`, and
`organize-photos-for-line-sharing` intentionally encode personal choices. These
profiles can travel with their user and depend on reusable specialists; the
reverse dependency is avoided. Private records are separate from the reusable
procedures that maintain them. Installing a profile never supplies its private
data, reference checkouts, tool access, or authorization.

## Layout

Each skill lives in its own directory and typically includes:

- `SKILL.md`: the main instructions
- `agents/openai.yaml`: Codex-specific UI metadata and invocation policy
- optional `scripts/` or `references/` directories when the skill needs helpers or supporting guidance
- optional ignored data directories such as `records/`, `archives/`, or `cache/` when a skill owns mutable local state

Other hosts need their own discovery and invocation adapters. Preserve explicit-only
invocation policies in each host. A skill may depend on host-specific tools;
installing its instructions alone does not provide those tools.

Local data migrations are explicit maintenance operations. Run
`python3 scripts/migrate_skill_data.py --list` to inspect available migrations
when a known legacy layout needs updating. Select the relevant scope, review the
dry run, and use `--apply` only for an authorized migration. The helper copies
missing targets, preserves conflicts, and stops the version chain on conflict;
it is not a required step after every pull or on a fresh installation.

## Verification

The repository requires Python 3.9 or later and a Bash 3.2-compatible shell.
Run the clone-ready verification entrypoint from the repository root:

```sh
bash scripts/verify_repository.sh
```

The command uses the Git index as its inventory. It validates every tracked
skill's frontmatter and `agents/openai.yaml`, checks the Included Skills list,
compiles tracked Python, syntax-checks tracked shell files, runs tracked Python
and shell tests, and checks both staged and unstaged diffs for whitespace errors. Ignored
runtime skills, generated Xcode skills, private records, archives, and caches
are not traversed.

## Intentionally Untracked

- `.system/`, `codex-primary-runtime/`, and `ci_scripts/` are not part of this repository because they are system/runtime/local-workflow managed rather than portable custom skill content.
- `track-developer-principles/records/` and `track-personal-principles/records/` are kept out of git because they hold private local principle history.
- `context-capture/archives/` is kept out of git because it holds private or work-local evidence captures.
- `apple-sample-code-advisor/cache/` is kept out of git because cached Apple sample projects are disposable local evidence.
- `organize-photos-for-line-sharing/work/` is kept out of git because inventories, media exports, contact sheets, and run reports are private task artifacts.
- `xcode-skill-*` and `sync-xcode-skills/state/` are generated locally by `sync-xcode-skills`; never edit or commit them directly.
