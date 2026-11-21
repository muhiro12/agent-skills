# Operations and ordering

Where the app exposes shared business use cases through library Operations,
trace the changed action from its actual callers. Views and App Intents can
adapt presentation, parameters and results. The library owns shared decisions,
calculations and writes. If two surfaces implement the same business branch
or call internal helpers directly, look for the existing operation first.
Models, routes and wire types can have their own public contracts.

For an ordering change, identify what the order means. Find the defining query
or sort descriptors and trace consumers that depend on that same sequence,
including derived values and transfers that reconstruct the records. Preserve
the comparison, direction and tie breakers across those boundaries. A ranked
summary, a chronological balance and a deterministic file format can each
legitimately need a different order.

Use tied records that distinguish the old and intended comparisons. Check the
actual query order and its consumer's result together. If a tie breaker is
assigned at save time or lost in transit, also compare after saving or decoding.
