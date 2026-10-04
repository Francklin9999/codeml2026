# OptiFrame

Défi SN-SF (Santé Numérique Sans Frontières), CodeML 2026 : mesurer un verre de lunettes recyclé avec un téléphone et générer une monture imprimable en 3D.

> **Règle de ce dépôt :** aucun chiffre mesuré n'est écrit de mémoire. Tout ce qui demande un vrai verre, un vrai téléphone ou une vraie impression est marqué `À COMPLÉTER` jusqu'à ce que la mesure existe.

## 1. Lien de l'app et QR code

| | |
|---|---|
| URL publique (HTTPS) | **https://francklin9999.github.io/codeml2026/** (GitHub Pages, déployé à chaque push sur `main` si le typecheck et les tests passent) |
| QR code | [`app/public/qr.svg`](app/public/qr.svg), aussi servi par l'app : https://francklin9999.github.io/codeml2026/qr.svg (généré par `npm run qr -- <url>` ; décodé et vérifié) |
| Vidéo de secours | `À COMPLÉTER` |

## 2. Ce que fait l'app

- Elle photographie un verre posé dans la fenêtre d'une feuille de référence imprimée, ou importe une photo d'origine.
- Elle repère la feuille, redresse l'image en vue de dessus à 10 pixels par millimètre, puis isole le verre.
- Elle affiche la largeur **A**, la hauteur **B** (système boxing) et le périmètre en mm, avec une image de contrôle et l'écart entre les photos d'un même verre.
- Elle exporte le contour en SVG à l'échelle 1:1, puis génère une face de monture (deux cercles, pont, tenons) à partir d'un verre gauche et d'un verre droit, avec aperçu 3D et téléchargement de `monture.stl`.
- Tout le calcul se fait dans le navigateur : pas d'installation, pas de compte, pas de clé, aucune photo envoyée à un serveur.

## 3. Tester en 2 minutes

