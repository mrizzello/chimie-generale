#!/usr/bin/env python3
"""List notation problems in a slides/content/<slug>.yml before reveal.js export.

The reveal.js decks render chemistry and maths with MathJax + mhchem, so the
.yml text must use LaTeX inside $...$ ($\\ce{H3O+}$, $10^{-9}$, $K_a$) instead
of Unicode sub/superscripts (H₃O⁺, 10⁻⁹, Kₐ) or bare LaTeX (K_b).

Flags, per text field (title, label, items):
  - any Unicode subscript/superscript character;
  - '_' or '^' outside $...$;
  - unbalanced '$'.
In renders (already LaTeX), only Unicode sub/superscripts are flagged.

Usage: check_notation.py slides/content/<slug>.yml   (exit 1 if anything found)
"""
import re
import sys
from pathlib import Path

import yaml

UNICODE_SUBSUP = re.compile(
    "[⁰¹²³⁴-ⁿ"  # superscripts ⁰¹²³⁴…⁹⁺⁻⁼⁽⁾ⁿ
    "₀-ₜ"                          # subscripts ₀…₉₊₋₌₍₎ₐₑₒₓ…
    "ᵢ-ᵪⁱ]"                   # ᵢᵣᵤᵥ…, ⁱ
)


def split_math(text):
    """Return (segments, balanced): segments are (is_math, str).

    '$' toggles math mode only at brace depth 0, so mhchem's own $...$
    escapes inside \\ce{...} don't end the enclosing math span."""
    segments, buf, in_math, depth, i = [], "", False, 0, 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text):
            buf += text[i:i + 2]
            i += 2
            continue
        if in_math and c == "{":
            depth += 1
        elif in_math and c == "}":
            depth -= 1
        if c == "$" and depth == 0:
            delim = "$$" if text[i:i + 2] == "$$" else "$"
            i += len(delim)
            if in_math:
                segments.append((True, buf + delim))
                buf = ""
            else:
                if buf:
                    segments.append((False, buf))
                buf = delim
            in_math = not in_math
            continue
        buf += c
        i += 1
    if buf:
        segments.append((in_math, buf))
    return segments, not in_math


def text_problems(text):
    problems = []
    if UNICODE_SUBSUP.search(text):
        chars = "".join(sorted(set(UNICODE_SUBSUP.findall(text))))
        problems.append(f"indices/exposants Unicode ({chars})")
    segments, balanced = split_math(text)
    if not balanced:
        problems.append("'$' non apparié")
    outside = "".join(s for is_math, s in segments if not is_math)
    if "_" in outside or "^" in outside:
        problems.append("'_' ou '^' hors de $...$")
    return problems


def iter_fields(content):
    """Yield (location, text, is_tex) for every string field of the plan."""
    for n, slide in enumerate(content.get("slides", []), start=1):
        where = f"diapo {n} ({slide.get('type')}"
        where += f" « {slide['title']} »)" if slide.get("title") else ")"
        for key in ("title", "label"):
            if slide.get(key):
                yield f"{where} {key}", str(slide[key]), False
        for item in slide.get("items") or []:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            yield f"{where} item", text, False
        for r in slide.get("renders") or []:
            for key in ("tex", "html"):
                if r.get(key):
                    yield f"{where} renders/{key}", r[key], True


def find_problems(content):
    found = []
    for where, text, is_tex in iter_fields(content):
        if is_tex:
            probs = ["indices/exposants Unicode"] if UNICODE_SUBSUP.search(text) else []
        else:
            probs = text_problems(text)
        for p in probs:
            found.append((where, p, text))
    return found


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: check_notation.py <content.yml>", file=sys.stderr)
        sys.exit(2)
    content = yaml.safe_load(Path(sys.argv[1]).read_text())
    problems = find_problems(content)
    for where, prob, text in problems:
        short = text if len(text) <= 90 else text[:87] + "..."
        print(f"{where}: {prob}\n    {short}")
    print(f"{len(problems)} problème(s)")
    sys.exit(1 if problems else 0)
