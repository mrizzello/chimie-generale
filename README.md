## Support du cours de chimie générale

Ce dépôt contient le support du cours de chimie générale (niveau gymnasial). Le manuel couvre le programme de la maturité gymnasiale, de l'introduction à la chimie (états de la matière, structure atomique, tableau périodique, liaisons chimiques) jusqu'à la thermodynamique, en passant par la stœchiométrie, les équilibres, les acides-bases et l'électrochimie. Chaque chapitre comprend des exercices corrigés. La version publiée est consultable sur [chimiegenerale.ch](https://chimiegenerale.ch/).

### Licence

Shield: [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

Cet ouvrage est placé sous licence Creative Commons
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

### Description technique

Le contenu est rédigé sur la base de [Quarto](https://quarto.org/), un système de publication scientifique open-source. En se basant sur le contenu rédigé au format Markdown/knitr, Quarto permet de générer le manuel dans plusieurs formats de sortie, notamment HTML et LaTeX/PDF.

### Générer un exemplaire

1. Installer [Quarto CLI](https://quarto.org/docs/get-started/) ainsi qu'une distribution TeX Live (`quarto install tinytex`) pour la sortie PDF.
2. Depuis la racine du dépôt, lancer :

   ```sh
   quarto render
   ```

   Les fichiers générés sont placés dans `_book/`.

   Pour prévisualiser le manuel en HTML avec rechargement automatique pendant la rédaction :

   ```sh
   quarto preview
   ```

### Champ d'évaluation

Le script `scripts/evaluations/champ_evaluation.py` génère le « champ d'évaluation » d'un ou plusieurs chapitres à partir de leur bloc d'objectifs (`::: {.objectives data-latex=""}`).

```sh
python3 scripts/evaluations/champ_evaluation.py 130 140
```

Chaque argument identifie un chapitre par son numéro de préfixe (ex. `130`), son slug (ex. `stoechiometrie`) ou une sous-chaîne unique du nom de fichier. Le document généré est écrit dans `fields/` (dossier gitignoré).
