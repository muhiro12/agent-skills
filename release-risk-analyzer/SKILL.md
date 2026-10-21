---
name: release-risk-analyzer
description: "Review release risk from a public release to the next candidate. Prioritize primary-data loss, deliver a readable HTML report, and supplement the risk judgment with important hard-to-change contracts and short source diffs. Review only; no fixes or release operations."
---

# Release Risk Analyzer

## Purpose and boundaries

Assess the next release's risks, prioritizing loss or corruption of existing
users' primary data. Preserve the review's breadth: persistence, destructive
operations, shared behavior, external integration, permissions, packaging, and
other changed release surfaces. Supplement that judgment with important contracts
that publication makes irreversible or costly to change, whether they are
appropriate, and whether existing commitments are preserved. Investigate broadly;
report selectively. Finding many matching literals is not the result.

This skill reviews and reports only. Do not edit the reviewed repository, run
migrations, change versions, commit, push, or distribute a build. Recommend checks
or fixes without performing them. A score is review priority, not failure
probability, permission to ship, or an operation-approval gate.

## Workflow

### Establish the comparison

- Compare the requested public release with the candidate. The latest reachable
  tag is a source-range fallback, not proof of public distribution.
- Default to this single upcoming-release comparison. A historical multi-release
  report requires an explicit request; a prior example does not change the scope.
- Use `--base-ref`, `--head-ref`, or `--tag-pattern` for the intended sources.
  Identify the distributed version/build and its source when available; disclose
  an unknown build-to-tag correspondence without a generic warning list.
- Separate shipped contracts, candidate additions, unpublished prototypes, and
  development-only state. Compare the net endpoints; a reverted experiment or
  moved definition is not a new or retired contract.

### Gather evidence

```bash
python3 scripts/review_release_risk.py --repo /path/to/repository --format json
```

Keep the JSON as working evidence rather than pasting it into the answer. The
script's default Markdown is a compact detector overview; `--verbose` expands
diagnostic detail. Neither is the final contextual review or the HTML deliverable.
Read [references/risk-rules.md](references/risk-rules.md) for contract inspection
and scoring. The script reads the selected refs, not the working-tree version.
Its matches are candidates, not proof of a contract, harm, or safety. Inspect
ref-specific source and consumers beyond the detector's matches. Keep a working
coverage record for each applicable contract surface in the reference: added,
changed, removed, unchanged, or unverified, with supporting evidence. Do not infer
coverage from the score or let a database-only review stand for all contracts.

### Inspect publication contracts

Inspect the applicable contract surfaces alongside the ordinary release risks.
Use these questions to establish the evidence, then select only material,
hard-to-change commitments for the supplemental report:

1. **What is new?** Check actual stored, serialized, externally registered, and
   published values. Include UserDefaults raw keys and stored value formats,
   scene restoration keys, file formats, deep-link screen identifiers, paths and
   query names, and external identities; do not stop at the database schema.
2. **Is it appropriate?** Check necessity, purpose, raw naming and local conventions,
   types/defaults, real writers/readers, promised behavior, and avoidable migration
   or support burden. Give a judgment and a short reason, not just an inventory.
3. **What happens to existing contracts?** Check changes and removals, old readers,
   keys, aliases, migrations, and continued interpretation of old saved or shared
   values. State whether each relevant contract is retained, compatibly replaced,
   or retired, and what breaks if compatibility is lost.

Trace who owns each value, where it lives, how long it survives, who reads it, and
what a change would lose. Distinguish an app-owned stable key from a newly generated
message ID. An Apple API, OS-retained latest message, or literal alone does not
establish a permanent app obligation. Mixed-version communication may need bounded
compatibility without creating a durable record identity.

Use the applicable classes: `identity-fixed`, `migration-required`, and
`legacy-support`. Describe the actual support lifetime and retirement conditions;
do not call every convention permanent. Necessary new contracts are not defects
or automatic risk surcharges. Disposable UI state and caches carry different
consequences from primary data.

