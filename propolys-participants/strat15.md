# Propolys · Strategy 15: "RedTeamBox": automated red-teaming and compliance reports for SMEs' chatbots

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h (+ optional 1–2 h demo) |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | Strategy 3 (AgentShield) is a **runtime** gateway for agents. This is **pre-deployment and periodic testing**: an automated attacker that probes a company's customer chatbot for leaks, jailbreaks, harmful or off-brand answers, and produces a remediation and compliance report |
| **Work folder** | `propolys-participants/work/strat15/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md). Theme: "AI needs protection too".

## 2. The idea

**Problem.** Thousands of SMEs deploy customer-service chatbots built on LLMs (on their website, WhatsApp, booking systems). Few test them: the bot may reveal internal documents or other customers' data, promise refunds it should not, be tricked into offensive content, or leak its system prompt. Security testing firms are too expensive for SMEs.

**Solution.** RedTeamBox connects to the chatbot's public interface (or API), then:
1. Runs a **library of attack scenarios** (prompt injection, data extraction, policy bypass, impersonation, harmful content, hallucinated commitments) adapted by an attacker LLM to the bot's domain.
2. Scores outcomes with automated judges + human spot checks.
3. Produces a **report**: findings ranked by severity, reproduction transcripts, fixes (prompt hardening, retrieval filters, guardrails), and a mapping to frameworks (e.g. OWASP Top 10 for LLM applications; Québec Law 25 privacy obligations where personal data is involved).
4. **Continuous mode:** re-tests after every bot update, trend over time.

**How AI contributes.** Attacker LLMs generating adaptive attacks; judge models; clustering of failure modes.

**Buyers.** SMEs and agencies that build chatbots for clients; insurers (as a risk-reduction requirement); chatbot platforms (OEM).

**Business model.** Per-assessment fee + monthly continuous testing subscription; agency partner plan.

## 3. Why it could win

Concrete, demonstrable live (attack a toy bot on stage), addresses a new attack surface, and has a simple SME-friendly offer.

## 4. Implementation plan

### 4.1 Research

- OWASP Top 10 for LLM applications (current edition); one public incident of a company chatbot making a costly or embarrassing statement (reputable source).
- Competitors: AI red-teaming platforms and open-source tools (e.g. LLM vulnerability scanners); our angle: SME price point, French-language attacks and reports, agency channel.

### 4.2 Optional demo

A toy "Boutique" chatbot with a hidden discount code in its system prompt; RedTeamBox runs 20 attacks, extracts the code in some, and generates a 1-page report. Record a backup video.

### 4.3 Slides

1. Problem: screenshot of a chatbot giving away something it shouldn't (our demo) + "les PME déploient sans tester".
2. Solution: attack → judge → report pipeline; sample report page.
3. Business: per-assessment + continuous pricing, agency channel, team, ask.

### 4.4 Script skeleton

Live hook (the bot leaks a secret) · new attack surface · automated red team · report and continuous testing · business · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Ethics / legality: testing only with the bot owner's authorisation (contract); never target third-party bots; responsible disclosure.
- Demo reliability: the demo runs offline or with a recorded fallback.

**Kill:** if we cannot differentiate from free open-source scanners (answer: managed service, reports, French, continuous monitoring for non-technical SMEs).

## 6. Risks and ethics

Dual use (attack libraries): restrict to authorised targets, keep the library private, log usage.

## 7. Combines with

Strategy 3 (runtime protection as the follow-up product).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Demo reliability | Verdict |
|---|---|---|---|---|---|
| | | | | | |
