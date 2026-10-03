# NOVA · Strategy 32: Evidence quotation fidelity and context windows

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (citation trust) |
| **Effort** | 2–4 h |
| **Depends on** | extracted source text and fact ledger |
| **Rubric lines** | evidence; answer nuance |
| **Work folder** | work/strat32/ |

## 1. Context and evidence

Strategy 11 checks whether extracted quotes appear in source text. A matching substring can still lose negation, speaker attribution, surrounding qualification, or attachment context. The corpus contains sources where proposals and approvals must be distinguished.

## 2. Idea and novelty

For each quoted fragment, capture a short surrounding context window and preserve speaker, document date, and attachment provenance. A human compares the excerpt against the original rendered source, including table/image cases. Unlike strategy 11's quote verification, this detects misleading excerpts that are verbatim but incomplete.

## 3. Rubric

Preserves the meaning of cited evidence and helps the jury verify nuance without searching the entire file.

## 4. Implementation

Create `work/strat32/context_review.csv` with exact quote, preceding/following text, source rendition method, speaker, and reviewer note. For tables and screenshots, retain page/cell/region locators and manually transcribe only relevant text.

## 5. Experiment and decision

Baseline: every quote in critical answers. Two reviewers assess whether context preserves polarity, actor, time, and status. Adopt if all critical excerpts pass all four dimensions; rewrite or expand context on any failure. Keep quoted text short and verbatim.

## 6. Risks

Extracted text order can be wrong in complex PDFs; context windows do not replace checking the rendered original. Overlong excerpts obscure the claim.

## 7. Combines with

Strategies 7, 10, 11, 24; particularly useful for table-based risk or status claims.

## 8. Results log

NOT RUN. No context-window review has been completed.
