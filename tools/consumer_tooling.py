#!/usr/bin/env python3
"""Validate and package library consumer guidance; Python 3.11+, standard library only.

This file is copied unchanged into library repositories by bootstrap_library.py.
It deliberately has no imports from engineering-standards.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import subprocess
import sys
from urllib.parse import unquote, urlsplit
import zipfile

CATALOG = "docs/consumers/catalog.json"
MARKETPLACE = ".agents/plugins/marketplace.json"
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
                    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
                    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
                    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?")


class ToolingError(ValueError):
    """Invalid metadata or an unsafe filesystem state."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ToolingError(message)


def text(value, label: str) -> str:
    require(isinstance(value, str) and bool(value.strip())
            and not any(ord(c) < 32 for c in value), f"{label}: expected nonempty single-line text")
    return value


def slug(value: str) -> str:
    require(isinstance(value, str) and len(value) <= 64 and SLUG.fullmatch(value) is not None,
            f"Invalid plugin/skill identifier: {value!r}")
    return value


def relative(value: str) -> str:
    text(value, "path")
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
    require(all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in (".", "..")
                and not p.endswith(".") and p.split(".")[0].upper() not in reserved
                for p in value.split("/")), f"Unsafe relative path: {value!r}")
    return value


def safe_path(root: Path, name: str) -> Path:
    current = root
    for part in relative(name).split("/"):
        current /= part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not (
            getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)),
            f"Refusing symbolic link or reparse point: {current}")
    require(current.resolve().is_relative_to(root.resolve()), f"Path escapes root: {name}")
    return current


