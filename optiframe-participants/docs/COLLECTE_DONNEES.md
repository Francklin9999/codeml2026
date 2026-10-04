# Collecte de données réelles : la liste

> **À quoi ça sert :** les agents n'ont ni verre, ni téléphone, ni pied à coulisse. Tout ce qui est mesuré « pour de vrai » (précision, métriques du modèle, biais) dépend de ce que tu collectes. Cette liste dit quoi apporter, quoi photographier et comment, pour que la page `collect.html` de l'app (brief 17) range tout correctement.
> **État :** v1 écrite avant la page de collecte. Le brief 17 la garde cohérente avec l'app (noms de fichiers, modes, quantités).
> **Contexte du Discord :** [`MENTOR_NOTES.md`](MENTOR_NOTES.md).

---

## 0. Résumé : ce que j'ai besoin de toi

| # | Donnée | Quantité visée | Minimum utile | Ça sert à | Mode de la page |
|---|---|---|---|---|---|
| 1 | Valeurs au **pied à coulisse** (A et B, 3 lectures chacun) | 15 verres | 8 verres | Vérité terrain : tout chiffre de précision en dépend | Validation |
| 2 | Photos de **validation** : même verre, 3 répétitions, 1 à 2 téléphones | 15 verres × 3 × 2 téléphones = 90 | 8 × 3 × 1 = 24 | Erreur moyenne A et B, prédiction de la note, `bias.json` | Validation |
| 3 | Photos **appariées** : même scène, 8 éclairages sans bouger | 15 verres × 6 positions × 8 conditions = 720 | 8 × 3 × 5 = 120 | Entraîner le segmenteur sans annoter à la main | Entraînement |
| 4 | Photos **libres** : lunettes montées du stand SN-SF, verres sur surfaces variées, cas durs | ~10 paires + 30 photos de cas durs | 10 paires | Tester la segmentation sur des cas que nous ne fabriquons pas | Libre |
| 5 | **Cas d'échec voulus** (feuille coupée, flou, main dans le champ, reflet fort) | 10 photos | 5 | Vérifier que l'app refuse avec une phrase claire, sans planter | Libre |

Temps estimé : mesures 30 min, validation 45 min, paires (version complète) 2 h ou version courte 40 min, libres 30 min.

## 1. Matériel à réunir

- [ ] **Pied à coulisse** (résolution 0,05 mm ou mieux). Les pieds à coulisse des tables de mesure sont partagés et ont été emportés par des équipes : demande qu'on en laisse, ou emprunte-en un pour toute la séance de mesure.
- [ ] **Feuille de référence** imprimée à 100 % (`rig/out/board_A4.pdf` ou `board_Letter.pdf`). Mesure la règle de 100 mm au pied à coulisse puis lance `python rig/set_print_scale.py <valeur mesurée>`.
- [ ] **Écran blanc** (portable ou tablette) pour le rétro-éclairage : page `lightbox.html`, luminosité au maximum. Prévois une feuille de papier calque en cas de moiré.
- [ ] **Téléphones :** idéalement un iPhone récent et un Android milieu de gamme. Note le modèle exact de chacun (il entre dans les noms de fichiers).
- [ ] **Support fixe** pour le téléphone (pile de livres, support de bureau). Indispensable pour les photos appariées.
- [ ] **Éclairages** pour les photos appariées : lampe de bureau (3 directions), flash du téléphone, une page imprimée à motif (texte, bois ou tissu), un écran qui affiche du rose ou du bleu.
- [ ] **Sachets étiquetés** (L01, L02…). On n'écrit jamais sur un verre.
- [ ] Ruban adhésif, ciseaux ou cutter (la fenêtre de la feuille), batteries chargées.

## 2. Les verres

**Cible : 15 verres, au minimum 8.** Varie tout ce qui peut faire échouer la mesure :

| Critère | Ce qu'il faut avoir |
|---|---|
| Teinte | clair, teinté léger, solaire foncé, anti-reflet |
| Puissance | plus fort (bord mince, rim peu visible), moins fort (bord épais, bande sombre large), plano |
| Forme | ovale, rectangle arrondi, rond, aviateur, œil de chat, un verre asymétrique |
| Particularités | rayé, poussiéreux, avec encoche ou perçage si tu en as |
| Taille | du plus petit au plus grand (35 à 65 mm de large) |

**Sources :** vieilles lunettes de la famille ou d'amis, lunettes de lecture ou solaires bon marché dont on sort les verres, et les **~10 paires du stand SN-SF** (elles doivent rester au stand : on les photographie là-bas, mode Libre, et on mesure leurs verres montés au pied à coulisse sans les démonter).

Pour chaque verre, note : identifiant (L01…), œil (gauche ou droit, côté nez), description courte, teinte, épaisseur de bord.

## 3. Mesure au pied à coulisse (vérité terrain)

Le jury mesure en **système boxing** : **A** = largeur du rectangle qui enserre le verre, **B** = sa hauteur, côtés parallèles et perpendiculaires à l'horizontale du verre.

