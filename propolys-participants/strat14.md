# Propolys · Strategy 14: "ProvenanceDesk": deepfake and provenance verification for newsrooms

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 3 h |
| **Rubric lines** | clear & original idea · link to security · entrepreneurial potential · pitch quality |
| **Differs from 1–10** | Strategies 2 and 6 fight impersonation in **private calls**. This protects **public information**: helping journalists verify whether images, audio and video circulating during elections or crises are authentic, combining content credentials (provenance metadata) with AI forensics |
| **Work folder** | `propolys-participants/work/strat14/` |

---

## 1. Context you need

Format, criteria and validation protocol: [strat1.md §1 and §5](strat1.md). Theme: "Who is really behind the screen? Deepfakes, synthetic voices and AI-generated content".

## 2. The idea

**Problem.** Newsrooms receive viral images and clips during elections, disasters and conflicts and must decide in minutes whether to publish or debunk. Detection tools alone are unreliable; provenance standards (content credentials) are emerging but rarely checked systematically.

**Solution.** ProvenanceDesk is a verification workspace:
1. **Provenance check:** reads content credentials (C2PA manifests) when present, shows the capture / edit chain, and flags missing or broken credentials.
2. **AI forensics:** multiple detectors (image generation artefacts, voice-clone indicators, face manipulation) presented as **evidence with uncertainty**, never a single "fake" verdict.
3. **Context search:** reverse image / video search, earliest appearance, geolocation hints, weather and shadow consistency checks.
4. **Shared verdict log** across newsroom staff, exportable as a public "how we verified this" note.

**How AI contributes.** Ensemble detectors; similarity search for earlier copies; LLM assistance to draft verification notes citing the evidence.

**Buyers.** Newsrooms (national and regional, French-language first), fact-checking organisations, public broadcasters, election bodies' communication teams.

**Business model.** Seat-based SaaS for newsrooms; discounted tier for non-profit fact-checkers; grants and media-innovation funds.

## 3. Why it could win

Very visible threat, clear public-interest value, and an honest design (evidence and provenance, not magic detection), which a security jury will appreciate.

## 4. Implementation plan

### 4.1 Research

- C2PA / Content Credentials: what the standard provides and which cameras / tools sign content today (cite the coalition's site).
- One documented deepfake incident in an election or crisis (reputable source).
- Competitors: deepfake-detection vendors and verification plug-ins used by journalists; our angle: provenance-first, French-language workflow, newsroom collaboration and public transparency notes.

### 4.2 Slides

1. Problem: a viral fake image example (clearly labelled as an example) + time pressure on journalists.
2. Solution: workspace mock showing provenance chain, detector evidence with confidence bars, earliest appearance, and the draft public note.
3. Business: newsroom pricing, fact-checker tier, pilot with one newsroom, team, ask.

### 4.3 Script skeleton

Hook (a fake image during an emergency) · why detection alone fails · provenance + evidence workflow · public trust · business · close.

## 5. How to test it

Shared protocol in [strat1.md §5](strat1.md). Specific checks:
- Honesty test: can we explain why we don't output "fake / real" alone?
- Market check: do newsrooms pay for tools, or rely on free ones? Find one example of paid verification tooling or funding programmes.

**Kill:** if the buyer cannot pay and no grant / public-funding route is credible.

## 6. Risks and ethics

Errors could discredit true content; transparency notes and human judgement are central. Detector arms race.

## 7. Combines with

Strategy 7 (crisis information), 2 / 6 (voice-clone detection components).

## 8. Results log

| Date | Who | Scorecard /30 | Mock-jury avg | Top objection | Verdict |
|---|---|---|---|---|---|
| | | | | | |
