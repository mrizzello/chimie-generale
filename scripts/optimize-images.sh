#!/usr/bin/env bash
# Nettoie et compresse les images sources avant rendu du PDF.
#
# Passe 0 : supprime dans images/ (récursivement) tout fichier PNG/JPG non
#           référencé par un chemin `images/...` dans un .qmd du dépôt.
# Passe 1 : redimensionne (si nécessaire) et compresse les images restantes
#           avec ImageMagick + pngquant + oxipng (PNG) ou ImageMagick (JPG).
#
# Prérequis : magick (ImageMagick), pngquant, oxipng (`brew install pngquant oxipng`).
#
# Usage : scripts/optimize-images.sh
# À relancer à chaque ajout de nouvelles images dans images/.

set -euo pipefail

cd "$(dirname "$0")/.."

IMAGES_DIR="images"
MAX_DIM=1600

for tool in magick pngquant oxipng; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Erreur : '$tool' introuvable. Installe-le avec 'brew install pngquant oxipng' (magick via 'brew install imagemagick')." >&2
    exit 1
  fi
done

echo "== Passe 0 : suppression des images non référencées =="

refs_file="$(mktemp)"
trap 'rm -f "$refs_file"' EXIT

grep -rohE "${IMAGES_DIR}/[A-Za-z0-9_./ +()-]+\.(png|jpg|jpeg|PNG|JPG|JPEG)" --include="*.qmd" . \
  | sort -u > "$refs_file"

removed_count=0
removed_size=0
while IFS= read -r -d '' file; do
  rel="${file#./}"
  if ! grep -qixF "$rel" "$refs_file"; then
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
    echo "  supprimé : $rel ($((size / 1024)) Ko)"
    rm -f "$file"
    removed_count=$((removed_count + 1))
    removed_size=$((removed_size + size))
  fi
done < <(find "$IMAGES_DIR" -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) -print0)

echo "-> ${removed_count} image(s) orpheline(s) supprimée(s), $((removed_size / 1024)) Ko libérés."

echo "== Passe 1 : redimensionnement + compression =="

before_total=$(du -sk "$IMAGES_DIR" | cut -f1)

while IFS= read -r -d '' file; do
  before=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")

  case "$file" in
    *.png|*.PNG)
      magick "$file" -resize "${MAX_DIM}x${MAX_DIM}>" -strip "$file"
      pngquant --quality=65-90 --skip-if-larger --strip --force --output "$file" "$file" 2>/dev/null || true
      oxipng -o4 --strip safe -q "$file"
      ;;
    *.jpg|*.jpeg|*.JPG|*.JPEG)
      magick "$file" -resize "${MAX_DIM}x${MAX_DIM}>" -strip -quality 85 "$file"
      ;;
  esac

  after=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
  if [ "$after" -lt "$before" ]; then
    saved=$(( (before - after) * 100 / before ))
    echo "  $file : $((before / 1024)) Ko -> $((after / 1024)) Ko (-${saved}%)"
  fi
done < <(find "$IMAGES_DIR" -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' \) -print0)

after_total=$(du -sk "$IMAGES_DIR" | cut -f1)

echo "== Résumé =="
echo "images/ : $((before_total / 1024)) Mo -> $((after_total / 1024)) Mo"
