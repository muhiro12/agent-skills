#!/usr/bin/env python3
"""Bind actual Xcode exports and explicit negative-test review to retained output."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


class Incomplete(Exception):
    pass


def require(condition, message):
    if not condition:
        raise Incomplete(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_file(path):
    require(path.is_file() and not path.is_symlink(), "A regular evidence file is required.")
    value = json.loads(path.read_text())
    require(isinstance(value, dict), "Evidence must be a JSON object.")
    return value


def native_nodes(value):
    if isinstance(value, dict):
        yield value
        for child in value.get("children", []):
            yield from native_nodes(child)


def assess(record, build, tests, tree, review, repo, raw_outputs, required_targets):
    verification = record.get("verification", {})
    require(record.get("schema_version") == 1 and verification.get("ran") is True
            and type(verification.get("exit_code")) is int and verification["exit_code"] == 0,
            "The producing Xcode command did not complete successfully.")
    require(record.get("source", {}).get("stable_clean_snapshot") is True
            and not record.get("evidence_errors")
            and record.get("diagnostics", {}).get("complete_captured_output") is True,
            "Source or captured execution evidence is incomplete.")
    require(build.get("status") == "succeeded"
            and all(type(build.get(key)) is int and build[key] == 0 for key in
                    ("errorCount", "warningCount", "analyzerWarningCount"))
            and all(build.get(key) == [] for key in ("errors", "warnings", "analyzerWarnings")),
            "Native build issues or incomplete native build exports remain.")
    diagnostics = record["diagnostics"]
    require(diagnostics.get("warning_count") == 0 and diagnostics.get("warnings") == [],
            "Captured real warnings cannot be reclassified as expected test output.")
    require(not any("BUG IN CLIENT" in output or "AddressSanitizer:" in output
                    or "ThreadSanitizer:" in output for output in raw_outputs.values()),
            "Unexpected runtime or test-lifecycle diagnostics remain in full output.")
    cases, bundles = {}, {}
    if tests is not None:
        require(tests.get("result") == "Passed" and type(tests.get("passedTests")) is int
                and tests["passedTests"] > 0 and tests.get("totalTestCount") == tests["passedTests"]
                and all(tests.get(key) == 0 for key in ("failedTests", "skippedTests", "expectedFailures"))
                and tests.get("testFailures") == [] and tests.get("runtimeWarnings") == [],
                "Native test execution, failures, skips or runtime warnings are unresolved.")
        for root in tree.get("testNodes", []):
            for node in native_nodes(root):
                if node.get("nodeType") == "Test Case":
                    cases[node.get("nodeIdentifierURL")] = node.get("result")
                if node.get("nodeType") in {"Unit test bundle", "UI test bundle"}:
                    bundles[node.get("name")] = node.get("result")
        require(required_targets and all(bundles.get(name) == "Passed" for name in required_targets),
                "A required native test bundle was not executed successfully.")
        require(record.get("tests", {}).get("executed") == tests["totalTestCount"],
                "Captured and native test totals disagree.")
    errors = diagnostics.get("errors", [])
    require(diagnostics.get("error_count") == len(errors), "Captured diagnostics are inconsistent.")
    entries = review.get("errors", []) if review else []
    require(isinstance(entries, list) and len(entries) == len(errors),
            "Every captured error candidate needs an exact explicit review; no blanket exemption.")
    head = record["source"]["before"]["head"]
    require(not errors or tests is not None and review.get("source_head") == head,
            "Expected diagnostic review belongs to a different source or lacks native tests.")
    seen = set()
    for error in errors:
        candidates = [entry for entry in entries if entry.get("line") == error.get("line")
                      and entry.get("text_sha256") == digest(error.get("text", "").encode())]
        require(len(candidates) == 1, "A diagnostic review is missing, duplicated or stale.")
        entry = candidates[0]
        key = (entry["line"], entry["text_sha256"])
        require(key not in seen, "Duplicated diagnostic review.")
        seen.add(key)
        output = raw_outputs.get(entry.get("artifact"), "").splitlines()
        require(0 < entry["line"] <= len(output)
                and digest(output[entry["line"] - 1].encode()) == entry["text_sha256"],
                "Reviewed diagnostic does not match the retained raw artifact.")
        require(cases.get(entry.get("test_id")) == "Passed" and entry.get("reason"),
                "Expected output lacks a passed native test case and contextual explanation.")
        path = Path(entry.get("source_path", ""))
        require(not path.is_absolute() and ".." not in path.parts and path.suffix == ".swift"
                and ("Tests" in path.parts or path.parts[0] in required_targets),
                "Expected output must cite tracked test source in a required test target.")
        source = subprocess.run(["git", "-C", str(repo), "show", head + ":" + str(path)],
                                capture_output=True)
        require(source.returncode == 0 and digest(source.stdout) == entry.get("source_sha256"),
                "The reviewed test source changed or is unavailable.")
    native = {"complete_scope": True, "build": build}
    if tests is not None:
        native.update(tests=tests, test_targets=bundles)
    return native, entries



def fixture_directories(raw_outputs, data_path, target="IncomesLibraryTests"):
    """Select only exact emitted, UUID-named persistent test fixture roots."""
    require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*Tests", target),
            "Fixture cleanup requires a named native test target.")
    marker = target[:-5] + " persistent fixture directory: "
    roots = set()
    for output in raw_outputs.values():
        for line in output.splitlines():
            if line.startswith(marker):
                path = Path(line[len(marker):])
                require(path.parent == data_path / "tmp" and
                        re.fullmatch(re.escape(target) + r"-[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}", path.name),
                        "A fixture marker points outside the assigned test temporary directory.")
                require((not path.exists() or path.is_dir())
                        and all(not part.is_symlink() for part in (path, *path.parents)),
                        "A fixture root is not a directory or is symlinked; cleanup needs explicit review.")
                require(not any(child.is_symlink() for child in path.rglob("*")),
                        "A fixture contains a symlink; cleanup needs explicit review.")
                roots.add(path)
    require(roots, "No owned persistent fixture markers were emitted by this test run.")
    return sorted(roots)


def cleanup_fixtures(argv, raw_outputs, device, target="IncomesLibraryTests"):
    require(argv.count("-destination") == 1 and
            re.search(r"(?:^|,)id=" + re.escape(device) + r"(?:,|$)",
                      argv[argv.index("-destination") + 1]),
            "Fixture cleanup requires the exact producing Simulator destination.")
    result = subprocess.run(["xcrun", "simctl", "list", "devices", "--json"],
                            capture_output=True, text=True, timeout=60)
    require(result.returncode == 0, "Assigned Simulator state is unavailable.")
    devices = [entry for group in json.loads(result.stdout)["devices"].values() for entry in group
               if entry.get("udid") == device]
    require(len(devices) == 1 and devices[0].get("isAvailable") is True
            and devices[0].get("state") == "Shutdown",
            "Finish the owned test process and shut down its device before fixture cleanup.")
    data_path = Path(devices[0]["dataPath"])
    require(data_path.is_absolute() and data_path.name == "data" and data_path.parent.name == device,
            "The assigned device data path is inconsistent.")
    roots = fixture_directories(raw_outputs, data_path, target)
    removed, absent = [], []
    for path in roots:
        if path.exists():
            shutil.rmtree(path)
            removed.append(str(path))
        else:
            absent.append(str(path))
    return {"device": device, "state": "Shutdown", "removed_roots": removed,
            "already_absent_roots": absent}


def export_native(bundle, kind, destination):
    command = ["xcrun", "xcresulttool", "get", *kind, "--path", str(bundle), "--format", "json"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    require(result.returncode == 0, "The official native-result export did not complete.")
    destination.write_text(result.stdout)
    destination.chmod(0o600)
    return object_file(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--cleanup-fixture-device", help="Owned, shutdown Simulator UUID; remove only emitted test fixture roots")
    parser.add_argument("--cleanup-fixture-target", default="IncomesLibraryTests",
                        help="Required native target owning the emitted fixture namespace")
    parser.add_argument("--required-test-target", action="append", default=[])
    args = parser.parse_args()
    try:
        record = object_file(args.evidence / "result.json")
        argv = record.get("verification", {}).get("argv", [])
        require(any(Path(word).name == "xcodebuild" for word in argv)
                and argv.count("-resultBundlePath") == 1,
                "Select the retained producing Xcode command with its explicit result bundle.")
        bundle = Path(argv[argv.index("-resultBundlePath") + 1])
        if not bundle.is_absolute():
            bundle = args.repo / bundle
        require(bundle.is_dir() and not bundle.is_symlink(), "The producing result bundle is missing.")
        require(not args.output.exists() and not args.output.is_symlink(), "Select a new private output directory.")
        args.output.mkdir(mode=0o700)
        raw_outputs = {}
        artifacts = []
        for artifact in record.get("artifacts", []):
            name = artifact.get("path", "")
            require(name and Path(name).name == name, "Raw artifacts must be local regular files.")
            path = args.evidence / name
            require(path.is_file() and not path.is_symlink()
                    and digest(path.read_bytes()) == artifact.get("sha256"), "Raw execution output changed.")
            raw_outputs[name] = path.read_text(errors="replace")
            shutil.copyfile(path, args.output / name)
            (args.output / name).chmod(0o600)
        require(raw_outputs, "Complete raw execution output is missing.")
        shutil.copyfile(args.evidence / "result.json", args.output / "original-result.json")
        (args.output / "original-result.json").chmod(0o600)
        build = export_native(bundle, ["build-results"], args.output / "native-build.json")
        tests, tree = None, None
        if "test" in argv or "test-without-building" in argv:
            tests = export_native(bundle, ["test-results", "summary"], args.output / "native-tests.json")
            tree = export_native(bundle, ["test-results", "tests"], args.output / "native-test-tree.json")
        review = object_file(args.review) if args.review else None
        if args.review:
            shutil.copyfile(args.review, args.output / "expected-test-output-review.json")
            (args.output / "expected-test-output-review.json").chmod(0o600)
        native, expected = assess(record, build, tests, tree, review, args.repo, raw_outputs,
                                  args.required_test_target)
        if args.cleanup_fixture_device:
            require(tests is not None, "Only a completed native test run can own fixture cleanup.")
            require(args.cleanup_fixture_target in args.required_test_target,
                    "Fixture cleanup target must be a successfully required native bundle.")
            cleanup = cleanup_fixtures(argv, raw_outputs, args.cleanup_fixture_device,
                                       args.cleanup_fixture_target)
            cleanup_path = args.output / "fixture-cleanup.json"
            cleanup_path.write_text(json.dumps(cleanup, indent=2) + "\n")
            cleanup_path.chmod(0o600)
        for path in sorted(args.output.iterdir()):
            artifacts.append({"path": path.name, "sha256": digest(path.read_bytes())})
        reviewed = dict(record)
        reviewed.update(producer="ci-verify-xcode-result-review", native=native, artifacts=artifacts)
        reviewed["verification"] = dict(record["verification"], status="passed",
                                        captured_candidate_status=record["verification"]["status"])
        reviewed["diagnostics"] = dict(record["diagnostics"], errors=[], error_count=0,
                                       expected_test_output=expected, expected_test_output_count=len(expected),
                                       scope="full captured output, complete native exports and exact reviewed negative-test output")
        result = args.output / "result.json"
        result.write_text(json.dumps(reviewed, indent=2) + "\n")
        result.chmod(0o600)
        print(json.dumps({"status": "passed", "errors": 0, "warnings": 0,
                          "expected_test_output": len(expected), "native_scope_complete": True}))
        return 0
    except (Incomplete, OSError, ValueError, KeyError, IndexError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "incomplete", "reason": str(exc) if isinstance(exc, Incomplete)
                          else "Native execution evidence is malformed or unavailable."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
