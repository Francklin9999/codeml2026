# NOVA - mémoire opérationnelle fiable

Application statique autonome pour reprendre le projet fictif NOVA au 30 septembre 2026 à 09:00 (Montréal), retrouver chaque preuve et intégrer un événement sans effacer la baseline.

## Ouvrir la livraison

Après construction, ouvrez directement `dist/index.html` dans Edge, Chrome ou Firefox. Aucun serveur, compte, abonnement ou accès réseau n'est requis.

```powershell
python -m pip install -r requirements.txt
python scripts/extract_corpus.py
python scripts/build_site.py --freeze-baseline
```

La livraison offre le brief d'une page, Q01-Q10, chronologie, décisions, contradictions, actions, risques, sources, limites, recherche locale et comparaison des versions. Les liens de preuve ouvrent le passage exact dans une copie HTML locale du corpus.

## Intégrer l'événement du jury

Prévisualiser sans modifier l'historique :

```powershell
python scripts/manage_event.py preview examples/event_security_validation.json --output tmp/event-preview.json
```

Après avoir adapté le JSON à l'information reçue, l'ajouter au journal puis reconstruire :

```powershell
python scripts/manage_event.py append mon-evenement.json
python scripts/build_site.py --freeze-baseline
```

Le moteur refuse notamment qu'une proposition remplace une décision, qu'une livraison fournisseur vaille validation, qu'un événement modifie silencieusement un autre sujet ou qu'un identifiant soit rejoué. La baseline et son SHA-256 demeurent inchangés.

## Vérifier

```powershell
python -m unittest discover -s tests -v
node --check app/assets/app.js
```

La suite couvre l'extraction des 64 sources, les 619 locateurs uniques, les citations verbatim, les liens/ancres, l'interface hors ligne, le brief, l'immuabilité et les scénarios d'événement.

## Structure

- `data/` : faits vérifiés, réponses, brief et registres métier.
- `nova/` : extraction, validation, baseline et règles d'événement.
- `app/` : interface statique accessible et imprimable.
- `scripts/` : extraction, build et gestion d'événements.
- `examples/` : événements de démonstration.
- `dist/` : livraison générée, volontairement ignorée par Git.

## Outils, traitements manuels et limites

Python, `pypdf`, `openpyxl`, HTML/CSS/JavaScript et assistance IA ont été utilisés. Les citations, l'autorité des sources, les calculs financiers, les contradictions et les huit captures ont été revus humainement. La capture du runbook est transcrite précisément; les sept autres captures restent conservées mais ne servent pas seules à conclure un statut courant. L'écart de taille de `README.txt` entre le manifeste et le ZIP est signalé sans masquer le fichier réel. Toute échéance absente est marquée « à confirmer ».

