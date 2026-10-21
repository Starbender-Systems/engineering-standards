#!/usr/bin/env python3
"""Compose the common repository bootstrap with the selected repository type's additions."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from _standards import StandardsError, load_catalog, load_consumer
from bootstrap_library import plan_additions, render_profile, write_additions
from consumer_tooling import ToolingError, absolute_path, require, safe_path, walk_files
from sync_standards import snapshot_files
from validate_repository import validate


def render_repository(source: Path, repository_type: str = "repository", *, name: str | None = None,
                      display_name: str | None = None, repository: str | None = None,
                      library_ref: str | None = None, plugin_version: str | None = None) -> dict[str, bytes]:
    require(repository_type in ("repository", "library"), f"Unknown repository type: {repository_type}")
    library_options = (name, display_name, repository, library_ref, plugin_version)
    require(repository_type == "library" or not any(option is not None for option in library_options),
            "Library options require --type library")
    if repository_type == "library":
        require(all(value is not None for value in (name, display_name, repository)),
                "--type library requires --name, --display-name, and --repository")
    errors = validate(source)
    require(not errors, "Standards source validation failed:\n" + "\n".join(errors))
    catalog = load_catalog(source)
    bootstrap_root = source / "templates/repository-bootstrap/.agent"
    manifest = load_consumer(bootstrap_root / "manifest.yaml", catalog)
    files = {p.removeprefix("templates/repository-bootstrap/"): data
             for p, data in walk_files(source, "templates/repository-bootstrap/.agent").items()}
    for name_in_source in ("AGENTS.md", "CLAUDE.md", "DEVELOPING.md"):
        files[name_in_source] = safe_path(source, f"templates/{name_in_source}").read_bytes()
    files.update({p.removeprefix("templates/"): data
                  for p, data in walk_files(source, "templates/.github").items()})
    files.update({f".agent/{p}": data for p, data in snapshot_files(source, catalog, manifest).items()})
    if repository_type == "library":
        additions = render_profile(source, name, display_name, repository, library_ref or "HEAD",
                                   plugin_version or "0.1.0")
        require(not files.keys() & additions.keys(), "Repository type additions overlap the common bootstrap")
        files.update(additions)
    return files


def bootstrap(source: Path, consumer: Path, repository_type: str = "repository", *,
              check: bool = False, **library_options) -> int:
    source, consumer = absolute_path(source), absolute_path(consumer)
    require(consumer.is_dir(), f"Consumer repository does not exist: {consumer}")
    require(not consumer.is_relative_to(source) and not source.is_relative_to(consumer),
            "Standards source and consumer repository must not overlap")
    files = render_repository(source, repository_type, **library_options)
    additions = plan_additions(consumer, files)
    # Unknown shared files would make the resulting snapshot invalid. Preserve them and fail early.
    for scope in ("standards", "workflows", "skills"):
        directory = f".agent/{scope}"
        if safe_path(consumer, directory).exists():
            for path in walk_files(consumer, directory):
                require(path in files, f"Untracked file in shared snapshot: {path}; move it outside shared directories")
    for path in additions:
        print(f"ADD {path}")
    if check:
        print("Bootstrap files missing." if additions else "Bootstrap matches; no changes.")
        return 1 if additions else 0
    write_additions(consumer, files, additions)
    print(f"Bootstrapped {repository_type}: {len(additions)} file(s) added.")
    print("Customize AGENTS.md and DEVELOPING.md, review the manifest selection, and review the diff before committing.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("consumer", type=Path, help="Existing target repository directory")
    parser.add_argument("--type", choices=("repository", "library"), default="repository",
                        help="repository: common setup (default); library: common setup plus consumer tooling")
    parser.add_argument("--check", action="store_true", help="Read-only: exit 1 for missing files, 2 for conflicts")
    parser.add_argument("--name", help="Library slug; requires --type library")
    parser.add_argument("--display-name", help="Human-readable library name")
    parser.add_argument("--repository", help="HTTPS library repository URL")
    parser.add_argument("--library-ref", help="Declared library tag or commit (library default: HEAD)")
    parser.add_argument("--plugin-version", help="Independent consumer plugin version (library default: 0.1.0)")
    args = parser.parse_args()
    try:
        return bootstrap(Path(__file__).resolve().parents[1], args.consumer, args.type, check=args.check,
                         name=args.name, display_name=args.display_name, repository=args.repository,
                         library_ref=args.library_ref, plugin_version=args.plugin_version)
    except (StandardsError, ToolingError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
