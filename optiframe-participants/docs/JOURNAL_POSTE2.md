# Journal du poste 2 (nuit du 3 au 4 octobre 2026)

> Travail fait sur un second poste (portable avec carte NVIDIA RTX 2070 Super). Jusqu'à 02:15, le workflow du poste principal modifiait `app/src/**` et les documents : ces zones n'ont été touchées qu'après son commit `548901c` (« toutes les zones sont libres »).
> Tout chiffre ci-dessous vient d'images **synthétiques**. Aucun n'est une précision sur verre réel.

## Fichiers ajoutés ou modifiés (hors zones verrouillées)

| Fichier | Quoi |
|---|---|
| `training/data/capture_protocol.md`, `training/data/dataset_card.md` | Noms des conditions alignés sur la page de collecte : `lampL`, `lampT`, `lampR`, `colour` (au lieu de `lamp1..3`, `color`). `autolabel.py` accepte déjà n'importe quel nom : seule la doc était fausse. |
| `training/data/synth_rig.py` | Générateur synthétique « domaine du dispositif » : fenêtre rétroéclairée ou papier blanc sans rétroéclairage, bord du verre faible, irrégulier ou interrompu, reflets qui traversent le bord, poussières, moiré, bandes de papier au bord de la fenêtre, verres teintés, verre encore dans sa monture, images vides. Écrit A et B exacts dans `index.csv`. |
| `training/data/build_dataset.py` | Assemble un dossier d'entraînement unique avec un découpage explicite (val et test synthétiques tirés avec leurs propres graines, tant qu'il n'y a pas de photos réelles). |
| `training/data/make_bench.py` | Convertit un jeu étiqueté en PNG + `truth.csv` pour le banc côté app. |
| `app/bench/seg_bench.test.ts`, `app/bench/vitest.bench.config.ts` | Banc de segmentation qui exécute le **code de l'app** (segmenteur classique, puis le modèle via onnxruntime-web comme dans `worker.ts`, puis `measureLens`). Hors de `npm test` : se lance exprès. |

## Avancement

| Heure | Étape | Résultat |
|---|---|---|
| 01:00 | Lecture de STATUS.md, environnement | Python 3.11 + torch 2.6 CUDA dans `training/.venv`, `npm ci` dans `app/` |
| 01:20 | Générateur `synth_rig.py` | Aperçu visuel vérifié (24 images, contours exacts) |
| 01:30 | Génération des jeux | val 600 (graine 1), test 1500 (graine 2), train 12 000 (graine 0) + 2 500 génériques (`synth.py`) |
| 01:20 | Banc côté app, segmenteur classique seul, 200 images de val | voir constat 1 |

