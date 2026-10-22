#!/usr/bin/env python3
"""Update a consumer's pinned standards snapshot; Python 3.11+, standard library only.

Copied unchanged into consumers by bootstrap. Git and authenticated GitHub CLI
are used for published releases; --source uses a clean local checkout offline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

REPOSITORY = "Starbender-Systems/engineering-standards"
SCOPES = ("standards/", "workflows/", "skills/", "VERSION", "sync-state.json")
RELEASE = re.compile(r"v?((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
                     r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?)")


class UpdateError(ValueError):
    """An update cannot safely proceed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UpdateError(message)


def reject_link(path: Path) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    require(not stat.S_ISLNK(info.st_mode) and not (
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)),
        f"Refusing symbolic link or reparse point: {path}")


def root_path(path: Path) -> Path:
    path = path.absolute()
    for parent in reversed((path, *path.parents)):
        reject_link(parent)
    return path.resolve()


def safe_path(root: Path, name: str) -> Path:
    require(isinstance(name, str) and bool(name), f"Invalid snapshot path: {name!r}")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
    parts = name.split("/")
    require(all(re.fullmatch(r"[A-Za-z0-9_.-]+", part) and part not in (".", "..")
                and not part.endswith(".") and part.split(".")[0].upper() not in reserved
                for part in parts), f"Unsafe snapshot path: {name!r}")
    path = root
    for part in parts:
        path /= part
        reject_link(path)
    return path


def read_json(data: bytes) -> dict:
    def pairs(items):
        value = {}
        for key, item in items:
            require(key not in value, f"Duplicate JSON key: {key!r}")
            value[key] = item
        return value

    value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs)
    require(isinstance(value, dict), "Expected a JSON-form YAML object")
    return value


def release_version(tag: str) -> str:
    require(isinstance(tag, str), "Release tag must be text")
    match = RELEASE.fullmatch(tag)
    require(match is not None, f"Expected a stable semantic version, got {tag!r}")
    return match[1]


def command(args: list[str]) -> str:
    try:
        result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=180)
    except FileNotFoundError as exc:
        raise UpdateError(f"Required command {args[0]!r} is missing; install Git and GitHub CLI "
                          "and authenticate with gh auth login.") from exc
    require(result.returncode == 0,
            f"{Path(args[0]).name} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def fetch_release(directory: Path, repository: str, version: str | None) -> tuple[Path, str]:
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repository)
            is not None, "Repository must be OWNER/REPO on github.com")
    args = ["gh", "release", "view"]
    if version:
        release_version(version)
        args.append(version if version.startswith("v") else "v" + version)
    args += ["--repo", repository, "--json", "tagName,isDraft,isPrerelease,publishedAt"]
    release = read_json(command(args).encode("utf-8"))
    require(release.get("isDraft") is False and release.get("isPrerelease") is False
            and bool(release.get("publishedAt")), "A published stable GitHub release is required")
    tag = release.get("tagName")
    release_version(tag)
    if version:
        require(release_version(tag) == release_version(version), "GitHub returned a different release")
    source = directory / "source"
    command(["git", "-c", "core.autocrlf=false", "clone", "--quiet", "--depth", "1",
             "--branch", tag, "--", f"https://github.com/{repository}.git", str(source)])
    require(safe_path(source, "VERSION").read_text(encoding="utf-8").strip() == release_version(tag),
            "Release tag does not match source VERSION")
    return source, tag


def snapshot(consumer: Path) -> dict[str, bytes]:
    """Read only managed files; reject edits, unknown files, and unsafe state paths."""
    files = {name: safe_path(consumer, f".agent/{name}").read_bytes()
             for name in ("manifest.yaml", "VERSION", "sync-state.json")}
    manifest, state = (read_json(files[name]) for name in ("manifest.yaml", "sync-state.json"))
    require(type(state.get("schema_version")) is int and state["schema_version"] == 1,
            "Unsupported sync-state schema_version")
    require(manifest.get("release") == state.get("release") == files["VERSION"].decode("utf-8").strip(),
            "Manifest, VERSION, and sync state must have the same existing pin")
    require(manifest["release"] == release_version(manifest["release"]), "Manifest release must omit the tag's v prefix")
    tracked = state.get("files")
    require(isinstance(tracked, dict) and "VERSION" in tracked, "Invalid sync-state file inventory")
    for name, sha in tracked.items():
        require(name == "VERSION" or any(name.startswith(scope) for scope in SCOPES[:3]),
                f"Invalid tracked snapshot path: {name!r}")
        require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha) is not None,
                f"Invalid tracked SHA-256: {name!r}")
        path = safe_path(consumer, f".agent/{name}")
        require(path.is_file(), f"Missing snapshot file: {name}; restore the committed snapshot first")
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == sha,
                f"Locally modified snapshot file: {name}; preserve and restore it before updating")
        files[name] = data
    for scope in SCOPES[:3]:
        folder = safe_path(consumer, ".agent/" + scope.rstrip("/"))
        if not folder.exists():
            continue
        require(folder.is_dir(), f"Expected snapshot directory: {folder}")
        for base, dirs, names in os.walk(folder, followlinks=False):
            for name in dirs + names:
                relative = (Path(base) / name).relative_to(consumer / ".agent").as_posix()
                safe_path(consumer, ".agent/" + relative)
                if name in names:
                    require(relative in tracked, f"Untracked file in shared snapshot: {relative}")
    return files


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def apply_update(consumer: Path, before: dict[str, bytes], after: dict[str, bytes], changes: list[str]) -> None:
    # Metadata last. Recover handled write failures; process termination is not transactional.
    completed = []
    try:
        for name in sorted(changes, key=lambda name: (name in ("VERSION", "sync-state.json", "manifest.yaml"), name)):
            path = safe_path(consumer, ".agent/" + name)
            if name in after:
                atomic_write(path, after[name])
            else:
                path.unlink()
            completed.append(name)
    except (OSError, KeyboardInterrupt):
        for name in reversed(completed):
            path = safe_path(consumer, ".agent/" + name)
            if name in before:
                atomic_write(path, before[name])
            elif path.exists():
                path.unlink()
        raise


