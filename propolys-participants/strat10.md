# Propolys · Strategy 10: "DepGuard": stopping malicious open-source packages before they reach developers

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (solid security problem, but technical and crowded; good backup idea) |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Work folder** | `propolys-participants/work/strat10/` |

---

## 1. Context you need

See [strat1.md §1](strat1.md) for the challenge format and criteria. One of ten alternative concepts; use the shared validation protocol.

## 2. The idea

**Problem.** Modern software is assembled from thousands of open-source packages. Attackers publish typo-squatted packages, take over abandoned maintainers' accounts, or slip malicious code into updates; one compromised dependency can reach thousands of companies. Small dev teams install updates automatically and never read the code.

**Solution.** DepGuard is a proxy in front of package registries (npm, PyPI) for a company's developers and CI:
1. Every new package or version is **analysed before it is allowed**: install scripts, network and file-system behaviour in a sandbox, obfuscated code, new maintainers, sudden permission changes, name similarity to popular packages.
2. A **risk score with reasons**; risky versions are quarantined; safe ones pass with no friction.
3. An inventory (SBOM) of what is used where, so the team knows its exposure when a new attack is announced.

**How AI contributes.** Classifiers on code and metadata features; LLM summarisation of suspicious diffs ("this update adds code that sends environment variables to an external server"); anomaly detection on maintainer behaviour.

**Buyers.** Software SMEs, startups, agencies; CI/CD platforms (OEM).

**Business model.** Per-developer subscription; free tier for open-source projects to build reputation and data.

## 3. Why it could win

Clear threat and a crisp demo (a typo-squatted package blocked before install). Weaker on originality because established supply-chain security vendors exist; we would need a sharp niche (e.g. Python data-science teams, French-speaking SMEs, an extremely simple setup).

## 4. Implementation plan

### 4.1 Research

- Public reports on malicious packages found in npm / PyPI (security vendors' annual reports; cite).
- Competitors: software-composition-analysis and supply-chain security vendors; identify what they charge and whom they target; find our niche.

### 4.2 Slides

1. Problem: one real incident (well documented) + "votre équipe installe 300 mises à jour par mois sans les lire".
2. Solution: proxy diagram; alert mock with an LLM explanation of a malicious diff.
3. Business: per-developer pricing, niche, team.

### 4.3 Script skeleton

Incident story · why small teams are exposed · DepGuard flow · niche and business · close.

## 5. How to test it

Shared scorecard, mock jury and timing from [strat1.md §5](strat1.md). Specific checks:
- **Originality test** (same as strategy 5): list the closest 3 products; if the niche is not crisp in one sentence, score ≤ 2.
- Non-technical clarity: can a non-developer juror explain what a "package" is after the hook?

**Kill:** if originality ≤ 2 and no niche emerges after one rewrite.

## 6. Risks and ethics

Crowded market; sandboxing malicious code safely (operational security of our own infrastructure).

## 7. Combines with

Strategy 3 (agents increasingly install packages themselves: AgentShield could include DepGuard checks).

## 8. Results log

| Date | Who | Scorecard /30 | Originality score | Mock-jury avg | Verdict |
|---|---|---|---|---|---|
| | | | | | |