def absolute_path(path: Path) -> Path:
    """Check caller-selected roots without imposing portable filename rules on their ancestors."""
    path = path.absolute()
    for current in reversed((path, *path.parents)):
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not (
            getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)),
            f"Refusing symbolic link or reparse point: {current}")
    return path.resolve()


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def read_json(data: bytes, label: str) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"{label}: duplicate key {key!r}")
            result[key] = value
        return result
    try:
        result = json.loads(data.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ToolingError(f"{label}: invalid JSON: {exc}") from exc
    require(isinstance(result, dict), f"{label}: expected an object")
    return result


def fields(value, expected: set[str], label: str) -> None:
    require(isinstance(value, dict) and set(value) == expected,
            f"{label}: expected fields {sorted(expected)}")


def string_list(value, label: str) -> list[str]:
    require(isinstance(value, list), f"{label}: expected a list")
    for item in value:
        text(item, label)
    require(len(set(value)) == len(value), f"{label}: duplicate entries")
    return value


def walk_files(root: Path, directory: str) -> dict[str, bytes]:
    start = safe_path(root, directory)
    require(start.is_dir(), f"Missing directory: {directory}")
    result = {}
    for base, dirs, names in os.walk(start, followlinks=False):
        for name in sorted(dirs + names):
            path = (Path(base) / name).relative_to(root).as_posix()
            target = safe_path(root, path)
            if name in names:
                require(target.is_file(), f"Expected regular file: {path}")
                result[path] = target.read_bytes()
    return result


def source_files(root: Path) -> dict[str, bytes]:
    data = safe_path(root, CATALOG).read_bytes()
    name = slug(read_json(data, CATALOG).get("plugin"))
    result = walk_files(root, "docs/consumers")
    require(all(Path(p).suffix in (".md", ".json") for p in result),
            "docs/consumers may contain only Markdown and JSON distribution files")
    result.update(walk_files(root, f"plugins/{name}"))
    result[MARKETPLACE] = safe_path(root, MARKETPLACE).read_bytes()
    return result


def markdown_links(data: bytes) -> list[tuple[str, str]]:
    body = data.decode("utf-8")
    body = re.sub(r"(?ms)^(`{3,}|~{3,})[^\n]*\n.*?^\1\s*$", "", body)
    links = re.findall(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\s*\)", body)
    links += re.findall(r"(?m)^\s{0,3}\[[^\]]+\]:\s*(<[^>]+>|\S+)", body)
    result = []
    for link in links:
        parsed = urlsplit(link.strip("<>"))
        if not parsed.scheme and not parsed.netloc:
            result.append((unquote(parsed.path), unquote(parsed.fragment)))
    return result


def anchors(data: bytes) -> set[str]:
    seen = {}
    result = set()
    for title in re.findall(r"(?m)^#{1,6} (.+?)\s*$", data.decode("utf-8")):
        key = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        count = seen.get(key, 0)
        result.add(key if not count else f"{key}-{count}")
        seen[key] = count + 1
    return result


def check_links(files: dict[str, bytes]) -> None:
    """Validate the closed, portable bundle rather than authoring-checkout paths."""
    for path, data in sorted(files.items()):
        if not path.endswith(".md"):
            continue
        for target, fragment in markdown_links(data):
            destination = posixpath.normpath(posixpath.join(posixpath.dirname(path), target)) if target else path
            exists = destination in files or any(p.startswith(destination.rstrip("/") + "/") for p in files)
            require(not destination.startswith(("/", "../")) and "\\" not in destination and exists,
                    f"{path}: broken or nonportable local link: {target}")
            if fragment and destination.endswith(".md") and destination in files:
                require(fragment in anchors(files[destination]), f"{path}: missing anchor: {target}#{fragment}")


def distribution_files(files: dict[str, bytes], name: str) -> dict[str, bytes]:
    prefix = f"plugins/{name}/skills/{name}/references/"
    result = {p: data for p, data in files.items() if p.startswith(f"plugins/{name}/")}
    for path, data in files.items():
        if path.startswith("docs/consumers/"):
            target = prefix + path.removeprefix("docs/consumers/")
            require(target not in result, f"Bundled reference would overwrite plugin file: {target}")
            result[target] = data
    # Distribute only this plugin, even when the authoring marketplace has other entries.
    marketplace = read_json(files[MARKETPLACE], MARKETPLACE)
    marketplace["plugins"] = [entry for entry in marketplace["plugins"] if entry["name"] == name]
    result[MARKETPLACE] = json_bytes(marketplace)
    return result


def validate_files(files: dict[str, bytes], inventory: dict | None = None) -> tuple[dict, dict]:
    catalog = read_json(files[CATALOG], CATALOG)
    fields(catalog, {"schema_version", "library", "plugin", "packages", "capabilities"}, CATALOG)
    require(type(catalog["schema_version"]) is int and catalog["schema_version"] == 1,
            "Unsupported consumer catalog schema_version")
    library = catalog["library"]
    fields(library, {"name", "repository", "ref"}, "library")
    for key, value in library.items():
        text(value, f"library.{key}")
    url = urlsplit(library["repository"])
    require(url.scheme == "https" and bool(url.netloc) and url.username is None and url.password is None
            and not url.query and not url.fragment, "library.repository: expected an HTTPS repository URL")
    require(not library["ref"].startswith("-"), "library.ref: must not start with '-'")
    name = slug(catalog["plugin"])
    plugin_path = f"plugins/{name}/plugin.json"
    require(plugin_path in files, f"Missing {plugin_path}")
    plugin = read_json(files[plugin_path], plugin_path)
    require(plugin.get("$schema") == PLUGIN_SCHEMA and plugin.get("name") == name,
            "Plugin schema/name must match the consumer catalog")
    require(isinstance(plugin.get("version"), str) and SEMVER.fullmatch(plugin["version"]) is not None,
            "Plugin version must be semantic versioning")
    text(plugin.get("description"), "plugin.description")
    require(plugin.get("repository") == library["repository"], "Plugin repository must match the catalog")
    skill_path = f"plugins/{name}/skills/{name}/SKILL.md"
    require(skill_path in files, f"Missing {skill_path}")
    skill = files[skill_path].decode("utf-8")
    front = re.match(r"\A---\nname: ([^\n]+)\ndescription: ([^\n]+)\n---\n", skill)
    require(front is not None and front[1] == name and len(front[2]) <= 1024,
            "Consumer skill needs matching name and a one-line description")
    marketplace = read_json(files[MARKETPLACE], MARKETPLACE)
    slug(marketplace.get("name"))
    require(isinstance(marketplace.get("plugins"), list)
            and all(isinstance(p, dict) and isinstance(p.get("name"), str) for p in marketplace["plugins"]),
            "Marketplace plugins must be named objects")
    names = [p["name"] for p in marketplace["plugins"]]
    require(len(names) == len(set(names)), "Duplicate marketplace plugin names")
    entries = [p for p in marketplace["plugins"] if p["name"] == name]
    require(len(entries) == 1 and entries[0].get("source") == {"source": "local", "path": f"./plugins/{name}"},
            "Marketplace must reference the local consumer plugin")
    require(entries[0].get("policy") == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}
            and entries[0].get("category") == "Productivity", "Consumer marketplace policy/category mismatch")

    require(isinstance(catalog["packages"], list), "packages: expected a list")
    packages = {}
    for package in catalog["packages"]:
        fields(package, {"id", "version"}, "package")
        package_id = text(package["id"], "package.id")
        text(package["version"], "package.version")
        require(package_id not in packages, f"Duplicate package: {package_id}")
        packages[package_id] = package["version"]
    require(isinstance(catalog["capabilities"], list), "capabilities: expected a list")
    ids = set()
    for capability in catalog["capabilities"]:
        fields(capability, {"id", "packages", "search_terms", "symbols", "page"}, "capability")
        identifier = slug(capability["id"])
        require(identifier not in ids, f"Duplicate capability: {identifier}")
        ids.add(identifier)
        owners = string_list(capability["packages"], "capability.packages")
        require(bool(owners) and all(p in packages for p in owners), f"{identifier}: unknown or missing package")
        require(bool(string_list(capability["search_terms"], "search_terms")), f"{identifier}: missing search terms")
        symbols = string_list(capability["symbols"], "symbols")
        page = relative(capability["page"])
        require(page.endswith(".md") and f"docs/consumers/{page}" in files,
                f"{identifier}: missing capability page: {page}")
        if inventory is not None:
            for symbol in symbols:
                require(any(symbol in inventory[p]["symbols"] for p in owners),
                        f"{identifier}: unknown inventory symbol: {symbol}")
    bundled = distribution_files(files, name)
    require(f"plugins/{name}/skills/{name}/references/provenance.json" not in bundled,
            "provenance.json is generated by the bundler; remove the authored copy")
    check_links(bundled)
    folded = [p.casefold() for p in bundled]
    require(len(folded) == len(set(folded)), "Case-insensitive distribution path collision")
    return catalog, plugin


