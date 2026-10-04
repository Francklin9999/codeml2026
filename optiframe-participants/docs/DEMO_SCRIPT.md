# OptiFrame : script de démonstration

> **Format imposé par les consignes :** 5 minutes sur téléphone, en direct, puis 2 minutes de questions.
> **Ce que le jury note (10 points) :** « Démo claire sur téléphone, choix justifiés, limites reconnues honnêtement ».
> **Règle de ce document :** tout chiffre annoncé au jury vient des tableaux de résultats de [`TEST_PLAN.md`](TEST_PLAN.md). Les champs marqués `À COMPLÉTER` se remplissent avec nos mesures, jamais de mémoire.

---

## 1. Qui fait quoi pendant la démo

| Rôle | Personne | Tâche |
|---|---|---|
| Voix | `À COMPLÉTER` | Parle. Ne touche à rien. |
| Téléphone | `À COMPLÉTER` | Manipule l'app. Écran recopié ou tenu face au jury. |
| Dispositif | `À COMPLÉTER` | Monte le dispositif, pose les verres, tend la feuille d'instructions au jury. |
| Chrono et secours | `À COMPLÉTER` | Chronomètre, tient le deuxième téléphone déjà ouvert sur l'app, lance la vidéo de secours si besoin. |

Chaque membre doit pouvoir expliquer sa partie : le jury peut interroger n'importe qui.

## 2. Avant de monter sur scène

- [ ] App ouverte sur les deux téléphones de l'équipe (un iPhone, un Android), batterie au-dessus de 50 %, mise en veille désactivée, mode « ne pas déranger ».
- [ ] QR code imprimé en grand, lisible à 2 mètres.
- [ ] Kit du dispositif complet, feuille d'instructions sur le dessus.
- [ ] Paire de verres de démonstration, avec ses valeurs au pied à coulisse notées sur une fiche.
- [ ] Tracé SVG 1:1 de cette paire, déjà imprimé.
- [ ] `monture.stl` de cette paire déjà téléchargé une fois (preuve que le téléchargement fonctionne) ; face imprimée sur la table si elle existe.
- [ ] Partage de connexion prêt sur un téléphone.
- [ ] Vidéo de secours lisible hors ligne, sur un téléphone et sur un portable.
- [ ] Une répétition complète chronométrée il y a moins d'une heure.

## 3. Les 5 minutes

| Temps | Ce qu'on montre | Ce qu'on dit (idée, pas mot à mot) |
|---|---|---|
| **0:00 → 0:30** | Le QR code. Le jury le scanne pendant qu'on parle. | « Un verre recyclé a sa propre forme. Pour lui dessiner une monture, l'opticien utilise une traceuse. Nous la remplaçons par un téléphone : une photo, le contour au millimètre, une monture prête à imprimer. Rien à installer : scannez ce code. » |
| **0:30 → 1:15** | Montage du dispositif, en direct, chronométré à voix haute. La règle imprimée sur la feuille de référence. | « Le dispositif tient dans une enveloppe et se monte en moins de deux minutes. Cette règle imprimée prouve que l'échelle est juste : si l'imprimante a réduit la feuille, on le voit tout de suite, et l'app en tient compte. » |
| **1:15 → 2:30** | Mesure d'un verre gauche puis d'un verre droit de formes différentes. Image de contrôle. A, B, périmètre. Écart entre les prises. | « L'app repère la feuille, redresse l'image, isole le verre et mesure. Voici l'image de contrôle : le contour est tracé sur la photo. Nous mesurons selon le système boxing, l'axe horizontal étant la ligne guide de la feuille. Largeur A : … mm, hauteur B : … mm. Au pied à coulisse, nous avions … et … . L'app a pris plusieurs photos : l'écart entre elles est de … mm. » |
| **2:30 → 3:15** | Réglage du pont à 18 mm, aperçu 3D, superposition du contour et du cercle avec le jeu en mm, téléchargement de `monture.stl`. Le tracé 1:1 imprimé avec le verre posé dessus. La face imprimée si elle existe. | « Deux verres de formes différentes, une seule monture. Chaque cercle est le contour mesuré, décalé d'un jeu de … mm pour le clipsage. Le fichier est un maillage fermé, imprimable à plat sans supports. Voici le tracé à l'échelle 1:1 : le verre l'épouse. » |
| **3:15 → 4:15** | Une diapositive : le jeu de données et les mesures de performance. | « Pour l'IA, le difficile est d'obtenir des contours annotés. Nous n'avons rien annoté à la main : le même verre est photographié une fois dans des conditions faciles, où le contour s'obtient sans IA, puis plusieurs fois dans des conditions difficiles, sans rien bouger. La première photo annote les autres. En attendant les photos, nous avons simulé notre dispositif : 16 000 images synthétiques, bord du verre faible ou interrompu, reflets, poussières, verre teinté ou monté, sans une seule annotation. Sur des images jamais vues, le modèle trouve le verre avec un recouvrement de 97 %, contre 40 % pour un seuillage simple ; et quand la méthode classique abandonne, il fait mesurer la majorité des verres à moins d'un millimètre. Sur de vrais verres : `À COMPLÉTER`. L'IA sert de recours quand la méthode classique échoue, et elle se tait quand elle n'est pas sûre d'elle ; elle ne remplace jamais une mesure fiable. » |
| **4:15 → 4:45** | Une diapositive : les limites. | « Ce qui ne marche pas encore : `À COMPLÉTER` (voir section 5). Dans ces cas, l'app le dit clairement et demande une nouvelle photo. » |
| **4:45 → 5:00** | Le QR code de nouveau. | « Le code est public, les sources et licences sont dans le README. Pour le test de novembre avec SN-SF, notre prochaine étape serait `À COMPLÉTER`. Merci. » |

