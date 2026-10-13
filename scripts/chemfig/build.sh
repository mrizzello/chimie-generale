#!/usr/bin/env bash
# Compile les dessins chemfig (images/chemfig/src/*.tex) en SVG (images/chemfig/*.svg).
# Usage : scripts/chemfig/build.sh            # tous les dessins
#         scripts/chemfig/build.sh KNO2 CaCO3 # seulement ceux-là
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$ROOT/images/chemfig/src"
OUT="$ROOT/images/chemfig"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

if [ $# -gt 0 ]; then
  files=(); for n in "$@"; do files+=("$SRC/${n%.tex}.tex"); done
else
  files=("$SRC"/*.tex)
fi

for f in "${files[@]}"; do
  name="$(basename "$f" .tex)"
  if ! pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$TMP" "$f" > "$TMP/$name.out"; then
    grep -A5 '^!' "$TMP/$name.log" >&2 || tail -20 "$TMP/$name.out" >&2
    echo "ÉCHEC : $name" >&2; exit 1
  fi
  # Les charges de \charge sont hors de la boîte englobante de standalone :
  # on compile avec une large marge (border dans le .tex) et on recadre sur l'encre.
  pdfcrop --margins 3 "$TMP/$name.pdf" "$TMP/$name-crop.pdf" > /dev/null
  pdftocairo -svg "$TMP/$name-crop.pdf" "$OUT/$name.svg"
  echo "ok  $name.svg"
done
