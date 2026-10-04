# Données et IA

> Retour au [`README`](../README.md). Licences des bibliothèques et du modèle pré-entraîné : [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md).

**État au moment d'écrire ce document.** Les outils de données (`training/data/`), d'entraînement (`training/model/`) et le chargement du modèle dans le navigateur (`app/src/vision/segmentModel.ts`) sont écrits et testés sur des données synthétiques. **Aucune photo réelle n'a encore été collectée et aucun modèle n'a été entraîné.** Tous les tableaux ci-dessous sont donc vides : ils se remplissent avec la sortie des scripts, jamais de mémoire.

## 1. Le problème des annotations

Entraîner un modèle de segmentation demande, pour chaque photo, le contour exact du verre. Or :

- aucune donnée n'est fournie, et aucun jeu public ne contient de verres de lunettes détourés au dixième de millimètre ;
- un verre transparent se détoure mal à la main : le bord est fin, les reflets trompent l'œil, et une erreur de quelques pixels est déjà une erreur de mesure ;
- en 24 heures, détourer des centaines de photos à la main n'est pas possible.

## 2. La capture appariée

Idée : le téléphone est fixé sur un support, le verre ne bouge pas, et on prend plusieurs photos de la **même scène** sous des éclairages différents.

1. Une photo **facile** (`easy`) : feuille sur l'écran blanc, verre rétro-éclairé. Le bord est sombre sur fond clair, et le contour s'obtient sans IA.
2. Des photos **difficiles** de la scène identique : lumière de la pièce seule, lampe de bureau depuis trois directions, flash, page à motif sous la feuille, écran de couleur.

Comme rien n'a bougé, le masque calculé sur la photo facile est exact pour toutes les photos difficiles du même groupe. **Aucun détourage manuel.**

`training/data/autolabel.py` fait ce travail : il redresse chaque photo avec les marqueurs de la feuille (fenêtre de 80 × 65 mm à 10 px/mm, soit 800 × 650 pixels), calcule le masque sur la photo facile, le copie aux autres photos du groupe, et **rejette tout le groupe** si les coins de la fenêtre ont bougé de plus de 3 pixels (le support a été déplacé). Il écrit aussi des images de contrôle (contour du masque sur une photo difficile) pour une relecture visuelle par échantillon. Protocole de prise de vue : `training/data/capture_protocol.md`.

Les photos se prennent avec la page de collecte de l'app (`collect.html`, lien « Collecte de données (équipe) » en bas de l'écran d'accueil) : elle nomme les fichiers, garde les fichiers d'origine, enregistre les valeurs au pied à coulisse et exporte le tout en ZIP. Liste complète de ce qui est à collecter : [`COLLECTE_DONNEES.md`](COLLECTE_DONNEES.md).

| Jeu réel | Valeur |
|---|---|
| Verres distincts | `À COMPLÉTER` |
| Positions par verre | `À COMPLÉTER` |
| Conditions d'éclairage par position | `À COMPLÉTER` |
| Photos étiquetées après rejets | `À COMPLÉTER` |
| Groupes rejetés (support bougé, marqueurs absents) | `À COMPLÉTER` |
| Masques relus à l'œil, et part jugée correcte | `À COMPLÉTER` |
| Téléphone(s) | `À COMPLÉTER` |

Noms des conditions : ceux de la page de collecte, `easy`, `room`, `lampL`, `lampT`, `lampR`, `flash`, `pattern`, `colour`. Le protocole et la fiche du jeu de données ont été alignés sur eux. `autolabel.py` accepte n'importe quel nom ; seul `easy` a un rôle.

## 3. Les images synthétiques

Deux générateurs, tous deux sans aucune annotation : le masque et les dimensions A et B sont connus exactement, puisque c'est nous qui dessinons le verre.

### 3.1 `synth_rig.py` : la fenêtre telle que le dispositif la montre

Conçu pour les cas où la méthode sans IA abandonne, donc ceux où le modèle sert. Chaque image est la fenêtre redressée (800 × 650 pixels, 10 px/mm), avec :

