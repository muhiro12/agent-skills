---
name: respect-incomes-architecture
description: Compare the current repository's architecture with a resolved read-only Incomes checkout when that comparison is requested or materially useful. Preserve app-local behavior and avoid copying incidental tooling or product complexity.
---

# Respect Incomes Architecture

Compare the current repository with Incomes only for the architectural or
workflow question at hand. Inspect the target's code and `AGENTS.md` first.
The current repository is the only writable target; reference checkouts stay
read-only. A comparison request alone does not authorize implementation.

## Resolve the Reference Once

Resolve `<incomes-root>` in this order:

1. An explicit path from the user or repository contract.
2. An `Incomes` sibling of the target's Git root.
3. `$HOME/Repositories/Incomes` when it exists.

Canonicalize the path and require an existing readable directory distinct from
the writable target. If unavailable, report that boundary and continue with
current repository evidence; do not guess another checkout.

## Compare Intent and Boundaries

Consult the relevant developer-principle domain for judgment-heavy decisions;
reuse already-read, current guidance. Current user instructions and repository
constraints override older principles. If they designate a maintained platform
foundation such as MHPlatform for this concern, resolve that reference from the
supplied evidence and inspect only relevant files, read-only. Incomes does not
supersede that source of truth.

Compare only the requested boundaries: app adapters and shared libraries,
responsibility and naming, repository contracts, documentation, or verification.
Use concrete paths to explain the problem each reference pattern solves.
Inspect build artifacts only when needed for a specific claim; do not scan
cached runs as a general comparison step.

Classify material differences as **Align**, **Adapt**, or **Keep as is**:

- Align with a demonstrated reusable pattern when it improves the target.
- Adapt for the target's framework, product, lifecycle, and maintenance needs.
- Keep the target's better solution or intentional divergence.

Do not copy finance models, product behavior, UI flows, legacy complexity, or
incidental scripts and artifact layouts. Shared dependencies need demonstrated
reuse, not visual symmetry. Call out weak or stale reference patterns explicitly.
For Apple verification, preserve the target's Xcode-native workflow and required
evidence; a reference shell script does not automatically become a local gate.

## Complete the Requested Outcome

Implement only when requested, inside the current repository, with its own
verification contract. Never patch Incomes or another reference checkout through
this workflow. Ask only for an unresolved choice that materially changes the
architecture and cannot be settled from current evidence.

Report the conclusion, concrete reference paths, material differences and their
reasoning, and any changes, verification, or unresolved limitations that apply.
A focused comparison needs no fixed multi-section report or unrelated audit.
