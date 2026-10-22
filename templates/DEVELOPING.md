# Developing this application

This document is locally owned. Start with [AGENTS.md](AGENTS.md) and the pinned [.agent/VERSION](.agent/VERSION).

## Architecture and constraints

TODO: Describe application boundaries, important directories, contracts, external services, and local constraints. Link actual architecture records after creating them.

## Environment and commands

TODO: Specify supported toolchains and copy-pastable setup, build, test, format, and run commands. Do not treat missing commands as successful checks.

## Data and operations

TODO: Record local development data setup, migration procedures, recovery methods, and release ownership. Do not put credentials in this file.

## Path instructions and ownership

TODO: Map maintained paths to owners and instruction files; remove unused stack adapters and tune globs.

## Shared snapshot updates

Use a reviewed local standards checkout matching the intended release, edit [.agent/manifest.yaml](.agent/manifest.yaml), synchronize, check for drift, and submit the snapshot diff for review. Keep shared content unchanged locally; put application-specific constraints here or in applicable local instructions.

For repositories initialized with the update helper, run `python tools/update_standards.py` from this root with Python 3.11+, Git, and an authenticated GitHub CLI to prepare the latest published stable snapshot. Add `--check` to preview or `--source /path/to/clean-standards-checkout` for offline use. Review the diff and run local checks before committing. The helper is locally owned; merge future helper updates explicitly.