| Scène | Ce qui est simulé |
|---|---|
| `backlit` | Verre clair sur l'écran blanc vu à travers la fenêtre : niveau parfois saturé, vignettage, moiré entre la trame de l'écran et le capteur, grain du papier calque |
| `paper` | Verre clair sur papier blanc, lumière de la pièce, sans rétro-éclairage : dégradé de la lampe, ombre du téléphone ou de la main, ombre portée et caustique du verre |
| `table` | Verre clair sur un plan de travail moucheté (le cas montré par une équipe sur le Discord) |
| `tinted` | Verre de soleil teinté (gris, brun, vert, bleu) sur l'un ou l'autre fond |
| `mounted` | Verre encore dans sa monture (opaque, unie ou écaille), pont qui sort de la fenêtre, tenon |
| `pattern` | Fonds calculés de `synth.py` (écran de couleur, rayures, grille, bruit) |
| `empty` | Aucun verre : le masque cible est vide, pour que le modèle apprenne à dire « rien ici » |
| `cut` | Verre qui dépasse de la fenêtre de 0,5 à 15 mm (mal posé) : le masque cible est la partie visible et touche le bord, pour que l'app réponde « Le verre dépasse » au lieu de mesurer un verre tronqué (ajouté pour le modèle v2) |

Sur toutes les scènes, le bord du verre est la difficulté principale : la bande sombre du biseau a une **largeur et une intensité qui varient le long du contour**, peut **disparaître sur des arcs entiers** (bord faible ou interrompu), et peut être recouverte par un **reflet**. S'y ajoutent : intérieur vu à travers une lentille mince (grossissement 0,9 à 1,12), transmission et teinte, reflet de traitement antireflet (vert, violet), traces de doigts, liseré clair dans le biseau, reflets de lampe ou de fenêtre sur la surface, poussières et fibres, bandes de papier et trait de coupe au bord de la fenêtre (fenêtre découpée un peu de travers), puis la chaîne du téléphone : perte de résolution (photo à moins de 10 px/mm), flou de mise au point, flou de bougé, exposition, gamma, bruit de photon et de lecture, compression JPEG. Formes : celles de `synth.py` (superellipse, rectangle arrondi, aviateur, œil de chat), 35 à 65 mm de large, tournées de ±10°.

### 3.2 `synth.py` : fonds variés

`training/data/synth.py` fabrique des images de la fenêtre (800 × 650 pixels) avec leur masque exact :

- formes : superellipse, rectangle arrondi, aviateur, œil de chat ;
- rendu : grossissement du fond à l'intérieur de la forme (approximation d'une lentille mince), bord sombre, liseré plus clair, 0 à 3 reflets elliptiques, ombre douce, flou, bruit, compression JPEG ;
- fonds : images fournies par l'équipe (option `--bg-dir`, uniquement nos propres images ou des images CC0), sinon fonds calculés (dégradé, bruit, rayures, grille, rétro-éclairage).

Dès qu'il y aura des photos réelles, les images synthétiques n'iront **que dans l'entraînement**, et la validation et le test seront faits sur des verres réels jamais vus. **En attendant, la validation et le test sont synthétiques**, tirés avec leurs propres graines (aucune image commune avec l'entraînement) : ils mesurent ce que le modèle a appris de la simulation, pas sa justesse sur un vrai verre.

| Jeu synthétique | Valeur |
|---|---|
| Nombre d'images | `À COMPLÉTER` |
| Fonds utilisés et leur licence | `À COMPLÉTER` |

## 4. Le modèle et l'entraînement

| Élément | Choix |
|---|---|
| Architecture | U-Net, encodeur MobileNetV3-Small (`segmentation_models_pytorch`, encodeur timm `tu-mobilenetv3_small_100`), une sortie |
| Poids de départ | Encodeur initialisé avec les poids ImageNet de timm (`mobilenetv3_small_100.lamb_in1k`), puis affiné sur notre jeu |
| Entrée | Fenêtre redressée, réduite de 800 × 650 à 384 × 320 pixels, normalisation ImageNet |
| Sortie | Une carte de 384 × 320 ; verre si la probabilité dépasse 0,5 |
| Augmentation | Perspective, luminosité et contraste, flou, bruit, compression JPEG, ombres aléatoires |
| Fonction de coût | Entropie croisée binaire + Dice |
| Optimisation | AdamW, pas de 0,001, décroissance en cosinus, 40 époques, lots de 16 (valeurs par défaut de `train.py`) |
| Choix du meilleur modèle | IoU sur les verres de validation |
| Export | ONNX (opset 17), sortie comparée à PyTorch ; copie quantifiée en entiers 8 bits |
| Exécution | Dans le navigateur, onnxruntime-web (WebAssembly, un seul fil) |

