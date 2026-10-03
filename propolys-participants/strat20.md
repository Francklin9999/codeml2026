# Propolys · Strategy 20: "SpoofRadar": crowd-sourced GNSS jamming and spoofing detection

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | No previous strategy addresses **navigation and timing signals**. This detects interference with satellite positioning (GPS / GNSS) that threatens aviation, shipping, drones, logistics, and the timing of telecom and power networks |
| **Work folder** | `propolys-participants/work/strat20/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md). Themes: "Protecting critical infrastructure", "One technology, multiple uses".

## 2. The idea

**Problem.** GNSS jamming (blocking signals) and spoofing (faking positions) have become common in some regions, affecting aircraft and ships; cheap jammers are also used by thieves (to hide stolen vehicles or cargo) and by drivers evading tracking. Many critical systems rely on GNSS for **timing** too (telecom networks, power-grid synchronisation, financial timestamps). Interference is often detected late and locally.

**Solution.** SpoofRadar builds a **live interference map** from data that already exists:
1. **Signal-quality data** from partner devices: fleet telematics units, smartphones in an opt-in app, drones, timing receivers at telecom sites (carrier-to-noise ratios, satellite counts, position jumps, clock anomalies).
2. **AI detection** of jamming (simultaneous signal-quality drops in an area) and spoofing (inconsistent positions / velocities across devices, impossible jumps).
3. **Localisation** of the interference source by combining many devices' observations.
4. **Alerts** to subscribers (fleet operators, airports / ports, telecom NOCs) and evidence reports for regulators.

**How AI contributes.** Anomaly detection on multi-device time series; spatial inference of source location; classification of interference types.

**Buyers.** Telecom and power operators (timing), airports and ports, logistics fleets, drone operators; regulators as partners.

**Business model.** Subscription per monitored site / fleet; data partnerships (devices contribute data, receive alerts).

## 3. Why it could win

Novel to most audiences, clearly security-critical (critical infrastructure + crime), and a clever "use data that already exists" angle. Strong dual-use discussion (civil and defence relevance) handled responsibly.

## 4. Implementation plan

### 4.1 Research

- Public reports on rising GNSS interference affecting aviation (aviation-safety agencies' bulletins; cite one).
- Canadian regulation: jammers are illegal to use / sell in Canada (verify with Innovation, Science and Economic Development Canada) → enforcement interest.
- Feasibility: Android exposes raw GNSS measurements (GnssMeasurement API) on many phones; telematics units log signal quality. Cite the API documentation.
- Competitors: specialised interference-monitoring vendors and research networks; our angle: crowd-sourced from existing fleets and phones, low-cost coverage.

### 4.2 Slides

1. Problem: map of a jamming incident (illustrative) + sourced bulletin + "your network's clock depends on it".
2. Solution: live map mock with an interference zone, affected devices, estimated source, alert.
3. Business: subscription + data partnership, pilot with a fleet operator or port, team, ask.

### 4.3 Script skeleton

Hook (a truck's GPS goes blank on the highway; a cell tower's clock drifts) · why it's invisible today · SpoofRadar crowd sensing + AI · who pays · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Data-access realism: will fleets share signal-quality data? Offer: free alerts in exchange for data.
- Clarity test: can a non-technical juror understand jamming vs spoofing in one sentence each?

**Kill:** if the clarity test fails twice and the concept cannot be simplified to one vivid story.

## 6. Risks and ethics

Location privacy of contributing devices (aggregate and anonymise); dual-use sensitivity of interference maps (access control for detailed data).

## 7. Combines with

Strategy 16 (cargo theft with jammers), 11 (drone operations), 4 / 12 (critical infrastructure).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Clarity test | Verdict |
|---|---|---|---|---|---|
| | | | | | |
