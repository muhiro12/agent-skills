"""Negative fixtures for retained boundary searches and SwiftLint provenance."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest

REPOSITORY = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("swiftlint_evidence", REPOSITORY / "scripts/swiftlint_evidence.py")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def legacy_project():
    return {"rootObject": "root", "objects": {
        "root": {"isa": "PBXProject", "packageReferences": ["fixture"]},
        "fixture": {"isa": "XCRemoteSwiftPackageReference", "repositoryURL": adapter.REMOTE,
                    "requirement": {"kind": "upToNextMajorVersion", "minimumVersion": "0.0.0"}}}}


def json_project():
    return {"packages": [{"kind": "remote", "repository": adapter.REMOTE,
                          "version": {"up-to-next-major-version": "0.0.0"}}]}


class SwiftLintEvidenceTests(unittest.TestCase):
    configuration_name = "project.pbxproj"

    def setUp(self):
        adapter.CONTRACT = {"schema_version":1,"project":"Incomes.xcodeproj","lint":{}}
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        (self.root / "Incomes.xcodeproj").mkdir()
        self.project = self.root / "Incomes.xcodeproj" / self.configuration_name
        self.project.write_bytes(plistlib.dumps(legacy_project()) if self.configuration_name == "project.pbxproj"
                                 else json.dumps(json_project()).encode())
        (self.root / "contract.json").write_text(json.dumps(adapter.CONTRACT))
        (self.root / ".swiftlint.yml").write_text("strict: true\n")
        (self.root / "Value.swift").write_text("let value = 1\n")
        self.git(self.root, "init", "-q")
        self.git(self.root, "add", ".")
        self.git(self.root, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Fixture")
        self.cache = self.root / "cache"
        self.package = self.cache / "checkouts/SwiftLintPlugins"
        self.package.mkdir(parents=True)
        self.url = "https://github.com/realm/SwiftLint/releases/download/0.65.1/SwiftLintBinary.artifactbundle.zip"
        (self.package / "Package.swift").write_text(self.url + '\n"' + "a" * 64 + '"\n')
        self.git(self.package, "init", "-q")
        self.git(self.package, "add", ".")
        self.git(self.package, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Package fixture")
        bundle = self.cache / "artifacts/swiftlintplugins/SwiftLintBinary/SwiftLintBinary.artifactbundle"
        self.binary = bundle / "macos/swiftlint"
        self.binary.parent.mkdir(parents=True)
        self.binary.write_text(f"#!{sys.executable}\nimport sys\nif sys.argv[1]=='version': print('0.65.1')\n")
        self.binary.chmod(0o700)
        (bundle / "info.json").write_text(json.dumps({"artifacts": {"swiftlint": {"type": "executable",
            "version": "0.65.1", "variants": [{"path": "macos/swiftlint"}]}}}))
        reference = {"identity": "swiftlintplugins", "location": adapter.REMOTE}
        self.state = {"object": {"dependencies": [{"packageRef": reference, "subpath": "SwiftLintPlugins",
            "state": {"checkoutState": {"version": "0.65.1", "revision": self.git(self.package, "rev-parse", "HEAD")}}}],
            "artifacts": [{"packageRef": reference, "targetName": "SwiftLintBinary",
                           "source": {"type": "remote", "url": self.url, "checksum": "a" * 64}}]}}
        self.save()
        self.environment = dict(os.environ)
        os.environ.pop("CI_SWIFTLINT_BIN", None)

    def tearDown(self):
        os.environ.clear(); os.environ.update(self.environment)
        self.temporary.cleanup()

    def git(self, root, *args):
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()

    def save(self):
        (self.cache / "workspace-state.json").write_text(json.dumps(self.state))

    def test_registered_binary_and_actual_execution_are_recorded(self):
        selected = adapter.select(self.root, [self.cache])
        self.assertEqual(selected["version"], "0.65.1")
        self.assertEqual(selected["binary_sha256"], adapter.sha256(self.binary))
        self.assertEqual(selected["project_path"], f"Incomes.xcodeproj/{self.configuration_name}")
        self.assertEqual(selected["project_sha256"], adapter.sha256(self.project))
        q = subprocess.run([sys.executable, str(REPOSITORY / "scripts/swiftlint_evidence.py"), str(self.root / "contract.json"), "run",
                            str(self.root), str(self.cache), str(self.root / "unused"), "lint", "Value.swift"],
                           capture_output=True, text=True)
        self.assertEqual(q.returncode, 0, q.stderr)
        proof = json.loads(q.stdout.removeprefix(adapter.MARKER))
        self.assertEqual(proof["files"], ["Value.swift"])
        self.assertEqual(proof["mode"], "lint")
        self.assertEqual(proof["argv"][-2:], ["--strict", "Value.swift"])

    def test_actual_version_mismatch_is_incomplete(self):
        self.binary.write_text(f"#!{sys.executable}\nprint('0.65.2')\n")
        with self.assertRaisesRegex(ValueError, "actual SwiftLint binary version"):
            adapter.select(self.root, [self.cache])

    def test_wrong_package_or_project_requirement_is_incomplete(self):
        self.state["object"]["dependencies"][0]["packageRef"]["location"] = "https://example.invalid/Other"
        self.save()
        with self.assertRaisesRegex(ValueError, "different source"):
            adapter.select(self.root, [self.cache])

    def test_unregistered_override_and_other_repo_cache_are_not_selected(self):
        os.environ["CI_XCODE_GLOBAL_DERIVED_DATA_DIR"] = str(self.cache)
        self.assertIsNone(adapter.select(self.root, [self.root / "missing"]))
        os.environ["CI_SWIFTLINT_BIN"] = str(self.binary)
        with self.assertRaisesRegex(ValueError, "registered artifact"):
            adapter.select(self.root, [self.root / "missing"])
        self.assertEqual(adapter.select(self.root, [self.cache])["binary"], str(self.binary))

    def test_missing_or_changed_package_resolution_is_incomplete(self):
        self.state["object"]["dependencies"][0]["state"]["checkoutState"]["revision"] = "b" * 40
        self.save()
        with self.assertRaisesRegex(ValueError, "checkout changed"):
            adapter.select(self.root, [self.cache])
        (self.cache / "workspace-state.json").unlink()
        with self.assertRaises(OSError):
            adapter.select(self.root, [self.cache])


    def test_tracked_pin_mismatch_is_incomplete(self):
        adapter.CONTRACT["lint"]["resolved"] = "Package.resolved"
        path = self.root / "Package.resolved"
        path.write_text(json.dumps({"pins": [{"identity":"swiftlintplugins", "state":{"version":"0.65.2","revision":"b"*40}}]}))
        with self.assertRaisesRegex(ValueError, "repository pin"):
            adapter.select(self.root, [self.cache])


    def test_resolved_version_must_satisfy_the_project_requirement(self):
        if self.configuration_name == "project.pbxproj":
            document = legacy_project()
            document["objects"]["fixture"]["requirement"]["minimumVersion"] = "1.0.0"
            self.project.write_bytes(plistlib.dumps(document))
        else:
            document = json_project()
            document["packages"][0]["version"]["up-to-next-major-version"] = "1.0.0"
            self.project.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, "project requirement"):
            adapter.select(self.root, [self.cache])


class SwiftLintJSONEvidenceTests(SwiftLintEvidenceTests):
    configuration_name = "project.xcproj"


class ProjectConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.bundle = self.root / "Nested/App.xcodeproj"
        self.bundle.mkdir(parents=True)
        adapter.CONTRACT = {"project": "Nested/App.xcodeproj"}

    def write(self, name, document):
        path = self.bundle / name
        path.write_bytes(plistlib.dumps(document) if name.endswith(".pbxproj") else json.dumps(document).encode())
        return path

    def test_native_formats_and_canonical_git_suffix(self):
        for name, document in (("project.pbxproj", legacy_project()), ("project.xcproj", json_project())):
            with self.subTest(name=name):
                package = document["objects"]["fixture"] if "objects" in document else document["packages"][0]
                package["repositoryURL" if "objects" in document else "repository"] += ".git"
                path = self.write(name, document)
                self.assertEqual(adapter.project_configuration(self.root), path)
                self.assertEqual(adapter.swiftlint_minimum(path), (0, 0, 0))
                path.unlink()

    def test_comments_trailing_commas_and_escaped_string_content(self):
        path = self.bundle / "project.xcproj"
        path.write_text(r'''{
            // An unrelated URL and comma-like string must remain valid.
            "note": "https://example.invalid/a,]//b \"quoted\" /* literal */",
            "packages": [{"kind": "remote", "repository": "https://github.com/SimplyDanny/SwiftLintPlugins",
                          "version": {"up-to-next-major-version": "0.65.1",},},],
        }''')
        self.assertEqual(adapter.swiftlint_minimum(path), (0, 65, 1))
        parsed = subprocess.check_output(["plutil", "-convert", "json", "-o", "-", str(path)])
        self.assertEqual(json.loads(parsed)["note"], 'https://example.invalid/a,]//b "quoted" /* literal */')

    def test_missing_ambiguous_and_nonregular_configurations_reject(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            adapter.project_configuration(self.root)
        self.write("project.pbxproj", legacy_project())
        path = self.write("project.xcproj", json_project())
        with self.assertRaisesRegex(ValueError, "exactly one"):
            adapter.project_configuration(self.root)
        path.unlink()
        (self.bundle / "project.pbxproj").unlink()
        path.mkdir()
        with self.assertRaisesRegex(ValueError, "regular"):
            adapter.project_configuration(self.root)

    def test_symlinked_configuration_and_bundle_reject(self):
        path = self.write("project.xcproj", json_project())
        target = self.root / "external-config"
        path.rename(target)
        path.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "regular"):
            adapter.project_configuration(self.root)
        path.unlink()
        path.symlink_to(self.root / "missing")
        with self.assertRaisesRegex(ValueError, "regular"):
            adapter.project_configuration(self.root)
        path.unlink()
        target.rename(path)
        moved = self.root / "Moved.xcodeproj"
        self.bundle.rename(moved)
        self.bundle.symlink_to(moved, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "regular"):
            adapter.project_configuration(self.root)

    def test_project_path_cannot_escape_the_repository(self):
        for name in ("../App.xcodeproj", str(self.bundle), "App.workspace"):
            with self.subTest(name=name):
                adapter.CONTRACT["project"] = name
                with self.assertRaisesRegex(ValueError, "repository-relative"):
                    adapter.project_configuration(self.root)

    def test_orphaned_legacy_package_cannot_satisfy_dependency(self):
        document = legacy_project()
        document["objects"]["root"]["packageReferences"] = []
        path = self.write("project.pbxproj", document)
        with self.assertRaisesRegex(ValueError, "one canonical"):
            adapter.swiftlint_minimum(path)
        document["objects"]["root"]["isa"] = "PBXGroup"
        self.write(path.name, document)
        with self.assertRaisesRegex(ValueError, "PBXProject"):
            adapter.swiftlint_minimum(path)

    def test_duplicate_or_foreign_dependencies_reject_in_both_formats(self):
        for name, make in (("project.pbxproj", legacy_project), ("project.xcproj", json_project)):
            for mutation in ("duplicate", "foreign", "local"):
                with self.subTest(name=name, mutation=mutation):
                    document = make()
                    if name.endswith(".pbxproj"):
                        package = document["objects"]["fixture"]
                        if mutation == "duplicate":
                            document["objects"]["root"]["packageReferences"].append("fixture")
                        elif mutation == "foreign":
                            package["repositoryURL"] = "https://example.invalid/SwiftLintPlugins"
                        else:
                            package["isa"] = "XCLocalSwiftPackageReference"
                    else:
                        package = document["packages"][0]
                        if mutation == "duplicate":
                            document["packages"].append(dict(package))
                        elif mutation == "foreign":
                            package["repository"] = "https://example.invalid/SwiftLintPlugins"
                        else:
                            package["kind"] = "local"
                    with self.assertRaisesRegex(ValueError, "one canonical"):
                        adapter.swiftlint_minimum(self.write(name, document))

    def test_unsupported_requirement_kinds_and_invalid_versions_reject(self):
        for name, make in (("project.pbxproj", legacy_project), ("project.xcproj", json_project)):
            with self.subTest(name=name):
                document = make()
                if name.endswith(".pbxproj"):
                    requirement = document["objects"]["fixture"]["requirement"]
                    requirement["kind"] = "exactVersion"
                else:
                    requirement = document["packages"][0]["version"]
                    requirement["exact"] = "0.65.1"
                with self.assertRaisesRegex(ValueError, "version requirement"):
                    adapter.swiftlint_minimum(self.write(name, document))
                document = make()
                if name.endswith(".pbxproj"):
                    document["objects"]["fixture"]["requirement"]["minimumVersion"] = "0.65"
                else:
                    document["packages"][0]["version"]["up-to-next-major-version"] = "0.65"
                with self.assertRaisesRegex(ValueError, "Unsupported SwiftLint version"):
                    adapter.swiftlint_minimum(self.write(name, document))

    def test_json_filename_cannot_select_the_legacy_model(self):
        document = {**legacy_project(), **json_project()}
        with self.assertRaisesRegex(ValueError, "JSON project model"):
            adapter.swiftlint_minimum(self.write("project.xcproj", document))

    def test_malformed_configuration_reports_incomplete_from_cli(self):
        contract = self.root / "contract.json"
        contract.write_text(json.dumps({"schema_version": 1, **adapter.CONTRACT}))
        path = self.bundle / "project.xcproj"
        for content in ("{broken", "[]", '{"packages": [null]}', '{"packages": null}',
                        '{"packages": [{"kind": "remote"}]}'):
            with self.subTest(content=content):
                path.write_text(content)
                result = subprocess.run([sys.executable, str(REPOSITORY / "scripts/swiftlint_evidence.py"),
                    str(contract), "select", str(self.root), str(self.root / "cache"), str(self.root / "unused")],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("SwiftLint verification incomplete:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

if __name__ == "__main__":
    unittest.main()