### Check serious consequences and calibrate risk

- Surface loss or corruption of long-term users' primary data first when present.
  Trace original stores, required sidecars, backups, and other viable copies,
  including pending mutations saved after a failed operation. Reader rejection,
  a recoverable crash, lost screen selection, and loss of all copies are distinct.
- Ordinary version/build increments contribute zero; migration or format consumers
  of those values and co-located contract changes remain separate effects.
- Retain category maxima and small independent breadth modifiers; count a cause
  once. Explain contextual adjustments briefly. Heuristic scores cap at 95;
  reserve 100 for separately substantiated catastrophic loss.
- Bands remain `80-100=Block`, `60-79=Hold for review`,
  `40-59=Proceed with caution`, `20-39=Review recommended`, `0-19=Proceed`.
  Zero means no scored signal, not verified safety. Unknown evidence or a new
  contract alone does not prohibit release.

## Human-readable report

Default to a self-contained HTML artifact in the conversation's language, saved
outside the reviewed repository and opened in an available preview. Honor an
explicit requested format; if HTML creation or delivery is unavailable, explain
the limitation and use readable Markdown. Read
[references/reporting.md](references/reporting.md) when composing the deliverable.

Lead with the overall release-risk judgment and its decisive reasons, putting
serious primary-data findings first. Keep this summary to a short paragraph and
roughly three to five points or a small table. Include material verification gaps
and practical attention needed; show the score/band as supporting information.
The contract supplement must not replace or bury this assessment.

Then highlight important contract additions, changes, or retirements, including
appropriate commitments with a low or zero score when future change would still
be costly. For each, explain its purpose, exact significant value or format,
what would break or be lost, compatibility handling, and actual support lifetime.
Show a short, real source diff directly with the explanation, using GitHub-style
addition/deletion colors or markers and verified source references. Keep full
files and classes out of the report.

Use `none found in the reviewed scope` or `unverified` where supported; do not
claim absence from a detector miss. Group unchanged areas in one sentence. Include
only decisive raw values and a few direct source links; retain the rest as working
evidence. Name unfamiliar technology and explain its consequence in one plain
sentence. For a format change, briefly identify what old and new data represent;
distinguish transport dictionary keys from actual persisted keys. Keep scope to one
line. Honor a request
limited to contracts without adding general build, UI, or CI summaries.

Do not paste the detector report, exhaustive key/schema/path lists, score
breakdowns, all commits/files, repeated unverified boilerplate, or every possible
confirmation item. Brevity comes from grouping and selecting evidence, not from
skipping investigation or hiding an independent serious finding. Select contracts
by consequence and reversal cost, not by the presence of a key, enum, or literal.
Routine UI state and easily regenerated caches usually stay in working evidence;
group unchanged surfaces briefly. Do not omit a material UserDefaults, route, or
other commitment merely because its detector score is low. A contract-free
candidate needs no artificial contract inventory. Keep the chat response to the
artifact link and a few decisive conclusions rather than repeating the report.

Separate technical evidence from personal acknowledgment. Do not infer the
user's approval from ADR status or authorship, or turn awareness into mandatory
questions. Mention acknowledgment only when it affects the requested judgment.

## Verification

- Check ref-specific values, raw-value equality, purpose and lifetime, legacy
  readers/aliases, recovery distinctions, and independent scoring.
- Separate detection candidates, confirmed defects, completed checks, and
  material uncertainty. A source review does not prove distribution readiness.
- Preserve JSON evidence and `risk_diff_snippets`; use short relevant excerpts
  in the final report after checking the selected refs and actual consumers.
- Verify the HTML renders, source links and excerpt line numbers match the frozen
  refs, and each displayed diff is real. Keep detection candidates distinct from
  reviewed conclusions; presentation alone does not validate them.
- When maintaining this skill, run its Git-fixture behavior tests and the
  repository verification contract. Verify observable behavior and read-only
  invariants rather than expected prose.
