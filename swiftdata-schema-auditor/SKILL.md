---
name: swiftdata-schema-auditor
description: "Inspect SwiftData entities, stored properties, relationships, and migration hotspots. Use for a read-only schema inventory or design explanation; use swiftdata-dev for implementation and persistence failures."
---

# SwiftData Schema Auditor

Inspect SwiftData model code read-only. Use the requested repository and scope;
implementation or runtime persistence debugging belongs to `swiftdata-dev`.
Prefer matching guidance from the active skill inventory; use the generated
Xcode catalog only for unresolved discovery and reuse current prior selections.

## Inventory or Explain

Search source declarations for `@Model`, `@Relationship`, `@Attribute`,
`@Transient`, `VersionedSchema`, migration plans, `ModelContainer`, and
`ModelConfiguration`. Exclude generated trees, build artifacts, dependency
checkouts, and caches unless requested.

For the requested entities, record source paths, stored properties and types,
optionality, visible defaults, relationships, inverse declarations, delete rules,
collection shape, and identity hints. Include computed/helpers only when useful
to distinguish them from persistent state. Identify versioned schema and migration
entrypoints when present without expanding an inventory into a migration audit.

- Treat stored properties as persisted candidates unless source evidence such
  as `@Transient`, computed accessors, or `static` indicates otherwise.
- Label initializer-only defaults as constructor defaults, not declaration defaults.
- Distinguish explicit declarations from inferred cardinality or macro behavior.
  A relationship visible from one side alone is incomplete evidence.
- Do not claim database column names, deployed schema, or actual store behavior
  from source declarations alone. Mark hidden or unresolved storage as ambiguous.
- If no models are found, report the searched scope and signals.

## Design or Migration Review

When the request includes relationship correctness, design quality, or migration
risk, read [design review](references/design-review.md) and apply only the relevant
lenses. Prioritize existing-store compatibility and destructive graph changes.
An inventory request does not require a broad architecture review, generated
improvement list, or a mandatory migration finding. Report a concrete material
risk encountered during inspection even if a broader audit was not requested.

## Evidence and Output

Use a compact inventory, diagram, or explanation appropriate to the request.
Every entity and material finding needs a source path. Separate source facts,
inferences, and unresolved questions; describe code-level patterns rather than
generic SwiftData advice. For reviews, prioritize actionable observed risks and
state when no issue was found. Keep the default workflow read-only.