| 01:48 | **Premier essai de l'app dans un vrai navigateur** (Chrome sans fenêtre, écran de téléphone Android 412 × 915, app construite avec `npm run build`, aucun bouchon) : `app/bench/e2e_browser.mjs` | **Réussi de bout en bout** : import d'une photo de fixture pour chaque œil, OpenCV.js dans le vrai worker, résultat, export SVG, monture, `monture.stl` téléchargé. Verre droit 57,0 × 45,0 mm (vérité 57 × 45), gauche 54,2 × 40,4 mm (vérité 54,2 × 40,4). Temps : 9,5 s pour la 1re photo (chargement d'OpenCV compris), 2,8 s pour la 2e, 1,6 s pour la monture. STL : `validate_stl.py` tout PASS (étanche, 1 corps, 146,6 × 52,4 × 4 mm). |
| 01:50 | Toutes les pages, taille iPhone (390 × 844) : `app/bench/pages_smoke.mjs` | `index`, `?demo=1`, `eval.html`, `collect.html`, `lightbox.html` : aucune erreur de page, pas de défilement horizontal. Les 10 codes d'erreur donnent une phrase claire en français, jamais un code. Seul défaut : `favicon.ico` absent (404 dans la console) → ajouté dans `app/public/favicon.ico`. |

| 02:15 | Commit `548901c` du poste principal récupéré ; **l'app est en ligne** : https://francklin9999.github.io/codeml2026/ (déploiement GitHub Pages réussi) | |
| 02:25 | Les deux essais navigateur relancés **sur l'URL publique** | E2E réussi (1re photo 4,5 s, 2e 3,5 s, monture 1,8 s, mêmes A et B). Pages : tout OK sauf `favicon.ico` demandé à la racine du domaine (`francklin9999.github.io/favicon.ico`) faute de `<link rel="icon">` → lien ajouté dans `index.html`, `eval.html`, `collect.html`, `lightbox.html`. |
| 02:25 | Correctif de marge (constat 1) appliqué dans `app/src/vision/segmentClassic.ts` | 3 tests ajoutés dans `segmentClassic.test.ts`. Le test de marge échoue sur l'ancien code et passe sur le nouveau. Les deux tests « bande de papier » passent sur les deux : ils servent de garde-fous. `segmentClassic.test.ts` + chaîne des fixtures : 22/22. `npm run typecheck` OK. |
| 02:20 → 03:35 | Entraînement du modèle v1 (RTX 2070 Super, précision mixte) | 15 959 images synthétiques d'entraînement (12 000 `synth_rig` + 2 000 table mouchetée et fonds variés + 1 959 `synth.py`), validation 600, test 1 500 + 300 table (graines distinctes). IoU de validation : 0,916 (époque 1) → 0,973 (époque 12). |
| 02:45 | Banc côté app avec un instantané du modèle (époque 4, IoU val 0,964), 300 images de test | voir constat 2 |
| 03:05 | Seuil de confiance du modèle | voir constat 3 ; `MIN_MODEL_SCORE = 0.85` dans `segmentModel.ts`, 2 tests |
| 03:18 | E2E sur l'URL publique en **émulation de téléphone lent** : processeur ralenti 4 fois, réseau 4G (9 Mbit/s, 60 ms), cache vide comme un téléphone neuf | Réussi. Accueil 3,4 s ; 1re photo 8,1 s (téléchargement d'OpenCV compris) ; 2e photo 3,8 s ; monture 13,9 s. Soit environ 26 s de calcul pour une paire, sous les 30 s des consignes mais avec peu de marge ; l'étape la plus lente sur processeur faible est la monture. Émulation sur PC (chargé par l'entraînement) : à confirmer sur un vrai téléphone de milieu de gamme. |
| 03:28 | Modèle v1 terminé : IoU de validation 0,9755 ; export ONNX (écart 4,9 × 10⁻⁴) | `evaluate.py` sur 1 500 fenêtres de test : IoU 0,973 (Otsu 0,395), erreur A/B 0,38/0,39 mm à la résolution du modèle ; table mouchetée et verre monté autour de 1,3 mm |
| 03:30 | **Chemin du modèle vérifié dans Chrome** sur l'app construite : les deux fixtures à bord très faible, refusées jusqu'ici, sont mesurées par le modèle | 50,0 × 38,0 mm (vérité 50 × 38) et 48,6 × 36,3 mm (vérité 48,6 × 36,2) ; « Pas à pas » : « méthode modèle », segmentation 3,0 s |
| 03:33 | Seuil de confiance revérifié sur le modèle final | 14 verres inventés sur 91 fenêtres vides, confiance 0,60 à 0,75 ; 1 238 masques justes à 1 mm près, tous ≥ 0,94. À 0,85 : 0 faux verre, 0 bon masque perdu |
| 03:37 | **Modèle livré** (`bd19f7c`, poussé sur `main`) : `app/public/models/lens_seg.onnx`, service worker v4, documents à jour | |

| 04:05 → 04:50 | Modèle v2 : 7 époques à partir de v1, avec 8 200 images en plus (table mouchetée, verre monté, fenêtre vide, verre qui dépasse, rétro-éclairage et papier) | IoU de validation 0,9695 sur une validation plus dure (v1 : 0,967) |
| 04:58 | **v2 comparé à v1 avec le code actuel de l'app**, puis livré | 600 fenêtres : 84 % à 1 mm près (v1 83 %) ; verre monté 57 % (51 %) ; verres qui dépassent mesurés à tort : 0 sur 200 (v1 : 4) ; fenêtres vides : 0 verre inventé ; table mouchetée inchangée (22 %) ; rétro-éclairage 90 % (91 %), un peu moins à 0,5 mm près (75 % contre 79 %). Chrome : fixtures à bord faible toujours mesurées à 0,1 mm près par le modèle |

