# NOVA extraction audit — 2026-10-03

The parent ran Claude's recovered extractor, then independently compared every indexed source digest with the supplied ZIP and extracted bytes. Four synthetic audit regression tests pass.

| Check | Measured result |
|---|---:|
| ZIP members / indexed extracted files | 64 / 64 |
| Unique locator IDs after screenshot transcription | 1,045 |
| Extractor decoding fallbacks / errors | 0 / 0 |
| Extracted attachments / matching standalone files | 5 / 5 |
| Source identity, index and attachment-integrity issues | 0 |
| Screenshot placeholders / images without locators | 0 / 0 |
| Manually transcribed screenshots / screenshot units | 8 / 58 |

The initial audit found eight screenshot placeholders and 979 locators. The parent then viewed all eight supplied images, transcribed visible text into versioned `transcriptions/*.md`, and regenerated extraction: all 64 files now have locators, including 58 screenshot units. Table separators are explicitly transcription formatting; no capture dates, defect causes or later validation are inferred from an image. This is extraction identity/coverage evidence plus manual visual transcription, not full semantic validation: PDF row correctness, claim entailment, facts, answers, chronology, the final memory and live-event updates remain unvalidated. No jury score is claimed.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -X utf8 loto-quebec-nova-participants/work/strat1/extract.py
.\.venv\Scripts\python.exe -X utf8 loto-quebec-nova-participants/work/strat1/audit_extract.py
.\.venv\Scripts\python.exe -m unittest discover -s loto-quebec-nova-participants/work/strat1 -p test_audit_extract.py -v
```

The extractor replaces its generated `work/_local/{corpus,text,attachments,images}` directories. Confirm those resolved targets are inside this workspace and are not reparse points before rerunning it. Source ZIP and datasets remain untouched; generated text/images are git-ignored.
