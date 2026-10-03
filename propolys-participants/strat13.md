# Propolys · Strategy 13: "MuleNet": graph AI to detect money-mule accounts at credit unions and small banks

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | Strategy 2 stops the victim's payment and strategy 8 detects forged documents. This targets the **infrastructure behind fraud**: the accounts that receive and launder scam proceeds (money mules), detected with graph analytics across transactions |
| **Work folder** | `propolys-participants/work/strat13/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md).

## 2. The idea

**Problem.** Almost every scam (romance, investment, grandparent, business email compromise) needs **mule accounts** to receive and move money: often students or newcomers recruited with "easy job" offers, or accounts opened with stolen identities. Small banks and credit unions see only their own slice and detect mules late, after the money is gone.

**Solution.** MuleNet scores accounts for mule behaviour in near real time:
1. **Transaction graph** per institution: new accounts receiving many incoming e-transfers from unrelated senders, then rapid outgoing transfers / crypto purchases / cash withdrawals ("in-and-out" patterns).
2. **Behavioural signals:** device and login changes, account age, profile mismatches.
3. **Optional consortium layer:** privacy-preserving sharing of risk signals between institutions (hashed identifiers / federated models), so a mule network spanning several banks becomes visible.
4. Case management for investigators with explanations ("12 incoming transfers from 12 new senders in 48 h, 95% moved out within 2 h").

**How AI contributes.** Graph neural networks or graph features + gradient boosting; anomaly detection on flows; explanation generation.

**Buyers.** Credit unions, small and mid-size banks, fintechs, payment processors.

**Business model.** SaaS priced per account monitored; consortium membership fee.

## 3. Why it could win

Clear security value (stopping fraud at its money layer), strong ML / graph story, recognisable buyer, and a social angle (protecting young people recruited as mules through awareness alerts).

## 4. Implementation plan

### 4.1 Research

- Canadian Anti-Fraud Centre / police communications about money-mule recruitment (cite one).
- Regulatory context: FINTRAC obligations (suspicious transaction reporting) as a demand driver.
- Competitors: transaction-monitoring / AML vendors; our angle: mule-specific graph models for smaller institutions, consortium signals, investigator-friendly explanations.

### 4.2 Slides

1. Problem: "Chaque arnaque a besoin d'un compte pour recevoir l'argent" + recruitment ad mock + sourced figure.
2. Solution: graph visual of a mule hub (many senders → one account → crypto exchange), score and explanation.
3. Business: pricing, consortium, pilot with one credit union, team, ask.

### 4.3 Script skeleton

Hook (a student's "job offer") · the mule layer of fraud · MuleNet graph detection · consortium · business · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Privacy and law: can institutions share signals? (Research how consortium fraud sharing works in Canada; mention privacy-preserving techniques.)
- Optional quick demo: a synthetic transaction graph (we generate it) with a planted mule ring and a simple graph-feature model that finds it.

**Kill:** if the regulatory and privacy obstacles to any cross-institution layer are too heavy and the single-institution version is not differentiated from existing AML tools.

## 6. Risks and ethics

False positives freezing legitimate accounts (newcomers, students: fairness concern); human review before action.

## 7. Combines with

Strategy 2 and 6 (victim side), 8 (identity documents at account opening).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
