# NOVA · Strategy 1: Curated fact ledger + offline static site

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P1 (foundation and conservative path) |
| **Effort** | 8–10 h |
| **Depends on** | nothing; strategies 2–10 build on its corpus extraction and `facts.yaml` |
| **Rubric lines** | every line, because this is the artefact the jury opens |
| **Work folder** | `loto-quebec-nova-participants/work/strat1/` |

---

## 1. Context you need

- **Challenge:** build an "operational memory" of the fictional NOVA project as of **30 Sept 2026, 09:00 Montréal (UTC−04:00)**. A new event is given during the final presentation and must be integrated without erasing history.
- **Data:** `NOVA_ETUDIANTS.zip` = 64 corpus files + `README.txt` (rubric + the 10 questions) + `MANIFEST.csv`. Everything is fictional, so AI tools are allowed but must be declared.
- **Rubric (100):** Q01–Q10 = 50 (0/3/5 each, for accuracy **and nuance**); Evidence 10; Chronology & contradictions 10; Brief & actions 10; Use & uncertainty 10; Update after event 10. *"Une belle interface, une technologie particulière ou le seul recours à l'IA ne donnent pas de points supplémentaires."* The jury must not need a paid subscription.
- **Required deliverables:** (1) 1-page brief; (2) searchable memory: timeline, decisions, resolved contradictions, sources, remaining actions (owner, evidence, due date, commitment vs recommendation); (3) the 10 answers, each with file + precise locator; (4) post-event state + diff, baseline kept; (5) short user guide.
- **Full analysis and draft answers:** `ANALYSE_CHALLENGES.md` §7.1.

## 2. The idea

Hand-curate, with LLM help but human verification, a **`facts.yaml` ledger of ~60–90 typed claims**, each with a verbatim quote and a precise locator. Generate from it a **static HTML deliverable that opens from `file://`** with no server, account or network. Every page (answers, timeline, decisions, contradictions, actions, sources, limits, versions) is a view over the ledger.

## 3. Why it could score

- The corpus is small (≈700 KB, all text-extractable except 8 screenshots). Reading everything and curating beats any automatic pipeline on precision, and precision is what the rubric rewards.
- "Use & uncertainty" requires the jury to open the deliverable and find a proof themselves. A static folder or single HTML file cannot break at demo time.
- One data source (`facts.yaml`) feeding every page means the post-event update (strategies 5–6) regenerates everything consistently.

## 4. Implementation plan

### 4.1 Setup

```bash
cd loto-quebec-nova-participants
python -m venv ../.venv && ../.venv/Scripts/activate      # Windows; on macOS/Linux: source ../.venv/bin/activate
pip install pyyaml jinja2 openpyxl pymupdf
mkdir -p work/strat1 work/_local
```

