# NOVA · Strategy 11: LLM-automated claim extraction with quote verification (and a measured comparison to manual curation)

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P2 |
| **Effort** | 4–5 h |
| **Depends on** | strategy 1 step A (extracted corpus + locators); strategy 1's curated `facts.yaml` as the reference |
| **Rubric lines** | Update after the event (10: speed and reliability on a new document), Use & uncertainty (10: "outils utilisés, traitements manuels"), challenge goals 1–3 ("comprendre et organiser", "associer", "identifier les décisions") |
| **Differs from 1–10** | Strategy 1 curates the ledger by hand. This one builds an **automatic** extractor and measures its precision and recall against the hand-made ledger, so we know how far we can trust it on the live event and on new projects |
| **Work folder** | `loto-quebec-nova-participants/work/strat11/` |

---

## 1. Context you need

- The corpus is 64 files (emails, meeting notes with timestamps, tickets with dated comments, PDFs, xlsx, Teams logs, screenshots). Strategy 1 extracts them to text with stable locators (`M04@15:22`, `SEC-210#2026-09-19T10:22`, `Registre_Risques_29sept.xlsx!H2`…).
- The README allows AI tools and external services, as long as they are declared and the facts come from the corpus. *"Un chatbot et une ingestion entièrement automatique ne sont pas obligatoires."* So automation is a speed tool, not a scoring criterion.
- The live event arrives during the final presentation; integrating it quickly and correctly is worth 10 points.

## 2. The idea

An extraction pipeline that turns any document (corpus file or live-event text) into **typed claims in the ledger schema**, each with a verbatim quote, then **mechanically verifies** every quote against the source and flags anything unverifiable. Run it on the whole corpus and compare with the hand-curated ledger to measure precision / recall per claim type. Use it in production only where it is measurably reliable.

## 3. Why it could score

- During the live event, a verified automatic first pass saves minutes while the human focuses on authority and impacts.
- Having **measured** our tool's reliability is a strong answer in the "Use & uncertainty" follow-up ("what did the AI do, and how do you know it's right?").

## 4. Implementation plan

### 4.1 Files

```
work/strat11/
  prompt_extract.md      # instructions + ledger schema + few-shot examples (2 from the corpus)
  extract_claims.py      # document text → candidate claims (JSON)
  verify_quotes.py       # quote ⊂ source text? locator valid? date parseable?
  match_to_ledger.py     # candidate ↔ curated fact matching for evaluation
  eval_11.md
```

### 4.2 Extraction prompt (core rules)

- Output only claims that are explicitly stated; never infer approvals.
- Classify each claim's `type` (fact / proposal / decision / delivery / validation / action / risk) with a one-line justification that cites the wording ("« il s'agit d'une proposition » → proposal").
- Copy a verbatim quote ≤ 25 words and the locator (timestamp, comment date, cell, page).
- Mark `actor` and their role if stated; never guess roles.
- If a document only repeats another (attachment copy, archive email), output `duplicate_of`.

Process **one document per call** (the corpus is small); for meetings, chunk by timestamp blocks to keep locators exact.

### 4.3 Verification (`verify_quotes.py`)

1. Normalise whitespace, quotes and markdown (`**`) in both strings; require the quote to be a substring of the source text at the cited locator (or ±1 line).
2. Reject claims whose locator does not exist in `locators.jsonl`.
3. Rule checks on types: a claim typed `decision` or `validation` whose actor is the vendor (Boréal) is flagged; a `decision` without an approving actor is flagged.
4. Output three buckets: `verified`, `flagged` (needs human), `rejected`.

### 4.4 Evaluation against the curated ledger

- Matching: same subject + overlapping locator + statement similarity (embedding cosine or token overlap ≥ 0.6), confirmed by a human for borderline pairs.
- Metrics: precision and recall overall and **per claim type**; type confusion matrix (especially proposal ↔ decision and delivery ↔ validation); hallucinated-quote rate before verification; rate of correct claims rejected by verification (over-strictness).

### 4.5 Live-event mode

`python extract_claims.py --text event.txt --record-time now` → candidate events for strategy 5's store; the human accepts / edits each in under a minute.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Full-corpus run | completes, < 10 min, cost logged |
| T2 | Quote verification | 100% of `verified` quotes found verbatim (re-check with an independent script) |
| T3 | Recall vs curated ledger | ≥ 85% of curated facts found (any bucket) |
| T4 | Precision of `verified` | ≥ 90% of verified claims correct (human-checked sample of 40) |
| T5 | Type confusion | 0 vendor statements typed as `validation` after rule checks |
| T6 | Live-event drill | on 5 drill events (strategy 6), candidate events ready in < 2 min, human edits needed listed |

**Adopt for the live event** if T2, T5 and T6 pass. **Do not use** it to replace the curated answers to Q01–Q10 unless T3 and T4 are both met.

## 6. Risks and guardrails

- LLMs flip "proposé" into "approuvé". The rule checks and the human gate exist for this.
- Screenshots: the model may not see images; their transcriptions (strategy 10) are the input.
- Declare the tool, model and version in the user guide.

## 7. Combines with

Strategy 1 (reference ledger), 5–6 (live event), 15 (multi-project reuse), 19 (presentation of "our search").

## 8. Results log

| Date | Who | Model | Recall | Precision (verified) | Type errors | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |
