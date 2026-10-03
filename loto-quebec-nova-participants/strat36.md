# NOVA · Strategy 36: Chronology-aware source search filters

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (stale-evidence prevention) |
| **Effort** | 3 h |
| **Depends on** | source metadata and searchable viewer |
| **Rubric lines** | chronology; contradiction explanation |
| **Work folder** | work/strat36/ |

## 1. Context and evidence

The corpus contains stale derived project records and primary records with later status. A text search can surface an obsolete date before the current decision. Strategy 3 resolves truth; this proposal changes how search results communicate temporal context.

## 2. Idea and novelty

Display search results grouped as current-at-cutoff, superseded, stale/derived, or unresolved, with source date and information-as-of date. Preserve all results and their evidence rather than hiding losing claims. Unlike strategy 3's resolver, this is a safety-oriented search presentation that helps a user see conflicting records before reading a conclusion.

## 3. Rubric

Makes chronology visible at the point of source discovery and helps explain contradictions by date.

## 4. Implementation

Create `work/strat36/search_labels.yaml`; require human-verified status metadata and link each result to source context. Unknown status defaults to “unclassified,” never “current.”

## 5. Experiment and decision

Baseline: ordinary ranked search. Prepare 12 queries where old and current records mention the same term. Adopt if all known stale records display their label and source date in the first five results; no current record is incorrectly marked stale. Otherwise retain plain search and show an explicit date sort.

## 6. Risks

Labels can encode a mistaken resolution or make old evidence seem irrelevant when it remains useful history. Avoid removing access to any source.

## 7. Combines with

Strategies 3, 7, 10 and 34; label provenance must be independently reviewable.

## 8. Results log

NOT RUN. No temporal search filter or stale-source query set is implemented.
