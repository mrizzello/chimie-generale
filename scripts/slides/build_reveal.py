#!/usr/bin/env python3
"""Build an offline reveal.js deck from a slides/content/<slug>.yml plan.

Output: slides/revealjs/<number>-<slug>.html, readable and meant to be edited
by hand afterwards (one indented <section> per slide). Once generated, the
HTML is the reference: this script refuses to overwrite it without --force.

Chemistry and maths are rendered by MathJax 3 (SVG output, mhchem + cancel,
same packages as the book's html/mathjax-mhchem.html), loaded from the shared
slides/revealjs/lib/ folder — no network access needed.

The .yml text fields must use LaTeX inside $...$ (see check_notation.py); the
build stops if Unicode sub/superscripts or bare '_'/'^' remain.

Usage: build_reveal.py slides/content/<slug>.yml [--force]
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

from build_index import write_index
from check_notation import find_problems, split_math
from manual_slides import validate as validate_manual

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "slides" / "revealjs"
LIB_DIR = OUT_DIR / "lib"
SETUP = Path(__file__).with_name("setup_revealjs.sh")


class TableError(Exception):
    pass


# --- HTML helpers -----------------------------------------------------------

def esc(text):
    """Minimal escaping that keeps LaTeX readable in the HTML source.

    Only '&' before a letter/'#' (could start an entity) and '<' before a
    letter, '/', '!' or '?' (could start a tag) are escaped; '<=>', '->',
    '& \\ce' etc. stay as written. MathJax reads the decoded text."""
    text = re.sub(r"&(?=[A-Za-z#])", "&amp;", str(text))
    return re.sub(r"<(?=[A-Za-z/!?])", "&lt;", text)


def fmt(text):
    """Escape a text field, gluing inline maths to touching punctuation.

    Browsers may break a line between '(' and a MathJax formula; '($\\ce{X}$).'
    becomes '<span class="nb">($\\ce{X}$).</span>' (no line break inside)."""
    segments, _ = split_math(str(text))
    raw = []   # plain text, not yet escaped (last element may be trimmed)
    html = []  # finished HTML pieces, in order, interleaved with raw via None
    for k, (is_math, seg) in enumerate(segments):
        if not is_math:
            raw.append(seg)
            html.append(None)
            continue
        before = ""
        if raw and html[-1] is None:
            m = re.search(r"\S+$", raw[-1])
            if m:
                before, raw[-1] = m.group(0), raw[-1][:m.start()]
        after = ""
        if k + 1 < len(segments) and not segments[k + 1][0]:
            nxt = segments[k + 1][1]
            m = re.match(r"\S+", nxt)
            if m:
                after = m.group(0)
                segments[k + 1] = (False, nxt[m.end():])
        piece = esc(before) + esc(seg) + esc(after)
        html.append(f'<span class="nb">{piece}</span>' if before or after else piece)
    texts = iter(raw)
    return "".join(esc(next(texts)) if h is None else h for h in html)


def indent(lines, n):
    pad = " " * n
    return [pad + line if line else line for line in lines]


def items_to_html(items):
    """Nested <ul> following each item's level (0 = main point)."""
    root = {"children": []}
    path = [root]  # path[k] = last node at level k-1
    for item in items:
        if isinstance(item, dict):
            text, level = item.get("text", ""), int(item.get("level", 0))
        else:
            text, level = str(item), 0
        level = min(level, len(path) - 1)
        node = {"text": text, "children": []}
        path[level]["children"].append(node)
        del path[level + 1:]
        path.append(node)

    def render(nodes):
        lines = ["<ul>"]
        for node in nodes:
            if node["children"]:
                lines.append(f"  <li>{fmt(node['text'])}")
                lines += indent(render(node["children"]), 4)
                lines.append("  </li>")
            else:
                lines.append(f"  <li>{fmt(node['text'])}</li>")
        lines.append("</ul>")
        return lines

    return render(root["children"])


# --- tabular -> <table> -------------------------------------------------------

