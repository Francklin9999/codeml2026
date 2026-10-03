# DayOne · Strategy 14: Real WhatsApp integration (Business Platform Cloud API or Twilio sandbox)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (bonus; only after the core flow works) |
| **Effort** | 4–6 h |
| **Depends on** | strategy 9 (dialogue manager), 8 (store / queue) |
| **Rubric lines** | bonus "Connecter l'agent à un bac à sable WhatsApp réel (WhatsApp Business Platform)"; Conversational review (20) demo realism |
| **Differs from 1–10** | Strategy 9 builds a WhatsApp-**style** simulator. This connects the same dialogue manager to **real WhatsApp** through a sandbox, with media download, interactive buttons and webhook reliability |
| **Work folder** | `dayone-participants/work/strat14/` |

---

## 1. Context you need

- Bonus in the brief: connect to a real WhatsApp sandbox (WhatsApp Business Platform). Bonuses only break ties.
- Constraints: synthetic data only; *"aucune donnée réelle de patiente ne peut être envoyée à un service tiers"* (WhatsApp / Meta / Twilio are third parties: in the design document, explain that real deployment would require an approved data-processing setup or keep images on device and send only non-identifying prompts).
- The offline layer must work without internet: WhatsApp itself needs connectivity, so offline capture stays in the device app (strategy 15) or is simulated; WhatsApp is the "online" channel.

## 2. The idea

Expose strategy 9's deterministic dialogue manager behind a webhook:
- **Option A, Meta WhatsApp Cloud API (test number):** free test phone number, up to 5 recipient numbers, webhook for incoming messages, Graph API to send text, images and **interactive reply buttons** (max 3 buttons per message, so use list messages for 4+ options like the patient-match choice).
- **Option B, Twilio WhatsApp sandbox:** quicker setup (join code), simple webhook; buttons via templates are limited, so fall back to numbered replies ("1 Confirmer, 2 Corriger, 3 Reprendre").

## 3. Why it could score

A live demo on a real phone in WhatsApp is memorable and directly answers the brief's framing ("agent WhatsApp"). The integration is thin if strategy 9 already separates dialogue logic from UI.

## 4. Implementation plan

### 4.1 Files

```
work/strat14/
  webhook.py           # FastAPI: GET verification, POST messages → dialogue manager → send replies
  wa_client.py         # send_text, send_image, send_buttons, send_list, download_media
  adapters.py          # map dialogue-manager messages ↔ WhatsApp message types
  idempotency.py       # dedupe webhook retries by message id
  .env.example         # tokens (never commit real tokens)
  SETUP.md             # step-by-step sandbox setup with screenshots
```

### 4.2 Flow

1. Midwife sends a photo → webhook receives `messages[].image.id` → `download_media` (Graph API media URL with the bearer token) → store encrypted (strategy 8) → enqueue for processing → reply "Page reçue, traitement en cours".
2. When processing finishes, send the summary and the first uncertain field with its **crop image** and buttons [Confirmer] [Corriger] [Illisible].
3. Corrections arrive as text → parsed by the field-type parser → validator feedback.
4. Patient match: list message with [Patiente 1 …] [Patiente 2 …] [Aucune, créer] [Je ne sais pas].
5. Webhook reliability: respond 200 within seconds (process asynchronously); dedupe by message id (WhatsApp retries); store conversation state server-side keyed by phone number hash (no phone number in clear in logs).

### 4.3 Exposure

Local dev via a tunnel (Cloudflare Tunnel / ngrok) to get an HTTPS URL for the webhook; record which tunnel was used.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | End-to-end | photo → summary → 2 confirmations → 1 correction → match decision, on a real phone |
| T2 | Retries | replaying the same webhook payload does not duplicate records |
| T3 | Media | images arrive at full resolution (WhatsApp compresses photos: measure the resolution; the brief's other challenge notes WhatsApp photos are recompressed, so check extraction accuracy on WhatsApp-received images vs originals) |
| T4 | Latency | acknowledgement < 3 s; summary after processing |
| T5 | Secrets | no token in Git history (`git log -p | grep -i token`) |

## 6. Risks

- WhatsApp's image compression may hurt extraction (T3). Mitigation: ask users to send the photo **as a document** (keeps the original), and say so in the bot's instructions.
- Account / verification steps can take time; start setup early or use Twilio.

## 7. Combines with

Strategy 9 (dialogue), 8 (queue, store), 15 (offline device app for capture without network).

## 8. Results log

| Date | Who | Option | T1–T5 | Image resolution received | Notes |
|---|---|---|---|---|---|
| | | | | | |
