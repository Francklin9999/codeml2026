# Passation pour l'audit : où en est OptiFrame

> **Écrit le 2026-10-03 vers 20 h, à la fin de la vague 1, pour qu'un autre modèle (Opus) audite l'ensemble, note la perspective de l'app et ce qu'il faut améliorer.**
> **Règle de lecture :** tout chiffre de précision ci-dessous vient de **fixtures synthétiques** (`rig/out/fixtures/`), jamais d'un verre réel. Aucune photo réelle, aucun téléphone, aucun pied à coulisse n'a encore été utilisé. L'auditeur doit le revérifier, pas me croire.

## 1. En une phrase

Les **modules de calcul** (redressement, segmentation, mesure, fusion, monture 3D, exports, outils de données, entraînement, modèle navigateur) existent et passent leurs tests ; **l'application que l'utilisateur voit n'existe pas encore** (écran d'accueil = squelette, pas de pipeline branché, pas de page de collecte, pas de documents pour le jury).

## 2. État par vague

| Vague | Briefs | État | Preuve |
|---|---|---|---|
| 0 | 01 scaffold, déploiement, dépendances | **fait, validé** | typecheck, tests, build, hébergement en sous-chemin |
| 1 | 02 feuille, 03 capture, 04 redressement, 05 segmentation, 06 mesure, 07 fusion, 08 monture, 09 exports, 11 données, 12 entraînement, 13 modèle navigateur | **faits, validés un par un par un second agent** | intégration verte à 20 h 18 : tsc 0 erreur, **194 tests JS** (13 fichiers), 28 + 14 + 10 tests Python, build OK |
| 1bis | correctif de la netteté (04) | **fait, validé** | voir §5 |
| 2 | 10 écrans et pipeline, 14 page d'évaluation et outils, **17 page de collecte sur téléphone** | **PAS LANCÉE** | |
| 3 | 15 documents jury (FR), 16 documents internes, audit final | **PAS LANCÉE** | |

Chaîne de bout en bout vérifiée sur les fixtures synthétiques : photo → redressement → segmentation → mesure → fusion → monture → STL. Erreurs sur A et B : au plus **0,05 mm** sur 10 fixtures (donc sans lumière réelle, sans reflets réels, sans verre transparent réel). Les longueurs STL suivent `84 + 50 × triangles` ; le contour est antihoraire (aire signée positive dans le repère y vers le bas) en sortie de `measureLens` et de `fuseShots` ; `generateFrame` accepte les deux sens.

## 3. Ce qui n'existe pas encore

- `app/src/main.ts` est le squelette de 01 : **aucun écran**, `worker.ts` n'appelle encore que les stubs. `pipeline.ts`, `ui/`, `preview3d.ts` : à faire (brief 10).
- Aucune page `eval.html`, aucun `tools/` (`validate_stl.py`, `accuracy_report.py`) : brief 14.
- Aucune page `collect.html` : brief 17 (ajouté après les échanges du Discord).
- `README.md` racine, `docs/DISPOSITIF_CAPTURE.md`, `PAS_A_PAS.md`, `DONNEES_ET_IA.md`, `LICENCES_ET_OUTILS_IA.md`, `ARCHITECTURE.md`, `TEST_PLAN.md`, `RUBRIC_CHECKLIST.md`, `RISKS.md`, `CLAUDE.md` : briefs 15 et 16.
- **Pas de modèle entraîné** : `app/public/models/lens_seg.onnx` n'existe pas (volontairement : un modèle jouet ne doit pas être livré). `segmentModel` répond « indisponible » et le pipeline devra s'en passer.
- À 20 h 15, des fichiers du brief 14 (`tools/`, `data/own_lenses.template.csv`) sont apparus sans que la session qui a écrit ce document ait lancé la vague 2 : une autre session travaille probablement sur le dépôt. Vérifier l'état réel avant de relancer une vague. Rien n'est **commité** (tout le projet est non suivi par git) et rien n'est **déployé** (Pages non activé, pas d'URL, pas de QR code).

## 4. Pour reprendre (ordre exact)

