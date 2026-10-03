# NOVA · Strategy 18: Financial reconciliation ledger (authorised / invoiced / paid / held) with what-if scenarios

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (protects Q05 and Q06, 10 pts, and the budget theme of the brief) |
| **Effort** | 2 h |
| **Depends on** | strategy 1 step A |
| **Rubric lines** | Q05, Q06, Brief (budget and invoices theme), Update (if the event is financial) |
| **Differs from 1–10** | Strategies 2 and 9 state the money answers in prose. This builds a **line-level reconciliation** with checks that must balance, and pre-computed scenarios for plausible financial events |
| **Work folder** | `loto-quebec-nova-participants/work/strat18/` |

---

## 1. Context you need (verify each figure in the PDFs)

| Document | Line | Amount | Status / note |
|---|---|---|---|
| Contract (`CONTRAT_Boreal_NOVA.pdf`) | initial maximum | 180,000 $ | period 7 Jul – 31 Oct 2026; out-of-scope work requires a written change request **approved before execution and invoicing** |
| CR-01 | advanced reports + summary export | 24,000 $ | APPROUVÉE 14 Aug 2026, project committee |
| CR-04 | advanced mobile optimisation | 18,000 $ (estimate) | BROUILLON, approval required; deferred to phase 2 (24 Sept) |
| INV-001 (31 Jul) | development phase 1, deposit | 60,000 $ | Payée |
| INV-002 (31 Aug) | phase 1 milestone 2 / CR-01 | 48,000 $ + 24,000 $ = 72,000 $ | Payée |
| INV-003 (22 Sept) | phase 1 milestone 3 / mobile optimisation CR-04 | 36,000 $ + 18,000 $ = 54,000 $ | En validation |
| INV-778 (ORION) | other project | 41,000 $ | exclude |

The README: *"Distinguez autorisé, facturé et payé; aucun calcul fiscal n'est demandé."* Amounts are CAD before tax.

## 2. The idea

A small ledger at **line level**, mapping every invoice line to an authorisation (base contract or a CR), with automatic checks:

| View | Value |
|---|---|
| Authorised | 180,000 + 24,000 = **204,000 $** |
| Invoiced (all lines) | 60,000 + 72,000 + 54,000 = **186,000 $** |
| Invoiced and backed by an authorisation | 186,000 − 18,000 = **168,000 $** |
| Paid | 60,000 + 72,000 = **132,000 $** |
| In validation | 54,000 $ (36,000 $ payable after normal validation; 18,000 $ to hold) |
| Remaining authorised, not yet invoiced | **36,000 $** of the base contract (180,000 − 60,000 − 48,000 − 36,000); CR-01 fully invoiced |

## 3. Why it could score

Money questions are where careless answers lose the nuance points (180k vs 204k, counting CR-04, adding ORION). A balanced ledger makes the answers verifiable and the brief's budget line exact.

## 4. Implementation plan

### 4.1 Files

```
work/strat18/
  finance.yaml           # authorisations and invoice lines with sources
  reconcile.py           # computes views + checks + scenarios
  test_reconcile.py
  finance.html (or a sheet in strategy 13)
```

### 4.2 Checks (`reconcile.py`)

1. Every invoice line maps to exactly one authorisation or is flagged `UNAUTHORISED` (expected: the CR-04 line).
2. For each authorisation, invoiced ≤ authorised (base: 144,000 ≤ 180,000; CR-01: 24,000 ≤ 24,000).
3. Invoices from other projects are excluded with a reason.
4. Totals per view as in §2; a check that the views reconcile (paid + in validation = invoiced).

### 4.3 What-if scenarios (pre-computed for the live event)

| Scenario | Effect |
|---|---|
| Committee approves CR-04 on date D | authorised 222,000 $; the CR-04 line becomes payable **only for work executed after D** (contract: approval before execution and invoicing) → ask Finance / legal for treatment of work already started |
| Boréal issues a credit note for 18,000 $ | INV-003 = 36,000 $; invoiced 168,000 $ |
| INV-003 corrected and paid | paid 168,000 $; remaining base 36,000 $ |
| New milestone invoice for the final 36,000 $ | base fully invoiced; check deliverables accepted |

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Source check | every amount in `finance.yaml` matches its PDF (two-person check) |
| T2 | Unit tests | the totals in §2 and each scenario's results |
| T3 | Answer consistency | Q05 / Q06 answers and the brief use exactly these numbers |

## 6. Risks

Mis-reading the INV-002 / INV-003 line order (the PDF text layer puts amounts and descriptions in separate columns; read the rendered page to pair each amount with its description).

## 7. Combines with

Strategy 2 (Q05 / Q06 atoms), 9 (brief), 6 (financial events), 13 (finance sheet).

## 8. Results log

| Date | Who | Checks passed | Notes |
|---|---|---|---|
| | | | |
