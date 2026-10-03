# NOVA · Strategy 13: The operational memory as a navigable Excel / LibreOffice workbook

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (alternative or complementary deliverable format) |
| **Effort** | 4 h |
| **Depends on** | strategy 1's `facts.yaml` (or any structured ledger) |
| **Rubric lines** | Use & uncertainty (10: "le jury peut ouvrir le rendu"), Evidence (10), Brief & actions (10), Update (10: baseline and updated sheets side by side) |
| **Differs from 1–10** | Strategies 1 and 7 deliver a static website. This delivers the same memory as a **spreadsheet**, the tool project managers and the jury already use daily, with hyperlinks to the source files and one sheet per view |
| **Work folder** | `loto-quebec-nova-participants/work/strat13/` |

---

## 1. Context you need

- Deliverables: brief, searchable memory (timeline, decisions, contradictions, sources, actions), 10 answers with locators, post-event state with diff while keeping the baseline, short user guide.
- *"Aucun abonnement payant ne doit être nécessaire au jury pour consulter le rendu; fournissez un export autonome si nécessaire."* An `.xlsx` opens in Excel, LibreOffice Calc (free) and Google Sheets (free).
- The corpus itself contains xlsx plans and a risk register; the audience is a PMO. A workbook "speaks their language".

## 2. The idea

Generate `NOVA_memoire.xlsx` from the ledger with `openpyxl`:

| Sheet | Content |
|---|---|
| `0_Mode_emploi` | how to navigate, tools used, manual steps, limits |
| `1_Brief` | the one-page brief, print area set to 1 page |
| `2_Questions` | Q01–Q10: short answer, nuance, sources as clickable hyperlinks |
| `3_Chronologie` | one row per claim, sorted by date, filterable by subject / type |
| `4_Décisions` | proposal → decision → validation per subject |
| `5_Contradictions` | claim A, claim B, resolution, reason (authority / date) |
| `6_Actions` | owner, status (confirmed / proposed), due (known / à confirmer), origin (commitment / recommendation), evidence |
| `7_Sources` | 64 files, class, info date, hyperlink to the file in `corpus/` |
| `8_Baseline` | frozen copy of the state at 30 Sept 09:00 (sheet protected) |
| `9_État_actualisé` + `10_Diff` | filled after the live event |

## 3. Why it could score

Zero risk at opening time, familiar navigation (filters, freeze panes, hyperlinks), and "keep the baseline" is literally a protected sheet. It can be produced in addition to the HTML site (same source data).

## 4. Implementation plan

### 4.1 Files

```
work/strat13/
  build_xlsx.py
  export/NOVA_memoire.xlsx
  export/corpus/...            # original files, so relative hyperlinks work after unzipping
```

### 4.2 Build details (`openpyxl`)

- Tables as real Excel tables (`ws.add_table`) with filters; freeze the header row; column widths set; wrap text.
- Hyperlinks: `cell.hyperlink = "corpus/02_Reunions/M04_Transcript_Comite_direction_10sept.txt"`, displayed text `M04 15:22–15:25`. Relative links work when the workbook and `corpus/` are unzipped together; test in Excel and LibreOffice (path separators).
- Locator precision inside files: for xlsx sources the hyperlink can target a cell (`file.xlsx#Sheet1!H2`); for text files show the timestamp / line in the display text.
- Conditional formatting: status colours (open / delivered / validated / closed), "à confirmer" in orange.
- Protect `8_Baseline` (`ws.protection.sheet = True`, no password needed or a documented one) and stamp the build date and SHA-256 of the ledger in a cell.
- Print setup for `1_Brief`: `ws.page_setup.fitToPage = True`, `fitToHeight = 1`, `fitToWidth = 1`, A4 portrait.
- Optional: a "Recherche" sheet with a formula-based search box (`FILTER(…, ISNUMBER(SEARCH(B1, …)))`), noting that `FILTER` needs Excel 365 / recent LibreOffice; fall back to AutoFilter instructions.

### 4.3 After the live event

Regenerate `9_État_actualisé` from `state_t1` and `10_Diff` from strategy 5's diff; leave `8_Baseline` untouched (verify the stamped hash).

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Open in Excel (Windows), LibreOffice Calc, Google Sheets (uploaded) | all sheets readable; no repair prompt |
| T2 | Hyperlinks | 100% of source links open the right file after unzipping on another machine (script: list links, check paths exist) |
| T3 | Brief printing | `1_Brief` prints on exactly one page |
| T4 | Baseline protection | `8_Baseline` unchanged after regeneration with an event (hash cell matches) |
| T5 | Stranger test | someone finds the proof for 3 random questions in < 3 min using filters and links |

## 6. Risks

Google Sheets cannot follow relative links to local files; say so in the user guide (jury should unzip and open locally).

## 7. Combines with

Strategy 1 (same ledger, second output format), 5 (baseline / state / diff), 9 (brief and actions), 17–18 (risk and finance sheets).

## 8. Results log

| Date | Who | T1 | T2 broken links | T3 pages | T5 time | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
