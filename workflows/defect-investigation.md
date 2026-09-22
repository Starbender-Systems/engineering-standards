# Defect investigation

## When to use

Investigating failures, regressions, or unexpected behavior.

## Preconditions

Observed versus expected behavior, available reproduction details, and access to relevant code or safe diagnostics.

## Implementation steps

1. Read [general](../standards/general.md), [testing](../standards/testing.md), and [security](../standards/security.md).
2. Reproduce the failure or document why reproduction is unavailable; separate evidence from hypotheses.
3. Trace the failure to a cause and identify the affected scope.
4. Implement a targeted correction and regression evidence; investigate contradictions before expanding scope.

## Required validation

Show that the original case now behaves correctly and relevant neighboring behavior still works.

## Documentation requirements

Record reproduction steps, cause, fix, and remaining uncertainty without sensitive diagnostics.

## Completion and handoff

Report reproduction status, causal evidence, checks run, and any investigation still required.

## Rollback or recovery

Revert the fix if it worsens behavior; preserve safe diagnostic evidence for further investigation.

