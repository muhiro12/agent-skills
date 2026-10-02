#!/usr/bin/env bash
set -euo pipefail

list_run_ids() {
  local run_base="$1"
  local path=""
  local run_id=""

  if [ ! -d "$run_base" ] || [ -L "$run_base" ]; then
    return 0
  fi

  {
    for path in "$run_base"/*; do
      [ -d "$path" ] || continue
      [ ! -L "$path" ] || continue
      run_id="$(basename "$path")"
      case "$run_id" in
        *[!A-Za-z0-9._-]*) continue ;;
      esac
      printf '%s\n' "$run_id"
    done
  } | sort
}

has_unsafe_run_entry() {
  local run_base="$1"
  local path=""

  [ -d "$run_base" ] || return 1
  for path in "$run_base"/*; do
    if [ -L "$path" ]; then
      return 0
    fi
  done
  return 1
}

extract_agents_entrypoint() {
  local agents_path="$1"
  python3 - "$agents_path" <<'PY'
import re
import sys
from pathlib import Path

agents_path = Path(sys.argv[1])
if not agents_path.is_file():
    raise SystemExit(0)

text = agents_path.read_text(encoding="utf-8")
commands = re.findall(r"\bbash[ \t]+([A-Za-z0-9_./-]+\.sh)(?=[`\s]|$)", text)
for command in commands:
    path = Path(command)
    if path.is_absolute() or ".." in path.parts:
        continue
    if not (re.fullmatch(r"(?:verify|check)(?:[_-][A-Za-z0-9_-]+)?\.sh", path.name)
            or path.name == "run_required_builds.sh"):
        continue
    print(command)
    break
PY
}

detect_verify_entrypoint() {
  local agents_entrypoint=""
  local rel_path=""

  agents_entrypoint="$(extract_agents_entrypoint "AGENTS.md")"
  if [ -n "$agents_entrypoint" ]; then
    printf '%s\n' "$agents_entrypoint"
    return 0
  fi

  for rel_path in \
    "ci_scripts/tasks/verify_task_completion.sh" \
    "ci_scripts/tasks/check_repository_rules.sh" \
    "ci_scripts/tasks/verify.sh" \
    "ci_scripts/verify.sh" \
    "ci_scripts/tasks/verify_repository_state.sh" \
    "ci_scripts/tasks/run_required_builds.sh" \
    "ci_scripts/run_required_builds.sh"
  do
    if [ -f "$rel_path" ]; then
      printf '%s\n' "$rel_path"
      return 0
    fi
  done

}

verify_output="$(mktemp "${TMPDIR:-/tmp}/ci_verify_and_summarize.XXXXXX")"

cleanup_verify_output() {
  rm -f -- "$verify_output"
}

trap cleanup_verify_output EXIT

diff_only=false
case "${1:-}" in
  "") ;;
  --diff-only) diff_only=true; shift ;;
  *) echo "Usage: bash run_verify_and_summarize.sh [--diff-only]" >&2; exit 2 ;;
esac
if [ "$#" -ne 0 ]; then
  echo "Usage: bash run_verify_and_summarize.sh [--diff-only]" >&2
  exit 2
fi
repository_root=$(git rev-parse --show-toplevel) || exit 1
cd "$repository_root"

run_base=".build/ci/runs"
verify_entrypoint=""
if [ "$diff_only" = false ]; then
  verify_entrypoint="$(detect_verify_entrypoint)"
fi
verification_ran=false
verify_command="(未実行)"
verify_exit=0
latest_run=""
run_dir=""
run_is_new=false
run_selection_error=""
if [ -n "$verify_entrypoint" ]; then
  verification_ran=true
for run_component in ".build" ".build/ci" "$run_base"; do
if [ -L "$run_component" ]; then
  echo "結果: ❌ failure"
  echo "最新RUN: (なし)"
  echo "要約:"
  echo "- $run_component がsymlinkのため、安全にCI成果物を選択できません。"
  echo "証拠の問題:"
  echo "- CI成果物rootがrepository外を指し得るため、verifyを実行していません。"
  echo "次の一手:"
  echo "- .build/ci/runs を通常directoryへ戻してから再実行してください。"
  exit 1
fi
done

pre_runs="$(list_run_ids "$run_base")"

verify_command="bash $verify_entrypoint"

set +e
python3 - "$verify_entrypoint" >"$verify_output" 2>&1 <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
if (path.is_absolute() or ".." in path.parts or not path.is_file()
        or any(part.is_symlink() for part in (path, *path.parents))):
    print(f"Verification script is missing or is not a regular repository file: {path}")
    raise SystemExit(1)
try:
    path.resolve().relative_to(Path.cwd().resolve())
except ValueError:
    print(f"Verification script escapes the repository: {path}")
    raise SystemExit(1)
PY
verify_exit=$?
if [ "$verify_exit" -eq 0 ]; then
  bash "$verify_entrypoint" >>"$verify_output" 2>&1
  verify_exit=$?
fi
set -e

post_runs="$(list_run_ids "$run_base")"
latest_run=""
run_is_new="false"
run_selection_error=""
new_runs="$(comm -13 <(printf '%s\n' "$pre_runs") <(printf '%s\n' "$post_runs"))"
new_run_count=0
while IFS= read -r run_id; do
  [ -n "$run_id" ] || continue
  latest_run="$run_id"
  new_run_count=$((new_run_count + 1))
done < <(printf '%s\n' "$new_runs")

if has_unsafe_run_entry "$run_base"; then
  latest_run=""
  run_selection_error="CI成果物rootにsymlink entryがあるため、新しいRUNを安全に選択できません。"
elif [ "$new_run_count" -eq 1 ]; then
  run_is_new="true"
elif [ "$new_run_count" -gt 1 ]; then
  latest_run=""
  run_selection_error="verify中に複数の新しいRUNが作られ、現在実行の成果物を一意に選択できません。"
fi

run_dir=""
if [ -n "$latest_run" ]; then
  run_dir="$run_base/$latest_run"
fi

fi

set +e
python3 - "$latest_run" "$run_dir" "$verify_exit" "$verify_command" "$verify_output" "$run_is_new" "$run_base" "$run_selection_error" "$verification_ran" <<'PY'
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def read_text(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def resolve_run_directory(raw_path: str, raw_run_base: str) -> tuple[Path | None, str]:
    if not raw_path:
        return None, ""

    run_base = Path(raw_run_base)
    candidate = Path(raw_path)
    if run_base.is_symlink() or candidate.is_symlink() or not candidate.is_dir():
        return None, "選択したCI RUNが通常directoryではありません。"

    resolved_run_base = run_base.resolve()
    resolved_candidate = candidate.resolve()
    if resolved_candidate.parent != resolved_run_base:
        return None, "選択したCI RUNが.build/ci/runsの外を指しています。"
    return resolved_candidate, ""


def resolve_run_artifact(run_dir: Path | None, relative_name: str) -> tuple[Path | None, str]:
    if run_dir is None:
        return None, ""

    candidate = run_dir / relative_name
    if not candidate.exists() and not candidate.is_symlink():
        return None, ""
    if candidate.is_symlink() or not candidate.is_file():
        return None, f"{relative_name}が通常fileではありません。"

    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(run_dir)
    except ValueError:
        return None, f"{relative_name}が選択RUNの外を指しています。"
    return resolved_candidate, ""


def clean_summary_line(line: str) -> str:
    line = re.sub(r"^#+\s*", "", line.strip())
    line = re.sub(r"^[-*]\s*", "", line)
    line = line.replace("`", "")
    return re.sub(r"\s+", " ", line).strip()


def load_verify_output_lines(path: Path, limit: int = 3) -> list[str]:
    lines: list[str] = []
    for raw_line in read_text(path).splitlines():
        cleaned = clean_summary_line(raw_line)
        if not cleaned:
            continue
        lines.append(f"verify出力: {cleaned[:160]}")
        if len(lines) >= limit:
            break
    return lines


def load_summary_lines(path: Path | None) -> list[str]:
    if path is None or not path.is_file():
        return []

    lines: list[str] = []
    for raw_line in read_text(path).splitlines():
        cleaned = clean_summary_line(raw_line)
        if not cleaned:
            continue
        if cleaned in {"AI Run Summary", "CI Run Summary", "Overview"}:
            continue
        lines.append(cleaned)
        if len(lines) >= 6:
            break
    return lines


def parse_meta(path: Path | None) -> tuple[dict[str, object], str]:
    if path is None or not path.is_file():
        return {}, "meta.json が存在しません。"

    try:
        value = json.loads(read_text(path))
        if not isinstance(value, dict):
            return {}, "meta.json はJSON objectではありません。"
        return value, ""
    except Exception as error:  # pragma: no cover - defensive
        return {}, f"meta.json の読取で問題がありました: {error}"


def normalize_lower(value: object) -> str:
    return str(value).strip().lower()


def resolve_failed_log(
    run_dir: Path | None,
    failed_log_value: str,
) -> tuple[Path | None, str]:
    if run_dir is None or not failed_log_value:
        return None, ""

    raw_path = Path(failed_log_value)
    candidate = raw_path if raw_path.is_absolute() else run_dir / raw_path
    if candidate.is_symlink() or not candidate.is_file():
        return None, "meta.jsonのfailed_logが選択RUN内の通常fileではありません。"

    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(run_dir)
    except ValueError:
        return None, "meta.jsonのfailed_logが選択RUNの外を指しています。"
    return resolved_candidate, ""


def collect_warning_samples(*paths: Path | None) -> list[str]:
    samples: list[str] = []
    seen: set[str] = set()

    for path in paths:
        if path is None or not path.is_file():
            continue

        for raw_line in read_text(path).splitlines():
            cleaned = " ".join(raw_line.split())
            lower = cleaned.lower()
            if "warning" not in lower:
                continue
            if "no warning" in lower or "0 warning" in lower:
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            samples.append(cleaned[:160])
            if len(samples) >= 3:
                return samples

    return samples


def warning_looks_external(sample: str) -> bool:
    lower = sample.lower()
    external_markers = (
        "/pods/",
        "pods/",
        "/carthage/",
        "carthage/",
        ".build/checkouts/",
        "sourcepackages/checkouts/",
        "source packages/checkouts/",
    )
    return any(marker in lower for marker in external_markers)


def warning_matches_current_change(sample: str, changed_files: list[str]) -> bool:
    lower = sample.lower()
    path_match = re.match(r"(.+?):\d+(?::\d+)?:\s*warning", sample, re.IGNORECASE)
    if path_match:
        warning_path = path_match.group(1).replace("\\", "/").lower()
        for changed_file in changed_files:
            normalized_changed_file = changed_file.replace("\\", "/").lower()
            if warning_path.endswith(normalized_changed_file):
                return True

    for changed_file in changed_files:
        basename = Path(changed_file).name.lower()
        if basename and basename in lower:
            return True

    return False


def run_command(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
        )
    except FileNotFoundError:
        return None

    if completed.returncode != 0:
        return None

    return completed.stdout


def parse_name_status(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        entries.append((parts[0], parts[-1]))
    return entries


def collect_git_state() -> dict[str, object]:
    git_root = run_command(["git", "rev-parse", "--show-toplevel"])
    if git_root is None:
        return {
            "available": False,
            "staged_files": [],
            "unstaged_files": [],
            "all_files": [],
        }

    outputs = [run_command(["git", "diff", *args, "--no-ext-diff", "--no-textconv", "--relative"])
               for args in (("--cached", "--name-status", "--find-renames"),
                            ("--name-status", "--find-renames"))]
    if any(output is None for output in outputs):
        return {"available": False}
    staged_status = parse_name_status(outputs[0])
    unstaged_status = parse_name_status(outputs[1])

    staged_files = sorted({path for _, path in staged_status})
    unstaged_files = sorted({path for _, path in unstaged_status})
    all_files = sorted(set(staged_files) | set(unstaged_files))

    return {
        "available": True,
        "git_root": git_root.strip(),
        "staged_files": staged_files,
        "unstaged_files": unstaged_files,
        "all_files": all_files,
        "staged_count": len(staged_files),
        "unstaged_count": len(unstaged_files),
    }


def dedupe_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for line in lines:
        if not line or line in seen:
            continue
        result.append(line)
        seen.add(line)
    return result


def limit_lines(lines: list[str], limit: int) -> list[str]:
    return dedupe_lines(lines)[:limit]


(
    latest_run_arg,
    run_dir_arg,
    verify_exit_arg,
    verify_command,
    verify_output_arg,
    run_is_new_arg,
    run_base_arg,
    run_selection_error,
    verification_ran_arg,
) = sys.argv[1:10]
verification_ran = verification_ran_arg == "true"
latest_run = latest_run_arg or "(なし)"
run_dir, run_dir_error = resolve_run_directory(run_dir_arg, run_base_arg)
verify_exit = int(verify_exit_arg)
verify_output = Path(verify_output_arg)
run_is_new = run_is_new_arg == "true"

artifact_integrity_errors = [
    error for error in (run_selection_error, run_dir_error) if error
]
summary_path, summary_error = resolve_run_artifact(run_dir, "summary.md")
meta_path, meta_path_error = resolve_run_artifact(run_dir, "meta.json")
commands_path, commands_error = resolve_run_artifact(run_dir, "commands.txt")
artifact_integrity_errors.extend(
    error for error in (summary_error, meta_path_error, commands_error) if error
)

summary_lines = load_summary_lines(summary_path)
meta, meta_error = parse_meta(meta_path)
if meta_path is not None and meta_error:
    artifact_integrity_errors.append(meta_error)
status_field = str(meta.get("status", ""))
result_field = str(meta.get("result", ""))
success_field = meta.get("success", "")
failed_step = str(meta.get("failed_step", ""))
failed_log_value = str(meta.get("failed_log", ""))

status_lower = normalize_lower(status_field)
result_lower = normalize_lower(result_field)
success_lower = normalize_lower(success_field)
meta_says_failure = success_lower == "false" or status_lower in {"failure", "failed", "error"} or result_lower in {"failure", "failed", "error"}
verify_failed = verify_exit != 0 or meta_says_failure
resolved_failed_log: Path | None = None
if verify_failed:
    resolved_failed_log, failed_log_error = resolve_failed_log(run_dir, failed_log_value)
    if failed_log_error:
        artifact_integrity_errors.append(failed_log_error)
missing_run = run_dir is None

warning_samples = collect_warning_samples(verify_output, resolved_failed_log)
git_state = collect_git_state()
all_files = git_state.get("all_files", [])
repo_warning_samples = [
    sample for sample in warning_samples
    if not warning_looks_external(sample) and warning_matches_current_change(sample, all_files)
]
preexisting_warning_samples = [
    sample for sample in warning_samples
    if not warning_looks_external(sample) and not warning_matches_current_change(sample, all_files)
]
external_warning_samples = [sample for sample in warning_samples if warning_looks_external(sample)]
staged_count = int(git_state.get("staged_count", 0))
unstaged_count = int(git_state.get("unstaged_count", 0))
if bool(git_state.get("available")) and staged_count == 0 and unstaged_count == 0:
    diff_overview = "stage済み 0件 / 未stage 0件を確認しました。作業ツリーに差分はありません。"
else:
    diff_overview = f"stage済み {staged_count}件 / 未stage {unstaged_count}件を確認しました。"

if not verification_ran:
    summary_lines = ["shell検証は未実行です。native契約または別commandの証拠はagentが別途報告してください。"]
elif missing_run:
    if verify_exit == 0:
        summary_lines = [
            f"{verify_command} は成功しました。",
            ".build/ci/runs/ のRUNは作られませんでした。",
        ]
        summary_lines.extend(load_verify_output_lines(verify_output))
    else:
        summary_lines = [
            f"{verify_command} を実行しましたが、.build/ci/runs/ にRUNがありません。",
            f"verify_exit={verify_exit}",
        ]
        summary_lines.extend(load_verify_output_lines(verify_output))
else:
    if not summary_lines:
        summary_lines.append("summary.md が見つかりません。")
    if len(summary_lines) < 3 and status_field:
        summary_lines.append(f"meta.json status: {status_field}")
    if len(summary_lines) < 3 and result_field:
        summary_lines.append(f"meta.json result: {result_field}")
    if len(summary_lines) < 3 and success_field != "":
        summary_lines.append(f"meta.json success: {success_field}")
    if len(summary_lines) < 3:
        summary_lines.append(f"verify_exit={verify_exit}")
    if not run_is_new and len(summary_lines) < 6:
        summary_lines.append("今回の実行では新しいRUNが作られず、既存の最新RUNを参照しました。")
    if meta_error and len(summary_lines) < 6:
        summary_lines.append(meta_error)
    if len(summary_lines) < 6:
        summary_lines.append(diff_overview)
    if len(summary_lines) < 6:
        summary_lines.append(f"実行コマンド: {verify_command}")

summary_lines = limit_lines(summary_lines, 6)

evidence_errors = list(artifact_integrity_errors)
if not bool(git_state.get("available")):
    evidence_errors.append("git diff / staged diff を確認できません。")

result_label = "✅ success" if verification_ran else "未実行 (diffのみ)"
if verify_failed or evidence_errors:
    result_label = "❌ failure"
print(f"結果: {result_label}")
print(f"実行コマンド: {verify_command}; exit={verify_exit if verification_ran else '(未実行)'}")
print(f"最新RUN: {latest_run}")
print("要約:")
for line in summary_lines:
    print(f"- {line}")
print(f"差分: {diff_overview}")
for path in all_files[:10]:
    print(f"- {path}")
for label, samples in (("現在変更に関連する可能性のあるwarning", repo_warning_samples),
                       ("既存要因の可能性のあるwarning", preexisting_warning_samples),
                       ("外部依存の可能性のあるwarning", external_warning_samples)):
    for sample in samples:
        print(f"{label}: {sample}")
for error in evidence_errors:
    print(f"証拠の問題: {error}")
if verify_failed:
    print(f"verify が失敗しています: {failed_step or verify_command}")
    for line in load_verify_output_lines(verify_output):
        print(line)
print("release riskと公開可否はこのhelperの判定対象外です。")
raise SystemExit(verify_exit or (1 if meta_says_failure or evidence_errors else 0))

PY
report_exit=$?
set -e
exit "$report_exit"
