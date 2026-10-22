"""Consumer upgrades using disposable Git releases and mocked GitHub discovery."""
from __future__ import annotations

from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import update_standards as updater  # noqa: E402
from sync_standards import synchronize  # noqa: E402


def inventory(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


class UpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_temp = tempfile.TemporaryDirectory(prefix="standards-update-release-")
        cls.addClassCleanup(cls.source_temp.cleanup)
        cls.source = Path(cls.source_temp.name).resolve() / "release source"
        shutil.copytree(ROOT, cls.source, ignore=shutil.ignore_patterns(".git", "__pycache__", ".venv"))
        current = (ROOT / "VERSION").read_text().strip().split(".")
        cls.version = f"{current[0]}.{int(current[1]) + 1}.0"
        cls.tag = "v" + cls.version
        for name in ("VERSION", "templates/repository-bootstrap/.agent/VERSION"):
            (cls.source / name).write_text(cls.version + "\n", encoding="utf-8", newline="\n")
        for name in ("standards-manifest.yaml", "templates/repository-bootstrap/.agent/manifest.yaml"):
            path = cls.source / name
            value = json.loads(path.read_text())
            value["release"] = cls.version
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
        path = cls.source / "CHANGELOG.md"
        path.write_text(path.read_text().replace("## Unreleased", f"## Unreleased\n\n## {cls.version} - 2026-10-22", 1),
                        encoding="utf-8", newline="\n")
        with (cls.source / "standards/general.md").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("\nFixture release guidance.\n")
        updater.command(["git", "-C", str(cls.source), "init", "--quiet"])
        updater.command(["git", "-C", str(cls.source), "add", "."])
        updater.command(["git", "-C", str(cls.source), "-c", "user.name=Fixture", "-c",
                         "user.email=fixture@example.com", "-c", "commit.gpgsign=false", "-c",
                         "core.hooksPath=/dev/null", "commit", "--quiet", "-m", "Release fixture"])
        updater.command(["git", "-C", str(cls.source), "tag", cls.tag])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="standards-update-consumer-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.consumer = self.directory / "consumer with spaces"
        self.consumer.mkdir()
        shutil.copytree(ROOT / "templates/repository-bootstrap/.agent", self.consumer / ".agent")
        with redirect_stdout(io.StringIO()):
            synchronize(ROOT, self.consumer)
        for name in ("AGENTS.md", "CLAUDE.md", ".agent/local-notes.md", "plugins/example/plugin.json"):
            path = self.consumer / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("locally owned\n", encoding="utf-8")

    def update(self, **options):
        output = io.StringIO()
        with redirect_stdout(output):
            result = updater.update(self.consumer, **options)
        return result, output.getvalue()

    def edit_manifest(self, **changes):
        path = self.consumer / ".agent/manifest.yaml"
        manifest = json.loads(path.read_text())
        manifest.update(changes)
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def test_latest_release_preserves_selections_and_local_files(self):
        self.edit_manifest(standards=["python"], workflows=[], skills=[])
        with redirect_stdout(io.StringIO()):
            synchronize(ROOT, self.consumer)
        original = inventory(self.consumer)
        real_command = updater.command
        requests = []

        def fake_github(args):
            if args[0] == "gh":
                requests.append(args)
                return json.dumps({"tagName": self.tag, "isDraft": False, "isPrerelease": False,
                                   "publishedAt": "2026-10-22T12:00:00Z"})
            if args[0] == "git" and "clone" in args:
                args = [*args[:-2], str(self.source), args[-1]]
            return real_command(args)

        with patch.object(updater, "command", side_effect=fake_github):
            result, output = self.update()
        self.assertEqual(result, 0)
        self.assertIn("source commit", output)
        self.assertIn("repeated sync and drift check passed", output)
        self.assertEqual(len(requests), 1)
        manifest = json.loads((self.consumer / ".agent/manifest.yaml").read_text())
        self.assertEqual(manifest["release"], self.version)
        self.assertEqual(manifest["standards"], ["python"])
        self.assertEqual(manifest["workflows"], [])
        self.assertEqual(manifest["skills"], [])
        for name, value in original.items():
            if not name.startswith((".agent/standards/", ".agent/workflows/", ".agent/skills/")) and name not in (
                    ".agent/VERSION", ".agent/manifest.yaml", ".agent/sync-state.json"):
                self.assertEqual(inventory(self.consumer)[name], value)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(synchronize(self.source, self.consumer, check=True), 0)

    def test_offline_check_is_read_only_then_update_is_idempotent(self):
        before = inventory(self.consumer)
        result, output = self.update(source=self.source, check=True)
        self.assertEqual(result, 1)
        self.assertIn("consumer unchanged", output)
        self.assertEqual(inventory(self.consumer), before)
        self.update(source=self.source)
        after = inventory(self.consumer)
        self.update(source=self.source)
        self.assertEqual(self.update(source=self.source, check=True)[0], 0)
        self.assertEqual(inventory(self.consumer), after)

    def test_copied_standalone_command_runs_without_source_imports(self):
        script = self.consumer / "tools/update_standards.py"
        script.parent.mkdir()
        shutil.copyfile(ROOT / "tools/update_standards.py", script)
        result = subprocess.run([sys.executable, str(script), "--source", str(self.source)],
                                cwd=self.consumer, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.consumer / ".agent/VERSION").read_text().strip(), self.version)
        for entry in (ROOT / "update.py", script):
            help_result = subprocess.run([sys.executable, str(entry), "--help"],
                                         capture_output=True, text=True, timeout=30)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)

    def test_edited_or_missing_snapshot_blocks_before_network_or_writes(self):
        path = self.consumer / ".agent/standards/general.md"
        original = path.read_bytes()
        for action in (lambda: path.write_text("local edit", encoding="utf-8"), path.unlink):
            action()
            before = inventory(self.consumer)
            with patch.object(updater, "fetch_release") as fetch:
                with self.assertRaises(updater.UpdateError):
                    self.update()
                fetch.assert_not_called()
            self.assertEqual(inventory(self.consumer), before)
            path.write_bytes(original)

    def test_unknown_shared_files_and_malicious_state_paths_are_preserved(self):
        path = self.consumer / ".agent/standards/local.md"
        path.write_text("local", encoding="utf-8")
        before = inventory(self.consumer)
        with self.assertRaisesRegex(updater.UpdateError, "Untracked file"):
            self.update(source=self.source)
        self.assertEqual(inventory(self.consumer), before)
        path.unlink()
        state_path = self.consumer / ".agent/sync-state.json"
        state = json.loads(state_path.read_text())
        state["files"]["../AGENTS.md"] = "0" * 64
        state_path.write_text(json.dumps(state), encoding="utf-8")
        before = inventory(self.consumer)
        with self.assertRaisesRegex(updater.UpdateError, "Invalid tracked snapshot path"):
            self.update(source=self.source)
        self.assertEqual(inventory(self.consumer), before)

    def test_invalid_selection_or_scope_does_not_change_consumer(self):
        original = (self.consumer / ".agent/manifest.yaml").read_bytes()
        for changes in ({"standards": ["nonexistent"]}, {"synchronized": ["VERSION", "sync-state.json"]}):
            (self.consumer / ".agent/manifest.yaml").write_bytes(original)
            self.edit_manifest(**changes)
            before = inventory(self.consumer)
            with self.assertRaises(updater.UpdateError):
                self.update(source=self.source)
            self.assertEqual(inventory(self.consumer), before)

    def test_source_validation_failure_preserves_manifest_and_snapshot(self):
        before = inventory(self.consumer)
        real_command = updater.command

        def invalid_source(args):
            if any(arg.endswith("validate_repository.py") for arg in args):
                raise updater.UpdateError("Source validation failed")
            return real_command(args)

        with patch.object(updater, "command", side_effect=invalid_source):
            with self.assertRaisesRegex(updater.UpdateError, "validation failed"):
                self.update(source=self.source)
        self.assertEqual(inventory(self.consumer), before)

    def test_handled_write_failure_restores_original_files(self):
        before = inventory(self.consumer)
        real_write = updater.atomic_write
        count = 0

        def interrupted(path, data):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("Simulated write failure")
            real_write(path, data)

        with patch.object(updater, "atomic_write", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "Simulated write failure"):
                self.update(source=self.source)
        self.assertEqual({name: value[0] for name, value in inventory(self.consumer).items()},
                         {name: value[0] for name, value in before.items()})

    def test_draft_prerelease_and_unpublished_releases_are_rejected(self):
        for change in ({"isDraft": True}, {"isPrerelease": True}, {"publishedAt": None}, {"tagName": "--evil"}):
            release = {"tagName": self.tag, "isDraft": False, "isPrerelease": False,
                       "publishedAt": "2026-10-22T12:00:00Z", **change}
            before = inventory(self.consumer)
            with patch.object(updater, "command", return_value=json.dumps(release)):
                with self.assertRaises(updater.UpdateError):
                    self.update()
            self.assertEqual(inventory(self.consumer), before)

    def test_source_repository_is_not_a_consumer_and_bad_repository_is_rejected(self):
        with self.assertRaisesRegex(updater.UpdateError, "source as a consumer"):
            updater.update(ROOT)
        for repository in ("../escape", "--evil/repository", "https://example.com/repo"):
            with patch.object(updater, "command") as command:
                with self.assertRaisesRegex(updater.UpdateError, "OWNER/REPO"):
                    self.update(repository=repository)
                command.assert_not_called()

    def test_missing_cli_and_bad_json_have_clear_errors(self):
        with patch.object(updater.subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(updater.UpdateError, "gh auth login"):
                self.update()
        with self.assertRaisesRegex(updater.UpdateError, "Duplicate JSON key"):
            updater.read_json(b'{"release":"0.1.0","release":"0.2.0"}')

    def test_snapshot_directory_links_are_rejected(self):
        outside = self.directory / "outside"
        outside.mkdir()
        link = self.consumer / ".agent/skills/linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            env = dict(os.environ, UPDATE_TEST_LINK=str(link), UPDATE_TEST_TARGET=str(outside))
            result = subprocess.run(["powershell", "-NoProfile", "-Command",
                                     "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                                     "-Path $env:UPDATE_TEST_LINK -Target $env:UPDATE_TEST_TARGET | Out-Null"],
                                    env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.assertRaisesRegex(updater.UpdateError, "symbolic link or reparse point"):
            self.update(source=self.source)
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
