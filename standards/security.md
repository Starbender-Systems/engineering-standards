# Security

<!-- authority: standard.security -->

## Purpose and scope

Secrets, access boundaries, input handling, and sensitive data in engineering work.

## Rules

- MUST keep credentials and sensitive production data out of source, generated artifacts, prompts, logs, and reports.
- MUST preserve authentication and authorization boundaries and validate untrusted input at those boundaries.
- SHOULD use the least access needed for a task and the repository's established secret configuration mechanism.
- MUST identify security-relevant behavior changes and unresolved exposure in the handoff without including sensitive evidence.

## Exceptions and escalation

Use the [general exception process](general.md#exceptions-and-escalation).

TODO: Establish vulnerability triage ownership, response targets, approved secret storage, and applicable compliance requirements. Do not infer them.

## Validation expectations

Exercise affected access controls and failure cases; run available repository security checks and document gaps.

## Related workflows or skills

- [Code review](../workflows/code-review.md)
- [Dependency update](../workflows/dependency-update.md)
