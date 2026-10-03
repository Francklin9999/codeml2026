# Propolys · Strategy 1: "ProcureGuard": AI detection of bid-rigging and invoice fraud in municipal procurement

| | |
|---|---|
| **Status** | NOT STARTED *(set to IN PROGRESS / DONE / ABANDONED with your name and the date)* |
| **Priority** | P1 (strong fit with our graph / anomaly skills and a Québec-specific story) |
| **Effort** | 3 h (research 1 h, slides 1 h, rehearsal 1 h) |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat1/` |

---

## 1. Context you need (same for all 10 Propolys strategies)

- **Startup Challenge: Security & AI** (Propolys, Polytechnique Montréal's incubator). Deliverable: **3-minute pitch + up to 3 slides**, by **16:00**. Prize: **$400**. Criteria: *clear and original idea · connection to security · entrepreneurial potential · quality of the pitch*. They want an idea where **AI provides genuine value** to a real security problem; define what, for whom, why, name, how AI contributes, a simple business model (users, value proposition, revenue model).
- Suggested themes include critical infrastructure, anticipating risks, digital–physical systems, "seeing without watching everything" (alert overload), "who is really behind the screen" (deepfakes, impersonation), "AI needs protection too", crisis resilience, dual-use technologies. Own ideas are welcome.
- Strategies 1–10 are **ten alternative startup concepts**. Run the same validation on each (section 5), then pitch the winner.

## 2. The idea

**Problem.** Public procurement is a classic fraud target: bid rotation, cover bids, shell suppliers, split contracts just under tender thresholds, inflated change orders and invoices. Québec lived it publicly (the Charbonneau Commission on the construction industry). Small and mid-size municipalities have no data team to monitor thousands of contracts.

**Solution.** ProcureGuard ingests a municipality's contracts, bids, change orders and invoices (plus public tender data such as Québec's SEAO open data), builds a **supplier–contract–person graph**, and flags risk patterns with explanations: suspicious bid patterns (always the same losers, rotation), contract splitting below thresholds, change-order inflation, invoices that do not match approved amounts (like the NOVA challenge's INV-003!), newly created suppliers sharing addresses / directors / bank accounts.

**How AI contributes.** Graph anomaly detection and community detection on supplier networks; statistical tests on bid distributions (screening methods used by competition authorities); document extraction (LLM) from PDFs of invoices and change orders; ranked, explained alerts instead of raw rules.

**Users / buyers.** Municipal comptrollers and internal auditors, inspector-general offices, procurement directors; later provinces, school service centres, health institutions.

**Business model.** SaaS per municipality, tiered by budget size; onboarding fee for data integration; audit-season reports.

## 3. Why it could win

Clear villain, clear buyer, Québec-relevant story, measurable value (money recovered / prevented), and the team can show a credible technical core (graphs + anomaly detection + extraction). Link to security: fraud and integrity of public funds, insider threats.

## 4. Implementation plan (building the pitch)

### 4.1 Research (1 h, cite every number on the slide footer)

- Size of public procurement in Québec / Canada (provincial and municipal spending on contracts): find an official figure.
- Evidence of procurement fraud cost (e.g. OECD or ACFE estimates of fraud as a share of procurement spending; Charbonneau findings about overbilling).
- SEAO open data: confirm what is published (tenders, bidders, winning bids) and its licence.
- Existing players (search: "procurement fraud analytics", "bid rigging detection software"): list 3 and our difference (municipal focus, French-language documents, explanations, price point).
- Buyer evidence: existence of municipal inspector-general / comptroller roles (e.g. Montréal's Bureau de l'inspecteur général).

### 4.2 Slides (max 3)

1. **Problem + who suffers:** one striking, sourced number; one real-world pattern illustrated (contract split just under threshold).
2. **Solution + how AI works:** a screenshot-style mock of an alert ("Fournisseur X a gagné 9 des 10 appels d'offres où Y et Z ont soumissionné ; écart de prix anormal") with the graph view; three bullets on the AI.
3. **Business + traction plan:** customer, price, go-to-market (pilot with one municipality using SEAO data), team, ask.

Optional quick prototype for credibility (1–2 h, only if time): download a slice of SEAO open data, compute "same bidders, same winner" co-occurrence statistics, and show one real chart (be careful: never accuse a real company on stage; anonymise).

### 4.3 3-minute script skeleton

0:00–0:30 hook (story of a split contract) · 0:30–1:00 problem size and who pays · 1:00–1:50 ProcureGuard demo mock and how AI finds patterns · 1:50–2:30 business model and first customer · 2:30–3:00 why us, why now, ask.

## 5. How to test it (same protocol for all 10 ideas)

### 5.1 Scorecard (fill in after research, before choosing)

| Criterion (jury) | Proxy question | Score 1–5 |
|---|---|---|
| Clear & original | Can a stranger restate problem, customer and solution after hearing a 30-second version? Is there a twist vs existing products? | |
| Link to security | Is security the core of the value, not a side benefit? | |
| Entrepreneurial potential | Named buyer with a budget line? Pricing that adds up? Pilot path? | |
| Pitch quality potential | Is there a vivid story and a visual demo mock? | |
| Team fit | Can we credibly explain the AI with our skills? | |
| Evidence | ≥ 3 sourced facts found in 1 hour? | |

### 5.2 Mock jury

Pitch the 30-second version to 3 people (or 3 LLM personas: incubator manager, security CISO, investor) and ask each to score the four official criteria 1–5 and say the first objection. Record objections; fix the top one.

### 5.3 Timing and clarity

Full rehearsal ≤ 3:00 twice; a listener restates problem / customer / solution correctly.

### 5.4 Kill criteria

No identifiable buyer with a budget; or an existing product already does exactly this for the same customer and we have no differentiation; or we cannot find any sourced number for the problem size.

## 6. Risks and ethics

Defamation: never name real companies as fraudulent. False positives: position alerts as "à vérifier par un auditeur", with explanations.

## 7. Combines with

NOVA challenge experience (invoice vs approved change request) makes a good anecdote; strategy 8 (document forgery) shares the extraction layer.

## 8. Results log

| Date | Who | Scorecard total /30 | Mock-jury avg (4 criteria) | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
