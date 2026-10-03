# DayOne · Strategy 36: Offline language-pack and font coverage manifest

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P2 |
| **Effort** | 2 h |
| **Depends on** | strategy 5 multilingual fixtures; strategy 15 PWA optional |
| **Work folder** | `dayone-participants/work/strat36/` |

## 1. Context and evidence

The challenge requires French, Arabic, and English; the specimen text layer is French-only and no phone OCR labels exist (`work/shared/report.md`). Strategy 5 proposes multilingual synthetic pages. This idea verifies that the actual offline review interface can display scripts and switch direction correctly; it does not claim recognition support or create language training data.

Evidence: [DayOne evaluation audit](work/shared/report.md) states the specimen labels are not reviewed and Arabic is absent.

## 2. Idea and distinction

Inventory bundled fonts, text shaping, keyboard entry, date/numeric direction, and fallback behavior for each supported locale. Render a fixed pack of mixed-script UI strings and synthetic values in RTL/LTR combinations. Fail the build if a glyph is missing, punctuation order changes, or an input field reverses digit entry unexpectedly.

## 3. Rubric relevance

Supports usable review in the target languages and robust offline operation without overclaiming model capability.

## 4. Implementation steps

Create `work/strat36/coverage.json`, screenshot fixtures, and browser checks under the DayOne work folder. Record font licenses and bundle only authorized assets. Label OCR language support separately from interface localization.

## 5. Proposed experiment

Render 60 fixed strings (20 per language) in offline mode on two browser engines. Baseline: current default font/locale. Adopt if every string renders without tofu glyphs and 100% of manually checked number/date sequences preserve intended order; kill or mark a language unsupported in UI if either browser fails. Proposed, not measured.

## 6. Risks

Correct rendering is not correct translation or clinical terminology. Have qualified speakers review wording; do not invent treatment content.

## 7. Combinations

Pairs with strategies 5, 9, 14, 15, and 23.

## 8. Results log

NOT RUN. No browser coverage audit has been conducted.
