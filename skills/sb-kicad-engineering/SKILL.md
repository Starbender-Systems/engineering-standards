---
name: sb-kicad-engineering
description: Edit and review KiCad designs and prepare traceable PCB fabrication or assembly packages.
---

# sb-kicad-engineering

## Trigger conditions

Use for schematic/layout changes, design checks, or PCBWay release preparation.

## Required context

Repository instructions, design revision, KiCad version, libraries, board constraints, and intended manufacturing service.

## Standards and workflows

[KiCad](../../standards/kicad.md), [PCB design](../../standards/pcb-design.md), and [PCBWay release](../../workflows/pcbway-release.md).

## Procedure

1. Read the linked standards and project-specific design constraints.
2. Inspect the schematic, PCB, libraries, and accepted rule-check exceptions.
3. Make the requested design change using available project tools and check schematic/PCB consistency.
4. For manufacturing packages, follow the PCBWay release workflow and inspect generated artifacts.

## Validation requirements

Record electrical/design-rule results, connectivity review, mechanical or orientation checks, and any unavailable viewer or tool.

## Safety boundaries

Do not infer electrical or manufacturing limits. Keep editing and export within task scope; uploading, purchasing, and ordering require explicit authorization.

## Completion report

Report changed design intent, source and tool versions, check results, accepted exceptions, artifact paths, and manufacturing readiness.

