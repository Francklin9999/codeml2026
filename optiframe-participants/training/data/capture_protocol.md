# Protocole de capture : photos appariées

But : des photos de verres avec un masque exact, sans aucun détourage manuel. Le téléphone ne bouge pas entre les prises d'une même position, donc le masque de la prise facile vaut pour toutes les autres.

## Matériel

- Téléphone sur un support fixe (pied ou potence), au-dessus de la feuille de référence imprimée, objectif à l'aplomb de la fenêtre. Les 4 marqueurs ArUco et la fenêtre doivent être entièrement visibles.
- Feuille de référence sur un écran blanc (rétroéclairage), plus : lampe de bureau, flash du téléphone, une page à motif (bois, tissu, texte) et un écran de couleur (rose, bleu).
- 15 verres différents (ne jamais mélanger deux verres sous le même identifiant).

## Séquence pour chaque position du verre

On pose le verre dans la fenêtre. On ne touche plus ni le support, ni la feuille, ni le verre jusqu'à la fin de la séquence.

1. `easy` : écran blanc allumé, rétroéclairage seul (prise facile, source du masque). Toujours en premier.
2. `room` : écran éteint, lumière de la pièce seule.
3. `lamp1`, `lamp2`, `lamp3` : lampe de bureau depuis trois directions (gauche, droite, haut).
4. `flash` : flash du téléphone.
5. `pattern` : page à motif glissée sous la feuille.
6. `color` : écran en couleur (rose ou bleu).

Puis on déplace ou on tourne le verre (6 positions par verre) et on recommence. Cible : 15 verres x 6 positions x 8 conditions = 720 photos, environ 2 h de prise de vue.

## Nommage

`<lensId>_<pos>_<cond>.jpg`, par exemple `L07_3_lamp2.jpg`. `lensId` : lettre et numéro du verre (pas de tiret bas dedans), `pos` : 1 à 6, `cond` : `easy` pour la prise 1, sinon un des mots ci-dessus (sans tiret bas). Photos en JPEG, orientation EXIF conservée, même résolution pour toute la séquence.

## Contrôles avant de partir

- Les 4 marqueurs sont nets et visibles sur chaque photo (sinon la photo est écartée).
- Aucune photo faite avec le support déplacé : `autolabel.py` rejette tout le groupe si les coins de la fenêtre bougent de plus de 3 px par rapport à la prise `easy`.
- Pas de visage, pas de nom, pas d'ordonnance dans le champ.

## Traitement

```
cd training/data
python autolabel.py <dossier_photos> --spec ../../app/public/board_spec.json --qc 50
python synth.py --n 2000 --bg-dir <dossier_fonds>
python split.py ../_local/real/index.csv ../_local/synth/index.csv --out ../_local/split.csv
```

Les sorties vont dans `training/_local/` (ignoré par git). Regarder les images de `qc/` (contour du masque sur une prise difficile) : au moins 95 % doivent être correctes, sinon vérifier que le support n'a pas bougé. Les groupes écartés sont listés avec la raison dans `rejected.csv`.

## Option : enseignant SAM (documentation seulement, aucun code fourni)

Si le masque classique échoue sur certaines positions (verres teintés, bords très fins), on peut passer un SAM complet (ViT-B ou ViT-H) hors ligne sur les photos rectifiées, avec une boîte autour du verre comme invite, vérifier les masques à l'œil, puis les utiliser comme étiquettes d'entraînement du petit modèle (stratégie 5, section 4.4). SAM reste un outil d'étiquetage : il n'est pas embarqué dans l'application.
