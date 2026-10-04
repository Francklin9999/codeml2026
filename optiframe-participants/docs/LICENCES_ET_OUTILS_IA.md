# Sources, licences et outils d'IA

> Retour au [`README`](../README.md). Données et modèle : [`DONNEES_ET_IA.md`](DONNEES_ET_IA.md).

**Comment ce tableau a été fait.** Les versions et les licences ont été lues dans les paquets installés sur le poste de l'équipe : champ `license` du `package.json` de chaque paquet dans `app/node_modules/`, et champs `License` / `License-Expression` des fichiers `METADATA` dans les environnements Python (`rig/.venv`, `tools/.venv`, `training/data/.venv`, `training/model/.venv`). Ce qui n'a pas pu être lu dans le paquet est marqué `À VÉRIFIER`. Aucun service payant et aucune API fermée ne sont utilisés.

## 1. Bibliothèques de l'application (`app/package.json`)

### 1.1 Livrées avec l'app

| Nom | Version installée | Licence | Usage |
|---|---|---|---|
| @techstark/opencv-js (OpenCV.js) | 5.0.0-release.1 | Apache-2.0 | Détection des marqueurs ArUco, homographie, redressement. Servi par l'app (`public/vendor/opencv/`, avec son fichier de licence). |
| manifold-3d | 3.5.4 | Apache-2.0 | Géométrie de la monture (décalages, extrusion, maillage fermé). Servi par l'app (`public/vendor/manifold/`, avec son fichier de licence). |
| three | 0.186.1 | MIT | Aperçu 3D de la monture. |
| onnxruntime-web | 1.30.0 | MIT | Exécution du modèle de segmentation dans le navigateur. Servi par l'app (`public/vendor/ort/`, avec son fichier de licence). Chargé seulement si un modèle est présent. |

### 1.2 Installées mais non utilisées par le code actuel

Prévues comme solutions de repli ; aucun fichier de `app/src/` ne les importe.

| Nom | Version installée | Licence | Usage prévu |
|---|---|---|---|
| clipper2-js | 1.2.4 | « Boost Software License » (champ `license` du paquet ; pas de fichier de licence dans le paquet : texte et version `À VÉRIFIER`) | Repli pour le décalage de polygones. |
| earcut | 3.2.4 | ISC | Repli pour la triangulation. |
| js-aruco2 | 2.0.0 | MIT | Repli pour la détection des marqueurs. |

### 1.3 Outils de développement (non livrés)

| Nom | Version installée | Licence | Usage |
|---|---|---|---|
| typescript | 7.0.2 | Apache-2.0 | Vérification des types. |
| vite | 8.3.2 | MIT | Serveur de développement et construction. |
| vitest | 5.0.3 | MIT | Tests. |
| jsdom | 29.1.1 | MIT | Tests des écrans. |
| pngjs | 7.0.0 | MIT | Lecture des images de test. |
| qrcode | 1.5.4 | MIT | Génération du QR code (`npm run qr`). |
| @types/node, @types/three, @types/earcut, @types/pngjs, @types/qrcode | 26.6.4, 0.186.0, 3.0.0, 6.0.5, 1.5.6 | MIT | Définitions de types. |

## 2. Bibliothèques Python (outils hors ligne, `requirements.txt`)

Aucune n'est livrée avec l'app : elles servent à fabriquer la feuille, les données, le modèle et les rapports.

| Nom | Version installée | Licence | Fichier `requirements.txt` | Usage |
|---|---|---|---|---|
| opencv-contrib-python | 5.0.0.93 | Apache 2.0 | `rig/`, `training/` | Marqueurs ArUco de la feuille ; redressement et masques automatiques. |
| numpy | 2.5.3 | BSD-3-Clause (et 0BSD, MIT, Zlib, CC0-1.0 pour des parties incluses) | tous | Calcul numérique. |
| reportlab | 5.0.1 | BSD | `rig/` | Écriture des PDF de la feuille à l'échelle exacte. |
| pypdf | 6.19.0 | BSD-3-Clause | `rig/` | Relecture des PDF dans les tests. |
| pytest | 9.1.1 | MIT | tous | Tests. |
| trimesh | 5.1.1 | MIT | `tools/` | Vérification du STL (maillage fermé, un seul corps). |
| torch | 2.14.1 | Apache-2.0, Apache-2.0 WITH LLVM-exception, BSD-2-Clause, BSD-3-Clause, BSL-1.0, MIT (expression lue dans le paquet) | `training/model/` | Entraînement. |
| segmentation_models_pytorch | 0.5.0 | MIT | `training/model/` | Architecture U-Net. |
| timm | 1.0.30 | Apache-2.0 | `training/model/` | Encodeur MobileNetV3-Small et ses poids. |
| albumentations | 2.0.8 | MIT | `training/model/` | Augmentation des images. |
| opencv-python-headless | 5.0.0.93 | Apache 2.0 | `training/model/` | Lecture et redimensionnement des images. |
| onnx | 1.23.1 | Apache-2.0 | `training/model/` | Export du modèle. |
| onnxruntime | 1.30.0 | MIT | `training/model/` | Contrôle de l'export, quantification. |

Installées par dépendance, hors `requirements.txt` : torchvision 0.29.1 (BSD), scipy 1.18.1 (BSD), huggingface_hub 2.1.1 (Apache-2.0, téléchargement des poids), safetensors 0.8.0 (Apache, lu dans le classificateur du paquet), pillow 12.3.0 (MIT-CMU). L'environnement `rig/.venv` du poste contient aussi PyMuPDF 1.28.2 (AGPL-3.0 ou licence commerciale) : il n'est dans aucun `requirements.txt` et aucun script du dépôt ne l'importe.

