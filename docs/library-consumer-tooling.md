# Library consumer tooling bootstrap

Libraries can optionally bootstrap a consumer plugin alongside their engineering-standards snapshot. The reusable parts are a task-oriented catalog, package/version discovery guidance, integration recipes, portable skill/plugin metadata, validation, and reproducible local packaging. Domain-specific APIs, build commands, owners, and release permissions remain with the library.

The design follows the separation used by the SharedPackages consumer tooling: curated discovery and integration decisions, optional generated API evidence, and a portable bundle. This implementation is independent, uses Python 3.11+ and its standard library, and needs no SharedPackages checkout, .NET SDK, or published package to bootstrap. Git is additionally needed for bundle provenance.

## Bootstrap a new library

First adopt the ordinary [repository bootstrap](../templates/repository-bootstrap/README.md), selecting the standards relevant to the library. Then run from this standards checkout, substituting the library's real identity:

```text
python tools/bootstrap_library.py ../example-library --name example-library --display-name "Example Library" --repository https://github.com/example/example-library --library-ref HEAD --check
python tools/bootstrap_library.py ../example-library --name example-library --display-name "Example Library" --repository https://github.com/example/example-library --library-ref HEAD
python ../example-library/tools/consumer_tooling.py validate ../example-library
```

`HEAD` is a useful initial ref for a new library; use the intended library tag or commit when preparing its consumer plugin release. `--plugin-version` defaults to `0.1.0` and is independent of library package versions and the standards release. `--name` is a lowercase hyphenated slug; the generated plugin and skill are named `<name>-consumer` (maximum 64 characters).

The command adds locally owned files:

```text
library/
  .agents/plugins/marketplace.json
  .github/workflows/consumer-tooling.yml
  docs/consumers/
    catalog.json
    index.md
    adoption.md
    packages.md
    maintenance.md
    recipes/README.md
  plugins/<name>-consumer/
    plugin.json
    skills/<name>-consumer/SKILL.md
  tools/consumer_tooling.py
```

It does not change the shared `.agent/` snapshot, existing agent adapters, application code, root README, Git configuration, or user plugin installations. Add links to the library-owned consumer guide from its AGENTS/DEVELOPING/README files as appropriate. Review the generated CI workflow alongside the library's existing checks.

All planned writes are checked before any files are created. Identical reruns preserve bytes and modification times. Conflicting locally owned files, symlinks/reparse points, unsafe paths, and overlapping source/target repositories are rejected. If a marketplace or workflow already exists, render into a disposable sibling directory and merge the relevant entries manually. The tool deliberately does not overwrite or silently reconcile custom instructions. File creation is exclusive but the whole run is not transactional; after interruption, rerun with the same arguments and resolve any conflicts reported.

Exit codes: **0** success/no missing files, **1** missing bootstrap files in `--check`, **2** invalid input, conflict, or filesystem error. `--check` is read-only. After customization, use the consumer tool's `validate` command for ongoing checks; bootstrap's `--check` compares against the original scaffold and will flag locally owned edits as conflicts.

## Curate discovery without inventing API coverage

The starter [catalog template](../templates/library-consumer/docs/consumers/catalog.json) has empty package and capability lists. Validation accepts this scaffold and explicitly reports its incomplete status. A release bundle requires real packages and at least one capability route; preview bundles can exercise empty scaffolds.

The catalog schema is strict JSON with the following structure (the API names below are illustrative):

```json
{
  "schema_version": 1,
  "library": {
    "name": "Example Library",
    "repository": "https://github.com/example/example-library",
    "ref": "v1.2.3"
  },
  "plugin": "example-library-consumer",
  "packages": [
    { "id": "Example.Core", "version": "1.2.3" }
  ],
  "capabilities": [
    {
      "id": "lookup",
      "packages": ["Example.Core"],
      "search_terms": ["lookup", "find"],
      "symbols": ["T:Example.Lookup"],
      "page": "recipes/lookup.md"
    }
  ]
}
```

Add the referenced Markdown page and document prerequisites, registration/configuration, lifetimes, version compatibility, application responsibilities, and actual verification. Capability pages can cover several related APIs; every member need not receive its own prose recipe. `symbols` may be empty for asset-only or conceptual capabilities. Symbol IDs are opaque, language-specific strings; the generic tool does not parse source code or infer APIs from names.

