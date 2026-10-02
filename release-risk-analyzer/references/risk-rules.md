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

Ordinary release versions, format-only equal values, and Swift logical renames with
unchanged storage/wire/registered contracts have no contract contribution. Defaults
for disposable preferences or caches are not primary data. Intentional random
eight-character keys need no naming correction. Shipped IDs need no cosmetic rename.
Version consumers that alter migrations, gates, or formats are separate effects;
co-located identity, capability, minimum-OS, or schema changes remain reviewable.

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
Keep the detector read-only and ref-specific. Include concrete awareness values,
unverified shipping/consumer/recovery evidence, and short diffs in both outputs.
Use generic Git fixtures for behavior regression; do not hard-code app histories.
