# Schema Design and Migration Review

5. Review relationship design.
- Infer one-to-one, one-to-many, and many-to-many style patterns from scalar vs collection properties and the matching side when present.
- Check whether inverse relationships appear symmetric and intentional.
- Call out collection relationships that may rely on array ordering or unstable graph mutation semantics.
- Flag delete rules that look dangerous for long-lived data, especially wide `cascade`, ambiguous `nullify`, or missing inverse on tightly coupled graphs.
- Call out cyclic references or dense relationship clusters that may complicate maintenance and migration.

6. Review schema quality from an architecture perspective.
- Check naming clarity and whether model names map cleanly to app concepts.
- Check optionality consistency and whether defaults appear to hide invalid states.
- Check for mixed responsibilities inside one model.
- Check for over-denormalization, under-modeling, or business logic leaking into persistence structure.
- Check uniqueness and identity assumptions, including whether duplicates are possible by accident.
- Check migration hotspots such as:
  - non-optional property additions without obvious defaults
  - enum/raw-value persistence that may be brittle if cases evolve
  - relationship cardinality changes
  - delete-rule changes
  - renames that lack versioned schema or migration structure
- If widgets, intents, watch targets, or extensions are present, mention tight coupling that may make cross-target reuse harder.

### Relationship Review

- Use scalar reference plus matching scalar reference as a likely one-to-one pattern.
- Use scalar reference plus collection reference as a likely one-to-many pattern.
- Use collection on both sides as a likely many-to-many pattern.
- If only one side is visible, describe the intended cardinality as inferred and incomplete.

### Migration Risk

- Prioritize risks that can break existing stores or force destructive migration.
- Treat persisted enum/raw-value changes, uniqueness changes, and required-field additions as high-signal migration hotspots.
- Treat relationship graph churn as a practical risk even when the code still compiles.