1. Lire [`../agents/README.md`](../agents/README.md) (vagues, changements) puis [`../agents/WAVE1_INTERFACES.md`](../agents/WAVE1_INTERFACES.md) (ce que les modules exportent vraiment, écrit à partir du code).
2. Relancer le script de workflow sauvegardé dans le dépôt :
   - vague 2 : `Workflow({ scriptPath: "<racine>/agents/orchestration/optiframe-wave.js", args: { wave: 2 } })` (10, 14, 17 en parallèle, chacun avec un vérificateur indépendant, puis contrôle d'intégration) ;
   - puis `args: { wave: 3 }` (15, 16, puis audit : couverture de la grille, cohérence des contrats, test de bout en bout).
   Si la limite de session coupe un workflow, le relancer avec `resumeFromRunId` : les agents terminés reviennent du cache.
3. Le dossier `agents/orchestration/docs_backup/` contient les copies d'origine de `CHALLENGE.md` et `docs/` pour que le brief 16 prouve qu'il n'a touché que des liens.
4. Avant d'ajouter une fonctionnalité : le brief qui possède le module, son bloc « Strategy inputs », puis les stratégies parkées de `docs/WINNING_PLAN.md` §6.

## 5. Dernier correctif : la netteté (brief 04), terminé

`Rectified.sharpness` était la variance du Laplacien de la fenêtre. Elle dépendait du contenu : une fenêtre vide donnait 0, et un verre à bord faible (le cas du verre transparent réel) était refusé comme « flou ». Elle est remplacée par une mesure sur les **marqueurs** de la feuille, normalisée par le contraste (`referenceSharpness` : patch de chaque marqueur à 10 px/mm, variance du Laplacien divisée par (p95 − p5)², moins un terme de bruit estimé sur les pixels plats, médiane sur les marqueurs). Un second repli classe `BLURRY` un flou extrême qui empêche de détecter les marqueurs (avant : `NO_REFERENCE` ou `REFERENCE_TILTED`).

Vérifié par un second agent : 10 fixtures sur 10 acceptées ; fenêtre vide = fenêtre avec verre à 0 % ; netteté strictement décroissante avec le flou ; flou fort refusé même avec du bruit ajouté (148 cas sur 150 en `BLURRY` sur ses propres sondes) ; précision de la chaîne inchangée (au plus 0,035 mm sur 3 fixtures). `MIN_SHARPNESS = 0.00015` est dérivé de fixtures **synthétiques** : `TO MEASURE` sur des photos de téléphone. Limites connues : marge de 1,27 × entre la fixture la plus floue acceptée et le seuil ; une photo très bruitée mais nette (environ 10 niveaux de gris de bruit) peut être refusée ; la médiane sur les marqueurs peut cacher une mise au point inégale sur la feuille.

## 6. Écarts et risques connus (à contrôler, pas à croire)

| # | Sujet | Détail | Source |
|---|---|---|---|
| 1 | **06 s'écarte du brief** | 60 harmoniques au lieu de 30 ; le point de bord est le point de pente maximale près du demi-niveau, pas le demi-niveau ; `restoreExtents` n'existe pas dans le brief. Documenté dans l'en-tête de `contour.ts` : sans ces trois changements, 4 tests sur 39 dépassent 0,05 mm. Le « brief gagne » : à trancher. | rapport de vérification 06 |
| 2 | Convention du sens des polygones | « Antihoraire » = aire signée positive dans le repère numérique y vers le bas (donc horaire à l'écran). Le brief ne le dit pas ; 08 normalise, mais 09 et la page de collecte doivent suivre. | rapport 06 |
| 3 | Maillage de la monture | y vers le haut (miroir du repère des contours), lentille gauche en +x ; débord de lèvre 0,7 mm (lèvre + jeu), pas 0,5 mm comme le brief. | rapport 08 |
| 4 | Poids au premier chargement | `opencv.js` 13,3 Mo + `ort-wasm` 14,2 Mo + manifold 0,5 Mo. Le service worker précharge OpenCV et manifold ; pas ort. | 04, 13 |
| 5 | Modèle int8 | `export.py` produit un int8 avec `ConvInteger` ; son exécution sur le fournisseur WASM de onnxruntime-web est à **vérifier** (13 devait le tester ou écrire `UNVERIFIED`). | 12, 13 |
| 6 | iOS Safari | événement `cancel` du sélecteur de fichier peut ne pas arriver : la promesse de `capturePhoto` reste en attente. `TO MEASURE` sur un iPhone. | vérificateur 03 |
| 7 | Versions de pointe | TypeScript 7.0.2, Vite 8, Vitest 5, onnxruntime-web 1.30 : risque de rupture. `clipper2-js` installe `@angular/core` en dépendance de pair (jamais importé ; `npm audit` signale des avis). | 01 |
| 8 | Déploiement | `deploy.yml` : typecheck et tests en `continue-on-error` (un build rouge peut partir en ligne) ; jamais exécuté sur GitHub ; Pages à activer à la main. | vérificateur 01 |
| 9 | Fixtures | `rig/out/fixtures/` est ignoré par git : un clone neuf doit exécuter `make_board.py --fixtures` avant les tests de 04 et 10. `set_print_scale.py` peut réécrire un fichier sur deux en cas d'échec partiel. | vérificateur 02 |
| 10 | Nettoyage | Un venv jetable `C:\tmp_of13` (créé par l'agent 13) traîne à la racine de `C:\`. Un fichier orphelin `app/seg.ts` (copie de profilage de 05) a été supprimé à la demande du vérificateur : seule suppression des agents, aucune autre. | 13, 05 |

## 7. Perspective de l'app (jugement du moment, à contredire si l'audit le justifie)

**Forces.** Architecture modulaire à contrats stricts, tout dans le navigateur (aucun serveur, aucun appel réseau voulu), mesure en millimètres avec échelle ancrée sur la feuille imprimée, chaque échec transformé en phrase (`messageFor`), frame watertight par construction (offsets 2D extrudés), fusion de plusieurs photos avec rejet des valeurs aberrantes, chaîne testée de bout en bout sur synthétique, honnêteté imposée (`TO MEASURE`, `À COMPLÉTER`).

**Faiblesse principale : aucune validation sur du réel.** La note de précision pèse 30 points. Tout ce qui est « au plus 0,05 mm » est un artefact de fixtures lisses, nettes et sans reflet. La cible officielle de SN-SF est **±0,5 mm sur A, B et le pont** (ISO 12870, voir [`MENTOR_NOTES.md`](MENTOR_NOTES.md)). Le cas réel montré sur le Discord (verre transparent sur surface mouchetée, sans rétro-éclairage, avec poussières et reflets) est le cas dur de notre segmenteur classique.

## 8. Ce qu'il faut améliorer, par ordre de priorité

1. **Données réelles d'abord** (liste : [`COLLECTE_DONNEES.md`](COLLECTE_DONNEES.md)) : 8 à 15 verres, 3 lectures au pied à coulisse, 3 photos de validation par verre et par téléphone. Sans cela aucun chiffre de précision n'est défendable. Brancher la page de collecte (17) sert à ça.
2. **Câbler l'application** (10) et la tester sur un vrai iPhone et un vrai Android : caméra, import, temps de calcul sous 30 s pour une paire, chargement de 13 Mo hors connexion.
3. **Mesurer le biais réel** (`tools/accuracy_report.py`, `bias.json`) : le biais de bord (bande sombre extérieure) et la parallaxe (bord du verre à environ 3 mm au-dessus de la feuille) sont les deux erreurs systématiques les plus probables.
4. **Segmentation sans rétro-éclairage** (verre transparent sur table claire) : évaluer le segmenteur classique sur les photos libres, puis décider si le modèle entraîné (12, données appariées de 11) doit devenir le chemin par défaut. Mesurer d'abord, ne rien promettre.
5. **Le pont** : l'app le règle à la main (18 mm). Si le jury compare le pont à ±0,5 mm, tester le générateur sur une paire réelle et envisager la mesure du pont sur des lunettes **montées** (stratégie 17, parkée) : des paires montées existent au stand SN-SF.
6. **Ajustement de la monture** : un test d'impression est la seule vérité sur le jeu (0,2 mm) et les lèvres (0,5 mm) ; une équipe signale que les verres entrent difficilement dans les montures d'exemple du stand.
7. **Orientation du verre** : l'axe horizontal est la ligne guide ; `rotationWarningDeg` avertit au-delà de 5°. À éprouver avec de vrais verres carrés.
8. **Robustesse** : refus clair de photos coupées, floues, avec main dans le champ, reflet fort ; vérifier le message pour chaque code et l'absence de trace technique à l'écran.
9. **Dette technique** : trancher l'écart de 06 (§6.1), rendre la CI bloquante, verrouiller ou épingler les versions de pointe, documenter le chargement des assets en sous-chemin.
10. **Perspectives** (non codées, à citer comme suite INOVA) : motif de réfraction, polarisation croisée, deux hauteurs de capture, modèle de forme, lunettes complètes, puissance du verre, recouvrement en direct.

## 9. Pour l'auditeur : quoi vérifier soi-même

- Relancer tout : `cd app && npm run typecheck && npm test && npm run build` ; `pytest` dans `rig`, `training/data`, `training/model` (chaque `.venv` local).
- Lire les tests, pas les rapports : un test qui reprend le résultat du code comme vérité est tautologique (vérifié pour chaque brief par un second agent, mais pas par un humain).
- Chercher tout chiffre « réel » non marqué `TO MEASURE` ou `À COMPLÉTER`.
- Vérifier qu'aucun module ne fait d'appel réseau en dehors du chargement de ses propres fichiers (`grep fetch`) et que le service worker ne met en cache que des réponses 200.
- Vérifier les licences réellement installées (`clipper2-js` : Boost ; OpenCV.js : Apache-2.0 ; manifold-3d : Apache-2.0 ; onnxruntime-web : MIT ; opencv-contrib-python : Apache-2.0 ; PyMuPDF est AGPL et n'est installé que dans `rig/.venv`, jamais dans `requirements.txt`).
- Ne pas faire confiance à l'ordre de grandeur « 0,05 mm » sans fixtures dégradées : appliquer flou, bruit, reflets et inclinaison réalistes avant de conclure.
