# Propolys · Strategy 11: "SkyWatch": low-cost drone detection for critical sites (dual-use theme)

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | Strategies 1–10 cover fraud, cyber, OT, crisis information and privacy. This one is **physical airspace security** and squarely addresses the brief's dual-use theme ("drones, autonomous systems, computer vision, detection technologies") |
| **Work folder** | `propolys-participants/work/strat11/` |

---

## 1. Context you need

Format and criteria: see [strat1.md §1](strat1.md) (3-min pitch, ≤ 3 slides, by 16:00, criteria: clear and original idea, link to security, entrepreneurial potential, pitch quality). Validation protocol (scorecard, mock jury, timing, kill criteria): [strat1.md §5](strat1.md).

## 2. The idea

**Problem.** Cheap consumer drones fly over prisons (contraband drops), airports, stadiums, power stations and dams, and industrial sites. Professional counter-drone systems are expensive and built for defence budgets; most civilian sites have nothing but guards looking up.

**Solution.** SkyWatch is a **detection-only** kit (no jamming, which is regulated): a few low-cost sensor nodes combining a microphone array (rotor acoustic signature), an RF receiver (drone control / video links) and a camera with an AI classifier (drone vs bird vs plane), fused into one alert with direction, track and confidence, plus incident logging for police.

**How AI contributes.** Acoustic and RF signal classification; vision detection and tracking; sensor fusion to suppress false alarms (birds, distant aircraft); learning per site.

**Buyers.** Correctional services, airport operators, utilities (hydro dams, substations), event venues, industrial parks.

**Business model.** Hardware nodes + monthly detection-and-logging subscription per site; installation through security integrators.

**Dual-use angle.** Same sensors serve civil security and could serve defence; the pitch explains the deliberate choice of **detection only**, civilian buyers, and export / misuse safeguards.

## 3. Why it could win

Concrete, visual, very current; strong "security" link; addresses the dual-use theme head-on with a responsible stance.

## 4. Implementation plan (building the pitch)

### 4.1 Research (cite on slides)

- Public reports of drone incursions at Canadian prisons or airports (news, government statements).
- Canadian rules: drone regulations (Transport Canada) and the legal status of jamming / counter-drone measures for civilians (verify; detection is generally allowed, mitigation is restricted).
- Competitors: defence-grade counter-UAS vendors and RF-only detectors; our angle: low cost, multi-sensor fusion, civilian buyers.

### 4.2 Slides

1. Problem: a photo / news headline of a prison contraband drop + one sourced number.
2. Solution: map mock with a detected track, confidence and sensor icons; "détection seulement".
3. Business: per-site pricing, integrator channel, first pilot (a correctional facility or a private industrial site), team, ask.

### 4.3 Script skeleton

Hook (a drone over a prison yard at night) · why current answers fail (cost, false alarms) · SkyWatch fusion · responsible dual-use · business · close.

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- Legal check: confirm that civilian **detection** is lawful in Canada and that we never claim mitigation.
- False-alarm objection: can we explain in one sentence how fusion avoids bird alerts?

**Kill:** if legal research suggests even passive RF detection is problematic for private buyers, and we cannot reframe around acoustic / vision only.

## 6. Risks and ethics

Privacy (cameras pointing at the sky near homes: masking, retention limits); misuse; hardware cost and certification.

## 7. Combines with

Strategy 4 (critical infrastructure buyers), 20 (GNSS / RF sensing).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Legal check | Verdict |
|---|---|---|---|---|---|
| | | | | | |