Pourquoi ce modèle : il est petit, il s'entraîne en peu de temps sur Colab, et il tourne dans le navigateur sans serveur. Le modèle voit toujours la fenêtre redressée, donc le verre à une échelle connue : la tâche est plus simple qu'une segmentation sur photo brute. Écartés : Ultralytics YOLO (licence AGPL-3.0) et Segment Anything dans le navigateur (trop lourd) ; SAM reste une option d'étiquetage hors ligne décrite dans le protocole, non utilisée à ce jour.

Commandes exactes : `training/model/README.md`. Carnet Colab : `training/model/train_colab.ipynb`.

| Entraînement réalisé | Valeur |
|---|---|
| Date, machine | 2026-10-04, PC Windows, carte NVIDIA RTX 2070 Super (8 Go) ; pas de Colab |
| Modèle v1 | 15 959 images synthétiques ; 1 époque en float32 (5,4 min), puis 18 époques en précision mixte repartant de ce point (`train.py --amp --init`, environ 70 min, cosinus) ; meilleure IoU de validation 0,9755 (600 images) |
| Modèle v2 (**livré**) | Part de v1 et ajoute 8 200 images : 3 000 tables mouchetées, 1 500 verres montés, 1 000 fenêtres vides, 1 200 verres qui dépassent de la fenêtre, 1 500 rétro-éclairage et papier ; 24 159 images en tout, 7 époques (pas de 3 × 10⁻⁴, environ 37 min) ; meilleure IoU de validation 0,9695 sur une validation plus dure (800 images dont 200 tables mouchetées), où v1 obtient 0,967 |
| Taille de `lens_seg.onnx` | 7,9 Mo (float32) |
| Écart maximal ONNX / PyTorch | 1,3 × 10⁻⁴ (tolérance 10⁻³) |
| La copie 8 bits ? | Non livrée : sur une entrée de bruit, son signe ne concorde avec le float32 que sur 78 % des pixels |
| Dans l'app | `app/public/models/lens_seg.onnx`, exécuté par onnxruntime-web (WebAssembly, un fil) ; vérifié dans Chrome sur l'app en ligne (section 7.1) ; 0,2 s par fenêtre sous Node sur le PC |

## 5. La séparation par verre

`training/data/split.py` répartit les **verres**, pas les images : environ 70 % des verres pour l'entraînement, 15 % pour la validation, 15 % pour le test. Toutes les photos d'un verre vont du même côté. Un verre du test n'a donc jamais été vu à l'entraînement, sous aucun éclairage : sans cela, les mesures seraient flatteuses et fausses.

| Découpage | Verres | Photos réelles | Images synthétiques |
|---|---|---|---|
| Entraînement | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| Validation | `À COMPLÉTER` | `À COMPLÉTER` | 0 |
| Test | `À COMPLÉTER` | `À COMPLÉTER` | 0 |

## 6. Les mesures

`training/model/evaluate.py` mesure, sur les verres de test, par condition d'éclairage et au total :

- **IoU** : recouvrement entre le masque prédit et le masque de référence ;
- **F de contour** : part du contour prédit à moins de 0,5 mm du contour de référence, et inversement ;
- **erreur A, erreur B** : écart absolu moyen, en mm, entre la largeur et la hauteur du masque prédit et celles de la référence ;
- **vides** : nombre d'images où rien n'a été trouvé.

Colonnes du fichier `metrics.md` écrit par le script.

### 6.0 En attendant les photos réelles : images synthétiques jamais vues (modèle v2 livré)

Sortie de `evaluate.py --onnx lens_seg.onnx` (le fichier livré), sur 1 500 fenêtres `synth_rig.py` tirées avec une graine absente de l'entraînement, puis sur 300 fenêtres « table mouchetée » (graine à part). Mesures à la résolution du modèle (384 × 320, 0,21 mm par pixel), **avant** l'affinage du bord au sous-pixel que fait l'app (section 7.1 pour les chiffres de l'app). Pour les fenêtres vides, l'IoU vaut 1 si le modèle ne trouve rien, 0 sinon. Entre parenthèses : le modèle v1.

