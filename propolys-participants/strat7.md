# Propolys · Strategy 7: "CrisisLens": verified situational awareness for municipal emergency response

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 ("building resilience in times of crisis"; reuses NOVA-style "operational memory" thinking) |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat7/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format and criteria. One of ten alternative concepts; use the shared validation protocol.

## 2. The idea

**Problem.** During floods, wildfires or major outages, municipal emergency coordinators are flooded with fragmented, duplicated and sometimes false information: citizen calls, social posts, field-team messages, sensor feeds, weather alerts. Decisions (evacuations, road closures, shelter openings) are made on an incomplete, unverified picture.

**Solution.** CrisisLens builds a **live, verified incident map and log**:
1. Ingests reports from many channels (311 / non-emergency lines, field-team messaging, public social posts, sensors, official alerts).
2. Extracts structured events (what, where, when, severity, source), **deduplicates** them and geolocates them.
3. Scores **credibility** (number of independent sources, source authority, consistency with sensors and weather) and separates *claimed* vs *confirmed* facts.
4. Produces a running situation report and a decision log for the after-action review.

**How AI contributes.** LLM / NLP extraction from messy French and English messages; clustering and deduplication; misinformation and rumour flags; credibility scoring; summaries with citations to the underlying reports.

**Buyers.** Municipal emergency management / civil security services, regional coordination bodies, utilities.

**Business model.** Annual licence per municipality (population-tiered), with "activation" support during events; grants for emergency preparedness as a funding path.

## 3. Why it could win

Québec has recurrent spring floods and wildfire seasons, so the jury will relate. The "claimed vs confirmed" view is a crisp, original angle compared with plain dashboards. Clear security link: public safety and resilience, misinformation.

## 4. Implementation plan

### 4.1 Research

- A recent Québec / Canadian flood or wildfire event and its scale (official sources).
- How municipalities coordinate (civil security plans, emergency operations centres).
- Competitors: emergency-management platforms and social-media monitoring tools; differentiate on verification, deduplication and decision log.

### 4.2 Slides

1. Problem: a coordinator's screen with 300 messages; one sourced event.
2. Solution: map mock with clusters, credibility badges (✓ confirmé par 3 sources / ? une seule source), auto-generated situation report.
3. Business: municipal licence, preparedness grants, pilot during the next spring flood season, team.

### 4.3 Script skeleton

Night of the flood (30 s) · the information problem · CrisisLens in 3 steps · why AI is necessary at this volume · business · close.

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- **Credibility of verification:** can we explain how a false rumour would be flagged (single source, contradicts sensor)?
- Data access: are the input channels realistically accessible to a municipality (own call logs, field teams, public posts)?

**Kill:** if the buyer persona (emergency coordinator) says the product duplicates tools they already have, and we cannot name the gap.

## 6. Risks and ethics

Privacy of citizens' messages; never automate evacuation decisions; social-media access terms.

## 7. Combines with

Strategy 4 (infrastructure sensors as a source).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