| 05:15 | Constat 6 corrigé : filtre `despike` des points accrochés à un mouchet (masques du modèle seulement), 2 tests | Table mouchetée 22 % → 37 % à 1 mm près ; 600 fenêtres : erreur 0,36 → 0,33 mm, rétro-éclairage à 0,5 mm près 75 % → 79 % |

Ces essais tournent sur un PC : ils ne remplacent pas un vrai iPhone (Safari) ni un vrai téléphone Android de milieu de gamme.

## Constats

### 0. Parallaxe : choisir une seule face posée sur la feuille (fait par le poste principal dans `548901c`)

`measure/correction.ts` suppose le bord du verre à `EDGE_HEIGHT_MM = 3` mm au-dessus de la feuille. Un verre posé **face bombée vers le haut** repose sur son bord (bord à environ 1 mm). Posé face bombée vers le bas, il bascule sur son centre et son bord monte à environ 3 mm ou plus. À 30 cm, 2 mm d'écart de hauteur font environ 0,4 mm d'erreur sur 55 mm. `bias.json` peut absorber ce biais, à condition que l'étalonnage et la démo utilisent **la même face**. Recommandation : écrire « face bombée vers le haut » dans la consigne d'écran (`app/src/ui/screens.ts`, écran de capture) et sur la fiche du dispositif, puis étalonner ainsi.

### 1. Le segmenteur classique refuse une bande sombre au bord de la fenêtre (`LENS_OUT_OF_WINDOW`)

Sur 200 images synthétiques « dispositif » (val), le segmenteur classique mesure 25 % des verres. Quand il mesure sur rétroéclairage, il est très juste (erreur moyenne sur A et B : 0,09 mm). Mais **45 refus sur 200 sont des `LENS_OUT_OF_WINDOW`** causés par une bande sombre au bord de la fenêtre : fenêtre découpée un peu de travers, trait de coupe imprimé, ombre du téléphone qui atteint le bord. Ce refus est définitif dans `worker.ts` (seul `NO_LENS` déclenche le modèle), donc le modèle ne peut pas rattraper ces photos.

Risque réel : la feuille imprime un trait de coupe exactement au bord de la fenêtre. Si la fenêtre n'est pas découpée, une erreur de redressement de quelques dixièmes de mm fait entrer ce trait dans l'image redressée.

**Correctif appliqué (02:25) dans `app/src/vision/segmentClassic.ts`** : les pixels de bord à moins de 2 mm du bord de la fenêtre sont ignorés, et un verre qui atteint cette marge compte comme « sorti » (constante `BORDER_MARGIN_MM = 2`). Mesuré d'abord sur une copie dans le banc : sur les mêmes 200 images, `LENS_OUT_OF_WINDOW` passe de 45 à 11. Ces photos deviennent des `NO_LENS`, donc rattrapables par le modèle. Aucun faux positif sur les images vides. Tests unitaires et 10 fixtures : tous verts avec la marge.

### 2. Le modèle en recours multiplie par 4,5 les verres mesurés à 1 mm près (synthétique)

Instantané de l'époque 4, 300 images de test synthétiques, **code de l'app** (classique, puis modèle via onnxruntime-web comme dans `worker.ts`, puis `measureLens`) :

| Chemin | Verres mesurés | À 1 mm près (A et B) | Erreur moyenne A, B | Image vide prise pour un verre |
|---|---|---|---|---|
| Classique seul | 20 % | 17 % | 0,42 mm | 0 % |
| Classique + modèle en recours | 89 % | 76 % | 0,41 mm | **47 %** |

Sur rétro-éclairage (le dispositif prévu) : 90 % à 1 mm près avec le modèle (erreur moyenne 0,28 mm), 13 % sans.