| scène | n | IoU modèle | F de contour | erreur A (mm) | erreur B (mm) | IoU Otsu | erreur A Otsu (mm) | erreur B Otsu (mm) |
|---|---|---|---|---|---|---|---|---|
| toutes | 1 500 | 0,977 (0,973) | 0,910 | 0,36 (0,38) | 0,37 (0,39) | 0,395 | 11,4 | 9,8 |
| rétro-éclairage | 675 | 0,983 (0,984) | 0,930 | 0,31 | 0,30 | 0,399 | 9,5 | 7,9 |
| papier, lumière de la pièce | 387 | 0,978 (0,978) | 0,869 | 0,43 | 0,45 | 0,426 | 13,4 | 12,5 |
| fonds variés | 172 | 0,983 (0,984) | 0,916 | 0,33 | 0,37 | 0,366 | 16,7 | 16,2 |
| verre teinté | 101 | 0,994 (0,994) | 0,985 | 0,14 | 0,14 | 0,917 | 1,8 | 1,6 |
| verre monté | 74 | 0,969 (0,952) | 0,843 | 0,83 (1,32) | 0,87 (1,27) | 0,030 | 18,7 | 9,2 |
| fenêtre vide | 91 | 0,901 (0,846) | sans objet | sans objet | sans objet | 0 | sans objet | sans objet |
| table mouchetée (jeu à part) | 300 | 0,943 (0,937) | 0,629 | 1,18 (1,33) | 1,05 (1,21) | 0,232 | 18,6 | 15,8 |

Lecture : le modèle sépare le verre du fond là où un seuillage simple échoue (IoU 0,98 contre 0,40). Points faibles : table mouchetée (environ 1,1 mm) et verre monté (environ 0,85 mm) ; le modèle brut voit un verre dans 9 des 91 fenêtres vides, que l'app refuse grâce au seuil de confiance (section 7.1). Ces chiffres disent ce que le modèle a appris de la simulation ; ils ne disent rien de sa justesse sur un vrai verre.

### 6.1 Modèle (`model`)

| condition | n | IoU | boundary F | err A (mm) | err B (mm) | empty |
|---|---|---|---|---|---|---|
| overall | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| easy | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| room | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| lampe (3 directions) | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| flash | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| pattern | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| couleur | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |

### 6.2 Référence sans IA du script (`otsu`)

Seuil d'Otsu sur l'image en niveaux de gris, volontairement simple : c'est le plancher à battre.

| condition | n | IoU | boundary F | err A (mm) | err B (mm) | empty |
|---|---|---|---|---|---|---|
| overall | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| easy | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| conditions difficiles | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |

### 6.3 Que valent les données ? (ligne `overall`, modèle)

Trois entraînements, option `--sources` de `train.py`, même test.

| Données d'entraînement | n | IoU | boundary F | err A (mm) | err B (mm) | empty |
|---|---|---|---|---|---|---|
| Réelles seules (`real`) | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| Synthétiques seules (`synth`) | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| Les deux (`both`) | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |

### 6.4 Dans le navigateur

| Mesure | Android de milieu de gamme | iPhone |
|---|---|---|
| Modèle du téléphone | `À COMPLÉTER` | `À COMPLÉTER` |
| Chargement du modèle | `À COMPLÉTER` | `À COMPLÉTER` |
| Temps de calcul par verre | `À COMPLÉTER` | `À COMPLÉTER` |

## 7. Comparaison avec la méthode sans IA de l'app

La méthode sans IA de l'app (`segmentClassic`) n'est pas le seuil d'Otsu du script : elle cherche la bande sombre du bord du verre rétro-éclairé. La vraie question est : sur les mêmes photos, que mesure l'app avec et sans le modèle, face au pied à coulisse ?

