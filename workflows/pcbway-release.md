# PCBWay manufacturing release

## When to use

Preparing a KiCad board for fabrication or assembly through PCBWay.

## Preconditions

Reviewed design revision, KiCad version, intended fabrication/assembly service, and current manufacturer requirements supplied or verified for this job.

## Implementation steps

1. Read [KiCad](../standards/kicad.md), [PCB design](../standards/pcb-design.md), and [documentation](../standards/documentation.md).
2. Confirm order-specific layer, stackup, drill, finish, and assembly requirements; do not assume universal manufacturer defaults.
3. Run electrical/design-rule checks and review documented exceptions.
4. Export fabrication plots and drill data; when assembly is requested, export and reconcile the BOM and placement data.
5. Inspect plots, drill alignment, component orientation, and completeness in an independent viewer where available.
6. Package artifacts from one revision, record checksums and production options, and hand off for the project's manufacturing signoff.

## Required validation

Check fabrication layers and drills; for assembly verify references, quantities, rotations, board side, and fitted/not-fitted parts.

## Documentation requirements

Include revision, tool version, file inventory, options, accepted exceptions, and unresolved manufacturer questions.

## Completion and handoff

Report package readiness separately from upload, purchase, or order placement; those require explicit task authorization.

## Rollback or recovery

Keep prior packages identifiable; replace an incorrect package before ordering and contact the order owner if already submitted.

