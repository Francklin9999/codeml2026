# DayOne · Strategy 25: Document-set completeness manifest

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2–3 h |
| **Depends on** | strategy 1 page types; strategy 17 assembler optional |
| **Work folder** | `dayone-participants/work/strat25/` |

## 1. Context and evidence

The continuation notes record an 80-page, eight-page-type fictional specimen set and 44 duplicate PNGs, while five real phone photos lack labels. Existing strategy 17 detects duplicates, ordering, and page type. This idea adds a user-visible completeness manifest: which expected documents are present, missing, repeated, or unclassified, without attempting patient matching or page classification itself.

Evidence: [DayOne evaluation audit](work/shared/report.md); strategy 17 is still a proposal in this repository.

## 2. Idea and distinction

Define an expected packet profile per workflow, with required, optional, and repeatable page types. As pages are assembled, maintain a manifest with confidence and evidence for each slot; surface unresolved slots and distinguish “not supplied” from “not yet captured.” Do not infer that a missing page means a clinical fact is absent. Unlike strategy 17's ingestion checks, it helps a reviewer understand packet completeness before accepting a record.

## 3. Rubric relevance

Supports multi-page reliability, understandable review, and explicit missingness; prevents silent partial packets from looking complete.

## 4. Implementation steps

Add `work/strat25/manifest.py`, YAML packet profiles, and a review-panel mockup. Keep manifest entries keyed to random session IDs; no direct identifiers. Add transitions for received, duplicate, uncertain type, expected, waived by user, and missing-at-close. Export a machine-readable audit summary.

## 5. Proposed experiment

Construct 30 packet scenarios from the 80-page specimen ordering: complete, one omitted page, one duplicate, one uncertain type, and shuffled order. Baseline: list of uploaded filenames. Adopt if the manifest catches all deliberately omitted required page types and produces zero false “complete” states; kill if optional pages are misreported as required in more than one scenario. Proposed values, not measured.

## 6. Risks

The challenge's actual workflow may not require all page types on every visit. Packet profiles must be configurable and must not assert medical completeness.

## 7. Combinations

Pairs with strategies 9, 10, 13, and 17; reuse the schema from strategy 1.

## 8. Results log

NOT RUN. Packet rules and scenarios are proposals only.
