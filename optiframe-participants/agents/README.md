# OptiFrame : briefs pour agents

Chaque fichier de ce dossier est une tâche autonome à donner **telle quelle** à un agent. Un agent = un brief. Chaque brief contient le contexte commun, les contrats de données, les fichiers dont l'agent est propriétaire, les idées retenues des stratégies de l'équipe (`strat*.md`) et les critères de fin : aucun autre document n'est nécessaire.

## Ordre de lancement

1. **Vague 0 :** le brief 01, seul. Il crée le squelette, `contracts.ts`, **installe toutes les dépendances npm** (aucun autre agent ne touche `package.json`), le `.gitignore`, le polyfill `ImageData` des tests et le service worker. Fusionner avant de continuer.
2. **Vague 1 :** les briefs 02 à 09, 11, 12 et 13, tous en parallèle. Leurs fichiers ne se recouvrent pas ; `app/public/vendor/` est découpé en sous-dossiers (`opencv/`, `manifold/`, `ort/`).
3. **Vague 2 :** les briefs 10, 14 et 17, en parallèle, une fois la vague 1 fusionnée (10 branche les vrais modules ; 14 construit `tools/` d'abord, la page d'éval ensuite ; 17 est la page de collecte de données sur téléphone).
4. **Vague 3 :** les briefs 15 et 16, en parallèle. Ils décrivent et contrôlent ce qui existe, donc ils passent en dernier.

| Brief | Sujet | Vague | Fichiers principaux |
|---|---|---|---|
| [01](01_app-scaffold-deploy.md) | App scaffold, contracts, deployment | 0 | app/package.json, app/vite.config.ts, app/tsconfig.json, app/index.html; app/src/contracts.ts, app/src/main.ts, app/src/worker.ts; .gitignore; app/src/test/setup.ts; app/public/sw.js |
| [02](02_reference-sheet.md) | Reference sheet generator and light-box page | 1 | rig/make_board.py, rig/set_print_scale.py, rig/requirements.txt, rig/README.md; rig/out/ |
| [03](03_capture.md) | Camera capture and file import | 1 | app/src/capture/ |
| [04](04_rectify.md) | Marker detection and rectification | 1 | app/src/vision/rectify.ts, app/src/vision/opencv.ts; app/public/vendor/opencv/ |
| [05](05_segment-classic.md) | Segmentation without AI | 1 | app/src/vision/segmentClassic.ts, tests |
| [06](06_measure.md) | Contour refinement and boxing measurement | 1 | app/src/measure/; app/public/bias.json |
| [07](07_quality-fusion.md) | Multi-shot fusion and user messages | 1 | app/src/quality/ |
| [08](08_frame-generator.md) | Parametric frame front | 1 | app/src/frame/; app/public/vendor/manifold/ |
| [09](09_exports.md) | SVG 1:1, STL and JSON exports | 1 | app/src/export/ |
| [10](10_ui-flow.md) | Screens and pipeline orchestration | 2 | app/index.html, app/src/main.ts, app/src/worker.ts, app/src/ui/; app/src/pipeline.ts |
| [11](11_dataset-tools.md) | Dataset tools: paired capture and synthetic lenses | 1 | training/data/; training/requirements.txt |
| [12](12_train-export.md) | Train a small segmenter and export it to ONNX | 1 | training/model/ (incl. requirements.txt) |
| [13](13_model-in-browser.md) | Run the segmenter in the browser | 1 | app/src/vision/segmentModel.ts, tests; app/public/vendor/ort/ |
| [14](14_eval-tools.md) | Evaluation page and validation tools | 2 | app/eval.html, app/src/eval/; tools/; data/ |
| [17](17_data-collection.md) | Data collection mode on the phone (photos, calliper values, ZIP export) | 2 | app/collect.html, app/src/collect/; docs/COLLECTE_DONNEES.md |
| [15](15_docs-jury.md) | Jury-facing documents (French) | 3 | README.md; docs/DISPOSITIF_CAPTURE.md, docs/PAS_A_PAS.md, docs/DONNEES_ET_IA.md, docs/LICENCES_ET_OUTILS_IA.md |
| [16](16_docs-internal.md) | Internal documents and link repair | 3 | docs/ARCHITECTURE.md, docs/TEST_PLAN.md, docs/RUBRIC_CHECKLIST.md, docs/RISKS.md; CLAUDE.md |

