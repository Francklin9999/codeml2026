# NOVA · Strategy 27: Chronology uncertainty and time-zone validation

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (date accuracy) |
| **Effort** | 2–3 h |
| **Depends on** | dated claims and event baseline |
| **Rubric lines** | chronology; live update |
| **Work folder** | work/strat27/ |

## 1. Context and evidence

The reference snapshot is 30 September 2026 at 09:00 Montréal time, and the challenge expects chronology and a live event update. Emails, chat, meeting timestamps, and date-only files may use different precision. No completed timeline has been validated.

## 2. Idea and novelty

Normalize timestamps while retaining original text, precision, timezone confidence, effective time, and record time. For date-only sources, store intervals rather than inventing midnight; flag ordering conflicts that cannot be resolved from source precision. Unlike strategy 5's bitemporal store, this focuses on uncertainty representation and temporal parsing edge cases.

## 3. Rubric

The chronology avoids false precision and clearly explains when the record supports only an ordering, not an exact time.

## 4. Implementation

Create `work/strat27/time_audit.csv` and parser tests for ISO timestamps, Montréal offset, daylight-saving transitions, date-only values, and ambiguous short years. Keep the source string and locator beside normalized values.

## 5. Experiment and decision

Baseline: every dated fact in the draft timeline. Require 100% retain source strings and timezone/precision labels; second reviewer checks all high-impact dates. Adopt if zero unsupported exact-time conversions remain; block timeline publication on unresolved date contradictions affecting current state.

## 6. Risks

The corpus may omit timezone metadata. Normalization cannot resolve conflicts in source authority or determine when a statement became true.

## 7. Combines with

Strategies 3, 5, 23; chronology is an input to, not a replacement for, authority resolution.

## 8. Results log

NOT RUN. No timestamp normalization or temporal review is complete.
