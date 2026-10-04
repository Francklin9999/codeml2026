# Pas à pas : une photo et ses images intermédiaires

> Retour au [`README`](../README.md). L'app montre les mêmes images pour la dernière photo mesurée : écran « Pas à pas », avec la durée de chaque étape sur le téléphone utilisé.

Les images ci-dessous sont à produire avec un vrai verre sur le dispositif de capture. Emplacements réservés dans `docs/img/` ; tant qu'un fichier n'existe pas, la ligne reste `À COMPLÉTER`.

| | |
|---|---|
| Verre photographié | `À COMPLÉTER` (identifiant, description) |
| Téléphone | `À COMPLÉTER` |
| Valeurs au pied à coulisse | A `À COMPLÉTER` mm, B `À COMPLÉTER` mm |

## 1. Référence détectée

Image : `docs/img/pas-a-pas-1.png` (`À COMPLÉTER`)

La photo d'origine, avec les marqueurs de la feuille tracés en vert là où le calcul les place.
Si les carrés verts recouvrent les marqueurs imprimés, la feuille est bien repérée ; avec moins de 4 marqueurs, l'app refuse la photo.

## 2. Image redressée

Image : `docs/img/pas-a-pas-2.png` (`À COMPLÉTER`)

La fenêtre de 80 × 65 mm vue de dessus, à 10 pixels par millimètre (800 × 650 pixels).
L'échelle vient des marqueurs et de la règle vérifiée au pied à coulisse ; une photo trop inclinée ou floue est refusée à cette étape.

## 3. Masque du verre

Image : `docs/img/pas-a-pas-3.png` (`À COMPLÉTER`)

En blanc, la surface que l'app attribue au verre ; la légende dit quelle méthode l'a produite (« classique » ou « modèle »).
La méthode classique cherche le bord sombre du verre rétro-éclairé ; elle refuse un reflet trop fort ou un verre qui dépasse de la fenêtre.

## 4. Contour

Image : `docs/img/pas-a-pas-4.png` (`À COMPLÉTER`)

Le contour mesuré, tracé sur l'image redressée : c'est l'image de contrôle.
Le contour est une liste de 720 points en millimètres, placée sur le bord extérieur du verre et calculée à une fraction de pixel (justesse sur un vrai verre : `À COMPLÉTER`).

## 5. Mesures

Image : `docs/img/pas-a-pas-5.png` (`À COMPLÉTER`, écran « résultat »)

A et B sont la largeur et la hauteur du rectangle qui enserre le contour, côtés parallèles aux axes de la feuille (système boxing) ; le périmètre est la longueur du contour.
Avec plusieurs photos, l'app affiche aussi l'écart entre elles sur A et sur B.

| Mesure | App | Pied à coulisse | Écart |
|---|---|---|---|
| A (mm) | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| B (mm) | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| Périmètre (mm) | `À COMPLÉTER` | sans objet | sans objet |

## Et ensuite

Le même contour sert au tracé SVG à l'échelle 1:1 et à la monture : chaque cercle est le contour décalé du jeu, relié à l'autre par le pont. Le montage du dispositif est décrit dans [`DISPOSITIF_CAPTURE.md`](DISPOSITIF_CAPTURE.md).
