# Propolys · Strategy 4: "WaterSentinel": anomaly detection for small water utilities (cyber and physical)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (strong "critical infrastructure" story, uses our time-series skills) |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat4/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format and criteria. One of ten alternative concepts; use the shared validation protocol.

## 2. The idea

**Problem.** Small municipalities run water treatment and distribution with a few operators and old SCADA / PLC systems increasingly connected for remote monitoring. Attacks on water utilities have been reported internationally, and physical faults (pump failures, leaks, sensor drift) cause outages. Small utilities cannot afford an OT security team or 24/7 monitoring.

**Solution.** WaterSentinel is a **passive, read-only edge box + cloud service**:
1. Listens to OT network traffic (port mirroring) and reads process values (flows, pressures, chlorine, pump states).
2. Learns normal behaviour per site (daily and seasonal patterns) and flags anomalies in both **network behaviour** (new device, unusual Modbus write, remote session at night) and **process physics** (chlorine dose inconsistent with flow, pump commanded on with no pressure change).
3. Explains alerts in plain language for operators, with severity and suggested checks; weekly report for the municipal council.

**How AI contributes.** Multivariate time-series forecasting / reconstruction models per site; physics-informed consistency checks; alert clustering to avoid alert fatigue.

**Buyers.** Small and mid-size municipalities, regional water boards, engineering firms that operate plants under contract.

**Business model.** Hardware box at cost + monthly subscription per site; partnership with integrators that already maintain the SCADA.

## 3. Why it could win

Tangible impact (safe drinking water), clear security link (OT cyber + resilience), and an honest technical core (read-only, no risk of disrupting the plant).

## 4. Implementation plan

### 4.1 Research

- Number of drinking-water systems / small municipalities in Québec or Canada (official source).
- Public advisories about cyber threats to water utilities (e.g. CISA or the Canadian Centre for Cyber Security).
- Competitors: industrial OT security vendors (often enterprise-priced); our angle: small-utility price point, process-physics checks, French-language operator UX.

### 4.2 Optional mini-demo

Public SCADA / water datasets exist for research (e.g. testbed datasets with attack labels; check licence before use). Train a simple reconstruction model on normal data and show one detected attack as a chart.

### 4.3 Slides

1. Problem: a small town's plant, two operators, remote access, one sourced advisory.
2. Solution: edge box diagram; example alert ("Écriture Modbus inhabituelle sur la pompe 2 à 3 h 12 : dosage de chlore incohérent avec le débit").
3. Business: per-site subscription, integrator channel, pilot municipality, team.

### 4.4 Script skeleton

Hook (water you drink tonight) · problem and gap · how it works · business · close.

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- Is "read-only, cannot break the plant" convincing to an operator persona?
- Can we name the buyer's budget line (operations budget, infrastructure grants)?

**Kill:** if the sales cycle to municipalities looks too long to be credible without a channel partner, and we cannot name one type of partner.

## 6. Risks and ethics

Long public-sector sales cycles; liability if an alert is missed (position as decision support, not a safety system).

## 7. Combines with

Strategy 7 (crisis response) for the resilience narrative.

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
