#!/usr/bin/env python3
"""Add optional, locally owned consumer tooling to a library; never overwrite local work."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from consumer_tooling import (
    ToolingError, absolute_path, json_bytes, read_json, require, safe_path, slug, text, validate_files, walk_files,
)


def render_profile(source: Path, name: str, display_name: str, repository: str,
                   library_ref: str, plugin_version: str = "0.1.0") -> dict[str, bytes]:
    slug(name)
    plugin_name = slug(name + "-consumer")
    for label, value in (("display name", display_name), ("repository", repository),
                         ("library ref", library_ref), ("plugin version", plugin_version)):
        text(value, label)
    tokens = {"library_slug": name, "plugin_name": plugin_name, "library_name": display_name,
              "repository": repository, "library_ref": library_ref, "plugin_version": plugin_version}

    def render(value: str) -> str:
        return re.sub(r"\{\{([a-z_]+)\}\}", lambda m: tokens.get(m[1], m[0]), value)

    def render_json(value):
        if isinstance(value, str):
            return render(value)
        if isinstance(value, list):
            return [render_json(item) for item in value]
        if isinstance(value, dict):
            return {key: render_json(item) for key, item in value.items()}
        return value

    files = {}
    prefix = "templates/library-consumer/"
    for path, data in walk_files(source, "templates/library-consumer").items():
        destination = render(path.removeprefix(prefix))
        destination = destination.replace("plugins/library-consumer/", f"plugins/{plugin_name}/")
        destination = destination.replace("skills/library-consumer/", f"skills/{plugin_name}/")
        if path.endswith(".json"):
            data = json_bytes(render_json(read_json(data, path)))
        else:
            content = render(data.decode("utf-8"))
            # JSON string quoting is also valid YAML and safely handles punctuation in display names.
            content = re.sub(r"(?m)^description: (.+)$",
                             lambda m: "description: " + json_bytes(m[1]).decode().strip(), content)
            data = content.encode("utf-8")
        require(destination not in files, f"Duplicate rendered path: {destination}")
        safe_path(source, destination)
        files[destination] = data
    runtime = source / "tools/consumer_tooling.py"
    files["tools/consumer_tooling.py"] = runtime.read_bytes()
    validate_files(files)
    return files


def bootstrap(source: Path, consumer: Path, name: str, display_name: str, repository: str,
              library_ref: str, plugin_version: str = "0.1.0", check: bool = False) -> int:
    source = source.resolve()
    consumer = absolute_path(consumer)
    require(consumer.is_dir(), f"Library repository does not exist: {consumer}")
    require(not consumer.is_relative_to(source) and not source.is_relative_to(consumer),
            "Standards source and library repository must not overlap")
    files = render_profile(source, name, display_name, repository, library_ref, plugin_version)
    additions = []
    # Preflight every destination before writing any file. Identical reruns preserve timestamps.
    for path, data in sorted(files.items()):
        target = safe_path(consumer, path)
        require(not target.exists() or target.is_file(), f"Expected file: {path}")
        require(not target.exists() or target.read_bytes() == data,
                f"Refusing to overwrite locally owned file: {path}; merge the template manually")
        for parent in target.parents:
            if parent == consumer:
                break
            require(not parent.exists() or parent.is_dir(), f"Expected directory: {parent}")
        if not target.exists():
            additions.append(path)
    for path in additions:
        print(f"ADD {path}")
    if check:
        print("Bootstrap files missing." if additions else "Bootstrap matches; no changes.")
        return 1 if additions else 0
    for path in additions:
        target = consumer / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(files[path])
    print(f"Library consumer tooling: {len(additions)} file(s) added.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("consumer", type=Path, help="Existing library repository directory")
    parser.add_argument("--name", required=True, help="Library slug; plugin is named <name>-consumer")
    parser.add_argument("--display-name", required=True, help="Human-readable library name")
    parser.add_argument("--repository", required=True, help="HTTPS library repository URL")
    parser.add_argument("--library-ref", required=True, help="Declared library Git tag or commit; HEAD for a new library")
    parser.add_argument("--plugin-version", default="0.1.0", help="Independent consumer plugin version")
    parser.add_argument("--check", action="store_true", help="Read-only: exit 1 for missing files, 2 for conflicts")
    args = parser.parse_args()
    try:
        return bootstrap(Path(__file__).resolve().parents[1], args.consumer, args.name, args.display_name,
                         args.repository, args.library_ref, args.plugin_version, args.check)
    except (ToolingError, OSError, UnicodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
