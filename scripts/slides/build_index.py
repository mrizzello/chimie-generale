#!/usr/bin/env python3
"""Write slides/revealjs/index.html listing every generated reveal.js deck.

The index is fully derived from the decks (titles are read from each HTML's
<title>, since the HTML is the reference and may be hand-edited), so it is
rewritten on every call. Called by build_reveal.py after each build; can also
be run on its own: build_index.py
"""
import html
import re
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parents[2] / "slides" / "revealjs"
DECK_RE = re.compile(r"^(\d+)-.+\.html$")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)

TEMPLATE = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Présentations — Chimie générale</title>
  <!-- Généré par scripts/slides/build_index.py : ne pas modifier à la main. -->
  <style>
    :root {{ color-scheme: light; --accent: rgb(0, 118, 186); }}
    body {{ margin: 0; background: #fff; color: #222;
            font-family: "Source Sans Pro", Helvetica, Arial, sans-serif; }}
    main {{ max-width: 720px; margin: 0 auto; padding: 48px 16px; }}
    h1 {{ color: var(--accent); font-weight: 600; margin: 0 0 1.2em; text-align: center; }}
    ul {{ list-style: none; padding: 0; margin: 0; }}
    li {{ border-bottom: 1px solid #ddd; }}
    a {{ display: flex; gap: 1em; align-items: baseline; padding: 0.8em 0.4em;
         color: inherit; text-decoration: none; font-size: 1.15em; }}
    a:hover, a:focus-visible {{ background: #f2f7fb; }}
    .num {{ color: var(--accent); min-width: 7.5em; font-variant-numeric: tabular-nums; }}
    .empty {{ text-align: center; color: #777; }}
  </style>
</head>
<body>
  <main>
    <h1>Présentations de chimie générale</h1>
{body}
  </main>
</body>
</html>
"""


def decks(out_dir):
    found = []
    for path in out_dir.glob("*.html"):
        m = DECK_RE.match(path.name)
        if not m:
            continue
        t = TITLE_RE.search(path.read_text(encoding="utf-8"))
        title = html.unescape(t.group(1).strip()) if t else path.stem
        found.append((int(m.group(1)), path.name, title))
    return sorted(found)


def write_index(out_dir=OUT_DIR):
    items = decks(out_dir)
    if items:
        lines = ["    <ul>"]
        for num, name, title in items:
            lines.append(f'      <li><a href="{html.escape(name)}" target="_blank" rel="noopener">'
                         f'<span class="num">Chapitre {num // 10}</span>'
                         f'<span>{html.escape(title)}</span></a></li>')
        lines.append("    </ul>")
    else:
        lines = ['    <p class="empty">Aucune présentation générée.</p>']
    path = out_dir / "index.html"
    path.write_text(TEMPLATE.format(body="\n".join(lines)), encoding="utf-8")
    print(f"Wrote {path} ({len(items)} présentation(s))")
    return path


if __name__ == "__main__":
    write_index()
