# Changelog

Guidance releases follow the [versioning policy](README.md#versioning): patches clarify without intended behavior changes, minor releases add compatible guidance or requirements, and major releases change or remove requirements that can require consumer updates.

## Unreleased

- Expand Python guidance with practical style, typing, API/data contracts, mutable-state isolation, errors/cleanup, I/O, packaging, concurrency, and validation. Add a portable engineering skill and thin path adapter to the catalog, bootstrap, and validator inventory. This is a proposed minor guidance addition; existing Python selections receive the expanded standard and linked skill through dependency closure on reviewed synchronization. Existing consumers can review/merge the locally owned path adapter separately. Runtime versions, tools, frameworks, schema versions, and release pins are unchanged.
- Add a C++ standard, portable engineering skill, and thin path adapter covering ownership/lifetimes, RAII, type/interface design, copy/move behavior, headers, errors, concurrency, and validation. Include them in new bootstrap selections and route C++ firmware from the embedded standard. This is a proposed minor guidance addition; reviewed synchronization can include the new content through direct selection or embedded dependency closure. Existing consumers can review/merge the locally owned path adapter separately. Toolchain/language, build system, formatting, exception/RTTI, allocation, and ABI choices remain local; release pins and schema versions are unchanged.
- Add a C# conventions standard with practical naming/style defaults, API and nullable contracts, dependency boundaries, async/concurrency guidance, error handling, collections, and value semantics. Route the .NET standard, skill, and path adapter to it and include it in new bootstrap selections. This is a proposed minor guidance addition; existing .NET selections receive it through dependency closure on a reviewed synchronization update. Formatting details, analyzer packages, and architecture remain local choices; release pins and schema versions are unchanged.
- Add a generic GitHub repository setup workflow covering branch/review rules, merge defaults, Actions, security reporting, and release environments. Include the workflow in new bootstrap selections and repository-maintenance routing; document configuration choices and verification steps without changing remote repositories or release pins. This is a proposed minor guidance addition; dependency closure can add the linked workflow to existing repository-maintenance selections on a reviewed synchronization update.
- Require every commit message to include a concise title and a nonempty summary body explaining what changed and why, with relevant validation or compatibility details; route feature development through the Git standard. This is a proposed minor guidance requirement for the next release.
- Add Claude Code and GitHub Copilot plugin build targets plus a combined bundle, deriving native manifests and marketplaces from one shared skill/metadata source; retain the default Codex command and archive name, record target agents in provenance, and generate combined CI previews. Existing library owners can review/copy the standalone runtime and template updates without changing snapshot manifests or release pins.
- Add opt-in native CLI acceptance tests for individual and combined plugins using disposable configuration/cache directories; verify strict Claude validation, marketplace registration, installation, enabled status, skill discovery, and uninstall. Include native attribution and marketplace descriptions to pass Claude's strict checks without warnings; verify with Claude Code 2.1.302 and Copilot CLI 1.0.102 on Windows.
- Add root `bootstrap.py` with a common repository setup and a library type that composes the common setup with consumer tooling; preflight the complete plan before writing and support read-only checks and identical reruns.
- Share snapshot rendering with synchronization and preserve snapshot bytes through a locally owned bootstrap `.agent/.gitattributes` file.
- Add an optional library-consumer bootstrap profile with locally owned discovery catalogs, integration recipe guidance, portable plugin/skill metadata, and a preview CI workflow.
- Add Python standard-library tooling for conflict-safe bootstrap, catalog and bundled-link validation, optional API inventory checks, and deterministic ZIPs with Git provenance and checksums.
- Cover bootstrap ownership, idempotence, malformed input, unsafe paths, bundle relocation, inventory compatibility, and release/preview boundaries with disposable-library tests.
- Keep existing snapshot scopes, schema, release pins, and consumers unchanged. This optional feature is a proposed minor addition for the next release; no release tag is implied.

## 0.1.0 - 2026-09-21

- Initialize shared standards, repeatable workflows, and portable skills.
- Add thin Codex/vendor-neutral, Claude Code, and GitHub Copilot templates.
- Add pinned local snapshot synchronization with drift checks and ownership boundaries.
- Add repository validation, behavioral tests, and cross-platform CI.
- Leave organization and product policy choices as explicit TODOs.
- Preserve the existing MIT license.

This entry initializes release metadata; it does not assert that a release tag has been published.
