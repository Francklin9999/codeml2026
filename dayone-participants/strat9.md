# DayOne · Strategy 9: Conversational review agent (WhatsApp-style)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P1 |
| **Effort** | 5–6 h |
| **Depends on** | strategy 6 (statuses / confidence) and 8 (state machine); stubs are fine at first |
| **Rubric lines** | Conversational review (20); bonuses: FR/EN interface, real WhatsApp sandbox |
| **Work folder** | `dayone-participants/work/strat9/` |

---

## 1. Context you need

Brief task 3: present extracted data, offer **Confirmer / Corriger / Reprendre la photo**, ask follow-up questions for illegible fields, allow **full manual entry** when AI is unavailable; *"L'agent dit quand il doute."* Task 6: patient matching with buttons **[Patiente 1] [Patiente 2] [Aucune, créer] [Je ne sais pas]**. Task 7: multi-page sessions form one document; when a registry is re-photographed, show the existing record and let the midwife choose what to update. Constraint: *zero change to the midwife's workflow*; the paper stays the reference. Demo must show: offline capture, connectivity return, review of an uncertain field, a match decision.

## 2. The idea

A chat flow that looks and behaves like WhatsApp, driven by a **deterministic dialogue manager** (not an LLM) that reads the record state and field statuses: it summarises what was read, asks **only about uncertain fields** (highest impact first), shows the **cropped evidence image** with each question, and offers quick-reply buttons at every step.

## 3. Why it could score

The rubric scores clarity of confirm / edit / retake, follow-ups, manual entry and multi-page sessions. A scripted, replayable flow with visible evidence crops shows doubt instead of hiding it, and it is testable with golden transcripts.

## 4. Implementation plan

### 4.1 Setup and files

```bash
pip install gradio pyyaml
# optional bonus: twilio (WhatsApp sandbox) or Meta WhatsApp Cloud API test number
```

```
work/strat9/
  chat_app.py           # Gradio UI (bubbles, images, quick replies)
  dialogue.py           # deterministic dialogue manager
  question_policy.py    # which fields to ask about, in which order
  messages_fr.yaml  messages_en.yaml
  tests/golden/*.yaml   # scripted conversations
  tests/test_golden.py
  DEMO.md               # step-by-step demo script
```

### 4.2 Dialogue manager

Input: event (photo received, button pressed, text typed, connectivity change) + record state (strategy 8) + fields (strategy 6). Output: list of messages (text, image crop, buttons) + state transitions. An LLM may only **rephrase** messages or parse free-text corrections into a typed value; it never decides transitions.

Main flows:

| Flow | Behaviour |
|---|---|
| New page | quality gate (strategy 4): fail → "Reprendre la photo" with the specific reason; pass → "Page reçue (Grossesse actuelle, 3/8). En attente de traitement" (offline) or processing |
| Summary | "J'ai lu 54 champs ; 51 sûrs, 3 à vérifier." + [Voir tout] [Vérifier les 3] |
| Uncertain field | crop image + "Tension, visite du 29/12 : je lis **115/63**, je ne suis pas sûr." [Confirmer] [Corriger] [Illisible] |
| Correction | free text → parser for the field type → validator (strategy 7) feedback ("115/63 enregistré") |
| Illegible | "Pouvez-vous me dicter la valeur ?" or [Laisser vide] |
| Validator conflict | "La date prévue d'accouchement (31/07/2026) ne correspond pas à la DDR (26/04/2025 → 31/01/2026). Laquelle est juste ?" |
| AI unavailable / offline | "Traitement automatique indisponible. Saisie manuelle ?" → field-by-field typed questions, grouped by section |
| Multi-page | session per registry code; "Pages reçues : 1, 2, 3. Manquent : 4–8." Out-of-order pages handled by page-type classification |
| Re-digitisation | existing record found → only changed fields: "Poids, visite du 29/12 : 64,8 → 66,2 ?" [Garder l'ancien] [Prendre le nouveau] |
| Match decision | candidates from strategy 10 → [Patiente 1 (code AB12, DDR 26/04/2025)] [Patiente 2 …] [Aucune, créer] [Je ne sais pas] |

### 4.3 Question policy

Score = (1 − P(correct)) × importance(field). Importance: test results (HIV, syphilis, hepatitis), BP, dates, weights first; descriptive fields last. Cap questions per page (e.g. 8); remaining low-importance uncertain fields stay À_RÉVISER and appear in a "à revoir plus tard" list. Batch trivial confirmations.

### 4.4 Language

FR default, EN toggle (bonus): all strings in `messages_*.yaml`; the dialogue manager never hard-codes text.

### 4.5 Optional real WhatsApp (bonus, last)

Twilio WhatsApp sandbox webhook → same dialogue manager; images downloaded from the media URL. Only synthetic data. Skip unless everything else is done.

## 5. How to test it

### 5.1 Golden transcripts (`tests/golden/*.yaml`)

Each file: initial state, sequence of user events, expected bot messages (text keys + buttons) and expected final record. Required set:
1. clean page, everything confident → summary + confirm;
2. page with 3 uncertain fields → 3 questions, one correction;
3. illegible field → dictated value;
4. quality-gate failure → retake → success;
5. AI unavailable → full manual entry of one page;
6. multi-page session with a missing page;
7. re-digitised registry with 2 changed fields;
8. wrong page type detected → user picks the type;
9. match decision with "Je ne sais pas" → record stays in manual review.

`pytest tests/test_golden.py` replays them; all must pass.

### 5.2 Efficiency metric

Simulated midwife who answers with the GT value: for each page in the degraded bench (strategy 4), count questions asked and residual errors after review. Target: ≤ 8 questions per page and 0 residual errors on fields shown as CONNU after review.

### 5.3 Usability

A teammate who has not seen the code completes the review of one page on a phone-sized window in < 2 minutes; note confusions.

### 5.4 Demo

`DEMO.md` scripted run covering the 4 required moments (offline capture, connectivity return, uncertain field, match decision), rehearsed 3 times.

## 6. Risks

An LLM-driven dialogue that drifts or invents. Keep decisions deterministic; tests guard it.

## 7. Combines with

Strategy 6 (what to ask), 7 (conflict messages), 8 (states), 10 (match buttons), 4 (retake reasons).

## 8. Results log

| Date | Who | Golden pass | Questions / page | Residual errors | Usability notes |
|---|---|---|---|---|---|
| | | | | | |
