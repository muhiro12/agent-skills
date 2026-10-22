from __future__ import annotations

import json
import hashlib
import io
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest
from unittest import mock


SCRIPT_DIRECTORY = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIRECTORY))

import sync_xcode_skills  # noqa: E402


class XcodeSourceSelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

    def write_xcode(
        self, name: str, version: str, bundle_version: str, build: str = "TEST123"
    ) -> Path:
        app = self.root / f"{name}.app"
        contents = app / "Contents"
        contents.mkdir(parents=True)
        for filename, data in (
            ("Info.plist", {"CFBundleIdentifier": "com.apple.dt.Xcode"}),
            ("version.plist", {
                "CFBundleShortVersionString": version,
                "CFBundleVersion": bundle_version,
                "ProductBuildVersion": build,
            }),
        ):
            with (contents / filename).open("wb") as stream:
                plistlib.dump(data, stream)
        executable = contents / "Developer/usr/bin/xcodebuild"
        executable.parent.mkdir(parents=True)
        executable.touch()
        executable.chmod(0o755)
        return app.resolve()

    def discover(self, apps: list[Path], *, selected: Path | None = None):
        with mock.patch.object(Path, "glob", return_value=[]), mock.patch.object(
            sync_xcode_skills, "selected_developer_dir", return_value=selected
        ), mock.patch.object(sync_xcode_skills, "run_command", return_value=(
            sync_xcode_skills.CommandResult(0, "\n".join(str(app) for app in apps), "")
        )):
            return sync_xcode_skills.discover_xcodes()

    def test_discovery_ranks_numeric_versions_instead_of_names_or_selected_xcode(self) -> None:
        old = self.write_xcode("Xcode Latest", "27.2", "500")
        middle = self.write_xcode("Xcode", "27.9", "600")
        newest = self.write_xcode("Xcode beta", "27.10", "100")
        discovered = self.discover([old, newest, middle], selected=old / "Contents/Developer")
        self.assertEqual([item.app for item in discovered], [newest, middle, old])
        with mock.patch.object(sync_xcode_skills, "discover_xcodes", return_value=discovered):
            chosen = sync_xcode_skills.resolve_xcode(None, install_only=False)
        self.assertEqual(chosen.app, newest)

    def test_discovery_ranks_builds_with_equal_marketing_versions(self) -> None:
        beta = self.write_xcode("Beta", "27.2", "25400.9")
        newer_beta = self.write_xcode("Beta Two", "27.2.0", "25400.10")
        release = self.write_xcode("Release", "27.2", "25400.10.1")
        discovered = self.discover([release, newer_beta, beta])
        self.assertEqual([item.app for item in discovered], [release, newer_beta, beta])

    def test_discovery_deduplicates_paths_and_ignores_incomplete_installations(self) -> None:
        app = self.write_xcode("Xcode", "27.2", "100")
        alias = self.root / "Alias.app"
        alias.symlink_to(app, target_is_directory=True)
        incomplete = self.write_xcode("Incomplete", "99.0", "999")
        (incomplete / "Contents/Developer/usr/bin/xcodebuild").unlink()
        discovered = self.discover([app, alias, incomplete], selected=app / "Contents/Developer")
        self.assertEqual([item.app for item in discovered], [app])

    def test_standard_directories_work_when_spotlight_is_unavailable(self) -> None:
        app = self.write_xcode("Xcode", "27.2", "100")
        with mock.patch.object(Path, "glob", return_value=[app]), mock.patch.object(
            sync_xcode_skills, "selected_developer_dir", return_value=None
        ), mock.patch.object(sync_xcode_skills, "run_command", return_value=(
            sync_xcode_skills.CommandResult(1, "", "Spotlight unavailable")
        )):
            discovered = sync_xcode_skills.discover_xcodes()
        self.assertEqual([item.app for item in discovered], [app])

    def test_explicit_source_overrides_newest_discovery(self) -> None:
        app = self.write_xcode("Requested", "27.0", "100")
        with mock.patch.object(sync_xcode_skills, "discover_xcodes") as discover:
            chosen = sync_xcode_skills.resolve_xcode(app, install_only=False)
        discover.assert_not_called()
        self.assertEqual(chosen.app, app)

    def test_existing_export_requires_its_source_instead_of_guessing_newest(self) -> None:
        with mock.patch.dict(sync_xcode_skills.os.environ, {}, clear=True), mock.patch.object(
            sync_xcode_skills, "discover_xcodes"
        ) as discover:
            with self.assertRaisesRegex(sync_xcode_skills.SyncError, "requires --developer-dir"):
                sync_xcode_skills.resolve_xcode(None, install_only=True)
        discover.assert_not_called()

    def test_existing_export_accepts_explicit_per_command_source(self) -> None:
        app = self.write_xcode("Export Source", "27.0", "100")
        developer_dir = app / "Contents/Developer"
        with mock.patch.dict(sync_xcode_skills.os.environ, {"DEVELOPER_DIR": str(developer_dir)}):
            chosen = sync_xcode_skills.resolve_xcode(None, install_only=True)
        self.assertEqual(chosen.developer_dir, developer_dir)

    def test_no_local_xcode_produces_actionable_error(self) -> None:
        with mock.patch.object(sync_xcode_skills, "discover_xcodes", return_value=[]):
            with self.assertRaisesRegex(sync_xcode_skills.SyncError, "No complete local Xcode"):
                sync_xcode_skills.resolve_xcode(None, install_only=False)

    def test_install_cli_records_the_export_source_instead_of_the_default_toolchain(self) -> None:
        app = self.write_xcode("Export Source", "27.0", "100")
        developer_dir = app / "Contents/Developer"
        export_dir = self.root / "export"
        skill_dir = export_dir / "alpha"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: Test skill.\n---\n# Alpha\n", encoding="utf-8"
        )
        skills_root = self.root / "skills"
        state_dir = self.root / "state"

        def version(command, **kwargs):
            self.assertEqual(command, ["xcodebuild", "-version"])
            source = kwargs.get("env", {}).get("DEVELOPER_DIR")
            text = "Xcode 27.0\nBuild version TEST123" if source == str(developer_dir) else "Xcode 27.2"
            return sync_xcode_skills.CommandResult(0, text, "")

        with mock.patch.object(sys, "argv", [
            "sync_xcode_skills.py", "--install-only", "--developer-dir", str(app),
            "--export-dir", str(export_dir), "--skills-root", str(skills_root),
            "--state-dir", str(state_dir),
        ]), mock.patch.object(sync_xcode_skills, "run_command", side_effect=version), mock.patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            self.assertEqual(sync_xcode_skills.main(), 0)
        marker = json.loads((skills_root / "xcode-skill-alpha" / sync_xcode_skills.MARKER_FILE).read_text())
        catalog = json.loads((state_dir / "catalog.json").read_text())
        self.assertEqual(marker["xcode_version"], "Xcode 27.0\nBuild version TEST123")
        self.assertEqual(catalog["xcode_version"], marker["xcode_version"])
        self.assertEqual(catalog["selected_developer_dir"], str(developer_dir))

    def test_default_install_and_prune_preserve_manual_external_skills(self) -> None:
        app = self.write_xcode("Export Source", "27.0", "100")
        export_dir = self.root / "export"
        source = export_dir / "sample"
        source.mkdir(parents=True)
        skill_file = source / "SKILL.md"
        skill_file.write_text("---\nname: alpha\ndescription: Example.\n---\nBody.\n")
        home = self.root / "home"
        discovery_root = home / ".agents/skills"
        manual = discovery_root / "external/manual/example/SKILL.md"
        manual.parent.mkdir(parents=True)
        manual.write_text("Preserve this upstream skill.\n")
        with mock.patch.object(Path, "home", return_value=home), mock.patch.object(
            sys, "argv", [
                "sync_xcode_skills.py", "--install-only", "--developer-dir", str(app),
                "--export-dir", str(export_dir), "--state-dir", str(self.root / "state"),
            ]
        ), mock.patch.object(sync_xcode_skills, "run_command", return_value=(
            sync_xcode_skills.CommandResult(0, "Xcode 27.0\nBuild version TEST123", "")
        )), mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(sync_xcode_skills.main(), 0)
            target_root = discovery_root / "external/xcode"
            self.assertTrue((target_root / "xcode-skill-alpha/SKILL.md").is_file())
            skill_file.write_text("---\nname: beta\ndescription: Replacement.\n---\nBody.\n")
            self.assertEqual(sync_xcode_skills.main(), 0)

        self.assertFalse((target_root / "xcode-skill-alpha").exists())
        self.assertTrue((target_root / "xcode-skill-beta/SKILL.md").is_file())
        self.assertFalse((discovery_root / "xcode-skill-beta").exists())
        self.assertEqual(manual.read_text(), "Preserve this upstream skill.\n")

    def test_nested_destination_requires_migration_before_duplicate_installation(self) -> None:
        discovery_root = self.root / "skills"
        legacy = discovery_root / "xcode-skill-alpha"
        legacy.mkdir(parents=True)
        with mock.patch.object(sys, "argv", [
            "sync_xcode_skills.py", "--skills-root", str(discovery_root / "external/xcode"),
        ]), mock.patch.object(sync_xcode_skills, "resolve_xcode") as resolve, mock.patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            self.assertEqual(sync_xcode_skills.main(), 2)
        resolve.assert_not_called()
        self.assertTrue(legacy.is_dir())
        self.assertFalse((discovery_root / "external").exists())

    def test_export_only_can_diagnose_a_legacy_installation_without_migrating(self) -> None:
        app = self.write_xcode("Export Source", "27.0", "100")
        discovery_root = self.root / "skills"
        (discovery_root / "xcode-skill-alpha").mkdir(parents=True)
        with mock.patch.object(sys, "argv", [
            "sync_xcode_skills.py", "--export-only", "--developer-dir", str(app),
            "--skills-root", str(discovery_root / "external/xcode"),
            "--export-dir", str(self.root / "export"),
        ]), mock.patch.object(sync_xcode_skills, "run_command", return_value=(
            sync_xcode_skills.CommandResult(0, "Xcode 27.0\nBuild version TEST123", "")
        )), mock.patch.object(sync_xcode_skills, "export_direct", return_value=(
            sync_xcode_skills.CommandResult(0, "", "")
        )) as export, mock.patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(sync_xcode_skills.main(), 0)
        export.assert_called_once()
        self.assertTrue((discovery_root / "xcode-skill-alpha").is_dir())
        self.assertFalse((discovery_root / "external").exists())

    def test_export_pins_bridge_and_running_app_to_the_same_source(self) -> None:
        app = self.write_xcode("Xcode Beta", "27.2", "100")
        developer_dir = app / "Contents/Developer"
        calls = []

        def run(command, **kwargs):
            calls.append((command, kwargs))
            if command == ["xcrun", "mcpbridge", "--help"]:
                return sync_xcode_skills.CommandResult(0, "MCP_XCODE_PID", "")
            if command[0] == "ps":
                return sync_xcode_skills.CommandResult(
                    0, f"111 /Applications/Older.app/Contents/MacOS/Xcode\n"
                    f"222 {app}/Contents/MacOS/Xcode\n", ""
                )
            return sync_xcode_skills.CommandResult(0, "success", "")

        with mock.patch.dict(sync_xcode_skills.os.environ, {}, clear=True), mock.patch.object(
            sync_xcode_skills, "run_command", side_effect=run
        ):
            result = sync_xcode_skills.export_direct(self.root / "export", 30, developer_dir=developer_dir)
            sync_xcode_skills.xcode_version_text(developer_dir)
        self.assertEqual(result.returncode, 0)
        for command, kwargs in calls:
            if command[0] != "ps":
                self.assertEqual(kwargs["env"]["DEVELOPER_DIR"], str(developer_dir))
            if "export" in command:
                self.assertEqual(kwargs["env"]["MCP_XCODE_PID"], "222")

    def test_wrong_inherited_pid_cannot_redirect_export_to_an_older_xcode(self) -> None:
        app = self.write_xcode("Xcode", "27.2", "100")
        with mock.patch.dict(sync_xcode_skills.os.environ, {"MCP_XCODE_PID": "111"}), mock.patch.object(
            sync_xcode_skills, "run_command", side_effect=[
                sync_xcode_skills.CommandResult(0, "MCP_XCODE_PID", ""),
                sync_xcode_skills.CommandResult(0, f"222 {app}/Contents/MacOS/Xcode\n", ""),
            ]
        ):
            with self.assertRaisesRegex(sync_xcode_skills.SyncError, "does not belong"):
                sync_xcode_skills.export_direct(self.root / "export", 30, developer_dir=app / "Contents/Developer")

    def test_export_stops_when_newest_is_not_running_or_process_access_is_denied(self) -> None:
        app = self.write_xcode("Xcode", "27.2", "100")
        for processes, message in (
            (sync_xcode_skills.CommandResult(0, "111 /Applications/Older.app/Contents/MacOS/Xcode", ""), "found 0"),
            (sync_xcode_skills.CommandResult(1, "", "Operation not permitted"), "Cannot inspect"),
        ):
            with self.subTest(message=message), mock.patch.dict(
                sync_xcode_skills.os.environ, {}, clear=True
            ), mock.patch.object(sync_xcode_skills, "run_command", side_effect=[
                sync_xcode_skills.CommandResult(0, "MCP_XCODE_PID", ""), processes
            ]):
                with self.assertRaisesRegex(sync_xcode_skills.SyncError, message):
                    sync_xcode_skills.export_direct(self.root / "export", 30, developer_dir=app / "Contents/Developer")


