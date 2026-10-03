import json
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_verify_and_summarize.sh"


class RunVerifyAndSummarizeTests(unittest.TestCase):
    maxDiff = None

    def test_without_agents_does_not_guess_from_readme_or_script_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_text(root / "README.md", """
                Use native library tests and consumer builds.
                Diagnose prerequisites: `bash ci_scripts/tasks/check_environment.sh --profile rules`.
            """)
            for name in ("verify_task_completion", "check_repository_rules", "check_environment"):
                self._write_executable(root / f"ci_scripts/tasks/{name}.sh",
                                       "#!/bin/bash\ntouch unintended-check\n")
            self._write_text(root / ".build/ci/runs/old/summary.md", "STALE_SUCCESS")
            completed = self._run_helper(root)
            self.assertFalse((root / "unintended-check").exists())
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("未実行 (diffのみ)", completed.stdout)
        self.assertNotIn("✅ success", completed.stdout)
        self.assertNotIn("STALE_SUCCESS", completed.stdout)

    def test_explicit_check_without_agents_preserves_literal_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "ci_scripts/tasks/verify_task_completion.sh",
                                   "#!/bin/bash\ntouch unintended-aggregate\n")
            self._write_executable(root / "checks/check with spaces.sh", """
                #!/bin/bash
                python3 - "$@" <<'PY'
                import json,sys
                from pathlib import Path
                Path('received.json').write_text(json.dumps(sys.argv[1:]))
                PY
            """)
            args = ("--profile", "rules", "a b", "$(touch injected)", "; touch injected")
            completed = self._run_helper(root, "--", "bash", "checks/check with spaces.sh", *args)
            received = json.loads((root / "received.json").read_text())
            self.assertFalse((root / "injected").exists())
            self.assertFalse((root / "unintended-aggregate").exists())
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(received, list(args))
        self.assertIn("✅ success", completed.stdout)

    def test_explicit_missing_check_does_not_run_legacy_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_text(root / "AGENTS.md", "`bash ci_scripts/tasks/verify.sh`\n")
            self._write_executable(root / "ci_scripts/tasks/verify.sh",
                                   "#!/bin/bash\ntouch unintended-fallback\n")
            completed = self._run_helper(root, "--", "bash", "checks/missing.sh")
            self.assertFalse((root / "unintended-fallback").exists())
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("checks/missing.sh", completed.stdout)

    def test_documented_repository_verify_precedes_legacy_delegate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_text(repo_root / "AGENTS.md", """
                Standard verification:
                ```sh
                bash scripts/verify_repository.sh
                ```
                Optional delegate: `bash ci_scripts/tasks/verify.sh`.
            """)
            self._write_executable(repo_root / "scripts/verify_repository.sh",
                                   "#!/bin/bash\necho Repository verification completed\n")
            self._write_executable(repo_root / "ci_scripts/tasks/verify.sh",
                                   "#!/bin/bash\necho WRONG_DELEGATE\nexit 99\n")
            self._commit_all(repo_root, "Add verification fixture")
            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("bash scripts/verify_repository.sh", completed.stdout)
        self.assertNotIn("WRONG_DELEGATE", completed.stdout)

    def test_missing_documented_verify_does_not_fall_back_silently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_text(repo_root / "AGENTS.md", "`bash scripts/verify_repository.sh`\n")
            self._write_executable(repo_root / "ci_scripts/tasks/verify.sh",
                                   "#!/bin/bash\necho WRONG_DELEGATE\n")
            self._commit_all(repo_root, "Add broken verification fixture")
            completed = self._run_helper(repo_root)

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("bash scripts/verify_repository.sh", completed.stdout)
        self.assertNotIn("WRONG_DELEGATE", completed.stdout)

    def test_documented_migration_is_not_executed_as_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._write_text(repo_root / "AGENTS.md", "`bash ci_scripts/migrate.sh`\n")
            marker = repo_root / "mutation.txt"
            self._write_executable(repo_root / "ci_scripts/migrate.sh",
                                   "#!/bin/bash\ntouch mutation.txt\n")
            completed = self._run_helper(repo_root)
            mutated = marker.exists()

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(mutated)

    def test_documented_verify_cannot_follow_an_external_directory_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            repo_root = root / "repo"
            repo_root.mkdir()
            self._init_git_repo(repo_root)
            self._write_text(repo_root / "AGENTS.md", "`bash checks/verify.sh`\n")
            self._write_executable(root / "external/verify.sh",
                                   "#!/bin/bash\ntouch mutation.txt\n")
            (repo_root / "checks").symlink_to(root / "external", target_is_directory=True)
            self._commit_all(repo_root, "Add linked verification fixture")
            completed = self._run_helper(repo_root)
            mutated = (repo_root / "mutation.txt").exists()

        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(mutated)

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")

    def _write_executable(self, path: Path, content: str) -> None:
        self._write_text(path, content)
        path.chmod(0o755)

    def _git(self, repo_root: Path, *args: str) -> str:
        completed = subprocess.run(
            ["git", *args],
            capture_output=True,
            check=True,
            cwd=repo_root,
            text=True,
        )
        return completed.stdout

    def _init_git_repo(self, repo_root: Path) -> None:
        self._git(repo_root, "init")
        self._git(repo_root, "config", "user.email", "skill-test@example.com")
        self._git(repo_root, "config", "user.name", "Skill Test")

    def _write_success_verify_script(
        self,
        repo_root: Path,
        *,
        extra_output: str = "",
        status: str = "success",
        success: str = "true",
    ) -> None:
        self._write_executable(
            repo_root / "ci_scripts" / "tasks" / "verify.sh",
            f"""
            #!/usr/bin/env bash
            set -euo pipefail
            run_dir=".build/ci/runs/20260310-010203-0000"
            mkdir -p "$run_dir"
            cat <<'EOF' > "$run_dir/summary.md"
            # AI Run Summary
            - Verify completed
            - Lint completed
            - Tests completed
            EOF
            cat <<'EOF' > "$run_dir/meta.json"
            {{"result":"{status}","success":{success}}}
            EOF
            {extra_output}
            """,
        )

    def _commit_all(self, repo_root: Path, message: str) -> None:
        self._git(repo_root, "add", ".")
        self._git(repo_root, "commit", "-m", message)

    def _run_helper(self, repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["TMPDIR"] = str(repo_root)
        if "--evidence-dir" in args:
            # Apple's Python launcher may create Xcode lookup files in TMPDIR.
            # Keep fixture infrastructure outside the verified source tree.
            private_temporary = repo_root / ".git/helper-tmp"
            private_temporary.mkdir(exist_ok=True)
            environment["TMPDIR"] = str(private_temporary)
        return subprocess.run(
            ["bash", str(SCRIPT_PATH), *args],
            capture_output=True,
            cwd=repo_root,
            env=environment,
            text=True,
        )

    def test_native_only_repository_reports_unexecuted_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_text(repo_root / "AGENTS.md", "Use native package tests and surface builds.\n")
            self._write_text(repo_root / ".build/ci/runs/old/summary.md", "STALE_NATIVE_EVIDENCE")
            self._commit_all(repo_root, "Add native fixture")
            completed = self._run_helper(repo_root)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("未実行 (diffのみ)", completed.stdout)
        self.assertNotIn("✅ success", completed.stdout)
        self.assertNotIn("STALE_NATIVE_EVIDENCE", completed.stdout)

    def test_does_not_run_an_arbitrary_ci_script_as_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            marker = repo_root / "format-ran.txt"
            self._write_executable(repo_root / "ci_scripts/tasks/format_swift.sh",
                                   "#!/bin/bash\ntouch format-ran.txt\n")
            completed = self._run_helper(repo_root)
            mutated = marker.exists()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("未実行 (diffのみ)", completed.stdout)
        self.assertFalse(mutated)

    def test_low_risk_success_reviews_staged_diff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(repo_root)
            self._write_text(repo_root / "docs" / "overview.md", "before\n")
            self._commit_all(repo_root, "Initial")

            self._write_text(repo_root / "docs" / "overview.md", "after\n")
            self._git(repo_root, "add", "docs/overview.md")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("結果: ✅ success", completed.stdout)
        self.assertIn("stage済み 1件 / 未stage 0件", completed.stdout)

    def test_low_risk_success_on_clean_worktree_still_reports_useful_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(repo_root)
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("結果: ✅ success", completed.stdout)
        self.assertIn("stage済み 0件 / 未stage 0件を確認しました。作業ツリーに差分はありません。", completed.stdout)

    def test_low_risk_success_without_run_artifacts_for_repository_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "check_repository_rules.sh",
                """
                #!/usr/bin/env bash
                set -euo pipefail
                echo "Repository rules check passed."
                """,
            )
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/check_repository_rules.sh")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("結果: ✅ success", completed.stdout)
        self.assertIn("最新RUN: (なし)", completed.stdout)
        self.assertIn("bash ci_scripts/tasks/check_repository_rules.sh は成功しました。", completed.stdout)

    def test_ignores_stale_run_when_repository_rules_make_no_new_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "check_repository_rules.sh",
                """
                #!/usr/bin/env bash
                set -euo pipefail
                echo "Repository rules check passed."
                """,
            )
            self._write_text(
                repo_root / ".build" / "ci" / "runs" / "20260310-010203-0000" / "summary.md",
                """
                # CI Run Summary
                - Old build failed
                """,
            )
            self._write_text(
                repo_root / ".build" / "ci" / "runs" / "20260310-010203-0000" / "meta.json",
                '{"result":"failure","success":false,"failed_step":"old build"}',
            )
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/check_repository_rules.sh")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("結果: ✅ success", completed.stdout)
        self.assertIn("最新RUN: (なし)", completed.stdout)
        self.assertIn("bash ci_scripts/tasks/check_repository_rules.sh は成功しました。", completed.stdout)
        self.assertNotIn("Old build failed", completed.stdout)
        self.assertNotIn("old build", completed.stdout)

    def test_rejects_multiple_new_run_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "verify.sh",
                """
                #!/usr/bin/env bash
                set -euo pipefail
                for run_id in 20260310-010203-0000 20260310-010204-0000; do
                  run_dir=".build/ci/runs/$run_id"
                  mkdir -p "$run_dir"
                  echo '{"result":"success","success":true}' > "$run_dir/meta.json"
                  echo 'Verify completed' > "$run_dir/summary.md"
                done
                """,
            )
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("複数の新しいRUN", completed.stdout)
        self.assertIn("結果: ❌ failure", completed.stdout)

    def test_does_not_read_failed_log_outside_selected_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            outside_log = repo_root / "outside.log"
            secret = "OUTSIDE_FAILED_LOG_MUST_NOT_BE_READ"
            self._write_text(outside_log, f"warning: {secret}\n")
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "verify.sh",
                f"""
                #!/usr/bin/env bash
                set -euo pipefail
                run_dir=".build/ci/runs/20260310-010203-0000"
                mkdir -p "$run_dir"
                echo 'Verify failed' > "$run_dir/summary.md"
                cat <<'EOF' > "$run_dir/meta.json"
                {{"result":"failure","success":false,"failed_log":"{outside_log}"}}
                EOF
                """,
            )
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("failed_logが選択RUNの外", completed.stdout)
        self.assertNotIn(secret, completed.stdout)

    def test_rejects_symlinked_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            outside_run = repo_root / "outside-run"
            secret = "SYMLINKED_RUN_MUST_NOT_BE_READ"
            self._write_text(outside_run / "summary.md", secret + "\n")
            self._write_text(
                outside_run / "meta.json",
                '{"result":"success","success":true}',
            )
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "verify.sh",
                f"""
                #!/usr/bin/env bash
                set -euo pipefail
                mkdir -p ".build/ci/runs"
                ln -s "{outside_run}" ".build/ci/runs/20260310-010203-0000"
                """,
            )
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("symlink entry", completed.stdout)
        self.assertNotIn(secret, completed.stdout)

    def test_agents_entrypoint_prefers_repository_rules_over_format_script(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_text(
                repo_root / "AGENTS.md",
                """
                Run formatting when Swift files are edited:

                ```sh
                bash ci_scripts/tasks/format_swift.sh
                ```

                Then run retained repository rules:

                ```sh
                bash ci_scripts/tasks/check_repository_rules.sh
                ```
                """,
            )
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "format_swift.sh",
                """
                #!/usr/bin/env bash
                set -euo pipefail
                echo "format should not be the final gate"
                """,
            )
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "check_repository_rules.sh",
                """
                #!/usr/bin/env bash
                set -euo pipefail
                echo "Repository rules check passed."
                """,
            )
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("bash ci_scripts/tasks/check_repository_rules.sh は成功しました。", completed.stdout)
        self.assertNotIn("format should not be the final gate", completed.stdout)

    def test_current_change_warning_is_evidence_not_a_failed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(
                repo_root,
                extra_output='echo "Sources/Feature.swift:10: warning: deprecated API is still used"\n',
            )
            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 1\n")
            self._commit_all(repo_root, "Initial")

            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 2\n")
            self._git(repo_root, "add", "Sources/Feature.swift")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("warning", completed.stdout)

    def test_preexisting_warning_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(
                repo_root,
                extra_output='echo "Sources/Legacy.swift:10: warning: deprecated API is still used"\n',
            )
            self._write_text(repo_root / "Sources" / "Legacy.swift", "let legacy = 1\n")
            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 1\n")
            self._commit_all(repo_root, "Initial")

            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 2\n")
            self._git(repo_root, "add", "Sources/Feature.swift")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("既存要因の可能性のあるwarning", completed.stdout)

    def test_external_warning_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(
                repo_root,
                extra_output='echo "SourcePackages/checkouts/SomePkg/Sources/Lib.swift:10: warning: deprecated API is still used"\n',
            )
            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 1\n")
            self._commit_all(repo_root, "Initial")

            self._write_text(repo_root / "Sources" / "Feature.swift", "let value = 2\n")
            self._git(repo_root, "add", "Sources/Feature.swift")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("外部依存の可能性のあるwarning", completed.stdout)

    def test_diff_keyword_does_not_override_command_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_success_verify_script(repo_root)
            self._write_text(
                repo_root / "scripts" / "release.sh",
                """
                #!/usr/bin/env bash
                git push origin main
                """,
            )
            self._commit_all(repo_root, "Initial")

            self._write_text(
                repo_root / "scripts" / "release.sh",
                """
                #!/usr/bin/env bash
                git push --no-verify origin main
                """,
            )
            self._git(repo_root, "add", "scripts/release.sh")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("結果: ✅ success", completed.stdout)
        self.assertIn("scripts/release.sh", completed.stdout)

    def test_verify_failure_reports_current_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            self._init_git_repo(repo_root)
            self._write_executable(
                repo_root / "ci_scripts" / "tasks" / "verify.sh",
                """
                #!/usr/bin/env bash
                set -euo pipefail
                run_dir=".build/ci/runs/20260310-010203-0000"
                mkdir -p "$run_dir"
                cat <<'EOF' > "$run_dir/summary.md"
                # AI Run Summary
                - Build failed
                - Tests did not complete
                EOF
                cat <<'EOF' > "$run_dir/meta.json"
                {"result":"failure","success":false,"failed_step":"tests","failed_log":"failed.log"}
                EOF
                cat <<'EOF' > "$run_dir/failed.log"
                error: test failure
                EOF
                cat <<'EOF' > "$run_dir/commands.txt"
                swift test
                EOF
                exit 1
                """,
            )
            self._write_text(repo_root / "README.md", "base\n")
            self._commit_all(repo_root, "Initial")

            completed = self._run_helper(repo_root, "--", "bash", "ci_scripts/tasks/verify.sh")

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("結果: ❌ failure", completed.stdout)
        self.assertIn("verify が失敗しています", completed.stdout)

    def test_diff_only_skips_existing_shell_checks_and_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "ci_scripts/tasks/verify.sh",
                                   "#!/bin/bash\ntouch verification-ran\n")
            (root / ".build/ci").mkdir(parents=True)
            (root / ".build/ci/runs").symlink_to(root / "outside")
            self._write_text(root / "outside/old/summary.md", "PRIVATE_STALE_EVIDENCE")
            completed = self._run_helper(root, "--diff-only")
            mutated = (root / "verification-ran").exists()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertFalse(mutated)
        self.assertIn("未実行 (diffのみ)", completed.stdout)
        self.assertNotIn("PRIVATE_STALE_EVIDENCE", completed.stdout)

    def test_version_and_contract_paths_do_not_override_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "ci_scripts/tasks/verify.sh", "#!/bin/bash\nexit 0\n")
            for path in ("App.xcodeproj/project.pbxproj", "Info.plist", "Sources/Schema.swift"):
                self._write_text(root / path, "version=1\n")
            self._commit_all(root, "Add version fixture")
            for path in ("App.xcodeproj/project.pbxproj", "Info.plist", "Sources/Schema.swift"):
                self._write_text(root / path, "version=2\n")
            self._git(root, "add", "App.xcodeproj/project.pbxproj")
            completed = self._run_helper(root, "--", "bash", "ci_scripts/tasks/verify.sh")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("stage済み 1件 / 未stage 2件", completed.stdout)

    def test_command_failure_exit_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "ci_scripts/tasks/verify.sh", "#!/bin/bash\necho CHECK_FAILED\nexit 7\n")
            completed = self._run_helper(root, "--", "bash", "ci_scripts/tasks/verify.sh")
        self.assertEqual(completed.returncode, 7, completed.stdout + completed.stderr)
        self.assertIn("CHECK_FAILED", completed.stdout)
        self.assertIn("exit=7", completed.stdout)

    def test_malformed_current_metadata_is_not_success(self) -> None:
        for metadata in ("[]", "{invalid"):
            with self.subTest(metadata=metadata), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                self._init_git_repo(root)
                self._write_executable(root / "ci_scripts/tasks/verify.sh",
                    "#!/bin/bash\nmkdir -p .build/ci/runs/new\n"
                    + "echo '" + metadata + "' > .build/ci/runs/new/meta.json\n")
                completed = self._run_helper(root, "--", "bash", "ci_scripts/tasks/verify.sh")
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn("meta.json", completed.stdout)

    def test_subdirectory_invocation_uses_repository_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_text(root / "AGENTS.md", "`bash scripts/verify_repository.sh`\n")
            self._write_executable(root / "scripts/verify_repository.sh", "#!/bin/bash\necho ROOT_CHECK\n")
            (root / "nested").mkdir()
            completed = self._run_helper(root / "nested")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("ROOT_CHECK", completed.stdout)

    def test_unknown_or_extra_arguments_do_not_execute_checks(self) -> None:
        for args in (("--unknown",), ("--diff-only", "extra"), ("--",),
                     ("--", "bash"), ("--", "bash", ""),
                     ("--", "sh", "ci_scripts/tasks/verify.sh")):
            with self.subTest(args=args), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                self._init_git_repo(root)
                self._write_executable(root / "ci_scripts/tasks/verify.sh",
                                       "#!/bin/bash\ntouch verification-ran\n")
                completed = self._run_helper(root, *args)
                self.assertFalse((root / "verification-ran").exists())
            self.assertEqual(completed.returncode, 2)
            self.assertIn("Usage:", completed.stderr)

    def test_artifact_parent_symlinks_are_rejected_before_execution(self) -> None:
        for component in (".build", ".build/ci"):
            with self.subTest(component=component), tempfile.TemporaryDirectory() as temporary_directory:
                root = Path(temporary_directory)
                self._init_git_repo(root)
                self._write_executable(root / "ci_scripts/tasks/verify.sh",
                                       "#!/bin/bash\ntouch verification-ran\n")
                (root / "outside").mkdir()
                path = root / component
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(root / "outside", target_is_directory=True)
                completed = self._run_helper(root, "--", "bash", "ci_scripts/tasks/verify.sh")
                self.assertFalse((root / "verification-ran").exists())
            self.assertEqual(completed.returncode, 1)
            self.assertIn("symlink", completed.stdout)

    def test_full_diagnostics_are_retained_and_strict_mode_rejects_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "scripts/check.sh",
                "#!/bin/bash\nfor n in 1 2 3 4 5 6; do echo \"Sources/A.swift:$n: warning: issue $n\"; done\n")
            self._commit_all(root, "Initial")
            evidence = root / ".git/evidence"
            completed = self._run_helper(root, "--evidence-dir", str(evidence),
                "--require-clean-diagnostics", "--", "bash", "scripts/check.sh")
            import json
            record = json.loads((evidence / "result.json").read_text())
            raw = (evidence / "output.log").read_text()
            self.assertEqual(record["diagnostics"]["warning_count"], 6)
            self.assertEqual(len(record["diagnostics"]["warnings"]), 6)
            self.assertIn("issue 6", raw)
            self.assertEqual(record["verification"]["status"], "failed")
            self.assertEqual((evidence / "result.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)

    def test_retained_success_records_real_command_source_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "scripts/check.sh",
                "#!/bin/bash\necho 'Executed 2 tests, with 0 failures'\n")
            self._commit_all(root, "Initial")
            evidence = root / ".git/evidence"
            completed = self._run_helper(root, "--evidence-dir", str(evidence),
                "--require-clean-diagnostics", "--", "bash", "scripts/check.sh")
            import json, hashlib
            record = json.loads((evidence / "result.json").read_text())
            self.assertTrue(record["source"]["stable_clean_snapshot"])
            self.assertEqual(record["verification"]["argv"], ["bash", "scripts/check.sh"])
            self.assertEqual(record["tests"]["executed"], 2)
            self.assertEqual(record["artifacts"][0]["sha256"],
                hashlib.sha256((evidence / "output.log").read_bytes()).hexdigest())
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_mutation_during_check_is_not_clean_source_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_text(root / "source.txt", "before\n")
            self._write_executable(root / "scripts/check.sh", "#!/bin/bash\necho after >> source.txt\n")
            self._commit_all(root, "Initial")
            evidence = root / ".git/evidence"
            completed = self._run_helper(root, "--evidence-dir", str(evidence),
                "--", "bash", "scripts/check.sh")
            import json
            record = json.loads((evidence / "result.json").read_text())
            self.assertFalse(record["source"]["stable_clean_snapshot"])
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_successful_run_log_warning_is_not_missed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "scripts/check.sh",
                "#!/bin/bash\nmkdir -p .build/ci/runs/new/logs\n"
                "echo '{\"result\":\"success\"}' > .build/ci/runs/new/meta.json\n"
                "echo 'warning: retained build warning' > .build/ci/runs/new/logs/build.log\n")
            self._commit_all(root, "Initial")
            completed = self._run_helper(root, "--require-clean-diagnostics", "--", "bash", "scripts/check.sh")
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertIn("retained build warning", completed.stdout)

    def test_diff_only_record_is_not_verification_success(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_text(root / "README.md", "base\n")
            self._commit_all(root, "Initial")
            evidence = root / ".git/evidence"
            completed = self._run_helper(root, "--evidence-dir", str(evidence), "--diff-only")
            import json
            record = json.loads((evidence / "result.json").read_text())
            self.assertEqual(record["verification"]["status"], "not_run")
            self.assertIsNone(record["verification"]["exit_code"])
            self.assertFalse(record["diagnostics"]["complete_captured_output"])
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_evidence_directory_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "scripts/check.sh", "#!/bin/bash\nexit 0\n")
            self._commit_all(root, "Initial")
            evidence = root / ".git/evidence"
            evidence.mkdir()
            (evidence / "sentinel").write_text("preserve")
            completed = self._run_helper(root, "--evidence-dir", str(evidence), "--", "bash", "scripts/check.sh")
            self.assertEqual((evidence / "sentinel").read_text(), "preserve")
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)

    def test_direct_tool_preserves_argv_and_retains_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_text(root / "README.md", "base\n")
            self._commit_all(root, "Initial")
            evidence = root / ".git/evidence"
            payload = "$(touch injected); literal argument"
            completed = self._run_helper(root, "--evidence-dir", str(evidence),
                "--require-clean-diagnostics", "--tool", "python3", "-c",
                "import sys; print(sys.argv[1])", payload)
            record = json.loads((evidence / "result.json").read_text())
            self.assertEqual(record["verification"]["argv"][-1], payload)
            self.assertFalse((root / "injected").exists())
            self.assertIn(payload, (evidence / "output.log").read_text())
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_skipped_tests_are_retained_for_push_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "scripts/check.sh",
                "#!/bin/bash\necho 'Test Case example skipped'\necho 'Executed 2 tests, with 0 failures'\n")
            self._commit_all(root, "Initial")
            evidence = root / ".git/evidence"
            completed = self._run_helper(root, "--evidence-dir", str(evidence), "--", "bash", "scripts/check.sh")
            record = json.loads((evidence / "result.json").read_text())
            self.assertEqual(record["tests"]["skipped"], 1)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_swift_testing_is_recorded_after_empty_xctest_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self._init_git_repo(root)
            self._write_executable(root / "scripts/check.sh",
                "#!/bin/bash\necho 'Executed 0 tests, with 0 failures'\n"
                "echo 'Test run with 3 tests passed after 0.01 seconds'\n")
            self._commit_all(root, "Initial")
            evidence = root / ".git/evidence"
            completed = self._run_helper(root, "--evidence-dir", str(evidence), "--", "bash", "scripts/check.sh")
            record = json.loads((evidence / "result.json").read_text())
            self.assertEqual(record["tests"]["executed"], 3)
            self.assertEqual(record["tests"]["skipped"], 0)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

if __name__ == "__main__":
    unittest.main()