def match_brace(s, start):
    """Index just after the '}' closing the '{' at s[start]."""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "\\":
            continue
        if s[i] == "{" and (i == 0 or s[i - 1] != "\\"):
            depth += 1
        elif s[i] == "}" and (i == 0 or s[i - 1] != "\\"):
            depth -= 1
            if depth == 0:
                return i + 1
    raise TableError("accolade non fermée")


def split_top(s, sep):
    """Split on `sep` at brace depth 0 (ignoring backslash-escaped `sep`)."""
    parts, depth, buf, i = [], 0, "", 0
    while i < len(s):
        if s.startswith(sep, i) and depth == 0 and not (sep == "&" and buf.endswith("\\")):
            parts.append(buf)
            buf = ""
            i += len(sep)
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
        buf += s[i]
        i += 1
    parts.append(buf)
    return parts


def cell_to_html(cell):
    """Text-mode tabular cell -> escaped HTML with $...$ math."""
    cell = cell.strip()
    out, plain = "", ""
    segments, balanced = split_math(cell)
    if not balanced:
        raise TableError(f"'$' non apparié dans la cellule « {cell} »")
    for is_math, seg in segments:
        if is_math:
            out += esc(seg)
            continue
        i = 0
        while i < len(seg):
            if seg.startswith("\\ce{", i):
                end = match_brace(seg, i + 3)
                out += esc(plain) + "$" + esc(seg[i:end]) + "$"
                plain, i = "", end
            elif seg.startswith("\\textbf{", i):
                end = match_brace(seg, i + 7)
                out += esc(plain) + "<strong>" + cell_to_html(seg[i + 8:end - 1]) + "</strong>"
                plain, i = "", end
            elif seg.startswith("\\hspace{", i):
                end = match_brace(seg, i + 7)
                n, unit = re.fullmatch(r"\s*([\d.]+)\s*(em|cm|mm|pt)\s*", seg[i + 8:end - 1]).groups()
                width = float(n) * {"em": 1, "cm": 2.4, "mm": 0.24, "pt": 0.083}[unit]
                out += esc(plain) + f'<span style="display:inline-block;width:{width:g}em"></span>'
                plain, i = "", end
            elif seg[i:i + 2] in ("\\%", "\\&", "\\_", "\\#", "\\ ", "\\,"):
                plain += {"\\ ": " ", "\\,": "\u202f"}.get(seg[i:i + 2], seg[i + 1])
                i += 2
            elif seg[i] == "\\":
                m = re.match(r"\\([A-Za-z]+|.)", seg[i:])
                raise TableError(f"commande « {m.group(0)} » non gérée dans « {cell} »")
            else:
                plain += seg[i]
                i += 1
        out += esc(plain)
        plain = ""
    return out.strip()


def tabular_to_html(tex):
    m = re.search(r"\\begin\{tabular\}\{([^}]*)\}(.*?)\\end\{tabular\}", tex, re.S)
    if not m:
        raise TableError("pas d'environnement tabular")
    if tex.count("\\begin{tabular}") > 1:
        raise TableError("plusieurs tabular dans un même bloc, seul le premier serait converti")
    spec, body = m.group(1).replace("|", "").replace(" ", ""), m.group(2)
    if re.search(r"[^lcr]", spec):
        raise TableError(f"spécification de colonnes « {m.group(1)} » non gérée")
    for bad in ("\\multicolumn", "\\multirow", "\\cline", "\\cmidrule"):
        if bad in body:
            raise TableError(f"« {bad} » non géré")
    align = {"l": "left", "c": "center", "r": "right"}
    body = re.sub(r"\\(toprule|bottomrule|hline)\b", "", body)
    head_tex, _, rows_tex = body.partition("\\midrule") if "\\midrule" in body else ("", "", body)
    # rules between body rows: reveal's theme already draws a line under each row
    rows_tex = rows_tex.replace("\\midrule", "")

    def rows(chunk):
        result = []
        for row in split_top(chunk, "\\\\"):
            row = re.sub(r"^\s*\[[^\]]*\]", "", row)  # \\[0.5em] spacing
            if row.strip():
                cells = split_top(row, "&")
                if len(cells) != len(spec):
                    raise TableError(f"{len(cells)} cellules au lieu de {len(spec)} : « {row.strip()} »")
                result.append([cell_to_html(c) for c in cells])
        return result

    lines = ["<table>"]
    for tag, chunk in (("th", head_tex), ("td", rows_tex)):
        data = rows(chunk)
        if not data:
            continue
        lines.append("  <thead>" if tag == "th" else "  <tbody>")
        for r in data:
            cells = "".join(
                f'<{tag} style="text-align:{align[a]}">{c}</{tag}>' for a, c in zip(spec, r)
            )
            lines.append(f"    <tr>{cells}</tr>")
        lines.append("  </thead>" if tag == "th" else "  </tbody>")
    lines.append("</table>")
    return lines


