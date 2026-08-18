---
description: Génère la présentation PowerPoint minimaliste d'un chapitre du cours de chimie générale
argument-hint: <numéro-ou-slug-du-chapitre>
---

# Génère les diapositives d'un chapitre

Chapitre demandé : $ARGUMENTS

Produis le fichier `.pptx` minimaliste de ce chapitre, en suivant exactement le pipeline et
les conventions déjà en place pour `10-introduction.qmd` (référence de style :
`slides/content/introduction.yml`).

## Étapes

1. **Identifier le fichier chapitre** correspondant à `$ARGUMENTS` (numéro, slug ou nom
   partiel) parmi les fichiers `NN-slug.qmd` à la racine du dépôt.
2. **Explorer sa structure** :
   - `./.venv/bin/python scripts/slides/parse_chapter.py <chapitre>.qmd` donne l'outline
     (titres, divs `.objectives`/`.tcolorbox`/`.Exercise`/`.Answer`, tableaux, exercices).
   - Lire aussi directement les fichiers `exe/<slug>/*.qmd` du chapitre pour le texte
     complet des exercices et de leurs corrigés (le parseur ne les distingue pas
     toujours assez finement pour les recopier tel quel).
3. **Vérifier l'ordre exact des exercices dans la source** avant de rédiger quoi que ce
   soit : `grep -n "include exe/<slug>" <chapitre>.qmd` donne la liste ordonnée des
   fichiers d'exercices telle qu'elle apparaît réellement dans le chapitre (l'ordre des
   fichiers `exe/<slug>/NN.qmd` n'est **pas** forcément l'ordre numérique de leurs noms —
   ne jamais supposer, toujours vérifier par ce grep). Cet ordre doit être respecté
   exactement dans le `.yml`, car la numérotation des exercices (étape 4) est calculée à
   partir de la position des diapositives `type: exercise` dans le fichier.
4. **Rédiger le plan de contenu** `slides/content/<slug>.yml`, en respectant les
   conventions déjà en place (voir `slides/content/introduction.yml` pour des exemples
   concrets) :
   - `type: title` → diapositive de titre du chapitre.
   - `type: objectives` → diapositive "Objectifs" (contenu du div `.objectives`).
   - `type: content` → une diapositive par section/sous-section, dans l'ordre du texte,
     avec un `title:` (nom de la section) et un contenu réduit à l'essentiel (condense
     les paragraphes en quelques phrases/mots-clés — ne recopie jamais un paragraphe
     complet).
   - `type: exercise` puis `type: answer` **consécutifs** pour chaque exercice rencontré
     dans le corps du texte, **dans l'ordre exact de l'étape 3**. L'énoncé et le corrigé
     restent complets (ce n'est pas de la prose à condenser). Le titre affiché
     ("Exercice C.N" / "Corrigé C.N") est **calculé automatiquement** par
     `build_deck.py` — ne jamais l'écrire à la main. Un champ optionnel `label:` sur la
     diapositive `exercise` ajoute un sous-titre descriptif après le numéro (ex.
     `label: "Un lingot métallique"` → "Exercice 1.15 — Un lingot métallique") ; ne pas en
     mettre sur `answer`, il reprend juste le numéro.
   - `type: divider` avec `title: "Exercices supplémentaires"` juste avant les exercices
     de la section `## Exercices supplémentaires`, puis les paires exercice/corrigé
     supplémentaires dans l'ordre du fichier — la numérotation continue sans se
     réinitialiser (comme dans le PDF/HTML).
   - Une diapositive `type: content` avec `title: "Résumé"` en fin de chapitre.
   - `items:` est une liste où chaque élément est soit une chaîne simple (niveau 0), soit
     `{text: "...", level: 1}` pour un sous-point indenté (ex. les variantes a/b/c/d d'un
     exercice, ou les exemples sous une définition) — ceci pilote la vraie hiérarchie de
     paragraphe du placeholder, pas un alignement par espaces (qui casserait dès qu'un
     thème change de police).
   - Pour toute formule LaTeX non triviale (fractions, dérivations multi-lignes, flèches
     `\underset`, `\begin{aligned}`…) ou tout tableau Markdown du cours, utilise un bloc
     `renders:` avec `kind: math` ou `kind: table` et le LaTeX correspondant. Pour des
     exposants/indices simples, écris directement en unicode (`10⁻³`, `H₂O`, `·`) plutôt
     que de générer une image inutile.
5. **Construire le fichier** :
   `./.venv/bin/python scripts/slides/build_deck.py slides/content/<slug>.yml`
   → produit `slides/<numero>-<slug>.pptx`.
6. **Vérifier avant de présenter** : un contrôle géométrique rapide (aucune forme ne doit
   déborder du cadre 13.333×7.5in), qu'aucun run de placeholder n'a de police/taille/
   couleur codée en dur (ce serait un signe qu'une zone de texte libre a été utilisée par
   erreur au lieu d'un placeholder), et que les titres `Exercice C.1` … `Exercice C.N`
   suivent une séquence continue et complète sans trou ni doublon.
7. **Ouvrir le fichier** (`open slides/<numero>-<slug>.pptx`) et résume en 3–4 lignes ce
   qu'il contient (nombre de diapositives, nombre de paires exercice/corrigé, choix de
   condensation notables) pour que l'utilisateur puisse valider avant de passer au
   chapitre suivant.

Ne traite qu'un seul chapitre par appel de cette commande.
