# Repository agent instructions

This file is owned by the application repository. Read [DEVELOPING.md](DEVELOPING.md) for local architecture, commands, and constraints, then the applicable material in [.agent/standards](.agent/standards/). The shared snapshot pin is [.agent/VERSION](.agent/VERSION).

## Instruction precedence

<!-- authority: template.instruction-precedence -->

Within repository-provided guidance, resolve conflicts in this order:

1. Explicit user task instructions.
2. Repository-specific instructions.
3. Path-specific instructions.
4. Shared engineering standards.
5. General agent defaults.

Path instructions refine work in their scope but cannot silently override a repository-wide constraint. Surface contradictions and resolve them with task context or the repository maintainer. Platform system instructions and tool permissions remain in force.

Agent-specific files may add native behavior but must not silently override shared engineering standards. Workflows and skills apply to the selected task and reference shared rules; they are not a higher precedence layer.

## Load applicable guidance

Start with [general](.agent/standards/general.md), then select standards for the affected concerns and stack. Use a procedure from [.agent/workflows](.agent/workflows/) when it matches the task. Read the relevant [skill](.agent/skills/) explicitly; native skill discovery is optional and agent-dependent.

Review applicable nested `AGENTS.md` files and [.github/instructions](.github/instructions/) for path-specific context, whether or not the agent loads them automatically. Prompts in [.github/prompts](.github/prompts/) are optional task entry points.

## Repository-specific context

TODO: Record architecture entry points, runnable setup/build/test commands, local constraints, and ownership in DEVELOPING.md. Adjust instruction globs to the actual repository layout.

The application owns this file and its adapters. The [.agent/manifest.yaml](.agent/manifest.yaml) selects a pinned shared snapshot. Propose shared changes upstream; receive updates through reviewable pull requests.
