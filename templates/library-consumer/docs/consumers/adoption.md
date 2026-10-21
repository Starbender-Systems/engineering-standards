# Adopt {{library_name}}

Read the application's instructions before changing an integration. Identify actual resolved package versions using its package manager's declarations, central version files, lockfiles, or restore metadata. Source-switched dependencies also need their source revision recorded.

Use [catalog.json](catalog.json) and the [package guide](packages.md) to discover existing capabilities. Verify signatures, required configuration, dependencies, lifetimes, and supported platform against the installed version. A newer plugin can document APIs absent from an older application dependency; installation of the plugin does not upgrade that dependency.

For a packaged plugin, inspect `provenance.json` alongside this page. It identifies source/ref resolution, declared package versions, included file hashes, optional API inventory, and whether this is a preview. Declared versions are curated metadata; compiled API verification requires a library-specific inventory adapter. A preview is local validation output, not a release.

Maintainers should add tested setup and integration recipes as real capabilities become available. Validate application behavior using the consuming repository's established commands. Report missing version/source evidence and runtime checks separately from successful compilation.