# --- slides -----------------------------------------------------------------

def copy_image(rel_path, slug):
    src = REPO_ROOT / rel_path
    if not src.exists():
        sys.exit(f"Image introuvable : {rel_path}")
    dest = OUT_DIR / "images" / slug / src.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return f"images/{slug}/{src.name}"


def render_to_html(item, slug, where):
    kind = item.get("kind", "math")
    if kind == "image":
        return [f'<img src="{copy_image(item["path"], slug)}" alt="">']
    if kind == "html":
        return item["html"].rstrip("\n").split("\n")
    if kind == "table":
        try:
            return tabular_to_html(item["tex"])
        except TableError as e:
            sys.exit(f"{where} : tableau non convertible ({e}).\n"
                     f"Réécrire ce bloc en `kind: html` dans le .yml.")
    tex = item["tex"].strip()
    if not tex.startswith("\\["):
        tex = f"\\[\n{tex}\n\\]"
    return ['<div class="math">', *indent(esc(tex).split("\n"), 2), "</div>"]


def section(classes, title_tag, title, body_lines, comment=None):
    lines = [f"<!-- {comment} -->"] if comment else []
    lines.append(f'<section class="{classes}">')
    lines.append(f"  <{title_tag}>{fmt(title)}</{title_tag}>")
    lines += indent(body_lines, 2)
    lines.append("</section>")
    return lines


def content_body(spec, slug, where, fade=True):
    body = []
    if spec.get("items"):
        body += items_to_html(spec["items"])
    if spec.get("renders"):
        body.append('<div class="renders">')
        for item in spec["renders"]:
            body += indent(render_to_html(item, slug, where), 2)
        body.append("</div>")
    # Course slides: the body is a fragment, hidden when the slide appears
    # (title only) and faded in by the next right/down arrow press.
    # Exercise and answer slides (fade=False) show their body immediately.
    cls = "body fragment fade-in" if fade else "body"
    return [f'<div class="{cls}">', *indent(body, 2), "</div>"]


