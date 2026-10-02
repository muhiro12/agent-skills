#!/usr/bin/env python3
"""Behavior regression against isolated Git repositories, never live app state."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sqlite3
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "review_release_risk.py"
SPEC = importlib.util.spec_from_file_location("release_risk_under_test", SCRIPT)
REVIEW = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REVIEW
SPEC.loader.exec_module(REVIEW)


class ReleaseRiskBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="release-risk-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        self.git("init", "-b", "main")
        self.write("README.md", "Fixture repository.\n")

    def git(self, *args):
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgsign=false",
             "-c", "user.name=Risk Fixture", "-c", "user.email=fixture@example.invalid",
             "-C", str(self.repo), *args],
            check=True, capture_output=True, text=True,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        )
        return result.stdout.strip()

    def write(self, path, content):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def commit(self, tag=None):
        self.git("add", "--all")
        self.git("commit", "--quiet", "--allow-empty", "-m", "Record fixture state")
        if tag:
            self.git("tag", tag)
        return self.git("rev-parse", "HEAD")

    def snapshot(self):
        return {str(path.relative_to(self.repo)): (path.stat().st_mode, path.stat().st_mtime_ns,
                hashlib.sha256(path.read_bytes()).hexdigest())
                for path in self.repo.rglob("*") if path.is_file()}

    def report(self, head="HEAD", format="json", verbose=False, base="public"):
        before = self.snapshot()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo), "--base-ref", base,
             "--head-ref", head, "--format", format] + (["--verbose"] if verbose else []),
            check=True, capture_output=True, text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0"},
        )
        self.assertEqual(before, self.snapshot(), "Review changed repository/Git content or modification times")
        return json.loads(result.stdout) if format == "json" else result.stdout

    def project(self, version="1.0", build="1", bundle="com.example.fixture", minimum="16.0"):
        return ("buildSettings = {\n" + f"MARKETING_VERSION = {version};\nCURRENT_PROJECT_VERSION = {build};\n"
                + f"PRODUCT_BUNDLE_IDENTIFIER = {bundle};\nIPHONEOS_DEPLOYMENT_TARGET = {minimum};\n" + "};\n")

    def test_version_only_is_zero_and_read_only_with_dirty_worktree(self):
        self.write("App.xcodeproj/project.pbxproj", self.project())
        self.commit("public")
        self.write("App.xcodeproj/project.pbxproj", self.project("2.0", "2"))
        self.commit()
        self.write("untracked.txt", "Preserve local work.\n")
        self.write("README.md", "Dirty local state.\n")
        report = self.report()
        self.assertEqual(report["risk_score"], 0)
        self.assertEqual(report["release_decision"], "Proceed")
        self.assertTrue(any(item["category"] == "release-metadata" for item in report["awareness_items"]))
        self.report(format="markdown")

    def test_mixed_identity_and_minimum_os_keep_independent_causes(self):
        self.write("App.xcodeproj/project.pbxproj", self.project())
        self.commit("public")
        self.write("App.xcodeproj/project.pbxproj", self.project("2.0", "2", "com.example.other", "18.0"))
        self.commit()
        report = self.report()
        categories = {item["category"]: item["score"] for item in report["score_breakdown"]}
        self.assertEqual(categories["release-metadata"], 0)
        self.assertEqual(categories["external-identity-config"], 55)
        self.assertEqual(categories["packaging"], 35)
        self.assertEqual(report["risk_score"], 56)
        identity = next(item for item in report["awareness_items"] if item["category"] == "external-identity-config")
        self.assertIn("identity-fixed", identity["contract_classes"])
        self.assertIn("legacy-support", identity["contract_classes"])

    def test_same_bundle_identifier_format_only_is_zero(self):
        self.write("App.xcodeproj/project.pbxproj", self.project())
        self.commit("public")
        self.write("App.xcodeproj/project.pbxproj", self.project().replace("PRODUCT_BUNDLE_IDENTIFIER =", "  PRODUCT_BUNDLE_IDENTIFIER   ="))
        self.commit()
        self.assertEqual(self.report()["risk_score"], 0)

    def test_external_diff_driver_is_not_executed(self):
        self.write("App.xcodeproj/project.pbxproj", self.project())
        self.commit("public")
        self.write("App.xcodeproj/project.pbxproj", self.project("2.0", "2"))
        self.commit()
        driver = self.repo / "external-diff.sh"
        driver.write_text('#!/bin/sh\ntouch "' + str(self.repo / "forbidden-write") + '"\n')
        driver.chmod(0o755)
        self.git("config", "diff.external", str(driver))
        self.assertEqual(self.report()["risk_score"], 0)
        self.assertFalse((self.repo / "forbidden-write").exists())

    def test_plist_value_change_reports_value_when_key_line_is_unchanged(self):
        path = "App/Info.plist"
        def content(identifier):
            return '<?xml version="1.0"?><plist version="1.0"><dict>\n<key>CFBundleIdentifier</key>\n<string>' + identifier + '</string>\n</dict></plist>\n'
        self.write(path, content("com.example.old"))
        self.commit("public")
        self.write(path, content("com.example.new"))
        self.commit()
        report = self.report()
        identity = next(item for item in report["awareness_items"] if item["category"] == "external-identity-config")
        self.assertIn('old: CFBundleIdentifier = "com.example.old"', identity["contract_values"])
        self.assertIn('new: CFBundleIdentifier = "com.example.new"', identity["contract_values"])
        self.assertGreater(report["risk_score"], 0)

    def test_raw_key_logical_rename_is_zero_and_raw_change_is_visible(self):
        path = "App/Settings/AppStorageKey.swift"
        self.write(path, 'enum AppStorageKey: String {\ncase oldName = "A1B2C3D4"\n}\n')
        self.commit("public")
        self.write(path, 'enum AppStorageKey: String {\ncase newName = "A1B2C3D4"\n}\n')
        self.commit()
        unchanged = self.report()
        self.assertEqual(unchanged["risk_score"], 0)
        values = unchanged["awareness_items"][0]["contract_values"]
        self.assertIn('old: oldName = "A1B2C3D4"', values)
        self.assertIn('new: newName = "A1B2C3D4"', values)
        self.write(path, 'enum AppStorageKey: String {\ncase newName = "E5F6A7B8"\n}\n')
        self.commit()
        changed = self.report()
        self.assertGreater(changed["risk_score"], 0)
        self.assertIn('new: newName = "E5F6A7B8"', changed["awareness_items"][0]["contract_values"])

    def test_required_new_defaults_key_does_not_automatically_add_risk(self):
        path = "App/Settings/AppStorageKey.swift"
        self.write(path, 'enum AppStorageKey: String {\ncase theme = "A1B2C3D4"\n}\n')
        self.write("App/Preferences.swift", "func chooseTheme() { let key = AppStorageKey.theme.rawValue }\n")
        self.commit("public")
        self.write(path, 'enum AppStorageKey: String {\ncase theme = "A1B2C3D4"\ncase selection = "E5F6A7B8"\n}\n')
        self.commit()
        report = self.report()
        self.assertEqual(report["risk_score"], 0)
        self.assertTrue(report["awareness_items"])

    def test_explicit_serialized_enum_logical_rename_preserves_contract(self):
        path = "App/Models/WireMode.swift"
        self.write(path, 'enum WireMode: String, Codable {\ncase oldName = "stable-wire"\n}\n')
        self.commit("public")
        self.write(path, 'enum WireMode: String, Codable {\ncase newName = "stable-wire"\n}\n')
        self.commit()
        report = self.report()
        self.assertEqual(report["risk_score"], 0)
        self.assertTrue(any(item["category"] == "serialized-registered" for item in report["awareness_items"]))

    def test_logical_rename_does_not_exempt_changed_registered_literal(self):
        path = "App/Settings/AppStorageKey.swift"
        self.write(path, 'enum AppStorageKey: String {\ncase oldName = "A1B2C3D4"\n}\nlet restorationIdentifier = "oldName"\n')
        self.commit("public")
        self.write(path, 'enum AppStorageKey: String {\ncase newName = "A1B2C3D4"\n}\nlet restorationIdentifier = "newName"\n')
        self.commit()
        report = self.report()
        self.assertGreater(report["risk_score"], 0)
        self.assertTrue(any(item["category"] == "serialized-registered" for item in report["awareness_items"]))

    def test_new_key_awareness_does_not_hide_change_among_many_unchanged_keys(self):
        path = "App/Settings/AppStorageKey.swift"
        before = "enum AppStorageKey: String {\n" + "".join(f'case key{i} = "R{i:07d}"\n' for i in range(20)) + "}\n"
        self.write(path, before)
        self.commit("public")
        self.write(path, before.replace('"R0000019"', '"NEW00019"'))
        self.commit()
        item = self.report()["awareness_items"][0]
        self.assertIn('old: key19 = "R0000019"', item["contract_values"])
        self.assertIn('new: key19 = "NEW00019"', item["contract_values"])
        self.assertEqual(len(item["contract_values"]), 2)

    def test_schema_addition_reports_exact_type_default_and_consumers(self):
        path = "App/Models/Record.swift"
        self.write(path, "@Model\nclass Record {\nvar name: String = \"\"\n}\n")
        self.commit("public")
        self.write(path, ' @Model\nclass Record {\nvar name: String = ""\nvar reserved: String = ""\n}\n')
        self.write("App/Reader.swift", "func read(_ record: Record) { print(record.reserved) }\n")
        self.commit()
        report = self.report()
        schema = next(item for item in report["awareness_items"] if item["category"] == "durable-state")
        self.assertIn('new: var reserved: String = ""', schema["contract_values"])
        self.assertTrue(any("record.reserved" in value for value in schema["consumers"]))
        self.assertEqual(set(schema["contract_classes"]), {"migration-required", "legacy-support"})
        self.assertLess(report["risk_score"], 30)

    def test_destructive_candidate_is_above_retained_store_crash_not_100(self):
        connection = sqlite3.connect(self.repo / "original.sqlite")
        self.addCleanup(connection.close)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("CREATE TABLE record(value TEXT)")
        connection.execute("INSERT INTO record VALUES ('long-term primary data')")
        connection.commit()
        self.write("backup.txt", "A separate restoration source.\n")
        self.write("App/Recovery.swift", "func recover() {}\n")
        self.commit("public")
        self.write("App/Recovery.swift", 'func recover() {\nfatalError("Cannot open retained sqlite store")\n}\n')
        crash = self.commit()
        crash_report = self.report(crash)
        self.assertEqual(connection.execute("SELECT value FROM record").fetchone()[0], "long-term primary data")
        self.assertTrue((self.repo / "original.sqlite-wal").exists())
        self.write("App/Recovery.swift", "func recover() {\ntry FileManager.default.removeItem(at: sqliteURL)\ntry FileManager.default.removeItem(at: walURL)\ntry FileManager.default.removeItem(at: backupURL)\n}\n")
        self.commit()
        destructive = self.report()
        self.assertGreater(destructive["risk_score"], crash_report["risk_score"])
        self.assertLess(destructive["risk_score"], 100)
        self.assertTrue(all("unverified" in finding["verification_status"] for finding in destructive["review_findings"]))
        self.assertTrue(any("restoration" in value for value in destructive["unverified_items"]))

    def test_version_and_schema_change_are_not_exempted_or_double_added(self):
        self.write("App.xcodeproj/project.pbxproj", self.project())
        self.write("App/Models/Record.swift", "@Model\nclass Record {\nvar name: String = \"\"\n}\n")
        self.commit("public")
        self.write("App/Models/Record.swift", "@Model\nclass Record {\nvar name: String = \"\"\nvar required: String\n}\n")
        schema_head = self.commit()
        schema_score = self.report(schema_head)["risk_score"]
        self.write("App.xcodeproj/project.pbxproj", self.project("2.0", "2"))
        self.commit()
        mixed = self.report()
        self.assertGreater(schema_score, 0)
        self.assertEqual(mixed["risk_score"], schema_score)
        self.assertTrue(any(item["category"] == "durable-state" and item["score"] > 0 for item in mixed["score_breakdown"]))

    def test_historical_head_does_not_use_checkout_model_marker(self):
        path = "App/Models/Record.swift"
        self.write(path, "struct Record {\n// old\n}\n")
        self.commit("public")
        self.write(path, "struct Record {\n// candidate\n}\n")
        candidate = self.commit()
        expected = self.report(candidate)
        self.write(path, "@Model\nclass Record {\nvar injected: String\n}\n")
        self.commit()
        self.write(path, "@Model\nclass Record { var dirty: Int }\n")
        historical = self.report(candidate)
        self.assertEqual(expected, historical)
        self.assertFalse(any(item["category"] == "durable-state" for item in historical["review_findings"]))

    def test_existing_version_migration_reader_is_reported(self):
        self.write("App.xcodeproj/project.pbxproj", self.project())
        self.write("App/Migration.swift", 'func migrate() { let version = Bundle.main.infoDictionary?["CFBundleShortVersionString"]; if version != nil { migrateOldStore() } }\n')
        self.commit("public")
        self.write("App.xcodeproj/project.pbxproj", self.project("2.0", "2"))
        self.commit()
        report = self.report()
        self.assertEqual(report["risk_score"], 40)
        self.assertTrue(any(item["category"] == "version-behavior" for item in report["review_findings"]))

    def test_app_group_is_not_counted_as_two_independent_causes(self):
        path = "App/App.entitlements"
        def content(value):
            return '<?xml version="1.0"?><plist version="1.0"><dict>\n<key>com.apple.security.application-groups</key>\n<array><string>' + value + '</string></array>\n</dict></plist>\n'
        self.write(path, content("group.com.example.old"))
        self.commit("public")
        self.write(path, content("group.com.example.new"))
        self.commit()
        report = self.report()
        self.assertEqual(report["risk_score"], 55)
        self.assertFalse(any(item["category"] == "security-capability" and item["score"] > 0 for item in report["score_breakdown"]))

    def test_same_cause_dedup_preserves_existing_aggregation(self):
        first = REVIEW.ReviewFinding("first", "high", "primary-data", 60, "candidate", "review", ["x"], [], risk_id="same")
        duplicate = REVIEW.ReviewFinding("second", "high", "durable-state", 45, "candidate", "review", ["x"], [], risk_id="same")
        items = REVIEW.score_items([], [first, duplicate], [])
        self.assertEqual(REVIEW.total_score(items), 60)
        self.assertEqual(REVIEW.total_score([{"score": 60}, {"score": 40}, {"score": 25}]), 64)

    def test_adr_does_not_become_personal_acknowledgment(self):
        self.write("App/Settings/AppStorageKey.swift", 'enum AppStorageKey: String {\ncase theme = "A1B2C3D4"\n}\n')
        self.commit("public")
        self.write("App/Settings/AppStorageKey.swift", 'enum AppStorageKey: String {\ncase theme = "E5F6A7B8"\n}\n')
        self.write("docs/adr.md", "Status: Accepted\n")
        self.commit()
        report = self.report()
        self.assertTrue(all(item["acknowledgment_status"].startswith("unconfirmed") for item in report["awareness_items"]))

    def test_scene_restoration_key_is_visible_without_claiming_fixed_identity(self):
        self.commit("public")
        self.write("App/Views/Navigation.swift",
                   '@SceneStorage("Navigation.restoredRoute") var route: String = ""\n')
        self.commit()
        report = self.report()
        scene = next(item for item in report["awareness_items"] if item["category"] == "scene-storage")
        self.assertEqual(scene["contract_values"], ['new: "Navigation.restoredRoute"'])
        self.assertEqual(scene["contract_classes"], [])
        self.assertFalse(any(item["category"] == "durable-state" for item in report["review_findings"]))
        self.assertLess(report["risk_score"], 20)
        self.git("tag", "scene-public")
        self.write("App/Views/Navigation.swift",
                   '@SceneStorage("Navigation.newRoute") var route: String = ""\n')
        self.commit()
        scene = next(item for item in self.report(base="scene-public")["awareness_items"] if item["category"] == "scene-storage")
        self.assertIn('old: "Navigation.restoredRoute"', scene["contract_values"])
        self.assertIn('new: "Navigation.newRoute"', scene["contract_values"])

    def test_default_output_groups_large_evidence_and_keeps_all_serious_kinds(self):
        for index in range(24):
            self.write(f"App/Models/Record{index}.swift",
                       f'@Model\nclass Record{index} {{\nvar originalField{index}: String = ""\n}}\n')
        self.write("App/Recovery.swift", "func recover() {}\n")
        self.commit("public")
        for index in range(24):
            self.write(f"App/Models/Record{index}.swift",
                       f'@Model\nclass Record{index} {{\nvar newField{index}: String = ""\n}}\n')
        self.write("App/Recovery.swift",
                   'func recover() {\ntry FileManager.default.removeItem(at: sqliteURL)\n'
                   'fatalError("Cannot open retained store")\n}\n')
        self.commit()
        report = self.report()
        compact = self.report(format="markdown")
        detailed = self.report(format="markdown", verbose=True)
        self.assertLess(len(compact.splitlines()), 45)
        self.assertGreater(len(detailed), len(compact) * 5)
        self.assertEqual(sum(item["category"] == "durable-state" for item in report["awareness_items"]), 24)
        self.assertIn("originalField23", json.dumps(report))
        self.assertIn("originalField23", detailed)
        self.assertNotIn("originalField23", compact)
        serious_titles = {item["title"] for item in report["review_findings"] if item["score"] >= 40}
        self.assertGreaterEqual(len(serious_titles), 3)
        for title in serious_titles:
            self.assertEqual(compact.count(title), 1)
        self.assertIn(str(report["risk_score"]), compact)
        self.assertTrue(report["risk_diff_snippets"])


if __name__ == "__main__":
    unittest.main()
