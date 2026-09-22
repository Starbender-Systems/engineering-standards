# Release

## When to use

Preparing a versioned software or standards release.

## Preconditions

Intended version, release scope, applicable local release process, and recovery options.

## Implementation steps

1. Read [git](../standards/git.md), [documentation](../standards/documentation.md), and [testing](../standards/testing.md).
2. Identify the exact revision, compatibility impact, and release contents.
3. Update version metadata and release notes; for this standards repository follow its root versioning policy.
4. Run release validation and assemble artifacts with provenance.
5. Publish only within existing task authorization and repository release ownership; otherwise hand off the prepared release.

## Required validation

Verify artifact contents, version consistency, and the required checks for the release.

## Documentation requirements

Record changes, migration steps, known issues, source revision, and recovery instructions.

## Completion and handoff

Report readiness and publication status separately, including the exact version and validation.

## Rollback or recovery

Restore the preceding release or use a documented forward fix; never move an already published standards tag.