## Notes d'interface

`WAVE1_INTERFACES.md` liste ce que les modules de la vague 1 exportent réellement (noms, conventions, pièges). Les briefs 10, 14, 15, 16 et 17 le lisent.

## Stratégies de l'équipe

Chaque brief a une section **Strategy inputs** : les fichiers `strat*.md` à lire, les idées à reprendre (elles font partie du brief et sont vérifiées) et ce qu'on laisse de côté. Les stratégies « parkées » de `docs/WINNING_PLAN.md` §6 (4, 12, 13, 14, 17, 20, et la caméra AR de 16) ne sont pas codées : elles servent de perspectives dans la documentation. Le brief gagne toujours contre une stratégie en cas de conflit (contrats, constantes, propriétaires de fichiers).

## Changements par rapport à la première version

- Le brief 01 installe toutes les dépendances et crée `.gitignore`, `src/test/setup.ts` (polyfill `ImageData`, absent de Node et jsdom) et un service worker : sans cela, chaque agent de la vague 1 aurait modifié `package.json` ou réinventé son polyfill.
- `app/public/vendor/` est découpé par agent (`opencv/`, `manifold/`, `ort/`) ; `training/model/requirements.txt` appartient au brief 12 (pile PyTorch), `training/requirements.txt` au 11 (outils de données).
- Le brief 06 applique aussi le biais au contour (pas seulement à A et B) pour que le SVG, la monture et les chiffres affichés restent cohérents.
- `worker.ts` passe du brief 01 au brief 10 ; le 10 doit prouver le câblage réel sur une fixture de `rig/out/fixtures/`.
- 13 passe en vague 1 (il ne dépend que de l'interface du modèle), 15 et 16 en vague 3 (ils décrivent l'existant).
- Brief 17 ajouté après les échanges du Discord (`docs/MENTOR_NOTES.md`) : l'équipe a des verres réels et des téléphones, il faut une page qui range les photos sous les bons noms, saisit les valeurs du pied à coulisse et exporte des ZIP lisibles par `tools/` et `training/`. La liste de ce qu'il faut collecter est dans `docs/COLLECTE_DONNEES.md`.
- Le module de capture exporte `chooseOriginalFile` et `decodeFile` (octets d'origine des photos) ; `vite.config.ts` construit toutes les pages `*.html` de `app/`.
- Ajouts de la revue des stratégies : `rig/set_print_scale.py` (02), détection d'un verre déplacé entre deux photos (07), contrôle qualité visuel des étiquettes `--qc` (11), ablation `--sources` (12), `getLastTimings()` (13), composantes de variance et biais écrit seulement s'il aide (14), `?demo=1&error=CODE` (10).

## Consignes pour vous

- Prompt à donner : « Exécute le brief ci-joint. Racine du projet : `optiframe-participants/`. » suivi du contenu du fichier.
- Les agents n'ont ni verre, ni téléphone, ni imprimante : ils prouvent leur code sur des images synthétiques et marquent `TO MEASURE` ce qui demande du matériel réel. Ces mesures restent à faire par l'équipe.
- Les briefs 04, 08 et 13 commencent par vérifier une bibliothèque (ArUco dans OpenCV.js, API de manifold-3d, onnxruntime-web) et ont un repli prévu : lisez leur rapport final.
- Si un agent signale un problème de contrat, corrigez le bloc « Shared context » dans tous les briefs en même temps, pas dans un seul : il doit rester identique partout.