def update(consumer: Path, *, source: Path | None = None, repository: str = REPOSITORY,
           version: str | None = None, check: bool = False) -> int:
    consumer = root_path(consumer)
    require(consumer.is_dir(), f"Consumer repository does not exist: {consumer}")
    require(not (consumer / "standards-manifest.yaml").exists(),
            "Refusing to update the engineering-standards source as a consumer")
    before = snapshot(consumer)
    manifest = read_json(before["manifest.yaml"])
    with tempfile.TemporaryDirectory(prefix="engineering-standards-update-") as directory:
        temporary = Path(directory).resolve()
        tag = "local checkout"
        if source is None:
            source, tag = fetch_release(temporary, repository, version)
        else:
            require(version is None, "--source and --version cannot be used together")
            source = root_path(source)
        require(not consumer.is_relative_to(source) and not source.is_relative_to(consumer),
                "Source and consumer repositories must not overlap")
        git_root = command(["git", "-C", str(source), "rev-parse", "--show-toplevel"])
        require(Path(git_root).resolve() == source, "Source must be a Git repository root")
        require(not command(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"]),
                "Source checkout must be clean")
        commit = command(["git", "-C", str(source), "rev-parse", "HEAD"])
        target = safe_path(source, "VERSION").read_text(encoding="utf-8").strip()
        require(target == release_version(target), "Source VERSION must omit the tag's v prefix")
        if version is None and tag != "local checkout":
            current_numbers = tuple(map(int, manifest["release"].split("+")[0].split(".")))
            target_numbers = tuple(map(int, target.split("+")[0].split(".")))
            require(target_numbers >= current_numbers, "Latest release is older than the current pin; use --version explicitly")
        command([sys.executable, str(safe_path(source, "tools/validate_repository.py"))])
        stage = temporary / "consumer"
        for name, data in before.items():
            path = stage / ".agent" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if manifest["release"] != target:
            manifest["release"] = target
            (stage / ".agent/manifest.yaml").write_text(json.dumps(manifest, indent=2) + "\n",
                                                       encoding="utf-8", newline="\n")
        sync = [sys.executable, str(safe_path(source, "tools/sync_standards.py")), str(stage)]
        command(sync)
        command(sync)
        command(sync + ["--check"])
        after = snapshot(stage)
        require(snapshot(consumer) == before, "Consumer snapshot changed during preparation; retry after resolving concurrent edits")
        changes = sorted(name for name in before.keys() | after.keys() if before.get(name) != after.get(name))
        print(f"Engineering standards {target} ({tag}); source commit {commit}")
        for name in changes:
            action = "ADD" if name not in before else "REMOVE" if name not in after else "UPDATE"
            print(f"{action} .agent/{name}")
        if check:
            print("Update available; consumer unchanged." if changes else "Already up to date; no drift.")
            return 1 if changes else 0
        apply_update(consumer, before, after, changes)
        require(snapshot(consumer) == after, "Update verification failed; restore the committed snapshot")
        print(f"Updated to {target}: {len(changes)} change(s); repeated sync and drift check passed.")
        print("Review the diff, run application checks, and commit the update through your review process.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("consumer", nargs="?", type=Path, default=Path.cwd(), help="Consumer root (default: current directory)")
    parser.add_argument("--repository", default=REPOSITORY, help="GitHub OWNER/REPO (default: %(default)s)")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--version", help="Specific published stable release (default: latest)")
    selection.add_argument("--source", type=Path, help="Clean local source checkout; no network or gh required")
    parser.add_argument("--check", action="store_true", help="Prepare and check without changing consumer files; exit 1 if an update exists")
    args = parser.parse_args()
    try:
        return update(args.consumer, source=args.source, repository=args.repository, version=args.version, check=args.check)
    except (UpdateError, OSError, UnicodeError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