1. Scanner le QR code avec le téléphone (Chrome sur Android, Safari sur iOS).
2. Monter le dispositif de capture : six étapes, dans [`docs/DISPOSITIF_CAPTURE.md`](docs/DISPOSITIF_CAPTURE.md).
3. Toucher « Verre gauche », poser le verre comme l'indique l'écran, « Prendre la photo » (jusqu'à 3 photos), lire A, B et le périmètre, « Valider ».
4. Faire de même pour « Verre droit ».
5. Toucher « Créer la monture », régler la largeur du pont (18 mm par défaut), « Télécharger monture.stl ».

Sans verre ni feuille : ouvrir l'URL suivie de `?demo=1`. Les cinq écrans se parcourent avec des valeurs synthétiques (ce ne sont pas des mesures). `?demo=1&error=NO_LENS` montre un message d'erreur.

## 4. Dispositif de capture

Une feuille imprimée (A4 ou Lettre) posée sur un écran blanc. La feuille porte 18 marqueurs ArUco autour d'une fenêtre de 80 × 65 mm, une règle de contrôle de 100 mm, une ligne guide et l'indication du côté nez pour chaque œil. L'écran, ouvert sur la page de rétro-éclairage de l'app, éclaire le verre par dessous : le bord du verre apparaît sombre sur fond clair.

Matériel, impression, montage en six étapes, pose du verre et dépannage : [`docs/DISPOSITIF_CAPTURE.md`](docs/DISPOSITIF_CAPTURE.md). Feuilles à imprimer : [`rig/out/board_A4.pdf`](rig/out/board_A4.pdf), [`rig/out/board_Letter.pdf`](rig/out/board_Letter.pdf).

Temps de montage par une personne qui ne connaît pas le dispositif : `À COMPLÉTER`.

## 5. Lancement local

Node.js et npm suffisent pour l'app. Commandes de [`app/README.md`](app/README.md) :

```
cd optiframe-participants/app
npm ci            # première fois
npm run dev       # http://localhost:5173 (la caméra demande HTTPS ou localhost)
```

Contrôles et construction :

```
npm run typecheck   # tsc --noEmit
npm test            # Vitest
npm run build       # écrit dist/
npm run size        # après un build : taille du JavaScript initial
npm run preview     # sert dist/ en local
```

Les tests de redressement lisent des images de test qui ne sont pas versionnées. Sur un clone neuf, les générer d'abord ([`rig/README.md`](rig/README.md)) :

```
cd optiframe-participants/rig
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Linux/macOS : .venv/bin/pip
.venv/Scripts/python make_board.py --fixtures
```

Mise en ligne : `.github/workflows/deploy.yml` (à la racine du dépôt Git) construit `app/` et publie `dist/` sur GitHub Pages à chaque poussée sur `main`. Pages doit être activé une fois dans les réglages du dépôt.

## 6. Choix techniques

| Étape | Choix | Raison |
|---|---|---|
| Objet de référence | Feuille imprimée, 18 marqueurs ArUco (`DICT_4X4_50`, 15 mm) autour d'une fenêtre de 80 × 65 mm | Donne l'échelle et la perspective dans le plan du verre ; reste lisible si quelques marqueurs sont cachés. |
| Échelle | Règle de 100 mm imprimée, valeur mesurée enregistrée dans `printScale` | Une imprimante qui réduit la page fausse toutes les mesures ; l'erreur se voit au pied à coulisse et se corrige. |
| Éclairage | Écran blanc sous la feuille (page `lightbox.html` de l'app) | Un verre transparent se voit par son bord : en lumière transmise le bord est sombre sur fond clair. |
| Redressement | OpenCV.js (détection des marqueurs, homographie, image à 10 px/mm) | Bibliothèque recommandée par les consignes ; fonctionne dans le navigateur. |
| Contrôle de la photo | Erreur de reprojection, inclinaison, netteté mesurée sur les marqueurs | Refuser une mauvaise photo avec une phrase claire plutôt que rendre une mesure fausse. |
| Segmentation | Méthode sans IA d'abord (bord sombre du verre) ; modèle entraîné en recours | Conseil des consignes : une mesure fiable sans IA avant tout entraînement. |
| Mesure | Contour sous-pixel de 720 points en mm ; A et B = étendues selon les axes de la feuille (système boxing) | Même définition que le pied à coulisse ; l'horizontale est la ligne guide de la feuille. |
| Parallaxe | Correction d'échelle quand la distance de prise de vue est connue (focale lue dans la photo) | Le bord du verre est au-dessus de la feuille, donc paraît plus grand. |
| Biais | Correction linéaire par axe lue dans `bias.json` (identité tant qu'elle n'est pas ajustée sur de vrais verres) | Corriger une erreur systématique sans toucher au code. |
| Plusieurs photos | Jusqu'à 3 photos par verre, fusion par médiane, rejet des valeurs aberrantes, écart affiché | Une seule mauvaise photo ne décide pas de la mesure. |
| Monture | Contours décalés du jeu, couches extrudées (lèvre, rainure, lèvre), pont, tenons percés, avec manifold-3d | Maillage fermé par construction ; chaque cercle suit son propre verre. |
| Aperçu 3D | three.js, chargé seulement à l'écran de la monture | Le premier écran reste léger. |
| Exports | SVG en mm à l'échelle 1:1 avec barre de 50 mm ; STL binaire ; JSON des mesures | Le jury peut poser le verre sur le tracé imprimé et ouvrir le STL dans un trancheur. |
| Exécution | Calcul dans un Web Worker ; service worker pour le hors ligne ; bibliothèques servies par l'app, sans CDN | L'écran reste réactif ; l'app marche avec peu de connexion ; aucun service tiers. |
| Application | Vite et TypeScript strict, sans cadre d'interface | Cinq écrans, peu de code, site statique. |

## 7. Données et IA

L'app mesure d'abord sans IA. Un petit modèle de segmentation (U-Net, encodeur MobileNetV3-Small, exporté en ONNX, 7,9 Mo) sert de recours quand la méthode sans IA ne trouve pas le verre ; il tourne dans le navigateur et refuse de répondre quand il n'est pas sûr de lui. Le jeu de données se construit sans annotation manuelle : le même verre est photographié une fois en conditions faciles (rétro-éclairé), puis en conditions difficiles sans rien bouger ; le masque de la première photo annote les autres. Des images synthétiques complètent les photos.

**État actuel :** un premier modèle est **livré** (`app/public/models/lens_seg.onnx`). Il est entraîné sur **24 159 images synthétiques** qui imitent la fenêtre du dispositif (rétro-éclairage, papier, table mouchetée, bord du verre faible ou interrompu, reflets, verre teinté ou monté, fenêtre vide), **sans aucune photo réelle** pour l'instant. Sur 600 images synthétiques jamais vues, passées par le code de l'app, 84 % des verres sont mesurés à 1 mm près avec le modèle en recours, contre 17 % sans lui (91 % contre 12 % en rétro-éclairage), sans aucun verre inventé sur une fenêtre vide ni aucun verre coupé par le bord mesuré au lieu d'être refusé (chiffres dans [`docs/DONNEES_ET_IA.md`](docs/DONNEES_ET_IA.md) §7.1). Dans Chrome, il mesure à 0,1 mm près les deux photos de test à bord très faible que la méthode sans IA refusait. Sa justesse sur de vrais verres reste à mesurer : il sera réentraîné avec les photos de la capture appariée.

Détail, tableaux de mesures et séparation par verre : [`docs/DONNEES_ET_IA.md`](docs/DONNEES_ET_IA.md). Photo et images intermédiaires : [`docs/PAS_A_PAS.md`](docs/PAS_A_PAS.md).

## 8. Résultats mesurés

Vérité terrain : pied à coulisse, trois lectures de A et de B par verre. Les tableaux se remplissent avec la sortie de `tools/accuracy_report.py` ([`tools/README.md`](tools/README.md)) sur les photos de [`docs/COLLECTE_DONNEES.md`](docs/COLLECTE_DONNEES.md).

| Nombre de verres | Téléphones | Photos | Erreur moyenne A (mm) | Erreur moyenne B (mm) | Pire cas (mm) | Photos refusées |
|---|---|---|---|---|---|---|
| `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |

| Axe | Biais (mm) | Limites d'accord à 95 % (mm) | Répétabilité (écart-type, mm) | Note prédite sur 30 (médiane) |
|---|---|---|---|---|
| A | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` |
| B | `À COMPLÉTER` | `À COMPLÉTER` | `À COMPLÉTER` | (commune aux deux axes) |

| Autres mesures | Valeur |
|---|---|
| Temps pour une paire de verres sur un téléphone de milieu de gamme | `À COMPLÉTER` |
| Tracé SVG imprimé à 1:1 : écart avec le verre posé dessus | `À COMPLÉTER` |
| Monture imprimée : les verres se clipsent-ils ? | `À COMPLÉTER` |

Repère donné par le mentor de SN-SF : la norme ISO 12870 tolère ±0,5 mm sur la taille du verre et sur le pont ; c'est notre cible. Le barème donne tous les points de précision à 1 mm d'erreur moyenne.

## 9. Limites connues

- **Aucune validation sur de vrais verres à ce jour.** Les tests automatiques utilisent des images synthétiques : ils prouvent que le calcul est cohérent, pas que la mesure est juste sur un verre réel. Tous les seuils de contrôle (netteté, inclinaison, contraste du bord) viennent de ces images : `À COMPLÉTER` sur de vraies photos.
- **Verre transparent sans rétro-éclairage :** le bord est peu contrasté ; la méthode sans IA peut répondre « Je ne trouve pas le verre ». Le rétro-éclairage fait partie du dispositif.
- **Modèle entraîné sur des images synthétiques seulement** (section 7) : sur de vraies photos, il peut se tromper là où la méthode sans IA aurait refusé. Garde-fous : il n'est appelé qu'en recours, il refuse quand sa confiance moyenne est sous 0,85, l'image de contrôle montre le contour, et la fusion de plusieurs photos écarte les mesures incohérentes. Sur table mouchetée sans rétro-éclairage, l'erreur reste d'environ 1,2 mm (synthétique). Premier recours : le modèle (7,9 Mo) et onnxruntime (14 Mo) se téléchargent en arrière-plan dès qu'OpenCV est prêt.
- **Verre posé de travers :** A et B sont mesurés selon les axes de la feuille. L'app avertit au-delà de 5° mais ne redresse pas le verre.
- **Parallaxe :** corrigée seulement si la photo contient la focale (photo d'origine). Hauteur du bord fixée à 3 mm pour tous les verres. Effet réel : `À COMPLÉTER`.
- **Pont :** réglé à la main (14 à 22 mm), pas mesuré.
- **Monture jamais imprimée :** jeu de 0,2 mm et lèvres de 0,5 mm sont des valeurs de départ ; tenons et trous de charnière non essayés. Résultat d'impression : `À COMPLÉTER`.
- **Téléphones :** aucun essai sur un vrai iPhone ou Android à ce jour : `À COMPLÉTER`. Premier chargement lourd (OpenCV.js, environ 13 Mo).
- **Photos passées par WhatsApp :** inutilisables (recompressées) ; utiliser la caméra de l'app ou le fichier d'origine.
- **Lunettes complètes :** l'app mesure un verre libre posé dans la fenêtre, pas un verre monté.

Perspectives pour INOVA (idées étudiées, non construites) :

| Idée | Fichier |
|---|---|
| Motif de réfraction affiché derrière le verre | [`strat4.md`](strat4.md) |
| Polarisation croisée | [`strat12.md`](strat12.md) |
| Capture à deux hauteurs (parallaxe mesurée) | [`strat13.md`](strat13.md) |
| Modèle de forme des verres | [`strat14.md`](strat14.md) |
| Lunettes complètes (verres montés, pont mesuré) | [`strat17.md`](strat17.md) |
| Puissance du verre | [`strat20.md`](strat20.md) |
| Superposition en direct dans la caméra | [`strat16.md`](strat16.md) |

## 10. Outils d'IA utilisés

Déclarés dans [`docs/LICENCES_ET_OUTILS_IA.md`](docs/LICENCES_ET_OUTILS_IA.md), section 4. Chaque membre explique le code de sa partie.

## 11. Sources et licences

Bibliothèques, modèle pré-entraîné et jeux de données, avec leur licence lue dans le paquet installé : [`docs/LICENCES_ET_OUTILS_IA.md`](docs/LICENCES_ET_OUTILS_IA.md). Aucun service payant, aucune API fermée.

## 12. Structure du dépôt

| Dossier | Contenu |
|---|---|
| `app/` | L'application web : `src/capture` (photo), `src/vision` (redressement, segmentation), `src/measure` (A, B, périmètre), `src/quality` (fusion, messages), `src/frame` (monture), `src/export` (SVG, STL, JSON), `src/ui` (écrans), `src/collect` et `collect.html` (collecte de données), `eval.html` (évaluation par lot), `public/` (feuille, bibliothèques, page de rétro-éclairage) |
| `rig/` | Générateur de la feuille de référence (PDF A4 et Lettre) et réglage de l'échelle d'impression |
| `training/data/` | Protocole de capture appariée, masques automatiques, images synthétiques, séparation par verre |
| `training/model/` | Entraînement, export ONNX, évaluation |
| `tools/` | Rapport de précision et vérification du STL |
| `data/` | Modèle de tableau pour les valeurs au pied à coulisse |
| `docs/` | Documents pour le jury et documents de travail |
| [`CHALLENGE.md`](CHALLENGE.md) | Les règles et le barème, tels que nous les lisons |

## 13. Équipe

| Membre | Rôle | Partie du code à expliquer |
|---|---|---|
| `À COMPLÉTER` | Intégration et mise en ligne | `À COMPLÉTER` |
| `À COMPLÉTER` | Capture et vision | `À COMPLÉTER` |
| `À COMPLÉTER` | Données et IA | `À COMPLÉTER` |
| `À COMPLÉTER` | 3D et interface | `À COMPLÉTER` |
| `À COMPLÉTER` | Présentation | `À COMPLÉTER` |
