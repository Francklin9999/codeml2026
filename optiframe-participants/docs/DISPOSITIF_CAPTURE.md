# Dispositif de capture

> Retour au [`README`](../README.md). Le montage à remettre au jury est la [section 3](#3-montage-en-6-étapes) : elle tient sur une page.

## 1. Matériel

| Élément | Remarque |
|---|---|
| Feuille de référence imprimée | [`board_A4.pdf`](../rig/out/board_A4.pdf) ou [`board_Letter.pdf`](../rig/out/board_Letter.pdf), papier ordinaire, fenêtre découpée |
| Écran blanc | Ordinateur portable ou tablette, ouvert sur la page de rétro-éclairage de l'app (`lightbox.html`) |
| Téléphone | Chrome (Android) ou Safari (iOS), app ouverte par le QR code |
| Feuille de papier calque | Seulement en cas de moiré (section 6) |
| Pied à coulisse | Pour vérifier la règle imprimée, une fois par imprimante |
| Ciseaux ou cutter | Pour découper la fenêtre |

La feuille : zone imprimée de 180 × 150 mm, 18 marqueurs carrés de 15 mm autour d'une fenêtre de 80 × 65 mm, une règle de 100 mm, des repères de ligne guide à mi-hauteur de la fenêtre, les mentions « HAUT », « ŒIL DROIT : nez de ce côté » (à droite) et « ŒIL GAUCHE : nez de ce côté » (à gauche).

## 2. Impression de la feuille

1. Imprimer à **100 %** (« taille réelle »), jamais « ajuster à la page ». A4 ou Lettre : le dessin est le même.
2. Mesurer la règle imprimée au pied à coulisse. Elle doit mesurer **100 mm**.
3. Découper la fenêtre le long du trait.

Si la règle mesure autre chose que 100 mm :

| Mesure | Geste |
|---|---|
| Entre 97 et 103 mm | Enregistrer la valeur : `python rig/set_print_scale.py <valeur mesurée>`, puis reconstruire et remettre l'app en ligne. L'app utilise alors la taille réelle de la feuille. |
| En dehors | Le réglage d'impression est faux (mise à l'échelle active). Corriger et réimprimer : la valeur est refusée. |

Le jour de l'évaluation, la feuille du kit est déjà vérifiée. Valeur mesurée sur la feuille du kit : `À COMPLÉTER` mm.

<div style="page-break-before: always"></div>

## 3. Montage en 6 étapes

1. **Écran.** Sur l'ordinateur ou la tablette, ouvrir l'app, toucher « Comment installer le dispositif » puis « Page de rétro-éclairage ». Toucher « Plein écran ». Luminosité au maximum.
2. **Feuille.** Coucher l'écran à plat. Poser la feuille dessus, le mot « HAUT » en haut, la fenêtre au milieu de l'écran.
3. **Téléphone.** Scanner le QR code. Toucher « Verre gauche » ou « Verre droit ».
4. **Verre.** Poser le verre au centre de la fenêtre, face bombée vers le haut, aligné sur les repères de la ligne guide, le côté du nez vers l'étiquette de l'œil choisi.
5. **Photo.** Tenir le téléphone à plat, 35 à 45 cm au-dessus, toute la feuille dans l'image. Toucher « Prendre la photo ». Refaire jusqu'à 3 photos en bougeant un peu le téléphone, sans toucher le verre.
6. **Résultat.** Lire A, B et le périmètre, toucher « Valider ». Recommencer à l'étape 3 pour l'autre verre, puis toucher « Créer la monture ».

Si l'app affiche une phrase au lieu d'une mesure, faire ce qu'elle dit et reprendre la photo.

<div style="page-break-after: always"></div>

## 4. Pose du verre

- **Face bombée vers le haut** (face creuse contre la feuille) : le bord du verre touche la feuille, là où l'échelle est connue.
- **Aligné sur la ligne guide :** l'horizontale du verre suit les deux repères à mi-hauteur de la fenêtre. A et B sont mesurés selon les axes de la feuille ; un verre tourné donne des valeurs trop grandes. L'app avertit quand le verre semble posé de travers.
- **Côté nez selon l'œil :** verre droit, côté du nez à droite de la fenêtre ; verre gauche, côté du nez à gauche. L'écran de l'app montre une flèche.
- Le verre ne doit pas dépasser de la fenêtre. On ne marque jamais un verre.

## 5. Tenue du téléphone

- À plat, parallèle à la feuille, 35 à 45 cm au-dessus.
- **Toute la feuille visible**, marqueurs compris ; rien ne cache les marqueurs (doigts, ombre de la main).
- Flash éteint. Toucher l'écran pour faire la mise au point, rester immobile au déclenchement.
- Utiliser la caméra de l'app ou le fichier d'origine. Une photo passée par WhatsApp est recompressée et inutilisable.

## 6. Dépannage

| Problème | Geste |
|---|---|
| « Je ne vois pas la feuille de référence en entier. » | Reculer un peu, cadrer toute la feuille, dégager les marqueurs. |
| « La feuille est trop inclinée. » | Tenir le téléphone bien à plat au-dessus de la feuille. Vérifier que la feuille n'est pas gondolée. |
| « La photo est floue. » | Toucher l'écran pour la mise au point, tenir le téléphone immobile, nettoyer l'objectif. |
| « Je ne trouve pas le verre. » | Poser le verre au centre de la fenêtre. Vérifier que l'écran est allumé sous la feuille, luminosité au maximum. |
| « Le verre dépasse de la fenêtre. » | Recentrer le verre. |
| « Il y a un reflet sur le verre. » | Éteindre le flash, changer légèrement d'angle, s'éloigner d'une lampe placée au-dessus. |
| « Les photos ne donnent pas la même mesure. » | Reprendre les photos sans bouger ni le verre ni la feuille. |
| « Le verre semble posé de travers. » | Réaligner le verre sur les repères de la ligne guide. |
| « L'accès à la caméra est refusé. » | Toucher « Importer une photo » et choisir une photo prise avec l'appareil photo du téléphone. |
| « Le chargement a échoué. » | Vérifier la connexion, recharger la page. Si le téléphone garde une ancienne version : ajouter `?nosw=1` à l'adresse. |
| Rayures ondulées (moiré) dans la fenêtre | Glisser une feuille de papier calque entre l'écran et la feuille imprimée ; ou reculer un peu le téléphone. |
| Écran trop faible dans une salle très éclairée | Luminosité au maximum, baisser la lumière de la salle. Secours : une tablette ; ou la lampe d'un téléphone tournée vers le haut derrière un papier calque, sous la fenêtre ; ou la feuille collée sur une vitre à la lumière du jour. |
| L'écran se met en veille | Désactiver la mise en veille de l'appareil ; toucher de nouveau « Plein écran ». |
| Éclairage inégal de l'écran | Garder le verre près du centre de la fenêtre. |
| La règle imprimée ne mesure pas 100 mm | Section 2. |

Contraste réel du bord du verre et moiré sur de vrais écrans : `À COMPLÉTER`. Temps de montage par une personne qui découvre le dispositif : `À COMPLÉTER`.
