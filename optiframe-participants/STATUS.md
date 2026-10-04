# OptiFrame : état du projet et reprise

> **Écrit le 2026-10-04 (nuit), mis à jour à 05:10 après la session du poste 2** ([`docs/JOURNAL_POSTE2.md`](docs/JOURNAL_POSTE2.md)). Pour quelqu'un qui reprend le travail de son côté, tout de suite.
> **À lire ensuite si besoin :** [`CHALLENGE.md`](CHALLENGE.md) (les règles et le barème), [`docs/WINNING_PLAN.md`](docs/WINNING_PLAN.md) (les priorités), [`agents/WAVE1_INTERFACES.md`](agents/WAVE1_INTERFACES.md) (ce que chaque module exporte).

## 1. En trois lignes

- **L'app est en ligne** : **https://francklin9999.github.io/codeml2026/**, QR code dans `app/public/qr.svg` (vérifié). Déployée à chaque push sur `main` si le typecheck et les tests passent. Parcours complet réussi dans un vrai Chrome (écran de téléphone) sur l'URL publique : import d'une photo, mesure des deux verres, SVG, monture, `monture.stl`.
- **Un modèle de segmentation entraîné est livré** (`app/public/models/lens_seg.onnx`, v2), en recours de la méthode sans IA. Entraîné sur 24 159 images **synthétiques** du dispositif : sur images jamais vues, passées par le code de l'app, 84 % des verres à 1 mm près avec lui contre 17 % sans ([`docs/DONNEES_ET_IA.md`](docs/DONNEES_ET_IA.md) §7.1).
- **Rien n'est encore validé sur du réel** : aucun vrai verre, aucun vrai téléphone, aucune impression. **Le plus urgent n'est plus du code** : pied à coulisse, photos, essais sur un iPhone et un Android.

## 2. Démarrer en 2 minutes

```bash
cd optiframe-participants/app
npm ci
npm run dev
```

Ouvrir `http://localhost:5173/?demo=1` : parcourt les cinq écrans sans caméra et télécharge un STL. `?demo=1&error=NO_LENS` (ou un autre code) montre le message d'erreur correspondant.

```bash
npm run typecheck
npm test
npm run build
```

La suite JS charge OpenCV.js : compter 1 min 30 seule, plus de 6 min si autre chose tourne en même temps. Les fixtures de test sont ignorées par git : sur un clone neuf, lancer d'abord `python rig/make_board.py --fixtures` depuis `rig/` (venv + `rig/requirements.txt`).

## 3. Ce qui est fait

Dernier contrôle complet (cette nuit, lancé seul) : typecheck sans erreur, **321 tests JS sur 321**, build correct, tests Python 28 (rig) + 14 (training/data) + 10 (training/model) + 22 (tools).

| Partie | Où | État |
|---|---|---|
| Feuille de référence (PDF A4 et Lettre, marqueurs ArUco, règle de 100 mm) | `rig/`, `rig/out/` | fait |
| Capture photo et import de fichier | `app/src/capture/` | fait, jamais essayé sur téléphone |
| Redressement (marqueurs, homographie, netteté) | `app/src/vision/rectify.ts` | fait |
| Segmentation sans IA | `app/src/vision/segmentClassic.ts` | fait ; ignore une marge de 2 mm au bord de la fenêtre ; refuse les bords très faibles (2 fixtures sur 10 → le modèle prend le relais) |
| Mesure A, B, périmètre, biais, parallaxe | `app/src/measure/` | fait ; erreur ≤ 0,05 mm **sur synthétique seulement** |
| Fusion de plusieurs photos, messages d'erreur en français | `app/src/quality/` | fait |
| Monture (cercles, rainure, pont, tenons), maillage fermé | `app/src/frame/` | fait, jamais imprimé |
| Exports SVG 1:1, STL, JSON | `app/src/export/` | fait, jamais imprimé |
| Écrans et pipeline | `app/src/ui/`, `app/src/pipeline.ts`, `app/src/worker.ts` | fait |
| Page d'évaluation par lot | `app/eval.html` | fait ; s'ouvre dans Chrome sans erreur (en ligne) ; jamais utilisée sur de vraies photos |
| Page de collecte sur téléphone (photos, valeurs pied à coulisse, ZIP) | `app/collect.html`, [`docs/COLLECTE_DONNEES.md`](docs/COLLECTE_DONNEES.md) | fait ; s'ouvre dans Chrome sans erreur (en ligne) ; jamais essayée sur téléphone |
| Rapport de précision, validation STL | `tools/accuracy_report.py`, `tools/validate_stl.py` | fait |
| Outils de données et entraînement | `training/data/`, `training/model/` | fait ; générateur du dispositif `synth_rig.py` ; modèle v2 entraîné (carte NVIDIA, précision mixte) |
| Modèle dans le navigateur | `app/src/vision/segmentModel.ts`, `app/public/models/lens_seg.onnx` | **actif** : v2 livré ; refusé sous 0,85 de confiance ou à moins de 1 mm du bord ; préchargé en arrière-plan ; vérifié dans Chrome (« méthode modèle ») |
| Bancs d'essai | `app/bench/` | banc de segmentation sur le code de l'app, parcours complet et pages dans un vrai Chrome (hors `npm test`, voir `docs/JOURNAL_POSTE2.md`) |

