#!/usr/bin/env python3
"""Validate engineering-standards structure, metadata, authority, and local links."""
from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path

from _standards import (
    GROUPS, SKILL_HEADINGS, STANDARD_HEADINGS, WORKFLOW_HEADINGS, StandardsError,
    load_catalog, load_consumer, local_link, markdown_links, prose, require,
    safe_path, selected_files, shared_files, version,
)

REQUIRED_STANDARDS = (
    "general architecture git documentation security testing dependencies dotnet python embedded kicad pcb-design"
).split()
REQUIRED_WORKFLOWS = (
    "feature-development defect-investigation dependency-update code-review release ef-migration pcbway-release"
).split()
REQUIRED_SKILLS = ("sb-dotnet-engineering", "sb-kicad-engineering", "sb-repository-maintenance")
REQUIRED_TEMPLATES = (
    "AGENTS.md", "CLAUDE.md", "DEVELOPING.md", ".github/copilot-instructions.md",
    ".github/instructions/dotnet.instructions.md", ".github/instructions/tests.instructions.md",
    ".github/instructions/database.instructions.md", ".github/prompts/review-pr.prompt.md",
    ".github/prompts/investigate-bug.prompt.md", "repository-bootstrap/.agent/VERSION",
    "repository-bootstrap/.agent/manifest.yaml", "repository-bootstrap/README.md",
)
REQUIRED_FILES = (
    "README.md", "AGENTS.md", "CONTRIBUTING.md", "CHANGELOG.md", "VERSION",
    "standards-manifest.yaml", "tools/sync_standards.py", "tools/validate_repository.py",
    "tools/_standards.py", ".github/CODEOWNERS", ".github/pull_request_template.md",
    ".github/workflows/validate.yml",
)
IGNORED = {".git", ".venv", "__pycache__"}


def headings(text: str) -> set[str]:
    return set(re.findall(r"(?m)^## (.+?)\s*$", prose(text)))


def anchors(text: str) -> set[str]:
    seen = {}
    result = set()
    for title in re.findall(r"(?m)^#{1,6} (.+?)\s*$", prose(text)):
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        count = seen.get(slug, 0)
        result.add(slug if not count else f"{slug}-{count}")
        seen[slug] = count + 1
    return result