Windows note: extract the zip to a **short path** (the repo path is fine; the session scratchpad path is too long for Windows' 260-character limit).

### 4.2 Step A: corpus extraction (shared by every NOVA strategy)

Create `work/strat1/extract.py` that:

1. Unzips `NOVA_ETUDIANTS.zip` into `work/_local/corpus/` (git-ignored; never edit those files).
2. Writes `work/_local/text/<relative_path>.txt` (UTF-8) for every file:
   - `.eml`: parse with `email.message_from_bytes(raw, policy=email.policy.default)`; write `From / To / Date / Subject`, the text body, and a list of attachments. Also save each attachment's bytes to `work/_local/attachments/<eml_stem>__<filename>` (needed by strategy 10 to check duplicates).
   - `.pdf`: PyMuPDF `page.get_text("text")` per page, prefixed with `=== page N ===`. **Warning:** the status report `Rapport_Statut_21sept.pdf` is a table whose text order comes out scrambled (labels shifted against their status and comment). Transcribe it by hand from the rendered page (`page.get_pixmap(dpi=150).save(...)` and look at it).
   - `.xlsx`: `openpyxl.load_workbook(path, data_only=True)`; one line per row with cell coordinates (`A2=R-01 | B2=Retard du connecteur interne | … | H2=Suivi au 9 septembre 2026`). Check `cell.comment` too (none found so far, but check). The workbooks use namespaced inline strings, so do not parse their XML by hand; openpyxl handles them.
   - `.txt`, `.md`, `.csv`: decode UTF-8, falling back to cp1252.
   - `.png`: copy to `work/_local/images/` and create an empty `<name>.transcription.md` to fill by hand (8 files; `OPS-601_runbook.png` holds a graded detail for Q10).
3. Writes `work/_local/locators.jsonl`: one record per addressable unit, with a stable ID:
   - meetings: one per timestamped line → `M04@15:22`;
   - tickets: one per dated comment → `SEC-210#2026-09-19T10:22`, plus `SEC-210#header` for title / status / priority;
   - emails: `E05#headers`, `E05#body`;
   - PDFs: `INV-003.pdf#p1`;
   - xlsx: `Registre_Risques_29sept.xlsx!H2`;
   - images: `OPS-601_runbook.png#step4`;
   - Teams: `Teams_19sept_Securite@10:31`.

```python
# sketch: meeting-line locators
import re
TS = re.compile(r'^(\d{2}:\d{2})\s+(.+?)\s*:\s*(.*)$')
for line in text.splitlines():
    m = TS.match(line)
    if m:
        hhmm, speaker, said = m.groups()
        emit(id=f"{doc_id}@{hhmm}", file=rel_path, speaker=speaker, text=said)
```

Run: `python work/strat1/extract.py` → expect 64 text files, 8 images, ≥ 150 locators.

### 4.3 Step B: the ledger schema

`work/strat1/facts.yaml`, one entry per claim:

```yaml
- id: F-GOLIVE-APPROVED
  subject: go-live                       # go-live | budget | INV-003 | CR-01 | CR-04 | SEC-210 | ACC-301..303 | OPS-601 | INT-101 | DATA-401 | PERF-501 | hosting | PM | scope
  type: decision                         # fact | proposal | decision | delivery | validation | action | risk | contradiction
  statement: "La date cible de mise en production est déplacée du 15 au 22 octobre 2026."
  status: current                        # current | superseded | stale | proposal-only
  date_effective: 2026-09-10
  info_as_of: 2026-09-10
  actor: "Comité de direction (formulée par Élodie Caron)"
  source_file: 02_Reunions/M04_Transcript_Comite_direction_10sept.txt
  locator: "M04@15:22"
  quote: "La date cible de mise en production NOVA est déplacée du 15 octobre au **22 octobre 2026**."
  authority: committee                   # see strategy 3 for the scale
  supersedes: [F-GOLIVE-CHARTER]
  superseded_by: []
  confidence: high
  notes: "Approuvé à 15:25 sans objection ; 15:27 : pas un go automatique."
```

Rules: `quote` is copied verbatim (≤ 25 words); every claim used in an answer must exist in the ledger; our own interpretations go in `notes`, never in `statement`.

### 4.4 Step C: fill the ledger, subject by subject

Order that matches the 10 questions: go-live date (Q01–Q03), PM (Q04), budget and invoices (Q05–Q06), hosting (Q07), security (Q08), accessibility (Q09), go-live conditions and runbook (Q10), then the rest (INT-101, DATA-401, PERF-501, scope / mobile, stale documents, distractors). Use the draft answers in analysis §7.1.4 as a checklist, but verify each locator in the extracted text.

LLM assistance (declared in the user guide): paste one source at a time and ask for candidate claims in the YAML format; a human checks every quote against the source.

### 4.5 Step D: generate the site

`work/strat1/build.py`: load `facts.yaml` (+ `work/strat2/answers_final.yaml` and `work/strat9/actions.yaml` if present), render Jinja2 templates into `work/strat1/export/`:

| Page | Content |
|---|---|
| `index.html` | the 1-page brief (strategy 9) + navigation |
| `questions.html` | Q01–Q10: one-line answer, nuance bullets, sources as links |
| `timeline.html` | all claims sorted by `date_effective`, coloured by type |
| `decisions.html` | proposal → decision → validation per subject (strategy 4) |
| `contradictions.html` | claim A vs claim B → resolution and reason (strategy 3) |
| `actions.html` | action register (strategy 9) |
| `sources.html` | every corpus file with class (strategy 10) and a link to its rendered copy (strategy 7) |
| `limits.html` | user guide: how to open, tools used (incl. AI), manual steps, uncertainties |
| `versions.html` | baseline vs updated state and diff (strategy 5) |

Copy the original corpus into `export/corpus/` so links work offline. Variant to compare: inline everything into **one self-contained `nova_memoire.html`** (JSON data in a `<script type="application/json">` tag, plain JS renders the views). Pick the variant that passes the clean-machine test most reliably.

### 4.6 Step E: integrity script

`work/strat1/check.py` fails (exit code 1) if:
- a `source_file` does not exist in the corpus;
- a `quote` is not found in the extracted text of its source (normalise whitespace and `**` markdown before comparing);
- a `locator` is not in `locators.jsonl`;
- an answer cites a fact ID that does not exist;
- a fact cites a distractor (`INV-778`, newsletter, Excel training, personal notes) as positive evidence.

## 5. How to test it

### 5.1 Test cases

| # | Test | How | Pass if |
|---|---|---|---|
| T1 | Extraction completeness | `extract.py` then count | 64 text files, 8 images, 0 decode errors |
| T2 | Ledger integrity | `python work/strat1/check.py` | exit 0 |
| T3 | Clean-machine open | zip `export/`, unzip on another machine or a fresh browser profile with Wi-Fi off, open `index.html` | every page renders, every source link opens |
| T4 | Jury simulation | someone who has not read the corpus gets 5 min, the questions page, and 3 random questions | they reach a proof for all 3 without help |
| T5 | Answer quality | grade with strategy 2's nuance atoms | all 10 answers at "5" |
| T6 | Stale-source guard | grep answers for citations of Plan v3, status report, register R-01 as **support** of a current fact | 0 hits (they may only appear as contradictions) |

### 5.2 Acceptance and kill criteria

- **Adopt** when T1–T3 pass and T5 shows ≥ 9/10 answers at 5.
- **Fallback at hour 14:** if the site is not ready, ship `facts.yaml` + a Markdown or PDF dossier generated from it (the points are in the content).

## 6. Risks and guardrails

- LLM-drafted claims can flip "proposed" into "approved" or shift a date. The verbatim-quote check (T2) is the guard.
- Do not let derived documents (plans, register, status report) support current facts; they are stale on purpose.
- Keep the original files untouched; the deliverable ships a copy.

## 7. Combines with

Strategy 2 (answer grading), 3 (contradictions), 4 (lifecycle view), 5–6 (live event), 7 (deep links), 9 (brief and actions), 10 (source classes).

## 8. Results log

| Date | Who | What was run (command / commit) | Result | Verdict |
|---|---|---|---|---|
| | | | | |