## 4. Dernière passe (terminée)

Le workflow d'agents est terminé : plus rien ne tourne, toutes les zones sont libres. Tout est commité sur la branche `optiframe-app`.

- **Performance** : OpenCV.js (13,3 Mo) se charge en arrière-plan dès l'accueil, dans le worker ; le runtime ONNX (14,2 Mo) n'est téléchargé que si un modèle existe ; JS initial 45 ko (21 ko gzip) ; les temps par étape s'affichent sur l'écran « Pas à pas » ; `npm run size` vérifie le budget ; le déploiement est bloqué si les tests échouent. Temps mesurés sous Node sur PC, pas sur téléphone.
- **Documents** : `README.md` et `docs/` (dispositif, pas à pas, données et IA, licences, architecture, plan de test, grille, risques) sont écrits, avec des `À COMPLÉTER` partout où il faut une mesure réelle.
- **Audit final** : sept défauts relevés, tous corrigés et couverts par des tests (321 tests JS, 16 tests `training/data`) :
  1. `training/data/autolabel.py` applique `printScale` comme l'app, n'accepte plus les photos de validation comme groupes d'entraînement et liste les `.heic` dans `rejected.csv`.
  2. Annuler la prise de photo n'affiche plus d'erreur.
  3. « Caméra refusée » ne peut pas se produire avec l'appareil photo natif : noté dans `docs/RUBRIC_CHECKLIST.md` ; « Importer une photo » reste le repli.
  4. L'écran monture propose « Contour gauche / droit (SVG 1:1) ».
  5. L'écran de capture dit « Face bombée vers le haut, le haut du verre vers HAUT ».
  6. Une photo de moins de 1600 px de côté (seuil provisoire) affiche un avertissement « image reçue par messagerie ».
  7. Le jeu affiché est maintenant calculé sur les logements générés (plus une simple copie du paramètre).
- **Cinq défauts mineurs**, corrigés aussi : `collect.html` et `eval.html` fonctionnent hors ligne après une visite ; un modèle réentraîné est repris sans vider le cache ; le `LISEZMOI.txt` des ZIP prévient pour le biais ; ligne périmée de `docs/COLLECTE_DONNEES.md` corrigée.

## 5. Ce que tu peux faire tout de suite, sans conflit

Par ordre de points en jeu. Les tâches 1 à 6 ne demandent pas de modifier le code.

