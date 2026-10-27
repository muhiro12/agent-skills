# Agent Skills

Reusable agent skills for development and personal workflows.
System-managed skills, runtime assets, generated artifacts, and private local data are excluded.

## Local Installation

Use `~/.agents/skills` for user skills shared across repositories. Keep one
maintained checkout there; Codex discovers the maintained top-level skills and
the nested external skill directories.
For an alternate checkout, link selected skill directories into that discovery
root instead of keeping separately maintained copies.

Codex settings and global instructions remain in `~/.codex/config.toml` and
`~/.codex/AGENTS.md`. Bundled system skills and plugin caches are owned by Codex
and should remain in their provider-managed locations.

Keep externally authored skills in `external/`, which is ignored as a whole:

- `external/xcode/`: generated installations managed only by `sync-xcode-skills`.
- `external/<repository>/`: upstream repositories or downloaded bundles,
  preserving their files, relative layout, and licenses. Clone or extract each
  repository directly here; no installation-method grouping is needed.

The name `external` describes the content's origin. The ignore rule controls
publication independently. Reserve `external/xcode/` for generated installations.

Codex discovers nested skill folders here; per-skill discovery links and local
exclude entries are unnecessary. Use the visible directory name `external`;
hidden directories are not interchangeable discovery locations. Provider-owned
plugin caches stay in their runtime-managed locations.

The generic `/external/` ignore rule travels with a clone. The installed
contents do not: each machine installs its own external skills. Keep individual
installation names, source URLs, and local paths out of tracked ignore files,
inventories, documentation, and commit messages unless their publication is
explicitly authorized. Ignore rules do not untrack existing files or prevent
forced staging; repository verification also rejects tracked `external/` content.

For an existing installation, preview the scoped migration before applying it:

```sh
python3 scripts/migrate_skill_data.py --only external-skills
python3 scripts/migrate_skill_data.py --only external-skills --external-source /path/to/upstream-bundle
```

Add `--apply` to move the previewed installations. The migration preserves
upstream bundles, removes their matching old top-level discovery links, and
regenerates the Xcode catalog with the new installation paths. Existing bundles
under the legacy `external/manual/` container are moved directly under
`external/`, and the empty container is removed. The migration refuses
conflicting destinations and rolls back a failed move. Remove obsolete local
exclude entries for the removed links after confirming discovery at the new
locations; preserve unrelated local patterns.

## Development Tools

Source search uses rg; passive publication scans use Betterleaks. Setup,
supported versions, missing-tool behavior and private scanning commands belong
to [the publication tools reference](git-publication-review/references/publication-tools.md).
Install and check these tools on each execution host; installing skills alone
supplies no binaries. This does not enable hooks or complete a repository's QA.

## Repository Maintenance

Use this README as the repository contract. Keep public instructions portable,
English, action-focused, and usable from a fresh clone.

- A tracked top-level directory containing `SKILL.md` is a maintained custom
  skill. Keep its entrypoint, `agents/openai.yaml`, referenced resources, and
  Included Skills entry consistent. Read the selected skill before editing it.
- `.system/`, `codex-primary-runtime/`, and `ci_scripts/` are local or managed
  content, not portable custom skills or verification inputs.
- Ignored `records/`, `archives/`, and `cache/` contain private or disposable
  data. They are not inputs to definition maintenance. Consult or maintain
  records through their owning workflow; migration and external distribution
  require their own explicit scope. Never copy private context into tracked files.
- Preserve external bundles and licenses. Do not edit generated Xcode skills or
  catalog state directly; update the owning synchronization workflow instead.
- Local data layout changes belong in `scripts/migrate_skill_data.py`, with
  dry-run defaults, idempotence, and conflict preservation.
- Keep long procedures in their owning skills. Describe Xcode verification by
  stable evidence capabilities and resolve tool actions at runtime; exact tool
  spellings belong in executable adapters or generated upstream guidance.
