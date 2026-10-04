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

Point à régler avant la première séance : la page de collecte nomme les conditions `lampL`, `lampT`, `lampR`, `colour`, alors que le protocole d'origine écrit `lamp1`, `lamp2`, `lamp3`, `color`. Les noms retenus dans le jeu final : `À COMPLÉTER`.

## 3. Les images synthétiques

`training/data/synth.py` fabrique des images de la fenêtre (800 × 650 pixels) avec leur masque exact :

- formes : superellipse, rectangle arrondi, aviateur, œil de chat ;
- rendu : grossissement du fond à l'intérieur de la forme (approximation d'une lentille mince), bord sombre, liseré plus clair, 0 à 3 reflets elliptiques, ombre douce, flou, bruit, compression JPEG ;
- fonds : images fournies par l'équipe (option `--bg-dir`, uniquement nos propres images ou des images CC0), sinon fonds calculés (dégradé, bruit, rayures, grille, rétro-éclairage).

Les images synthétiques ne vont **que dans l'entraînement**, jamais dans la validation ni le test.

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
| Date, machine (Colab, GPU) | `À COMPLÉTER` |
| Durée | `À COMPLÉTER` |
| Taille de `lens_seg.onnx` | `À COMPLÉTER` |
| Écart maximal ONNX / PyTorch | `À COMPLÉTER` |
| La copie 8 bits tourne-t-elle dans le navigateur ? | `À COMPLÉTER` (non vérifié) |

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

## 8. Où l'IA est utilisée dans l'app, et où elle ne l'est pas

| Étape | IA ? | Détail |
|---|---|---|
| Repérage de la feuille, redressement | Non | Marqueurs imprimés et géométrie. |
| Isolement du verre | **En recours seulement** | La méthode sans IA passe d'abord. Le modèle n'est appelé que si elle ne trouve pas de verre ou si son masque est douteux, et seulement si le fichier du modèle est présent. |
| Contour, A, B, périmètre | Non | Calcul géométrique sur le masque et l'image redressée. |
| Fusion de plusieurs photos | Non | Médiane et rejet des valeurs aberrantes. |
| Monture, SVG, STL | Non | Géométrie. |

L'écran « Pas à pas » indique pour chaque photo la méthode qui a produit le masque (« classique » ou « modèle »).

**Aujourd'hui, le fichier du modèle (`app/public/models/lens_seg.onnx`) n'est pas livré : l'app en ligne fonctionne entièrement sans IA.** Le seuil qui déclenche le recours au modèle est une valeur de départ, à régler sur de vraies photos : `À COMPLÉTER`.

Rien ne quitte le téléphone : le modèle tourne dans le navigateur, aucune photo n'est envoyée à un serveur ni à un service d'IA.

## 9. Données personnelles : aucune

- Les photos montrent un verre seul sur la feuille de référence : aucun visage, aucun nom, aucune ordonnance.
- Les verres portent un identifiant (L01, L02…) écrit sur leur sachet, jamais sur le verre.
- L'app n'a pas de compte ; les photos restent sur le téléphone. La page de collecte les garde dans le navigateur jusqu'à l'export en ZIP fait par l'équipe.
- Les photos et les modèles entraînés ne sont pas versionnés dans le dépôt (`training/_local/` est ignoré).
- Vérification du jeu final (aucune donnée personnelle dans le cadre) faite par : `À COMPLÉTER`.

## 10. Limites

- Tant que les tableaux sont vides, rien ne prouve que le modèle aide. Si le modèle ne fait pas mieux que la méthode sans IA sur les photos difficiles, nous le dirons et l'app restera sans IA.
- Les masques automatiques supposent un bord sombre sur la photo rétro-éclairée : un verre très teinté ou à bord très fin peut être rejeté, donc absent du jeu.
- Les outils de données écrivent les photos réelles et les images synthétiques dans deux dossiers séparés ; les réunir en un seul jeu se fait à la main avant l'entraînement.
- Les poids de départ ont été entraînés par leurs auteurs sur ImageNet ; les conditions d'utilisation d'ImageNet n'ont pas été vérifiées par nous (`À VÉRIFIER`, voir [`LICENCES_ET_OUTILS_IA.md`](LICENCES_ET_OUTILS_IA.md)).
