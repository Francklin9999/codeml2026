# NOVA · Strategy 8: Offline, citation-locked natural-language Q&A

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (optional; only after strategies 1–6 are done) |
| **Effort** | 4–6 h |
| **Depends on** | strategy 1 (ledger), 7 (anchors) |
| **Rubric lines** | Use & uncertainty (10); the brief's goal 7 "interroger le projet en langage naturel" (not separately scored) |
| **Work folder** | `loto-quebec-nova-participants/work/strat8/` |

---

## 1. Context you need

`consignes.pdf` lists natural-language querying and gives example questions: *"Quelle est la date de livraison actuellement prévue et pourquoi?", "Quelles décisions ont été prises concernant le fournisseur?", "Quels engagements ne sont toujours pas complétés?", "Existe-t-il des informations contradictoires?", "Quels sont les trois principaux risques du projet aujourd'hui?", "Pourquoi cette décision a-t-elle été prise?", "Qu'est-ce qui a changé depuis la semaine dernière?", "Si je devais reprendre le projet demain matin, que devrais-je savoir?"*. But the README rubric says a chatbot is not required and AI earns nothing by itself; the jury must not need a paid subscription.

## 2. The idea

A question box that **only answers from the ledger**, cites fact IDs and source links, and says **"non documenté dans le corpus"** otherwise. Two variants:

- **A. Client-side retrieval, no LLM** (MiniSearch or Lunr in the static site): returns the top facts grouped by subject with badges *valide / historique / proposition*. Zero hallucination by construction; runs for the jury offline.
- **B. LLM with forced citations** (team demo only, declared): the model gets the question + retrieved facts and must cite `[F-xx]` for every sentence; a validator rejects uncited sentences.

## 3. Why it could score (and why P3)

It covers the follow-up questions quickly and shows uncertainty handling (abstention). It does not add rubric points by itself, so build it last.

## 4. Implementation plan

### 4.1 Files

```
work/strat8/
  qbank.yaml          # evaluation questions with expected fact IDs or "abstain"
  build_index.py      # exports facts + passages to search_index.json
  search.js           # variant A (MiniSearch, vendored file for offline use)
  qa_llm.py           # variant B
  eval_qa.py
```

### 4.2 Question bank (~40)

- Q01–Q10 + 2 paraphrases each (30).
- The 8 example questions from `consignes.pdf`.
- 6 unanswerable: "Quel est le budget de la phase 2 ?", "Qui remplace Olivier Côté ?", "Quand aura lieu le prochain comité ?" (check the corpus first), etc.
- 4 traps: "La sécurité est-elle complétée selon le rapport de statut ?", "Le connecteur est-il encore un risque ouvert ?", "Combien a-t-on payé à Boréal pour ORION ?", "La date du 15 octobre est-elle confirmée ?".

### 4.3 Variant A

Index fields: `statement` (boost 3), `subject` (boost 2), `quote`, `notes`, French synonyms (mise en production / go-live / lancement; facture / invoice; sécurité / SEC-210). Normalise accents. Display top-k facts grouped by subject, with status badges and links to strategy 7 anchors. Vendor the MiniSearch JS file into the export (no CDN at runtime).

### 4.4 Variant B

```
SYSTEM: Réponds uniquement à partir des faits fournis. Chaque phrase doit se terminer par
au moins une citation [F-xxx]. Si les faits ne permettent pas de répondre, réponds
exactement « Non documenté dans le corpus ». Distingue proposition, décision, livraison, validation.
USER: <question> + <top 12 facts as YAML>
```

Validator: split sentences; each must contain ≥ 1 citation to a retrieved fact ID; otherwise reject and show variant A's result instead.

## 5. How to test it

| Metric (on `qbank.yaml`) | Target |
|---|---|
| Answerable questions: correct fact in top 3 (A) / correct and cited (B) | ≥ 80% |
| Unanswerable: correct abstention | ≥ 5/6 |
| Trap questions answered with the nuance | 4/4 |
| Hallucinated claims (B) | **0** |
| Offline operation (A) | works from `file://` with network off |

**Decision rule:** if A reaches ≥ 80% on answerable questions, ship A only. Any hallucination in B that the validator misses → drop B.

## 6. Risks

Time sink. Hard stop at the effort estimate.

## 7. Combines with

Strategy 1 (facts), 7 (links), 5 (query `state_t1` after the event).

## 8. Results log

| Date | Variant | Answerable | Abstention | Traps | Hallucinations | Verdict |
|---|---|---|---|---|---|---|
| | | | | | | |
