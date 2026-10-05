#!/usr/bin/env python3
"""Check publication tools and passively scan an immutable outgoing Git range."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


class Incomplete(Exception):
    """Required evidence is unavailable; never treat this as a clean scan."""


def clean_env():
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("GIT_", "GITLEAKS_", "BETTERLEAKS_"))}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull,
               GIT_CONFIG_NOSYSTEM="1", GIT_NO_REPLACE_OBJECTS="1",
               GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0", GIT_PAGER="cat",
               LC_ALL="C")
    return env


def run(argv, *, cwd=None, timeout=30):
    try:
        return subprocess.run(argv, cwd=cwd, env=clean_env(), capture_output=True,
                              text=True, errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Incomplete("A required command could not complete.") from exc


def check_tool(name):
    executable = shutil.which(name)
    if not executable:
        raise Incomplete(f"Required tool '{name}' is missing from PATH.")
    result = run([executable, "version" if name == "betterleaks" else "--version"])
    first = result.stdout.splitlines()[0] if result.stdout else ""
    if result.returncode:
        raise Incomplete(f"Required tool '{name}' did not report its version.")
    if name == "rg":
        match = re.fullmatch(r"ripgrep (15\.2\.\d+)", first)
    elif name == "betterleaks":
        match = re.fullmatch(r"(1\.9\.0)", first)
    else:
        match = re.fullmatch(r"git version (2\.(\d+)\.\d+(?:[ .].*)?)", first)
        if match and int(match.group(2)) < 38:
            match = None
    if not match:
        raise Incomplete(f"Required tool '{name}' has an unsupported version.")
    return {"path": executable, "version": match.group(1)}


def git(repo, *args):
    result = run(["git", "-C", str(repo), *args])
    if result.returncode:
        raise Incomplete("Required local Git objects or range evidence are unavailable.")
    return result.stdout.strip()


def scan(repo, head, base, new_ref):
    tools = {name: check_tool(name) for name in ("git", "betterleaks")}
    repo = Path(repo).resolve()
    if git(repo, "rev-parse", "--is-shallow-repository") != "false":
        raise Incomplete("Shallow history cannot establish the outgoing commit set.")
    git_dir = Path(git(repo, "rev-parse", "--absolute-git-dir"))
    common_dir = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    if (common_dir / "info" / "grafts").exists():
        raise Incomplete("Legacy grafts change history traversal; review them separately.")
    partial = run(["git", "-C", str(repo), "config", "--local", "--get-regexp",
                   r"^(extensions\.partialclone|remote\..*\.promisor)$"])
    if partial.returncode not in (0, 1):
        raise Incomplete("Local Git object availability could not be established.")
    if partial.returncode == 0 or any((common_dir / "objects" / "pack").glob("*.promisor")):
        raise Incomplete("Partial clone history needs a separately prepared complete snapshot.")
    for oid in (head, base):
        if oid is None:
            continue
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid):
            raise Incomplete("Supply immutable full commit OIDs, not revision expressions.")
        if git(repo, "rev-parse", "--verify", oid + "^{commit}") != oid:
            raise Incomplete("The supplied object is not the selected commit.")
    if not new_ref:
        ancestor = run(["git", "-C", str(repo), "merge-base", "--is-ancestor", base, head])
        if ancestor.returncode:
            raise Incomplete("This helper supports fast-forward updates and new refs only.")
    revision = head if new_ref else f"{base}..{head}"
    commits_text = git(repo, "rev-list", "--topo-order", revision, "--")
    commits = sorted(commits_text.splitlines()) if commits_text else []
    # Scan the Git directory rather than the worktree. Upstream also loads ignore
    # files from its source directory, even with an explicit ignore-path flag.
    for name in (".betterleaksignore", ".gitleaksignore"):
        if (git_dir / name).exists() or (git_dir / name).is_symlink():
            raise Incomplete("A scanner ignore file in the Git directory needs review.")
    # Explicit options preserve merge changes and avoid local textconv/diff drivers.
    log_opts = ("--full-history --root --diff-merges=separate --no-renames "
                "--no-ext-diff --no-textconv --no-show-signature --no-color --format=medium "
                + revision + " --")
    with tempfile.TemporaryDirectory(prefix="publication-scan-") as temporary:
        private = Path(temporary)
        config = private / "default-rules.toml"
        config.write_text("[extend]\nuseDefault = true\n", encoding="utf-8")
        config.chmod(0o600)
        report = private / "findings.json"
        command = [tools["betterleaks"]["path"], "git", str(git_dir),
                   "--config", str(config), "--gitleaks-ignore-path", str(private),
                   "--ignore-gitleaks-allow", "--validation=false", "--redact=100",
                   "--no-banner", "--no-color", "--log-level=error",
                   "--exit-code=17", "--report-format=json", "--report-path", str(report),
                   "--log-opts", log_opts]
        result = run(command, cwd=private, timeout=600)
        if result.returncode not in (0, 17) or result.stderr.strip():
            raise Incomplete("Betterleaks reported a scan error; raw output is withheld.")
        try:
            findings = json.loads(report.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise Incomplete("Betterleaks did not produce a valid JSON report.") from exc
        if not isinstance(findings, list) or bool(findings) != (result.returncode == 17):
            raise Incomplete("Betterleaks exit status and findings disagree.")
        safe_findings = []
        for finding in findings:
            if not isinstance(finding, dict) or finding.get("Commit") not in commits:
                raise Incomplete("A finding does not belong to the reviewed commit set.")
            # Discard match, secret, context, author, message, links and arbitrary
            # extension fields. Even a redacted upstream report contains metadata.
            safe_findings.append({key: finding.get(key) for key in
                                  ("RuleID", "Commit", "File", "StartLine", "EndLine")})
    return {"status": "findings" if safe_findings else "clean",
            "scanner": "betterleaks", "scanner_version": tools["betterleaks"]["version"],
            "head": head, "base": base, "new_ref": new_ref, "commits": commits,
            "validation": False, "findings": safe_findings,
            "scope": "added text in outgoing Git patches, including separate merge diffs",
            "exclusions": ["uncommitted and untracked files", "commit/tag metadata",
                           "non-archive binary content, LFS and submodule content",
                           "default-rule allowlists and decoder/archive depth limits"]}


def write_report(path, record):
    # Refuse overwrites, symlinks and stale output; keep findings paths private.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check")
    check.add_argument("--tool", choices=("all", "search", "scanner"), default="all")
    scan_parser = commands.add_parser("scan")
    scan_parser.add_argument("--repo", required=True)
    scan_parser.add_argument("--head", required=True)
    boundary = scan_parser.add_mutually_exclusive_group(required=True)
    boundary.add_argument("--base")
    boundary.add_argument("--new-ref", action="store_true")
    scan_parser.add_argument("--report", required=True)
    args = parser.parse_args()
    try:
        if args.command == "check":
            names = {"all": ("rg", "git", "betterleaks"), "search": ("rg",),
                     "scanner": ("git", "betterleaks")}[args.tool]
            tools = {name: check_tool(name) for name in names}
            print(json.dumps({"status": "available", "tools": tools}))
            return 0
        if Path(args.report).exists() or Path(args.report).is_symlink():
            raise Incomplete("Select a new private report path; existing output is preserved.")
        record = scan(args.repo, args.head, args.base, args.new_ref)
        write_report(args.report, record)
        print(json.dumps({"status": record["status"], "commits": len(record["commits"]),
                          "findings": len(record["findings"]), "validation": False}))
        return 1 if record["findings"] else 0
    except (Incomplete, OSError) as exc:
        print(json.dumps({"status": "incomplete", "reason": str(exc)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
