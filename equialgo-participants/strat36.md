# EquiAlgo · Strategy 36: Preregistered limited leaderboard tournament

| | |
|---|---|
| **Status** | NOT STARTED · **Priority** P1 · **Effort** 2 h · **Depends on** organizer upload cap and candidate registry |
| **Rubric** | Actual hidden-reference accuracy; evaluation integrity |
| **Work folder** | work/strat36/ |

## 1. Context and evidence

The user confirms that 94% refers to leaderboard accuracy against the hidden reference and can manually return scores. Upload cap is unknown; V1 baseline CSV is validated at 4,000 rows/1,600 grants, but has no recorded score.

## 2. Idea and novelty

Pre-register a small tournament: baseline V1 plus no more than three one-mechanism candidate families, upload order, stopping rule, and result log. Unlike strategy 3's designed probes of hypotheses, this compares actual candidate prediction files against the explicit >94% benchmark, without treating scalar feedback as row-level labels.

## 3. Rubric

Creates a bounded, auditable route to the only relevant success criterion.

## 4. Implementation

Create `work/strat36/tournament.md`; confirm allowed uploads before starting, hash every candidate, and log returned accuracy verbatim with timestamp. Do not vary candidate IDs to infer individual hidden outcomes.

## 5. Experiment

Upload baseline first. Then candidates in preregistered order only if allowed. Stop when a candidate scores >94% or budget is exhausted. Adoption requires strictly >94% on same official leaderboard metric; a score ≤94% is failure to beat benchmark.

## 6. Risks

Small scalar feedback supports little diagnosis; leader score itself and evaluation conditions must be recorded.

## 7. Combines with

Candidate families 21–35; leaderboard protocol must be authorized by organizers.

## 8. Results log

NOT RUN. No leaderboard upload or score has been recorded.
