# engineering-standards

A versioned, vendor-neutral source of engineering guidance for application repositories and AI development agents. Initial release: **0.1.0**.

## Shared core and thin adapters

[Standards](standards/) are the authoritative standing rules. [Workflows](workflows/) are repeatable procedures that link to those rules. [Skills](skills/) package task routing, context, procedures, and completion expectations. [Prompts](templates/.github/prompts/) are small task entry points into workflows.

Application repositories consume a pinned snapshot in `.agent/`. They own their adapters, architecture, commands, path constraints, and product decisions. This repository owns reusable guidance, portable skills, starter templates, and synchronization/validation tools. It does not prescribe application architecture, branching rules, compliance regimes, or release permissions that have not been decided.

## Instructions and adapters

The primary entry point is [templates/AGENTS.md](templates/AGENTS.md), which defines the [instruction precedence](templates/AGENTS.md#instruction-precedence): explicit user task instructions, repository-specific instructions, path-specific instructions, shared engineering standards, then general agent defaults.

Workflow and skill instructions apply when selected for a task and derive their authority from shared standards. They do not create a separate override layer. Adapters may add native behavior but must make conflicts visible rather than silently override the core. Platform-enforced instructions and permissions remain in force; this repository cannot change a host's instruction-loading algorithm.

- Codex: use the repository's `AGENTS.md`, including its manual routing to shared skills.
- Claude Code: the thin [CLAUDE.md](templates/CLAUDE.md) adapter routes to the same entry point.
- GitHub Copilot: [copilot-instructions.md](templates/.github/copilot-instructions.md), path instructions, and prompts route to shared content.
- Other agents: explicitly read `AGENTS.md` and the applicable shared files.

Native automatic discovery varies by agent and interface. `.agent/skills/` is a portable content location, not a promise of native skill discovery. Read the selected `SKILL.md` explicitly, or add a locally owned native wrapper that references it. Do not duplicate its rules.

Adapter syntax references, checked during initialization: [Codex instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [VS Code instructions](https://code.visualstudio.com/docs/agent-customization/custom-instructions), and [VS Code prompts](https://code.visualstudio.com/docs/agent-customization/prompt-files). These are maintainer references; agents need no remote fetch to use this repository.

## Versioning

<!-- authority: repository.versioning -->

[VERSION](VERSION), the [catalog](standards-manifest.yaml), bootstrap pin, and [changelog](CHANGELOG.md) describe the same release. Use semantic versioning:

- **Patch:** clarification with no intended behavior change.
- **Minor:** new guidance or a backward-compatible requirement.
- **Major:** changed or removed requirements that may require consumer updates.

Use this policy even before 1.0. Schema version is separate from the guidance release. Publish immutable version tags only as an authorized release action; an initialized VERSION file does not mean a tag has been published. Update release metadata together. Record migrations for incompatible changes.

A consumer commits its request manifest, exact VERSION, copied content, and generated `sync-state.json` hashes. Keep the source release immutable and record its commit in the update PR. This preserves the exact instruction inputs needed to reproduce previous agent behavior; model versions, tools, and nondeterminism can still affect outputs.

## Adopt a snapshot

See the [bootstrap guide](templates/repository-bootstrap/README.md) for the consumer layout and copy steps.

1. Obtain a reviewed local checkout of the intended standards release. No network downloads occur in the tools.
2. In the consumer, copy the bootstrap `.agent/manifest.yaml` and `.agent/VERSION`. Copy or merge the adapter templates and `DEVELOPING.md` without replacing existing local work.
3. Fill in application commands and constraints. Select content identifiers in the manifest; the example selects all available content.
4. Run from the standards checkout (replace the example consumer path):

```text
python tools/validate_repository.py
python tools/sync_standards.py ../application-repo
python tools/sync_standards.py ../application-repo --check
```

Use a Python 3.11+ executable; on Windows, `py -3.12` is an example if `python` points to an older installation. These are examples, not required application commands.

The consumer manifest's release must exactly match the local checkout. Selection includes transitive dependencies expressed by relative Markdown links in shared content, so linked standards and workflows remain usable offline. Select only needed adapter/path templates and adjust their links if narrowing the snapshot.

## Manifest contract and ownership

Both `.yaml` manifests use **JSON-form YAML (the JSON subset of YAML 1.2)**: quoted keys and strings, arrays and objects, no comments, anchors, custom tags, or block-style YAML. This deliberate subset allows unambiguous parsing with Python's standard library. Unsupported syntax, duplicate keys, unknown keys/identifiers, and version mismatches fail with an error.

The source catalog lists schema/release versions, available identifiers and paths, templates, synchronized scopes, and consumer-owned paths. The consumer request includes `schema_version`, `release`, `standards`, `workflows`, `skills`, and `synchronized`. All three selection arrays are required; empty arrays are valid. Unknown content is an error.

Synchronized paths are relative to `.agent/`: `standards/`, `workflows/`, `skills/`, `VERSION`, and `sync-state.json`. The consumer must explicitly declare every scope needed by its selection and dependency closure, including both metadata files. The tool refuses any other write scope. It never copies adapters or changes `.agent/manifest.yaml`.

Locally owned files include `AGENTS.md`, `CLAUDE.md`, `DEVELOPING.md`, `.github/`, `.agent/manifest.yaml`, and application architecture and constraints. All files outside the declared shared paths remain untouched. Do not edit shared snapshot files; propose changes upstream or document local constraints in local instructions.

Synchronization compares bytes, writes only differences, and emits sorted changes without timestamps. It records file hashes in `sync-state.json`. Previously tracked files no longer selected are removed only if their hashes are unchanged. Modified stale files and unknown files in shared directories produce errors and are preserved. Existing selected shared files can be restored from the source by synchronization; inspect or commit local changes first. Symlinks/reparse points and traversal paths are rejected.

Exit codes: **0** success/no drift, **1** drift in `--check`, **2** invalid input or filesystem error. `--check` never writes. Each replacement is atomic, but a whole update is not transactional: do not run concurrent writers. After interruption, restore the consumer's committed snapshot or rerun against the same checkout after resolving reported conflicts. Review the diff before committing.

## Update through a pull request

Prepare and review shared changes here first. A consumer update uses a matching reviewed checkout, changes its manifest release/selections, runs sync and `--check`, and updates locally owned adapters only if needed. Open a reviewable PR containing snapshot, manifest, hashes, compatibility notes, and local validation evidence. Do not silently update all consumers.

Rollback restores the prior committed manifest, snapshot, and adapters together, then checks against the prior source checkout. Never retag an existing release.

## Validate and contribute

```text
python tools/validate_repository.py
python -m unittest discover -s tests -v
python tools/sync_standards.py --help
```

The validator checks required structure, release metadata, manifest inventory, standard/workflow/skill sections, explicit authority markers, local Markdown links/anchors, and templates in a virtual consumer layout. It validates inline and reference-definition links outside fenced code; raw URLs, arbitrary HTML, and full Markdown parsing are outside its scope. It also checks backtick references into shared template paths. External URLs are not fetched.

GitHub Actions runs validation and behavioral tests across Windows, Linux, and macOS. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to propose changes and avoid competing sources of authority.

## Undecided policies

TODO entries are decisions to resolve, not requirements to invent. See the individual standards for details.

- TODO: Assign standards owners, CODEOWNERS entries, review expectations, and exception escalation contacts.
- TODO: Select repository branching, merge, and release/signoff policies.
- TODO: Select supported toolchains, dependency update policy, testing thresholds, and documentation review rules.
- TODO: Establish security triage, secret-storage ownership, and applicable compliance requirements.
- TODO: Define product-specific hardware constraints, manufacturing libraries, and fabrication signoff.
