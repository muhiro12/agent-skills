# Release Risk Rules

The canonical detector is `scripts/review_release_risk.py`;
`scripts/analyze_release_diff.py` remains its compatibility wrapper. Use built-in
rules, not repository-local rule configuration. Repository evidence informs review;
it does not replace the rules with a private scoring policy.

## Evidence and consequences

Prioritize primary-data loss and corruption, especially loss of all viable recovery
sources. Determine what can actually be recovered from the original database,
required sidecars, backups, exports, or other copies. Reader rejection or startup
failure with recoverable state is not complete loss. Pending mutations written by
a later save after a failed operation can damage saved data even without a crash.

Publication obligations are distinct from data-loss findings. Classify each contract
as applicable, allowing multiple classes:

1. `identity-fixed`: identity cannot change for the same published product.
2. `migration-required`: changes need risky implementation, technical migration,
   or user guidance.
3. `legacy-support`: changed contracts leave old schema, keys, readers, aliases, or
   migration code to support over time.

Do not claim literal permanence without evidence. Describe the support lifetime and
retirement conditions; old states may persist on long-term users' devices. Inspect
exact raw values, types, defaults, serialized fields, actual consumers, introduction
status, and old metadata/readers. Unused or reserved schema fields deserve careful
pre-publication review, even if empty today. A justified contract addition can be
reported without increasing risk; mere existence of a key or schema is not harm.

## Contract inspection

For every relevant addition, change, or removal, establish ownership, purpose,
exact raw value/type/default, writer and reader, lifetime, and the consequence of
renaming or dropping it. Report both whether a contract exists and whether it is
appropriate. Necessity alone does not justify a poorly chosen format or avoidable
support obligation; a justified new contract need not increase the score.

Keep a working coverage record for the surfaces used by the product. For each,
record net additions, changes/removals, unchanged values, or the specific unchecked
area. Locate definitions and actual consumers at both refs; a detector miss or
unchanged codec alone is not evidence that the whole surface was checked. This
record supports completeness and stays out of the default answer. Inspect:

- Stored schema and relationships, database/cloud identities and locations.
- UserDefaults/AppStorage, SceneStorage and other restoration state, Keychain,
  app groups, shared preferences, and SDK-owned settings touched by cleanup.
- Serialized files and backup formats: extension/type identifier, schema version,
  field names/types, old readers, and what the promised restoration preserves.
- Deep links and saved routes: scheme, host, path, query names/encoding, old aliases,
  and acceptance behavior. Check producers and parsers, notifications, widgets,
  shared URLs, pending links, and persisted route consumers even if the codec is
  unchanged. Display labels and internal screen names are not URL contracts unless
  serialized or exposed; a new consumer of an existing path is not a new path.
- Published API and OS-registered identifiers, such as widget kinds, activities,
  and intent/entity identifiers. Check actual external use, not just Swift visibility.

Compare raw values across refs, not file names or declaration names. A moved
defaults descriptor, reused key, or logical rename is not a new contract when
storage/wire/registered values and meaning are preserved. A newly protected
SDK-owned key in a cleanup allowlist is not a newly introduced app-owned key.
For UserDefaults, compare the actual raw keys, suites, value formats and types,
cleanup registration, migration readers, and any continued old-format writes.
Distinguish a logical Swift name, the fixed storage key, the stored value, and a
transport payload field even when their logical names match. Verify semantics as
well as strings; random-looking fixed keys are not values generated on each launch.

Distinguish the stable name of a field from its changing contents. A UUID generated
for each refresh is not a durable record identity. Framework support or retention
of the latest transport payload, such as a WatchConnectivity application context,
does not by itself make the app's message key permanent. Trace version skew,
regeneration, fallback, and the actual replacement window before assigning
long-term compatibility debt. Defaults storing durable preferences, disposable
scene selection, and recomputable caches deserve different consequences.

