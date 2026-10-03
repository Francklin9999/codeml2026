# Propolys · Strategy 5: "TriageCopilot": AI alert triage for SMEs and managed security providers

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (directly the "seeing without watching everything" theme; crowded market) |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat5/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format and criteria. One of ten alternative concepts; use the shared validation protocol.

## 2. The idea

**Problem.** Security tools generate thousands of alerts; small teams and managed security service providers (MSSPs) cannot investigate them all, so real incidents hide in the noise. Analysts are scarce and burn out.

**Solution.** TriageCopilot sits on top of existing tools (EDR, firewall, identity provider, email security):
1. **Groups** related alerts into incidents (same host, user, time window, technique).
2. **Enriches** each incident automatically (asset criticality, user role, threat intel, past similar incidents).
3. **Ranks** incidents by likely severity and **writes a one-paragraph explanation** with the evidence and the recommended first steps, in French or English.
4. **Learns from analyst feedback** (true / false positive) to tune ranking per client.

**How AI contributes.** Graph-based correlation of alerts; learning-to-rank on analyst decisions; LLM summaries constrained to cite the underlying events (no invented facts).

**Buyers.** MSSPs serving SMEs (multi-tenant), SMEs with a 1–3 person IT team.

**Business model.** Per-endpoint or per-tenant monthly pricing; MSSP partner programme.

## 3. Why it could win

Universally felt pain; measurable value (minutes saved per alert, incidents caught). The "evidence-cited summaries" angle shows responsible AI.

## 4. Implementation plan

### 4.1 Research

- A sourced statistic on alert volumes / alert fatigue or the cybersecurity workforce gap (e.g. an ISC2 workforce study).
- Competitors: large SIEM / XDR vendors adding AI assistants. Differentiation must be sharp: **SME / MSSP price point, multi-tenant, French-language, evidence-cited summaries, works on top of the tools they already have**.

### 4.2 Slides

1. Problem: "1 analyste, 4 000 alertes par jour" (replace with a sourced number).
2. Solution: before / after screenshot mock (raw alert list → 5 ranked incidents with explanations).
3. Business: MSSP channel, pricing, pilot, team.

### 4.3 Script skeleton

Day in the life of an overwhelmed analyst · what TriageCopilot does · proof of value metric · business · close.

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- **Originality test:** list the three closest products; if the jury persona cannot see the difference in one sentence, score "original" ≤ 2.
- Value metric: can we state a target like "−50% time per alert" and how a pilot would measure it?

**Kill:** if originality scores ≤ 2 after two rewrites.

## 6. Risks and ethics

Incumbents with large budgets; over-trust in AI summaries (always show evidence, analyst decides).

## 7. Combines with

Strategy 3 (agent logs as a new alert source), strategy 9 (same correlation engine applied to health-record access).

## 8. Results log

| Date | Who | Scorecard /30 | Originality score | Mock-jury avg | Verdict |
|---|---|---|---|---|---|
| | | | | | |
