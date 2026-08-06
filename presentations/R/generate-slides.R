# Helpers pour générer les diapositives d'exercices à partir des fichiers
# exe/<thème>/NN.Rmd déjà utilisés par le manuel, sans dupliquer leur contenu.
#
# Ces fichiers ont systématiquement la même forme, sans heading interne :
#   ::: {.Exercise data-latex=""}
#   ...
#   :::
#
#   ::: {.Answer data-latex=""}
#   ...
#   :::
#
# Certains exercices enveloppent en plus le bloc .Exercise dans un
# .Exercise-container (6 deux-points) qui ajoute du contenu (typiquement un
# tableau avec des images) APRÈS la fermeture du bloc .Exercise mais avant la
# fermeture du container - ce contenu fait partie de l'énoncé et doit être
# inclus aussi.
#
# presentations/exe et presentations/images sont des liens symboliques vers
# ../exe et ../images, donc les chemins bruts "images/..." utilisés dans ces
# fichiers résolvent correctement sans aucune modification.

# Les fences de div pandoc (`:::`) peuvent être imbriquées (ex. un
# .multicols ou un .center à l'intérieur d'un .Exercise), et pandoc autorise
# d'utiliser plus de deux-points sur la fence englobante (`::::::`, voire
# `:::::::::`) pour lever l'ambiguïté - certains fichiers exe/**/NN.Rmd
# utilisent effectivement 6 ou 9 deux-points directement sur .Exercise/.Answer
# eux-mêmes lorsqu'ils contiennent un .multicols. Une simple recherche du
# premier ":::" isolé (comme avant) referme donc le mauvais niveau. On calcule
# à la place la fermeture correspondante via une pile, comme le fait pandoc.
fence_len <- function(line) {
  m <- regmatches(trimws(line), regexpr("^:{3,}", trimws(line)))
  if (length(m) == 0) NA_integer_ else nchar(m)
}

is_opening_fence <- function(line) grepl("^:{3,}\\s*\\{", trimws(line))
is_closing_fence <- function(line) grepl("^:{3,}\\s*$", trimws(line))

# Retourne l'indice de la ligne qui referme la fence ouverte à `open_idx`.
# Pandoc apparie les fences par simple pile (LIFO) : n'importe quelle ligne de
# fermeture (3 deux-points ou plus, sans attributs) referme le div ouvert le
# plus récemment, sans comparer le nombre de deux-points - vérifié en testant
# `exe/liaisons/30.Rmd` (ouverture à 9 deux-points, fermeture à 6) directement
# avec `pandoc -t html`, qui referme correctement les deux div malgré l'écart.
find_fence_close <- function(lines, open_idx) {
  depth <- 1
  i <- open_idx + 1
  n <- length(lines)
  while (i <= n) {
    line <- lines[i]
    if (is_opening_fence(line)) {
      depth <- depth + 1
    } else if (is_closing_fence(line)) {
      depth <- depth - 1
      if (depth == 0) return(i)
    }
    i <- i + 1
  }
  NA_integer_
}

# Retourne le contenu du bloc .Exercise ou .Answer d'un fichier, sous forme de
# chaîne de caractères (ou NULL si le bloc n'existe pas dans ce fichier - ce
# n'est pas une erreur, certains exercices n'ont pas de bloc .Answer écrit).
extract_part <- function(path, part = c("Exercise", "Answer")) {
  part <- match.arg(part)
  if (!file.exists(path)) {
    warning(sprintf("Fichier introuvable : %s", path))
    return(NULL)
  }
  lines <- readLines(path, encoding = "UTF-8", warn = FALSE)

  open_idx <- grep(sprintf("^:{3,}\\s*\\{\\.%s[ }]", part), lines)
  if (length(open_idx) == 0) {
    return(NULL)
  }
  open_idx <- open_idx[1]

  close_idx <- find_fence_close(lines, open_idx)
  if (is.na(close_idx)) {
    warning(sprintf("Bloc .%s non fermé dans %s", part, path))
    return(NULL)
  }

  content <- lines[(open_idx + 1):(close_idx - 1)]

  # Contenu additionnel entre la fin du .Exercise et la fin du container,
  # s'il y en a un (uniquement pertinent pour la partie Exercise).
  if (part == "Exercise" && open_idx > 1) {
    container_open <- grep("^:{3,}\\s*\\{\\.Exercise-container\\b", lines[seq_len(open_idx - 1)])
    if (length(container_open) > 0) {
      container_open <- container_open[length(container_open)]
      container_close <- find_fence_close(lines, container_open)
      if (!is.na(container_close) && container_close > close_idx + 1) {
        content <- c(content, lines[(close_idx + 1):(container_close - 1)])
      }
    }
  }

  paste(content, collapse = "\n")
}

# Repère, dans l'ordre, tous les `child=c('exe/<thème>/NN.Rmd')` d'un chapitre
# du manuel, et la position de la section "Exercices supplémentaires", pour
# émettre une diapo Exercice + une diapo verticale Correction par exercice
# (avec une diapo de séparation avant les exercices supplémentaires), numérotés
# comme dans le PDF (chapitre.numéro, ex. "Exercice 6.5").
generate_exercise_slides <- function(chapter_path, chapter_num) {
  if (!file.exists(chapter_path)) {
    warning(sprintf("Chapitre introuvable : %s", chapter_path))
    return(invisible(NULL))
  }
  lines <- readLines(chapter_path, encoding = "UTF-8", warn = FALSE)

  supp_idx <- grep("^##\\s+Exercices suppl", lines)
  supp_idx <- if (length(supp_idx) > 0) supp_idx[1] else Inf

  child_idx <- grep("child\\s*=\\s*c\\(['\"][^'\"]+['\"]\\)", lines)

  divider_emitted <- FALSE
  ex_num <- 0

  for (line_no in child_idx) {
    exe_path <- sub(".*child\\s*=\\s*c\\(['\"]([^'\"]+)['\"]\\).*", "\\1", lines[line_no])

    if (!divider_emitted && line_no > supp_idx) {
      cat("\n## Exercices supplémentaires\n\n")
      divider_emitted <- TRUE
    }

    ex_num <- ex_num + 1
    num_label <- sprintf("%s.%d", chapter_num, ex_num)

    exercise_content <- extract_part(exe_path, "Exercise")
    if (is.null(exercise_content)) {
      warning(sprintf("Aucun bloc .Exercise dans %s - diapo ignorée", exe_path))
      next
    }
    cat(sprintf("\n## Exercice %s\n\n", num_label))
    cat(exercise_content)
    cat("\n")

    answer_content <- extract_part(exe_path, "Answer")
    if (!is.null(answer_content)) {
      cat(sprintf("\n### Correction %s\n\n", num_label))
      cat(answer_content)
      cat("\n")
    }
  }
}
