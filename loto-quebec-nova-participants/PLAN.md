# Plan d'exécution - NOVA

## Objectif

Livrer une mémoire opérationnelle autonome et vérifiable de NOVA, consultable hors ligne, qui préserve l'état de référence du 30 septembre 2026 à 09:00 (Montréal) et permet d'intégrer un événement sans réécrire l'historique.

## Décision d'architecture

- Données éditables dans `data/` (JSON, sans dépendance de lecture).
- Générateur Python dans `scripts/` et logique métier testable dans `nova/`.
- Application statique générée dans `dist/`, ouvrable directement avec `file://`.
- Sources originales copiées dans `dist/corpus/`; rendus HTML avec ancres précises dans `dist/evidence/`.
- Baseline canonique, triée et hachée; événements ajoutés dans `data/events/`; diff explicite des changements et non-changements.
- Recherche locale déterministe et réponses limitées aux faits vérifiés; réponse prudente lorsque le corpus ne documente pas la question.

## Contrats de données

### `data/facts.json`

Liste d'objets avec au minimum: `id`, `subject`, `type`, `statement`, `status`, `date`, `info_as_of`, `actor`, `authority`, `source_file`, `locator`, `quote`, `confidence`, `tags`. Les interprétations vont dans `notes`; les citations demeurent verbatim.

### `data/answers.json`

Objet indexé par `Q01` a `Q10`: `question`, `answer`, `nuance[]`, `fact_ids[]`, `sources[]`. Chaque source possède `file`, `locator`, `label`.

### Registres complémentaires

- `actions.json`: responsable, confirmation du responsable, échéance ou `a confirmer`, origine `engagement` ou `recommandation`, état, faits liés.
- `contradictions.json`: deux affirmations, résolution, règle d'autorité/date, faits liés.
- `risks.json`: probabilité, impact, propriétaire, mitigation, provenance et faits liés.
- `unknowns.json`: manque, impact, personne à interroger, question proposée et faits liés.
- `sources.json`: les 64 fichiers classés et leur date d'information.

## Flux de travail parallèles

1. **Ingestion et preuves**: extraction reproductible des EML/PDF/XLSX/TXT/CSV/PNG, locateurs stables, pages de preuve ancrées, inventaire complet et tests de couverture.
2. **Vérité métier**: lecture du corpus, registre de faits, dix réponses nuancées, brief, actions, contradictions, risques et inconnues; chaque assertion liée à une preuve exacte.
3. **Expérience hors ligne**: application accessible, responsive et imprimable; vues brief, questions, chronologie, décisions, contradictions, actions, risques, sources, limites, versions; recherche locale.
4. **Événements et intégration**: baseline immuable, validation d'autorité, ajout d'événement, état dérivé, diff sourcé, garde-fous, orchestration de build et tests de bout en bout.

## Ordre d'intégration

1. Faire passer extraction + couverture du corpus.
2. Auditer les faits contre les textes et captures.
3. Brancher les vues sur les données réelles et corriger les liens profonds.
4. Geler puis vérifier la baseline.
5. Simuler plusieurs événements: proposition, livraison fournisseur, validation responsable, information ambiguë.
6. Tester hors ligne, impression du brief, clavier, petits écrans et liens de preuves.
7. Exécuter la suite complète, revoir les écarts, corriger, puis pousser un checkpoint.

## Critères d'acceptation

- Les 64 fichiers du manifeste sont traités ou explicitement classés comme bruit/autre projet.
- Q01-Q10 contiennent une réponse exacte et nuancée avec fichier + repère précis.
- Au moins deux contradictions, dont une issue d'un plan ou registre, sont résolues par autorité/date.
- Les trois conditions de go-live ont action, responsable et échéance connue ou `a confirmer`.
- Le brief tient sur une page imprimée et couvre responsable, date/conditions, portée, budget/factures et priorités.
- La recherche et toutes les vues fonctionnent sans réseau ni serveur.
- La baseline reste byte-identique après l'ajout d'un événement; son SHA-256 est vérifié.
- Un événement ne transforme jamais une proposition en décision ni une livraison fournisseur en validation.
- Le diff nomme ce qui change, les réponses/actions touchées et ce qui ne change pas.
- Tous les tests automatisés et le validateur de données passent.

## Périmètre différé tant que le noyau n'est pas vert

- Classeur Excel alternatif.
- Extraction de faits par LLM.
- Démonstrateur multi-projet ORION.
- PDF de repli complet.

