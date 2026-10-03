# NOVA extraction audit — 2026-10-03

The parent ran Claude's recovered extractor, then independently compared every indexed source digest with the supplied ZIP and extracted bytes. Four synthetic audit regression tests pass.

| Check | Measured result |
|---|---:|
| ZIP members / indexed extracted files | 64 / 64 |
| Unique locator IDs | 979 |
| Extractor decoding fallbacks / errors | 0 / 0 |
| Extracted attachments / matching standalone files | 5 / 5 |
| Source identity, index and attachment-integrity issues | 0 |
| Screenshot placeholders / images without locators | 8 / 8 |

The eight screenshots have **not** been transcribed. Their placeholders are not evidence text. This is extraction identity/coverage evidence only: locator semantics, PDF row correctness, quotes, facts, answers, chronology, the final memory and live-event updates are not validated. No jury score is claimed.

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -X utf8 loto-quebec-nova-participants/work/strat1/extract.py
.\.venv\Scripts\python.exe -X utf8 loto-quebec-nova-participants/work/strat1/audit_extract.py
.\.venv\Scripts\python.exe -m unittest discover -s loto-quebec-nova-participants/work/strat1 -p test_audit_extract.py -v
```

The extractor replaces its generated `work/_local/{corpus,text,attachments,images}` directories. Confirm those resolved targets are inside this workspace and are not reparse points before rerunning it. Source ZIP and datasets remain untouched; generated text/images are git-ignored.
