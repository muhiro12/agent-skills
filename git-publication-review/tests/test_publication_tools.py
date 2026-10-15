"""Synthetic repositories exercise the real supported scanner without validation."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "publication_tools.py"
SPEC = importlib.util.spec_from_file_location("publication_tools", SCRIPT)
TOOLS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOLS)
# Deliberately synthetic, generated locally; never a credential obtained from a service.
SECRET = "gh" + "p_" + "Ab3Cd4Ef5Gh6Ij7Kl8Mn9Op0Qr1St2Uv3Wx4"


class PreflightTests(unittest.TestCase):
    def test_supported_ripgrep_with_and_without_build_revision(self):
        for version in ("ripgrep 15.2.0", "ripgrep 15.2.0 (rev e89fff89ac)"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                binary = Path(directory) / "rg"
                binary.write_text(f"#!{sys.executable}\nprint({version!r})\n")
                binary.chmod(0o700)
                with patch.dict(os.environ, {"PATH": directory}):
                    self.assertEqual(TOOLS.check_tool("rg")["version"], "15.2.0")

    def test_unsupported_ripgrep_versions_remain_incomplete(self):
        for version in ("ripgrep 14.1.1", "ripgrep 15.2.0-rc.1", "ripgrep 16.0.0"):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as directory:
                binary = Path(directory) / "rg"
                binary.write_text(f"#!{sys.executable}\nprint({version!r})\n")
                binary.chmod(0o700)
                with patch.dict(os.environ, {"PATH": directory}):
                    with self.assertRaises(TOOLS.Incomplete):
                        TOOLS.check_tool("rg")

    def test_missing_tool_is_incomplete(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"PATH": directory}):
                with self.assertRaisesRegex(TOOLS.Incomplete, "missing"):
                    TOOLS.check_tool("betterleaks")

    def test_v2_release_candidate_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "betterleaks"
            binary.write_text(f"#!{sys.executable}\nprint('2.0.0-rc.1')\n")
            binary.chmod(0o700)
            with patch.dict(os.environ, {"PATH": directory}):
                with self.assertRaisesRegex(TOOLS.Incomplete, "unsupported"):
                    TOOLS.check_tool("betterleaks")

    def test_report_never_overwrites_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "existing.json"
            report.write_text("preserve")
            with self.assertRaises(FileExistsError):
                TOOLS.write_report(report, {"status": "clean"})
            self.assertEqual(report.read_text(), "preserve")


class ActualScannerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            TOOLS.check_tool("git")
            TOOLS.check_tool("betterleaks")
        except TOOLS.Incomplete as exc:
            raise unittest.SkipTest("Actual scanner fixtures unavailable: " + str(exc))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Synthetic Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.write("README.md", "Synthetic fixture\n")
        self.base = self.commit("Initial fixture")

    def git(self, *args):
        process = TOOLS.run(["git", "-C", str(self.repo), *args])
        self.assertEqual(process.returncode, 0, "Fixture Git command failed")
        return process.stdout.strip()

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "-qm", message)
        return self.git("rev-parse", "HEAD")

    def scan(self, base=None, new_ref=False):
        return TOOLS.scan(self.repo, self.git("rev-parse", "HEAD"),
                          None if new_ref else base or self.base, new_ref)

    def test_added_then_removed_secret_is_in_outgoing_history(self):
        self.write("secret.txt", SECRET + "\n")
        secret_commit = self.commit("Add synthetic credential")
        (self.repo / "secret.txt").unlink()
        head = self.commit("Remove synthetic credential")
        record = self.scan()
        self.assertEqual(record["commits"], sorted([secret_commit, head]))
        self.assertEqual(record["status"], "findings")
        self.assertFalse(record["validation"])
        self.assertIn(secret_commit, {item["Commit"] for item in record["findings"]})
        self.assertNotIn(SECRET, json.dumps(record))
        self.assertNotIn("Match", json.dumps(record))

    def test_existing_baseline_secret_is_excluded_but_new_ref_includes_it(self):
        self.write("prior.txt", SECRET + "\n")
        baseline = self.commit("Prior synthetic credential")
        self.write("README.md", "Only new prose\n")
        self.commit("New prose")
        self.assertEqual(self.scan(base=baseline)["status"], "clean")
        self.assertEqual(self.scan(new_ref=True)["status"], "findings")

    def test_merge_side_history_and_merge_resolution_are_both_scanned(self):
        self.git("switch", "-qc", "side")
        self.write("side.txt", SECRET + "\n")
        side = self.commit("Side history credential")
        self.git("switch", "-q", "main")
        self.write("main.txt", "Main branch prose\n")
        main = self.commit("Main history")
        self.git("merge", "--no-commit", "--no-ff", "side")
        self.write("resolution.txt", SECRET + "\n")
        merge = self.commit("Merge with synthetic resolution credential")
        record = self.scan()
        self.assertEqual(record["commits"], sorted([side, main, merge]))
        self.assertIn(side, {item["Commit"] for item in record["findings"]})
        self.assertTrue(any(item["Commit"] == merge and item["File"] == "resolution.txt"
                            for item in record["findings"]))

    def test_worktree_ignores_config_comments_and_untracked_files(self):
        self.write(".gitignore", "ignored.txt\n")
        self.write(".hidden.txt", SECRET + " # betterleaks:allow\n")
        self.write("ignored.txt", SECRET + "\n")
        self.git("add", "-f", "ignored.txt")
        self.write(".betterleaks.toml", 'title = "No rules"\n')
        self.commit("Track hidden and ignored synthetic credentials")
        self.write("untracked.txt", SECRET + "\n")
        record = self.scan()
        files = {item["File"] for item in record["findings"]}
        self.assertIn(".hidden.txt", files)
        self.assertIn("ignored.txt", files)
        self.assertNotIn("untracked.txt", files)

    def test_benign_identifiers_are_clean_and_cli_exit_is_zero(self):
        self.write("examples.txt", "id = 550e8400-e29b-41d4-a716-446655440000\n"
                   "api_key = YOUR_API_KEY\nPublic text and synthetic fixture identifiers.\n")
        head = self.commit("Benign examples")
        report = Path(self.temporary.name) / "clean.json"
        result = subprocess.run([sys.executable, str(SCRIPT), "scan", "--repo", str(self.repo),
                                 "--head", head, "--base", self.base, "--report", str(report)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(report.read_text())["status"], "clean")
        self.assertEqual(report.stat().st_mode & 0o777, 0o600)

    def test_findings_cli_exit_is_one_without_secret_output(self):
        self.write("secret.txt", SECRET + "\n")
        head = self.commit("Synthetic credential")
        report = Path(self.temporary.name) / "findings.json"
        result = subprocess.run([sys.executable, str(SCRIPT), "scan", "--repo", str(self.repo),
                                 "--head", head, "--base", self.base, "--report", str(report)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertNotIn(SECRET, result.stdout + result.stderr + report.read_text())

    def test_scanner_execution_failure_is_incomplete_not_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "betterleaks"
            binary.write_text(f"#!{sys.executable}\nimport sys\n"
                              "print('1.9.0') if sys.argv[1] == 'version' else None\n"
                              "sys.exit(0 if sys.argv[1] == 'version' else 1)\n")
            binary.chmod(0o700)
            with patch.dict(os.environ, {"PATH": directory + os.pathsep + os.environ["PATH"]}):
                with self.assertRaisesRegex(TOOLS.Incomplete, "scan error"):
                    self.scan()

    def test_git_directory_ignore_is_incomplete(self):
        (self.repo / ".git" / ".betterleaksignore").write_text("fixture fingerprint\n")
        with self.assertRaisesRegex(TOOLS.Incomplete, "ignore file"):
            self.scan()

    def test_partial_clone_is_incomplete_without_fetch(self):
        self.git("config", "remote.synthetic.promisor", "true")
        self.git("config", "remote.synthetic.url", "https://example.invalid/never-fetch")
        with self.assertRaisesRegex(TOOLS.Incomplete, "Partial clone"):
            self.scan()

    def test_shallow_history_is_incomplete(self):
        (self.repo / ".git" / "shallow").write_text(self.base + "\n")
        with self.assertRaisesRegex(TOOLS.Incomplete, "Shallow"):
            self.scan()

    def test_branch_name_is_rejected_as_mutable_boundary(self):
        with self.assertRaisesRegex(TOOLS.Incomplete, "immutable"):
            TOOLS.scan(self.repo, "main", self.base, False)


if __name__ == "__main__":
    unittest.main()
