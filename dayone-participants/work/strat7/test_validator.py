"""Strategy 7 tests: T1 no false alarms on the 10 GT booklets; T2/T3 injected OCR-like date errors are caught and
repaired when the recogniser finds the implied value plausible (stub scorer: edit-distance based)."""
import copy
import json
import random
import sys
from pathlib import Path

W = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(W / "shared"), str(W / "strat7")]
from common import GT_DIR  # noqa: E402
from validator import validate_booklet  # noqa: E402


def booklets():
    pages = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(GT_DIR.glob("page_*.json"))]
    out = {}
    for g in pages:
        g = copy.deepcopy(g)
        for f in g["fields"]:
            f["confidence"] = 0.95
        out.setdefault(g["patient"], []).append(g)
    return out


class EditScorer:
    """Stands in for the CRNN: log-likelihood falls with the edit distance to what is 'written'."""
    def __init__(self, truth):
        self.truth = truth

    def score(self, lp, text):
        from rapidfuzz.distance import Levenshtein
        return -3.0 * Levenshtein.distance(self.truth[lp], text or "")


def test_no_false_alarms_on_gt():
    n_issues = 0
    for pid, pages in booklets().items():
        iss = validate_booklet(pages)
        n_issues += len(iss)
        assert not iss, (pid, iss)
    assert n_issues == 0


def test_injected_date_errors_repaired():
    random.seed(0)
    caught = repaired = total = 0
    targets = [(3, "inline.date_prevue_d_accouchement"), (3, "inline.date_de_depassement_de_terme"),
               (4, "inline.age_gestationnel"), (6, "inline.age"), (6, "inline.date_de_la_consultation")]
    for pid, pages in booklets().items():
        for t, key in targets:
            pg = copy.deepcopy(pages)
            truth = {}
            for p in pg:
                p["_lp"] = {}
                for f in p["fields"]:
                    if f["type"] == "text" and f.get("value"):
                        k = (p["page_type"], f["key"]); truth[k] = f["value"]; p["_lp"][f["key"]] = k
            p = next(p for p in pg if p["page_type"] == t)
            f = next(f for f in p["fields"] if f["key"] == key)
            orig = f["value"]
            v = list(orig)
            i = random.choice([j for j, c in enumerate(v) if c.isdigit()])
            v[i] = {"1": "7", "7": "1", "3": "8", "8": "3", "0": "6", "6": "0", "5": "6", "4": "9", "9": "4", "2": "7"}[v[i]]
            f["value"] = "".join(v)
            f["confidence"] = 0.6
            iss = validate_booklet(pg, EditScorer(truth))
            total += 1
            caught += any(x["key"] == key for x in iss)
            repaired += f["value"] == orig
    print(f"caught {caught}/{total}, repaired {repaired}/{total}")
    assert caught / total >= 0.8 and repaired / total >= 0.7
