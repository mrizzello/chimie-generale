# Illustrations SVG

Conventions communes pour les illustrations du livre redessinées en SVG (première : `images/timeline-cosmos.svg`).

## Fichier

- SVG écrit à la main, lisible et commenté, un `<g>` commenté par partie de la figure.
- `viewBox` uniquement, sans `width`/`height` fixes : la taille est donnée par le `.qmd` (`width="100%"`).
- Format paysage, largeur `1400` dans le `viewBox` (hauteur selon le contenu, ex. `0 0 1400 840`) pour une figure pleine largeur.
- Fond blanc explicite (`<rect>` blanc en premier élément) : le livre n'a pas de mode sombre.
- Pictogrammes définis une seule fois dans `<defs>` et réutilisés avec `<use>`. Ils sont dessinés à leur taille finale, sans `transform` sur l'élément de `<defs>` lui-même : un minifieur (type SVGO) qui « inline » les `<use>` perd ces transformations (un pictogramme réduit par `scale()` réapparaît à sa taille brute). Le `transform` se met sur le `<use>`.
- Pas de filtres, de masques complexes, de polices externes, d'images bitmap intégrées ni de CSS externe : `rsvg-convert` doit rendre le fichier exactement comme le navigateur.

## Typographie

- `font-family="Helvetica, Arial, sans-serif"` sur l'élément `<svg>` racine. Les textes restent du texte, ils ne sont pas vectorisés.
- Tailles dans un `viewBox` de 1400 de large, affiché sur environ 16 cm en PDF :

| usage | taille |
| :--- | :---: |
| titre de l'axe | 26 |
| libellés des jalons | 24 |
| graduations, bandes | 22 |
| textes de l'encart | 20–22 |
| notes secondaires | 18 |

La taille minimale est 18, soit environ 6 pt une fois imprimé.

## Palette

| rôle | couleur | variante foncée (texte) |
| :--- | :---: | :---: |
| encre (axes, textes) | `#1F2A44` | — |
| pictogrammes (monochromes) | `#2F6DB5` | teinte claire par `fill-opacity` |
| texte secondaire | `#5B6478` | — |
| traits légers, grille | `#C9CED8` | — |
| primordiale / accent chaud | `#E9A23B` | `#9A5B00` |
| stellaire | `#E2553F` | `#A3281A` |
| explosive | `#7C4DBA` | `#4E2785` |
| interstellaire | `#5A9E2F` | `#3B6B1C` |

- Frises chronologiques (inspirées des infographies « horizontal timeline ») : chevrons de même largeur dans une rampe de bleus, du plus ancien (sombre) au plus récent (clair) : `#1F1F5C` `#2C3A8C` `#3552B0` `#3A6CC8` `#2F86C9` `#1F9BC0`. Date en blanc gras dans le chevron, pastille ronde de la couleur du chevron avec pictogramme blanc, titre en gras et une ligne de description, en alternance au-dessus et en dessous.
- Les zones colorées utilisent la couleur avec `fill-opacity="0.18"`, un liseré plein à gauche et le texte dans la variante foncée.
- Traits : axe principal 4, jalons 2.5, pictogrammes 2.5–3, avec des extrémités arrondies (`stroke-linecap="round"`).

## Intégration

- Dans le `.qmd` : `![Légende](images/nom.svg){#fig-nom width="100%"}`.
- HTML : le SVG est servi tel quel.
- PDF (xelatex) : Quarto convertit le SVG en PDF avec `rsvg-convert`. Celui-ci doit être installé en local (`brew install librsvg`) et dans la CI (étape `brew install librsvg` de `.github/workflows/renderbook.yml`).
- Diapositives : `scripts/slides/build_deck.py` convertit les `.svg` en PNG (cache dans `slides/_assets/<slug>/`).

## Vérification

- Aperçu navigateur : `open images/nom.svg`.
- Aperçu du rendu PDF : `rsvg-convert -w 2000 images/nom.svg -o /tmp/apercu.png`.
- Ne rendre que le chapitre concerné, par exemple `quarto render 40-historique.qmd --to html`.
