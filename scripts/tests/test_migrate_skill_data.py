from __future__ import annotations

import importlib.util
import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "migrate_skill_data.py"
SPEC = importlib.util.spec_from_file_location("migrate_skill_data", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write_apple_cache(root: Path, cache_path: str) -> None:
    sample_root = root / "samples/example-sample"
    sample_root.mkdir(parents=True)
    metadata = {
        "slug": "example-sample",
        "cache_path": cache_path,
    }
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "samples": {"example-sample": metadata},
            }
        ),
        encoding="utf-8",
    )
    (sample_root / "metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )


class MigrateSkillDataTests(unittest.TestCase):
    def test_list_files_does_not_follow_symbolic_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "source"
            outside = base / "outside"
            source.mkdir()
            outside.mkdir()
            accepted = source / "accepted.md"
            accepted.write_text("accepted", encoding="utf-8")
            outside_file = outside / "outside.md"
            outside_file.write_text("outside", encoding="utf-8")
            (source / "linked-file.md").symlink_to(outside_file)
            (source / "linked-directory").symlink_to(outside, target_is_directory=True)

            self.assertEqual(MODULE.list_files(source), [accepted])

    def test_copy_file_rejects_symbolic_link_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "source.md"
            outside = base / "outside.md"
            target = base / "target.md"
            source.write_text("new", encoding="utf-8")
            outside.write_text("new", encoding="utf-8")
            target.symlink_to(outside)
            stats = MODULE.MigrationStats()

            MODULE.copy_file(source, target, apply=True, stats=stats)

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(outside.read_text(encoding="utf-8"), "new")
            self.assertTrue(target.is_symlink())

    def test_copy_file_rejects_symbolic_link_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "source.md"
            target_root = base / "target"
            outside = base / "outside"
            source.write_text("new", encoding="utf-8")
            target_root.mkdir()
            outside.mkdir()
            (target_root / "linked").symlink_to(outside, target_is_directory=True)
            target = target_root / "linked" / "target.md"
            stats = MODULE.MigrationStats()

            MODULE.copy_file(
                source,
                target,
                apply=True,
                stats=stats,
                target_boundary=target_root,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertFalse((outside / "target.md").exists())

    def test_atomic_copy_preserves_contents_and_leaves_no_temporary_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            source = base / "source.md"
            target_directory = base / "target"
            target = target_directory / "target.md"
            source.write_text("content", encoding="utf-8")
            source.chmod(0o640)
            target_directory.mkdir()
            stats = MODULE.MigrationStats()

            MODULE.copy_file(source, target, apply=True, stats=stats)

            self.assertEqual(stats.copied, 1)
            self.assertEqual(target.read_text(encoding="utf-8"), "content")
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)
            self.assertEqual(list(target_directory.glob(".target.md.*.tmp")), [])

    def test_private_permission_audit_and_apply_skip_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "records"
            directory = root / "principles"
            file_path = directory / "current.md"
            outside = Path(temporary_directory) / "outside.md"
            directory.mkdir(parents=True)
            file_path.write_text("private", encoding="utf-8")
            outside.write_text("outside", encoding="utf-8")
            root.chmod(0o755)
            directory.chmod(0o755)
            file_path.chmod(0o644)
            outside.chmod(0o644)
            (root / "linked.md").symlink_to(outside)

            dry_run = MODULE.MigrationStats()
            MODULE.enforce_private_permissions([root], apply=False, stats=dry_run)
            self.assertEqual(dry_run.permissions_would_change, 3)
            self.assertEqual(stat.S_IMODE(file_path.stat().st_mode), 0o644)

            applied = MODULE.MigrationStats()
            MODULE.enforce_private_permissions([root], apply=True, stats=applied)
            self.assertEqual(applied.permissions_changed, 3)
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(file_path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(outside.stat().st_mode), 0o644)

    def test_apple_cache_migration_rebases_manifest_and_metadata_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            source_sample = source_root / "samples/example-sample"
            source_sample.mkdir(parents=True)
            legacy_path = str(source_sample)
            metadata = {
                "slug": "example-sample",
                "cache_path": legacy_path,
            }
            (source_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "samples": {"example-sample": metadata},
                    }
                ),
                encoding="utf-8",
            )
            (source_sample / "metadata.json").write_text(
                json.dumps(metadata),
                encoding="utf-8",
            )

            dry_run = MODULE.MigrationStats()
            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=False,
                stats=dry_run,
            )
            self.assertEqual(dry_run.metadata_would_rebase, 2)
            self.assertFalse(
                (skills_root / "apple-sample-code-advisor/cache/manifest.json").exists()
            )

            applied = MODULE.MigrationStats()
            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=applied,
            )

            target_root = skills_root / "apple-sample-code-advisor/cache"
            desired_path = str((target_root / "samples/example-sample").resolve())
            target_manifest = json.loads(
                (target_root / "manifest.json").read_text(encoding="utf-8")
            )
            target_metadata = json.loads(
                (target_root / "samples/example-sample/metadata.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(applied.metadata_rebased, 2)
            self.assertEqual(
                target_manifest["samples"]["example-sample"]["cache_path"],
                desired_path,
            )
            self.assertEqual(target_metadata["cache_path"], desired_path)

            second_run = MODULE.MigrationStats()
            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=second_run,
            )
            self.assertEqual(second_run.metadata_rebased, 0)
            self.assertEqual(second_run.conflicts, 0)

    def test_apple_cache_migration_rejects_symbolic_link_target_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            target_root = skills_root / "apple-sample-code-advisor/cache"
            outside_root = base / "outside-cache"
            write_apple_cache(source_root, "legacy-source")
            write_apple_cache(outside_root, "outside-original")
            target_root.parent.mkdir(parents=True)
            target_root.symlink_to(outside_root, target_is_directory=True)
            original_manifest = (outside_root / "manifest.json").read_text(encoding="utf-8")
            original_metadata = (outside_root / "samples/example-sample/metadata.json").read_text(
                encoding="utf-8"
            )
            stats = MODULE.MigrationStats()

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 0)
            self.assertEqual(
                (outside_root / "manifest.json").read_text(encoding="utf-8"),
                original_manifest,
            )
            self.assertEqual(
                (outside_root / "samples/example-sample/metadata.json").read_text(
                    encoding="utf-8"
                ),
                original_metadata,
            )

    def test_apple_cache_migration_rejects_symbolic_link_sample_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            target_root = skills_root / "apple-sample-code-advisor/cache"
            outside_sample = base / "outside-sample"
            write_apple_cache(source_root, "legacy-source")
            target_root.joinpath("samples").mkdir(parents=True)
            outside_sample.mkdir()
            target_metadata = {
                "slug": "example-sample",
                "cache_path": "outside-original",
            }
            (target_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "samples": {"example-sample": target_metadata},
                    }
                ),
                encoding="utf-8",
            )
            (outside_sample / "metadata.json").write_text(
                json.dumps(target_metadata),
                encoding="utf-8",
            )
            (target_root / "samples/example-sample").symlink_to(
                outside_sample,
                target_is_directory=True,
            )
            original_manifest = (target_root / "manifest.json").read_text(encoding="utf-8")
            original_metadata = (outside_sample / "metadata.json").read_text(encoding="utf-8")
            stats = MODULE.MigrationStats()

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 0)
            self.assertEqual(
                (target_root / "manifest.json").read_text(encoding="utf-8"),
                original_manifest,
            )
            self.assertEqual(
                (outside_sample / "metadata.json").read_text(encoding="utf-8"),
                original_metadata,
            )

    def test_apple_cache_migration_rejects_symbolic_link_sample_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            target_root = skills_root / "apple-sample-code-advisor/cache"
            write_apple_cache(source_root, "legacy-source")
            target_root.joinpath("samples").mkdir(parents=True)
            target_metadata = {
                "slug": "example-sample",
                "cache_path": "target-original",
            }
            (target_root / "manifest.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "samples": {"example-sample": target_metadata},
                    }
                ),
                encoding="utf-8",
            )
            (target_root / "samples/example-sample").symlink_to(
                "example-sample",
                target_is_directory=True,
            )
            original_manifest = (target_root / "manifest.json").read_text(encoding="utf-8")
            stats = MODULE.MigrationStats()

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 0)
            self.assertEqual(
                (target_root / "manifest.json").read_text(encoding="utf-8"),
                original_manifest,
            )

    def test_apple_cache_migration_does_not_rebase_after_copy_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            target_root = skills_root / "apple-sample-code-advisor/cache"
            write_apple_cache(source_root, "legacy-source")
            write_apple_cache(target_root, "target-original")
            (source_root / "notes.txt").write_text("source", encoding="utf-8")
            (target_root / "notes.txt").write_text("target", encoding="utf-8")
            original_manifest = (target_root / "manifest.json").read_text(encoding="utf-8")
            original_metadata = (target_root / "samples/example-sample/metadata.json").read_text(
                encoding="utf-8"
            )
            stats = MODULE.MigrationStats()

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 0)
            self.assertEqual(
                (target_root / "manifest.json").read_text(encoding="utf-8"),
                original_manifest,
            )
            self.assertEqual(
                (target_root / "samples/example-sample/metadata.json").read_text(
                    encoding="utf-8"
                ),
                original_metadata,
            )

    def test_apple_cache_migration_ignores_preexisting_conflicts_for_rebase_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            base = Path(temporary_directory)
            skills_root = base / "skills"
            home = base / "home"
            source_root = home / ".codex/cache/apple-sample-code"
            write_apple_cache(source_root, "legacy-source")
            stats = MODULE.MigrationStats(conflicts=1)

            MODULE.migrate_apple_cache(
                skills_root,
                home,
                apply=True,
                stats=stats,
            )

            self.assertEqual(stats.conflicts, 1)
            self.assertEqual(stats.metadata_rebased, 2)


class ExternalSkillMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base = Path(self.temporary_directory.name).resolve()
        self.root = self.base / "skills"
        self.root.mkdir()
        self.source = self.base / "upstream-bundle"
        self.source_skill = self.source / "skills/example/SKILL.md"
        self.source_skill.parent.mkdir(parents=True)
        self.source_skill.write_text("---\nname: example\ndescription: Example.\n---\nBody.\n")
        (self.source / "LICENSE").write_text("Upstream license.\n")
        self.link = self.root / "example-link"
        self.link.symlink_to(self.source_skill.parent, target_is_directory=True)
        self.legacy = self.root / "xcode-skill-alpha"
        self.legacy.mkdir()
        (self.legacy / "SKILL.md").write_text("---\nname: xcode-skill-alpha\ndescription: Example.\n---\n")
        self.sync = MODULE.load_xcode_sync()
        self.sync.write_marker(self.legacy, "alpha", self.legacy.name, xcode_version="Xcode Test")
        self.state = self.root / "sync-xcode-skills/state"
        self.sync.write_catalog(
            self.state, developer_dir=None, export_dir=self.base / "export",
            skills_root=self.root, name_prefix="xcode-skill-", xcode_version="Xcode Test",
            installed=[{
                "installed_name": self.legacy.name, "original_name": "alpha",
                "path": str(self.legacy), "source_path": str(self.base / "export/alpha"),
                "description": "Example.",
            }], skipped=[], pruned=[],
        )

    def migrate(self, *, apply: bool) -> object:
        stats = MODULE.MigrationStats()
        with contextlib.redirect_stdout(io.StringIO()):
            MODULE.migrate_external_skills(
                self.root, self.base, apply, {"external-skills"}, stats, [self.source]
            )
        return stats

    def test_dry_run_does_not_move_or_create_any_destination(self) -> None:
        stats = self.migrate(apply=False)
        self.assertEqual((stats.would_move, stats.would_remove_links), (2, 1))
        self.assertTrue(self.source_skill.is_file())
        self.assertTrue(self.legacy.is_dir())
        self.assertTrue(self.link.is_symlink())
        self.assertFalse((self.root / "external").exists())

    def test_move_preserves_upstream_and_rebases_catalog_without_duplicate_links(self) -> None:
        original_marker = (self.legacy / self.sync.MARKER_FILE).read_bytes()
        original_body = self.source_skill.read_bytes()
        stats = self.migrate(apply=True)
        self.assertEqual((stats.moved, stats.removed_links, stats.conflicts), (2, 1, 0))
        target = self.root / "external/upstream-bundle"
        self.assertEqual((target / "skills/example/SKILL.md").read_bytes(), original_body)
        self.assertEqual((target / "LICENSE").read_text(), "Upstream license.\n")
        xcode = self.root / "external/xcode/xcode-skill-alpha"
        self.assertEqual((xcode / self.sync.MARKER_FILE).read_bytes(), original_marker)
        self.assertFalse(self.source.exists())
        self.assertFalse(self.legacy.exists())
        self.assertFalse(self.link.is_symlink())
        catalog = json.loads((self.state / "catalog.json").read_text())
        self.assertEqual(catalog["skills_root"], str(xcode.parent))
        self.assertEqual(catalog["skills"][0]["path"], str(xcode))
        snapshot = (self.state / "catalog.json").read_bytes()
        repeated = self.migrate(apply=True)
        self.assertEqual((repeated.moved, repeated.conflicts), (0, 0))
        self.assertEqual((self.state / "catalog.json").read_bytes(), snapshot)

    def test_destination_conflict_preserves_all_original_installations(self) -> None:
        destination = self.root / "external/upstream-bundle"
        destination.mkdir(parents=True)
        (destination / "LICENSE").write_text("Keep existing destination.")
        stats = self.migrate(apply=True)
        self.assertEqual(stats.conflicts, 1)
        self.assertTrue(self.source_skill.exists())
        self.assertTrue(self.legacy.exists())
        self.assertTrue(self.link.is_symlink())
        self.assertEqual((destination / "LICENSE").read_text(), "Keep existing destination.")

    def test_unmanaged_reserved_directory_blocks_the_whole_migration(self) -> None:
        (self.legacy / self.sync.MARKER_FILE).unlink()
        stats = self.migrate(apply=True)
        self.assertEqual(stats.conflicts, 1)
        self.assertTrue(self.source_skill.exists())
        self.assertFalse((self.root / "external").exists())

    def test_symbolic_link_destination_cannot_redirect_moved_data(self) -> None:
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / "external").symlink_to(outside, target_is_directory=True)
        stats = self.migrate(apply=True)
        self.assertEqual(stats.conflicts, 1)
        self.assertTrue(self.source_skill.exists())
        self.assertEqual(list(outside.iterdir()), [])

    def test_source_tree_link_blocks_moves_instead_of_omitting_files(self) -> None:
        (self.source / "linked-license").symlink_to(self.source / "LICENSE")
        stats = self.migrate(apply=True)
        self.assertEqual(stats.conflicts, 1)
        self.assertTrue(self.source_skill.exists())
        self.assertTrue(self.legacy.exists())

    def test_catalog_failure_restores_directories_links_and_previous_catalog(self) -> None:
        snapshot = {path.name: path.read_bytes() for path in self.state.iterdir()}
        with mock.patch.object(self.sync, "write_catalog", side_effect=OSError("catalog failure")):
            stats = self.migrate(apply=True)
        self.assertEqual(stats.conflicts, 1)
        self.assertTrue(self.source_skill.exists())
        self.assertTrue(self.legacy.exists())
        self.assertTrue(self.link.is_symlink())
        self.assertEqual(self.link.resolve(), self.source_skill.parent)
        self.assertEqual({path.name: path.read_bytes() for path in self.state.iterdir()}, snapshot)

    def test_cli_defaults_to_dry_run_and_only_runs_external_group(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            result = MODULE.main([
                "--only", "external-skills", "--skills-root", str(self.root),
                "--external-source", str(self.source),
            ])
        self.assertEqual(result, 0)
        self.assertTrue(self.legacy.exists())
        self.assertFalse((self.root / "external").exists())


class FlatExternalRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.base = Path(self.temporary_directory.name).resolve()
        self.root = self.base / "skills"
        self.external = self.root / "external"
        self.legacy = self.external / "manual"
        for name in ("alpha-repository", "beta-repository"):
            bundle = self.legacy / name
            skill = bundle / "skills/example/SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(f"---\nname: {name}\ndescription: Example.\n---\nBody.\n")
            (bundle / "LICENSE").write_text("Preserve upstream license.\n")
        self.xcode_marker = self.external / "xcode/sentinel.txt"
        self.xcode_marker.parent.mkdir()
        self.xcode_marker.write_text("Do not change generated installations.")

    def migrate(self, *, apply: bool, extra: list[str] | None = None) -> int:
        args = ["--only", "external-skills", "--skills-root", str(self.root)]
        if apply:
            args.append("--apply")
        with contextlib.redirect_stdout(io.StringIO()):
            return MODULE.main(args + (extra or []))

    def test_dry_run_preserves_the_legacy_container(self) -> None:
        self.assertEqual(self.migrate(apply=False), 0)
        self.assertTrue((self.legacy / "alpha-repository/LICENSE").is_file())
        self.assertFalse((self.external / "alpha-repository").exists())

    def test_apply_preserves_repository_layout_and_license_and_is_idempotent(self) -> None:
        self.assertEqual(self.migrate(apply=True), 0)
        for name in ("alpha-repository", "beta-repository"):
            bundle = self.external / name
            self.assertTrue((bundle / "skills/example/SKILL.md").is_file())
            self.assertEqual((bundle / "LICENSE").read_text(), "Preserve upstream license.\n")
        self.assertFalse(self.legacy.exists())
        self.assertEqual(self.xcode_marker.read_text(), "Do not change generated installations.")
        self.assertEqual(self.migrate(apply=True), 0)

    def test_collision_blocks_all_moves_and_preserves_the_existing_target(self) -> None:
        target = self.external / "beta-repository"
        target.mkdir()
        (target / "keep.txt").write_text("Keep existing target.")
        self.assertEqual(self.migrate(apply=True), 2)
        self.assertTrue((self.legacy / "alpha-repository/LICENSE").is_file())
        self.assertTrue((self.legacy / "beta-repository/LICENSE").is_file())
        self.assertFalse((self.external / "alpha-repository").exists())
        self.assertEqual((target / "keep.txt").read_text(), "Keep existing target.")

    def test_symbolic_link_container_cannot_redirect_the_migration(self) -> None:
        outside = self.base / "outside"
        self.legacy.rename(outside)
        self.legacy.symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.migrate(apply=True), 2)
        self.assertTrue((outside / "alpha-repository/LICENSE").is_file())
        self.assertFalse((self.external / "alpha-repository").exists())

    def test_move_failure_restores_all_repositories_to_the_container(self) -> None:
        rename = Path.rename
        def fail_second_move(source: Path, destination: Path):
            if source == self.legacy / "beta-repository":
                raise OSError("simulated move failure")
            return rename(source, destination)
        with mock.patch.object(Path, "rename", fail_second_move):
            self.assertEqual(self.migrate(apply=True), 2)
        self.assertTrue((self.legacy / "alpha-repository/LICENSE").is_file())
        self.assertTrue((self.legacy / "beta-repository/LICENSE").is_file())
        self.assertFalse((self.external / "alpha-repository").exists())

    def test_explicit_repository_cannot_claim_the_generated_installation_directory(self) -> None:
        source = self.base / "xcode"
        source.mkdir()
        (source / "SKILL.md").write_text("---\nname: example\ndescription: Example.\n---\n")
        self.assertEqual(self.migrate(apply=True, extra=["--external-source", str(source)]), 2)
        self.assertTrue((source / "SKILL.md").is_file())
        self.assertTrue((self.legacy / "alpha-repository/LICENSE").is_file())


if __name__ == "__main__":
    unittest.main()
