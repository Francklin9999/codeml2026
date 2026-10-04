# Extraction reproductible du corpus NOVA

La commande suivante reconstruit les artefacts locaux et l'inventaire versionné :

```powershell
python scripts/extract_corpus.py
```

Entrée : `NOVA_ETUDIANTS.zip`. Sorties locales : `work/_local/corpus`, `text`,
`attachments`, `images`, `transcriptions`, `evidence`, `locators.jsonl` et
`inventory.json`. L'inventaire consommable par l'application est écrit dans
`data/sources.json`.

Le pipeline traite les EML (en-têtes, corps, pièces jointes), les PDF page par
page, les XLSX cellule par cellule, les TXT/CSV/MD et les PNG. Chaque unité de
preuve reçoit un locateur stable et une ancre HTML. Les formats inconnus, pages
PDF sans texte, erreurs de décodage et écarts de contenu du manifeste provoquent
un échec explicite. L'écart de taille connu de `README.txt` dans le manifeste est
conservé comme avertissement visible (`7103` octets déclarés contre `5741` dans
le ZIP), sans masquer l'extraction réussie du fichier réel.

Les transcriptions PNG ont un état explicite. Celle de
`OPS-601_runbook.png` est renseignée; les sept autres fichiers portent la mention
`expected` et doivent être vérifiés manuellement avant d'être cités seuls. Une
capture historique ne suffit jamais à conclure au statut courant d'un ticket.

Tests :

```powershell
python -m unittest discover -s tests -p "test_extraction.py" -v
```
