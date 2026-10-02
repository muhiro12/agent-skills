---
name: release-risk-analyzer
description: "Review and report release risk between a previous public release and a candidate, prioritizing primary-data loss and published compatibility obligations. Use for pre-release assessment; do not implement fixes or perform release operations."
---

# Release Risk Analyzer

## Scope and boundaries

This skill reviews and reports only. Do not edit the reviewed repository, run
migrations, change versions, commit, push, or distribute a build. Recommend concrete
checks or fixes without performing them. A score is review priority, not failure
probability, permission to ship, or an operation-approval gate.

## Workflow

1. Establish the comparison.
- Normally compare the previous **public** release with the candidate. The script's
  latest reachable tag is a source-range fallback, not proof of public distribution.
- Use `--base-ref`, `--head-ref`, or `--tag-pattern` to select the intended sources.
  Follow an explicit request for previous -> current -> next or longer history.
- Identify the distributed version/build and its source when evidence is available.
  Distinguish archive/build source from tag source; report an unknown correspondence.
- Separate shipped contracts, candidate additions, unpublished prototypes, and
  development-only state. Git ancestry alone does not establish shipping status.

2. Generate candidate evidence using the bundled rules, without external rule files.

```bash
python3 scripts/review_release_risk.py --repo /path/to/repository --format markdown
```

Read [references/risk-rules.md](references/risk-rules.md) for interpretation and
scoring. The script reads source at the selected refs, not the working-tree version.
Its matches are review candidates; inspect context, consumers, guards, and recovery
sources before treating them as defects. Regex or path matches prove neither harm
nor safety.

3. Review consequences in this order.
- First, loss or corruption of long-term users' primary data, especially loss of
  all restoration sources. Distinguish already-saved rows lost through writes from
  a crash, inaccessible export, retired selection state, or a derived-cache reset.
- Check the original database, required sidecars, backups, and other viable copies.
  A SQLite filename remaining does not prove recoverability; a consistent retained
  store with required sidecars is different from complete loss. Trace error paths,
  including pending delete/update mutations persisted by a later save.
- Then inspect what publication commits the product to. A contract may belong to
  several classes: (1) identity fixed for the same published product, (2) changeable
  with risky technical migration or user guidance, (3) changeable while old schema,
  keys, readers, aliases, or migration code require long-term support.
- Do not call every obligation literally permanent. State its retirement evidence;
  without guaranteed retirement of old states, assume long-term compatibility work.
- Review actual schema/raw key/ID/type/default/serialized wire or file field/OS
  registered identifier values before publication. Check typos, naming mismatches,
  unused columns, speculative reserved fields, real consumers, and whether stored
  empty or recomputable values need to become contracts. A necessary new contract
  is an awareness item, not an automatic risk surcharge.
- Swift logical names are not contracts when storage/wire/registered values are
  unchanged. Intentional eight-character random defaults keys are valid; do not
  propose cosmetic renames of shipped identifiers. Defaults used for disposable UI
  preferences or derived caches do not gain risk merely because a raw key exists.
- Ordinary `MARKETING_VERSION` / `CURRENT_PROJECT_VERSION` updates contribute zero.
  Inspect version readers that drive migration, feature gates, or stored formats;
  score those effects separately. Never exempt co-located identity, entitlement,
  minimum-OS, schema, or other changes as part of a version bump.
- Judge reversible bugs using affected users, trigger frequency, recovery options,
  and available recovery effort. Do not block every unknown or every irreversible
  contract. An acknowledged change is not automatically harmless either.

4. Explain the assessment.
- Keep the existing category-maximum aggregation and small independent breadth
  modifiers. Count one cause once; path hints and awareness items do not add a
  second contribution for the same change. Explain any contextual adjustment from
  the script score. The script caps heuristic output at 95; reserve a final 100 for
  separately substantiated catastrophic loss, never a deletion regex alone.
- Bands remain `80-100=Block`, `60-79=Hold for review`, `40-59=Proceed with caution`,
  `20-39=Review recommended`, `0-19=Proceed`. A high score recommends pausing because
  of the stated consequences; it does not perform a release operation or require
  answers to every awareness item. Zero means no scored signal, not verified safety.
- Prioritize serious findings before general diff summaries. Use short relevant
  diff excerpts. Do not promote a path-only label into a confirmed severe defect.

## Report contract

Report in the conversation's language:

1. **Overall score and rationale:** score out of 100, band, strongest consequence,
   independent modifiers, evidence strength, and reasons for contextual adjustments.
2. **Scope:** public release/build/source -> candidate, refs/range, any history, and
   whether distributed-build source matches the tag source.
3. **Serious findings:** trigger, affected users/data, impact, retained/lost recovery
   sources, evidence, missing evidence, and recommended checks or remedies.
4. **Awareness and confirmation items:** concrete old/new raw values (including
   unchanged relevant values), introduction/shipping status, consumers, applicable
   contract classes, migration/user-guidance burden, future compatibility and
   retirement responsibility, evidence, and what remains unverified. Specify whether
   the candidate retains, replaces with an alias/reader, or retires old metadata and
   readers. A retirement record alone does not establish state regeneration.
5. **Unverified items:** the specific missing evidence and its effect on the judgment.

Keep technical verification separate from personal acknowledgment. Mark personal
awareness as explicitly evidenced or unconfirmed; `ADR Accepted`, account identity,
or commit authorship alone is not evidence of the user's approval. Report concrete
recognition items instead of asking many questions or making all replies mandatory.

## Verification

- Check the intended range and ref-specific source, mixed version changes, raw-value
  equality, contract classes, recovery distinctions, and independent scoring.
- Separate detection candidates, confirmed defects, completed verification, and
  remaining uncertainty. A source diff cannot prove distribution readiness.
- Preserve `risk_diff_snippets` in JSON and relevant snippets in Markdown.
- Use `--verbose` only when full file/commit listings help the review.
- When maintaining this skill, run its Git-fixture behavior tests and the repository
  verification contract. Tests should verify decisions and read-only behavior, not
  merely expected wording.
