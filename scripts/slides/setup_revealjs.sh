#!/usr/bin/env bash
# One-time install of reveal.js + MathJax into slides/revealjs/lib/ (gitignored),
# so the generated decks work fully offline (file://, USB stick).
# Idempotent: does nothing if both libraries are already present.
set -euo pipefail

REVEAL_VERSION="5.1.0"
MATHJAX_VERSION="3.2.2"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LIB="$ROOT/slides/revealjs/lib"

if [[ -f "$LIB/reveal.js/dist/reveal.js" && -f "$LIB/mathjax/es5/tex-svg-full.js" ]]; then
  echo "Libraries already installed in $LIB"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP"
npm pack --silent "reveal.js@$REVEAL_VERSION" "mathjax@$MATHJAX_VERSION" >/dev/null

mkdir -p reveal mathjax
tar -xzf "reveal.js-$REVEAL_VERSION.tgz" -C reveal
tar -xzf "mathjax-$MATHJAX_VERSION.tgz" -C mathjax

rm -rf "$LIB/reveal.js" "$LIB/mathjax"
mkdir -p "$LIB/reveal.js" "$LIB/mathjax"
cp -R reveal/package/dist reveal/package/plugin reveal/package/LICENSE "$LIB/reveal.js/"
# MathJax: only the es5 bundle tree (tex-svg-full.js includes mhchem and cancel;
# SVG output needs no web fonts, which avoids file:// font-loading restrictions).
cp -R mathjax/package/es5 mathjax/package/LICENSE "$LIB/mathjax/"

echo "Installed reveal.js $REVEAL_VERSION and MathJax $MATHJAX_VERSION in $LIB"