def build_sections(content):
    slug = content["slug"]
    chapter_num = int(content.get("number", "0") or 0) // 10
    exercise_counter = 0
    stack = []  # exercise section + its answer sections (vertical stack)
    out = []

    def flush():
        if len(stack) == 1:
            out.extend(stack[0] + [""])
        elif stack:
            body = []
            for k, sec in enumerate(stack):
                body += ([""] if k else []) + sec
            out.extend(["<section>", *indent(body, 2), "</section>", ""])
        stack.clear()

    for n, spec in enumerate(content["slides"], start=1):
        stype = spec["type"]
        where = f"diapo {n} ({stype})"
        if stype != "answer":
            flush()
        if stype == "title":
            out += section("title-slide", "h1", spec.get("title") or content["chapter"],
                           [f"<p>Chapitre {chapter_num}</p>"])
        elif stype == "divider":
            out += section("divider", "h2", spec["title"], [])
        else:
            if stype == "exercise":
                exercise_counter += 1
                title = f"Exercice {chapter_num}.{exercise_counter}"
            elif stype == "answer":
                title = f"Corrigé {chapter_num}.{exercise_counter}"
            elif stype == "objectives":
                title = "Objectifs"
            else:
                title = spec.get("title") or stype.capitalize()
            comment = title if stype in ("exercise", "answer") else None
            if spec.get("label"):
                title = f"{title} — {spec['label']}"
            if stype in ("exercise", "answer"):
                # Exercise on top, its answer(s) below it (down arrow).
                stack.append(section(stype, "h2", title,
                                     content_body(spec, slug, where, fade=False), comment))
                continue
            if spec.get("items") and spec.get("renders"):
                # Course slide with text and a figure/table/formula: the text
                # and the renders go on two consecutive slides, same title.
                parts = [{"items": spec["items"]}, {"renders": spec["renders"]}]
            else:
                parts = [spec]
            for k, part in enumerate(parts):
                out += ([""] if k else []) + section(stype, "h2", title,
                                                     content_body(part, slug, where))
        out.append("")
    flush()
    return out


TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <link rel="stylesheet" href="lib/reveal.js/dist/reset.css">
  <link rel="stylesheet" href="lib/reveal.js/dist/reveal.css">
  <link rel="stylesheet" href="lib/reveal.js/dist/theme/white.css">
  <style>
    .reveal {{ font-size: 30px; }}
    .reveal h1 {{ font-size: 2.2em; }}
    .reveal h2 {{ font-size: 1.5em; margin-bottom: 0.6em; }}
    .reveal {{ --r-heading-text-transform: none; }}  /* no uppercase headings */
    .reveal h1, .reveal h2 {{ text-align: center; color: rgb(0, 118, 186); }}
    .reveal section {{ text-align: left; }}
    .reveal section.title-slide, .reveal section.divider {{ text-align: center; padding-top: 250px; }}
    .reveal .body {{ height: 560px; display: flex; flex-direction: column; overflow: hidden; }}
    .reveal .body > ul {{ flex: none; margin: 0 0 0.4em 1em; }}
    .reveal ul ul {{ font-size: 0.95em; }}
    .reveal li {{ margin: 0.2em 0; }}
    .reveal .renders {{ flex: 1 1 auto; min-height: 0; display: flex; flex-direction: column;
                        justify-content: flex-start; gap: 0.6em; align-items: center; }}
    .reveal .renders img {{ flex: 1 1 0; min-height: 120px; max-width: 100%;
                            object-fit: contain; margin: 0.2em 0; }}
    .reveal .renders .math {{ width: 100%; flex: none; }}
    .reveal mjx-container[display="true"] {{ overflow: hidden; margin: 0.3em 0; }}
    .reveal table {{ font-size: 0.8em; }}
    .reveal .renders > table {{ margin: 0 auto; }}  /* top-aligned, not centered */
    .reveal .nb {{ white-space: nowrap; }}
    /* reveal.css animates fragments with `transition: all`: fitSlide() would
       measure an in-between font-size. Only the fade is animated. */
    .reveal .body.fragment {{ transition-property: opacity, visibility; }}
  </style>
</head>
<body>
<div class="reveal">
<div class="slides">

{sections}
</div>
</div>

