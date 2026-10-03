# Propolys · Strategy 9: "SnoopWatch": detecting inappropriate access to health records (insider privacy breaches)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (clear compliance-driven buyer; strong Québec privacy angle) |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat9/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format and criteria. One of ten alternative concepts; use the shared validation protocol.

## 2. The idea

**Problem.** Hospital staff legitimately need broad access to electronic health records, which makes **snooping** (looking up a celebrity, an ex-partner, a neighbour or a colleague) easy and hard to detect. Breaches damage patients and expose institutions to sanctions under privacy law. Access logs exist but nobody can review millions of lines.

**Solution.** SnoopWatch analyses EHR access logs and flags accesses that lack a care relationship:
1. Builds the **care context** for each access: is the employee on the patient's care team, unit, schedule, referral, appointment?
2. Detects patterns: same last name / address as the patient, access to VIP or employee records, accesses outside shift, bursts of lookups, accesses to a patient never treated by the employee's unit.
3. Produces a short, explained case file for the privacy officer, with a workflow (investigate, interview, close) and statistics for compliance reporting.

**How AI contributes.** Graph of employees, patients, units and encounters; anomaly detection and learning from privacy-officer decisions; explanation generation; privacy-preserving processing (on-premises, pseudonymised identifiers).

**Buyers.** Health institutions' privacy and compliance offices, CISOs of hospital networks, private clinics groups.

**Business model.** Annual licence by number of beds or users; on-prem deployment; implementation services with the EHR vendor's log format.

## 3. Why it could win

The jury will immediately see the harm and the buyer (privacy officers have a mandate and a budget). Strong link to security (insider threat) and to Québec's privacy framework (Law 25 strengthened obligations and penalties).

## 4. Implementation plan

### 4.1 Research

- Documented cases of snooping in Canadian hospitals (news / privacy commissioner decisions; cite one).
- Québec privacy obligations for health institutions (Law 25 and the 2023 health information act, check the exact name and provisions) and incident-reporting requirements.
- Competitors: patient-privacy monitoring vendors (mostly US); differentiation: Québec health-network integration, French-language, on-prem, explanations.

### 4.2 Slides

1. Problem: "Une infirmière consulte le dossier de son ex-conjoint" story; one sourced case; obligations.
2. Solution: case-file mock with reasons (same address as patient, no care relationship, access at 2 a.m.).
3. Business: licence per institution, on-prem, pilot with one hospital privacy office, team.

### 4.3 Script skeleton

Story (30 s) · scale and obligations · how SnoopWatch decides "no care relationship" · privacy-preserving design · business · close.

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- Data access realism: do EHR systems produce access logs with enough context (user, patient, time, function)? Find a source.
- Employee-relations objection: how do we avoid a surveillance culture? (Transparency, focus on no-care-relationship accesses, human review.)

**Kill:** if we cannot show that access logs with care context are realistically obtainable.

## 6. Risks and ethics

Staff surveillance concerns; false accusations (always human investigation); highly sensitive data (on-prem only).

## 7. Combines with

Strategy 5 (alert ranking engine).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
