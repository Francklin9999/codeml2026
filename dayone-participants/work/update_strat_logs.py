"""Write the 2026-10-03 implementation status and results into each strategy write-up (strat1.md ... strat20.md).

Replaces the Status line and rewrites section '## 8. Results log' (the last section of every write-up):
original table header + a filled row + implementation notes. Idempotent.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((Path(__file__).resolve().parent / "strat_results.json").read_text(encoding="utf-8"))

for n, info in R.items():
    p = ROOT / f"strat{n}.md"
    s = p.read_text(encoding="utf-8")
    s = re.sub(r"\| \*\*Status\*\* \|[^\n]*\|", f"| **Status** | {info['status']} |", s, count=1)
    i = s.index("## 8. Results log")
    lines = s[i:].split("\n")
    header = [l for l in lines[1:] if l.startswith("|")][:2]
    s = s[:i] + "## 8. Results log\n\n" + "\n".join(header) + "\n" + info["row"].strip() + "\n\n" + \
        f"**Implementation notes ({info.get('date', '2026-10-03')}).** " + info["notes"].strip() + "\n"
    p.write_text(s, encoding="utf-8")
    print("updated", p.name)
