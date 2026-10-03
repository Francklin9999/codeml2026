# Propolys · Strategy 19: "SafeExit": AI-guided evacuation in smart buildings

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | Strategy 7 helps **city-level** coordinators understand a crisis. This acts **inside a building, in real time**: fusing building sensors to guide each occupant along the safest exit route during a fire, gas leak or other emergency |
| **Work folder** | `propolys-participants/work/strat19/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md). Themes: "When the digital world meets the physical world", "Building resilience in times of crisis".

## 2. The idea

**Problem.** Static exit signs point to the nearest exit even when that route is filled with smoke or blocked; large buildings (hospitals, campuses, malls, metro stations) have complex layouts, visitors who don't know them, and people with reduced mobility. Fire wardens have little real-time information about where people are and which corridors are dangerous.

**Solution.** SafeExit connects to existing building systems:
1. **Hazard map:** smoke / heat / gas detectors, door states, sprinkler activations, camera-based smoke detection → which corridors are unsafe now and in the next minutes (spread prediction).
2. **Occupancy estimate:** anonymous counts from Wi-Fi / access control / people counters (no identification).
3. **Dynamic guidance:** computes safest routes and drives dynamic exit signs, public-address messages and notifications (French / English), with special routes for people with reduced mobility (refuge areas, evacuation elevators where allowed).
4. **Responder dashboard:** where hazards and remaining occupants are, for firefighters.

**How AI contributes.** Hazard-spread prediction from sensor time series; crowd-flow simulation to avoid congestion; anomaly detection on sensor data to distinguish real events from faults.

**Buyers.** Owners and operators of large buildings (hospitals, universities, airports, malls, transit), fire-safety integrators.

**Business model.** Per-building licence + integration services through fire-safety integrators; maintenance subscription.

## 3. Why it could win

Life-safety stakes, a clear before / after story (static vs dynamic signs), and a credible integrator channel.

## 4. Implementation plan

### 4.1 Research

- Building and fire codes: are dynamic / adaptive exit signs allowed in Canada? (Verify: codes are strict; the pitch may need to position SafeExit as **supplementary guidance** for responders and occupants' phones, not a replacement for code-mandated signs.)
- Evidence on evacuation problems (studies on wayfinding during fires; cite one).
- Competitors: building-management and fire-alarm vendors' dashboards; our angle: real-time route intelligence and responder view, vendor-agnostic.

### 4.2 Slides

1. Problem: floor plan with a static exit sign pointing into smoke.
2. Solution: same plan with dynamic routes, hazard overlay, refuge areas, responder view.
3. Business: per-building licence, integrator channel, pilot (a university campus building), team, ask.

### 4.3 Script skeleton

Hook (smoke in the corridor the sign points to) · why static guidance fails · SafeExit sense / predict / guide · regulatory path · business · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Regulatory check: what can legally change during an emergency (signs, PA, phone notifications)? Adapt the pitch accordingly.
- Reliability objection: what happens if sensors or network fail? (Fail-safe to standard signage.)

**Kill:** if regulation makes dynamic guidance impossible and the responder-dashboard-only version is not differentiated.

## 6. Risks and ethics

Liability for wrong guidance; certification; privacy of occupancy data (aggregate only).

## 7. Combines with

Strategy 7 (city-level crisis view), 4 (sensor anomaly detection).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Regulatory check | Verdict |
|---|---|---|---|---|---|
| | | | | | |