def frontmatter(text: str, label: str) -> dict[str, str]:
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    require(match is not None, f"{label}: missing front matter")
    fields = {}
    for line in match.group(1).splitlines():
        item = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*):\s*(.+)", line)
        require(item is not None, f"{label}: metadata must use one-line key: value fields")
        key, value = item.groups()
        require(key not in fields, f"{label}: duplicate metadata {key}")
        fields[key] = value.strip().strip('"\'')
    return fields


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    required = list(REQUIRED_FILES) + [f"templates/{p}" for p in REQUIRED_TEMPLATES]
    required += [f"standards/{name}.md" for name in REQUIRED_STANDARDS]
    required += [f"workflows/{name}.md" for name in REQUIRED_WORKFLOWS]
    required += [f"skills/{name}/SKILL.md" for name in REQUIRED_SKILLS]
    for path in required:
        check(safe_path(root, path).is_file(), f"Missing required file: {path}")
    for directory in (*GROUPS, "templates", "templates/.github/instructions",
                      "templates/.github/prompts", "templates/repository-bootstrap/.agent",
                      "tools", ".github/workflows"):
        check(safe_path(root, directory).is_dir(), f"Missing required directory: {directory}")
    try:
        catalog = load_catalog(root)
        bootstrap_root = root / "templates/repository-bootstrap/.agent"
        manifest = load_consumer(bootstrap_root / "manifest.yaml", catalog)
        check(version(bootstrap_root) == catalog["release"], "Bootstrap VERSION must match release")
        files = selected_files(root, catalog, manifest)
        for group in GROUPS:
            check(set(manifest[group]) == set(catalog[group]),
                  f"Bootstrap must select all catalog {group} so every starter adapter resolves")
        check(manifest["synchronized"] == catalog["synchronized"], "Bootstrap must declare all sync scopes")
        for group in ("standards", "workflows"):
            actual = {p.relative_to(root).as_posix() for p in (root / group).rglob("*") if p.is_file()}
            check(actual == set(catalog[group].values()), f"{group}: catalog and file inventory differ")
        actual_skills = {p.relative_to(root).as_posix() for p in (root / "skills").rglob("SKILL.md")}
        check(actual_skills == set(catalog["skills"].values()), "skills: catalog and entry-point inventory differ")
        actual_templates = {p.relative_to(root).as_posix() for p in (root / "templates").rglob("*") if p.is_file()}
        check(actual_templates == set(catalog["templates"]), "templates: catalog and file inventory differ")
        folded = [p.casefold() for bundle in shared_files(root, catalog).values() for p in bundle]
        check(len(folded) == len(set(folded)), "Shared paths collide on case-insensitive filesystems")
    except (StandardsError, OSError, UnicodeError) as exc:
        errors.append(str(exc))
        return sorted(set(errors))

    documents = {}
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if not set(relative.parts) & IGNORED:
            safe_path(root, relative.as_posix())
            documents[relative.as_posix()] = path.read_text(encoding="utf-8")
    for group, required_headings in (("standards", STANDARD_HEADINGS), ("workflows", WORKFLOW_HEADINGS),
                                     ("skills", SKILL_HEADINGS)):
        for name, path in catalog[group].items():
            text = documents[path]
            for heading in required_headings:
                check(heading in headings(text), f"{path}: missing heading '## {heading}'")
            if group == "standards":
                check(f"<!-- authority: standard.{name} -->" in text,
                      f"{path}: missing authoritative definition marker")
            if group == "skills":
                try:
                    fields = frontmatter(text, path)
                    check(fields.get("name") == name and len(name) <= 64, f"{path}: invalid skill name")
                    description = fields.get("description", "")
                    check(bool(description.strip()) and len(description) <= 1024
                          and "TODO" not in description and not set("<>") & set(description),
                          f"{path}: missing or invalid skill description")
                except StandardsError as exc:
                    errors.append(str(exc))
    authority = {}
    for path, text in sorted(documents.items()):
        outside_code = re.sub(r"`[^`\n]*`", "", prose(text))
        for marker in re.findall(r"<!--\s*authority:\s*([a-zA-Z0-9_.-]+)\s*-->", outside_code):
            if marker in authority:
                errors.append(f"Duplicate authority '{marker}': {authority[marker]} and {path}")
            authority[marker] = path
        if path.endswith((".instructions.md", ".prompt.md")):
            try:
                field = "applyTo" if path.endswith(".instructions.md") else "description"
                check(bool(frontmatter(text, path).get(field)), f"{path}: missing {field} metadata")
            except StandardsError as exc:
                errors.append(str(exc))

    # Map templates as if installed in a consumer; do not create fake .agent copies here.
    virtual = {f".agent/{path}": root / path for path in files}
    virtual.update({".agent/VERSION": bootstrap_root / "VERSION",
                    ".agent/manifest.yaml": bootstrap_root / "manifest.yaml"})
    for path in catalog["templates"]:
        if not path.startswith("templates/repository-bootstrap/"):
            virtual[path.removeprefix("templates/")] = root / path

    for path, text in sorted(documents.items()):
        is_adapter = path.startswith("templates/") and not path.startswith("templates/repository-bootstrap/")
        origin = path.removeprefix("templates/") if is_adapter else path
        links = markdown_links(text)
        if is_adapter:
            links += re.findall(r"`(\.agent/(?:standards|workflows|skills)/[^`\n]*)`", prose(text))
        for link in links:
            local = local_link(link)
            if local is None:
                continue
            target, fragment = local
            destination = posixpath.normpath(posixpath.join(posixpath.dirname(origin), target)) if target else origin
            if destination.startswith(("../", "/")) or "\\" in destination:
                errors.append(f"{path}: relative link escapes repository: {link}")
                continue
            if is_adapter:
                resolved = virtual.get(destination)
                exists = resolved is not None or any(p.startswith(destination.rstrip("/") + "/") for p in virtual)
            else:
                resolved = root / destination
                exists = resolved.exists()
            check(exists, f"{path}: broken relative link: {link}")
            if exists and fragment and resolved is not None and resolved.suffix == ".md":
                check(fragment in anchors(resolved.read_text(encoding="utf-8")),
                      f"{path}: missing Markdown anchor: {link}")
    changelog = documents.get("CHANGELOG.md", "")
    check(re.search(r"(?m)^## " + re.escape(catalog["release"]) + r"(?:\s|$)", changelog) is not None,
          "CHANGELOG.md must have a heading for the current release")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1],
                        help="Repository to validate (default: this script's repository)")
    args = parser.parse_args()
    try:
        errors = validate(args.root)
    except (StandardsError, OSError, UnicodeError, ValueError) as exc:
        errors = [str(exc)]
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        print(f"Validation failed: {len(errors)} error(s).", file=sys.stderr)
        return 1
    print("Repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