**Versions de l'entraînement réellement fait** (modèle v1, 2026-10-04, PC Windows avec carte NVIDIA RTX 2070 Super, environnement `training/.venv`, Python 3.11.9), lues dans les métadonnées des paquets installés : torch 2.6.0+cu124 (BSD-3-Clause), torchvision 0.21.0+cu124 (BSD), segmentation_models_pytorch 0.5.0 (MIT), timm 1.0.30 (Apache-2.0), albumentations 2.0.8 (MIT), onnx 1.23.1 (Apache-2.0), onnxruntime 1.30.0 (MIT), numpy 2.4.6 (BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0), opencv-contrib-python et opencv-python-headless 5.0.0.93 (Apache 2.0), huggingface_hub 2.1.1 (Apache-2.0), safetensors 0.8.0 (Apache, classificateur), scipy 1.17.1 (BSD), pillow 12.3.0 (MIT-CMU). Pas d'entraînement sur Colab.

## 3. Modèles pré-entraînés et jeux de données

### 3.1 Modèles

| Modèle | Source | Licence | Usage |
|---|---|---|---|
| Poids `mobilenetv3_small_100.lamb_in1k` | timm (téléchargés par Hugging Face Hub à l'entraînement) | Apache-2.0, déclarée par timm 1.0.30. Poids entraînés par leurs auteurs sur ImageNet-1k : conditions d'ImageNet `À VÉRIFIER` | Initialisation de l'encodeur, affiné ensuite sur notre jeu. |
| `lens_seg.onnx` (notre modèle) | Entraîné par l'équipe avec `training/model/` | `À COMPLÉTER` | Segmentation du verre en recours. **Non livré à ce jour.** Lien de téléchargement : `À COMPLÉTER`. |

Non utilisés : Segment Anything (cité dans le protocole comme option d'étiquetage hors ligne, sans code), Ultralytics YOLO (AGPL-3.0, écarté).

### 3.2 Jeux de données

| Jeu | Source | Licence | Usage |
|---|---|---|---|
| Photos de nos verres (capture appariée) | Prises par l'équipe avec la page de collecte | `À COMPLÉTER` | Entraînement, validation, test. Nombre de photos : `À COMPLÉTER`. |
| Masques des photos | Calculés par `training/data/autolabel.py`, sans annotation manuelle | Comme les photos | Étiquettes. |
| Images synthétiques | Générées par `training/data/synth_rig.py` (fenêtre du dispositif : rétro-éclairage, papier, table mouchetée, verre teinté, verre monté, fenêtre vide) et `training/data/synth.py` (fonds variés) | Produites par notre code | Entraînement ; validation et test synthétiques (graines distinctes) tant qu'il n'y a pas de photos réelles. |
| Images de fond des images synthétiques | Aucune image externe : tous les fonds sont calculés par le code (dégradés, bruit, rayures, grille, papier, mouchetis) | Produites par notre code | Variété des fonds. |
| Valeurs au pied à coulisse | Mesurées par l'équipe | Sans objet | Vérité terrain de A et B. |
| Jeu public | Aucun | Sans objet | |

Aucune donnée personnelle : pas de visage, pas de nom, pas d'ordonnance.

### 3.3 Autres sources

| Élément | Source | Remarque |
|---|---|---|
| Marqueurs ArUco `DICT_4X4_50` | Dictionnaire fourni par OpenCV | Dessinés sur la feuille par `rig/make_board.py`. |
| Système boxing (A, B, pont) | Norme ISO 8624, citée dans les consignes | Définition des mesures. |
| Tolérance de ±0,5 mm | Norme ISO 12870, citée par le mentor de SN-SF | Cible de précision. |
| Consignes du défi | SN-SF, `consignes.pdf` | Règles et barème. |
| Hébergement | GitHub Pages et GitHub Actions (`actions/checkout`, `setup-node`, `upload-pages-artifact`, `deploy-pages`) | Gratuit ; aucun traitement côté serveur. |

## 4. Outils d'IA utilisés pour coder

Lignes à compléter par l'équipe. Chaque membre doit pouvoir expliquer le code de sa partie.

| Outil | Version ou modèle | Usage | Partie du code | Relu et expliqué par |
|---|---|---|---|---|
| Claude Code (Anthropic) | `À COMPLÉTER` | Écriture du code et des tests à partir de fiches de tâche rédigées par module (dossier `agents/`), relecture par un second agent, rédaction des documents | `À COMPLÉTER` | `À COMPLÉTER` |
| Claude Code (Anthropic), modèle Claude Opus 5.5 | Session du 2026-10-04 sur un second poste ([`JOURNAL_POSTE2.md`](JOURNAL_POSTE2.md)) | Générateur synthétique du dispositif, outils de jeu de données, entraînement et export du modèle, bancs d'essai (code de l'app, navigateur réel), marge de bord du segmenteur classique, seuil de confiance et préchargement du modèle, documents | `training/data/synth_rig.py`, `build_dataset.py`, `preresize.py`, `make_bench.py`, `bench_report.py`, `training/model/train.py` (options), `app/bench/`, `app/src/vision/segmentClassic.ts` (marge), `app/src/vision/segmentModel.ts` (seuil), `app/src/worker.ts` (préchargement) | `À COMPLÉTER` |
| `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |

L'app elle-même n'appelle aucun service d'IA en ligne.
