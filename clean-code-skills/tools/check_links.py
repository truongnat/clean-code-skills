#!/usr/bin/env python3
"""Check the relative links in the pack: `[text](path)` links and paths inside backticks.

Why this exists: the documents cross-reference each other constantly (skill <-> playbook <-> prompts <->
config). A path that is renamed without updating its references is invisible - until someone clicks it and gets 404.
A machine can check it in well under a second.

Run:  python3 tools/check_links.py     (exit 0 = no broken link)
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKIP_DIRS = {"node_modules"}

MD_LINK = re.compile(r"(?<!\!)\[[^\]]*\]\((?!https?:|mailto:)([^)#\s]+)")
CODE_PATH = re.compile(
    r"`((?:\.\./)*(?:references|checklists|templates|snippets|tools|configs|playbook|prompts|skills)"
    r"/[\w./-]+\.(?:md|py|json|js|ts|tsx|toml|ya?ml|xml|go|java|sh|properties))"
    r"(?:[#][\w-]+)?`"
)


def doc_files() -> list[pathlib.Path]:
    return [p for p in sorted(ROOT.rglob("*.md")) if not SKIP_DIRS & set(p.parts)]


def wanted(rel: str) -> bool:
    """Skip placeholders, URLs and anything that is not a real path."""
    rel = rel.strip("./")
    return bool(rel) and not rel.startswith(("http", "mailto", "<", "…")) and " " not in rel and "{" not in rel


def matches(base: pathlib.Path, rel: str) -> bool:
    """A path is correct if it exists at one of the valid locations inside the pack."""
    clean = rel.strip("./")
    roots = [base, base.parent, ROOT, ROOT / "skills/clean-code", base.parent / "clean-code"]
    if any((r / clean).resolve().exists() for r in roots):
        return True
    return bool(tail_exists(clean))


def tail_exists(rel: str) -> pathlib.Path | None:
    """Fallback on the last two segments - an abbreviated `../references/x.md` is still resolved."""
    parts = [x for x in rel.split("/") if x not in ("", "..", ".")]
    if len(parts) < 2:
        return None
    for hit in ROOT.rglob("/".join(parts[-2:])):
        if not SKIP_DIRS & set(hit.parts):
            return hit
    return None


def raw_matches(text: str):
    """Every (path) group the two regexes find in the text."""
    for regex in (MD_LINK, CODE_PATH):
        yield from regex.finditer(text)


def references_in(md: pathlib.Path):
    """Relative paths a document points at, placeholders filtered out."""
    for match in raw_matches(md.read_text(encoding="utf-8")):
        if wanted(match.group(1)):
            yield match.group(1)


def all_refs():
    yield from ((md, rel) for md in doc_files() for rel in references_in(md))


def main() -> int:
    refs = list(all_refs())
    broken = [f"{md.relative_to(ROOT)} -> {rel}" for md, rel in refs if not matches(md.parent, rel)]
    unique = list(dict.fromkeys(broken))
    print(f"checked {len(refs)} references to files inside the pack")
    if not unique:
        print("✅ Every relative link points at a file that exists.")
        return 0
    print(f"{len(unique)} BROKEN LINKS:")
    print("\n".join(f"  · {line}" for line in unique))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
