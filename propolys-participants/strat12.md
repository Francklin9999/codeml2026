# Propolys · Strategy 12: "GridGuard": predicting wildfire ignition risk from power lines

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | Strategy 4 protects water utilities' control systems; strategy 7 supports crisis response after an event. This **anticipates** a physical hazard before it happens: power-line-caused wildfires, combining vegetation imagery, weather and grid telemetry |
| **Work folder** | `propolys-participants/work/strat12/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md). Relevant themes: "Protecting critical infrastructure", "Anticipating rather than reacting", "Building resilience in times of crisis".

## 2. The idea

**Problem.** Power lines can start wildfires (vegetation contact, equipment failure in high wind); wildfire seasons in Canada have become more severe. Utilities manage tens of thousands of kilometres of lines with periodic, calendar-based vegetation trimming and limited visibility into where risk is highest **this week**.

**Solution.** GridGuard produces a **risk map per line segment**, updated daily:
1. Vegetation encroachment from satellite / aerial imagery (canopy height, distance to conductors, growth since last trimming).
2. Fire-weather forecasts (wind, humidity, drought indices).
3. Grid telemetry (faults, reclosers operating, line loading).
4. Asset age and maintenance history.
Output: prioritised trimming and inspection lists, and "high-risk days" alerts for operational decisions (e.g. adjusting protection settings).

**How AI contributes.** Computer vision on imagery; spatio-temporal risk models trained on historical faults and ignitions; explainable risk drivers per segment.

**Buyers.** Electric utilities and distribution co-ops, municipalities with their own grids, forestry / fire-protection agencies as partners.

**Business model.** Annual SaaS per km of line monitored; paid pilots on one region; data partnerships for imagery.

## 3. Why it could win

Vivid stakes, clear "anticipate rather than react" message, strong fit with our time-series and spatial ML skills, and a large, identifiable buyer type.

## 4. Implementation plan

### 4.1 Research

- Canadian wildfire season statistics (Natural Resources Canada / CIFFC) for a recent year; examples of utility-caused wildfires and their consequences (e.g. well-documented cases elsewhere in North America).
- Open data: Canadian Wildland Fire Information System (fire-weather indices), satellite imagery availability (Sentinel-2, open licence), open fault data (probably not public: say pilots need utility data).
- Competitors: vegetation-management analytics vendors and utility risk-modelling consultancies; our angle: daily operational risk + explainability, mid-size utilities.

### 4.2 Slides

1. Problem: a wildfire image + one sourced statistic + "trimming on a calendar, not on risk".
2. Solution: map mock of line segments coloured by risk with "why" tooltips (wind 70 km/h, branch at 1.2 m from conductor, fault yesterday).
3. Business: per-km pricing, pilot with a utility region, team, ask.

### 4.3 Script skeleton

Hook (a spark on a dry day) · why utilities can't see risk today · GridGuard daily map · results a pilot would measure (fewer faults on high-risk days, better trimming ROI) · business · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Data realism: which inputs are open (imagery, weather) and which need the utility (faults, assets)? Be explicit in the pitch.
- Buyer reality: does Québec's grid structure (one dominant utility) make the market too concentrated? Consider other provinces and US co-ops in the pitch.

**Kill:** if the only buyer in our home market is a single utility and no broader market story holds.

## 6. Risks and ethics

Model errors leading to complacency; data sharing with utilities (critical-infrastructure security).

## 7. Combines with

Strategy 7 (crisis response), 4 (infrastructure).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
