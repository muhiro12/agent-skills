---
name: repo-consistency-refiner
description: "Audit structural, architectural, workflow, and documentation consistency within one repository. Use to identify evidence-backed drift and optionally apply requested low-risk refinements."
---

# Repo Consistency Refiner

## Overview

Use this skill as a repository gardener for one repository at a time.
Default to report-only, keep explanations concise, and always cite concrete file paths.
Never modify files outside the current repository.
Use cross-repository constraints only when supplied by the request or applicable contracts; do not discover personal archives or owner-specific profiles.

## Workflow

1. Resolve the repository scope.
- Use the current workspace root unless the user provides a narrower repository path inside the same workspace.
- Treat sibling repositories, external worktrees, and referenced shared packages as out of scope for edits.
- Read `AGENTS.md` first when present and use it as a repository-specific convention baseline.

2. Identify the governing constraints.
- Use current repository conventions and explicit task requirements for architectural direction, naming, maintainability, and documentation expectations.
- Distinguish supplied preferences from requirements established by code or the repository contract.

3. Build a small consistency map before judging details.
- Inspect top-level layout and entry points first.
- Prioritize files and directories such as `README*`, `AGENTS.md`, `Package.swift`, `pyproject.toml`, `Cargo.toml`, `package.json`, `.xcodeproj`, `.xcworkspace`, `ci_scripts/`, `.github/workflows/`, hook configs such as `.pre-commit-config.yaml`, `verify.sh`, `.build/`, `docs/`, `adr/`, and architecture overviews.
- Prefer fast inventory commands such as `rg --files`, shallow `find`, and targeted `rg` searches over loading large trees.
- Respect `.gitignore` and exclude generated, vendored, cached, private-data, and runtime-owned trees from recursive inventory. Never recursively enumerate `.build`; inspect only its shallow convention and, when the current repository contract explicitly uses `.build/ci/runs/<RUN_ID>`, the newest run needed for the current judgment.
- Never scan older runs under `.build/ci/runs`; one newest contract-owned run is the maximum evidence scope for a single consistency audit.
- Use Git metadata when available to confirm tracked structure or recent drift, but keep the audit focused on consistency, not feature review.

4. Evaluate the repository with four consistency lenses.
- Use `references/consistency-lenses.md` as the checklist for structural, architectural, workflow, and documentation signals.
- Compare similar areas against each other instead of judging files in isolation.
- Look for drift that raises cognitive load: similar patterns implemented differently, inconsistent naming, mixed ownership of the same responsibility, and docs that no longer match the codebase.
- Distinguish harmful inconsistency from intentional divergence that matches an explicitly supplied architectural or workflow constraint.

5. Classify findings carefully.
- Put each finding into exactly one primary category: structural, architectural, workflow, or documentation.
- Distinguish clearly between confirmed inconsistency, probable drift or ambiguity, and healthy aligned patterns worth preserving.
- Cite repository-relative file paths for every meaningful finding.

6. Propose improvements with maintenance leverage first.
- Prioritize changes that make the repository more predictable for the next contributor.
- Prefer convention alignment, naming cleanup, documentation correction, script consolidation, or boundary clarification over broad refactors.
- State likely blast radius when a recommendation would touch many files or public APIs.
- Say explicitly when a recommendation is driven by an explicitly supplied architectural or workflow constraint.

7. Edit only on explicit request.
- Stay report-only by default.
- If the user explicitly asks for implementation, limit changes to minimal low-risk refinements inside the current repository.
- Safe examples include small documentation corrections, internal naming normalization, lightweight script/help-text cleanup, or folder/readme alignment.
- Do not perform large moves, module splits, public API renames, or cross-repository edits automatically.

## Evaluation Rules

### Structural

- Compare directory organization, module boundaries, file placement, test placement, and naming conventions.
- Flag cases where similar modules use different folder shapes or filename suffixes without a clear framework-driven reason.
- Treat duplicated concepts split across multiple locations as a structural smell when ownership is unclear.

### Architectural

- Check whether domain logic leaks into UI, persistence leaks into views/controllers, or service and adapter roles are mixed differently across similar features.
- Compare routing, dependency wiring, shared-library usage, and data-access boundaries between equivalent surfaces.
- Treat concept drift as architectural inconsistency even when both implementations appear functional.

### Workflow

- Inspect `ci_scripts/`, `.github/workflows/`, `verify.sh`, hook configs, shallow `.build/` conventions, and contributor instructions.
- Flag duplicated verification entry points, stale script names, inconsistent artifact locations, or repository rules documented in `AGENTS.md` that the codebase no longer follows.
- Flag heavy verification attached to commit-time hooks when the repository already has a better direct-shell or push-time path.
- Prefer maintainability and predictability concerns over one-off local quirks.

### Documentation

- Compare `README`, overview docs, architecture notes, ADRs, and contributor guides against the current code layout and actual commands.
- Flag missing documentation only when the absence materially hurts predictability, onboarding, or safe changes.
- Distinguish stale docs from intentionally high-level docs.

## Output Contract

Report concisely using these sections in the conversation's language:

1. `Consistency summary`
2. `Structural inconsistencies`
3. `Architectural inconsistencies`
4. `Workflow inconsistencies`
5. `Documentation inconsistencies`
6. `Prioritized improvements`

For each inconsistency section:

- Write `No findings` when no meaningful inconsistency is found.
- Otherwise, list only the highest-signal findings first.
- Explain why each mismatch increases maintenance cost, confusion, or unpredictability.
- Include concrete repository-relative file paths.

For `Prioritized improvements`:

- Order items by maintenance leverage first and implementation risk second.
- Mark each item as `low`, `medium`, or `high` risk.
- Distinguish clearly between report-only recommendations and changes that are safe to implement now.

## Verification

- Confirm the inspected repository scope is explicit.
- Identify any supplied preference that materially affected the judgment.
- Confirm every finding is assigned to exactly one primary category.
- Confirm the report cites concrete file paths for material findings.
- Confirm recommendations stay inside the current repository.
- Confirm the report remains concise and does not collapse into a raw file inventory.
