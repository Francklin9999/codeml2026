# Propolys · Strategy 2: "CallBack": deepfake-voice and impersonation fraud guard for SMB finance teams

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (very timely "who is really behind the screen" theme, easy to make vivid) |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat2/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format (3-min pitch, ≤ 3 slides, by 16:00, four criteria). This is one of ten alternative concepts; validate with the shared protocol in §5 and pitch the best one.

## 2. The idea

**Problem.** "Fraude du président" / business email compromise: someone impersonating the CEO, a supplier or a bank asks an accountant to change bank details or make an urgent transfer. Synthetic voices and video now make the call itself convincing. SMEs have no security team, and their controls are informal ("I recognised her voice").

**Solution.** CallBack is a payment-request risk layer for small finance teams:
1. Every payment or bank-detail change request (email, call, Teams/Zoom, SMS) is logged in one place (email plug-in + simple mobile app).
2. An AI risk score combines **content signals** (urgency, secrecy, new beneficiary, changed IBAN, unusual amount or time), **channel signals** (lookalike domains, first-time sender, voice-clone / liveness indicators on recorded calls), and **context** (vendor history, approval chain).
3. For risky requests, CallBack **forces an out-of-band verification**: it calls back the known number from the vendor master file (never the number in the request), or pushes a confirmation to the real executive's phone with a shared challenge.

**How AI contributes.** NLP classification of social-engineering patterns; anomaly detection on payment behaviour; synthetic-voice detection models as one signal (not the only one, since detectors can be fooled); LLM summaries for the approver.

**Buyers.** SMEs (20–500 employees) via their accountants, banks and credit unions (as a value-added service), cyber-insurers (premium discounts).

**Business model.** Per-seat SaaS for finance staff; channel deals with banks / insurers; insurer-subsidised pricing.

## 3. Why it could win

Everyone understands the scenario; a 20-second role-play ("Allô, c'est Marie, la PDG…") makes a great hook. The design is honest about AI limits (detection + **process** verification), which judges appreciate.

## 4. Implementation plan

### 4.1 Research (cite on slides)

- Latest Canadian Anti-Fraud Centre statistics on reported fraud losses and on business email compromise / spear-phishing.
- One or two well-documented deepfake-voice or video-call fraud cases reported in reputable media (verify details).
- Competitors: payment-fraud / BEC protection vendors and voice-deepfake detection vendors; position CallBack as **SMB-first, process-centric, bank / insurer channel**.
- Insurer angle: does cyber insurance in Canada exclude or limit social-engineering fraud cover? (Look up a source.)

### 4.2 Slides

1. Problem: the role-play quote + one sourced number + "detection alone loses the arms race".
2. Solution: flow diagram request → risk score → mandatory call-back → approve/deny; screenshot mock of the alert ("Changement de coordonnées bancaires du fournisseur X demandé par un nouvel interlocuteur, urgence élevée : rappel obligatoire au 514-…").
3. Business: SMB pricing, bank / insurer channels, pilot plan, team, ask.

### 4.3 Script skeleton

Role-play hook (20 s) · cost of the problem (30 s) · how CallBack works, with the AI signals and the call-back (60 s) · business model and channels (40 s) · close (30 s).

## 5. How to test it

Apply the shared scorecard, mock-jury and timing protocol from [strat1.md §5](strat1.md). Specific checks for this idea:
- Can we explain in one sentence why our score is hard to fool even with a perfect voice clone? (Answer: the process verification does not depend on the voice.)
- Does a bank or insurer channel exist in Canada for similar SME security products? (Find one example.)

**Kill:** if we cannot articulate differentiation from existing BEC / payment-fraud tools beyond "we also do voice".

## 6. Risks and ethics

Privacy of recorded calls (consent, Law 25 in Québec); false alarms slowing payments (score thresholds, fast path for known vendors).

## 7. Combines with

Strategy 6 (consumer version for seniors) shares the core; pick one of the two.

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
