# NOVA · Strategy 7: Deep-link evidence viewer (locator-precise)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 4–5 h |
| **Depends on** | strategy 1 (extraction, `locators.jsonl`, site) |
| **Rubric lines** | Evidence & navigation (10), Use & uncertainty (10) |
| **Work folder** | `loto-quebec-nova-participants/work/strat7/` |

---

## 1. Context you need

Deliverable 3 asks for each answer with *"un fichier source et un repère précis (page, cellule, commentaire daté, passage ou capture)"*. Evidence criterion: ≥ 3 answers with a **retrievable** file + locator, ≥ 2 of them crossing distinct sources. Use criterion: the jury opens the deliverable and finds a proof themselves.

## 2. The idea

Render every source as an HTML page with **anchors at the granularity the rubric names**, and make every citation a link that lands on the exact passage, **highlighted**. Two clicks from a question to its proof, offline.

## 3. Why it could score

It makes both 5-point findings of the Evidence criterion and the first finding of the Use criterion visible in seconds, and it handles the follow-up question "montrez-moi où c'est écrit".

## 4. Implementation plan

### 4.1 Files

```
work/strat7/
  render_sources.py
  templates/source.html.j2
  check_links.py
  out/sources/*.html     # copied into strategy 1's export/
```

### 4.2 Anchor scheme by format

| Format | Anchor | Example |
|---|---|---|
| Meeting transcripts / minutes | one per timestamped line; for minutes without timestamps, one per bullet | `M04.html#t-1522`, `M05.html#b-3` |
| Tickets | header block + one per dated comment | `SEC-210.html#c-20260919-1022` |
| Emails | headers, body paragraphs, attachment list (with "copie de … (non indépendante)") | `E05.html#p-3` |
| PDFs | one per page + hand-checked table for the status report (its text layer is scrambled) | `INV-003.html#page-1`, `Rapport_Statut.html#row-securite` |
| xlsx | HTML table, one anchor per cell | `Registre_Risques_29sept.html#H2` |
| Teams | one per message | `Teams_19sept.html#t-1031` |
| PNG screenshots | the image + manual transcription + highlight boxes | `OPS-601_runbook.html#step-4`, `#step-5` |
| md (ADR, scope decision) | one per heading / paragraph | `ADR-007.html#decision` |

### 4.3 Highlighting without JavaScript

```css
:target { background: #fff3a3; outline: 2px solid #e0b000; scroll-margin-top: 4rem; }
```

For images: absolutely positioned `<a id="step-5" class="box" style="left:..%;top:..%;width:..%;height:..%">` over the `<img>`; `.box:target` gets a visible border. Measure box coordinates once by hand (8 images).

### 4.4 Backlinks

Each source page lists "cité par: Q08, Q10, contradiction C3, action A-04" using the ledger. Helps the jury navigate in both directions.

### 4.5 Citation format in answers

`[M04 15:22–15:25](sources/M04.html#t-1522)` plus a hover title with the verbatim quote.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | `check_links.py`: parse every `href` in the export, verify file + anchor `id` exist | 0 broken links |
| T2 | Two-click test: for each Q01–Q10, from the questions page to the highlighted passage | ≤ 2 clicks, 10/10 |
| T3 | Offline / browser matrix: `file://` with network disabled, Chrome + Firefox (+ Edge) | anchors and highlight work |
| T4 | Screenshot evidence: `OPS-601_runbook.html#step-5` highlights the right region | visual check |
| T5 | Duplicate notes: E03, E07, E10, E11 pages show the attachment as a copy | present |

**Kill / simplify:** if the image overlays are fiddly, use a cropped image of the region next to the full image.

## 6. Risks

Anchor IDs drifting from the ledger's locators. Generate both from `locators.jsonl`; never type IDs by hand.

## 7. Combines with

Strategy 1 (site), 10 (duplicate classes shown on pages), 8 (Q&A results link here), 2 (T3 of strategy 2 uses these links).

## 8. Results log

| Date | Who | Broken links | Two-click | Verdict |
|---|---|---|---|---|
| | | | | |
