# Propolys · Strategy 17: "CyberScore": AI-assisted cyber-risk underwriting for SME insurance

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | Previous strategies sell protection tools to the organisation at risk. This sells **risk measurement to insurers and brokers**, turning security posture into prices and incentives, so SMEs get a financial reason to fix their weaknesses |
| **Work folder** | `propolys-participants/work/strat17/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md). Theme: "Anticipating rather than reacting".

## 2. The idea

**Problem.** Insurers struggle to price cyber insurance for small businesses: long questionnaires that SMEs answer optimistically, little visibility into actual exposure, and correlated losses (one vulnerability hits thousands of clients). SMEs, in turn, don't know what to fix first.

**Solution.** CyberScore gives brokers and insurers an underwriting score in minutes:
1. **Outside-in scan** (with consent): exposed services, outdated software versions, email-security configuration (SPF / DKIM / DMARC), leaked credentials signals, TLS hygiene.
2. **Smart questionnaire:** an LLM-guided interview that asks only what the scan cannot see and checks consistency of answers.
3. **Risk model:** probability and severity estimates per control gap, calibrated on claims data from partner insurers.
4. **Improvement plan for the SME:** "fix these 3 things to lower your premium by X%", with step-by-step guides.

**How AI contributes.** Risk modelling on claims and scan features; LLM questionnaire with consistency checks; prioritisation of remediation by expected-loss reduction.

**Buyers.** Insurers and MGAs writing SME cyber policies, brokers; SMEs indirectly (free improvement plan).

**Business model.** Per-assessment fee paid by insurers / brokers; premium-linked revenue share; SME upsell for remediation help.

## 3. Why it could win

Strong business logic (aligned incentives), clear security outcome (SMEs fix the right things), and it uses our quant / scoring skills directly.

## 4. Implementation plan

### 4.1 Research

- Size / growth of SME cyber insurance in Canada (industry reports; cite) and common claim causes (ransomware, BEC).
- Competitors: cyber-insurance analytics and outside-in rating firms; our angle: SME-focused, French-language questionnaire, remediation linked to premium.
- Regulation: consent for scanning; privacy of results.

### 4.2 Slides

1. Problem: "Questionnaire de 40 questions, réponses optimistes, primes mal calculées" + sourced figure.
2. Solution: scorecard mock for an SME (score, top 3 gaps, premium impact).
3. Business: insurer / broker pricing, pilot with a broker, team, ask.

### 4.3 Script skeleton

Hook (an SME hit by ransomware with the wrong coverage) · the underwriting blind spot · CyberScore scan + interview + model · win-win incentives · business · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Data dependency: claims data is needed to calibrate; pitch must name the partner type and a cold-start approach (expert priors + public incident data).
- Ethics: scanning only with consent; scores explained to the SME.

**Kill:** if the jury persona (investor) sees it as "another security rating company" and we cannot articulate the SME / remediation-premium loop.

## 6. Risks and ethics

Scores used to deny coverage unfairly; transparency and an appeal route for SMEs.

## 7. Combines with

Strategy 18 (patch prioritisation as the remediation engine), 2 (BEC controls).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
