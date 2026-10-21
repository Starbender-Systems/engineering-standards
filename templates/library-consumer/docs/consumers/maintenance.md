# Maintain consumer tooling

The library owns this catalog, its plugin, and `tools/consumer_tooling.py`. The tool is copied at bootstrap and is not updated by engineering-standards snapshot synchronization. Review later tooling/template changes explicitly.

Update affected capability routes, package versions, and recipes when reusable behavior changes. Increment the consumer plugin's version in its `plugin.json` when bundled guidance changes. It is independent of the library release and engineering-standards versions. Run from the library repository root with Python 3.11+:

```text
python tools/consumer_tooling.py validate .
python tools/consumer_tooling.py bundle . --output ../consumer-tooling-preview --allow-dirty-preview
```

Extract the ZIP into an unrelated directory and inspect the skill and links there. The archive contains `.agents/plugins/marketplace.json` and `plugins/{{plugin_name}}/` with all consumer references. It needs no original library checkout. Local marketplace discovery follows the host's plugin installation instructions; generating an archive does not install or enable it.

Before a release bundle, fill the catalog with real packages and capabilities, set `library.ref` to the intended tag or commit, and commit the tooling and guidance. Bundle from a clean Git checkout at that ref into a new directory outside the source repository:

```text
python tools/consumer_tooling.py bundle . --output ../consumer-tooling-release
```

Output includes a deterministic marketplace ZIP, `provenance.json`, and `SHA256SUMS`. Provenance records the actual source commit and resolved library ref, declared package versions, and bundled file hashes. Preview output is marked in its filename and metadata. The generic tool does not publish Git refs, upload releases, or modify user plugin configuration. Define those operations through the library's existing release process when needed.

The optional `--inventory path/to/inventory.json` argument to either command verifies package IDs/versions and capability symbols against a language-specific adapter's inventory and includes that inventory when bundling. See the engineering-standards library tooling guide for its schema. Inventory generation, API diffs, recipe compilation, and downstream runtime acceptance are library-specific extensions; do not describe those checks as passing until implemented and run.

Recover by reverting the library-owned tooling/guidance together and rebuilding from the recorded revision. Never replace a published immutable plugin version with different bytes.
