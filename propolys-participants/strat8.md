# Propolys · Strategy 8: "DocTrust": detecting AI-forged documents in rental and loan applications

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (concrete, original angle; fits our extraction skills and the JADCO rental-market domain) |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat8/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format and criteria. One of ten alternative concepts; use the shared validation protocol.

## 2. The idea

**Problem.** Generative AI makes it trivial to fabricate pay stubs, employment letters, bank statements and IDs. Landlords and property managers, small lenders and car dealers receive these documents as PDFs or photos and verify them by eye. Fraudulent applications lead to unpaid rent, evictions and losses, and push honest applicants into heavier checks.

**Solution.** DocTrust is an API and web portal that checks submitted documents in seconds:
1. **Forensics:** PDF structure and metadata (producer tool, edit history, font inconsistencies, layered text over images), image tampering signals, AI-generation indicators.
2. **Internal consistency:** pay stub arithmetic (gross − deductions = net, year-to-date coherence, tax and contribution rates plausible for the province), dates, employer details.
3. **External consistency (with consent):** employer existence in business registries, address checks, optional bank-data verification through open-banking style consent flows.
4. A **risk report with reasons** for the property manager, and a fair process: the applicant can explain or provide alternatives.

**How AI contributes.** Document extraction (layout models / LLMs), learned forensic classifiers, rule + ML consistency checks, explanation generation.

**Buyers.** Property-management companies (large rental portfolios), tenant-screening services, small lenders, dealerships.

**Business model.** Per-document API pricing; monthly plans for property managers; integration with screening platforms.

## 3. Why it could win

Original, concrete and easy to demo with a fake pay stub where net pay doesn't add up. Clear security link (fraud, identity, trust in documents). Credible team story if we also did the JADCO rental challenge.

## 4. Implementation plan

### 4.1 Research

- Evidence of rental-application fraud / document fraud growth (industry surveys, news; cite).
- Québec / Canada payroll deduction rules (QPP, EI, QPIP, income tax) to explain the arithmetic checks credibly.
- Competitors: document-fraud detection vendors (mostly for banks / fintech in the US); differentiation: Canadian payroll knowledge, French documents, small-landlord price point, fair-process design.
- Legal: tenant-screening rules and privacy (Québec's rental board guidance on what landlords may ask; Law 25).

### 4.2 Optional demo (1 h)

Create two fake pay stubs (one coherent, one with a net-pay inconsistency and a mismatched font), run a small script that extracts numbers and checks the arithmetic; show the report.

### 4.3 Slides

1. Problem: side-by-side real-looking vs forged pay stub; one sourced statistic.
2. Solution: risk report mock with three reasons; flow for property managers and applicants.
3. Business: per-document pricing, screening-platform channel, pilot with a property manager, team.

### 4.4 Script skeleton

"Lequel est faux ?" hook (20 s) · problem size · DocTrust checks · fairness and privacy · business · close.

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- Fairness objection: can we answer "won't this discriminate against applicants with unusual documents?" (human review, applicant can respond, no automatic rejection).
- Legal check: what landlords may legally request in Québec (find the official guidance).

**Kill:** if what landlords may legally collect in Québec makes the core checks unusable, and B2B lenders alone are not convincing.

## 6. Risks and ethics

False positives harming applicants; privacy; arms race with forgers (consistency checks are harder to fool than visual detectors).

## 7. Combines with

Strategy 1 (shared document-extraction layer).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Legal check | Verdict |
|---|---|---|---|---|---|
| | | | | | |
