---
name: sb-repository-maintenance
description: Maintain repository instructions, shared snapshot pins, dependencies, and reviewable engineering metadata.
---

# sb-repository-maintenance

## Trigger conditions

Use for repository setup, instruction maintenance, dependency updates, or engineering-standards snapshot upgrades.

## Required context

Working tree state, local instructions, development commands, current snapshot manifest/version, and intended maintenance scope.

## Standards and workflows

[General](../../standards/general.md), [documentation](../../standards/documentation.md), [dependency update](../../workflows/dependency-update.md), [code review](../../workflows/code-review.md), and [release](../../workflows/release.md).

## Procedure

1. Inspect repository-owned files and distinguish them from synchronized shared files.
2. Choose the applicable linked workflow and identify the intended versions and compatibility impact.
3. For snapshot upgrades, use a matching local standards checkout and its documented sync tool; update the consumer request manifest and review the resulting diff.
4. Validate changed repository commands, links, and snapshots; prepare the change for review.

## Validation requirements

Run relevant repository checks; for snapshots run synchronization, repeat it, and run --check against the same source checkout.

## Safety boundaries

Preserve unrelated work. Never edit synchronized guidance as a local customization or invent owners, credentials, or release policy. The skill does not grant publication authority.

## Completion report

Report updated files and pins, compatibility impact, validation outcomes, ownership decisions still needed, and recovery steps.

