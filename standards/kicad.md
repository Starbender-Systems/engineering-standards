# KiCad engineering

<!-- authority: standard.kicad -->

## Purpose and scope

Schematics, PCB layouts, and KiCad project artifacts.

## Rules

- MUST record the KiCad version and preserve project-local symbol, footprint, and design-rule dependencies.
- MUST keep schematic and PCB connectivity consistent and review intentional changes to nets and footprints.
- MUST review electrical and design-rule checks and document each accepted exception with its rationale.
- MUST identify generated outputs and their source revision; avoid treating generated files as editable design sources.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Choose supported KiCad versions, library ownership, and approved exception reviewers per project.

## Validation expectations

Open the project, run relevant electrical/design-rule checks, and inspect changed connectivity and footprints.

## Related workflows or skills

- [PCBWay manufacturing release](../workflows/pcbway-release.md)
