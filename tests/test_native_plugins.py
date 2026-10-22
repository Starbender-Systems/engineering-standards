"""Opt-in CLI acceptance checks; no model calls or normal user configuration changes."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from bootstrap_library import render_profile  # noqa: E402

ENABLED = os.environ.get("ENGINEERING_NATIVE_PLUGIN_TESTS") == "1"
PLUGIN = "native-smoke-consumer"
MARKETPLACE = "native-smoke-tooling"


@unittest.skipUnless(ENABLED, "Set ENGINEERING_NATIVE_PLUGIN_TESTS=1 to run installed CLI checks")
class NativePluginTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="engineering-native-plugins-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.source = self.directory / "library with spaces"
        self.source.mkdir()
        for name, data in render_profile(ROOT, "native-smoke", "Native Smoke Fixture",
                                         "https://example.com/fixture", "HEAD").items():
            path = self.source / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.environment = dict(
            os.environ,
            CLAUDE_CONFIG_DIR=str(self.directory / "claude-config"),
            COPILOT_HOME=str(self.directory / "copilot-config"),
            COPILOT_CACHE_HOME=str(self.directory / "copilot-cache"),
            COPILOT_AUTO_UPDATE="false",
            DISABLE_AUTOUPDATER="1",
        )
        self.run_command("git", "init", "--quiet", str(self.source))
        self.run_command("git", "-C", str(self.source), "-c", "user.name=Fixture",
                         "-c", "user.email=fixture@example.com", "-c", "commit.gpgsign=false",
                         "-c", "core.hooksPath=/dev/null", "commit", "--quiet", "--allow-empty",
                         "-m", "Native plugin fixture")

    def run_command(self, executable, *arguments):
        binary = shutil.which(executable)
        self.assertIsNotNone(binary, f"Required native test executable not on PATH: {executable}")
        result = subprocess.run(
            [binary, *arguments], cwd=self.directory, env=self.environment,
            stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=60,
        )
        self.assertEqual(result.returncode, 0,
                         f"{executable} {' '.join(arguments)}\n{result.stdout}\n{result.stderr}")
        return result.stdout

    def extract_bundle(self, agent):
        output = self.directory / "bundle"
        self.run_command(sys.executable, str(self.source / "tools/consumer_tooling.py"),
                         "bundle", str(self.source), "--agent", agent, "--output", str(output),
                         "--allow-dirty-preview")
        extracted = self.directory / "extracted with spaces"
        with zipfile.ZipFile(next(output.glob("*.zip"))) as archive:
            archive.extractall(extracted)
        # Native discovery must use only the extracted distribution.
        self.source.rename(self.directory / "unavailable-authoring-checkout")
        return extracted

    def check_claude(self, agent):
        extracted = self.extract_bundle(agent)
        plugin = extracted / "plugins" / PLUGIN
        for target in (plugin, extracted):
            report = json.loads(self.run_command("claude", "plugin", "validate", str(target),
                                                 "--strict", "--json"))
            self.assertTrue(report["success"], report)
            self.assertEqual(report["manifest"]["errors"], [])
            self.assertEqual(report["manifest"]["warnings"], [])
        self.run_command("claude", "plugin", "marketplace", "add", str(extracted), "--json")
        identity = f"{PLUGIN}@{MARKETPLACE}"
        self.run_command("claude", "plugin", "install", identity, "--json")
        plugins = json.loads(self.run_command("claude", "plugin", "list", "--json"))
        installed = next(p for p in plugins if p["id"] == identity)
        self.assertTrue(installed["enabled"])
        self.assertEqual(installed["version"], "0.1.0")
        details = self.run_command("claude", "plugin", "details", identity)
        self.assertIn(f"Skills (1)  {PLUGIN}", details)
        self.assertTrue((plugin / "skills" / PLUGIN / "references/catalog.json").is_file())
        self.run_command("claude", "plugin", "uninstall", identity)
        plugins = json.loads(self.run_command("claude", "plugin", "list", "--json"))
        self.assertFalse(any(p["id"] == identity for p in plugins))

    def check_copilot(self, agent):
        extracted = self.extract_bundle(agent)
        self.run_command("copilot", "plugin", "marketplace", "add", str(extracted))
        identity = f"{PLUGIN}@{MARKETPLACE}"
        self.run_command("copilot", "plugin", "install", identity)
        plugins = json.loads(self.run_command("copilot", "plugin", "list", "--json"))
        installed = next(p for p in plugins if p["name"] == PLUGIN and p["marketplace"] == MARKETPLACE)
        self.assertTrue(installed["enabled"])
        self.assertEqual(installed["version"], "0.1.0")
        skills = json.loads(self.run_command("copilot", "skill", "list", "--json"))
        skill = next(s for s in skills if s["name"] == PLUGIN and s["source"] == "plugin")
        self.assertTrue(skill["enabled"])
        path = Path(skill["path"])
        self.assertTrue(path.resolve().is_relative_to(self.directory))
        self.assertEqual((path / "SKILL.md").read_bytes(),
                         (extracted / "plugins" / PLUGIN / "skills" / PLUGIN / "SKILL.md").read_bytes())
        self.assertTrue((path / "references/catalog.json").is_file())
        self.run_command("copilot", "plugin", "uninstall", identity)
        plugins = json.loads(self.run_command("copilot", "plugin", "list", "--json"))
        # Local marketplace plugins are live directories: uninstall disables them,
        # preserving the caller-owned files and the discoverable marketplace entry.
        self.assertFalse(any(p["name"] == PLUGIN and p["enabled"] for p in plugins))
        skills = json.loads(self.run_command("copilot", "skill", "list", "--json"))
        self.assertFalse(any(s["name"] == PLUGIN and s["enabled"] for s in skills))
        self.assertTrue((path / "SKILL.md").is_file())

    def test_claude_bundle(self):
        self.check_claude("claude")

    def test_claude_combined_bundle(self):
        self.check_claude("all")

    def test_copilot_bundle(self):
        self.check_copilot("copilot")

    def test_copilot_combined_bundle(self):
        self.check_copilot("all")


if __name__ == "__main__":
    unittest.main()
