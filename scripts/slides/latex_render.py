#!/usr/bin/env python3
"""Render standalone LaTeX snippets (formulas or tables) to cached PNGs."""
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageOps

TRIM_MARGIN_PX = 10

MATH_TEMPLATE = r"""
\documentclass[preview,border=3pt,varwidth]{standalone}
\usepackage{amsmath,amssymb}
\usepackage[T1]{fontenc}
\usepackage[version=4]{mhchem}
\pagestyle{empty}
\begin{document}
%s
\end{document}
"""

TABLE_TEMPLATE = r"""
\documentclass[preview,border=6pt]{standalone}
\usepackage{amsmath,amssymb}
\usepackage[T1]{fontenc}
\usepackage{booktabs}
\renewcommand{\arraystretch}{1.4}
\sffamily
\pagestyle{empty}
\begin{document}
%s
\end{document}
"""

TEMPLATES = {"math": MATH_TEMPLATE, "table": TABLE_TEMPLATE}


def _hash(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:16]


def _trim_to_content(png_path: Path, margin_px: int = TRIM_MARGIN_PX) -> None:
    im = Image.open(png_path)
    rgb = im.convert("RGB")
    white = Image.new("RGB", rgb.size, (255, 255, 255))
    bbox = ImageChops.difference(rgb, white).getbbox()
    if bbox is None:
        return
    padded = ImageOps.expand(im.crop(bbox), border=margin_px, fill="white")
    padded.save(png_path)


def render_tex(tex_body: str, kind: str, cache_dir: Path, dpi: int = 400) -> Path:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    template = TEMPLATES[kind]
    key = _hash(f"{kind}::{dpi}::{tex_body}")
    png_path = cache_dir / f"{key}.png"
    if png_path.exists():
        return png_path

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        tex_file = tdp / "snippet.tex"
        tex_file.write_text(template % tex_body)
        try:
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_file.name],
                cwd=td, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
        except subprocess.CalledProcessError as exc:
            log = (tdp / "snippet.log")
            detail = log.read_text(errors="replace")[-2000:] if log.exists() else exc.stdout
            raise RuntimeError(f"pdflatex failed for:\n{tex_body}\n---\n{detail}") from exc

        pdf_file = tdp / "snippet.pdf"
        subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), pdf_file.name, str(tdp / "out")],
            cwd=td, check=True,
        )
        produced = sorted(tdp.glob("out*.png"))
        if not produced:
            raise RuntimeError(f"pdftoppm produced no output for:\n{tex_body}")
        shutil.copy(produced[0], png_path)
    _trim_to_content(png_path)
    return png_path
