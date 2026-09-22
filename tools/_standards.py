"""Shared manifest, path, and Markdown helpers; Python 3.11+, standard library only."""
from __future__ import annotations

import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

GROUPS = ("standards", "workflows", "skills")
SCOPES = ("standards/", "workflows/", "skills/", "VERSION", "sync-state.json")
SEMVER = re.compile(
    r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
STANDARD_HEADINGS = (
    "Purpose and scope", "Rules", "Exceptions and escalation",
    "Validation expectations", "Related workflows or skills",
)
WORKFLOW_HEADINGS = (
    "When to use", "Preconditions", "Implementation steps", "Required validation",
    "Documentation requirements", "Completion and handoff", "Rollback or recovery",
)
SKILL_HEADINGS = (
    "Trigger conditions", "Required context", "Standards and workflows", "Procedure",
    "Validation requirements", "Safety boundaries", "Completion report",
)


class StandardsError(ValueError):
    """Actionable invalid input or unsafe filesystem state."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise StandardsError(message)


def read_manifest(path: Path) -> dict:
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"{path}: duplicate key {key!r}")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StandardsError(f"{path}: expected JSON-form YAML (see README): {exc}") from exc
    require(isinstance(value, dict), f"{path}: manifest must be an object")
    return value


def keys(value: dict, expected: set[str], label: str) -> None:
    require(set(value) == expected,
            f"{label}: missing keys {sorted(expected - set(value))}; "
            f"unknown keys {sorted(set(value) - expected)}")


def strings(value, label: str) -> list[str]:
    require(isinstance(value, list) and all(isinstance(x, str) for x in value),
            f"{label}: expected a list of strings")
    require(len(value) == len(set(value)), f"{label}: duplicate entries")
    return value


def relative_path(value: str) -> str:
    require(isinstance(value, str) and bool(value), f"Invalid relative path: {value!r}")
    parts = value.removesuffix("/").split("/")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
    require(all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in (".", "..")
                and not p.endswith(".") and p.split(".")[0].upper() not in reserved
                for p in parts), f"Unsafe or nonportable relative path: {value!r}")
    return value


def safe_path(root: Path, relative: str) -> Path:
    """Reject links/reparse points, including dangling links, before any read/write."""
    relative_path(relative)
    current = root
    for part in PurePosixPath(relative).parts:
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode)
                and not (getattr(info, "st_file_attributes", 0)
                         & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)),
                f"Refusing symbolic link or reparse point: {current}")
    require(current.resolve().is_relative_to(root.resolve()), f"Path escapes root: {current}")
    return current


def version(root: Path) -> str:
    path = safe_path(root, "VERSION")
    value = path.read_text(encoding="utf-8").strip()
    require(SEMVER.fullmatch(value) is not None, f"{path}: invalid semantic version {value!r}")
    return value


def load_catalog(root: Path) -> dict:
    catalog = read_manifest(safe_path(root, "standards-manifest.yaml"))
    keys(catalog, {"schema_version", "release", *GROUPS, "templates", "synchronized",
                   "locally_owned"}, "standards-manifest.yaml")
    require(type(catalog["schema_version"]) is int and catalog["schema_version"] == 1,
            "Unsupported repository schema_version; expected 1")
    require(catalog["release"] == version(root), "Catalog release must match VERSION")
    require(catalog["synchronized"] == list(SCOPES), "Invalid catalog synchronized paths")
    for group in GROUPS:
        entries = catalog[group]
        require(isinstance(entries, dict) and bool(entries), f"{group}: expected nonempty object")
        for name, path in entries.items():
            require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) is not None,
                    f"Invalid {group} identifier: {name!r}")
            expected = f"{group}/{name}" + ("/SKILL.md" if group == "skills" else ".md")
            require(path == expected, f"{group}.{name}: expected path {expected}")
            require(safe_path(root, path).is_file(), f"Missing catalog file: {path}")
    for path in strings(catalog["templates"], "templates"):
        require(path.startswith("templates/"), f"Invalid template path: {path}")
        require(safe_path(root, path).is_file(), f"Missing template: {path}")
    for path in strings(catalog["locally_owned"], "locally_owned"):
        relative_path(path)
        require(not any(path == f".agent/{scope}" or
                        (scope.endswith("/") and path.startswith(f".agent/{scope}"))
                        for scope in SCOPES), f"Local/synchronized ownership overlap: {path}")
    return catalog


def load_consumer(path: Path, catalog: dict) -> dict:
    manifest = read_manifest(path)
    keys(manifest, {"schema_version", "release", *GROUPS, "synchronized"}, str(path))
    require(type(manifest["schema_version"]) is int and manifest["schema_version"] == 1,
            "Unsupported consumer schema_version; expected 1")
    require(manifest["release"] == catalog["release"],
            f"Requested release {manifest['release']!r} does not match local checkout "
            f"{catalog['release']!r}; use the matching checkout or review a manifest update")
    for group in GROUPS:
        for name in strings(manifest[group], group):
            require(name in catalog[group], f"Unknown {group} entry: {name!r}")
    for path in strings(manifest["synchronized"], "synchronized"):
        require(path in SCOPES, f"Undeclared synchronization scope: {path!r}")
    return manifest


def prose(text: str) -> str:
    # This repository uses fenced examples; do not validate links inside code.
    return re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$", "", text)


def markdown_links(text: str) -> list[str]:
    text = prose(text)
    inline = re.findall(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\s*\)", text)
    references = re.findall(r"(?m)^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", text)
    return [link.strip("<>") for link in inline + references]


def local_link(link: str) -> tuple[str, str] | None:
    parsed = urlsplit(link)
    if parsed.scheme or parsed.netloc:
        return None
    return unquote(parsed.path), unquote(parsed.fragment)


def shared_files(root: Path, catalog: dict) -> dict[tuple[str, str], list[str]]:
    result = {}
    for group in GROUPS:
        for name, entry in catalog[group].items():
            if group == "skills":
                folder = safe_path(root, entry).parent
                files = []
                for base, dirs, names in os.walk(folder, followlinks=False):
                    for child in sorted(dirs + names):
                        relative = (Path(base) / child).relative_to(root).as_posix()
                        safe_path(root, relative)
                    files.extend((Path(base) / n).relative_to(root).as_posix() for n in names)
                result[group, name] = sorted(files)
            else:
                result[group, name] = [entry]
    return result


def selected_files(root: Path, catalog: dict, manifest: dict) -> list[str]:
    """Follow local shared links so a selected bundle has no dangling dependencies."""
    bundles = shared_files(root, catalog)
    owners = {path: key for key, files in bundles.items() for path in files}
    pending = {(group, name) for group in GROUPS for name in manifest[group]}
    selected = set()
    while pending:
        key = min(pending)
        pending.remove(key)
        if key in selected:
            continue
        selected.add(key)
        for path in bundles[key]:
            if not path.endswith(".md"):
                continue
            for link in markdown_links((root / path).read_text(encoding="utf-8")):
                local = local_link(link)
                if local is None or not local[0]:
                    continue
                target = (root / path).parent.joinpath(local[0]).resolve()
                require(target.is_relative_to(root), f"Shared link escapes source: {path}: {link}")
                dependency = target.relative_to(root).as_posix()
                require(dependency in owners,
                        f"Shared link must target a cataloged shared file: {path}: {link}")
                if owners[dependency] not in selected:
                    pending.add(owners[dependency])
    return sorted({path for key in selected for path in bundles[key]})
