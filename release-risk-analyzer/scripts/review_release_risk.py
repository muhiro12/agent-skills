#!/usr/bin/env python3
"""Read-only release-risk evidence between selected Git sources."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from fnmatch import fnmatchcase
from pathlib import Path

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

SEVERITY_DEFAULT_SCORES = {
    "none": 0,
    "low": 5,
    "medium": 18,
    "high": 30,
    "critical": 50,
}

SEVERITY_LABELS = {
    "none": "なし",
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "重大",
}

SCORE_MAX = 100
HEURISTIC_SCORE_MAX = 95
FALLBACK_UNKNOWN_CHANGE_SCORE = 15

VERSION_ASSIGNMENT = re.compile(r'^\s*(?:MARKETING_VERSION|CURRENT_PROJECT_VERSION)\s*=\s*["\w.]+\s*;?\s*$')
VERSION_READER = r'CFBundleShortVersionString|CFBundleVersion|MARKETING_VERSION|CURRENT_PROJECT_VERSION'
EXPLICIT_RAW_CASE = re.compile(r'^\s*case\s+(\w+)\s*=\s*("(?:\\.|[^"\\])*"|\d+)\s*[,;]?\s*$')
CONFIG_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[\w.$]+|[^\s]')
DESTRUCTIVE_OPERATION = re.compile(r'\b(?:removeItem|deleteAll)\s*\(|\b(?:DROP\s+TABLE|DELETE\s+FROM)\b|\b\w*context\.delete\(', re.I)
CRASH_OPERATION = re.compile(r'\bfatalError\s*\(|\btry!\s')

BUILTIN_RULES = [
    {
        "name": "一意ID・外部固定設定の変更",
        "severity": "medium",
        "category": "external-identity-config",
        "score": 20,
        "mode": "any",
        "paths": [
            "**/*.xcodeproj/project.pbxproj",
            "**/Info.plist",
            "**/*.entitlements",
            "**/*.xcconfig",
            "project.yml",
            "project.yaml",
            "**/project.yml",
            "**/project.yaml",
            "**/*.storekit",
            "**/StoreKit/**",
        ],
        "reason": "外部登録済みの一意IDや配布・連携設定値は、誤って出すと既存アプリ、外部サービス、ユーザー導線へ長く残りやすい。",
        "advice": "既存の配布設定、外部連携、チーム/署名、購入/クラウド/ドメイン設定と照合し、新規作成や変更が意図的か確認する。",
    },
    {
        "name": "永続化領域・スキーマ互換性の変更",
        "severity": "medium",
        "category": "durable-state",
        "score": 20,
        "mode": "any",
        "paths": [
            "**/Persistence/**",
            "**/Database/**",
            "**/DB/**",
            "**/Realm/**",
            "**/CoreData/**",
            "**/Migration/**",
            "**/Migrations/**",
            "**/*Migration*.swift",
            "**/*Migrator*.swift",
            "**/Schema/**",
            "**/ModelContainerFactory.swift",
            "**/Database.swift",
            "**/*.sql",
            "**/*.sqlite",
            "**/*.xcdatamodeld/**",
        ],
        "reason": "端末やバックエンドに残る永続状態の構造・保存先・移行処理の変更は、既存ユーザーの起動不能やデータ不整合につながりやすい。",
        "advice": "既存データを持つ状態での起動、読み書き、移行、ロールバック時の扱いを先に確認する。",
    },
    {
        "name": "権限・セキュリティ面の変更",
        "severity": "medium",
        "category": "security-capability",
        "score": 20,
        "mode": "any",
        "paths": [
            "**/Auth/**",
            "**/Authentication/**",
            "**/Security/**",
            "**/Crypto/**",
            "**/Credential/**",
            "**/Token/**",
            "**/Session/**",
            "**/Keychain/**",
            "**/*.entitlements",
        ],
        "reason": "権限や認証まわりの変更は審査・起動・既存ユーザー導線に影響しやすい。",
        "advice": "不要な権限追加がないか、既存導線が壊れていないかを確認する。",
    },
    {
        "name": "ビルド・依存関係・CI の変更",
        "severity": "medium",
        "category": "packaging",
        "score": 20,
        "mode": "any",
        "paths": [
            ".github/workflows/**",
            "ci_scripts/**",
            "Dockerfile*",
            "docker/**",
            "**/*.xcodeproj/project.pbxproj",
            "Package.swift",
            "Package.resolved",
            "**/Package.resolved",
            "Podfile",
            "Podfile.lock",
            "Gemfile",
            "Gemfile.lock",
            "Cartfile",
            "Cartfile.resolved",
            "**/*.xcscheme",
        ],
        "reason": "ビルドや依存関係の変更は、コード差分以上に配布物へ影響することがある。",
        "advice": "クリーンビルドと配布フローを確認する。",
    },
    {
        "name": "共有ロジックの変更",
        "severity": "medium",
        "category": "shared-logic",
        "score": 15,
        "mode": "any",
        "paths": [
            "**/Domain/**",
            "**/Model/**",
            "**/Models/**",
            "**/UseCase/**",
            "**/Service/**",
            "**/Services/**",
            "**/Store/**",
            "**/Repository/**",
            "**/Repositories/**",
            "**/Provider/**",
            "**/Providers/**",
        ],
        "reason": "共有ロジックの変更は複数機能へ波及しやすい。",
        "advice": "変更機能だけでなく周辺導線も含めて回帰確認する。",
    },
    {
        "name": "API / 通信面の変更",
        "severity": "medium",
        "category": "networking",
        "score": 20,
        "mode": "any",
        "paths": [
            "**/API/**",
            "**/Network/**",
            "**/Networking/**",
            "**/HTTP/**",
            "**/Client/**",
            "**/Remote/**",
        ],
        "reason": "通信面の変更は実データ条件でのみ不具合化することがある。",
        "advice": "実データまたはステージング相当で通信経路を確認する。",
    },
    {
        "name": "UI・リソースのみの変更",
        "severity": "low",
        "category": "ui-resource",
        "score": 5,
        "mode": "all",
        "paths": [
            "Resources/**",
            "**/UI/**",
            "Views/**",
            "**/View/**",
            "**/Views/**",
            "Components/**",
            "**/Component/**",
            "**/Components/**",
            "**/Presentation/**",
            "**/Resources/**",
            "**/*.storyboard",
            "**/*.xib",
            "**/*.xcassets/**",
            "*.xcstrings",
            "**/*.xcstrings",
            "*.strings",
            "**/*.strings",
            "*.css",
            "**/*.css",
            "*.scss",
            "**/*.scss",
            "*.html",
            "**/*.html",
            "*.svg",
            "**/*.svg",
            "*.png",
            "**/*.png",
            "*.jpg",
            "**/*.jpg",
            "*.jpeg",
            "**/*.jpeg",
            "*.gif",
            "**/*.gif",
        ],
        "reason": "変更面が表示や同梱リソースに閉じている可能性が高い。",
        "advice": "対象画面の重点確認で進めやすい。",
    },
    {
        "name": "テスト・ドキュメントのみの変更",
        "severity": "low",
        "category": "tests-docs",
        "score": 0,
        "mode": "all",
        "paths": [
            "**/Tests/**",
            "docs/**",
            "*.md",
            "**/*.md",
            "*.txt",
            "**/*.txt",
        ],
        "reason": "テストやドキュメントのみの変更は通常、出荷挙動を直接変えにくい。",
        "advice": "生成物が意図せず変わっていないかだけ確認する。",
    },
]

IDENTIFIER_MARKER_PATTERNS = [
    re.compile(r"\bPRODUCT_BUNDLE_IDENTIFIER\s*=\s*([^;]+);?"),
    re.compile(r"\bDEVELOPMENT_TEAM\s*=\s*([^;]+);?"),
    re.compile(r"\bPROVISIONING_PROFILE_SPECIFIER\s*=\s*([^;]+);?"),
    re.compile(r"\bCODE_SIGN_ENTITLEMENTS\s*=\s*([^;]+);?"),
    re.compile(r"\b(?:CFBundleIdentifier|CFBundleURLName|CFBundleURLSchemes)\b"),
    re.compile(r"(group\.[A-Za-z0-9\.-]+)"),
    re.compile(r"(iCloud\.[A-Za-z0-9\.-]+)"),
    re.compile(r"(applinks:[^<>\s\",;]+)"),
    re.compile(r"(webcredentials:[^<>\s\",;]+)"),
    re.compile(r"(activitycontinuation:[^<>\s\",;]+)"),
    re.compile(r"(com\.apple\.security\.application-groups)"),
    re.compile(r"(com\.apple\.developer\.icloud-container-identifiers)"),
    re.compile(r"(com\.apple\.developer\.associated-domains)"),
    re.compile(r"(keychain-access-groups)"),
    re.compile(r"\b(?:productID|productIdentifier)\b\s*[:=]\s*\"([^\"]+)\""),
    re.compile(r"\bProduct\.products\s*\(\s*for:\s*(\[[^\]]+\])"),
]

CAPABILITY_MARKER_PATTERNS = [
    re.compile(
        r"<key>((?:NS[A-Za-z0-9]+UsageDescription)|(?:com\.apple\.[^<]+)|"
        r"(?:aps-environment)|(?:keychain-access-groups))</key>"
    ),
    re.compile(r"INFOPLIST_KEY_(NS[A-Za-z0-9]+UsageDescription)"),
    re.compile(r"(aps-environment|com\.apple\.developer\.[A-Za-z0-9\.-]+)"),
    re.compile(r"\bSystemCapabilities\b"),
]

PERSISTENT_USAGE_PATTERNS = [
    re.compile(r"@AppStorage\("),
    re.compile(r"\bAppStorage\("),
    re.compile(r"\bUserDefaults\("),
    re.compile(r"\.set\([^)]*forKey:"),
    re.compile(r"\.(?:string|bool|integer|double|object|data)\(forKey:"),
]

APP_STORAGE_CASE_PATTERN = re.compile(r"^\s*case\s+([A-Za-z_]\w*)\s*=")
MODEL_PROPERTY_PATTERN = re.compile(
    r"^\s*(?:(?:public|private|internal|fileprivate|open)\s+)*(?:private\(set\)\s+|public\(set\)\s+|package\(set\)\s+)*var\s+([A-Za-z_]\w*)\b"
)

DURABLE_STORAGE_INFRA_PATTERNS = [
    "**/Database.swift",
    "**/*Migrator*.swift",
    "**/ModelContainerFactory.swift",
    "**/*.xcdatamodeld/**",
    "**/*.sql",
    "**/*.sqlite",
]

DURABLE_MODEL_MARKERS = [
    "@Model",
    "NSManagedObject",
]

PERSISTENT_SETTINGS_PATTERNS = [
    "**/AppStorageKey.swift",
    "**/NotificationSettings.swift",
]

DEFAULT_IGNORE_USAGE_PATTERNS = [
    "**/Tests/**",
    "docs/**",
]


@dataclass
class Commit:
    hash: str
    short_hash: str
    date: str
    subject: str
    author: str


@dataclass
class FileChange:
    status: str
    path: str
    old_path: str | None = None


@dataclass
class RiskRule:
    name: str
    severity: str
    category: str
    score: int
    mode: str
    paths: list[str]
    exclude_paths: list[str]
    reason: str
    advice: str


@dataclass
class RiskSignal:
    name: str
    severity: str
    category: str
    score: int
    mode: str
    reason: str
    advice: str
    matched_files: list[str]


@dataclass
class DiffLines:
    added: list[str]
    removed: list[str]
    changed: list[str] = field(default_factory=list)


@dataclass
class DiffSnippet:
    title: str
    category: str
    source: str
    file: str
    lines: list[str]


@dataclass
class ReviewFinding:
    title: str
    severity: str
    category: str
    score: int
    reason: str
    advice: str
    files: list[str]
    evidence: list[str]
    risk_id: str = ""
    covered_lines: list[str] = field(default_factory=list)
    verification_status: str = "candidate; semantics, guards, scope and recovery unverified"


@dataclass
class AwarenessItem:
    title: str
    category: str
    files: list[str]
    contract_values: list[str]
    introduction_status: str
    consumers: list[str]
    contract_classes: list[str]
    migration_burden: str
    future_responsibility: str
    evidence: list[str]
    classification_status: str = "candidate classes; actual applicability and support lifetime unverified"
    verification_status: str = "source evidence only; runtime and distribution unverified"
    acknowledgment_status: str = "unconfirmed; ADR status and authorship are not personal acknowledgment"


class GitCommandError(RuntimeError):
    """Raised when a git command fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assess release-blocking risk between the latest tag and a target ref.",
    )
    parser.add_argument("--repo", required=True, help="Path to the git repository")
    parser.add_argument("--base-ref", help="Base git ref. Defaults to the latest reachable tag.")
    parser.add_argument("--head-ref", default="HEAD", help="Head git ref. Defaults to HEAD.")
    parser.add_argument(
        "--tag-pattern",
        help="Optional glob passed to git describe --match when auto-detecting the base tag.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=20,
        help="Maximum changed files to print in verbose markdown output",
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=20,
        help="Maximum commits to print in verbose markdown output",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Expand candidate evidence, score breakdown, diffs, file and commit sections in markdown output",
    )
    return parser.parse_args()


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise GitCommandError(message)
    return result.stdout.strip()


def normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized or path


def short_ref(repo: Path, ref: str) -> str:
    return run_git(repo, "rev-parse", "--short", ref)


def detect_base_ref(repo: Path, head_ref: str, tag_pattern: str | None) -> str:
    args = ["describe", "--tags", "--abbrev=0"]
    if tag_pattern:
        args.extend(["--match", tag_pattern])
    args.append(head_ref)
    base_ref = run_git(repo, *args)
    if not base_ref:
        raise GitCommandError("到達可能なタグが見つかりません。--base-ref を指定してください。")
    return base_ref


def load_rules_from_dicts(raw_rules: list[dict]) -> list[RiskRule]:
    rules: list[RiskRule] = []
    for raw_rule in raw_rules:
        rules.append(
            RiskRule(
                name=raw_rule["name"],
                severity=raw_rule["severity"],
                category=raw_rule.get("category", raw_rule["name"]),
                score=int(raw_rule.get("score", SEVERITY_DEFAULT_SCORES[raw_rule["severity"]])),
                mode=raw_rule.get("mode", "any"),
                paths=[normalize_path(pattern) for pattern in raw_rule["paths"]],
                exclude_paths=[normalize_path(pattern) for pattern in raw_rule.get("exclude_paths", [])],
                reason=raw_rule.get("reason", ""),
                advice=raw_rule.get("advice", ""),
            )
        )
    return rules


def path_matches(path: str, patterns: list[str]) -> bool:
    return any(
        fnmatchcase(path, pattern)
        or (pattern.startswith("**/") and fnmatchcase(path, pattern[3:]))
        for pattern in patterns
    )


def evaluate_rule(rule: RiskRule, files: list[FileChange]) -> RiskSignal | None:
    if not files:
        return None

    matched_files = [
        file.path
        for file in files
        if path_matches(file.path, rule.paths)
        and not path_matches(file.path, rule.exclude_paths)
    ]

    if rule.mode == "any":
        if not matched_files:
            return None
    else:
        if len(matched_files) != len(files):
            return None

    return RiskSignal(
        name=rule.name,
        severity=rule.severity,
        category=rule.category,
        score=rule.score,
        mode=rule.mode,
        reason=rule.reason,
        advice=rule.advice,
        matched_files=sorted(set(matched_files)),
    )