<script src="lib/reveal.js/dist/reveal.js"></script>
<script src="lib/reveal.js/plugin/math/math.js"></script>
<script src="lib/reveal.js/plugin/notes/notes.js"></script>
<script>
  // Shrink the current slide's content until it fits (display maths to the
  // slide width, then the whole body to its height). Runs after MathJax and
  // on every slide change, so hand edits stay readable without tuning.
  function fitSlide(slide) {{
    if (!slide) return;
    slide.querySelectorAll('mjx-container[display="true"]').forEach(function (m) {{
      m.style.fontSize = '';
      if (m.scrollWidth > m.clientWidth + 1) {{
        m.style.fontSize = Math.floor(100 * m.clientWidth / m.scrollWidth) + '%';
      }}
    }});
    var body = slide.querySelector('.body');
    if (!body) return;
    var size = 100;
    body.style.fontSize = '';
    while (body.scrollHeight > body.clientHeight + 1 && size > 50) {{
      size -= 5;
      body.style.fontSize = size + '%';
    }}
  }}
  function fitCurrent() {{ fitSlide(Reveal.getCurrentSlide()); }}

  Reveal.initialize({{
    width: 1280,
    height: 720,
    margin: 0.04,
    center: false,
    hash: true,
    slideNumber: false,
    transition: 'none',
    mathjax3: {{
      mathjax: 'lib/mathjax/es5/tex-svg-full.js',
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        packages: {{ '[+]': ['mhchem', 'cancel'] }}
      }},
      startup: {{
        ready: function () {{
          MathJax.startup.defaultReady();
          MathJax.startup.promise.then(function () {{ Reveal.layout(); fitCurrent(); }});
        }}
      }}
    }},
    plugins: [RevealMath.MathJax3, RevealNotes]  // RevealNotes: speaker view, key S
  }});
  Reveal.on('slidechanged', fitCurrent);

  // Speaker view (key S), "Default" layout: the upcoming slide gets the whole
  // right column (65 % of the width) to stay readable; current slide and
  // controls (timer, notes) share the left column.
  // notes.js opens an about:blank window and document.write()s the speaker
  // view into it; under file:// that window becomes inaccessible right after,
  // so the style is added to the written HTML itself. lib/ stays untouched.
  var SPEAKER_CSS =
    'body[data-speaker-layout="default"] #current-slide' +
      '{{ left: 0; top: 0; width: 35%; height: 35%; padding: 6px; }}' +
    'body[data-speaker-layout="default"] #upcoming-slide' +
      '{{ left: 35%; top: 0; width: 65%; height: 100%; padding: 6px; }}' +
    'body[data-speaker-layout="default"] #speaker-controls' +
      '{{ left: 0; top: 35%; width: 35%; height: 65%; }}';
  (function () {{
    var openWindow = window.open;
    window.open = function (url, name) {{
      var win = openWindow.apply(window, arguments);
      if (win && name === 'reveal.js - Notes') {{
        try {{
          var doc = win.document, write = doc.write;
          doc.write = function (html) {{
            doc.write = write;
            return write.call(doc, String(html).replace('</head>',
              '<style id="speaker-layout-override">' + SPEAKER_CSS + '</style></head>'));
          }};
        }} catch (e) {{ /* keep the reveal.js layout */ }}
      }}
      return win;
    }};
  }})();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yml")
    ap.add_argument("--force", action="store_true", help="écraser un HTML existant")
    args = ap.parse_args()

    content = yaml.safe_load(Path(args.yml).read_text())
    problems = find_problems(content)
    if problems:
        for where, prob, _ in problems:
            print(f"{where}: {prob}", file=sys.stderr)
        sys.exit(f"{len(problems)} problème(s) de notation : corriger le .yml "
                 f"(voir check_notation.py).")
    errors = validate_manual(content)
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(f"{len(errors)} problème(s) d'id ou de slide manuelle : corriger le .yml "
                 f"(voir manual_slides.py).")

    out_path = OUT_DIR / f"{content.get('number', '')}-{content['slug']}.html"
    if out_path.exists() and not args.force:
        sys.exit(f"{out_path} existe déjà et fait foi (retouches manuelles possibles).\n"
                 f"Relancer avec --force pour l'écraser.")

    if not (LIB_DIR / "reveal.js" / "dist" / "reveal.js").exists():
        subprocess.run(["bash", str(SETUP)], check=True)

    sections = "\n".join(build_sections(content))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(TEMPLATE.format(title=esc(content["chapter"]), sections=sections))
    print(f"Wrote {out_path}")
    write_index(OUT_DIR)


if __name__ == "__main__":
    main()
