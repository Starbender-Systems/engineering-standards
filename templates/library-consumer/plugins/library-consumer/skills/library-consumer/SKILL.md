---
name: {{plugin_name}}
description: Discover and integrate {{library_name}} capabilities in consuming applications. Use for implementation requests where this library may provide an existing capability. Excludes maintenance of the library itself and unrelated application work.
---

# Integrate {{library_name}}

Read the consuming repository's AGENTS.md and applicable path instructions first. This plugin supplies library capability guidance; the application owns its engineering rules and product decisions.

Use the bundled [catalog](references/index.md), [discovery metadata](references/catalog.json), and [package guide](references/packages.md) to find a capability by application need. Read only relevant capability pages and recipes. Use [adoption](references/adoption.md) for version discovery and configuration checks. An empty starter catalog is not evidence that the library lacks a capability.

1. Identify the affected application projects and their actual resolved library versions, including central version files, lockfiles, transitive dependencies, and switched source references where applicable.
2. Search existing application integrations, then catalog search terms and owning packages. Check relevant source or generated API inventory when available. Bundles may include `references/api/inventory.json`; `references/provenance.json` records the source revision and declared package versions.
3. Verify signatures, prerequisites, service lifetimes, configuration, and compatibility with the installed version before using an API. Catalog declarations alone do not prove runtime or binary compatibility. If version evidence is unavailable, report what remains unverified.
4. Prefer direct reuse or composition. Keep application authorization, business policy, endpoints, and data mappings in application adapters. If local implementation is needed, identify the specific capability gap and the shared APIs investigated.
5. Run the application's established validation for the affected integration and report results and remaining runtime checks. Do not install or upgrade packages or adopt engineering standards as an incidental part of integration.

In the library authoring repository, canonical references live under `docs/consumers/`; the bundler assembles the relative `references/` tree. Review and test the packaged skill after extraction into an unrelated directory.
