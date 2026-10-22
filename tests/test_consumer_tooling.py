"""Library bootstrap, validation, relocation, and packaging against disposable libraries."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from bootstrap_library import render_profile  # noqa: E402
from consumer_tooling import (  # noqa: E402
    CATALOG, MARKETPLACE, ToolingError, check_links, json_bytes, source_files, validate_files,
)


def inventory(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): (p.read_bytes(), p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts}


class ConsumerToolingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="library-consumer-test-")
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.library = self.directory / "library"
        self.library.mkdir()
        self.args = [self.library, "--name", "example", "--display-name", "Example Library",
                     "--repository", "https://example.com/team/library", "--library-ref", "HEAD"]

    def tool(self, script, *args, code=0):
        result = subprocess.run([sys.executable, str(ROOT / "tools" / script), *map(str, args)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def bootstrap(self, *args, code=0):
        return self.tool("bootstrap_library.py", *self.args, *args, code=code)

    def run_consumer(self, command="validate", *args, code=0):
        # Execute the copied standalone runtime: it must not rely on this source checkout.
        result = subprocess.run([sys.executable, str(self.library / "tools/consumer_tooling.py"),
                                 command, str(self.library), *map(str, args)],
                                cwd=self.directory, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def edit_catalog(self, **changes):
        path = self.library / CATALOG
        value = json.loads(path.read_bytes())
        value.update(changes)
        path.write_bytes(json_bytes(value))

    def populate(self):
        self.edit_catalog(packages=[{"id": "Example.Core", "version": "1.2.3"}], capabilities=[{
            "id": "lookup", "packages": ["Example.Core"], "search_terms": ["lookup", "find"],
            "symbols": ["T:Example.Lookup"], "page": "recipes/lookup.md",
        }])
        (self.library / "docs/consumers/recipes/lookup.md").write_text(
            "# Lookup\n\nUse the lookup service. See [packages](../packages.md).\n", encoding="utf-8")

    def git(self, *args):
        result = subprocess.run(["git", "-C", str(self.library), *args], capture_output=True,
                                text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self):
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.com",
                 "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
                 "commit", "--quiet", "-m", "Fixture")
        return self.git("rev-parse", "HEAD")

    def api_inventory(self, **changes):
        value = {"schema_version": 1, "packages": [{
            "id": "Example.Core", "version": "1.2.3", "symbols": ["T:Example.Lookup"],
        }]}
        value.update(changes)
        path = self.directory / "api-inventory.json"
        path.write_bytes(json_bytes(value))
        return path

    def directory_link(self, link: Path, target: Path):
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                raise
            # Junctions exercise the same boundary on Windows without symlink privileges.
            env = dict(os.environ, LIBRARY_TEST_LINK=str(link), LIBRARY_TEST_TARGET=str(target))
            result = subprocess.run(["powershell", "-NoProfile", "-Command",
                                     "$ErrorActionPreference='Stop'; New-Item -ItemType Junction "
                                     "-Path $env:LIBRARY_TEST_LINK -Target $env:LIBRARY_TEST_TARGET | Out-Null"],
                                    env=env, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_bootstrap_preserves_application_and_shared_snapshot_files(self):
        for name in ("AGENTS.md", "CLAUDE.md", "README.md", "DEVELOPING.md", ".github/existing.yml",
                     ".agent/manifest.yaml", ".agent/standards/general.md", "src/app.cs"):
            path = self.library / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("local work\n", encoding="utf-8")
        before = inventory(self.library)
        self.bootstrap()
        for name, data in before.items():
            self.assertEqual(inventory(self.library)[name], data)
        self.assertIn("Starter catalog", self.run_consumer())
        self.assertEqual((self.library / "tools/consumer_tooling.py").read_bytes(),
                         (ROOT / "tools/consumer_tooling.py").read_bytes())

    def test_check_is_read_only_and_reruns_preserve_timestamps(self):
        before = inventory(self.library)
        self.assertIn("files missing", self.bootstrap("--check", code=1))
        self.assertEqual(inventory(self.library), before)
        self.bootstrap()
        before = inventory(self.library)
        self.assertIn("0 file(s)", self.bootstrap())
        self.assertIn("no changes", self.bootstrap("--check"))
        self.assertEqual(inventory(self.library), before)

    def test_conflict_preflight_preserves_every_file(self):
        for conflict in (MARKETPLACE, "tools/consumer_tooling.py", "docs/consumers/index.md"):
            with self.subTest(conflict=conflict):
                target = self.library / conflict
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("existing local file\n", encoding="utf-8")
                before = inventory(self.library)
                self.assertIn("Refusing to overwrite", self.bootstrap(code=2))
                self.assertEqual(inventory(self.library), before)
                target.unlink()

    def test_parent_file_blocks_entire_bootstrap(self):
        (self.library / "plugins").write_text("local", encoding="utf-8")
        self.assertIn("ERROR:", self.bootstrap(code=2))
        self.assertEqual(set(inventory(self.library)), {"plugins"})

    def test_names_and_versions_are_checked_without_writes(self):
        for option, value in (("--name", "../escape"), ("--name", "a" * 60), ("--name", "CON"),
                              ("--display-name", "line\nbreak"), ("--repository", "file:///tmp/x"),
                              ("--repository", "https://user:secret@example.com/x"),
                              ("--plugin-version", "invalid"), ("--plugin-version", "1.0.0-01")):
            with self.subTest(option=option, value=value):
                args = self.args.copy()
                if option in args:
                    args[args.index(option) + 1] = value
                else:
                    args += [option, value]
                self.tool("bootstrap_library.py", *args, code=2)
                self.assertEqual(inventory(self.library), {})

    def test_display_name_is_safely_quoted_in_json_and_skill_yaml(self):
        args = self.args.copy()
        args[args.index("--display-name") + 1] = 'Example: "Quoted" Library'
        self.tool("bootstrap_library.py", *args)
        self.assertIn("valid:", self.run_consumer())
        data = json.loads((self.library / CATALOG).read_bytes())
        self.assertEqual(data["library"]["name"], 'Example: "Quoted" Library')
        skill = (self.library / "plugins/example-consumer/skills/example-consumer/SKILL.md").read_text()
        self.assertIn('description: "Discover', skill)

    def test_source_overlap_is_rejected(self):
        args = self.args.copy()
        args[0] = ROOT
        self.assertIn("must not overlap", self.tool("bootstrap_library.py", *args, code=2))

    def test_bootstrap_validation_and_bundle_support_roots_with_spaces(self):
        self.library = self.directory / "library with spaces"
        self.library.mkdir()
        self.args[0] = self.library
        self.bootstrap()
        self.populate()
        self.commit()
        self.run_consumer()
        output = self.directory / "distribution with spaces"
        self.run_consumer("bundle", "--output", output)
        self.assertTrue(next(output.glob("*.zip")).is_file())

    def test_malformed_catalogs_fail_cleanly(self):
        self.bootstrap()
        path = self.library / CATALOG
        original = path.read_bytes()
        for data in (b"[]", b"{}", b'{"plugin":"a","plugin":"b"}', b'not JSON'):
            with self.subTest(data=data):
                path.write_bytes(data)
                self.assertIn("ERROR:", self.run_consumer(code=2))
                path.write_bytes(original)

    def test_unknown_packages_duplicate_capabilities_and_traversal_are_rejected(self):
        self.bootstrap()
        self.populate()
        original = json.loads((self.library / CATALOG).read_bytes())
        for key, value, message in (("packages", ["Absent"], "unknown or missing package"),
                                     ("page", "../../outside.md", "Unsafe relative path"),
                                     ("page", "missing.md", "missing capability page")):
            with self.subTest(key=key):
                capability = dict(original["capabilities"][0], **{key: value})
                self.edit_catalog(capabilities=[capability])
                self.assertIn(message, self.run_consumer(code=2))
        self.edit_catalog(capabilities=original["capabilities"] * 2)
        self.assertIn("Duplicate capability", self.run_consumer(code=2))

    def test_packaged_links_are_checked_instead_of_source_only_links(self):
        self.bootstrap()
        page = self.library / "docs/consumers/index.md"
        for link, message in (("[outside](../../README.md)", "nonportable local link"),
                               ("[missing](packages.md#absent)", "missing anchor")):
            page.write_text(link + "\n", encoding="utf-8")
            self.assertIn(message, self.run_consumer(code=2))

    def test_bundle_reference_overwrites_and_case_collisions_are_rejected(self):
        self.bootstrap()
        files = source_files(self.library)
        files["plugins/example-consumer/skills/example-consumer/references/index.md"] = b"local"
        with self.assertRaisesRegex(ToolingError, "overwrite plugin file"):
            validate_files(files)
        del files["plugins/example-consumer/skills/example-consumer/references/index.md"]
        files["plugins/example-consumer/PLUGIN.JSON"] = b"{}"
        with self.assertRaisesRegex(ToolingError, "Case-insensitive"):
            validate_files(files)
        del files["plugins/example-consumer/PLUGIN.JSON"]
        files["docs/consumers/provenance.json"] = b"{}"
        with self.assertRaisesRegex(ToolingError, "generated by the bundler"):
            validate_files(files)

    def test_inventory_verifies_versions_and_symbols(self):
        self.bootstrap()
        self.populate()
        path = self.api_inventory()
        self.run_consumer("validate", "--inventory", path)
        for package, expected in (({"id": "Other", "version": "1.2.3", "symbols": []}, "IDs and versions"),
                                   ({"id": "Example.Core", "version": "2.0.0", "symbols": []}, "IDs and versions"),
                                   ({"id": "Example.Core", "version": "1.2.3", "symbols": []}, "unknown inventory symbol")):
            path = self.api_inventory(packages=[package])
            self.assertIn(expected, self.run_consumer("validate", "--inventory", path, code=2))

    def test_release_bundle_is_deterministic_relocatable_and_checksummed(self):
        self.bootstrap()
        self.populate()
        commit = self.commit()
        before = inventory(self.library)
        outputs = [self.directory / "first", self.directory / "second"]
        api = self.api_inventory()
        for output in outputs:
            self.run_consumer("bundle", "--output", output, "--inventory", api)
        self.assertEqual({p: data[0] for p, data in inventory(outputs[0]).items()},
                         {p: data[0] for p, data in inventory(outputs[1]).items()})
        self.assertEqual(inventory(self.library), before)
        result = outputs[0]
        for line in (result / "SHA256SUMS").read_text().splitlines():
            sha, name = line.split("  ")
            self.assertEqual(hashlib.sha256((result / name).read_bytes()).hexdigest(), sha)
        provenance = json.loads((result / "provenance.json").read_bytes())
        self.assertEqual(provenance["source_commit"], commit)
        self.assertEqual(provenance["library_commit"], commit)
        self.assertFalse(provenance["preview"])
        self.assertTrue(provenance["api_inventory_included"])
        with zipfile.ZipFile(next(result.glob("*.zip"))) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
            check_links(files)
            prefix = "plugins/example-consumer/skills/example-consumer/references/"
            self.assertIn(prefix + "api/inventory.json", files)
            self.assertEqual(files[prefix + "provenance.json"], (result / "provenance.json").read_bytes())
            for name, sha in provenance["files"].items():
                self.assertEqual(hashlib.sha256(files[name]).hexdigest(), sha)
            unrelated = self.directory / "unrelated/extracted"
            archive.extractall(unrelated)
        self.library.rename(self.directory / "unavailable-authoring-checkout")
        check_links({p.relative_to(unrelated).as_posix(): p.read_bytes()
                     for p in unrelated.rglob("*") if p.is_file()})

    def test_empty_starter_cannot_be_a_release_but_can_be_a_preview(self):
        self.bootstrap()
        self.commit()
        output = self.directory / "release"
        self.assertIn("Add packages and capabilities", self.run_consumer("bundle", "--output", output, code=2))
        self.assertFalse(output.exists())
        self.run_consumer("bundle", "--output", output, "--allow-dirty-preview")
        self.assertTrue(next(output.glob("*-preview.zip")).is_file())
        self.assertTrue(json.loads((output / "provenance.json").read_bytes())["preview"])

    def test_agent_bundles_share_guidance_and_have_native_metadata(self):
        self.bootstrap()
        self.populate()
        self.commit()
        before = inventory(self.library)
        api = self.api_inventory()
        common = None
        for agent in ("codex", "claude", "copilot", "all"):
            with self.subTest(agent=agent):
                archives = []
                for attempt in range(2):
                    output = self.directory / f"{agent}-{attempt}"
                    self.run_consumer("bundle", "--agent", agent, "--output", output, "--inventory", api)
                    archive = next(output.glob("*.zip"))
                    suffix = "" if agent == "codex" else f"-{agent}"
                    self.assertEqual(archive.name, f"example-consumer-0.1.0{suffix}.zip")
                    archives.append(archive.read_bytes())
                    with zipfile.ZipFile(archive) as zipped:
                        files = {p: zipped.read(p) for p in zipped.namelist()}
                    check_links(files)
                    provenance = json.loads((output / "provenance.json").read_bytes())
                    expected_agents = ["codex", "claude", "copilot"] if agent == "all" else [agent]
                    self.assertEqual(provenance["agents"], expected_agents)
                    prefix = "plugins/example-consumer/"
                    references = prefix + "skills/example-consumer/references/"
                    self.assertEqual(files[references + "provenance.json"],
                                     (output / "provenance.json").read_bytes())
                    for path, sha in provenance["files"].items():
                        self.assertEqual(hashlib.sha256(files[path]).hexdigest(), sha)
                    guidance = {p: data for p, data in files.items()
                                if "/skills/" in p and not p.endswith("/provenance.json")}
                    if common is None:
                        common = guidance
                    self.assertEqual(guidance, common)
                    self.assertIn(references + "api/inventory.json", files)
                    for host, marketplace_path in (
                            ("codex", MARKETPLACE), ("claude", ".claude-plugin/marketplace.json"),
                            ("copilot", ".github/plugin/marketplace.json")):
                        self.assertEqual(marketplace_path in files, host in expected_agents)
                        if host in expected_agents and host != "codex":
                            marketplace = json.loads(files[marketplace_path])
                            self.assertEqual(marketplace["name"], "example-tooling")
                            self.assertEqual(marketplace["owner"], {"name": "Example Library"})
                            self.assertEqual(marketplace["plugins"][0]["source"], "./plugins/example-consumer")
                    self.assertEqual(prefix + "plugin.json" in files, agent != "claude")
                    self.assertEqual(prefix + ".claude-plugin/plugin.json" in files,
                                     agent in ("claude", "all"))
                    if agent in ("claude", "all"):
                        manifest = json.loads(files[prefix + ".claude-plugin/plugin.json"])
                        self.assertEqual(manifest, {
                            "name": "example-consumer", "version": "0.1.0",
                            "description": "Discover and integrate Example Library capabilities in consuming applications.",
                            "repository": "https://example.com/team/library",
                            "author": {"name": "Example Library"},
                        })
                    extracted = self.directory / f"extracted-{agent}-{attempt}"
                    with zipfile.ZipFile(archive) as zipped:
                        zipped.extractall(extracted)
                    check_links({p.relative_to(extracted).as_posix(): p.read_bytes()
                                 for p in extracted.rglob("*") if p.is_file()})
                self.assertEqual(archives[0], archives[1])
        self.assertEqual(inventory(self.library), before)

    def test_native_adapter_collisions_are_rejected_before_output(self):
        self.bootstrap()
        self.populate()
        path = self.library / "plugins/example-consumer/.claude-plugin/plugin.json"
        path.parent.mkdir()
        path.write_text("{}", encoding="utf-8")
        for agent in ("codex", "claude", "copilot", "all"):
            with self.subTest(agent=agent):
                output = self.directory / agent
                self.assertIn("Generated agent adapter would overwrite", self.run_consumer(
                    "bundle", "--agent", agent, "--output", output, "--allow-dirty-preview", code=2))
                self.assertFalse(output.exists())

    def test_preview_and_release_guards_apply_to_each_new_agent(self):
        self.bootstrap()
        self.commit()
        for agent in ("claude", "copilot", "all"):
            with self.subTest(agent=agent):
                output = self.directory / agent
                self.assertIn("Add packages and capabilities", self.run_consumer(
                    "bundle", "--agent", agent, "--output", output, code=2))
                self.assertFalse(output.exists())
                self.run_consumer("bundle", "--agent", agent, "--output", output, "--allow-dirty-preview")
                self.assertTrue(next(output.glob(f"*-{agent}-preview.zip")).is_file())
                self.assertTrue(json.loads((output / "provenance.json").read_bytes())["preview"])

    def test_target_specific_broken_links_fail_before_output(self):
        self.bootstrap()
        page = self.library / "docs/consumers/index.md"
        page.write_text("[root manifest](../../../plugin.json)\n", encoding="utf-8")
        # The link exists in the combined layout, but Claude uses its native manifest instead.
        self.run_consumer()
        self.commit()
        output = self.directory / "claude"
        self.assertIn("nonportable local link", self.run_consumer(
            "bundle", "--agent", "claude", "--output", output, "--allow-dirty-preview", code=2))
        self.assertFalse(output.exists())

    def test_dirty_or_wrong_ref_release_fails_before_output_creation(self):
        self.bootstrap()
        self.populate()
        self.commit()
        output = self.directory / "release"
        (self.library / "local.txt").write_text("uncommitted", encoding="utf-8")
        self.assertIn("clean source", self.run_consumer("bundle", "--output", output, code=2))
        self.assertFalse(output.exists())
        catalog = json.loads((self.library / CATALOG).read_bytes())
        catalog["library"]["ref"] = "missing-tag"
        self.edit_catalog(library=catalog["library"])
        self.assertIn("does not resolve", self.run_consumer("bundle", "--output", output, code=2))
        self.assertFalse(output.exists())
        self.run_consumer("bundle", "--output", output, "--allow-dirty-preview")
        provenance = json.loads((output / "provenance.json").read_bytes())
        self.assertIsNone(provenance["library_commit"])
        self.assertTrue(provenance["source_dirty"])

    def test_existing_and_overlapping_outputs_are_preserved(self):
        self.bootstrap()
        self.populate()
        self.commit()
        inside = self.library / "artifacts/bundle"
        self.assertIn("must not overlap", self.run_consumer("bundle", "--output", inside, code=2))
        self.assertFalse(inside.exists())
        output = self.directory / "existing"
        output.mkdir()
        (output / "keep.txt").write_text("local", encoding="utf-8")
        self.assertIn("new directory", self.run_consumer("bundle", "--output", output, code=2))
        self.assertEqual((output / "keep.txt").read_text(), "local")

    def test_ignored_inputs_are_not_misrepresented_as_committed_release_content(self):
        self.bootstrap()
        self.populate()
        (self.library / ".gitignore").write_text("docs/consumers/ignored.md\n", encoding="utf-8")
        self.commit()
        (self.library / "docs/consumers/ignored.md").write_text("# Ignored input\n", encoding="utf-8")
        self.assertEqual(self.git("status", "--porcelain"), "")
        output = self.directory / "ignored-release"
        self.assertIn("must be tracked", self.run_consumer("bundle", "--output", output, code=2))
        self.assertFalse(output.exists())
        self.run_consumer("bundle", "--output", output, "--allow-dirty-preview")
        provenance = json.loads((output / "provenance.json").read_bytes())
        self.assertEqual(provenance["untracked_inputs"], ["docs/consumers/ignored.md"])

    def test_unrelated_marketplace_entries_are_not_distributed(self):
        self.bootstrap()
        path = self.library / MARKETPLACE
        marketplace = json.loads(path.read_bytes())
        marketplace["plugins"].append({"name": "other-plugin", "source": {"source": "local", "path": "./other"}})
        path.write_bytes(json_bytes(marketplace))
        self.populate()
        self.commit()
        output = self.directory / "release"
        self.run_consumer("bundle", "--output", output)
        with zipfile.ZipFile(next(output.glob("*.zip"))) as archive:
            packaged = json.loads(archive.read(MARKETPLACE))
            self.assertEqual([p["name"] for p in packaged["plugins"]], ["example-consumer"])
        self.assertEqual(len(json.loads(path.read_bytes())["plugins"]), 2)

    def test_destination_links_are_rejected(self):
        outside = self.directory / "outside"
        outside.mkdir()
        link = self.library / "plugins"
        self.directory_link(link, outside)
        self.assertIn("symbolic link or reparse point", self.bootstrap(code=2))
        self.assertEqual(list(outside.iterdir()), [])

    def test_source_links_are_rejected_before_packaging(self):
        self.bootstrap()
        outside = self.directory / "outside"
        outside.mkdir()
        self.directory_link(self.library / "docs/consumers/linked", outside)
        self.assertIn("symbolic link or reparse point", self.run_consumer(code=2))

    def test_template_rendering_and_cli_help(self):
        files = render_profile(ROOT, "example", "Example Library", "https://example.com/library", "HEAD")
        catalog, _ = validate_files(files)
        self.assertEqual(catalog["plugin"], "example-consumer")
        for script in ("bootstrap_library.py", "consumer_tooling.py"):
            self.assertIn("usage:", self.tool(script, "--help"))


if __name__ == "__main__":
    unittest.main()
