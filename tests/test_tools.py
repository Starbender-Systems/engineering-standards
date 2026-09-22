"""Behavioral tests against disposable consumers and mutated source checkouts."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from _standards import SEMVER  # noqa: E402


def inventory(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="engineering-standards-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.consumer = self.directory / "consumer"
        self.consumer.mkdir()
        shutil.copytree(ROOT / "templates/repository-bootstrap/.agent", self.consumer / ".agent")
        self.manifest_path = self.consumer / ".agent/manifest.yaml"

    def run_tool(self, tool, *args, code=0):
        result = subprocess.run([sys.executable, str(ROOT / "tools" / tool), *map(str, args)],
                                text=True, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def sync(self, *args, code=0):
        return self.run_tool("sync_standards.py", self.consumer, *args, code=code)

    def edit_manifest(self, **changes):
        manifest = json.loads(self.manifest_path.read_text())
        manifest.update(changes)
        self.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def source_copy(self):
        source = self.directory / "source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv"))
        return source

    def test_bootstrap_sync_idempotence_and_check_preserve_local_files(self):
        for path in ("AGENTS.md", "CLAUDE.md", "DEVELOPING.md", ".github/copilot-instructions.md",
                     ".agent/local-notes.md", "src/app.py"):
            target = self.consumer / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("locally owned\n", encoding="utf-8")
        initial = inventory(self.consumer)
        self.assertIn("ADD .agent/standards/general.md", self.sync())
        after = inventory(self.consumer)
        for path, value in initial.items():
            self.assertEqual(after[path], value, path)
        self.assertIn("0 change(s)", self.sync())
        self.assertEqual(inventory(self.consumer), after)
        self.assertIn("No drift", self.sync("--check"))
        self.assertEqual(inventory(self.consumer), after)
        for group in ("standards", "workflows", "skills"):
            for source in (ROOT / group).rglob("*"):
                if source.is_file():
                    self.assertEqual(source.read_bytes(), (self.consumer / ".agent" / source.relative_to(ROOT)).read_bytes())

    def test_check_before_first_sync_is_read_only(self):
        before = inventory(self.consumer)
        output = self.sync("--check", code=1)
        self.assertIn("Drift detected", output)
        self.assertEqual(inventory(self.consumer), before)

    def test_drift_reports_missing_and_changed_files_then_repairs(self):
        self.sync()
        modified = self.consumer / ".agent/standards/general.md"
        missing = self.consumer / ".agent/workflows/release.md"
        modified.write_text("local drift", encoding="utf-8")
        missing.unlink()
        before = inventory(self.consumer)
        output = self.sync("--check", code=1)
        self.assertIn("UPDATE .agent/standards/general.md", output)
        self.assertIn("ADD .agent/workflows/release.md", output)
        self.assertEqual(inventory(self.consumer), before)
        self.sync()
        self.sync("--check")

    def test_dependencies_follow_shared_links_without_copying_unrelated_stack(self):
        self.edit_manifest(standards=["python"], workflows=[], skills=[])
        self.sync()
        self.assertTrue((self.consumer / ".agent/standards/testing.md").is_file())
        self.assertTrue((self.consumer / ".agent/workflows/feature-development.md").is_file())
        self.assertFalse((self.consumer / ".agent/standards/kicad.md").exists())
        self.sync("--check")

    def test_reduced_selection_prunes_only_unmodified_tracked_files(self):
        self.sync()
        self.edit_manifest(standards=[], workflows=[], skills=[])
        output = self.sync()
        self.assertIn("REMOVE .agent/standards/kicad.md", output)
        self.assertFalse((self.consumer / ".agent/standards/kicad.md").exists())
        self.sync("--check")

    def test_modified_stale_file_blocks_entire_plan(self):
        self.sync()
        target = self.consumer / ".agent/standards/kicad.md"
        target.write_text("uncommitted modification", encoding="utf-8")
        self.edit_manifest(standards=[], workflows=[], skills=[])
        before = inventory(self.consumer)
        self.assertIn("modified stale file", self.sync(code=2))
        self.assertEqual(inventory(self.consumer), before)

    def test_unknown_file_in_shared_directory_is_preserved(self):
        self.sync()
        (self.consumer / ".agent/standards/local.md").write_text("local", encoding="utf-8")
        before = inventory(self.consumer)
        self.assertIn("Untracked file", self.sync(code=2))
        self.assertEqual(inventory(self.consumer), before)

    def test_unknown_identifier_version_and_scope_rejected_without_writes(self):
        original = self.manifest_path.read_bytes()
        for change, message in (({"standards": ["nonexistent"]}, "Unknown standards"),
                                ({"release": "9.0.0"}, "does not match local checkout"),
                                ({"synchronized": ["../AGENTS.md"]}, "Undeclared synchronization scope"),
                                ({"schema_version": True}, "schema_version"),
                                ({"workflows": "release"}, "list of strings"),
                                ({"skills": ["sb-dotnet-engineering"] * 2}, "duplicate entries")):
            with self.subTest(change=change):
                self.manifest_path.write_bytes(original)
                self.edit_manifest(**change)
                before = inventory(self.consumer)
                self.assertIn(message, self.sync(code=2))
                self.assertEqual(inventory(self.consumer), before)

    def test_missing_write_scope_rejected_before_any_change(self):
        self.edit_manifest(synchronized=["standards/", "workflows/", "VERSION", "sync-state.json"])
        before = inventory(self.consumer)
        self.assertIn("Refusing undeclared", self.sync(code=2))
        self.assertEqual(inventory(self.consumer), before)

    def test_invalid_manifest_forms_have_clear_errors(self):
        for content, expected in (("release: 0.1.0\n", "JSON-form YAML"),
                                  ('{"release":"0.1.0","release":"0.2.0"}', "duplicate key"),
                                  ("[]", "must be an object"), ("{}", "missing keys")):
            with self.subTest(content=content):
                self.manifest_path.write_text(content, encoding="utf-8")
                self.assertIn(expected, self.sync(code=2))
        self.manifest_path.unlink()
        self.assertIn("manifest.yaml", self.sync(code=2))

    def test_malicious_state_cannot_delete_locally_owned_file(self):
        self.sync()
        local = self.consumer / "AGENTS.md"
        local.write_text("preserve me", encoding="utf-8")
        state_path = self.consumer / ".agent/sync-state.json"
        state = json.loads(state_path.read_text())
        state["files"]["../AGENTS.md"] = "0" * 64
        state_path.write_text(json.dumps(state), encoding="utf-8")
        before = inventory(self.consumer)
        self.assertIn("Invalid tracked path", self.sync(code=2))
        self.assertEqual(inventory(self.consumer), before)

    def test_destination_link_is_rejected(self):
        outside = self.directory / "outside"
        outside.mkdir()
        link = self.consumer / ".agent/standards"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            # Directory junctions exercise the Windows reparse-point boundary
            # without requiring the CreateSymbolicLink privilege.
            environment = dict(os.environ, STANDARDS_TEST_LINK=str(link),
                               STANDARDS_TEST_TARGET=str(outside))
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                 "-Path $env:STANDARDS_TEST_LINK -Target $env:STANDARDS_TEST_TARGET | Out-Null"],
                env=environment, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("symbolic link or reparse point", self.sync(code=2))
        self.assertEqual(list(outside.iterdir()), [])

    def test_source_traversal_reference_is_rejected(self):
        source = self.source_copy()
        catalog_path = source / "standards-manifest.yaml"
        catalog = json.loads(catalog_path.read_text())
        catalog["standards"]["general"] = "../outside.md"
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        self.assertIn("expected path standards/general.md", self.sync("--source", source, code=2))

    def test_custom_source_release_updates_pin_and_hashes(self):
        self.sync()
        source = self.source_copy()
        (source / "VERSION").write_text("0.2.0\n", encoding="utf-8")
        catalog_path = source / "standards-manifest.yaml"
        catalog = json.loads(catalog_path.read_text())
        catalog["release"] = "0.2.0"
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        with (source / "standards/general.md").open("a", encoding="utf-8") as handle:
            handle.write("\nUpdated guidance.\n")
        self.edit_manifest(release="0.2.0")
        self.sync("--source", source)
        self.assertEqual((self.consumer / ".agent/VERSION").read_text(), "0.2.0\n")
        self.assertIn("Updated guidance", (self.consumer / ".agent/standards/general.md").read_text())
        self.sync("--source", source, "--check")

    def test_output_is_deterministic_and_help_is_available(self):
        first = self.sync("--check", code=1)
        self.assertEqual(first, self.sync("--check", code=1))
        for tool in ("sync_standards.py", "validate_repository.py"):
            self.assertIn("usage:", self.run_tool(tool, "--help"))

    def test_valid_repository_passes(self):
        self.assertIn("validation passed", self.run_tool("validate_repository.py"))

    def test_validator_catches_missing_structure_metadata_and_links(self):
        source = self.source_copy()
        mutations = (
            ("VERSION", "01.2.3\n", "invalid semantic version"),
            ("templates/repository-bootstrap/.agent/VERSION", "0.2.0\n", "Bootstrap VERSION"),
            ("standards/general.md", "# General\n", "missing heading"),
            ("skills/sb-dotnet-engineering/SKILL.md", "# Skill\n", "missing front matter"),
            ("templates/CLAUDE.md", "[missing](.agent/standards/missing.md)\n", "broken relative link"),
            ("templates/CLAUDE.md", "Read `.agent/standards/missing.md`.\n", "broken relative link"),
            ("README.md", "[broken](standards/general.md#missing-anchor)\n", "missing Markdown anchor"),
            ("README.md", "[example][ref]\n\n[ref]: absent.md\n", "broken relative link"),
            ("README.md", "<!-- authority: standard.general -->\n", "Duplicate authority"),
        )
        for relative, replacement, expected in mutations:
            with self.subTest(path=relative, expected=expected):
                path = source / relative
                original = path.read_bytes()
                path.write_text(replacement, encoding="utf-8")
                self.assertIn(expected, self.run_tool("validate_repository.py", "--root", source, code=1))
                path.write_bytes(original)
        (source / "workflows/release.md").unlink()
        self.assertIn("Missing required file", self.run_tool("validate_repository.py", "--root", source, code=1))

    def test_semantic_version_examples(self):
        for value in ("0.1.0", "1.2.3", "1.0.0-rc.1", "2.0.0+build.4"):
            self.assertIsNotNone(SEMVER.fullmatch(value), value)
        for value in ("01.2.3", "1.2", "v1.2.3", "1.2.3-01", "-1.2.3"):
            self.assertIsNone(SEMVER.fullmatch(value), value)


if __name__ == "__main__":
    unittest.main()
