# DayOne · Strategy 3: Whole-page VLM extraction with a JSON schema

| | |
|---|---|
| **Status** | DONE - not adopted (Claude Code, 2026-10-03) |
| **Priority** | P1 (extractor B; fastest path to a working pipeline) |
| **Effort** | 4–6 h |
| **Depends on** | strategy 1 (schema, ground truth) |
| **Rubric lines** | Extraction quality (30), Uncertainty (20) |
| **Work folder** | `dayone-participants/work/strat3/` |

---

## 1. Context you need

- Schema, statuses and ground truth: strategy 1. Real photos and their difficulties: strategy 2 §1.
- **Data rules:** the data is synthetic, but the design must hold for real patients: *"aucune donnée réelle de patiente ne peut être envoyée à un service tiers"*. The brief's architecture queues pages "En attente de traitement IA" offline and processes them **when connectivity returns**, so server-side AI is allowed architecturally, as long as real data would go to a self-hosted or compliant server.
- The global Python on this machine has `torch 2.4.1+cu121`; check whether a CUDA GPU is present (`python -c "import torch; print(torch.cuda.is_available())"`).

## 2. The idea

Send the page image (or tiles of it) to a vision-language model together with the page type's JSON schema, allowed values and status definitions; get back a structured object (value, status, raw text read) per field. Compare a **local open model** with a **hosted frontier model** (synthetic data only, declared).

## 3. Why it could score

VLMs read handwriting and use table context far better than classic OCR, and they handle French, Arabic and English natively. It is the quickest route to a working extractor; strategy 2 is the complement or fallback.

## 4. Implementation plan

### 4.1 Models

| Role | Candidates | Notes |
|---|---|---|
| Local (production-like) | Qwen2.5-VL-7B-Instruct (Apache-2.0); Qwen2.5-VL-3B if VRAM < 16 GB; alternatives MiniCPM-V 2.6, InternVL2 | `transformers` ≥ 4.49 or `vllm`; 4-bit with `bitsandbytes` if needed |
| Hosted (upper bound, synthetic only) | any frontier VLM API | declare it; never used with real data in the documented design |

### 4.2 Files

```
work/strat3/
  prompts/p1.md ... p8.md      # per page type: field list, enums, status rules, output JSON schema
  vlm_extract.py               # image → schema Page
  self_consistency.py          # N samples → agreement per field
  eval_03.md
```

### 4.3 Prompt structure (per page type)

```
Tu lis une page de registre maternel (type: GROSSESSE ACTUELLE).
Retourne UNIQUEMENT un JSON conforme au schéma ci-dessous.
Pour chaque champ : "value" (texte lu, normalisé), "raw" (exactement ce qui est écrit), "status".
Statuts : CONNU (lu avec certitude) ; ILLISIBLE (quelque chose est écrit mais illisible) ;
NON_FOURNI (case vide sur le papier, ou un tiret) ; NON_APPLICABLE (la logique du formulaire l'exclut) ;
À_RÉVISER (lu mais doute) ; INCONNU (la sage-femme a écrit « inconnu », « ? »).
N'invente jamais une valeur pour une case vide. N'écris jamais de nom, numéro CIN, téléphone ou adresse.
Schéma : {...}
```

Include allowed vocabularies (RAS, Normales, Oui/Non, Neg/Pos, Fermé, Céphalique, Immune…) and accepted formats (dates dd/mm/yyyy, BP sys/dia).

### 4.4 Structured output

- Local: grammar-constrained decoding (`outlines` or `lm-format-enforcer` with the Pydantic schema), else parse + validate + one retry with the validation error.
- Hosted: JSON mode / tool-call schema.

### 4.5 Tiling for dense pages

*Grossesse actuelle* has ~30 rows × 9 visit columns. Variant: send three vertical bands (row-label column + 3 visit columns each) at full resolution and merge. Compare accuracy and latency with the whole page.

### 4.6 Confidence signals (consumed by strategy 6)

- token log-probabilities of each value (local model: `output_scores=True`);
- **self-consistency:** 5 samples at temperature 0.7 → per-field agreement rate;
- agreement with strategy 2's zonal reading when available.

## 5. How to test it

### 5.1 Datasets

80 clean specimen pages, strategy 4's degraded pages, the 5 hand-labelled photos, strategy 5's AR/EN pages.

### 5.2 Metrics

| Metric | Why |
|---|---|
| Field accuracy (type-aware normalisation) | rubric 30 pts |
| Status accuracy (vs GT statuses) | rubric 20 pts |
| **Hallucination rate on blanks** (value produced where GT is NON_FOURNI) | the most dangerous error in a medical record |
| **Identifier leak rate** (any name / CIN / phone / address string in output) | must be 0 |
| Latency per page (GPU / CPU) | demo feasibility |

### 5.3 Comparisons

local vs hosted vs strategy 2 vs hybrid (VLM on strategy 2's registered crops); whole page vs bands.

### 5.4 Acceptance / kill

- **Target:** local model ≥ 90% field accuracy on clean pages, hallucination on blanks < 2%, 0 identifier leaks.
- **Kill:** local model < 70% on clean pages after prompt iteration → switch to the hybrid (crops) or strategy 2.

## 6. Risks

Hallucinated values in blank cells; slow inference on CPU (the offline queue tolerates latency, but the live demo needs a GPU or a hosted model with synthetic data).

## 7. Combines with

Strategy 1 (scoring), 2 (hybrid), 5 (AR/EN tests), 6 (confidence), 7 (catches impossible values).

## 8. Results log

| Date | Who | Model | Dataset | Field acc. | Halluc. on blanks | Leaks | Latency |
|---|---|---|---|---|---|---|---|
| 2026-10-03 | Claude Code | Qwen2.5-VL-3B-Instruct, 4-bit, local | 200 filled crops, pages 9-24, clean / sev 2 | 0.650 / 0.245 (CRNN raw on same crops 0.840 / 0.590) | not measured on blanks | 0 (identifier zones masked before reading) | 110 ms/crop (~30 s/page) |

**Implementation notes (2026-10-03).** Hybrid variant (VLM reads the registered zone crops with field label + vocabulary in the prompt). The VLM is right where the CRNN is wrong on only 8% (clean) / 6.5% (sev 2) of fields, mostly vocabulary words that constrained rescoring already repairs; too slow for full pages on an 8 GB laptop GPU. A 7B model or a hosted model was not tried (8 GB VRAM, and real data must stay local). Code kept (`work/strat3/`) for a cascade on low-confidence fields.
