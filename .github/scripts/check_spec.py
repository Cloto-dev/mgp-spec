#!/usr/bin/env python3
"""Checks that the specification is internally consistent.

Three checks, each taken from a rule in CLAUDE.md:

1. Relative Markdown links resolve: the target file exists and, when the link names a heading
   (`#anchor`), the target has that heading.
2. Every JSON Schema under `schemas/` is a valid Draft 2020-12 schema whose `$id` matches where
   the file lives.
3. The protocol version is stamped the same everywhere it must be: `docs/MGP_SPEC.md`, the four
   sub-documents, `CHANGELOG.md` and `docs/MGP_GUIDE.md` section 18.1. The README status badge
   is a SHOULD, so a mismatch there is reported as a warning only.

Exit status 0 when every check passes, 1 otherwise. Standard library only, apart from
`jsonschema` for check 2.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_BASE = "https://cloto.dev/schemas/"
SUB_DOCS = ["MGP_COMMUNICATION.md", "MGP_DISCOVERY.md", "MGP_GUIDE.md", "MGP_SECURITY.md"]

errors: list[str] = []
warnings: list[str] = []


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


# --- 1. links -----------------------------------------------------------------------------------

FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")
# Every "](target)" on the line: links, images, and a badge image wrapped in a link, whose outer
# target a "[text](target)" pattern misses because the text itself holds brackets.
TARGET = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")


def prose_lines(text: str):
    """Yields (line number, line) for lines outside fenced code blocks, inline code removed."""
    in_fence = False
    for n, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield n, INLINE_CODE.sub("", line)


def slug(heading: str) -> str:
    """GitHub's heading anchor: lower-cased, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"<[^>]+>", "", heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # a link keeps its text
    text = text.replace("`", "").lower()
    out = []
    for ch in text:
        if ch == " ":
            out.append("-")
        elif ch in "-_" or ch.isalnum() or unicodedata.category(ch).startswith("M"):
            out.append(ch)
    return "".join(out)


def anchors(path: Path, cache: dict) -> set[str]:
    if path not in cache:
        seen: dict[str, int] = {}
        found = set()
        for _, line in prose_lines(path.read_text(encoding="utf-8")):
            m = HEADING.match(line)
            if not m:
                continue
            base = slug(m.group(2))
            n = seen.get(base, 0)
            found.add(base if n == 0 else f"{base}-{n}")
            seen[base] = n + 1
        cache[path] = found
    return cache[path]


def check_links() -> None:
    cache: dict = {}
    for md in sorted(ROOT.rglob("*.md")):
        if ".git" in md.parts:
            continue
        for n, line in prose_lines(md.read_text(encoding="utf-8")):
            for target in TARGET.findall(line):
                if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):  # http:, mailto:, ...
                    continue
                file_part, _, anchor = target.partition("#")
                dest = md if file_part == "" else (md.parent / file_part).resolve()
                where = f"{rel(md)}:{n}"
                if not dest.exists():
                    errors.append(f"{where}: link to {target}: {file_part} does not exist")
                    continue
                if anchor and dest.suffix == ".md" and anchor.lower() not in anchors(dest, cache):
                    errors.append(f"{where}: link to {target}: {rel(dest)} has no heading #{anchor}")


# --- 2. schemas ---------------------------------------------------------------------------------


def check_schemas() -> None:
    try:
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError
    except ImportError:
        errors.append("jsonschema is not installed, so the schemas were not checked")
        return
    for path in sorted((ROOT / "schemas").rglob("*.json")):
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{rel(path)}: not valid JSON: {e}")
            continue
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as e:
            errors.append(f"{rel(path)}: not a valid Draft 2020-12 schema: {e.message}")
        want = SCHEMA_BASE + path.relative_to(ROOT / "schemas").as_posix()
        if schema.get("$id") != want:
            errors.append(f"{rel(path)}: $id is {schema.get('$id')!r}, expected {want!r}")


# --- 3. version stamps --------------------------------------------------------------------------


def table_row(text: str, version: str):
    """The (version, date) of the table row whose first cell is exactly version, or None."""
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0] == version:
            return cells[0], cells[1]
    return None


def check_versions() -> None:
    docs = ROOT / "docs"
    spec = (docs / "MGP_SPEC.md").read_text(encoding="utf-8")
    m = re.search(r"^\*\*Version:\*\*\s*(\S+)\s*$", spec, re.M)
    if not m:
        errors.append("docs/MGP_SPEC.md: no **Version:** header")
        return
    version = m.group(1)

    changelog = table_row((ROOT / "CHANGELOG.md").read_text(encoding="utf-8"), version)
    if changelog is None:
        errors.append(f"CHANGELOG.md: no row for {version} (docs/MGP_SPEC.md says {version})")
    date = changelog[1] if changelog else None

    guide = (docs / "MGP_GUIDE.md").read_text(encoding="utf-8")
    history = guide.split("### 18.1 Version History", 1)
    if len(history) < 2:
        errors.append("docs/MGP_GUIDE.md: no 18.1 Version History section")
    else:
        section = re.split(r"^#{1,3} ", history[1], maxsplit=1, flags=re.M)[0]
        row = table_row(section, version)
        if row is None:
            errors.append(f"docs/MGP_GUIDE.md 18.1: no row for {version}")
        elif date and row[1] != date:
            errors.append(f"docs/MGP_GUIDE.md 18.1: {version} is dated {row[1]}, CHANGELOG.md says {date}")

    stamp = re.compile(r"^> Part of the \[MGP Specification\]\(MGP_SPEC\.md\) \(v(\S+), (\d{4}-\d{2}-\d{2})\)\s*$", re.M)
    for name in SUB_DOCS:
        m = stamp.search((docs / name).read_text(encoding="utf-8"))
        if not m:
            errors.append(f"docs/{name}: no 'Part of the MGP Specification (vX, date)' line")
            continue
        if m.group(1) != version:
            errors.append(f"docs/{name}: stamped v{m.group(1)}, docs/MGP_SPEC.md says {version}")
        if date and m.group(2) != date:
            errors.append(f"docs/{name}: dated {m.group(2)}, CHANGELOG.md dates {version} {date}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    badge = re.search(r"status-draft%20v([0-9][0-9.]*)", readme)
    if badge and f"{badge.group(1)}-draft" != version:
        warnings.append(f"README.md: status badge says v{badge.group(1)}, docs/MGP_SPEC.md says {version}")


def main() -> int:
    check_links()
    check_schemas()
    check_versions()
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
