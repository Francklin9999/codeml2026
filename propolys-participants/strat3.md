# Propolys · Strategy 3: "AgentShield": security gateway for enterprise AI agents (prompt injection, tool abuse, data leaks)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (matches the "AI needs protection too" theme and our LLM / agent skills) |
| **Effort** | 3 h (+ 1–2 h optional live demo) |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat3/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format and criteria. One of ten alternative concepts; use the shared validation protocol.

## 2. The idea

**Problem.** Companies are connecting LLM agents to email, files, CRMs and payment tools. An agent that reads a malicious web page or email can be **prompt-injected** into exfiltrating data or taking actions (sending money, deleting records). Traditional security tools do not see these "natural-language attacks", and security teams cannot review every agent action.

**Solution.** AgentShield is a gateway between agents and their tools:
1. **Policy engine** for tool calls (who / what / how much, per agent and per user), with human approval for high-risk actions.
2. **Injection and exfiltration detection** on inputs (retrieved documents, emails, web pages) and outputs (tool arguments, messages), combining classifiers, canary tokens and data-loss-prevention patterns.
3. **Provenance tracking:** taints content from untrusted sources so it cannot trigger privileged tools without confirmation.
4. **Audit trail** of every agent decision for compliance and incident response.

**How AI contributes.** Classifiers trained on injection attempts; LLM-as-judge for ambiguous tool calls; anomaly detection on agent behaviour (an agent suddenly calling an export tool at 3 a.m.).

**Buyers.** CISOs and platform teams at mid-to-large companies deploying agents (finance, insurance, government); also agent-platform vendors (OEM).

**Business model.** Usage-based pricing (per 1,000 agent actions) + enterprise tier with on-prem deployment for regulated sectors.

## 3. Why it could win

Very current, clearly security, and we can show a **live 60-second demo**: an agent reads a poisoned document, tries to email a file out, AgentShield blocks it with an explanation. Demos win pitches.

## 4. Implementation plan

### 4.1 Research

- OWASP Top 10 for LLM Applications (prompt injection ranked first): cite the current edition.
- Two public examples of indirect prompt injection against assistants (security research write-ups).
- Competitors / adjacent: LLM firewalls and AI-security startups, cloud providers' guardrail services. Differentiate on **tool-call policy + provenance** rather than prompt filtering only, and on on-prem deployment for Canadian regulated buyers.

### 4.2 Optional demo (1–2 h)

Tiny Python agent with two tools (`read_document`, `send_email`), a poisoned document containing hidden instructions, and a gateway that (a) tags the document as untrusted, (b) blocks `send_email` with an attachment to an external domain unless a human approves, (c) shows the audit log. Record it as a 30-second video as backup.

### 4.3 Slides

1. Problem: "Votre agent IA lit un courriel… et envoie vos contrats à un inconnu." Diagram of indirect injection.
2. Solution: gateway architecture; live demo or video.
3. Business: buyers, pricing, Canadian regulated-sector angle, team.

### 4.4 Script skeleton

Hook with the attack (30 s) · why existing tools miss it (30 s) · AgentShield + demo (75 s) · business (30 s) · close (15 s).

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- Can a non-technical juror understand "prompt injection" in one sentence? Test on someone outside tech.
- Does the demo run reliably 5 times in a row offline (no API dependency during the pitch, or a recorded fallback)?

**Kill:** if the jury test shows the concept is too technical to grasp in 30 seconds and we cannot simplify it.

## 6. Risks and ethics

Fast-moving field with large incumbents; position as a focused, regulated-market product. Dual use: attack examples must be harmless.

## 7. Combines with

Strategy 5 (SOC triage) could later integrate AgentShield logs.

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Demo reliability | Verdict |
|---|---|---|---|---|---|
| | | | | | |