Les mesures se font avec la page `eval.html` puis `tools/accuracy_report.py` (colonnes : erreur moyenne, biais, limites d'accord, répétabilité, note prédite).

| Photos | Méthode | Photos refusées | Erreur moyenne A (mm) | Erreur moyenne B (mm) | Biais A / B (mm) | Limites d'accord à 95 % A / B (mm) | Répétabilité A / B (mm) | Note prédite sur 30 |
|---|---|---|---|---|---|---|---|---|
| Rétro-éclairées | Sans IA | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| Rétro-éclairées | Sans IA, modèle en recours | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| Difficiles | Sans IA | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| Difficiles | Sans IA, modèle en recours | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |

Repère : le mentor de SN-SF donne ±0,5 mm (ISO 12870) comme tolérance réelle sur la taille du verre et sur le pont.

### 7.1 En attendant : le même calcul sur des fenêtres synthétiques, avec le code de l'app

Banc `app/bench/seg_bench.test.ts` : il exécute **le code de l'app**, sans bouchon, sur des fenêtres redressées synthétiques dont A et B sont connus exactement : `segmentClassic`, puis le modèle exactement comme `worker.ts` l'enchaîne (onnxruntime-web, WebAssembly), puis `measureLens` avec son affinage du bord au sous-pixel. Résumé par `training/data/bench_report.py`. Un verre compte « à 1 mm près » si |ΔA| et |ΔB| sont tous deux sous 1 mm.

Modèle v2 livré, code actuel de l'app (recours au modèle après `NO_LENS` ou `LENS_OUT_OF_WINDOW` de la méthode sans IA, seuil de confiance 0,85, marge de 1 mm, filtre des points accrochés à un mouchet décrit plus bas), 600 fenêtres de test, 300 tables mouchetées, 200 verres qui dépassent de la fenêtre. Entre parenthèses : le modèle v1 avec le même code avant le filtre.

| Fenêtres | n | Sans IA : verres mesurés | Sans IA : à 1 mm près | Avec le modèle : verres mesurés | Avec le modèle : à 1 mm près | Avec le modèle : erreur moyenne A, B |
|---|---|---|---|---|---|---|
| Toutes (test) | 600 | 20 % | 17 % | 96 % | **84 %** (83 %) | 0,33 mm (0,38) |
| Rétro-éclairage | 255 | 13 % | 12 % | 96 % | **91 %** (91 %) | 0,20 mm (0,22) |
| Papier, lumière de la pièce | 157 | 13 % | 4 % | 97 % | 75 % (73 %) | 0,52 mm |
| Fonds variés | 76 | 21 % | 18 % | 99 % | 86 % (84 %) | 0,25 mm |
| Verre teinté | 37 | 89 % | 89 % | 100 % | 100 % | 0,08 mm |
| Verre monté | 37 | 38 % | 35 % | 86 % | 57 % (51 %) | 0,98 mm (1,30) |
| Table mouchetée | 300 | 2 % | 0 % | 95 % | **37 %** (23 %) | 1,22 mm (1,53) |

| Cas où il faut refuser | n | Sans IA | Avec le modèle v2 (v1) |
|---|---|---|---|
| Fenêtre vide : verre inventé | 38 | 0 | **0** (0) |
| Verre qui dépasse de 0,5 à 15 mm : mesuré tronqué au lieu d'être refusé | 200 | 0 | **0** (4) |

Lecture : quand la méthode sans IA mesure, elle est très juste (0,14 mm en rétro-éclairage) mais elle refuse les bords faibles ou interrompus ; le modèle rattrape ces refus. Le modèle v2 a été préféré à v1 parce qu'il ne mesure plus aucun verre qui dépasse et fait mieux sur les verres montés.

**Filtre des points accrochés à un mouchet** (`despike` dans `measure/contour.ts`, masques du modèle seulement). L'app affine chaque point du contour vers le bord le plus net à moins de 1 mm. Sur un fond moucheté, ce bord est souvent un mouchet, et l'erreur sur table passait de 1,1 mm (masque du modèle) à 1,57 mm (après affinage). Le bord d'un verre se déplace régulièrement le long du contour, un mouchet non : un point dont le déplacement s'écarte de plus de 0,25 mm de la médiane de ses voisins (± 1,5 mm) reprend cette médiane. Effet mesuré avec le modèle v2 : table mouchetée 22 % → 37 % à 1 mm près (erreur 1,57 → 1,22 mm) ; 600 fenêtres de test : erreur moyenne 0,36 → 0,33 mm, à 0,5 mm près 65 % → 68 % (rétro-éclairage 75 % → 79 %). Les masques de la méthode sans IA ne passent pas par ce filtre. Fichiers : `training/_local/bench_*/final_v2.csv` (non versionnés), résumé par `bench_report.py`.

Dans Chrome (app construite, aucun bouchon, `app/bench/e2e_browser.mjs`) : les deux photos de test de `rig/make_board.py` à bord très faible (gris 200 à 205 sur 252), que la méthode sans IA refuse (`NO_LENS`), sont mesurées par le modèle : 50,0 × 38,0 mm pour une vérité de 50 × 38, et 48,6 × 36,3 mm pour 48,6 × 36,2. L'écran « Pas à pas » indique « méthode modèle ».

**Seuil de confiance.** Sur les 1 500 fenêtres de test, le modèle v2 brut voit un verre dans 9 des 91 fenêtres vides, avec une confiance moyenne de 0,57 à 0,67 (v1 : 14 fenêtres, 0,60 à 0,75) ; les 1 250 masques justes à 1 mm près ont tous une confiance d'au moins 0,94. L'app refuse donc tout masque du modèle dont la confiance moyenne est sous **0,85** (`MIN_MODEL_SCORE` dans `segmentModel.ts`) : plus aucun verre inventé, aucun bon masque perdu, sur ce jeu.

## 8. Où l'IA est utilisée dans l'app, et où elle ne l'est pas

| Étape | IA ? | Détail |
|---|---|---|
| Repérage de la feuille, redressement | Non | Marqueurs imprimés et géométrie. |
| Isolement du verre | **En recours seulement** | La méthode sans IA passe d'abord. Le modèle n'est appelé que si elle ne trouve pas de verre ou si son masque est douteux, et seulement si le fichier du modèle est présent. |
| Contour, A, B, périmètre | Non | Calcul géométrique sur le masque et l'image redressée. |
| Fusion de plusieurs photos | Non | Médiane et rejet des valeurs aberrantes. |
| Monture, SVG, STL | Non | Géométrie. |

L'écran « Pas à pas » indique pour chaque photo la méthode qui a produit le masque (« classique » ou « modèle »).

**Le modèle v2 est livré (`app/public/models/lens_seg.onnx`, 7,9 Mo), entraîné sur images synthétiques seulement.** Il est appelé quand la méthode sans IA répond `NO_LENS` ou `LENS_OUT_OF_WINDOW`, ou que son masque a un score sous `LOW_MASK_SCORE` (0,3) ; il est lui-même refusé sous une confiance de 0,85 (`MIN_MODEL_SCORE`) ou à moins de 1 mm du bord de la fenêtre (`BORDER_MARGIN_MM`). Si le modèle refuse après un « verre hors de la fenêtre », ce message est gardé. Ces deux seuils viennent d'images synthétiques : à régler sur de vraies photos (`À COMPLÉTER`). Le modèle et onnxruntime se téléchargent en arrière-plan dès qu'OpenCV est prêt, pour que la première photo difficile n'attende pas leurs 22 Mo. Pour revenir à une app sans IA : supprimer ce seul fichier.

Rien ne quitte le téléphone : le modèle tourne dans le navigateur, aucune photo n'est envoyée à un serveur ni à un service d'IA.

## 9. Données personnelles : aucune

- Les photos montrent un verre seul sur la feuille de référence : aucun visage, aucun nom, aucune ordonnance.
- Les verres portent un identifiant (L01, L02…) écrit sur leur sachet, jamais sur le verre.
- L'app n'a pas de compte ; les photos restent sur le téléphone. La page de collecte les garde dans le navigateur jusqu'à l'export en ZIP fait par l'équipe.
- Les photos et les modèles entraînés ne sont pas versionnés dans le dépôt (`training/_local/` est ignoré).
- Vérification du jeu final (aucune donnée personnelle dans le cadre) faite par : `À COMPLÉTER`.

## 10. Limites

- Le modèle livré n'a vu **que des images synthétiques**. Sur ces images, il aide nettement (sections 6.0 et 7.1) ; sur de vraies photos, rien n'est encore prouvé. Si, sur nos verres, il ne fait pas mieux que la méthode sans IA sur les photos difficiles, nous le dirons et nous retirerons le fichier.
- Table mouchetée sans rétro-éclairage : environ 1,2 mm d'erreur dans l'app sur synthétique (section 7.1), 37 % des verres à 1 mm près ; verre encore monté : environ 1 mm. Le rétro-éclairage du dispositif reste la condition de mesure recommandée.
- Les masques automatiques supposent un bord sombre sur la photo rétro-éclairée : un verre très teinté ou à bord très fin peut être rejeté, donc absent du jeu.
- Les outils de données écrivent les photos réelles et les images synthétiques dans deux dossiers séparés ; les réunir en un seul jeu se fait à la main avant l'entraînement.
- Les poids de départ ont été entraînés par leurs auteurs sur ImageNet ; les conditions d'utilisation d'ImageNet n'ont pas été vérifiées par nous (`À VÉRIFIER`, voir [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md)).