def get_commits(repo: Path, base_ref: str, head_ref: str) -> list[Commit]:
    output = run_git(
        repo,
        "log",
        "--date=short",
        "--reverse",
        "--pretty=format:%H%x1f%h%x1f%ad%x1f%s%x1f%an",
        f"{base_ref}..{head_ref}",
    )
    if not output:
        return []

    commits: list[Commit] = []
    for line in output.splitlines():
        full_hash, short_hash, date, subject, author = line.split("\x1f")
        commits.append(
            Commit(
                hash=full_hash,
                short_hash=short_hash,
                date=date,
                subject=subject,
                author=author,
            )
        )
    return commits


def get_files(repo: Path, base_ref: str, head_ref: str) -> list[FileChange]:
    output = run_git(repo, "diff", "--no-ext-diff", "--no-textconv", "--name-status", "--find-renames", f"{base_ref}..{head_ref}")
    if not output:
        return []

    files: list[FileChange] = []
    for line in output.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            files.append(
                FileChange(
                    status="R",
                    old_path=normalize_path(parts[1]),
                    path=normalize_path(parts[2]),
                )
            )
            continue

        if len(parts) >= 2:
            files.append(FileChange(status=status, path=normalize_path(parts[1])))

    return files


def get_diff_lines(repo: Path, base_ref: str, head_ref: str, files: list[FileChange]) -> dict[str, DiffLines]:
    diffs: dict[str, DiffLines] = {}
    for file in files:
        patch = run_git(
            repo,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--unified=0",
            "--no-color",
            f"{base_ref}..{head_ref}",
            "--",
            *([file.old_path] if file.old_path else []),
            file.path,
        )
        added: list[str] = []
        removed: list[str] = []
        changed: list[str] = []
        for line in patch.splitlines():
            if line.startswith("+++ ") or line.startswith("--- "):
                continue
            if line.startswith("@@"):
                changed.append(line)
                continue
            if line.startswith("+"):
                changed.append(line)
                added.append(line[1:])
                continue
            if line.startswith("-"):
                changed.append(line)
                removed.append(line[1:])
        diffs[file.path] = DiffLines(added=added, removed=removed, changed=changed)
    return diffs


