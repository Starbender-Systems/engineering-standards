---
name: sb-dotnet-engineering
description: Implement and review .NET application changes, including Entity Framework migrations, using the shared standards.
---

# sb-dotnet-engineering

## Trigger conditions

Use for .NET features, defects, code review, or EF schema changes.

## Required context

Task acceptance criteria, repository AGENTS.md, development commands, SDK/target frameworks, and persistence context when relevant.

## Standards and workflows

[.NET](../../standards/dotnet.md), [feature development](../../workflows/feature-development.md), [defect investigation](../../workflows/defect-investigation.md), [code review](../../workflows/code-review.md), and [EF migration](../../workflows/ef-migration.md).

## Procedure

1. Load repository and applicable path instructions, then the linked .NET standard.
2. Choose the workflow matching the task; read additional standards referenced by that workflow.
3. Inspect affected contracts and implement the change through the selected workflow.
4. Use the migration workflow when changing the EF model or schema.

## Validation requirements

Run repository restore/build/test commands with the declared SDK; include persistence checks when affected.

## Safety boundaries

Use available local tools without assuming a particular agent API. Schema deployment and destructive data operations need task authorization; generating a migration does not authorize applying it.

## Completion report

Report changed behavior, SDK and commands used, results, compatibility or migration effects, and unresolved work.

