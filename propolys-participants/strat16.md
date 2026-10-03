# Propolys · Strategy 16: "CargoSentinel": predicting and preventing cargo theft for trucking fleets

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | No previous strategy addresses **physical supply-chain crime**. This combines telematics, location patterns and theft history to anticipate where and when loads are at risk, and to detect theft in progress (where digital and physical worlds meet) |
| **Work folder** | `propolys-participants/work/strat16/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md). Themes: "When the digital world meets the physical world", "Anticipating rather than reacting".

## 2. The idea

**Problem.** Cargo theft (stolen trailers, fictitious pickups by fraudulent carriers, thefts at unsecured stops) costs carriers, shippers and insurers heavily, and organised groups target specific corridors and parking areas. Small and mid-size fleets have GPS trackers but no analytics; alerts come too late.

**Solution.** CargoSentinel:
1. **Route risk planning:** risk score for planned stops and parking areas from historical theft data, time of day, load type and value; suggests safer stops and timing.
2. **Live anomaly detection:** telematics streams (GPS, door sensors, engine status, trailer disconnect): unexpected stops, route deviations, trailer decoupling, GPS signal loss or jamming patterns → graded alerts to dispatch.
3. **Fraudulent pickup checks:** verification of carrier identity and booking anomalies (fictitious pickups, double brokering), a fast-growing fraud type.
4. Reports for insurers to support premium discounts.

**How AI contributes.** Spatio-temporal risk models; anomaly detection on telematics; NLP / graph checks on carrier and booking data.

**Buyers.** Trucking fleets (20–500 trucks), freight brokers, shippers of high-value goods, cargo insurers.

**Business model.** Per-truck monthly subscription integrating with existing telematics providers; insurer partnerships.

## 3. Why it could win

Tangible losses, clear buyer, strong ML fit (time series + geospatial), and an insurer channel that makes the business model credible.

## 4. Implementation plan

### 4.1 Research

- Canadian cargo-theft statistics or industry reports (insurance bureaus, trucking associations; cite one).
- Fraud trends: fictitious pickups / double brokering (industry sources).
- Competitors: telematics providers' security add-ons, high-value-cargo monitoring services; our angle: predictive route risk + fraud checks for SME fleets via integrations.

### 4.2 Slides

1. Problem: "Une remorque volée pendant la pause du chauffeur" + sourced statistic.
2. Solution: route map with risky stops highlighted, live alert mock ("arrêt imprévu + perte GPS 12 min, remorque détachée").
3. Business: per-truck pricing, telematics integrations, insurer partnership, pilot fleet, team, ask.

### 4.3 Script skeleton

Hook (a theft story) · why trackers aren't enough · CargoSentinel predict + detect + verify · insurer value · business · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Data access: can we get historical theft data (insurers, police open data)? Name the source type.
- Integration realism: do telematics platforms offer APIs? Find one public example.

**Kill:** if no credible source of theft history exists to train risk models and the pitch would rely only on generic anomaly detection.

## 6. Risks and ethics

Driver privacy (location tracking limited to work hours and purpose); false alerts; data-sharing agreements.

## 7. Combines with

Strategy 20 (GNSS jamming detection), 13 (fraud graph techniques).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
