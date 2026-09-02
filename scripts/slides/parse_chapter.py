#!/usr/bin/env python3
"""Print a structural outline of a resolved chapter, via pandoc's JSON AST.

Used while authoring a slides/content/<slug>.yml file: gives a quick map of
headings, boxed divs (.objectives/.tcolorbox/.Exercise/.Answer/...), tables
and images, in document order, without needing to re-read the whole .qmd.
"""
import json
import subprocess
import sys
from pathlib import Path

from resolve_chapter import resolve


def to_pandoc_json(markdown: str) -> dict:
    proc = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "json"],
        input=markdown, capture_output=True, text=True, check=True,
    )
    return json.loads(proc.stdout)


def inline_text(inlines) -> str:
    parts = []
    for node in inlines:
        t = node.get("t")
        if t in ("Str",):
            parts.append(node["c"])
        elif t in ("Space", "SoftBreak"):
            parts.append(" ")
        elif t == "LineBreak":
            parts.append(" / ")
        elif t in ("Emph", "Strong", "SmallCaps"):
            parts.append(inline_text(node["c"]))
        elif t in ("Math",):
            parts.append(f"${node['c'][1]}$")
        elif t in ("Superscript",):
            parts.append("^" + inline_text(node["c"]))
        elif t in ("Subscript",):
            parts.append("_" + inline_text(node["c"]))
        elif t == "Code":
            parts.append(node["c"][1])
    return "".join(parts).strip()


def walk(blocks, depth=0):
    for node in blocks:
        t = node.get("t")
        pad = "  " * depth
        if t == "Header":
            level, (ident, classes, _), inlines = node["c"]
            print(f"{pad}{'#' * level} {inline_text(inlines)}  [{ident}]")
        elif t == "Div":
            (ident, classes, _), content = node["c"]
            print(f"{pad}::: {'.'.join(classes)} [{ident}]")
            walk(content, depth + 1)
            print(f"{pad}:::")
        elif t == "Para":
            preview = inline_text(node["c"])[:100]
            print(f"{pad}¶ {preview}")
        elif t == "Table":
            caption = node["c"][1]
            cap_text = inline_text(caption[1][0]["c"]) if caption and caption[1] else ""
            print(f"{pad}[TABLE] {cap_text}")
        elif t == "Figure":
            (ident, _, _), caption, body = node["c"]
            cap_text = inline_text(caption[1][0]["c"]) if caption and caption[1] else ""
            src = ""
            for block in body:
                if block.get("t") == "Plain":
                    for inline in block["c"]:
                        if inline.get("t") == "Image":
                            src = inline["c"][2][0]
            print(f"{pad}[FIGURE {ident}] {src} — {cap_text}")
        elif t in ("BulletList", "OrderedList"):
            items = node["c"] if t == "BulletList" else node["c"][1]
            print(f"{pad}[LIST]")
            for item in items:
                walk(item, depth + 1)
        elif t == "Plain":
            preview = inline_text(node["c"])[:100]
            print(f"{pad}- {preview}")
        elif t == "RawBlock":
            fmt, content = node["c"]
            print(f"{pad}[RAW:{fmt}] {content[:60]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: parse_chapter.py <chapter.qmd>", file=sys.stderr)
        sys.exit(1)
    md = resolve(Path(sys.argv[1]))
    doc = to_pandoc_json(md)
    walk(doc["blocks"])
