# Propolys · Strategy 6: "AînéGarde": protecting seniors from phone and text scams (AI voice, grandparent scams)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 (emotionally strong, socially relevant; consumer go-to-market is harder) |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat6/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format and criteria. One of ten alternative concepts; use the shared validation protocol.

## 2. The idea

**Problem.** "Grandparent scams" (a fake grandchild in trouble asking for bail money), fake bank or police calls, and romance scams target seniors; AI voice cloning makes the fake grandchild sound real. Victims often act within an hour, alone, under pressure and secrecy.

**Solution.** AînéGarde is a phone app + family network + bank partnership:
1. **Call and SMS screening** on the senior's phone: flags scam scripts in real time (urgency, secrecy, money request, gift cards, courier pickup) and shows a large, simple warning: "Raccrochez et rappelez votre petit-fils à son numéro habituel."
2. **Family circle:** a trusted relative gets an alert (no call content, just "appel à risque élevé, 4 min") and can call the senior.
3. **Bank signal:** with consent, partner banks / credit unions receive a "heightened scam risk" flag that triggers extra verification on unusual withdrawals in the next hours.

**How AI contributes.** On-device speech-to-text and scam-script classification (privacy-preserving: audio never leaves the phone); synthetic-voice indicators as one signal; risk scoring combining call metadata and content.

**Buyers.** Families (subscription), banks / credit unions (white-label for senior clients), telecoms (add-on), seniors' associations.

**Business model.** B2B2C: white-label licence to financial institutions and telecoms; direct family subscription as a secondary channel.

## 3. Why it could win

A vivid story the jury feels personally, clear social impact, and a privacy-first design (on-device AI) that answers the obvious objection.

## 4. Implementation plan

### 4.1 Research

- Canadian Anti-Fraud Centre figures on frauds targeting seniors / emergency ("grandparent") scams (latest year).
- Feasibility: on-device speech recognition on phones (e.g. small Whisper models); platform limits on call-audio access (iOS restricts third-party call recording: check; design may require speakerphone / companion device or work on SMS + call metadata on iOS).
- Competitors: carrier spam blockers, bank fraud education. Differentiation: content-aware, family loop, bank signal.

### 4.2 Slides

1. Problem: role-play of a fake grandchild call + one sourced statistic.
2. Solution: phone screen mock with the big warning, family alert, bank flag flow.
3. Business: white-label to credit unions (e.g. Québec's large cooperative banking network as a target type), pricing, pilot with a seniors' association, team.

### 4.3 Script skeleton

Role-play (25 s) · scale and why seniors · AînéGarde in action · privacy by design · business · close.

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- **Platform feasibility:** confirm in docs what call-audio access is allowed on Android and iOS; if iOS blocks it, the pitch must say how we handle it (Android-first, SMS + metadata on iOS).
- Consent and privacy: can we explain in one sentence why the bank never hears the call?

**Kill:** if platform restrictions make the core feature impossible on both major OSes and no workaround is credible.

## 6. Risks and ethics

Consent of the senior (autonomy, not surveillance), false alarms, data minimisation (Law 25).

## 7. Combines with

Strategy 2 (same detection core for businesses); choose one of the two for the final pitch.

## 8. Results log

| Date | Who | Scorecard /30 | Feasibility check | Mock-jury avg | Verdict |
|---|---|---|---|---|---|
| | | | | | |
