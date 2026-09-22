# Instructions for this repository

Read [README.md](README.md) for the shared-core model and [CONTRIBUTING.md](CONTRIBUTING.md) before changing guidance. Use the [consumer precedence model](templates/AGENTS.md#instruction-precedence) when resolving repository guidance; platform system instructions and execution permissions still apply.

This repository is the shared source, so read [standards/general.md](standards/general.md) and applicable material directly from [standards](standards/), [workflows](workflows/), and [skills](skills/). Do not bootstrap a consumer snapshot into this repository.

Repository-specific constraints:

- Keep tooling compatible with Python 3.11 or later and use only its standard library.
- Preserve the existing license and unrelated work.
- Keep authoritative rules in standards and agent adapters as routing instructions.
- Use JSON-form YAML for manifests, as described in the README.
- Run `python tools/validate_repository.py` and `python -m unittest discover -s tests -v` after changes to tooling or schemas.
- Update release metadata and compatibility notes together when preparing a release. For unreleased edits, record the proposed change in the changelog.