*Correction à 04:05* : la première version de ce constat donnait 100 % / 80 % (et 93 % sur rétro-éclairage). Mon banc appelait le modèle aussi après un refus classique `LENS_OUT_OF_WINDOW` ou `GLARE`, alors que `worker.ts` ne le faisait que sur `NO_LENS`. `bench_report.py` recalcule désormais le chemin de l'app à partir des colonnes classique et modèle, avec la règle exacte. Lunettes montées : le modèle fait pire (2,8 mm), attendu, à citer comme limite. Inférence : 1,35 s médiane (Node, WASM un fil, PC chargé).

### 3. Le modèle inventait un verre sur une fenêtre vide : seuil de confiance

Le score d'un masque du modèle (probabilité moyenne à l'intérieur, déjà calculé par `postprocess`) sépare nettement les deux cas sur les 1 500 images de test : les 29 verres inventés sur des fenêtres vides ont un score de 0,64 à 0,71 ; **les 1 160 masques justes à 1 mm près ont tous un score ≥ 0,94**. Avec `MIN_MODEL_SCORE = 0.85`, `postprocess` répond `NO_LENS` aux 29 et garde les 1 160. À revérifier sur le modèle final et sur de vraies photos.

### 4. Premier recours au modèle : 22 Mo à télécharger

Le modèle (7,9 Mo en fp32) et le runtime ONNX (14,2 Mo) ne sont téléchargés qu'au premier recours. Sur le Wi-Fi d'un salon, la première photo difficile peut donc prendre de 10 à 30 s de plus. Options : précharger les deux fichiers en arrière-plan une fois OpenCV prêt, ou ouvrir l'app une fois sur le téléphone de démo avec une photo difficile avant le passage du jury. La copie int8 (2,2 Mo) n'est pas une option sûre : sur une entrée de bruit, son signe ne concorde avec le fp32 que sur 66 % des pixels.

### 5. Le modèle peut aussi rattraper un faux « verre hors de la fenêtre », sans mesurer un verre coupé

Banc du modèle v1 sur 600 fenêtres de test : la méthode classique répond `LENS_OUT_OF_WINDOW` sur 41 fenêtres où le verre est bien dans la fenêtre (sur table mouchetée : 111 sur 300 ; le mouchetis près du bord ressemble à un verre qui dépasse). Ce refus était définitif. Désormais (`worker.ts`), le modèle est aussi essayé après ce refus ; s'il ne mesure pas un verre **à l'intérieur** de la fenêtre, le refus « Le verre dépasse » est maintenu.

Garde-fou : un verre qui dépasse vraiment ne doit pas être mesuré tronqué. Le modèle n'a jamais vu de verre à moins de 2 mm du bord, donc `postprocess` refuse tout masque à moins de 1 mm du bord (`BORDER_MARGIN_MM`). Essai sur 200 fenêtres synthétiques où le verre dépasse de 0,5 à 15 mm (nouvelle scène `cut` de `synth_rig.py`) : **196 refusées** (`LENS_OUT_OF_WINDOW` ou `NO_LENS`), 4 mesurées à tort avec le modèle v1. Le modèle v2 apprend sur 1 200 verres coupés dont le masque touche le bord.

Effet sur les 600 fenêtres de test (modèle v1) : 83 % des verres à 1 mm près au lieu de 79 %, sans fausse détection sur les fenêtres vides.

### 6. Table mouchetée : l'affinage du bord de l'app dégrade le masque du modèle

Sur 300 tables mouchetées, le masque du modèle v2 donne 1,1 mm d'erreur à sa propre résolution (`evaluate.py`), mais 1,57 mm après `measureLens`, qui déplace chaque point du contour vers le plus fort gradient à moins de 1 mm. Sur un fond moucheté, ce gradient est souvent un mouchet. Piste : quand le masque vient du modèle et que le fond est texturé, ne déplacer un point que si le gradient trouvé est cohérent avec ses voisins (ou garder le contour du modèle). **Fait à 05:15** (`despike`, masques du modèle seulement, voir `DONNEES_ET_IA.md` §7.1) : table 22 % → 37 % à 1 mm près, et un léger gain partout ailleurs. À valider sur de vraies photos.