def read_file(repo: Path, path: str, ref: str = "HEAD") -> str:
    if Path(path).suffix.lower() in {".sqlite", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip"}:
        return ""
    try:
        return run_git(repo, "show", f"{ref}:{path}")
    except GitCommandError:
        return ""


def top_areas(files: list[FileChange], limit: int = 5) -> list[dict[str, int | str]]:
    counter: Counter[str] = Counter()
    for file in files:
        parts = Path(file.path).parts
        if not parts:
            continue
        if len(parts) >= 2 and not parts[0].startswith("."):
            label = "/".join(parts[:2])
        else:
            label = parts[0]
        counter[label] += 1

    return [{"area": area, "count": count} for area, count in counter.most_common(limit)]


def truncate_list(values: list[str], limit: int) -> list[str]:
    if len(values) <= limit:
        return values
    remaining = len(values) - limit
    return [*values[:limit], f"... (+{remaining} 件)"]


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def collect_markers(lines: list[str], patterns: list[re.Pattern[str]]) -> list[str]:
    markers: list[str] = []
    for line in lines:
        stripped = line.strip()
        for pattern in patterns:
            match = pattern.search(stripped)
            if not match:
                continue
            markers.append(match.group(1) if match.groups() else stripped)
            break
    return unique(markers)


def find_model_properties(lines: list[str]) -> list[str]:
    properties: list[str] = []
    for line in lines:
        stripped = line.strip()
        if "(" in stripped and "=" not in stripped and ":" not in stripped:
            continue
        match = MODEL_PROPERTY_PATTERN.match(stripped)
        if not match:
            continue
        properties.append(match.group(1))
    return unique(properties)


def matches_any(path: str, patterns: list[str]) -> bool:
    return path_matches(path, patterns)


def has_durable_model_marker(content: str, diff: DiffLines) -> bool:
    changed_lines = [*diff.added, *diff.removed]
    return (
        any(marker in content for marker in DURABLE_MODEL_MARKERS)
        or ("Object" in content and "Realm" in content)
        or any(marker in line for line in changed_lines for marker in DURABLE_MODEL_MARKERS)
    )


def tokens(content: str) -> list[str]:
    return CONFIG_TOKEN.findall(content)


def raw_cases(content: str) -> dict[str, str]:
    return {match.group(1): match.group(2) for line in content.splitlines()
            if (match := EXPLICIT_RAW_CASE.match(line))}


def changed_source(diff: DiffLines) -> list[str]:
    return [line for line in [*diff.removed, *diff.added] if line.strip()]


def config_contract_values(repo: Path, file: FileChange, diff: DiffLines, base: str, head: str, *, capability: bool = False) -> tuple[list[str], list[str]]:
    patterns = CAPABILITY_MARKER_PATTERNS if capability else IDENTIFIER_MARKER_PATTERNS
    if file.path.endswith((".plist", ".entitlements")):
        try:
            old = plistlib.loads(read_file(repo, file.old_path or file.path, base).encode()) if file.status != "A" else {}
            new = plistlib.loads(read_file(repo, file.path, head).encode()) if file.status != "D" else {}
            if isinstance(old, dict) and isinstance(new, dict):
                identity_keys = {"CFBundleIdentifier", "CFBundleURLTypes", "com.apple.security.application-groups",
                                 "com.apple.developer.icloud-container-identifiers", "com.apple.developer.associated-domains", "keychain-access-groups"}
                def selected(key: str) -> bool:
                    if capability:
                        return key not in identity_keys and bool(re.match(r"NS.*UsageDescription$|com\.apple\.|aps-environment$", key))
                    return key in identity_keys
                keys = [key for key in sorted(set(old) | set(new)) if selected(key)]
                changed = [key for key in keys if old.get(key) != new.get(key) or (key in old) != (key in new)]
                if changed:
                    keys = changed
                elif not any(collect_markers([line], patterns) for line in changed_source(diff)):
                    keys = []
                def values(content: dict) -> list[str]:
                    return [f"{key} = {json.dumps(content[key], ensure_ascii=False, sort_keys=True)}" for key in keys if key in content]
                return values(old), values(new)
        except (ValueError, plistlib.InvalidFileException, OverflowError):
            pass
    return collect_markers(diff.removed, patterns), collect_markers(diff.added, patterns)


def nonrisk_reason(repo: Path, file: FileChange, diff: DiffLines, base: str, head: str) -> str:
    if file.status != "M":
        return ""
    old = read_file(repo, file.old_path or file.path, base)
    new = read_file(repo, file.path, head)
    if file.path.endswith((".plist", ".entitlements")):
        try:
            if plistlib.loads(old.encode()) == plistlib.loads(new.encode()):
                return "format-equivalent"
        except (ValueError, plistlib.InvalidFileException, OverflowError):
            pass
    elif file.path.endswith((".pbxproj", ".xcconfig")) and old and new and tokens(old) == tokens(new):
        return "format-equivalent"
    lines = changed_source(diff)
    if file.path.endswith((".pbxproj", ".xcconfig")) and lines and all(VERSION_ASSIGNMENT.fullmatch(line) for line in lines):
        return "release-metadata"
    if matches_any(file.path, PERSISTENT_SETTINGS_PATTERNS) or re.search(r'\benum\s+\w+\s*:\s*(?:String|U?Int\d*)\b', old):
        before, after = raw_cases(old), raw_cases(new)
        if before and len(before) == len(after) and Counter(before.values()) == Counter(after.values()):
            # Only unique explicit raw values support a logical-name pairing.
            if len(set(before.values())) == len(before):
                names = {name: next(key for key, value in after.items() if value == raw)
                         for name, raw in before.items()}
                # Rename identifiers, never quoted registered/wire values.
                renamed = [names.get(token, token) if re.fullmatch(r"\w+", token) else token for token in tokens(old)]
                if renamed == tokens(new):
                    return "unchanged-contract"
    return ""


def grep_source(repo: Path, ref: str, terms: list[str], *, regex: bool = False) -> list[str]:
    if not terms:
        return []
    args = ["grep", "-n", "-E" if regex else "-F"]
    for term in unique(terms):
        args.extend(["-e", term])
    args.extend([ref, "--", "*.swift", "*.m", "*.mm", "*.kt", "*.java", "*.sql"])
    try:
        return run_git(repo, *args).splitlines()
    except GitCommandError:
        return []


def consumer_candidates(repo: Path, base: str, head: str, terms: list[str]) -> list[str]:
    hits: list[str] = []
    for ref in unique([base, head]):
        for hit in grep_source(repo, ref, terms):
            source = hit.split(":", 3)[-1].strip()
            if re.match(r"(?:case\s|(?:public\s|private\s|static\s)*(?:let|var)\s)", source):
                continue
            hits.append(hit)
    return truncate_list(unique(hits), 6) or ["No consumer candidate found by literal search; indirect consumers remain unverified."]


def build_awareness_items(repo: Path, files: list[FileChange], diffs: dict[str, DiffLines], base: str, head: str) -> list[AwarenessItem]:
    items: list[AwarenessItem] = []
    for file in files:
        diff = diffs.get(file.path, DiffLines([], []))
        old = read_file(repo, file.old_path or file.path, base)
        new = read_file(repo, file.path, head)
        groups: list[tuple[str, str, list[str], list[str], list[str]]] = []
        identity_before, identity_after = config_contract_values(repo, file, diff, base, head)
        if identity_before or identity_after:
            classes = ["migration-required", "legacy-support"]
            if any("PRODUCT_BUNDLE_IDENTIFIER" in line or "CFBundleIdentifier" in line for line in [*changed_source(diff), *identity_before, *identity_after]):
                classes.insert(0, "identity-fixed")
            groups.append(("External identity/configuration", "external-identity-config", identity_before, identity_after, classes))
        capability_before, capability_after = config_contract_values(repo, file, diff, base, head, capability=True)
        if capability_before or capability_after:
            groups.append(("Permission/capability", "security-capability", capability_before, capability_after, ["migration-required"]))
        versions_before = [line.strip() for line in diff.removed if VERSION_ASSIGNMENT.fullmatch(line)]
        versions_after = [line.strip() for line in diff.added if VERSION_ASSIGNMENT.fullmatch(line)]
        if versions_before or versions_after:
            groups.append(("Release version metadata", "release-metadata", versions_before, versions_after, []))
        is_settings = matches_any(file.path, PERSISTENT_SETTINGS_PATTERNS) or "enum AppStorageKey" in old + new
        raw_before = raw_cases(old) if is_settings else {}
        raw_after = raw_cases(new) if is_settings else {}
        touched_names = {match.group(1) for line in changed_source(diff) if (match := EXPLICIT_RAW_CASE.match(line))}
        raw_before = {name: value for name, value in raw_before.items() if name in touched_names}
        raw_after = {name: value for name, value in raw_after.items() if name in touched_names}
        literal_key = re.compile(r'@AppStorage\(\s*("[^"\n]+")|forKey:\s*("[^"\n]+")')
        def defaults_values(lines: list[str]) -> list[str]:
            return unique([next(group for group in match.groups() if group)
                           for line in lines for match in literal_key.finditer(line)])
        defaults_before = [f"{name} = {value}" for name, value in raw_before.items()] or defaults_values(diff.removed)
        defaults_after = [f"{name} = {value}" for name, value in raw_after.items()] or defaults_values(diff.added)
        if defaults_before or defaults_after:
            groups.append(("Defaults raw values and purpose", "persistent-settings", defaults_before, defaults_after, ["legacy-support"]))
        scene_key = re.compile(r'@SceneStorage\(\s*("[^"\n]+")')
        scene_before = unique([match.group(1) for line in diff.removed for match in scene_key.finditer(line)])
        scene_after = unique([match.group(1) for line in diff.added for match in scene_key.finditer(line)])
        if scene_before or scene_after:
            groups.append(("Scene restoration raw values and purpose", "scene-storage", scene_before, scene_after, []))
        if not is_settings and re.search(r'\benum\s+\w+\s*:\s*(?:String|U?Int\d*)\b', old + new):
            before = [line.strip() for line in diff.removed if EXPLICIT_RAW_CASE.match(line)]
            after = [line.strip() for line in diff.added if EXPLICIT_RAW_CASE.match(line)]
            if before or after:
                groups.append(("Explicit enum raw values", "serialized-registered", before, after, ["migration-required", "legacy-support"]))
        if has_durable_model_marker(old + new, diff) or file.path.endswith(".sql"):
            fields_before = [line.strip() for line in diff.removed if MODEL_PROPERTY_PATTERN.match(line.strip()) or file.path.endswith(".sql")]
            fields_after = [line.strip() for line in diff.added if MODEL_PROPERTY_PATTERN.match(line.strip()) or file.path.endswith(".sql")]
            if fields_before or fields_after:
                groups.append(("Stored schema fields/types/defaults", "durable-state", fields_before, fields_after, ["migration-required", "legacy-support"]))
        wire_or_os = re.compile(r'CodingKeys|\bkind\s*[:=]|\b(?:identifier|activityType|restorationIdentifier)\s*[:=]')
        if "CodingKeys" in old + new or any(wire_or_os.search(line) for line in changed_source(diff)):
            before = [line.strip() for line in diff.removed if wire_or_os.search(line) or re.match(r"\s*case\s", line)]
            after = [line.strip() for line in diff.added if wire_or_os.search(line) or re.match(r"\s*case\s", line)]
            if before or after:
                groups.append(("Serialized/OS-registered values", "serialized-registered", before, after, ["migration-required", "legacy-support"]))
        for title, category, before, after, classes in groups:
            search_terms = find_model_properties(changed_source(diff)) if category == "durable-state" else []
            if category == "persistent-settings":
                search_terms = [*raw_before, *raw_after, *[value.strip('"') for value in [*raw_before.values(), *raw_after.values()]]]
            if category == "release-metadata":
                consumers = truncate_list(grep_source(repo, head, [VERSION_READER], regex=True), 6)
                consumers = consumers or ["No literal version reader found; indirect/version-generated readers remain unverified."]
            else:
                consumers = consumer_candidates(repo, base, head, search_terms or [*before, *after])
            items.append(AwarenessItem(
                title=title, category=category, files=[file.path],
                contract_values=[*truncate_list([f"old: {value}" for value in before], 12),
                                 *truncate_list([f"new: {value}" for value in after], 12)],
                introduction_status="present in base source; public/prototype/development status unverified" if before else "added in candidate source; shipping status unverified",
                consumers=consumers, contract_classes=classes,
                migration_burden="Assess purpose, recoverability, migration and user guidance; no automatic score for a necessary contract." if category != "release-metadata" else "Ordinary metadata has no compatibility surcharge; inspect behavioral version readers.",
                future_responsibility="Trace ownership, writers/readers and retention; identify retained/replaced/retired metadata and aliases. Disposable preferences/cache may need no legacy support." if category != "release-metadata" else "No fixed-contract obligation inferred from the version number alone.",
                evidence=truncate_list(changed_source(diff), 8),
            ))
    return items


def detect_external_identity_config_findings(repo: Path, files: list[FileChange], diffs: dict[str, DiffLines], base: str, head: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for file in files:
        if not (file.path.endswith((".entitlements", "Info.plist", "project.pbxproj", ".xcconfig", ".storekit", "project.yml", "project.yaml")) or "/StoreKit/" in file.path):
            continue
        diff = diffs.get(file.path, DiffLines([], []))
        before, after = config_contract_values(repo, file, diff, base, head)
        if not before and not after:
            continue
        score = 55 if before != after and before else 0
        lines = [line for line in changed_source(diff) if collect_markers([line], IDENTIFIER_MARKER_PATTERNS)]
        findings.append(ReviewFinding(
            title="既存の外部ID・設定値変更候補" if score else "外部契約の追加または同値維持",
            severity="high" if score else "none", category="external-identity-config", score=score,
            reason="既存値の変更は同じ公開製品のidentityや連携互換性へ影響する候補。新規値や同値だけでは危険を断定しない。",
            advice="公開状態、対象target、登録値、旧alias、移行と利用者案内の責任を確認する。",
            files=[file.path], evidence=[f"old: {value}" for value in before] + [f"new: {value}" for value in after],
            risk_id=f"external-config:{file.path}", covered_lines=lines,
        ))
    return findings


def detect_capability_findings(repo: Path, files: list[FileChange], diffs: dict[str, DiffLines], base: str, head: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for file in files:
        diff = diffs.get(file.path, DiffLines([], []))
        # Shared identity markers (such as App Groups) represent one cause.
        before = [line for line in diff.removed if not collect_markers([line], IDENTIFIER_MARKER_PATTERNS)]
        after = [line for line in diff.added if not collect_markers([line], IDENTIFIER_MARKER_PATTERNS)]
        old = collect_markers(before, CAPABILITY_MARKER_PATTERNS)
        new = collect_markers(after, CAPABILITY_MARKER_PATTERNS)
        if file.path.endswith((".plist", ".entitlements")):
            old, new = config_contract_values(repo, file, diff, base, head, capability=True)
        if old == new or not (old or new):
            continue
        findings.append(ReviewFinding(
            title="権限・Capability 変更候補", severity="medium", category="security-capability", score=35,
            reason="新しい権限要求や既存機能への作用を確認する候補で、不要権限や実害の確定ではない。",
            advice="差分の用途、公開状態、対象利用者、既存導線を確認する。",
            files=[file.path], evidence=old + new, risk_id=f"capability:{file.path}",
            covered_lines=[line for line in [*before, *after] if collect_markers([line], CAPABILITY_MARKER_PATTERNS)],
        ))
    return findings


def detect_durable_state_findings(repo: Path, files: list[FileChange], diffs: dict[str, DiffLines], base: str, head: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for file in files:
        diff = diffs.get(file.path, DiffLines([], []))
        old = read_file(repo, file.old_path or file.path, base)
        new = read_file(repo, file.path, head)
        if has_durable_model_marker(old + new, diff):
            removed = [line for line in diff.removed if MODEL_PROPERTY_PATTERN.match(line.strip())]
            added = [line for line in diff.added if MODEL_PROPERTY_PATTERN.match(line.strip())]
            if removed or added:
                # Added optional/defaulted properties are awareness, not automatic harm.
                uninitialized = [line for line in added if "=" not in line and "?" not in line]
                score = 45 if removed else 35 if uninitialized else 0
                findings.append(ReviewFinding(
                    title="保存プロパティの互換性確認候補", severity="high" if score >= 40 else "medium" if score else "none",
                    category="durable-state", score=score,
                    reason="旧fieldの削除/変更や非optional・既定値なしの追加は読込互換性の候補。必要な新field自体には加点しない。",
                    advice="raw schema、type/default、consumer、旧reader、不要/予約fieldの必要性を確認する。",
                    files=[file.path], evidence=[line.strip() for line in [*removed, *added]],
                    risk_id=f"model-compatibility:{file.path}", covered_lines=[*removed, *added],
                ))
        if matches_any(file.path, DURABLE_STORAGE_INFRA_PATTERNS):
            lines = [line for line in changed_source(diff) if re.search(r'ModelContainer|Migration|legacyURL|fileName|\burl\b|Schema', line)]
            if lines:
                findings.append(ReviewFinding(
                    title="保存先・移行経路変更候補", severity="medium", category="durable-state", score=35,
                    reason="保存先や移行経路の差分候補。ファイル名だけで起動不能やデータ消失とは断定しない。",
                    advice="旧storeと必要sidecar、guards、旧reader、失敗後の書込みと復元経路を確認する。",
                    files=[file.path], evidence=[line.strip() for line in lines], risk_id=f"storage-route:{file.path}", covered_lines=lines,
                ))
    return findings


def detect_persistent_settings_findings(repo: Path, files: list[FileChange], diffs: dict[str, DiffLines], base: str, head: str) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for file in files:
        diff = diffs.get(file.path, DiffLines([], []))
        old = read_file(repo, file.old_path or file.path, base)
        new = read_file(repo, file.path, head)
        settings = matches_any(file.path, PERSISTENT_SETTINGS_PATTERNS) or "enum AppStorageKey" in old + new
        before, after = raw_cases(old) if settings else {}, raw_cases(new) if settings else {}
        usage = [line for line in changed_source(diff) if any(pattern.search(line) for pattern in PERSISTENT_USAGE_PATTERNS)]
        if not settings and not usage:
            continue
        removed_raw = set(before.values()) - set(after.values())
        removed_usage = [line for line in diff.removed if any(pattern.search(line) for pattern in PERSISTENT_USAGE_PATTERNS)]
        score = 15 if removed_raw or removed_usage else 0
        lines = [line for line in changed_source(diff) if EXPLICIT_RAW_CASE.match(line) or line in usage]
        findings.append(ReviewFinding(
            title="Defaultsのraw値・用途確認", severity="low" if score else "none", category="persistent-settings", score=score,
            reason="既存raw値/読出し前提の変更候補。UI選好や派生cacheの許容されるresetと一次データを区別する。",
            advice="consumer、保存用途、type/default、旧keyを残す責任を確認する。random rawやlogical名だけを改名理由にしない。",
            files=[file.path], evidence=[f"old: {name} = {value}" for name, value in before.items()] + [f"new: {name} = {value}" for name, value in after.items()] or [line.strip() for line in usage],
            risk_id=f"defaults:{file.path}", covered_lines=lines,
        ))
    return findings


def detect_operation_findings(files: list[FileChange], diffs: dict[str, DiffLines]) -> list[ReviewFinding]:
    findings: list[ReviewFinding] = []
    for file in files:
        if matches_any(file.path, DEFAULT_IGNORE_USAGE_PATTERNS):
            continue
        diff = diffs.get(file.path, DiffLines([], []))
        destructive = [line for line in diff.added if DESTRUCTIVE_OPERATION.search(line)]
        crash = [line for line in diff.added if CRASH_OPERATION.search(line)]
        if destructive:
            state_named = any(re.search(r'sqlite|store|database|backup|\bwal\b|DROP\s+TABLE|DELETE\s+FROM', line, re.I) for line in destructive)
            findings.append(ReviewFinding(
                title="削除・破壊的書込み候補", severity="high", category="primary-data", score=60 if state_named else 45,
                reason="削除候補を先に確認する。guard、保存用途、発火条件と全復元元の有無は未確認で、完全消失の証明ではない。",
                advice="一次データかcacheか、原storeと必要sidecar/backup、失敗後pending変更と後続saveを追跡する。",
                files=[file.path], evidence=[line.strip() for line in destructive], risk_id=f"destructive-state:{file.path}", covered_lines=destructive,
            ))
        if crash:
            findings.append(ReviewFinding(
                title="起動・操作不能候補", severity="high", category="operational", score=40,
                reason="crash候補。保存済みdata消失とは別で、元storeが復元可能か、人数・頻度・復旧資源を確認する。",
                advice="発火条件と利用者範囲、原store/sidecar保持、復旧手段を確認する。",
                files=[file.path], evidence=[line.strip() for line in crash], risk_id=f"crash:{file.path}", covered_lines=crash,
            ))
        minimum_os = [line for line in changed_source(diff) if re.search(r'\b(?:IPHONEOS|MACOSX|WATCHOS|TVOS)_DEPLOYMENT_TARGET\s*=', line)]
        if minimum_os:
            findings.append(ReviewFinding(
                title="最小OS変更候補", severity="medium", category="packaging", score=35,
                reason="対象端末/OSの変更は通常version更新と別の互換面。data消失を意味しない。",
                advice="旧利用者の更新可否と配布対象を確認する。",
                files=[file.path], evidence=[line.strip() for line in minimum_os], risk_id=f"minimum-os:{file.path}", covered_lines=minimum_os,
            ))
    return findings


def version_effect_findings(repo: Path, head: str, files: list[FileChange], diffs: dict[str, DiffLines]) -> list[ReviewFinding]:
    version_files = [file.path for file in files if any(VERSION_ASSIGNMENT.fullmatch(line) for line in changed_source(diffs.get(file.path, DiffLines([], []))))]
    if not version_files:
        return []
    hits = grep_source(repo, head, [VERSION_READER], regex=True)
    behavioral: list[str] = []
    paths: list[str] = []
    for hit in hits:
        parts = hit.split(":", 3)
        if len(parts) != 4:
            continue
        path = parts[1]
        content = read_file(repo, path, head)
        if re.search(r'migrat|feature.?gate|schema|removeItem|deleteAll', path + content, re.I):
            behavioral.append(hit)
            paths.append(path)
    if not behavioral:
        return []
    return [ReviewFinding(
        title="version値の挙動consumer候補", severity="high", category="version-behavior", score=40,
        reason="版番号自体は0点。既存readerにmigration/gate等の文脈があり、版番号で変わる作用を確認する候補。",
        advice="表示/ログだけか、今回の値で移行・feature gate・保存形式が変わるかを追跡する。",
        files=unique(paths + version_files), evidence=truncate_list(behavioral, 6), risk_id="version-behavior",
    )]


def build_review_findings(repo: Path, files: list[FileChange], diff_by_file: dict[str, DiffLines], base_ref: str = "HEAD", head_ref: str = "HEAD") -> list[ReviewFinding]:
    findings = [
        *detect_external_identity_config_findings(repo, files, diff_by_file, base_ref, head_ref),
        *detect_capability_findings(repo, files, diff_by_file, base_ref, head_ref),
        *detect_durable_state_findings(repo, files, diff_by_file, base_ref, head_ref),
        *detect_persistent_settings_findings(repo, files, diff_by_file, base_ref, head_ref),
        *detect_operation_findings(files, diff_by_file),
    ]
    for file in files:
        lines = [line for line in changed_source(diff_by_file.get(file.path, DiffLines([], []))) if VERSION_ASSIGNMENT.fullmatch(line)]
        if file.path.endswith((".pbxproj", ".xcconfig")) and lines:
            findings.append(ReviewFinding(
                title="通常のrelease metadata", severity="none", category="release-metadata", score=0,
                reason="通常の版番号代入には契約加点しない。同じファイルの別変更は免除しない。",
                advice="versionの実作用は別consumer候補として確認する。", files=[file.path],
                evidence=[line.strip() for line in lines], risk_id=f"release-metadata:{file.path}", covered_lines=lines,
            ))
    return sorted(findings, key=lambda finding: (-finding.score, -SEVERITY_ORDER[finding.severity], finding.title))


def score_items(
    files: list[FileChange],
    findings: list[ReviewFinding],
    signals: list[RiskSignal],
    diff_by_file: dict[str, DiffLines] | None = None,
) -> list[dict[str, int | str]]:
    items: list[dict[str, int | str]] = []
    strongest_by_cause: dict[str, ReviewFinding] = {}
    for index, finding in enumerate(findings):
        cause = finding.risk_id or f"finding:{index}"
        previous = strongest_by_cause.get(cause)
        if previous is None or finding.score > previous.score:
            strongest_by_cause[cause] = finding
    explained: dict[str, Counter[str]] = {}
    for finding in strongest_by_cause.values():
        for path in finding.files:
            explained.setdefault(path, Counter()).update(line.strip() for line in finding.covered_lines if line.strip())
    covered_finding_paths = set()
    if diff_by_file is not None:
        for path, covered in explained.items():
            remaining = Counter(line.strip() for line in changed_source(diff_by_file.get(path, DiffLines([], [])))) - covered
            if not remaining:
                covered_finding_paths.add(path)
    for finding in strongest_by_cause.values():
        items.append(
            {
                "source": "finding",
                "name": finding.title,
                "severity": finding.severity,
                "category": finding.category,
                "score": finding.score,
            }
        )
    for signal in signals:
        if signal.matched_files and set(signal.matched_files).issubset(covered_finding_paths):
            continue
        items.append(
            {
                "source": "path-rule",
                "name": signal.name,
                "severity": signal.severity,
                "category": signal.category,
                "score": signal.score,
            }
        )

    unclassified = files and not items
    if diff_by_file is not None:
        located = {path for signal in signals for path in signal.matched_files}
        unclassified = unclassified or any(file.path not in covered_finding_paths and file.path not in located for file in files)
    if unclassified:
        items.append(
            {
                "source": "fallback",
                "name": "未分類の出荷差分",
                "severity": "medium",
                "category": "unknown-change",
                "score": FALLBACK_UNKNOWN_CHANGE_SCORE,
            }
        )

    strongest_by_category: dict[str, dict[str, int | str]] = {}
    for item in items:
        category = str(item["category"])
        existing = strongest_by_category.get(category)
        if existing is None:
            strongest_by_category[category] = item
            continue

        item_score = int(item["score"])
        existing_score = int(existing["score"])
        if item_score > existing_score:
            strongest_by_category[category] = item
            continue

        if (
            item_score == existing_score
            and SEVERITY_ORDER[str(item["severity"])] > SEVERITY_ORDER[str(existing["severity"])]
        ):
            strongest_by_category[category] = item

    return sorted(
        strongest_by_category.values(),
        key=lambda item: (-int(item["score"]), str(item["name"])),
    )


def truncate_diff_lines(lines: list[str], limit: int) -> list[str]:
    if len(lines) <= limit:
        return lines
    remaining = len(lines) - limit
    return [*lines[:limit], f"... (+{remaining} 行)"]


def build_snippets_for_files(
    title: str,
    category: str,
    source: str,
    files: list[str],
    diff_by_file: dict[str, DiffLines],
    *,
    max_files: int = 3,
    max_lines: int = 14,
) -> list[DiffSnippet]:
    snippets: list[DiffSnippet] = []
    for path in unique(files)[:max_files]:
        diff = diff_by_file.get(path)
        if not diff or not diff.changed:
            continue
        snippets.append(
            DiffSnippet(
                title=title,
                category=category,
                source=source,
                file=path,
                lines=truncate_diff_lines(diff.changed, max_lines),
            )
        )
    return snippets


def build_risk_diff_snippets(
    findings: list[ReviewFinding],
    signals: list[RiskSignal],
    diff_by_file: dict[str, DiffLines],
    *,
    max_snippets: int = 8,
) -> list[DiffSnippet]:
    snippets: list[DiffSnippet] = []
    covered_finding_paths = {path for finding in findings for path in finding.files}

    for finding in findings:
        if finding.score < 20:
            continue
        snippets.extend(
            build_snippets_for_files(
                finding.title,
                finding.category,
                "finding",
                finding.files,
                diff_by_file,
            )
        )

    for signal in signals:
        if signal.score < 20:
            continue
        if signal.matched_files and set(signal.matched_files).issubset(covered_finding_paths):
            continue
        snippets.extend(
            build_snippets_for_files(
                signal.name,
                signal.category,
                "path-rule",
                signal.matched_files,
                diff_by_file,
            )
        )

    return snippets[:max_snippets]


def total_score(items: list[dict[str, int | str]]) -> int:
    scores = sorted((int(item["score"]) for item in items), reverse=True)
    if not scores:
        return 0

    score = scores[0]
    for secondary_score in scores[1:]:
        if secondary_score >= 60:
            score += 5
        elif secondary_score >= 40:
            score += 3
        elif secondary_score >= 25:
            score += 1

    return min(HEURISTIC_SCORE_MAX, score)


def risk_from_score(score: int) -> str:
    if score <= 0:
        return "none"
    if score < 20:
        return "low"
    if score < 40:
        return "medium"
    if score < 80:
        return "high"
    return "critical"


def release_decision(score: int) -> str:
    if score >= 80:
        return "Block"
    if score >= 60:
        return "Hold for review"
    if score >= 40:
        return "Proceed with caution"
    if score >= 20:
        return "Review recommended"
    return "Proceed"


def release_posture(score: int, files: list[FileChange], findings: list[ReviewFinding]) -> str:
    if not files:
        return "未リリース差分は見つかっていません。"
    if score >= 90:
        return "優先確認すべき重大な候補があります。実害・発火条件・復元元を確認して出荷判断へ反映してください。"
    if score >= 80:
        return "重大候補の確認を優先する判定です。静的検出だけでは実害や全復元元消失の確定ではありません。"
    if score >= 60:
        return "リリース前に手動レビューで可否を判断するべき変更候補があります。"
    if score >= 40:
        return "明確なリスク候補があります。変更意図と重点検証を揃えてから出す方が安全です。"
    if score >= 20:
        return "軽い手動レビューで変更意図を確認してから進めるのが無難です。"
    return "限定的な確認で進めやすい状態です。"


def confidence(findings: list[ReviewFinding], signals: list[RiskSignal]) -> str:
    if any(finding.score > 0 for finding in findings):
        return "中（source候補あり・実害は未検証）"
    return "低（静的差分のみ・安全性は未証明）"


def sort_signals(signals: list[RiskSignal]) -> list[RiskSignal]:
    return sorted(
        signals,
        key=lambda signal: (
            -signal.score,
            -SEVERITY_ORDER[signal.severity],
            signal.name.lower(),
        ),
    )


def format_severity(severity: str) -> str:
    return SEVERITY_LABELS.get(severity, severity)


def render_findings(title: str, findings: list[ReviewFinding]) -> list[str]:
    lines = [f"## {title}"]
    if not findings:
        lines.append("- 該当なし")
        return lines

    for finding in findings:
        lines.append(f"- `[{format_severity(finding.severity)} / {finding.score}点]` {finding.title}")
        lines.append(f"  理由: {finding.reason}")
        lines.append(f"  対象: {', '.join(truncate_list(finding.files, 4))}")
        if finding.evidence:
            lines.append(f"  手がかり: {', '.join(truncate_list(finding.evidence, 4))}")
        lines.append(f"  確認: {finding.advice}")
        lines.append(f"  検証状態: {finding.verification_status}")
    return lines


def render_signals(title: str, signals: list[RiskSignal]) -> list[str]:
    lines = [f"## {title}"]
    if not signals:
        lines.append("- 該当なし")
        return lines

    for signal in signals:
        lines.append(f"- `[{format_severity(signal.severity)} / {signal.score}点]` {signal.name}")
        lines.append(f"  理由: {signal.reason or '理由なし'}")
        lines.append(f"  対象: {', '.join(truncate_list(signal.matched_files, 4))}")
        lines.append(f"  確認: {signal.advice or '確認手順なし'}")
    return lines


def render_score_breakdown(items: list[dict[str, int | str]]) -> list[str]:
    lines = ["## スコア内訳"]
    if not items:
        lines.append("- `0/100` 未リリース差分なし")
        return lines

    for item in items[:8]:
        lines.append(
            f"- `{item['score']}点` {item['name']} ({format_severity(str(item['severity']))}, {item['source']}, {item['category']})"
        )
    if len(items) > 8:
        lines.append(f"- ... (+{len(items) - 8} 件)")
    lines.append("- 点数は単純合計ではありません。最も高いリスク軸を基準に、独立した追加リスクだけを小さく補正します。")
    lines.append("- `100点` は大きな実害がほぼ避けられないと判断できる場合の上限で、通常のヒューリスティック検出は `95点` を上限にします。")
    return lines


def render_diff_snippets(snippets: list[dict]) -> list[str]:
    lines = ["## リスク差分抜粋"]
    if not snippets:
        lines.append("- 該当なし")
        return lines

    for snippet in snippets:
        lines.append(
            f"- {snippet['title']} (`{snippet['category']}`, {snippet['source']}) / `{snippet['file']}`"
        )
        lines.append("```diff")
        lines.extend(snippet["lines"])
        lines.append("```")
    lines.append("- 抜粋はリスク確認用に短く丸めています。全差分が必要なら `--verbose` と `git diff` を併用してください。")
    return lines


def render_awareness(items: list[dict]) -> list[str]:
    lines = ["## 認識・確認事項（この一覧自体は加点しません）"]
    if not items:
        return [*lines, "- 組み込み検出で該当なし。公開契約がないことの証明ではありません。"]
    for item in items:
        lines.append(f"- {item['title']} / `{', '.join(item['files'])}`")
        lines.append(f"  契約値: {'; '.join(item['contract_values'])}")
        lines.append(f"  導入状態: {item['introduction_status']}")
        lines.append(f"  consumer候補: {'; '.join(item['consumers'])}")
        lines.append(f"  契約分類候補: {', '.join(item['contract_classes']) or '固定契約を推定しない。用途・保存期間を要確認'} / {item['classification_status']}")
        lines.append(f"  移行負担: {item['migration_burden']}")
        lines.append(f"  将来責任: {item['future_responsibility']}")
        lines.append(f"  根拠: {'; '.join(item['evidence'])}")
        lines.append(f"  技術確認: {item['verification_status']}")
        lines.append(f"  本人認識: {item['acknowledgment_status']}")
    return lines


def render_compact_markdown(report: dict) -> str:
    lines = [
        "# リリースリスク検出候補",
        "",
        f"比較: `{report['range']}` / 候補 `{report['head_commit']}`"
        f"（{report['commit_count']}コミット、{report['file_count']}ファイル）",
        f"検出スコア: `{report['risk_score']}/{report['risk_score_max']}`"
        f" / `{report['release_decision']}`",
        "",
        "これは調査の入口です。新しい契約の妥当性、旧契約の維持、実害は文脈確認が必要です。",
        "",
        "## 重大所見候補",
        "",
    ]
    groups: dict[tuple[str, str], list[dict]] = {}
    for finding in report["review_findings"]:
        if finding["score"] >= 40:
            groups.setdefault((finding["category"], finding["title"]), []).append(finding)
    ordered = sorted(groups.values(), key=lambda group: (
        group[0]["category"] != "primary-data", -max(item["score"] for item in group)))
    for group in ordered:
        strongest = max(group, key=lambda item: item["score"])
        lines.append(f"- {strongest['title']}（最大{strongest['score']}点、{len(group)}候補）: {strongest['reason']}")
    if not groups:
        lines.append("- 組み込み検出で該当なし。安全性の証明ではありません。")

    lines.extend(["", "## 契約の確認候補", ""])
    labels = {
        "external-identity-config": "外部ID・登録設定",
        "security-capability": "権限・Capability",
        "durable-state": "保存スキーマ",
        "persistent-settings": "UserDefaults等の設定",
        "scene-storage": "画面の復元状態",
        "serialized-registered": "シリアライズ・OS登録値",
    }
    counts = Counter(item["category"] for item in report["awareness_items"]
                     if item["category"] != "release-metadata")
    for category, count in sorted(counts.items()):
        lines.append(f"- {labels.get(category, category)}: {count}候補")
    if not counts:
        lines.append("- 組み込み検出で該当なし。契約の追加・破棄がないことの証明ではありません。")
    minor_count = sum(0 < item["score"] < 40 for item in report["review_findings"])
    signal_count = sum(item["score"] > 0 for item in report["risk_signals"])
    lines.extend([
        "",
        f"その他: 所見候補{minor_count}件、変更面からのシグナル{signal_count}件。",
        "候補は種類ごとにまとめています。個別の値・対象ファイル・根拠は"
        " `--format json` または `--verbose` で確認してください。",
        "公開状態、実際の読み書き、保存期間、互換処理、復元元を確認してから結論にしてください。",
    ])
    return "\n".join(lines)


def render_markdown(report: dict, max_files: int, max_commits: int, verbose: bool) -> str:
    if not verbose:
        return render_compact_markdown(report)
    blocker_findings = [
        ReviewFinding(**finding)
        for finding in report["review_findings"]
        if finding["score"] >= 40
    ]
    minor_findings = [
        ReviewFinding(**finding)
        for finding in report["review_findings"]
        if 0 < finding["score"] < 40
    ]
    signals = [RiskSignal(**signal) for signal in report["risk_signals"]]

    lines: list[str] = []
    lines.append("# リリースリスク診断")
    lines.append("")
    lines.append("## 判定")
    lines.append(f"- リスクスコア: `{report['risk_score']}/{report['risk_score_max']}`")
    lines.append(f"- ヒューリスティック上限: `{report['heuristic_score_max']}`")
    lines.append(f"- 総合リスク: `{format_severity(report['overall_risk'])}`")
    lines.append(f"- リリース判定: `{report['release_decision']}`")
    lines.append(f"- リリース方針: {report['release_posture']}")
    lines.append(
        "- 判定しきい値: `80-100=Block`, `60-79=Hold for review`, "
        "`40-59=Proceed with caution`, `20-39=Review recommended`, `0-19=Proceed`"
    )
    lines.append(f"- 信頼度: `{report['confidence']}`")
    lines.append(f"- 比較範囲: `{report['range']}`")
    lines.append(f"- 基準タグ: `{report['base_ref']}`")
    lines.append(f"- 先頭コミット: `{report['head_commit']}`")
    lines.append(f"- コミット数: `{report['commit_count']}`")
    lines.append(f"- 変更ファイル数: `{report['file_count']}`")
    lines.append("- ルールソース: `built-in`")
    if report["top_areas"]:
        areas = ", ".join(
            f"`{entry['area']}` ({entry['count']})" for entry in report["top_areas"]
        )
        lines.append(f"- 主な変更領域: {areas}")
    lines.append("")

    lines.extend(render_score_breakdown(report["score_breakdown"]))
    lines.append("")
    blocker_findings.sort(key=lambda finding: (finding.category != "primary-data", -finding.score))
    lines.extend(render_findings("重大所見候補（実害・復元元は要確認）", blocker_findings))
    lines.append("")
    lines.extend(render_diff_snippets(report["risk_diff_snippets"]))
    lines.append("")
    lines.extend(render_findings("追加で確認したい項目", minor_findings))
    lines.append("")
    lines.extend(render_signals("変更面から見たリスクシグナル", signals))
    lines.append("")
    lines.extend(render_awareness(report["awareness_items"]))
    lines.append("")
    lines.append("## 未確認")
    lines.extend(f"- {item}" for item in report["unverified_items"])

    lines.append("")
    lines.append("## 変更ファイル")
    if report["files"]:
        for file in report["files"][:max_files]:
            old_path = f" <- `{file['old_path']}`" if file["old_path"] else ""
            lines.append(f"- `{file['status']}` `{file['path']}`{old_path}")
        remaining_files = report["file_count"] - min(report["file_count"], max_files)
        if remaining_files > 0:
            lines.append(f"- ... (+{remaining_files} 件)")
    else:
        lines.append("- 該当なし")

    lines.append("")
    lines.append("## コミット")
    if report["commits"]:
        for commit in report["commits"][:max_commits]:
            lines.append(
                f"- `{commit['date']}` `{commit['short_hash']}` {commit['subject']} ({commit['author']})"
            )
        remaining_commits = report["commit_count"] - min(report["commit_count"], max_commits)
        if remaining_commits > 0:
            lines.append(f"- ... (+{remaining_commits} 件)")
    else:
        lines.append("- 該当なし")

    return "\n".join(lines)


def build_report(args: argparse.Namespace) -> dict:
    repo = Path(args.repo).resolve()
    if not repo.exists():
        raise FileNotFoundError(f"Repository not found: {repo}")

    base_ref = args.base_ref or detect_base_ref(repo, args.head_ref, args.tag_pattern)
    head_ref = args.head_ref
    commits = get_commits(repo, base_ref, head_ref)
    files = get_files(repo, base_ref, head_ref)
    diff_by_file = get_diff_lines(repo, base_ref, head_ref, files)

    rules = load_rules_from_dicts(BUILTIN_RULES)

    review_files: list[FileChange] = []
    signals: list[RiskSignal] = []
    for file in files:
        reason = nonrisk_reason(repo, file, diff_by_file[file.path], base_ref, head_ref)
        if reason:
            signals.append(RiskSignal(
                name="通常metadataまたは契約同値の差分", severity="none", category=reason,
                score=0, mode="any", reason=reason,
                advice="契約加点は0。versionの挙動consumerと同梱された別変更は独立して確認する。",
                matched_files=[file.path],
            ))
        else:
            review_files.append(file)
    signals.extend(signal for rule in rules if (signal := evaluate_rule(rule, review_files)))
    signals = sort_signals(signals)

    findings = build_review_findings(repo, review_files, diff_by_file, base_ref, head_ref)
    findings.extend(version_effect_findings(repo, head_ref, files, diff_by_file))
    findings.sort(key=lambda finding: -finding.score)
    awareness = build_awareness_items(repo, files, diff_by_file, base_ref, head_ref)

    score_breakdown = score_items(files, findings, signals, diff_by_file)
    risk_diff_snippets = build_risk_diff_snippets(findings, signals, diff_by_file)
    risk_score = total_score(score_breakdown)
    risk = risk_from_score(risk_score)
    return {
        "repo": str(repo),
        "range": f"{base_ref}..{head_ref}",
        "base_ref": base_ref,
        "head_ref": head_ref,
        "head_commit": short_ref(repo, head_ref),
        "commit_count": len(commits),
        "file_count": len(files),
        "risk_score": risk_score,
        "risk_score_max": SCORE_MAX,
        "heuristic_score_max": HEURISTIC_SCORE_MAX,
        "overall_risk": risk,
        "release_decision": release_decision(risk_score),
        "confidence": confidence(findings, signals),
        "release_posture": release_posture(risk_score, files, findings),
        "top_areas": top_areas(files),
        "score_breakdown": score_breakdown,
        "risk_diff_snippets": [asdict(snippet) for snippet in risk_diff_snippets],
        "review_findings": [asdict(finding) for finding in findings],
        "awareness_items": [asdict(item) for item in awareness],
        "unverified_items": [
            "Public shipping status and distributed-build/source-to-tag correspondence are not established by Git.",
            "Candidate semantics, guards, affected users/frequency, and runtime behavior require contextual review.",
            "Primary-data scope and viability of original stores, required sidecars, backups and other restoration copies are unverified.",
            "Indirect consumers, migration/user-guidance burden, old metadata/readers/aliases and retirement conditions remain to be checked.",
            "Personal acknowledgment requires explicit evidence; ADR status and authorship alone do not establish it. Awareness items are not mandatory-response gates.",
        ],
        "risk_signals": [asdict(signal) for signal in signals],
        "files": [asdict(file) for file in files],
        "commits": [asdict(commit) for commit in commits],
    }


def main() -> int:
    args = parse_args()
    try:
        report = build_report(args)
    except (FileNotFoundError, GitCommandError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(render_markdown(report, args.max_files, args.max_commits, args.verbose))
    return 0


if __name__ == "__main__":
    sys.exit(main())