class SyncXcodeSkillsTests(unittest.TestCase):
    name_prefix = "xcode-skill-"
    xcode_version = "Xcode Test\nBuild version TEST123"

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.export_root = self.root / "export"
        self.skills_root = self.root / "skills"
        self.state_root = self.root / "state"
        self.export_root.mkdir()
        self.skills_root.mkdir()

    def write_exported_skill(
        self,
        directory_name: str,
        *,
        skill_name: str,
        description: str = "Exported test skill.",
    ) -> Path:
        skill_directory = self.export_root / directory_name
        skill_directory.mkdir()
        (skill_directory / "SKILL.md").write_text(
            "---\n"
            f"name: {skill_name}\n"
            f"description: {description}\n"
            "---\n"
            f"\n# {directory_name}\n",
            encoding="utf-8",
        )
        return skill_directory

    def write_managed_skill(self, original_name: str, *, sentinel: str) -> Path:
        installed_name = f"{self.name_prefix}{original_name}"
        skill_directory = self.skills_root / installed_name
        skill_directory.mkdir()
        (skill_directory / "SKILL.md").write_text(
            "---\n"
            f"name: {installed_name}\n"
            'description: "Previously installed skill."\n'
            "---\n\n# Previously Installed\n",
            encoding="utf-8",
        )
        (skill_directory / "sentinel.txt").write_text(sentinel, encoding="utf-8")
        marker = {
            "managed_by": sync_xcode_skills.MANAGED_BY,
            "original_name": original_name,
            "installed_name": installed_name,
            "synced_at": "2026-01-01T00:00:00+00:00",
            "xcode_version": "Old Xcode",
        }
        (skill_directory / sync_xcode_skills.MARKER_FILE).write_text(
            json.dumps(marker),
            encoding="utf-8",
        )
        return skill_directory

    def synchronize(
        self,
        *,
        name_prefix: str | None = None,
    ) -> tuple[list[dict[str, str]], list[str], list[str]]:
        return sync_xcode_skills.synchronize_exported_skills(
            self.export_root,
            self.skills_root,
            state_dir=self.state_root,
            developer_dir=Path("/Applications/Xcode.app/Contents/Developer"),
            name_prefix=name_prefix or self.name_prefix,
            xcode_version=self.xcode_version,
        )

    def assert_no_transaction_directories(self) -> None:
        leftovers = [
            path.name
            for root in (self.skills_root, self.state_root)
            if root.exists()
            for path in root.iterdir()
            if path.name.startswith((".sync-xcode-skills-", ".catalog-transaction-"))
        ]
        self.assertEqual(leftovers, [])

    def test_reviewed_summary_preserves_complete_upstream_guidance_and_body(self) -> None:
        description = "Guidance for a specialized workflow. " + "Detailed trigger. " * 100
        trigger = "Use for a rare capability that must not be lost."
        body = "# Original Body\n\nKeep the linked reference: [Details](references/details.md).\n"
        source = self.write_exported_skill("alpha", skill_name="alpha")
        (source / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: " + description
            + "\nwhen_to_use: " + trigger + "\n---\n" + body,
            encoding="utf-8",
        )
        original = (source / "SKILL.md").read_text()
        metadata, _ = sync_xcode_skills.parse_frontmatter(source / "SKILL.md")
        digest = hashlib.sha256(json.dumps(
            {key: metadata.get(key, "") for key in ("description", "when_to_use")},
            sort_keys=True, ensure_ascii=False,
        ).encode()).hexdigest()
        # Exercise the real summary lookup while isolating its reviewed data.
        summary_data = json.dumps({"alpha": {"source_sha256": digest, "summary": "Use for the specialized workflow and rare capability."}})
        read_text = Path.read_text
        def read_with_summary(path, *args, **kwargs):
            if path.name == "discovery-summaries.json":
                return summary_data
            return read_text(path, *args, **kwargs)
        with mock.patch.object(Path, "read_text", read_with_summary):
            installed, _, _ = self.synchronize()
        target = self.skills_root / "xcode-skill-alpha" / "SKILL.md"
        result_metadata, result_body = sync_xcode_skills.parse_frontmatter(target)
        self.assertLess(len(result_metadata["description"]), 100)
        self.assertIn(description.strip(), result_body)
        self.assertIn(trigger, result_body)
        self.assertTrue(result_body.endswith(body))
        self.assertEqual((source / "SKILL.md").read_text(), original)
        self.assertEqual(installed[0]["description"], result_metadata["description"])

    def test_changed_upstream_metadata_does_not_reuse_stale_summary(self) -> None:
        metadata = {"description": "New upstream behavior", "when_to_use": "New important trigger"}
        warning = io.StringIO()
        with mock.patch.object(Path, "read_text", return_value=json.dumps({
            "alpha": {"source_sha256": "obsolete", "summary": "Old behavior"}
        })), mock.patch("sys.stderr", warning):
            result = sync_xcode_skills.discovery_description(metadata, "alpha")
        self.assertIn(metadata["description"], result)
        self.assertIn(metadata["when_to_use"], result)
        self.assertNotIn("Old behavior", result)
        self.assertIn("alpha", warning.getvalue())

    def test_unknown_skill_keeps_all_discovery_triggers(self) -> None:
        metadata = {"description": "A new skill. " * 100, "when_to_use": "Important trailing trigger"}
        result = sync_xcode_skills.discovery_description(metadata, "unreviewed-new-skill")
        self.assertIn(metadata["description"].strip(), result)
        self.assertIn(metadata["when_to_use"], result)

    def test_rejects_unsafe_exported_skill_name(self) -> None:
        self.write_exported_skill("unsafe", skill_name="../../outside")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "Invalid exported skill name"):
            self.synchronize()

        self.assertFalse(self.state_root.exists())
        self.assertFalse((self.root / "outside").exists())

    def test_rejects_unsafe_name_prefix(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "Invalid name prefix"):
            self.synchronize(name_prefix="../xcode-skill-")

        self.assertFalse(self.state_root.exists())

    def test_rejects_install_target_symlink_outside_skills_root(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "sentinel.txt").write_text("outside", encoding="utf-8")
        (self.skills_root / "xcode-skill-alpha").symlink_to(outside, target_is_directory=True)

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "symbolic link"):
            self.synchronize()

        self.assertEqual((outside / "sentinel.txt").read_text(encoding="utf-8"), "outside")

    def test_rejects_symbolic_link_inside_exported_skill(self) -> None:
        skill = self.write_exported_skill("alpha", skill_name="alpha")
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        (skill / "linked.txt").symlink_to(outside)

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "must not contain symbolic links"):
            self.synchronize()

        self.assertEqual(outside.read_text(encoding="utf-8"), "outside")
        self.assertFalse((self.skills_root / "xcode-skill-alpha").exists())
        self.assertFalse(self.state_root.exists())

    def test_rejects_duplicate_installed_names_before_mutation(self) -> None:
        self.write_exported_skill("first", skill_name="duplicate")
        self.write_exported_skill("second", skill_name="Duplicate")
        existing = self.write_managed_skill("duplicate", sentinel="old")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "Duplicate installed skill name"):
            self.synchronize()

        self.assertEqual((existing / "sentinel.txt").read_text(encoding="utf-8"), "old")
        self.assertFalse(self.state_root.exists())

    def test_corrupt_marker_remains_a_reserved_prefix_collision(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        existing = self.skills_root / "xcode-skill-alpha"
        existing.mkdir()
        (existing / "sentinel.txt").write_text("do not replace", encoding="utf-8")
        (existing / sync_xcode_skills.MARKER_FILE).write_text("{", encoding="utf-8")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "reserved for Xcode-provided"):
            self.synchronize()

        self.assertEqual(
            (existing / "sentinel.txt").read_text(encoding="utf-8"),
            "do not replace",
        )

    def test_non_mapping_marker_remains_a_reserved_prefix_collision(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        existing = self.skills_root / "xcode-skill-alpha"
        existing.mkdir()
        (existing / "sentinel.txt").write_text("do not replace", encoding="utf-8")
        (existing / sync_xcode_skills.MARKER_FILE).write_text("[]", encoding="utf-8")

        with self.assertRaisesRegex(sync_xcode_skills.SyncError, "reserved for Xcode-provided"):
            self.synchronize()

        self.assertEqual(
            (existing / "sentinel.txt").read_text(encoding="utf-8"),
            "do not replace",
        )

    def test_staging_failure_leaves_all_existing_skills_untouched(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        self.write_exported_skill("beta", skill_name="beta")
        alpha = self.write_managed_skill("alpha", sentinel="old alpha")
        beta = self.write_managed_skill("beta", sentinel="old beta")
        original_validate = sync_xcode_skills.validate_staged_skill

        def fail_second_staged_validation(
            skill_dir: Path,
            *,
            original_name: str,
            installed_name: str,
            xcode_version: str,
        ) -> None:
            if installed_name == "xcode-skill-beta":
                raise sync_xcode_skills.SyncError("injected staged validation failure")
            original_validate(
                skill_dir,
                original_name=original_name,
                installed_name=installed_name,
                xcode_version=xcode_version,
            )

        with mock.patch.object(
            sync_xcode_skills,
            "validate_staged_skill",
            side_effect=fail_second_staged_validation,
        ):
            with self.assertRaisesRegex(
                sync_xcode_skills.SyncError,
                "injected staged validation failure",
            ):
                self.synchronize()

        self.assertEqual((alpha / "sentinel.txt").read_text(encoding="utf-8"), "old alpha")
        self.assertEqual((beta / "sentinel.txt").read_text(encoding="utf-8"), "old beta")
        self.assertFalse(self.state_root.exists())
        self.assert_no_transaction_directories()

    def test_swap_failure_rolls_back_all_existing_skills(self) -> None:
        self.write_exported_skill("aardvark", skill_name="aardvark")
        self.write_exported_skill("alpha", skill_name="alpha")
        self.write_exported_skill("beta", skill_name="beta")
        alpha = self.write_managed_skill("alpha", sentinel="old alpha")
        beta = self.write_managed_skill("beta", sentinel="old beta")
        original_move = sync_xcode_skills.move_path

        def fail_during_second_staged_swap(source: Path, target: Path) -> None:
            if (
                source.parent.name.startswith(".sync-xcode-skills-stage-")
                and source.name == "xcode-skill-beta"
            ):
                raise OSError("injected staged swap failure")
            original_move(source, target)

        with mock.patch.object(
            sync_xcode_skills,
            "move_path",
            side_effect=fail_during_second_staged_swap,
        ):
            with self.assertRaisesRegex(sync_xcode_skills.SyncError, "injected staged swap failure"):
                self.synchronize()

        self.assertEqual((alpha / "sentinel.txt").read_text(encoding="utf-8"), "old alpha")
        self.assertEqual((beta / "sentinel.txt").read_text(encoding="utf-8"), "old beta")
        self.assertFalse((self.skills_root / "xcode-skill-aardvark").exists())
        self.assertFalse(self.state_root.exists())
        self.assert_no_transaction_directories()

    def test_catalog_pair_failure_restores_skills_and_both_catalogs(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        alpha = self.write_managed_skill("alpha", sentinel="old alpha")
        stale = self.write_managed_skill("stale", sentinel="old stale")
        self.state_root.mkdir()
        old_json = '{"old": true}\n'
        old_markdown = "# Old Catalog\n"
        (self.state_root / "catalog.json").write_text(old_json, encoding="utf-8")
        (self.state_root / "catalog.md").write_text(old_markdown, encoding="utf-8")
        original_replace = sync_xcode_skills.os.replace

        def fail_second_catalog_replace(source: Path, target: Path) -> None:
            source_path = Path(source)
            if source_path.parent.name == "new" and source_path.name == "catalog.md":
                raise OSError("injected catalog pair failure")
            original_replace(source, target)

        with mock.patch.object(
            sync_xcode_skills.os,
            "replace",
            side_effect=fail_second_catalog_replace,
        ):
            with self.assertRaisesRegex(sync_xcode_skills.SyncError, "catalog pair failure"):
                self.synchronize()

        self.assertEqual((alpha / "sentinel.txt").read_text(encoding="utf-8"), "old alpha")
        self.assertEqual((stale / "sentinel.txt").read_text(encoding="utf-8"), "old stale")
        self.assertEqual((self.state_root / "catalog.json").read_text(encoding="utf-8"), old_json)
        self.assertEqual(
            (self.state_root / "catalog.md").read_text(encoding="utf-8"),
            old_markdown,
        )
        self.assert_no_transaction_directories()

    def test_successful_transaction_prunes_stale_skill_and_writes_consistent_catalogs(self) -> None:
        self.write_exported_skill("alpha", skill_name="alpha")
        self.write_exported_skill("beta", skill_name="beta")
        alpha = self.write_managed_skill("alpha", sentinel="old alpha")
        stale = self.write_managed_skill("stale", sentinel="old stale")

        installed, skipped, pruned = self.synchronize()

        installed_names = [item["installed_name"] for item in installed]
        self.assertEqual(installed_names, ["xcode-skill-alpha", "xcode-skill-beta"])
        self.assertEqual(skipped, [])
        self.assertEqual(pruned, ["xcode-skill-stale"])
        self.assertFalse((alpha / "sentinel.txt").exists())
        self.assertFalse(stale.exists())
        markers = [
            json.loads(
                (self.skills_root / name / sync_xcode_skills.MARKER_FILE).read_text(
                    encoding="utf-8"
                )
            )
            for name in installed_names
        ]
        catalog = json.loads((self.state_root / "catalog.json").read_text(encoding="utf-8"))
        catalog_markdown = (self.state_root / "catalog.md").read_text(encoding="utf-8")
        self.assertEqual(
            [marker["xcode_version"] for marker in markers],
            [self.xcode_version, self.xcode_version],
        )
        self.assertEqual(catalog["xcode_version"], self.xcode_version)
        self.assertEqual(
            [skill["installed_name"] for skill in catalog["skills"]],
            installed_names,
        )
        self.assertIn(f"Generated at: `{catalog['generated_at']}`", catalog_markdown)
        self.assertIn("Xcode version: `Xcode Test Build version TEST123`", catalog_markdown)
        self.assertIn("`xcode-skill-alpha`", catalog_markdown)
        self.assertIn("`xcode-skill-beta`", catalog_markdown)
        self.assertIn("`xcode-skill-stale`", catalog_markdown)
        self.assert_no_transaction_directories()


if __name__ == "__main__":
    unittest.main()
