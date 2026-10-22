"""End-to-end common and library bootstrap through the root command."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def inventory(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}


class RepositoryBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="repository-bootstrap-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.consumer = self.directory / "repository with spaces"
        self.consumer.mkdir()
        self.library_options = ["--type", "library", "--name", "example", "--display-name", "Example Library",
                                "--repository", "https://example.com/library"]

    def run_command(self, *args, code=0):
        result = subprocess.run([sys.executable, str(ROOT / "bootstrap.py"), *map(str, args)],
                                cwd=self.directory, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def bootstrap(self, *args, code=0):
        return self.run_command(self.consumer, *args, code=code)

    def run_tool(self, script, *args, code=0):
        result = subprocess.run([sys.executable, str(ROOT / "tools" / script), *map(str, args)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.consumer), *map(str, args)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def assert_common_setup(self):
        self.assertEqual((self.consumer / "tools/update_standards.py").read_bytes(),
                         (ROOT / "tools/update_standards.py").read_bytes())
        for name in ("AGENTS.md", "CLAUDE.md", "DEVELOPING.md"):
            self.assertEqual((self.consumer / name).read_bytes(), (ROOT / "templates" / name).read_bytes())
        for directory in ("templates/.github", "templates/repository-bootstrap/.agent"):
            for source in (ROOT / directory).rglob("*"):
                if source.is_file():
                    prefix = ROOT / ("templates" if directory.endswith(".github") else "templates/repository-bootstrap")
                    self.assertEqual((self.consumer / source.relative_to(prefix)).read_bytes(), source.read_bytes())
        self.assertIn("No drift", self.run_tool("sync_standards.py", self.consumer, "--check"))
        state = json.loads((self.consumer / ".agent/sync-state.json").read_bytes())
        for path, sha in state["files"].items():
            self.assertEqual(hashlib.sha256((self.consumer / ".agent" / path).read_bytes()).hexdigest(), sha)

    def test_default_type_installs_the_entire_common_setup_and_preserves_unrelated_files(self):
        for name in ("README.md", ".github/workflows/existing.yml", "src/app.txt", ".agent/local-notes.md"):
            path = self.consumer / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("existing work\n", encoding="utf-8")
        before = inventory(self.consumer)
        self.assertIn("Bootstrapped repository", self.bootstrap())
        after = inventory(self.consumer)
        for path, value in before.items():
            self.assertEqual(after[path], value)
        self.assert_common_setup()
        self.assertFalse((self.consumer / "plugins").exists())
        self.assertFalse((self.consumer / ".git").exists())
        self.assertFalse((self.consumer / "docs/consumers").exists())

    def test_read_only_checks_and_identical_reruns_for_both_types(self):
        self.assertIn("files missing", self.bootstrap("--check", code=1))
        self.assertEqual(inventory(self.consumer), {})
        self.bootstrap()
        before = inventory(self.consumer)
        self.assertIn("0 file(s)", self.bootstrap())
        self.bootstrap("--check")
        self.assertEqual(inventory(self.consumer), before)
        self.assertIn("files missing", self.bootstrap(*self.library_options, "--check", code=1))
        self.assertEqual(inventory(self.consumer), before)
        self.bootstrap(*self.library_options)
        self.assert_common_setup()
        before = inventory(self.consumer)
        self.bootstrap(*self.library_options, "--check")
        self.assertIn("0 file(s)", self.bootstrap(*self.library_options))
        self.assertEqual(inventory(self.consumer), before)

    def test_library_type_installs_common_setup_and_valid_consumer_tooling(self):
        self.assertIn("Bootstrapped library", self.bootstrap(*self.library_options))
        self.assert_common_setup()
        self.run_tool("consumer_tooling.py", "validate", self.consumer)
        catalog = json.loads((self.consumer / "docs/consumers/catalog.json").read_bytes())
        plugin = json.loads((self.consumer / "plugins/example-consumer/plugin.json").read_bytes())
        self.assertEqual(catalog["library"]["ref"], "HEAD")
        self.assertEqual(plugin["version"], "0.1.0")
        self.assertTrue((self.consumer / ".github/workflows/consumer-tooling.yml").is_file())
        self.assertTrue((self.consumer / "tools/consumer_tooling.py").is_file())

    def test_library_release_metadata_options_are_forwarded(self):
        self.bootstrap(*self.library_options, "--library-ref", "v1.2.3", "--plugin-version", "0.2.0")
        catalog = json.loads((self.consumer / "docs/consumers/catalog.json").read_bytes())
        plugin = json.loads((self.consumer / "plugins/example-consumer/plugin.json").read_bytes())
        self.assertEqual(catalog["library"]["ref"], "v1.2.3")
        self.assertEqual(plugin["version"], "0.2.0")

    def test_common_conflicts_block_the_entire_library_plan(self):
        (self.consumer / "AGENTS.md").write_text("custom instructions\n", encoding="utf-8")
        before = inventory(self.consumer)
        self.assertIn("Refusing to overwrite", self.bootstrap(*self.library_options, code=2))
        self.assertEqual(inventory(self.consumer), before)

    def test_library_conflicts_block_the_entire_common_plan(self):
        conflict = self.consumer / "plugins/example-consumer/plugin.json"
        conflict.parent.mkdir(parents=True)
        conflict.write_text("custom plugin\n", encoding="utf-8")
        before = inventory(self.consumer)
        self.assertIn("Refusing to overwrite", self.bootstrap(*self.library_options, code=2))
        self.assertEqual(inventory(self.consumer), before)
        self.assertFalse((self.consumer / ".agent").exists())

    def test_invalid_or_misplaced_library_options_do_not_write(self):
        for options, message in ((["--type", "library"], "requires --name"),
                                  (["--name", "unused"], "require --type library"),
                                  (self.library_options + ["--plugin-version", "invalid"], "semantic versioning"),
                                  (self.library_options + ["--name", "../escape"], "Invalid plugin/skill identifier")):
            with self.subTest(options=options):
                self.assertIn(message, self.bootstrap(*options, code=2))
                self.assertEqual(inventory(self.consumer), {})
        self.run_command(self.consumer, "--type", "unknown", code=2)
        self.assertEqual(inventory(self.consumer), {})

    def test_unknown_shared_files_are_preserved_and_block_initialization(self):
        unexpected = self.consumer / ".agent/standards/local.md"
        unexpected.parent.mkdir(parents=True)
        unexpected.write_text("local guidance\n", encoding="utf-8")
        before = inventory(self.consumer)
        self.assertIn("Untracked file in shared snapshot", self.bootstrap(code=2))
        self.assertEqual(inventory(self.consumer), before)

    def test_changed_snapshot_is_never_overwritten_by_bootstrap(self):
        self.bootstrap()
        target = self.consumer / ".agent/standards/general.md"
        target.write_text("local change\n", encoding="utf-8")
        before = inventory(self.consumer)
        self.assertIn("Refusing to overwrite", self.bootstrap(code=2))
        self.assertEqual(inventory(self.consumer), before)

    def test_missing_or_overlapping_target_and_help(self):
        self.assertIn("does not exist", self.run_command(self.directory / "missing", code=2))
        self.assertIn("must not overlap", self.run_command(ROOT, code=2))
        self.assertIn("usage:", self.run_command("--help"))

    def test_linked_destinations_are_rejected_before_writing(self):
        outside = self.directory / "outside"
        outside.mkdir()
        link = self.consumer / ".github"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            env = dict(os.environ, BOOTSTRAP_TEST_LINK=str(link), BOOTSTRAP_TEST_TARGET=str(outside))
            result = subprocess.run(["powershell", "-NoProfile", "-Command",
                                     "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                                     "-Path $env:BOOTSTRAP_TEST_LINK -Target $env:BOOTSTRAP_TEST_TARGET | Out-Null"],
                                    env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("symbolic link or reparse point", self.bootstrap(code=2))
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.consumer / "AGENTS.md").exists())

    def test_snapshot_hashes_survive_git_checkout_with_autocrlf_enabled(self):
        self.bootstrap()
        self.git("init", "--quiet")
        self.git("-c", "core.autocrlf=true", "add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.com",
                 "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                 "commit", "--quiet", "-m", "Bootstrap fixture")
        checkout = self.directory / "checkout"
        self.git("-c", "core.autocrlf=true", "clone", "--quiet", "--no-hardlinks", self.consumer, checkout)
        self.assertIn("No drift", self.run_tool("sync_standards.py", checkout, "--check"))


if __name__ == "__main__":
    unittest.main()
