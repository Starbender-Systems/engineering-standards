#!/usr/bin/env python3
"""Synchronize a pinned shared snapshot from a local checkout; never use the network."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from _standards import (
    SCOPES, StandardsError, keys, load_catalog, load_consumer, read_manifest,
    require, safe_path, selected_files,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def authorized(path: str, scopes: list[str]) -> bool:
    return any(path == scope or (scope.endswith("/") and path.startswith(scope))
               for scope in scopes)


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            name = handle.name
            handle.write(data)
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def synchronize(source: Path, consumer: Path, check: bool = False) -> int:
    source, consumer = source.resolve(), consumer.resolve()
    require(consumer.is_dir(), f"Consumer repository does not exist: {consumer}")
    require(not consumer.is_relative_to(source) and not source.is_relative_to(consumer),
            "Source and consumer repositories must not overlap")
    catalog = load_catalog(source)
    agent = safe_path(consumer, ".agent")
    manifest = load_consumer(safe_path(consumer, ".agent/manifest.yaml"), catalog)
    desired = {path: safe_path(source, path).read_bytes()
               for path in selected_files(source, catalog, manifest)}
    desired["VERSION"] = (catalog["release"] + "\n").encode()
    state = {
        "schema_version": 1,
        "release": catalog["release"],
        "source_manifest_sha256": digest((source / "standards-manifest.yaml").read_bytes()),
        "files": {path: digest(data) for path, data in sorted(desired.items())},
    }
    desired["sync-state.json"] = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    state_path = safe_path(consumer, ".agent/sync-state.json")
    previous = {}
    if state_path.exists():
        prior = read_manifest(state_path)
        keys(prior, {"schema_version", "release", "source_manifest_sha256", "files"}, "sync-state.json")
        require(type(prior["schema_version"]) is int and prior["schema_version"] == 1,
                "Unsupported sync-state schema_version")
        require(isinstance(prior["files"], dict), "sync-state files must be an object")
        previous = prior["files"]
        for path, sha in previous.items():
            require(path != "sync-state.json" and authorized(path, list(SCOPES)),
                    f"Invalid tracked path: {path}")
            safe_path(consumer, f".agent/{path}")
            require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha) is not None,
                    f"Invalid tracked SHA-256: {path}")
    # Preflight the whole plan before changing anything, including removed selections.
    for path in sorted(set(desired) | set(previous)):
        require(authorized(path, manifest["synchronized"]),
                f"Refusing undeclared synchronized path: .agent/{path}; "
                "declare its scope in manifest.yaml")
        target = safe_path(consumer, f".agent/{path}")
        require(not target.exists() or target.is_file(), f"Expected a file: {target}")
    # Unknown files are never implicitly adopted or deleted during pruning.
    for scope in SCOPES:
        if not scope.endswith("/"):
            continue
        directory = safe_path(consumer, f".agent/{scope}")
        if not directory.exists():
            continue
        require(directory.is_dir(), f"Expected synchronized directory: {directory}")
        for base, dirs, names in os.walk(directory, followlinks=False):
            for name in sorted(dirs + names):
                path = (Path(base) / name).relative_to(agent).as_posix()
                safe_path(consumer, f".agent/{path}")
            for name in names:
                path = (Path(base) / name).relative_to(agent).as_posix()
                require(path in desired or path in previous,
                        f"Untracked file in shared snapshot: .agent/{path}; move it outside shared directories")
    changes = []
    for path, data in sorted(desired.items()):
        target = agent / path
        if not target.exists():
            changes.append(("ADD", path))
        elif target.read_bytes() != data:
            changes.append(("UPDATE", path))
    for path in sorted(set(previous) - set(desired)):
        target = agent / path
        if target.exists():
            require(digest(target.read_bytes()) == previous[path],
                    f"Refusing to delete modified stale file: .agent/{path}; preserve or restore it first")
            changes.append(("REMOVE", path))
    changes.sort(key=lambda item: item[1])
    for action, path in changes:
        print(f"{action} .agent/{path}")
    if check:
        print("Drift detected." if changes else "No drift.")
        return 1 if changes else 0
    # Metadata last; atomic replacement per file. See README for interrupted-run recovery.
    for action, path in changes:
        if path in ("VERSION", "sync-state.json"):
            continue
        if action == "REMOVE":
            (agent / path).unlink()
        else:
            atomic_write(agent / path, desired[path])
    changed_paths = {path for _, path in changes}
    for path in ("VERSION", "sync-state.json"):
        if path in changed_paths:
            atomic_write(agent / path, desired[path])
    print(f"Synchronized {catalog['release']}: {len(changes)} change(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("consumer", type=Path, help="Consumer repository containing .agent/manifest.yaml")
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Local standards checkout (default: this script's repository)")
    parser.add_argument("--check", action="store_true", help="Report drift without writing; exit 1 on drift")
    args = parser.parse_args()
    try:
        return synchronize(args.source, args.consumer, args.check)
    except (StandardsError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