def load_inventory(data: bytes, catalog: dict) -> dict:
    value = read_json(data, "API inventory")
    fields(value, {"schema_version", "packages"}, "API inventory")
    require(type(value["schema_version"]) is int and value["schema_version"] == 1
            and isinstance(value["packages"], list), "Invalid API inventory schema")
    packages = {}
    for package in value["packages"]:
        fields(package, {"id", "version", "symbols"}, "inventory package")
        identifier = text(package["id"], "inventory package.id")
        text(package["version"], "inventory package.version")
        string_list(package["symbols"], "inventory symbols")
        require(identifier not in packages, f"Duplicate inventory package: {identifier}")
        packages[identifier] = package
    require({p: item["version"] for p, item in packages.items()}
            == {p["id"]: p["version"] for p in catalog["packages"]},
            "API inventory must match the declared package IDs and versions exactly")
    return packages


def validate(root: Path, inventory_path: Path | None = None) -> tuple[dict[str, bytes], dict, dict]:
    root = absolute_path(root)
    files = source_files(root)
    catalog, plugin = validate_files(files)
    if inventory_path is not None:
        data = inventory_path.read_bytes()
        validate_files(files, load_inventory(data, catalog))
        target = f"plugins/{catalog['plugin']}/skills/{catalog['plugin']}/references/api/inventory.json"
        require(target not in distribution_files(files, catalog["plugin"]), "API inventory target already exists")
        files[target] = data
    return files, catalog, plugin


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                            text=True, encoding="utf-8", timeout=30)
    require(result.returncode == 0, f"Git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def source_provenance(root: Path, library_ref: str, preview: bool, source_paths: list[str]) -> dict:
    require(Path(git(root, "rev-parse", "--show-toplevel")).resolve() == root.resolve(),
            "Bundle source must be the Git repository root")
    commit = git(root, "rev-parse", "HEAD")
    dirty = bool(git(root, "status", "--porcelain", "--untracked-files=all"))
    ref_commit = None
    try:
        ref_commit = git(root, "rev-parse", "--verify", "--end-of-options", library_ref + "^{commit}")
    except ToolingError:
        require(preview, f"library.ref does not resolve: {library_ref}")
    require(preview or (not dirty and commit == ref_commit),
            "Release bundles require clean source at library.ref; use --allow-dirty-preview for local previews")
    tracked = set(git(root, "ls-files", "-z").rstrip("\0").split("\0"))
    untracked = sorted(set(source_paths) - tracked)
    require(preview or not untracked,
            f"Release bundle inputs must be tracked in Git, including ignored files: {untracked}")
    return {"source_commit": commit, "library_commit": ref_commit, "source_dirty": dirty,
            "preview": preview, "untracked_inputs": untracked}


def zip_bytes(files: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return stream.getvalue()


def bundle(root: Path, output: Path, inventory_path: Path | None = None, preview: bool = False) -> None:
    # Output must be outside source so it cannot contaminate Git provenance or package itself.
    root, output = absolute_path(root), absolute_path(output)
    require(not output.is_relative_to(root) and not root.is_relative_to(output),
            "Bundle output and source must not overlap")
    require(not output.exists(), f"Bundle output must be a new directory: {output}")
    files, catalog, plugin = validate(root, inventory_path)
    require(preview or bool(catalog["packages"]) and bool(catalog["capabilities"]),
            "Add packages and capabilities before creating a release bundle")
    # An optional adapter inventory is an external input, recorded by hash rather than Git tracking.
    authoring_paths = list(source_files(root))
    provenance = source_provenance(root, catalog["library"]["ref"], preview, authoring_paths)
    packaged = distribution_files(files, catalog["plugin"])
    provenance.update({"schema_version": 1, "library": catalog["library"],
                       "plugin": {"name": catalog["plugin"], "version": plugin["version"]},
                       "declared_packages": catalog["packages"],
                       "api_inventory_included": inventory_path is not None,
                       "files": {p: hashlib.sha256(data).hexdigest() for p, data in sorted(packaged.items())}})
    provenance_data = json_bytes(provenance)
    packaged[f"plugins/{catalog['plugin']}/skills/{catalog['plugin']}/references/provenance.json"] = provenance_data
    archive_name = f"{catalog['plugin']}-{plugin['version']}" + ("-preview" if preview else "") + ".zip"
    outputs = {archive_name: zip_bytes(packaged), "provenance.json": provenance_data}
    checksums = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(outputs.items()))
    outputs["SHA256SUMS"] = checksums.encode("utf-8")
    output.mkdir(parents=True, exist_ok=False)
    for name, data in outputs.items():
        (output / name).write_bytes(data)
    print(f"Created {'preview' if preview else 'release'} bundle: {output / archive_name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "bundle"):
        child = sub.add_parser(command)
        child.add_argument("root", type=Path, help="Library repository root")
        child.add_argument("--inventory", type=Path, help="Optional language-adapter API inventory JSON")
        if command == "bundle":
            child.add_argument("--output", type=Path, required=True, help="New directory outside the source repository")
            child.add_argument("--allow-dirty-preview", action="store_true", help="Mark output as a local preview")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            _, catalog, _ = validate(args.root, args.inventory)
            print(f"Consumer tooling valid: {len(catalog['packages'])} package(s), "
                  f"{len(catalog['capabilities'])} capability route(s).")
            if not catalog["packages"] or not catalog["capabilities"]:
                print("Starter catalog: add real packages and capability routes before a release bundle.")
        else:
            bundle(args.root, args.output, args.inventory, args.allow_dirty_preview)
        return 0
    except (ToolingError, OSError, UnicodeError, subprocess.SubprocessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
