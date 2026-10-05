"""Native evidence/negative-output contract tests; no Xcode execution is claimed."""
import copy
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/review_xcode_evidence.py"
SPEC = importlib.util.spec_from_file_location("review_xcode_evidence", SCRIPT)
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name).resolve()
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()
        git("init", "-q")
        git("config", "user.name", "Synthetic Fixture")
        git("config", "user.email", "fixture@example.invalid")
        git("config", "commit.gpgsign", "false")
        self.source_path = "Tests/FailureTests.swift"
        source = self.repo / self.source_path
        source.parent.mkdir()
        source.write_text("func readOnlySave() { /* synthetic #expect(throws:) source */ }\n")
        git("add", "Tests")
        git("commit", "-qm", "Synthetic test source")
        self.head = git("rev-parse", "HEAD")
        self.record = {"schema_version": 1,
                       "verification": {"ran": True, "exit_code": 0, "status": "failed"},
                       "source": {"stable_clean_snapshot": True, "before": {"head": self.head}},
                       "evidence_errors": [], "tests": {"executed": 1},
                       "diagnostics": {"complete_captured_output": True, "warning_count": 0,
                                       "warnings": [], "error_count": 1,
                                       "errors": [{"line": 1, "text": "CoreData: error: synthetic refused save"}]}}
        self.build = {"status": "succeeded", "errorCount": 0, "warningCount": 0,
                      "analyzerWarningCount": 0, "errors": [], "warnings": [], "analyzerWarnings": []}
        self.tests = {"result": "Passed", "passedTests": 1, "totalTestCount": 1,
                      "failedTests": 0, "skippedTests": 0, "expectedFailures": 0,
                      "testFailures": [], "runtimeWarnings": []}
        self.case = "test://fixture/FailureTests/readOnlySave()"
        self.tree = {"testNodes": [{"nodeType": "Unit test bundle", "name": "RequiredTests",
                     "result": "Passed", "children": [{"nodeType": "Test Case",
                     "nodeIdentifierURL": self.case, "result": "Passed"}]}]}
        self.raw = {"output.log": "CoreData: error: synthetic refused save\n"}
        self.review = {"source_head": self.head, "errors": [{"line": 1, "artifact": "output.log",
                       "text_sha256": REVIEW.digest(self.raw["output.log"].strip().encode()),
                       "test_id": self.case, "source_path": self.source_path,
                       "source_sha256": REVIEW.digest(source.read_bytes()),
                       "reason": "Synthetic asserted refusal; not product evidence."}]}

    def assess(self):
        return REVIEW.assess(self.record, self.build, self.tests, self.tree, self.review,
                             self.repo, self.raw, ["RequiredTests"])

    def test_exact_review_and_native_case_match(self):
        native, expected = self.assess()
        self.assertTrue(native["complete_scope"])
        self.assertEqual(len(expected), 1)
        self.assertEqual(self.record["diagnostics"]["error_count"], 1)

    def test_real_captured_or_native_warning_cannot_be_exempted(self):
        for target, key in ((self.record["diagnostics"], "warning_count"), (self.build, "warningCount")):
            target[key] = 1
            with self.assertRaises(REVIEW.Incomplete):
                self.assess()
            target[key] = 0

    def test_missing_stale_duplicate_or_wrong_source_review_rejects(self):
        original = copy.deepcopy(self.review)
        for mutation in (lambda r: r["errors"].clear(),
                         lambda r: r["errors"].append(copy.deepcopy(r["errors"][0])),
                         lambda r: r["errors"][0].update(text_sha256="changed"),
                         lambda r: r["errors"][0].update(source_sha256="changed"),
                         lambda r: r.update(source_head="0" * 40)):
            self.review = copy.deepcopy(original)
            mutation(self.review)
            with self.assertRaises(REVIEW.Incomplete):
                self.assess()

    def test_failed_or_missing_native_case_cannot_explain_output(self):
        self.tree["testNodes"][0]["children"][0]["result"] = "Failed"
        with self.assertRaises(REVIEW.Incomplete):
            self.assess()

    def test_missing_bundle_skips_counts_or_unexpected_runtime_fault_rejects(self):
        self.tree["testNodes"][0]["name"] = "OtherTests"
        with self.assertRaises(REVIEW.Incomplete):
            self.assess()
        self.tree["testNodes"][0]["name"] = "RequiredTests"
        self.tests["skippedTests"] = 1
        with self.assertRaises(REVIEW.Incomplete):
            self.assess()
        self.tests["skippedTests"] = 0
        self.raw["output.log"] += "BUG IN CLIENT OF libsqlite3\n"
        with self.assertRaises(REVIEW.Incomplete):
            self.assess()

    def test_fixture_cleanup_selects_exact_emitted_roots_only(self):
        data = self.repo / "device" / "data"
        tmp = data / "tmp"
        tmp.mkdir(parents=True)
        root = tmp / "IncomesLibraryTests-12345678-1234-1234-1234-123456789ABC"
        root.mkdir()
        unrelated = tmp / "unrelated"
        unrelated.mkdir()
        raw = {"output.log": "IncomesLibrary persistent fixture directory: " + str(root) + "\n"}
        self.assertEqual(REVIEW.fixture_directories(raw, data), [root])
        self.assertTrue(unrelated.exists())
        for rejected in (unrelated, self.repo / root.name):
            with self.assertRaises(REVIEW.Incomplete):
                REVIEW.fixture_directories({"output.log": "IncomesLibrary persistent fixture directory: " + str(rejected)}, data)
        (root / "link").symlink_to(unrelated)
        with self.assertRaises(REVIEW.Incomplete):
            REVIEW.fixture_directories(raw, data)


if __name__ == "__main__":
    unittest.main()
