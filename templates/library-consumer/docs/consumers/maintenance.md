# Maintain consumer tooling

The library owns this catalog, its plugin, and `tools/consumer_tooling.py`. The tool is copied at bootstrap and is not updated by engineering-standards snapshot synchronization. Review later tooling/template changes explicitly.

Update affected capability routes, package versions, and recipes when reusable behavior changes. Increment the consumer plugin's version in its `plugin.json` when bundled guidance changes. It is independent of the library release and engineering-standards versions. Run from the library repository root with Python 3.11+:

```text
python tools/consumer_tooling.py validate .
python tools/consumer_tooling.py bundle . --agent all --output ../consumer-tooling-preview --allow-dirty-preview
```

Choose `--agent codex`, `--agent claude` (Claude Code), `--agent copilot` (GitHub Copilot), or `--agent all` (one combined archive). Omitting the flag preserves the Codex default. Every target uses the same skill, catalog, recipes, and optional inventory. Maintain the root `plugin.json` as the metadata source; the bundler generates native adapters without changing the authoring files.

Extract the ZIP into an unrelated directory and inspect the skill and links there. All targets include `plugins/{{plugin_name}}/` with consumer references. Codex adds `.agents/plugins/marketplace.json`; Claude adds `.claude-plugin/marketplace.json` and a `.claude-plugin/plugin.json` inside the plugin; Copilot adds `.github/plugin/marketplace.json` and uses the root plugin manifest. The combined archive includes all adapters. Generated native marketplaces use the catalog's library name as their owner name, and Claude uses it as the plugin author name; review that attribution before distribution. Keep the generated paths out of the authoring plugin tree to avoid collisions. It needs no original library checkout. Local marketplace discovery follows the host's plugin installation instructions; generating an archive does not install or enable it. Copilot local marketplace installs load the extracted plugin live, so retain that directory while the plugin is installed.

Before a release bundle, fill the catalog with real packages and capabilities, set `library.ref` to the intended tag or commit, and commit the tooling and guidance. Bundle from a clean Git checkout at that ref into a new directory outside the source repository:

```text
python tools/consumer_tooling.py bundle . --agent all --output ../consumer-tooling-release
```

Output includes a deterministic marketplace ZIP, `provenance.json`, and `SHA256SUMS`. Provenance records the selected agents, actual source commit and resolved library ref, declared package versions, and bundled file hashes including generated adapters. Claude, Copilot, and combined archives add `-claude`, `-copilot`, or `-all` before the optional `-preview` suffix; Codex keeps its original archive name. The generic tool does not publish Git refs, upload releases, or modify user plugin configuration. Define those operations through the library's existing release process when needed.

The optional `--inventory path/to/inventory.json` argument to either command verifies package IDs/versions and capability symbols against a language-specific adapter's inventory and includes that inventory when bundling. See the engineering-standards library tooling guide for its schema. Inventory generation, API diffs, recipe compilation, and downstream runtime acceptance are library-specific extensions; do not describe those checks as passing until implemented and run.

Recover by reverting the library-owned tooling/guidance together and rebuilding from the recorded revision. Never replace a published immutable plugin version with different bytes.
