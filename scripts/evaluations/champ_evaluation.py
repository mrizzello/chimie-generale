#!/usr/bin/env python3
"""Génère le "champ d'évaluation" markdown de un ou plusieurs chapitres.

Extrait le bloc `::: {.objectives data-latex=""}` de chaque chapitre demandé et
écrit un document markdown groupé par chapitre dans fields/ (gitignoré).
"""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FOOTER = (
    "#### Compétences transversales\n\n"
    "- Établir des liens entre les savoirs acquis pour construire un raisonnement "
    "scientifique pour résoudre un problème.\n"
    "- Les objectifs ci-dessus peuvent être combinés entre eux, et la matière des "
    "chapitres précédents est considérée comme acquise."
)

CHAPTER_RE = re.compile(r"^(\d+)-.+\.qmd$")
H1_RE = re.compile(r"^#\s+(.+?)\s*$")
ATTR_SUFFIX_RE = re.compile(r"\s*\{[^{}]*\}\s*$")
OBJECTIVES_OPEN_RE = re.compile(r"^:::\s*\{\.objectives\b")
FENCE_CLOSE_RE = re.compile(r"^:::\s*$")


def chapter_files():
    return sorted(REPO_ROOT.glob("[0-9]*-*.qmd"))


def resolve_chapter_arg(arg):
    files = chapter_files()

    if arg.isdigit():
        matches = [f for f in files if CHAPTER_RE.match(f.name).group(1) == arg]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = ", ".join(f.name for f in matches)
            sys.exit(f"erreur: numéro « {arg} » ambigu entre : {names}")

    matches = [f for f in files if f.stem.split("-", 1)[1] == arg]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(f.name for f in matches)
        sys.exit(f"erreur: slug « {arg} » ambigu entre : {names}")

    needle = arg.lower()
    matches = [f for f in files if needle in f.name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(f.name for f in matches)
        sys.exit(f"erreur: « {arg} » ambigu entre : {names}")

    available = ", ".join(f.name for f in files)
    sys.exit(f"erreur: aucun chapitre ne correspond à « {arg} ».\nDisponibles : {available}")


def extract_title(lines):
    for line in lines:
        m = H1_RE.match(line)
        if m:
            return ATTR_SUFFIX_RE.sub("", m.group(1))
    return None


def extract_objectives(lines):
    in_block = False
    objectives = []
    for line in lines:
        if not in_block:
            if OBJECTIVES_OPEN_RE.match(line):
                in_block = True
            continue
        if FENCE_CLOSE_RE.match(line):
            return objectives
        if line.startswith("- "):
            objectives.append(line.rstrip())
    return None


def build_section(path):
    lines = path.read_text().splitlines()
    prefix = CHAPTER_RE.match(path.name).group(1)
    chapter_num = int(prefix) // 10
    title = extract_title(lines)
    objectives = extract_objectives(lines)
    if objectives is None:
        sys.exit(f"erreur: {path.name} n'a pas de bloc objectifs.")
    heading = f"#### Chapitre {chapter_num} — {title}"
    return prefix, "\n".join([heading, "", *objectives])


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: champ_evaluation.py <chapitre1> [chapitre2 ...]")

    resolved = []
    seen = set()
    for arg in sys.argv[1:]:
        path = resolve_chapter_arg(arg)
        if path not in seen:
            seen.add(path)
            resolved.append(path)

    prefixes = []
    sections = []
    for path in resolved:
        prefix, section = build_section(path)
        prefixes.append(prefix)
        sections.append(section)

    doc = "\n\n".join(["### Champ d'évaluation", *sections, FOOTER]) + "\n"

    out_dir = REPO_ROOT / "fields"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{'-'.join(prefixes)}.md"
    out_path.write_text(doc)
    print(out_path.relative_to(REPO_ROOT))


if __name__ == "__main__":
    main()