Judge names under the repository's relevant convention. Intentional random
eight-character defaults keys are valid; descriptive names may be appropriate
for communication fields or route paths. Do not impose one convention on every
surface or propose cosmetic renames of shipped identifiers. Check new raw names
before publication for errors, ambiguity, unnecessary fields, and local consistency.

For existing contracts, check whether old states still load or resolve with the
intended meaning. Keeping a parser declaration is insufficient if acceptance or
interpretation changes. Removing a reader, alias, or key can break users without
deleting their files. Identify retained, migrated, aliased, or deliberately retired
contracts and the users/data affected; a retirement note alone proves no regeneration.
Separate net endpoint changes from reverted or unpublished prototypes.

Ordinary release versions, format-only equal values, and logical renames preserving
the actual contract have no contract contribution. Version consumers that alter
migrations, gates, or formats are separate effects; co-located identity, capability,
minimum-OS, or schema changes remain reviewable.

## Select material contracts for the report

The coverage record remains broad. The final contract supplement selects only
commitments whose reversal has a substantial consequence: primary-data or
meaningful preference migration, loss of readable exported files, changes to
published identities or saved external references, coordination with deployed
clients, or costly recovery and user action. A persistent enum or AppStorage key
qualifies through its stored meaning and consumers, not its declaration alone.
Remote update endpoints, configuration fields, activation/expiry semantics, and
failure behavior qualify when installed binaries depend on them to remain usable
or updateable; they do not need to live in a database to create a commitment.

Do not promote every cache, generated message ID, notification identifier, or
temporary OS activity into a critical contract. Report one when its actual
replacement or retirement cost is material, and state that bounded lifetime.
Easily regenerated state usually stays in working evidence. This is a presentation
filter, not a narrower inspection scope, a new scoring threshold, or a reason to
hide an independent serious risk. Necessary commitments may still be important
to explain with a zero risk score.

## Scoring

Scores are review priority, not failure probability. Path matches are low-confidence
locators. Concrete changed values and destructive operations are still **candidates**
until their meaning, guards, reachability, affected state, and restoration sources
are inspected. Never infer all-copy deletion or readiness from a regex.

Retain the strongest item per independent category. Deduplicate the same cause
across categories and suppress only path hints whose changed lines are explained.
Start with the strongest category and add 5 for another category >=60, 3 for >=40,
or 1 for >=25. Do not sum individual findings or awareness items. Ordinary detector
output is capped at 95. A separately substantiated catastrophic loss may warrant
100 in the reviewed report, with the adjustment and evidence stated explicitly.

Keep bands: `80-100=Block`, `60-79=Hold for review`, `40-59=Proceed with caution`,
`20-39=Review recommended`, `0-19=Proceed`. Bands recommend a posture, not an action
or a universal confirmation gate. Unknown evidence alone does not prohibit release.

Use consequences to contextualize the detector score: recovery intact is generally
less serious than destructive writes; unavoidable new compatibility commitments
are not defects; avoidable long-term obligations deserve scrutiny before shipping.
Do not assign a universal fixed score to all new contracts. Consider affected users,
trigger frequency, migration complexity, recoverability, and available recovery
effort. Personal acknowledgment does not erase actual harm and must not be inferred
from ADR status or authorship.

## Maintenance

Keep rules technology-independent: frameworks and paths are anchors for primary
data, compatibility, external identity, capability, packaging, or operational risk.
Keep the detector read-only and ref-specific. Preserve concrete awareness values,
unverified shipping/consumer/recovery evidence, and short diffs in JSON and verbose
Markdown. Script-default Markdown groups candidates into a compact overview and clearly
discloses that contextual review is required. Do not mistake that overview for the
final assessment or restrict investigation to its matches. Keep overall release
risks primary in the final report, followed by the selected contract supplement
with short verified source diffs; see [reporting.md](reporting.md). Important
contracts remain reportable when appropriate and unscored. Group related
obligations so brevity does not hide a material storage or external commitment.
Use generic Git fixtures for behavior regression; do not hard-code app histories.
