#!/usr/bin/env python3
"""Slides added by hand to a slides/content/<slug>.yml plan.

A slide written by Claude from the chapter (auto, the default) carries a
stable `id`. A slide added by hand carries `source: manual` and
`after: <id>`, the id of the auto slide it follows. When the plan is
rewritten from the chapter, manual slides are copied back unchanged after
their anchor, so they are never lost.

    - type: content
      source: manual
      after: autoprotolyse-de-l-eau
      title: "Exemple en classe"
      items: [...]

The plan stays in presentation order: a manual slide sits right after its
anchor (or after other manual slides with the same anchor). Anchored on an
exercise (`after: exe-120`), it goes after the whole exercise + answer(s)
stack, i.e. after the last `answer`.

Usage:
  manual_slides.py validate <plan.yml>
  manual_slides.py check <old.yml> <new.yml>   # after a rewrite
"""
import sys
from pathlib import Path

import yaml

SOURCES = ("auto", "manual")


def is_manual(slide):
    return slide.get("source", "auto") == "manual"


def where(n, slide):
    label = slide.get("id") or slide.get("title") or ""
    return f"diapo {n} ({slide.get('type')}{' « ' + label + ' »' if label else ''})"


def validate(content):
    """List of error messages (empty if the plan is consistent)."""
    errors = []
    slides = content.get("slides") or []
    ids = {}
    for n, s in enumerate(slides, start=1):
        src = s.get("source", "auto")
        if src not in SOURCES:
            errors.append(f"{where(n, s)} : source « {src} » inconnue (auto ou manual)")
            continue
        if src == "auto":
            if not s.get("id"):
                errors.append(f"{where(n, s)} : slide auto sans id")
        if s.get("id"):
            if s["id"] in ids:
                errors.append(f"{where(n, s)} : id « {s['id']} » déjà utilisé (diapo {ids[s['id']]})")
            ids.setdefault(s["id"], n)

    auto_ids = {s["id"] for s in slides if not is_manual(s) and s.get("id")}
    anchor = None  # id of the auto slide manual slides may follow here
    for n, s in enumerate(slides, start=1):
        if not is_manual(s):
            if s.get("type") == "answer" and n > 1 and is_manual(slides[n - 2]):
                errors.append(f"{where(n - 1, slides[n - 2])} : placée entre un exercice et "
                              f"son corrigé ; la mettre après le dernier corrigé")
            if s.get("type") == "answer" and anchor and anchor[0] == "exercise":
                anchor = ("exercise", anchor[1], s.get("id"))
            else:
                anchor = (s.get("type"), s.get("id"), s.get("id"))
            continue
        if s.get("type") in ("exercise", "answer"):
            errors.append(f"{where(n, s)} : une slide manuelle ne peut pas être "
                          f"un exercice ou un corrigé (numérotation)")
        after = s.get("after")
        if not after:
            errors.append(f"{where(n, s)} : slide manuelle sans « after: <id> »")
        elif after not in auto_ids:
            errors.append(f"{where(n, s)} : after « {after} » ne désigne aucune slide auto")
        elif anchor is None or after not in anchor[1:]:
            here = anchor[1] if anchor else "début du plan"
            errors.append(f"{where(n, s)} : after « {after} » mais placée après « {here} » "
                          f"(déplacer la slide ou corriger after)")
    return errors


def manual_slides(content):
    return [s for s in content.get("slides") or [] if is_manual(s)]


def strip(slide):
    return {k: v for k, v in slide.items() if k != "after"}


def check(old, new):
    """Compare manual slides of the old and the rewritten plan.

    Returns (errors, notes): errors = lost or modified slides + validate();
    notes = manual slides whose anchor was reassigned."""
    errors, notes = [], []
    remaining = manual_slides(new)
    for s in manual_slides(old):
        title = s.get("title") or s.get("type")
        match = next((r for r in remaining if strip(r) == strip(s)), None)
        if match is None:
            errors.append(f"slide manuelle « {title} » (after {s.get('after')}) "
                          f"absente ou modifiée dans le nouveau plan")
            continue
        remaining.remove(match)
        if match.get("after") != s.get("after"):
            notes.append(f"slide manuelle « {title} » : ancre « {s.get('after')} » "
                         f"→ « {match.get('after')} »")
    for r in remaining:
        notes.append(f"slide manuelle nouvelle dans le nouveau plan : « {r.get('title')} »")
    errors += validate(new)
    return errors, notes


def load(path):
    return yaml.safe_load(Path(path).read_text())


def main(argv):
    if len(argv) == 3 and argv[1] == "validate":
        errors, notes = validate(load(argv[2])), []
    elif len(argv) == 4 and argv[1] == "check":
        errors, notes = check(load(argv[2]), load(argv[3]))
    else:
        print(__doc__, file=sys.stderr)
        return 2
    for line in notes:
        print(f"note : {line}")
    for line in errors:
        print(f"erreur : {line}")
    print(f"{len(errors)} erreur(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
