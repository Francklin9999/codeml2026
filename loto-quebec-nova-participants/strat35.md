# NOVA · Strategy 35: Controlled vocabulary for project entities and aliases

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (cross-source matching) |
| **Effort** | 2–3 h |
| **Depends on** | corpus extraction; entity mentions |
| **Rubric lines** | evidence navigation; chronology |
| **Work folder** | work/strat35/ |

## 1. Context and evidence

Project entities recur across email, tickets, plans, chats, and attachments. Acronyms and name variants can fragment timeline or evidence search. Strategy 10 detects duplicate files and strategy 14 maps stakeholders; this proposal standardizes entity references without making claims about responsibility.

## 2. Idea and novelty

Create a controlled entity register for people, ticket IDs, project components, contract records, and aliases, with each alias linked to a source occurrence. Do not merge ambiguous names automatically. Unlike RACI mapping, the register is an evidence-navigation aid and does not infer roles or authority.

## 3. Rubric

Users can follow the same entity across documents without conflating similar names or ticket references.

## 4. Implementation

Create `work/strat35/entities.yaml`; record preferred label, exact alias, occurrence locator, confidence, and reviewer. Add a disambiguation page for collisions, including similar project names or distractor documents.

## 5. Experiment and decision

Baseline: extracted corpus mentions for Q01–Q10 topics. Two reviewers independently resolve 30 sampled mentions. Adopt if ≥95% entity matches agree and every ambiguous occurrence is explicitly unresolved; otherwise restrict aliases to exact identifiers and verified names.

## 6. Risks

Alias resolution can leak across people or projects; a matching string does not prove identity. Keep source-level evidence and confidence.

## 7. Combines with

Strategies 7, 10, 14, 34; entity links should navigate to the original occurrence.

## 8. Results log

NOT RUN. No entity register or alias audit exists.
