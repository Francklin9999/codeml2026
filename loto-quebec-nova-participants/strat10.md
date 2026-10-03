# NOVA · Strategy 10: Source triage, duplicate detection and coverage audit

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (cheap safety net) |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 step A (corpus + saved attachments) |
| **Rubric lines** | Evidence (distinct sources), Use & uncertainty (limits, follow-up question), trap avoidance on Q05 and Q07 |
| **Work folder** | `loto-quebec-nova-participants/work/strat10/` |

---

## 1. Context you need

Corpus reading rules: *"Certaines pièces jointes sont aussi présentes comme fichiers séparés : ne les comptez pas comme des confirmations indépendantes."* and *"une date de fichier récente ne garantit pas une information exacte."* Verified so far: `08_Archives_et_documents_connexes/Courriel_archive_17sept.eml` has the same headers and body as E12; E02, E03, E07, E10, E11 carry PDF attachments named like standalone files (`Architecture_NOVA_v1.pdf`, `Architecture_NOVA_v2.pdf`, `INV-003.pdf`, `CR-04_Optimisation_mobile_BROUILLON.pdf`, `Rapport_Statut_21sept.pdf`). Distractors: `INV-778_Projet_ORION.pdf`, newsletter, Excel training invite, anonymous personal notes, June preliminary plan.

## 2. The idea

Classify **all 64 files** before answering, mechanically detect duplicates, record the information date of derived documents, and publish a coverage table proving every file was either used or deliberately dismissed.

Classes: `primary` · `derived/stale` · `attachment-copy` · `exact-duplicate` · `other-project` · `noise` · `image-only-evidence`.

## 3. Why it could score

- The Evidence criterion's second finding requires answers that cross **distinct** sources; this tells us which sources really are distinct.
- The follow-up question in the Use criterion ("how do you know you didn't miss anything?") gets a one-table answer.
- It prevents two concrete point losses: counting E03 + Architecture v2 as two confirmations (Q07), and adding INV-778 to NOVA money (Q05).

## 4. Implementation plan

### 4.1 Files

```
work/strat10/
  triage.py
  classes.yaml        # manual class + reason per file (the script pre-fills what it can)
  duplicates.csv
  coverage.md         # generated
```

### 4.2 Duplicate detection

```python
import hashlib, pathlib
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
corpus = {rel: sha(p) for rel, p in corpus_files()}
attach = {name: sha(p) for name, p in saved_attachments()}   # from strategy 1 step A
for a_name, a_hash in attach.items():
    match = [rel for rel, h in corpus.items() if h == a_hash]
    # if no byte match, compare normalised extracted text (PDF metadata can differ)
```

Email duplicates: compare `(From, Date, Subject, normalised body)` across all `.eml` files.

### 4.3 Information dates for derived documents

| Document | File date | Information date | Evidence |
|---|---|---|---|
| `Registre_Risques_29sept.xlsx` R-01 | 29 Sept | 9 Sept | cell H2 "Suivi au 9 septembre 2026" |
| `Rapport_Statut_21sept.pdf` | 21 Sept | before detailed ticket checks | its own management comment |
| `Plan_Projet_NOVA_v3_12sept.xlsx` | 12 Sept | not updated after 10 Sept decision | Teams 15 Sept |
| `Plan_Projet_NOVA_v2.xlsx` | earlier | PM = Élodie | — |
| `Plan_NOVA_preliminaire_juin.xlsx` | June | "Version préliminaire" | cell G3 |
| `Charte_Projet_NOVA_v1.txt` | 7 Jul | not updated automatically | its last line |

### 4.4 Coverage table

For each of the 64 files: path, class, information date (if derived), used by (fact IDs / answers), duplicate group, dismissal reason (for noise / other project), transcription status (for PNGs). Render as Markdown and as a page in strategy 1's site.

### 4.5 Image-only evidence

The 8 PNGs get a manual transcription file each. Priority: `OPS-601_runbook.png` (steps 1–3 OK, step 4 rollback TODO, step 5 post-deployment functional validation "À compléter"; version of 25 Sept per the analysis; verify), `ACC-303_focus.png`, `SEC-210_audit.png`, `INT-101_aucun_resultat.png`. Reminder from the rules: *"Une capture historique ne démontre pas à elle seule qu'un défaut reste ouvert."* Pair each screenshot with the dated ticket comment that gives its current status.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Attachment ↔ standalone table | 5 attachments classified as exact / same text / different |
| T2 | Email duplicates | `Courriel_archive_17sept.eml` ↔ E12 detected |
| T3 | Coverage | 64/64 files classified; 0 "unknown"; every `primary` file cited by ≥ 1 fact or has a reason |
| T4 | Independence check | for each answer claiming ≥ 2 sources, the sources are in different duplicate groups |
| T5 | Distractor guard | no fact uses `other-project` or `noise` files as support |

## 6. Risks

None significant; it is cheap. Do it early so other strategies cite the right files.

## 7. Combines with

Strategy 1 (sources page), 7 (source pages show "copie de…"), 2 (Q05 and Q07 atoms, Evidence T3).

## 8. Results log

| Date | Who | Duplicates found | Coverage | Verdict |
|---|---|---|---|---|
| | | | | |
