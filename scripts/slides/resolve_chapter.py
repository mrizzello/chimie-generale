#!/usr/bin/env python3
"""Resolve Quarto {{< include >}} shortcodes in a chapter .qmd file.

Splices in the content of included exercise files (exe/<slug>/NN.qmd), drops
the end-of-chapter LaTeX-only solutions include, and strips \\newpage markers
(PDF pagination noise irrelevant to slide breaks).
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INCLUDE_RE = re.compile(r"^\{\{<\s*include\s+([^\s>]+)\s*>\}\}\s*$")


def resolve(qmd_path: Path, _seen=None) -> str:
    _seen = _seen or set()
    qmd_path = qmd_path.resolve()
    if qmd_path in _seen:
        raise RecursionError(f"Circular include: {qmd_path}")
    _seen = _seen | {qmd_path}

    lines = qmd_path.read_text().splitlines()
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped == r"\newpage":
            continue
        m = INCLUDE_RE.match(stripped)
        if m:
            target = (REPO_ROOT / m.group(1)).resolve()
            if target.name == "_solutions-fin-chapitre.qmd":
                continue
            out.append(resolve(target, _seen))
            continue
        out.append(line)
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: resolve_chapter.py <chapter.qmd>", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(resolve(Path(sys.argv[1])))