1. Pose le verre à plat, face bombée vers le haut, aligné sur la ligne guide de la feuille (c'est notre axe horizontal).
2. Mesure A puis B : mâchoires parallèles aux axes, serrage léger. **Trois lectures par dimension**, en reposant le verre entre deux lectures.
3. Idéalement une deuxième personne refait les mesures sans voir les premières (bruit de la vérité terrain).
4. Écris les six valeurs (A1 A2 A3 B1 B2 B3) et l'épaisseur du bord. Elles se saisissent dans la page, mode Validation.
5. Pour une **paire montée** : A et B de chaque ouverture, plus la distance entre les verres (pont, DBL). La cible de SN-SF est environ **0,5 mm** sur largeur, hauteur et pont.

## 4. Les photos

**Règles communes.** Photos prises avec la page de collecte (caméra native, fichier original conservé). **Pas de WhatsApp** (recompression). Feuille entière visible, téléphone à plat à 35 à 45 cm, verre au centre de la fenêtre. Aucun visage, aucun nom, aucune ordonnance dans le cadre.

### Jeu A : validation (précision)
Pour chaque verre : 3 répétitions par téléphone, en reposant la feuille et le téléphone entre deux répétitions au moins une fois. Nom : `<verre>_<téléphone>_<rep>.jpg` (la page le fait). Ajoute 4 photos de stress sur 4 verres : inclinaison 10° et 20°, distance 30 et 50 cm, éclairage de pièce, fenêtre.

### Jeu B : entraînement (paires)
Téléphone **fixé**, verre **immobile** pendant tout un groupe. Pour chaque position du verre : 1. `easy` (rétro-éclairé, d'abord), 2. `room` (lumière de la pièce, écran éteint), 3. `lampL`, 4. `lampT`, 5. `lampR` (lampe de bureau de gauche, du dessus, de droite), 6. `flash`, 7. `pattern` (page à motif sous la feuille), 8. `colour` (écran rose ou bleu). Puis tu bouges ou tournes le verre et tu recommences (6 positions). Version courte : `easy`, `room`, `lampL`, `flash`, `pattern` sur 3 positions de 8 verres.

### Jeu C : libre
- Les **paires du stand SN-SF** : 3 photos par paire sur un fond uni (de face, avec et sans reflet), plus une photo de chaque verre posé sur la feuille si ça tient dans la fenêtre. Note l'identifiant de la paire sur ta feuille de notes, pas sur la paire.
- **Surfaces difficiles :** verre posé sur papier moucheté ou poussiéreux sans rétro-éclairage (le cas que d'autres équipes montrent sur le Discord), sur du bois, du tissu, un écran allumé.
- **Retourné :** un verre face concave vers le haut, un verre très réfléchissant.

### Cas d'échec voulus (10 photos)
Feuille coupée, feuille très inclinée, photo floue, main dans le champ, reflet du flash sur le verre, verre qui dépasse de la fenêtre, verre tourné de 10° par rapport à la ligne guide, fenêtre vide. L'app doit répondre par une phrase claire, jamais par une erreur technique.

## 5. Ce que je fais ensuite des données

| Données | Traitement | Résultat |
|---|---|---|
| Jeu A + valeurs du pied à coulisse | `tools/accuracy_report.py` (ou la page `eval.html`) | Erreur moyenne A et B, limites d'accord, répétabilité, note prédite, `bias.json` |
| Jeu B | `training/data/autolabel.py` puis `training/model/train.py` | Masques sans annotation manuelle, modèle ONNX, métriques sur verres jamais vus |
| Jeu C et échecs | Relecture visuelle, mesure directe | Cas qui cassent, messages à ajuster, jeu de test final |

## 6. Faire passer les photos du téléphone à l'ordinateur

1. Dans la page de collecte, bouton **Exporter** : un ou plusieurs ZIP (50 Mo maximum chacun) contenant les photos originales, `manifest.csv`, `own_lenses.csv`, `results.csv`.
2. Partage-les (AirDrop, Drive, câble) vers l'ordinateur.
3. Décompresse dans `training/_local/raw/` (ce dossier n'est pas versionné).
4. Le bouton « Vider les photos exportées » ne supprime que ce qui a été exporté, après confirmation.

## 7. Pour que l'app serve depuis ton téléphone

- La caméra native (`capture`) fonctionne même en HTTP, mais le partage de fichiers et le service worker demandent **HTTPS**.
- Local : `npm run dev -- --host` dans `app/`, puis ouvre l'adresse du réseau local sur le téléphone (HTTP : export par téléchargement seulement).
- HTTPS : déploiement GitHub Pages (`.github/workflows/deploy.yml`, à activer dans les réglages du dépôt) ou un tunnel temporaire (toléré par le brief). La mise en ligne est une décision à prendre par toi.

## 8. Questions ouvertes à poser sur le Discord (voir `CHALLENGE.md` §10)

- Les verres d'évaluation sont-ils des **verres libres** ou des **lunettes montées** ? (Le stand propose des paires montées pour tester la segmentation.)
- Dans quelle **orientation** le jury tient-il chaque verre pour le pied à coulisse ? Où est le côté nasal si on n'a pas le droit de marquer ?
- Quels types de verres : clairs ou teintés, plus ou moins, biseau ?
- Peut-on prendre **plusieurs photos par verre** ?
- Qui imprime le **SVG 1:1** pendant l'évaluation ?
- Une **imprimante 3D** est-elle disponible sur place ?
- Peut-on garder un **pied à coulisse** à notre table ?

## 9. Checklist de séance

- [ ] Feuille imprimée, règle de 100 mm vérifiée, `printScale` enregistré
- [ ] Téléphone chargé, modèle noté, page de collecte ouverte, stockage persistant accepté
- [ ] Pied à coulisse sur la table, sachets étiquetés
- [ ] Pour chaque verre : 6 mesures saisies, 3 photos de validation, (paires : groupes d'éclairage)
- [ ] Export ZIP fait et copié sur l'ordinateur **avant** de vider quoi que ce soit