| # | Tâche | Comment | Pourquoi |
|---|---|---|---|
| 1 | **Mesurer les verres au pied à coulisse** | 8 à 15 verres, 3 lectures de A et de B chacun, dans `data/own_lenses.csv` (colonnes de `data/own_lenses.template.csv`). Numéro du verre sur son sachet, jamais sur le verre. | Sans vérité terrain, aucun chiffre de précision n'est défendable. 30 points. |
| 2 | **Imprimer la feuille de référence** | `rig/out/board_Letter.pdf` (ou `board_A4.pdf`) à 100 %. Mesurer la règle : elle doit faire 100 mm. Sinon : `python rig/set_print_scale.py <mm mesurés>`. | L'échelle de toutes les mesures en dépend. |
| 3 | **Photographier les verres** | Suivre [`docs/COLLECTE_DONNEES.md`](docs/COLLECTE_DONNEES.md) : 3 photos par verre et par téléphone, plus les photos « difficiles » pour l'entraînement. Photos d'origine, jamais passées par WhatsApp. | Validation et jeu de données. Des paires montées sont au stand SN-SF. |
| 4 | **Essayer l'app sur un iPhone et un Android** | Scanner `app/public/qr.svg` (l'URL est en ligne). Noter : la caméra s'ouvre-t-elle, temps par photo (écran « Pas à pas »), messages affichés. En émulation de téléphone lent, une paire prend environ 26 s de calcul : à confirmer. | 15 points, et ça conditionne tout le reste. |
| 5 | **Trouver une imprimante 3D** | Imprimer un `monture.stl` du mode démo, face à plat. Vérifier avec `python tools/validate_stl.py monture.stl`. | Seule façon de régler le jeu (0,2 mm) et les lèvres (0,5 mm). |
| 6 | ~~Mettre en ligne~~ **fait** | URL ci-dessus, QR dans `app/public/qr.svg`. Reste : **imprimer le QR en grand** (deux copies) pour la démo. | |
| 7 | **Réentraîner le modèle avec les vraies photos** | v2 (synthétique) est livré. Après les photos : `training/data/autolabel.py`, `split.py`, puis `build_dataset.py` pour réunir réel et synthétique, `preresize.py`, et `training/model/train.py --amp --init training/_local/model_v2/best.pt` (machine avec carte NVIDIA) ou Colab. Comparer avec `app/bench/seg_bench.test.ts` + `training/data/bench_report.py` avant de remplacer `app/public/models/lens_seg.onnx`, puis augmenter `VERSION` dans `sw.js`. | Chiffres « sur nos verres » pour les 15 points « Données et IA ». |

Une fois les photos et le CSV prêts : ouvrir `eval.html`, y déposer les photos, télécharger `results.csv`, puis `python tools/accuracy_report.py results.csv data/own_lenses.csv`. Le rapport donne l'erreur moyenne, le biais et la note prévue. **Lancer l'évaluation avec le `bias.json` identité**, sinon la correction est ajustée deux fois.

## 6. Pièges connus

- **Précision réelle inconnue.** Le « 0,05 mm » vient d'images synthétiques nettes et sans reflet. La cible de SN-SF est ±0,5 mm sur A, B et le pont ([`docs/MENTOR_NOTES.md`](docs/MENTOR_NOTES.md)).
- **Verre transparent sans rétro-éclairage** : c'est le cas difficile du segmenteur sans IA. Poser la feuille sur un écran blanc (`lightbox.html`) change tout.
- **Seuil de netteté** (`MIN_SHARPNESS`) calé sur du synthétique : à régler sur de vraies photos si l'app refuse des photos nettes.
- **iPhone** : si Safari n'envoie pas l'événement d'annulation du sélecteur de photo, rien ne s'affiche et le bouton reste utilisable ; à confirmer sur un vrai iPhone.
- **Le pont** est réglé à la main (18 mm par défaut), pas mesuré.
- **Modèle entraîné sur synthétique seulement.** Ses seuils (`LOW_MASK_SCORE` 0,3 dans `worker.ts`, `MIN_MODEL_SCORE` 0,85 dans `segmentModel.ts`) viennent d'images synthétiques. Point faible connu : table mouchetée sans rétro-éclairage (environ 1,6 mm). Pour couper l'IA : supprimer `app/public/models/lens_seg.onnx`.
- **Premier recours au modèle** : 22 Mo (modèle + onnxruntime), préchargés en arrière-plan une fois OpenCV prêt. Avant la démo, ouvrir l'app une fois sur le téléphone de démo, sur le Wi-Fi.
- **Bancs `app/bench/`** : `vite.config.ts` découpe les tests en projets ; le banc a sa propre config (`bench/vitest.bench.config.ts`) qui les retire. Les images synthétiques et les modèles sont dans `training/_local/` (non versionné) ; pour les refaire : `training/data/synth_rig.py`.
- Détail de tout le reste : [`docs/HANDOFF_AUDIT.md`](docs/HANDOFF_AUDIT.md) (écrit avant la vague 2, donc en retard sur les écrans et les outils).

## 7. Règles de travail

- Un module = un propriétaire : voir le tableau de [`agents/README.md`](agents/README.md). Ne jamais modifier `app/src/contracts.ts` sans prévenir.
- Ne jamais écrire un chiffre de précision qui ne sort pas de `tools/accuracy_report.py` sur de vraies photos.
- Déclarer les outils d'IA utilisés : ils doivent figurer dans le README final.