- Preserve unrelated work and keep commits scoped to one coherent purpose.
- Run the [verification entrypoint](#verification) after changes. Add Python
  behavior tests as `test_*.py` under a `tests/` or `scripts/` directory and shell
  behavior tests as `tests/test_*.sh`; fixture inputs are not executed as tests.

## Included Skills

- `app-store-release-notes-writer`: Generates App Store Connect-ready release notes across supported locales from a git range and project localization settings.
- `app-store-release-preparer`: Prepares versions, localized release notes, descriptions, and screenshots through Apogee with read-back verification and resumable deferred work.
- `apple-hig-ui-guardian`: Audits and repairs Apple-platform UI work against Apple's Human Interface Guidelines.
- `apple-intelligence-dev`: Builds and evaluates Apple Intelligence features with current Apple guidance, grounded generation, lifecycle safety, and platform-specific evidence.
- `apple-ios-dev-flow`: Orchestrates the owner's Apple development workflow using personal principles, MH Swift style, reference architecture, and reusable platform specialists.
- `apple-sample-code-advisor`: Finds and applies Apple Developer sample code as official implementation guidance for Apple-platform work.
- `ci-verify-and-summarize`: Runs the repository's standard verify flow, reviews only the newest CI run artifacts, and reports verification evidence and gaps from the current diff.
- `context-capture`: On explicit `$context-capture` invocation, saves user-provided material as near-raw local Markdown evidence.
- `context-consult`: On explicit `$context-consult` invocation, searches local context archives and returns cited context packs.
- `coordinate-codex-claude`: Explicitly coordinates Claude implementation and return handoffs, applies `refine-development-changes` before acceptance, and owns optional Claude adapter guidance.
- `git-publication-review`: Audits destination visibility and outgoing history, pushes reviewed commits when checks pass, and verifies the remote result; honors explicit review-only requests.
- `issue-implementation-planner`: Turns existing issues into code-grounded implementation plans, dependency ordering, and acceptance criteria, with verified posting when requested.
- `mh-issue-workflow`: Applies the owner's GitHub Issue and Project workflow across repositories, including non-development work, privacy-aware routing, association read-back, and resumption reconciliation.
- `mh-swift-style`: Applies this repository owner's established Swift formatting and code-organization preferences to Apple-platform code.
- `organize-photos-for-line-sharing`: Applies the owner's source-aware monthly Photos workflow to build outbound LINE-sharing albums from self-captured originals, preserves their dates, actively corrects their orientation, normalizes dates only for confirmed LINE downloads, rotates LINE media conservatively, never deletes media, and produces a visual HTML report.
- `product-overview-syncer`: Conservatively syncs an existing product or architecture overview Markdown document with the current codebase reality.
- `refine-development-changes`: Inspects and actively improves selected commits and working changes against applicable development rules and intended behavior, through necessary reimplementation and verification.
- `release-risk-analyzer`: Reviews the next candidate against a public release, prioritizing primary-data risk in a readable HTML report with short diffs for important hard-to-change contracts.
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
- `sync-xcode-skills`: Exports agent Skills from the newest usable local Xcode and installs Codex-compatible local copies.
- `track-developer-principles`: Consults and automatically maintains weighted developer judgment expressed by the user; private records stay outside this repository history.
- `track-personal-principles`: Consults and automatically maintains weighted personal judgment expressed by the user, without inferring personality or copying raw conversations.
- `verify-contract-maintainer`: Creates, audits, and maintains minimal verification contracts, with Apple bootstrap guidance and compatible existing-entrypoint maintenance.
- `xcode-preview-auditor`: Audits SwiftUI `#Preview` coverage and capture results screen-by-screen, with audit-first reporting.
- `xcode-ui-smoke-auditor`: Runs safe Simulator UI smoke audits for Apple-platform apps and reports visual or interaction risks without auto-fixing by default.

## Response Language

Skill instructions and metadata use English. User-facing explanations follow the
active conversation and host/user language preferences; artifact language follows
its target locale or repository contract. Report section names describe content,
not mandatory English output. Helper output and existing localized artifact
formats are evidence to interpret, not instructions fixing the reply language.
Keep personal response-language preferences in local agent instructions.

## Reuse and Personal Profiles

Platform or tool requirements such as Xcode, SwiftData, or Apogee define the
intended audience; they do not imply dependence on one owner's environment.
General specialists receive constraints from the current task and repository.
They must not select a particular owner's personal profile or private records.

`mh-issue-workflow`, `mh-swift-style`, `respect-incomes-architecture`,
`apple-ios-dev-flow`, and
`organize-photos-for-line-sharing` intentionally encode personal choices. These
profiles can travel with their user and depend on reusable specialists; the
reverse dependency is avoided. Private records are separate from the reusable
procedures that maintain them. Installing a profile never supplies its private
data, reference checkouts, tool access, or authorization.

Principle skills maintain reusable judgment expressed by the user without a
separate save request. Read-only and no-record instructions take precedence;
raw archive capture, migration, external synchronization, and publication stay
separate operations. They work with local skill-owned records and require no
repository inside `records/`, private README, GitHub connection, or sync setup.
If a host still requires explicit consent for every local principle update,
that host instruction takes precedence until its owner aligns the host policy.

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
dry run, and use `--apply` only for an authorized migration. The helper preserves
conflicts and stops the version chain on conflict. Legacy private-data migrations
copy missing targets; external-skill migration moves the selected installations.
It is not a required step after every pull or on a fresh installation.

## Verification

The repository requires Python 3.9 or later and a Bash 3.2-compatible shell.
Run the clone-ready verification entrypoint from the repository root:

```sh
bash scripts/verify_repository.sh
```

The command uses the Git index as its inventory. It validates every tracked
skill's frontmatter and `agents/openai.yaml`, checks the Included Skills list,
compiles tracked Python, syntax-checks tracked shell files, runs tracked Python
and shell tests, and checks both staged and unstaged diffs for whitespace errors.
Tracked `external/` content is rejected. Ignored external skills, runtime skills,
private records, archives, and caches are not traversed.

## Intentionally Untracked

- `.system/`, `codex-primary-runtime/`, and `ci_scripts/` are not part of this repository because they are system/runtime/local-workflow managed rather than portable custom skill content.
- `track-developer-principles/records/` and `track-personal-principles/records/` are kept out of git because they hold private local principle history.
- `mh-issue-workflow/records/` is kept out of git because it holds private routing configuration.
- `context-capture/archives/` is kept out of git because it holds private or work-local evidence captures.
- `apple-sample-code-advisor/cache/` is kept out of git because cached Apple sample projects are disposable local evidence.
- `organize-photos-for-line-sharing/work/` is kept out of git because inventories, media exports, contact sheets, and run reports are private task artifacts.
- `external/` contains externally authored skill bundles and generated installations; individual installation names and contents remain local.
- `external/xcode/` and `sync-xcode-skills/state/` are generated locally by `sync-xcode-skills`; never edit or commit them directly.
