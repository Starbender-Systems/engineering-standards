# Library consumer tooling bootstrap

Libraries can optionally bootstrap a consumer plugin alongside their engineering-standards snapshot. The reusable parts are a task-oriented catalog, package/version discovery guidance, integration recipes, portable skill/plugin metadata, validation, and reproducible local packaging. Domain-specific APIs, build commands, owners, and release permissions remain with the library.

The design follows the separation used by the SharedPackages consumer tooling: curated discovery and integration decisions, optional generated API evidence, and a portable bundle. This implementation is independent, uses Python 3.11+ and its standard library, and needs no SharedPackages checkout, .NET SDK, or published package to bootstrap. Git is additionally needed for bundle provenance.

## Bootstrap a new library

The root [bootstrap command](../bootstrap.py) installs the complete common [repository setup](../templates/repository-bootstrap/README.md) plus the library consumer tooling. From this standards checkout, substitute an existing target directory and the library's real identity:

```text
python bootstrap.py ../example-library --type library --name example-library --display-name "Example Library" --repository https://github.com/example/example-library
```

It accepts `--check`, `--library-ref` (default `HEAD`), and `--plugin-version` (default `0.1.0`). All common and library files are preflighted together before any write.

If the library already has a customized common baseline, the existing add-on-only command remains available:

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
python tools/consumer_tooling.py bundle . --agent all --output ../consumer-preview --allow-dirty-preview
python tools/consumer_tooling.py bundle . --agent claude --output ../consumer-claude
python tools/consumer_tooling.py bundle . --agent copilot --output ../consumer-copilot
python tools/consumer_tooling.py bundle . --output ../consumer-codex
```

Both commands return **0** on success and **2** on invalid metadata, unsafe paths, Git/provenance failures, or filesystem errors. Validation checks strict catalog fields and duplicates, package ownership, plugin/skill identity, marketplace wiring, capability pages, and local Markdown links/anchors in the assembled bundle. It does not fetch external links. Markdown support covers inline links and reference definitions outside fenced code, not arbitrary HTML or a full Markdown parser.

Packaging requires a new output directory outside the source repository. Select a host using `--agent codex`, `--agent claude`, or `--agent copilot`; `--agent all` produces one combined ZIP. Omitting the option preserves the Codex default. Every archive contains the same skill and curated references, an identical external/embedded `provenance.json`, and `SHA256SUMS`. Only the selected plugin's marketplace entry is distributed. ZIP ordering, timestamps, permissions, and JSON output are deterministic for the same inputs/runtime; no machine paths or run timestamps are recorded. The source repository and normal Git index remain unchanged.

| Build target | Marketplace in the ZIP | Plugin manifest |
| --- | --- | --- |
| `codex` (default) | `.agents/plugins/marketplace.json` | `plugins/<name>-consumer/plugin.json` |
| `claude` (Claude Code) | `.claude-plugin/marketplace.json` | `plugins/<name>-consumer/.claude-plugin/plugin.json` |
| `copilot` (GitHub Copilot) | `.github/plugin/marketplace.json` | `plugins/<name>-consumer/plugin.json` (Agent Plugins 1.0) |
| `all` | All three marketplaces | Both plugin manifests |

Keep editing the authoring root `plugin.json`, portable `SKILL.md`, and `docs/consumers/`. Native adapters are generated during assembly; no duplicate skill or separate metadata maintenance is needed. The Claude manifest copies `name`, `version`, `description`, and `repository`, and uses the catalog library name for `author.name`. Native marketplaces use the authoring marketplace name, catalog library name as `owner.name`, plugin description, and a relative string source pointing to the plugin. Review that attribution before distribution. The Codex marketplace's policy and interface fields stay in its own adapter. These targets package the scaffold's skills and references; translating arbitrary host-specific hooks, MCP configuration, or other extensions is outside this tooling's scope.

Validation checks the combined adapter layout for generated-path collisions and portable links. Bundling also checks links in the selected host layout before writing output. Do not author `plugins/<name>-consumer/.claude-plugin/plugin.json`; an existing file there is preserved and reported as a conflict. Generated native marketplaces exist only in bundles, so direct installation from an unbundled authoring checkout is not the documented Claude/Copilot workflow.

Non-Codex archive names add `-claude`, `-copilot`, or `-all` before the optional `-preview` suffix. Codex archive naming is unchanged. Provenance adds an `agents` array and hashes every generated adapter as well as shared content.

Ordinary bundles require a clean Git repository root whose HEAD equals the resolved `library.ref`, with every authoring input tracked (even if an ignored file would otherwise escape the dirty check). Previews explicitly record `preview: true`, source dirtiness, untracked inputs, and any unresolved declared library ref, and include `-preview` in the archive name. Package versions are declared metadata, not automatically measured from binaries. Provenance records the source commit, resolved ref, declared package versions, optional inventory presence, and SHA-256 hashes for every bundled input file. The provenance file excludes its own hash.

Extract the archive into an unrelated directory and verify the skill works using only bundled relative references. The authoring skill's `references/` tree is assembled from `docs/consumers/` at bundle time. Keep consumer documentation links within that tree; links back to the original checkout are rejected. Keep only intended Markdown/JSON distribution material in `docs/consumers/`.

The generated GitHub Actions workflow validates and uploads a combined `--agent all` review preview on relevant pull requests or manual dispatch. It neither publishes a release nor installs the plugin. The local Codex marketplace and portable root `plugin.json` follow the [official OpenAI plugin packaging documentation](https://developers.openai.com/plugins/build/plugins), checked on 2026-10-20. Claude adapters follow the [Claude Code manifest reference](https://code.claude.com/docs/en/plugins-reference) and [marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces). Copilot adapters follow the [GitHub Copilot plugin creation guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/plugins-creating) and [plugin reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference), checked on 2026-10-21. Host discovery/installation can change; consult the respective documentation for interface support.

### Native CLI acceptance checks

Maintainers of engineering-standards can run [the opt-in native tests](../tests/test_native_plugins.py) from this checkout with both CLIs and Git on PATH. In PowerShell with Python 3.11+ (substitute your Python launcher):

```powershell
$env:ENGINEERING_NATIVE_PLUGIN_TESTS = '1'
py -3.12 -m unittest discover -s tests -p test_native_plugins.py -v
Remove-Item Env:ENGINEERING_NATIVE_PLUGIN_TESTS
```

These tests build standalone preview fixtures for each native target and the combined target, extract them under paths with spaces, and make the authoring checkout unavailable. They require Claude's strict plugin and marketplace validation to pass without warnings, register and install each local marketplace plugin, verify enabled status and skill discovery, check bundled references, and uninstall. Configuration and cache state use disposable `CLAUDE_CONFIG_DIR`, `COPILOT_HOME`, and `COPILOT_CACHE_HOME` directories. Normal user plugin configuration is unchanged; no model prompts or release publication occur. The ordinary suite skips these four tests unless explicitly enabled; an enabled run fails if a required CLI is missing.

On 2026-10-21, these checks passed on Windows with Claude Code **2.1.302** and GitHub Copilot CLI **1.0.102** for the individual and combined bundles. This verifies native installation and discovery; it does not measure model adherence to the guidance or assert compatibility with every Copilot interface. Copilot's local marketplace install loads the extracted plugin directory live, so keep that directory available for as long as the plugin is installed. In this Copilot version, uninstalling a live local plugin disables it and its skill while preserving the extracted files and marketplace listing; the tests check that behavior.

For optional manual verification after extracting the appropriate archive, substitute its absolute directory and plugin/marketplace names. These commands install into the local host's configuration; the bundler never runs them:

```text
claude plugin validate /path/to/extracted/plugins/example-library-consumer --strict
claude plugin marketplace add /path/to/extracted
claude plugin install example-library-consumer@example-library-tooling
copilot plugin marketplace add /path/to/extracted
copilot plugin install example-library-consumer@example-library-tooling
```

### Existing library compatibility

No catalog, shared snapshot manifest, schema version, or release-pin migration is needed. Existing libraries can review and copy the updated standalone `tools/consumer_tooling.py`, then merge the maintenance guide and CI template changes. Bootstrap still refuses to overwrite locally owned files. Previous bundle commands continue to target Codex; add `--agent` to choose another host. No native marketplace or user installation is added by standards synchronization.

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

This optional feature is included in engineering-standards 0.2.0. Existing consumers keep their current standards pin until a reviewed snapshot update; see the [0.2.0 upgrade notes](../README.md#upgrading-from-010-to-020). The manifest schema and synchronization scopes are unchanged, and standards sync does not install or update plugin files. Plugin versions remain independent, including the `0.1.0` bootstrap default; a standards release alone does not require rebuilding or publishing a library's plugin. Adopt relevant tooling/template changes explicitly, then rebuild and version any updated plugin output through the library's own release process.
