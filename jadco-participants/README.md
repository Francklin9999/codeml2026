# JADCO — Collection Équinoxe

Le point d’entrée de livraison est [`work/final/README.md`](work/final/README.md).
Le dossier `work/final/` contient le notebook exécuté, ses sources, les tables publiques, le modèle comparateur entraîné et les contrôles.
Les CSV CRM restent à la racine : ils ne sont jamais inclus dans le bundle.

## Prêt pour le jury

- [`work/submission/jadco_submission.zip`](work/submission/jadco_submission.zip) : bundle vérifié, avec manifeste SHA-256.
- [`work/presentation/presentation.pdf`](work/presentation/presentation.pdf) : huit diapositives avec graphiques calculés.
- [`work/presentation/PRESENTATION.md`](work/presentation/PRESENTATION.md) : notes de présentation et réponses aux questions du jury.
- [`work/final/outputs/final_answer.json`](work/final/outputs/final_answer.json) : estimation, définition, bandes et scénarios.
- [`work/final/AUDIT_PROGRESS.md`](work/final/AUDIT_PROGRESS.md) : provenance, corrections et limites.

## Reconstruire et vérifier

Avec l’environnement du projet activé :

```bash
cd work/final
python release.py --rebuild
```

Cette commande exécute le modèle, lance le gate et les tests, régénère les documents et le PDF, puis reconstruit le ZIP.
Pour valider et empaqueter le notebook déjà exécuté : `python release.py`.
`outputs/validation.json` consigne les versions réellement utilisées, les contrôles et les empreintes des résultats.

## Organisation

`work/external/` conserve les sources publiques et leurs scripts de collecte ; `work/final/external/` livre les tables publiques nécessaires hors réseau.
`archive/` conserve les stratégies et prototypes exploratoires ; ils ne sont pas des entrées supportées.
Les données CRM, le notebook de départ et les consignes d’origine restent à leur emplacement.
