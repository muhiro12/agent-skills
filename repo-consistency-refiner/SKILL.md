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

4. Evaluate only the consistency lenses relevant to the requested scope.
- Consult `references/consistency-lenses.md` for the relevant structural, architectural, workflow, or documentation signals; a focused request does not require all four.
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

## Report

Lead with the conclusion and highest-signal findings, supported by concrete paths
and the maintenance impact. Group by structural, architectural, workflow, or
documentation category when useful; omit empty categories. A focused request needs
no full-repository report. Distinguish confirmed drift, uncertainty, and intentional
differences worth preserving.

Prioritize improvements by maintenance benefit and implementation risk. Identify
broad API or file impacts and distinguish recommendations from completed edits.

## Verification

- Confirm the inspected repository scope is explicit.
- Identify any supplied preference that materially affected the judgment.
- Confirm every finding is assigned to exactly one primary category.
- Confirm the report cites concrete file paths for material findings.
- Confirm recommendations stay inside the current repository.
- Confirm the report remains concise and does not collapse into a raw file inventory.
