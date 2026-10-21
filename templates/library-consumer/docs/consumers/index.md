# {{library_name}} consumer catalog

This catalog routes application needs to reusable library capabilities. Start with [adoption](adoption.md), [package responsibilities](packages.md), and [catalog.json](catalog.json). Search the catalog's `search_terms` and load only the relevant capability page or [recipe](recipes/README.md).

The initial catalog is intentionally empty. Maintainers need to add real package IDs, exact versions, and capability routes before producing a release bundle. The declared library ref is `{{library_ref}}`; bundle provenance records the resolved source commit. Plugin version `{{plugin_version}}` is independent of library package versions.

The generated plugin is consumer guidance. It does not install packages, change application instructions, or provide library-maintenance rules. See [maintenance](maintenance.md) for validation and packaging.
