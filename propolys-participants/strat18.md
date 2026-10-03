# Propolys · Strategy 18: "PatchPilot": exploit-likelihood forecasting to tell SMEs what to patch first

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | Strategy 5 triages alerts **after** something happens; strategy 10 vets new packages. This **forecasts which known vulnerabilities in the company's own systems are about to be exploited** and turns thousands of findings into a short, ordered patch list |
| **Work folder** | `propolys-participants/work/strat18/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md). Theme: "Anticipating rather than reacting".

## 2. The idea

**Problem.** Vulnerability scanners report hundreds or thousands of CVEs per company; IT teams in SMEs and municipalities patch by severity score (CVSS) or not at all. Only a small fraction of vulnerabilities are ever exploited in the wild, and attackers move fast once an exploit appears.

**Solution.** PatchPilot ingests scanner output and asset inventories, then:
1. Predicts **exploitation likelihood** in the next 30 days per vulnerability (signals: public exploit code, chatter, vendor advisories, similar past vulnerabilities, known-exploited catalogues).
2. Combines it with **asset context** (internet-facing? holds sensitive data? business-critical?) into a business-risk ranking.
3. Produces a **weekly patch plan** sized to the team's capacity ("these 12 patches remove 80% of your expected risk"), with tickets created in their tools.
4. Measures risk reduction over time for management and insurers.

**How AI contributes.** Time-series and classification models on vulnerability lifecycle data; NLP on advisories; optimisation of the patch plan under capacity constraints.

**Buyers.** SMEs' IT teams and their managed service providers, municipalities, school boards.

**Business model.** Per-asset subscription; MSP partner pricing.

## 3. Why it could win

Clear pain, measurable outcome (risk reduced per hour of work), and a modelling core that fits our forecasting skills. Public data sources make a credible demo possible.

## 4. Implementation plan

### 4.1 Research

- Public prioritisation signals: CISA Known Exploited Vulnerabilities catalogue; the Exploit Prediction Scoring System (EPSS, FIRST.org); cite both and explain our added value (asset context + capacity-aware plan, SME UX).
- A statistic on the share of CVEs exploited in the wild or time-to-exploit (cite).
- Competitors: risk-based vulnerability management vendors (enterprise-priced); our angle: SME / MSP price point, French-language, plan sized to capacity.

### 4.2 Optional demo

Take a sample scanner export (synthetic), join public EPSS scores and the KEV catalogue, add asset tags, and produce the "12 patches = 80% of risk" chart.

### 4.3 Slides

1. Problem: "3 000 vulnérabilités, 2 personnes, par où commencer ?" + sourced statistic.
2. Solution: before / after list and the risk-reduction curve.
3. Business: per-asset pricing, MSP channel, pilot, team, ask.

### 4.4 Script skeleton

Hook (Monday morning scanner report) · why CVSS ordering wastes effort · PatchPilot prediction + plan · measurable risk reduction · business · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Originality test: given EPSS is public and free, can we state our value in one sentence? (Asset context + capacity planning + SME workflow.)

**Kill:** if the mock jury sees no value beyond the public EPSS score after one rewrite.

## 6. Risks and ethics

Mis-prioritisation leaving a critical hole; always keep known-exploited vulnerabilities at the top regardless of model output.

## 7. Combines with

Strategy 17 (remediation engine for insured SMEs), 5 (alerts), 10 (supply chain).

## 8. Results log

| Date | Who | Scorecard /30 | Originality | Mock-jury avg | Verdict |
|---|---|---|---|---|---|
| | | | | | |
