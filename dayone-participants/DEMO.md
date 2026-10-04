# Demo script (≈ 3 minutes)

Shows what the brief asks for: **an offline capture, the return of connectivity, the review of an uncertain
field and a patient-match decision** — plus the quality gate, re-scan diff and privacy.

## Setup (once, before the jury)

```bash
./run_box.sh            # or .\run_box.ps1 on Windows — edge box + phone app on port 8765
```

Open `http://<box-ip>:8765` on a phone on the same Wi-Fi (or a desktop browser). Seed two known patients so the
match step has candidates (simulates earlier visits):

```bash
curl -X POST http://localhost:8765/admin/seed -H "Content-Type: application/json" -d "{\"patients\":[{\"code\":\"2026-987-006\",\"facts\":{\"ddr\":\"21/11/2025\",\"date_prevue\":\"28/08/2026\"}},{\"code\":\"2026-987-008\",\"facts\":{\"ddr\":\"02/02/2025\"}}]}"
```

Demo photos (synthetic specimen pages photographed with phone-like degradations) are in
`work/strat15/app/testdata/`: `p1_cover.jpg`, `p3_grossesse.jpg`, `p4_accouchement.jpg`, `blurry.jpg`.

## Script

| # | Action | What the jury sees | Rubric |
|---|---|---|---|
| 1 | Unlock with the PIN | records are encrypted with a key derived from the PIN; a wrong PIN is refused | Privacy |
| 2 | Tap 📶 → 📴 (offline) | header says *hors ligne* | Offline |
| 3 | 📷 send `blurry.jpg` | "La photo est floue…" → *Reprendre la photo* (on-device quality gate) | Bonus |
| 4 | 📷 send the 3 pages | each: "📥 Page reçue et chiffrée… en attente de traitement IA" ; ☰ shows 3 × EN_ATTENTE_IA | Offline |
| 5 | Reload the page / close the app, unlock again | "3 dossier(s) en cours repris": nothing lost | Offline |
| 6 | Tap 📴 → 📶 (online) | "📶 La connexion est revenue…", pages go TRAITÉ_IA | Offline |
| 7 | Review | "📄 Page « Accouchement » lue : 29 champs sûrs, 1 à vérifier…" then a question **with the image crop**: "Je ne suis pas sûre de « … » : j'ai lu « … » (62 %)" → *Corriger* and type the value; on another one *Confirmer*; on an illegible one *Saisir la valeur* / *Inconnu* | Uncertainty, Review |
| 8 | (long page) | after 8 questions: "Il reste N champs incertains" → *Continuer* or *Valider, garder « à réviser »* (doubt stays recorded) | Review |
| 9 | *Terminer le registre* | "🔎 Vérification croisée" (DDR + 280 j, ages, same fact on two pages) | Extraction |
| 10 | Match | "Code lu sur la fiche : 2026-987-006" → *Patiente 1 · DDR 21/11/2025 ✓* / *Aucune, créer* / *Je ne sais pas* → choose **Patiente 1** | Linking |
| 11 | Sync | "☁️ Synchronisé (3 page(s))"; ☰ shows SYNCHRONISÉ | Offline |
| 12 | Send `p3_grossesse.jpg` again, finish | "📚 Page déjà numérisée…" diff → *Mettre à jour* / *Garder l'ancien* (re-digitisation) | Review |
| 13 | Open `http://<box>:8765/dashboard` | anonymised aggregates from the synced records, cells < 5 suppressed, missing shown | Bonus |
| 14 | Toggle **EN** | the same agent in English | Bonus |

Also worth showing: a real booklet photo (`data/Paper Registry/1-3.jpg`) → "🤔 Je ne reconnais pas cette page…
Je préfère ne rien inventer" (*Reprendre la photo* / *Saisie manuelle*): the agent never hides its doubt.

## Automated rehearsal

The same flow is exercised by the test suites (`pytest work/`) and was run end-to-end in a browser on 2026-10-03
(see `work/RESULTS_SUMMARY.md`).
