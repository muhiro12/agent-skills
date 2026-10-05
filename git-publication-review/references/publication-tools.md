# Search and Passive Publication Scanning

Use `rg` for source discovery and Betterleaks for mechanical secret detection.
These tools are adopted parts of this workflow. Installation on one host does
not install them on another host, establish credentials, or enable Git hooks.
Contextual publication review remains mandatory.

## Setup and Supported Versions

Resolve tools from the active `PATH`. Do not copy executables, hardcode an app
bundle or owner-specific binary path, or silently substitute another scanner.
On a Homebrew host, use the official core stable formulas:

```sh
brew install ripgrep betterleaks
```

Other hosts use the respective upstream stable release and its published
integrity checks. Do not use HEAD, nightly, or release candidates. Verify the
actual distribution, version and dependency closure on that host. Homebrew's
stable formula can advance; installation alone does not establish compatibility.

Run from this skill directory:

```sh
python3 scripts/publication_tools.py check
```

The supported adapter versions are rg `15.2.x`, Betterleaks **`1.9.0`**, and Git
`2.38+` within major version 2. The checked installation uses rg `15.2.0` and
Betterleaks `1.9.0`. Python 3.9 or later is required. Homebrew ripgrep has a pcre2
runtime dependency; Betterleaks has no formula runtime dependency. Build-only
dependencies are unnecessary when using the official bottles.

Use `check --tool search` for source search or `check --tool scanner` for
publication scanning. A missing or unsupported tool returns exit 2 and reports
`incomplete`; it is never a clean result. Before widening supported versions,
recheck upstream flags, rule/config semantics, report shape, exit behavior and
the real-scanner fixtures. Betterleaks v2 changes CLI/config/report contracts;
its `-v` can enable credential validation. This adapter never uses `-v` and
explicitly sets `--validation=false` and `--redact=100`.

## Search Coverage

By default rg respects ignore rules and skips hidden and binary content. It
searches present files, not earlier Git revisions. Broaden its file scope only
for the task's relevant content and explain exclusions. A successful rg search
is neither a secret scan nor proof that outgoing history is clean.

## Scan an Observed Immutable Boundary

First resolve the exact destination, visibility and freshly observed destination
OID using the main skill workflow. This helper performs no remote access and
does not validate that an input base came from the intended destination.
Supply full immutable commit OIDs, with a new private output path:

```sh
python3 scripts/publication_tools.py scan --repo /path/to/repository \
  --head FULL_SOURCE_COMMIT_OID --base FULL_OBSERVED_DESTINATION_COMMIT_OID \
  --report /private/new-report.json
```

For a genuinely new ref, replace `--base ...` with `--new-ref`; this scans the
full reachable history. Existing updates require a fast-forward boundary.
Shallow/partial history, missing objects, grafts and unsupported update types remain
incomplete. Recheck source and destination OIDs before publication.

The helper records every outgoing commit, including merged side history. It
scans added text in their patches, with root commits and separate merge diffs;
a later deletion does not remove an earlier finding. It does not read unrelated
untracked files. It disables external diff/textconv drivers, signature commands
and lazy fetching, and rejects partial-clone configuration or promisor packs.

The Git directory is the scanner source so worktree scanner config and ignore
files cannot silently suppress findings. An ignore file in that Git directory
stops for review. The adapter extends the supported binary's default rules,
ignores inline allow comments, supplies no baseline, and accepts no arbitrary
scanner options or custom expression filters. It keeps raw scanner output
private and temporary, suppresses forwarding it, then exports only finding rule,
commit, path and line references. Match, secret, context, author, commit message
and extension fields are discarded. Output uses mode 0600 and refuses overwrites.

Exit 0 means this limited scan completed with no findings; exit 1 means findings;
exit 2 means incomplete evidence or execution failure. The scanner's finding exit
code is distinct from its error exit code; absent/malformed/inconsistent reports
never pass. Inspect findings in context: benign fixtures passing does not justify
global suppression of identifiers or automatic dismissal of future findings.

Review commit/tag metadata, private information, final relevant tree content,
binary/LFS/submodule content, default-rule allowlists and archive/decode limits
separately. A clean scan is one piece of evidence, not publication clearance.
The emitted summary is not an Incomes pilot receipt and must not be relabeled
as a Gitleaks report.

## Verification and Hook Boundary

```sh
python3 tests/test_publication_tools.py
```

Fixtures use synthetic repositories and the actual supported scanner with live
validation disabled. They cover outgoing-range exclusion, new-ref full history,
removed secrets, merge side/resolution changes, hidden/ignored tracked files,
benign examples, report privacy and error/exit behavior. The actual-scanner tests
explicitly skip if the tool is unavailable; that skip does not establish scanner
readiness. Run the version preflight and these fixtures on each deployment host.

This workflow does not install or enable a hook. An existing receipt checker
that supports Gitleaks alone remains incompatible until deliberately updated and
tested end to end. Tool adoption and these process fixtures do not complete an
application's build/test/lint/diagnostic requirements or an unfinished QA pilot.

Upstream references: [ripgrep](https://github.com/BurntSushi/ripgrep),
[Betterleaks 1.9.0](https://github.com/betterleaks/betterleaks/releases/tag/v1.9.0),
[Betterleaks core formula](https://formulae.brew.sh/formula/betterleaks),
[ripgrep core formula](https://formulae.brew.sh/formula/ripgrep).
