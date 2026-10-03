# NOVA · Strategy 34: Search-query coverage set for the operational memory

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (findability) |
| **Effort** | 2–3 h |
| **Depends on** | searchable export and verified corpus |
| **Rubric lines** | use & uncertainty; evidence navigation |
| **Work folder** | work/strat34/ |

## 1. Context and evidence

Strategy 8 proposes offline natural-language Q&A; the deliverable itself must help users find facts, including when an exact answer is not documented. Search relevance is not yet measured because extraction and ledger work remain incomplete.

## 2. Idea and novelty

Build a fixed query set using actual corpus vocabulary, synonyms, ticket IDs, and ambiguous asks; grade whether results expose the right evidence and whether “not found” is safe. Unlike strategy 8's answer generation, this measures retrieval quality only and permits a direct source link without composing an answer.

## 3. Rubric

Reliable search helps the evaluator verify evidence and reduces confident unsupported responses.

## 4. Implementation

Create `work/strat34/query_benchmark.csv` with query, expected fact/source, acceptable alternative results, and ambiguity label. Include 10 answer-seeking, 5 entity, and 5 deliberately unsupported queries. Human-curate expected sources from the corpus.

## 5. Experiment and decision

Baseline: proposed search index. Measure recall@5 for supported queries and false-answer rate for unsupported prompts. Proposed adoption: recall@5 ≥.90 and zero fabricated-answer results on the unsupported set; otherwise simplify to ranked source search with explicit no-answer message.

## 6. Risks

Small benchmark can be overfit; language variants and OCR/transcription gaps may affect retrieval. Results do not establish factual answer quality.

## 7. Combines with

Strategies 7, 8, 21; keep retrieval benchmark separate from answer-generation evaluation.

## 8. Results log

NOT RUN. No query benchmark or retrieval score is available.
