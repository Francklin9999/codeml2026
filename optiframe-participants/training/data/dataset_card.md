# Fiche du jeu de données OptiFrame (segmentation de verres)

Partie synthétique remplie (2026-10-04, modèle v2 livré). Partie réelle à compléter après la prise de vue : À COMPLÉTER.

## Contenu

| Élément | Valeur |
|---|---|
| Verres réels distincts | À COMPLÉTER |
| Positions par verre | À COMPLÉTER |
| Photos réelles étiquetées (après rejets) | À COMPLÉTER |
| Groupes rejetés (support bougé, marqueurs absents) | À COMPLÉTER |
| Échantillons synthétiques | 24 159 en entraînement (12 000 `synth_rig.py` toutes scènes, 2 000 table mouchetée ou rétro-éclairage ou papier, 3 000 tables mouchetées, 1 500 verres montés, 1 000 fenêtres vides, 1 200 verres qui dépassent, 1 500 rétro-éclairage et papier, 1 959 `synth.py`) ; 800 en validation (600 toutes scènes, 200 tables) ; 1 500 + 300 tables + 200 verres qui dépassent en test. Graines distinctes pour chaque jeu |
| Taille des images | 800 x 650 px (fenêtre 80 x 65 mm, 10 px/mm) |
| Images / masques | `images/*.jpg`, `masks/*.png` (255 = verre) |

## Conditions de prise de vue

`easy` (rétroéclairage), `room`, `lampL`, `lampT`, `lampR`, `flash`, `pattern`, `colour` (voir `capture_protocol.md`). Nombre de photos par condition : À COMPLÉTER.

## Découpage

Par identifiant de verre (`split.py`), jamais par image : train / val / test environ 70 / 15 / 15. Les échantillons synthétiques sont uniquement dans train. Verres par découpage : train À COMPLÉTER, val À COMPLÉTER, test À COMPLÉTER.

## Sources

- Photos réelles : prises par l'équipe avec le matériel décrit dans le protocole. Appareil(s) : À COMPLÉTER.
- Masques réels : calculés automatiquement (aplat de fond, chapeau noir, Otsu, remplissage depuis le bord, plus grande composante) sur la prise `easy` puis copiés aux autres prises de la même position. Contrôle visuel : À COMPLÉTER images revues, À COMPLÉTER % correctes.
- Échantillons synthétiques : `synth_rig.py` (la fenêtre telle que le dispositif la montre : rétro-éclairage, papier, table mouchetée, verre teinté, verre monté, fenêtre vide, verre qui dépasse ; bord du verre faible, irrégulier ou interrompu, reflets, poussières, moiré, chaîne du téléphone) et `synth.py`, formes superellipse, rectangle arrondi, aviateur, oeil de chat. Fonds : tous procéduraux, aucune image externe.

## Licences

- Photos et masques réels : propriété de l'équipe, licence de diffusion À COMPLÉTER.
- Images de fond : À COMPLÉTER (uniquement CC0 ou images de l'équipe).
- Outils : numpy (BSD-3-Clause), opencv-contrib-python (Apache-2.0), pytest (MIT).

## Vie privée

Aucun visage, aucun nom, aucune ordonnance ne figure dans les images. Les verres sont photographiés seuls sur la feuille de référence. Vérification faite par : À COMPLÉTER.

## Limites connues

Précision de la segmentation sur des verres réels inconnus : À MESURER (À COMPLÉTER). Le masque classique suppose un bord de verre sombre sur la prise rétroéclairée ; les verres très teintés ou sans bord visible peuvent être rejetés.
