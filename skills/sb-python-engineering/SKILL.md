---
name: sb-python-engineering
description: Implement and review Python applications, libraries, and automation using shared guidance on contracts, runtime compatibility, and validation.
---

# sb-python-engineering

## Trigger conditions

Use for Python features, defects, code review, or runtime/packaging maintenance.

## Required context

Repository instructions, acceptance criteria, supported interpreters/platforms, environment and installation commands, packaging metadata, entry points, and configured test/format/lint/type checks.

## Standards and workflows

[Python](../../standards/python.md), [feature development](../../workflows/feature-development.md), [defect investigation](../../workflows/defect-investigation.md), [code review](../../workflows/code-review.md), and [dependency update](../../workflows/dependency-update.md).

## Procedure

1. Read repository/path instructions and the Python standard; identify runtime, public API, and external-data contracts.
2. Select the applicable workflow and inspect affected imports, mutable state, resource lifetimes, and error/concurrency behavior.
3. Implement the scoped change using established tooling and supported features; keep package/runtime migrations explicit in the task.
4. Validate affected behavior and, for packaging changes, the installed artifact and its entry points.

## Validation requirements

Use repository test and configured static-check commands in the intended environment. Check relevant boundary, portability, cleanup, and failure behavior; distinguish source-tree evidence from installed-package evidence.

## Safety boundaries

Use existing dependency and external-service processes. Running development checks does not grant authority to publish packages, deploy applications, or change live data.

## Completion report

Report changed behavior, interpreter/environment, commands and results, compatibility effects, and unavailable checks or remaining local decisions.
