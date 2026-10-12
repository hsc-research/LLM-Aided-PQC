#!/usr/bin/env python3
"""Check repository-local Markdown/HTML links without network access.

Checks inline links, images, reference-link definitions, and HTML href/src
attributes in tracked documentation locations. Code fences are ignored.
Local file/directory targets must exist; Markdown fragments must name a heading
or an explicit HTML anchor. External links are intentionally not fetched.
"""
from __future__ import annotations

import re
import sys
from html import unescape
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def without_fences(text: str) -> str:
    lines = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            char = marker.group(1)[0]
            if fence is None:
                fence = char
            elif fence == char:
                fence = None
            lines.append("")
        else:
            lines.append(line if fence is None else "")
    return "\n".join(lines)


def anchors(path: Path) -> set[str]:
    text = without_fences(path.read_text(encoding="utf-8"))
    found = set(re.findall(r'<[^>]+\b(?:id|name)=["\']([^"\']+)["\']', text))
    counts: dict[str, int] = {}
    for line in text.splitlines():
        match = re.match(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if not match:
            continue
        title = re.sub(r"<[^>]+>", "", unescape(match.group(1))).lower()
        title = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
        n = counts.get(title, 0)
        counts[title] = n + 1
        found.add(title if n == 0 else f"{title}-{n}")
    return found


def targets(text: str):
    text = without_fences(text)
    patterns = (
        r'!?\[[^\]\n]*\]\(\s*<?([^\s<>]+?)>?(?:\s+["\'][^\n]*?["\'])?\s*\)',
        r'^ {0,3}\[[^\]\n]+\]:\s*<?([^\s<>]+)>?',
        r'<[^>]+\b(?:href|src)=["\']([^"\']+)["\']',
    )
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            yield match.start(), unescape(match.group(1))


def main() -> int:
    files = sorted(set(ROOT.glob("*.md")) | set((ROOT / "docs").rglob("*.md")) |
                   set((ROOT / "agent").glob("README.md")) |
                   set((ROOT / "asic").glob("README.md")))
    errors = []
    checked = 0
    cache: dict[Path, set[str]] = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        for position, raw in targets(text):
            url = urlsplit(raw)
            if url.scheme or url.netloc:
                continue
            checked += 1
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            line = text.count("\n", 0, position) + 1
            if not target.exists():
                errors.append(f"{path.relative_to(ROOT)}:{line}: missing target {raw}")
            elif url.fragment and target.is_file() and target.suffix == ".md":
                if target not in cache:
                    cache[target] = anchors(target)
                if unquote(url.fragment) not in cache[target]:
                    errors.append(f"{path.relative_to(ROOT)}:{line}: missing heading {raw}")
    for error in errors:
        print(error, file=sys.stderr)
    print(f"Checked {checked} local links in {len(files)} Markdown files; {len(errors)} errors.")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
