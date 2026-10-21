# Changelog

Guidance releases follow the [versioning policy](README.md#versioning): patches clarify without intended behavior changes, minor releases add compatible guidance or requirements, and major releases change or remove requirements that can require consumer updates.

## Unreleased

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
