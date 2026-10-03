# NOVA · Strategy 20: Presentation choreography: a scripted, rehearsed jury walkthrough

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 (the deliverable is judged through the presentation) |
| **Effort** | 3 h + rehearsals |
| **Depends on** | a working deliverable; strategies 6 (event drills), 12 (follow-up bank), 19 (limits) |
| **Rubric lines** | Use & uncertainty (10: "l'équipe montre sa recherche et explicite les limites lors de la question complémentaire"), Evidence (10), Update (10, the live part), overall impression |
| **Differs from 1–10** | Strategy 6 rehearses only the live event. This designs and rehearses the **whole presentation**: timing, who speaks, what is clicked, how a proof is shown, how the event slot and the follow-up question are handled, and a fallback if anything fails |
| **Work folder** | `loto-quebec-nova-participants/work/strat20/` |

---

## 1. Context you need

- The jury evaluates by opening the deliverable and finding proofs, by the team's demonstration of its search, by the live event integration, and by the follow-up question.
- *"Une solution simple qui fonctionne bien vaut mieux qu'une architecture extrêmement ambitieuse qui ne fonctionne qu'en partie."* and *"Nous évaluons votre capacité à comprendre le problème, concevoir une solution utile…"*
- Unknown: exact presentation length and format (ask the organisers; prepare a 5-minute and an 8-minute version).

## 2. The idea

Write a **run sheet** for the presentation and rehearse it like a demo: each minute has a speaker, a screen, a point, and a click path. Build in the moments that score: showing a proof live in two clicks, explaining one contradiction by authority and date, handling the event with the "changed / unchanged / proposal / actions / unknowns" structure, and stating limits.

## 3. Why it could score

Several rubric findings are only observable live. Teams with good content lose points when the demo wanders, a link breaks, or the event is answered vaguely.

## 4. Implementation plan

### 4.1 Files

```
work/strat20/
  run_sheet.md          # minute-by-minute script, speakers, click paths
  click_paths.md        # exact navigation for each planned proof
  fallback/             # PDF export of every page + screenshots, offline
  rehearsal_log.md
```

### 4.2 Draft run sheet (5 minutes, adapt)

| Time | Speaker | Screen | Point |
|---|---|---|---|
| 0:00–0:30 | A | brief | "Voici ce qu'il faut savoir lundi matin": owner, 22 Oct conditional, 3 conditions, budget / INV-003 |
| 0:30–1:30 | B | Q08 → SEC-210 ticket → Teams 19 Sept | live proof in two clicks; "déployé ≠ accepté" |
| 1:30–2:15 | B | contradictions page | Plan v3 (15 Oct) vs committee (22 Oct); register R-01 stale ("suivi au 9 septembre") |
| 2:15–2:45 | C | actions page | conditions → owners → due dates or "à confirmer"; commitment vs recommendation |
| 2:45–3:15 | C | limits page | what we do not know, tools used (incl. AI), manual steps |
| 3:15–5:00 | A + C | event integration | read the event aloud, apply, show diff vs baseline, say what does *not* change |

### 4.3 Roles

A = narrator and time-keeper; B = proof navigator (drives the screen); C = event integrator (uses strategy 5 / 6 tools). Everyone can answer "where is the proof of X?".

### 4.4 Fallbacks

Deliverable copied on two laptops and a USB key; a PDF export of every page; screenshots of the key click paths; the event handled on paper with the impact map if the tooling fails.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Timed rehearsals | 3 full runs within ±15 s of the target length |
| T2 | Cold proof requests | a teammate names 5 random facts; the navigator shows each proof in ≤ 2 clicks |
| T3 | Event slot | with an unseen event, the integration fits its time slot and covers changed / unchanged / proposal / actions / unknowns |
| T4 | Follow-up | 10 questions from strategy 12's bank answered in ≤ 30 s each, pointing to the deliverable |
| T5 | Failure drill | mid-rehearsal, close the browser: the team switches to the fallback in < 30 s |

## 6. Risks

Over-scripting makes the event answer sound rehearsed even when the event differs. Rehearse the structure, not the content.

## 7. Combines with

Strategy 6, 12, 19, 9, 16.

## 8. Results log

| Rehearsal | Length | Proof requests (≤ 2 clicks) | Event slot OK | Issues |
|---|---|---|---|---|
| | | | | |
