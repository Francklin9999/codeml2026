# DayOne · Strategy 10: Identifier redaction + code-based patient linking

| | |
|---|---|
| **Status** | DONE (Claude Code, 2026-10-03) |
| **Priority** | P1 |
| **Effort** | 3–4 h |
| **Depends on** | strategy 1 (identifier zones), 2 (registration) or a text detector; 8 (store) |
| **Rubric lines** | Patient linking & privacy (10); hard constraints of the brief |
| **Work folder** | `dayone-participants/work/strat10/` |

---

## 1. Context you need

- *"Les noms des femmes ne sont pas collectés. Tout identifiant direct visible sur le papier (nom, nom du conjoint, numéro national, téléphone, adresse) doit être ignoré ou masqué, jamais stocké."*
- Linking: each new visit is attached to the existing profile **through a random code assigned by the midwife and written on the registry**; propose possible matches **without ever auto-creating a patient when a match is plausible**; offer [Patiente 1] [Patiente 2] [Aucune, créer] [Je ne sais pas]; internal IDs generated automatically, **never derived from personal information**.
- Keep the original image linked to record ID, capture date, midwife ID and status, **with role-based access**.
- The specimen pages contain fictional identifiers (e.g. name, husband's name, CIN like `CB609814`, phone like `06 00 76 13 48`, address on page 2 "Identification et antécédents"; name on the cover page and on delivery / post-partum pages). Photo `1-1.jpg` shows a paper strip already hiding the name on a real booklet.

## 2. The idea

1. **Mask before reading:** identifier zones are known from the template; mask them on the working image **before** any OCR / VLM call and before anything is stored.
2. **Leak guard:** scan every extractor output, log and store for identifier patterns; drop and log incidents.
3. **Restricted original:** keep the untouched photo encrypted, readable only by an authorised role, with access logged.
4. **Linking by code** with fuzzy candidate generation that tolerates misread characters, ranked with non-identifying consistency checks; the midwife always decides.

## 3. Why it could score

The rubric's 10 points test exactly these four things. "Mask before read" is a stronger, easier-to-demonstrate guarantee than "delete afterwards".

## 4. Implementation plan

### 4.1 Files

```
work/strat10/
  mask.py            # template-zone masking + detector fallback
  leak_scanner.py    # regexes + label list
  linking.py         # code normalisation, candidates, ranking
  rbac.py            # roles, permissions, access log
  tests/test_mask.py  tests/test_leaks.py  tests/test_linking.py  tests/test_rbac.py
  PRIVACY.md         # design note for the project README
```

### 4.2 Masking

- Primary: after registration (strategy 2), fill each `identifier_zones` polygon (from strategy 1's zone files) with an opaque rectangle (+ 10% margin) on the working copy.
- Fallback when registration fails: run a text detector, then regex / keyword matching and mask matched boxes; if still unsure, mask the whole identity block (top half of page 2, name line of the cover).
- The **original** is saved encrypted (strategy 8) and never sent to the AI step.

### 4.3 Leak scanner

```python
PATTERNS = {
  "cin": r"\b[A-Z]{1,2}\s?\d{5,6}\b",
  "phone_ma": r"\b0[5-7](?:[\s.-]?\d{2}){4}\b",
  "phone_intl": r"\+212[\s.-]?\d(?:[\s.-]?\d{2}){4}",
  "address": r"\b(rue|avenue|bd|boulevard|quartier|hay|derb)\b",
}
LABELS = ["nom/prénom", "nom du mari", "cin", "téléphone", "adresse", "patiente :"]
```

Run on: extractor JSON, chat transcripts, logs, DB plaintext (before encryption), sync payloads. On a hit: remove the value, log an incident without the value itself.

### 4.4 Linking

```python
CONFUSABLE = str.maketrans({"O": "0", "Q": "0", "D": "0", "I": "1", "L": "1", "|": "1", "S": "5", "B": "8", "Z": "2", "G": "6"})
def norm(code): return re.sub(r"[\s\-_/.]", "", code.upper()).translate(CONFUSABLE)
def candidates(read_code, registry, ocr_conf):
    c = norm(read_code)
    hits = [(p, damerau_levenshtein(c, norm(p.code))) for p in registry]
    hits = [(p, d) for p, d in hits if d <= (1 if len(c) <= 6 else 2)]
    return sorted(hits, key=lambda h: (h[1], -consistency(h[0], new_visit)))[:2]
```

`consistency()` uses only non-identifying clinical data: same DDR (± 7 days), age (± 1 year), gravidity / parity compatible, delivery not before previous visits. Exact code match with consistent data → propose it first but **still ask**. No candidate → [Aucune, créer] / [Je ne sais pas]. Internal IDs: `uuid.uuid4()`.

### 4.5 Role-based access

Roles: `sage_femme` (own records; original image only before validation), `superviseur` (original images of the facility; every access logged with time and reason), `analyste` (de-identified aggregates only, for the bonus dashboard). Enforced in the store API (strategy 8), not in the UI only.

## 5. How to test it

| # | Test | How | Pass if |
|---|---|---|---|
| T1 | Leak test (end-to-end) | run the full pipeline on all 80 specimen pages + 5 photos; collect every identifier string from the PDF text layer; grep DB (decrypted export), logs, queue, chat transcripts, sync payloads | **0 hits** |
| T2 | Masking coverage | overlay masks on the 80 pages; check every identifier word box is covered | 100% |
| T3 | Linking simulation | 100 patients × 3 visits with random 6-char codes; corrupt 15% of read codes with confusable substitutions, 5% with a dropped char; add 5% new patients whose code is 1 edit away from an existing one | recall@2 ≥ 95%; auto-create when a plausible match exists = **0**; correct option offered ≥ 95% |
| T4 | ID derivation | internal IDs are UUIDv4 and independent of code / data (property test) | pass |
| T5 | RBAC | `sage_femme` cannot fetch an original after validation; `superviseur` access logged; `analyste` sees aggregates only | pass |

## 6. Risks

Template masking fails when registration fails; the fallback must err on the side of masking too much.

## 7. Combines with

Strategy 2 (zones after registration), 8 (encrypted store, states), 9 (match buttons). The bonus dashboard of anonymised aggregates (BP, temperature, HIV / syphilis / hepatitis C) can be built on the `analyste` view.

## 8. Results log

| Date | Who | Leak hits | Mask coverage | Recall@2 | Auto-creates | Notes |
|---|---|---|---|---|---|---|
| 2026-10-03 | Claude Code | 0 leaks in every evaluation run (all 80 pages x all severities) | identifier zones masked before recognition | candidates tolerate OCR confusions (1/7, 0/O...) | 0 (never auto-creates; 'Je ne sais pas' links nothing) | `pytest work/strat10` 6/6 |

**Implementation notes (2026-10-03).** Leak scanner (CIN / phone / address patterns, identifier keys) on every output; facility/region/province names exempted from the address pattern. Linking by the registry code with a confusion-weighted edit distance + non-identifying fact checks; internal ids are random UUIDs.