**Si le jury teste lui-même pendant ces 5 minutes :** on lui tend la feuille d'instructions et on se tait. Le montage par un inconnu est précisément ce qui est évalué.

## 4. Plan de secours

| Problème | Réaction, dans cet ordre |
|---|---|
| L'app ne se charge pas sur le téléphone du jury | 1. Partage de connexion. 2. Téléphone de l'équipe déjà ouvert sur l'app. 3. Vidéo de secours. |
| La caméra est refusée | Bouton d'import de fichier : photo prise avec l'appareil photo du téléphone, puis importée. |
| Une mesure est manifestement fausse | Le dire, reprendre la photo une fois. Si l'erreur persiste : l'annoncer comme une limite et passer à la suite. |
| Le téléchargement du STL échoue | Montrer le fichier déjà téléchargé, et la face imprimée. |
| Dépassement de temps à 4:15 | Sauter la diapositive des données et aller aux limites. Les limites comptent dans la note. |

On ne débogue jamais en direct.

## 5. Limites à annoncer

À remplir à partir de l'étude de validation. Ne garder que ce qui a été observé.

| Limite observée | Ce que fait l'app | Mesure à l'appui |
|---|---|---|
| `À COMPLÉTER` (exemples possibles : verres très épais, verres teintés foncés, verres percés, photo trop inclinée, éclairage ambiant fort) | `À COMPLÉTER` | `À COMPLÉTER` |

## 6. Questions probables

Réponses à préparer avec nos propres chiffres. La colonne « Qui » indique le membre qui répond.

| Question | Éléments de réponse | Qui |
|---|---|---|
| Comment savez-vous que c'est précis à 1 mm ? | Étude de validation sur nos verres : nombre de verres, de téléphones, de répétitions ; erreur absolue moyenne `À COMPLÉTER` ; pire cas `À COMPLÉTER`. Vérité terrain au pied à coulisse, trois lectures par verre. | V |
| Et si la feuille est imprimée à la mauvaise échelle ? | Règle de contrôle imprimée sur la feuille ; consigne « imprimer à 100 % » ; la taille réelle mesurée est celle que l'app utilise. | V |
| Pourquoi mesurer sans IA d'abord ? | Les consignes le recommandent ; sur notre dispositif le bord du verre est assez contrasté pour être mesuré directement ; l'IA intervient quand les contrôles de qualité échouent. Sur images synthétiques, quand la méthode classique mesure, elle est très juste (environ 0,1 à 0,2 mm sur rétro-éclairage) mais elle refuse les bords faibles ; le modèle rattrape ces refus ([`DONNEES_ET_IA.md`](DONNEES_ET_IA.md) §7.1). Sur vrais verres : `À COMPLÉTER`. | D |
| Qu'apporte votre modèle par rapport à un modèle pré-entraîné ? | Un modèle généraliste ne sait pas ce qu'est le bord d'un verre sur notre feuille ; le nôtre (7,9 Mo, dans le navigateur) est affiné sur la fenêtre exacte que l'app redresse, à échelle connue, et sait dire « rien ici » (fenêtres vides dans l'entraînement, seuil de confiance à 0,85). Comparaison sur les mêmes photos difficiles réelles : `À COMPLÉTER`. | D |
| D'où viennent vos données ? Y a-t-il des données personnelles ? | Nos propres verres, photographiés par nous ; images synthétiques ; aucune photo de visage, aucun nom, aucune ordonnance. Sources et licences dans le README. | D |
| Pourquoi tout dans le navigateur ? | Pas de serveur à maintenir, les photos restent sur le téléphone, l'app fonctionne avec peu ou pas de connexion : le contexte humanitaire des consignes. | L |
| Comment le verre tient-il dans la monture ? | Cercle décalé d'un jeu de `À COMPLÉTER` mm, rainure, lèvres ; valeur ajustée après essai d'impression : `À COMPLÉTER`. | F |
| Le fichier STL est-il vraiment imprimable ? | Maillage fermé vérifié automatiquement et dans un trancheur ; face à plat, sans supports ; essai réel : `À COMPLÉTER`. | F |
| Que se passe-t-il avec deux verres de formes différentes ? | Chaque cercle suit son propre contour ; les deux sont alignés sur l'axe horizontal et reliés par le pont. Montré en direct. | F |
| Quelle est la différence entre votre A et celui du pied à coulisse ? | Même définition : rectangle englobant, côtés parallèles à l'horizontale du verre. L'horizontale est la ligne guide. Si le verre est posé de travers, l'app avertit. | V |
| L'épaisseur du verre fausse-t-elle la mesure ? | Oui, par parallaxe : le bord est quelques millimètres au-dessus de la feuille. Effet estimé `À COMPLÉTER` mm, corrigé par `À COMPLÉTER`. | V |
| Quels outils d'IA avez-vous utilisés pour coder ? | Liste déclarée dans le README. Chaque membre explique le code de sa partie. | L |
| Que feriez-vous avec une semaine de plus ? | `À COMPLÉTER` : choisir dans la liste « Parked » de [`WINNING_PLAN.md`](WINNING_PLAN.md). | Voix |
| Qu'est-ce qui ne marche pas ? | La section 5, sans détour. | Voix |

## 7. Vidéo de secours

- Durée : moins de 2 minutes. Même déroulé que la section 3, sans la diapositive des données.
- Filmée en une prise, téléphone visible en entier, sans montage qui cacherait un échec.
- Enregistrée après le gel des fonctionnalités, avec la version en ligne.
- Stockée hors ligne sur deux appareils.

## 8. Répétitions

| N° | Heure | Durée mesurée | Ce qui a accroché | Corrigé |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