The consumer [skill template](../templates/library-consumer/plugins/library-consumer/skills/library-consumer/SKILL.md) routes agents to the application's instructions, actual resolved package versions, relevant capabilities and recipes, and application validation. It applies to integration in consuming applications. Library maintenance instructions belong in the library's own AGENTS.md and local skills.

## Validate and package

From the generated library root:

```text
python tools/consumer_tooling.py validate .
python tools/consumer_tooling.py bundle . --output ../consumer-preview --allow-dirty-preview
python tools/consumer_tooling.py bundle . --output ../consumer-release
```

Both commands return **0** on success and **2** on invalid metadata, unsafe paths, Git/provenance failures, or filesystem errors. Validation checks strict catalog fields and duplicates, package ownership, plugin/skill identity, marketplace wiring, capability pages, and local Markdown links/anchors in the assembled bundle. It does not fetch external links. Markdown support covers inline links and reference definitions outside fenced code, not arbitrary HTML or a full Markdown parser.

Packaging requires a new output directory outside the source repository. It creates a ZIP containing `.agents/plugins/marketplace.json` plus this plugin and all curated references, an identical external/embedded `provenance.json`, and `SHA256SUMS`. Only the selected plugin's marketplace entry is distributed. ZIP ordering, timestamps, permissions, and JSON output are deterministic for the same inputs/runtime; no machine paths or run timestamps are recorded. The source repository and normal Git index remain unchanged.

Ordinary bundles require a clean Git repository root whose HEAD equals the resolved `library.ref`, with every authoring input tracked (even if an ignored file would otherwise escape the dirty check). Previews explicitly record `preview: true`, source dirtiness, untracked inputs, and any unresolved declared library ref, and include `-preview` in the archive name. Package versions are declared metadata, not automatically measured from binaries. Provenance records the source commit, resolved ref, declared package versions, optional inventory presence, and SHA-256 hashes for every bundled input file. The provenance file excludes its own hash.

Extract the archive into an unrelated directory and verify the skill works using only bundled relative references. The authoring skill's `references/` tree is assembled from `docs/consumers/` at bundle time. Keep consumer documentation links within that tree; links back to the original checkout are rejected. Keep only intended Markdown/JSON distribution material in `docs/consumers/`.

The generated GitHub Actions workflow validates and uploads a review preview on relevant pull requests or manual dispatch. It neither publishes a release nor installs the plugin. The local marketplace and portable root `plugin.json` follow the [official OpenAI plugin packaging documentation](https://developers.openai.com/plugins/build/plugins), checked on 2026-10-20. Host discovery/installation can change; use that documentation for current installation steps. Native plugin loading was not exercised by the Python tests.

## Optional API inventory adapter

A library can generate this JSON shape from its own compiler, reflection tooling, or package metadata and pass `--inventory path/to/inventory.json` to either consumer command:

```json
{
  "schema_version": 1,
  "packages": [
    {
      "id": "Example.Core",
      "version": "1.2.3",
      "symbols": ["T:Example.Lookup", "M:Example.Lookup.Find(System.String)"]
    }
  ]
}
```

The package IDs and versions must exactly match the catalog, and every referenced capability symbol must exist in at least one owning package. Bundles include the validated inventory at `references/api/inventory.json`. This checks agreement with the adapter's supplied data; correctness and provenance of API extraction remain the adapter's responsibility. Without an inventory, the generic checks validate guidance structure and portability but do not claim symbol existence.

Language-specific extensions may add full API extraction, baseline diffs, recipe compilation, consumer acceptance tests, or a publication workflow. Keep these isolated from published runtime packages. A generic bootstrap should not import a particular library's build system, company identifiers, authentication configuration, downstream registry, or release policy.

## Ownership, updates, and recovery

All generated files are locally owned. Standards synchronization continues to write only its existing `.agent/` scopes and never updates these files. Review future template/runtime changes explicitly rather than rerunning bootstrap over customized material. Restore prior committed tooling, metadata, and guidance together to recover.

This addition is unreleased and leaves the existing standards `0.1.0` pin and schema unchanged. A future release should classify the new optional feature as a minor addition and update release metadata together. Existing consumers need no manifest migration and receive no plugin files merely by running standards sync.
