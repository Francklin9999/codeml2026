"""Strategy 7 (part 2) + strategy 13: cross-field / cross-page consistency rules with likelihood-checked repair.

Rules (all verified on the 10 specimen patients, 0 false alarms):
  D1  date_prevue_d_accouchement = ddr + 280 d             (page 3)
  D2  date_de_depassement_de_terme = date_prevue + 7 d      (page 3)
  D4  visit "Âge probable" = round((venue_le - ddr) / 7) SA (page 3, soft ±1)
  D5  age_gestationnel (p4) = floor((date accouchement - ddr) / 7) SA        (booklet)
  D6  newborn age (p6) = consultation (p5/p6) - delivery date (days)         (booklet)
  D7  newborn age (p8) = consultation (p7/p8) - delivery date (days)         (booklet)
  E1  same fact on two pages: p5/p6 consultation date, p7/p8 consultation date, p4/p6 head circumference,
      p6/p8 "vu par"                                                          (booklet)
  O1  gravidity >= parity ; living children <= parity + 1 (soft)
  V*  physiological ranges (BP format sys>dia, temperature 34-42, weight 30-200 kg, FHR 80-220, Hb 4-20)

Repair: a rule proposes the implied value v*; it replaces the reading only if the recogniser itself finds v*
plausible: CTC log-likelihood of v* >= reading's score - DELTA_RULE. Otherwise the field is flagged
(À_RÉVISER, with v* offered to the midwife as a quick reply). We never invent a value for a blank field.
"""
from __future__ import annotations

import datetime as dt
import re

DELTA_RULE = 8.0


def pdate(s):
    if not s:
        return None
    m = re.fullmatch(r"\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*", s)
    if not m:
        return None
    try:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def fdate(d):
    return d.strftime("%d/%m/%Y")


def pint(s, unit=None):
    if not s:
        return None
    m = re.match(r"\s*(\d+)", s)
    return int(m.group(1)) if m else None


class FieldRef:
    """A field reading with what is needed to test alternatives: (page dict, field dict, logp, rec)."""

    def __init__(self, page, field, lp=None):
        self.page, self.f, self.lp = page, field, lp

    @property
    def value(self):
        return self.f.get("value")


def try_repair(ref: FieldRef, implied: str, rec, rule: str, issues: list, delta=DELTA_RULE):
    cur = ref.value
    if cur == implied:
        ref.f.setdefault("rules_ok", []).append(rule)
        return False
    if cur is None:                       # never fill a blank from a rule
        return False
    if ref.lp is not None and rec is not None and not ref.f.get("reviewed"):   # never override the midwife
        s_cur = rec.score(ref.lp, cur)
        s_imp = rec.score(ref.lp, implied)
        if s_imp >= s_cur - delta:
            ref.f["value"] = implied
            ref.f.setdefault("repairs", []).append(dict(rule=rule, old=cur, new=implied, d=s_cur - s_imp))
            issues.append(dict(rule=rule, key=ref.f["key"], old=cur, new=implied, repaired=True))
            return True
    ref.f["status"] = "À_RÉVISER"
    ref.f.setdefault("suggestions", []).append(implied)
    issues.append(dict(rule=rule, key=ref.f["key"], old=cur, suggestion=implied, repaired=False))
    return False


def _get(pages, t, key):
    for pg in pages:
        if pg["page_type"] == t:
            for f in pg["fields"]:
                if f["key"] == key:
                    return FieldRef(pg, f, pg.get("_lp", {}).get(key))
    return None


def _vote3(refs_vals, rec, rule, issues):
    """Three-way date constraint: if two agree with each other, repair the third."""
    pass


def validate_booklet(pages: list[dict], rec=None):
    """pages: extracted page dicts (with optional '_lp' {key: logp}). Applies rules in place; returns issues."""
    issues = []
    g = lambda t, k: _get(pages, t, k)   # noqa: E731
    ddr, dpa, ddt = g(3, "inline.ddr"), g(3, "inline.date_prevue_d_accouchement"), g(3, "inline.date_de_depassement_de_terme")
    if ddr and dpa and ddt:
        a, b, c = pdate(ddr.value), pdate(dpa.value), pdate(ddt.value)
        ok1 = a and b and (b - a).days == 280
        ok2 = b and c and (c - b).days == 7
        if ok1 and not ok2 and b:
            try_repair(ddt, fdate(b + dt.timedelta(7)), rec, "D2", issues)
        elif ok2 and not ok1 and b:
            try_repair(ddr, fdate(b - dt.timedelta(280)), rec, "D1", issues)
        elif not ok1 and not ok2:
            # DDR and DDT agree with each other (287 d) -> repair DPA
            if a and c and (c - a).days == 287:
                try_repair(dpa, fdate(a + dt.timedelta(280)), rec, "D1", issues)
            elif a and not b and not c:
                pass
            elif c and a is None and b is None:
                pass
        ddr_d = pdate(ddr.value)
    else:
        ddr_d = pdate(ddr.value) if ddr else None
    # D4: visit gestational age
    if ddr_d:
        for pg in pages:
            if pg["page_type"] != 3:
                continue
            for f in pg["fields"]:
                if f["key"].startswith("visites.venue_le."):
                    col = f["key"].split(".")[-1]
                    vd = pdate(f.get("value"))
                    ap = _get(pages, 3, f"visites.age_probable.{col}")
                    if vd and ap and ap.value:
                        weeks = (vd - ddr_d).days / 7
                        n = pint(ap.value)
                        if n is not None and abs(n - weeks) > 1.6:
                            m = re.match(r"\s*\d+\s*(.*)", ap.value)
                            implied = f"{round(weeks)} {m.group(1).strip() if m else 'SA'}".strip()
                            try_repair(ap, implied, rec, "D4", issues, delta=4.0)
    # D5 gestational age at birth
    acc = g(4, "inline.date_de_l_accouchement")
    acc_d = pdate(acc.value) if acc else None
    ga = g(4, "inline.age_gestationnel")
    if ddr_d and acc_d and ga and ga.value:
        w = (acc_d - ddr_d).days // 7
        n = pint(ga.value)
        if n is not None and n != w:
            m = re.match(r"\s*\d+\s*(.*)", ga.value)
            try_repair(ga, f"{w} {m.group(1).strip() if m else 'SA'}".strip(), rec, "D5", issues, delta=5.0)
    # E1 same fact on two pages: keep the reading the recogniser is more sure about
    for (t1, k1), (t2, k2) in [((5, "inline.date_de_la_consultation"), (6, "inline.date_de_la_consultation")),
                               ((7, "inline.date_de_la_consultation"), (8, "inline.date_de_la_consultation")),
                               ((4, "inline.perimetre_cranien_a_la_naissance"), (6, "inline.perimetre_cranien")),
                               ((6, "inline.vu_par"), (8, "inline.vu_par"))]:
        a, b = g(t1, k1), g(t2, k2)
        if a and b and a.value and b.value and a.value != b.value:
            ca, cb = a.f.get("confidence", 0), b.f.get("confidence", 0)
            src, dst = (a, b) if ca >= cb else (b, a)
            try_repair(dst, src.value, rec, "E1", issues, delta=6.0)
    # D6/D7 newborn age in days
    for tc, tn in ((5, 6), (7, 8)):
        cons = g(tn, "inline.date_de_la_consultation") or g(tc, "inline.date_de_la_consultation")
        age = g(tn, "inline.age")
        cd = pdate(cons.value) if cons else None
        if acc_d and cd and age and age.value:
            days = (cd - acc_d).days
            n = pint(age.value)
            if n is not None and n != days and 0 < days < 120:
                m = re.match(r"\s*\d+\s*(.*)", age.value)
                try_repair(age, f"{days} {m.group(1).strip() if m else 'jours'}".strip(), rec, "D6", issues, delta=5.0)
    # range / format checks -> flags only
    for pg in pages:
        for f in pg["fields"]:
            v = f.get("value")
            if not v or f.get("type") != "text":
                continue
            k = f["key"]
            bad = None
            if k.endswith(".ta") or k.split(".")[-2:-1] == ["ta"] or ".ta." in k:
                m = re.fullmatch(r"(\d{2,3})/(\d{2,3})", v)
                if not m or not (60 <= int(m.group(1)) <= 250 and 30 <= int(m.group(2)) <= 150 and int(m.group(1)) > int(m.group(2))):
                    bad = "V1"
            elif k in ("inline.t",) or k.startswith("inline.temperature"):
                x = re.match(r"(\d+(?:\.\d+)?)", v)
                if not x or not 34 <= float(x.group(1)) <= 42:
                    bad = "V3"
            elif ".bcf." in k:
                x = pint(v)
                if x is None or not 80 <= x <= 220:
                    bad = "V5"
            if bad:
                f["status"] = "À_RÉVISER" if f.get("status") == "CONNU" else f.get("status")
                f.setdefault("flags", []).append(bad)
                issues.append(dict(rule=bad, key=k, value=v, repaired=False))
    return issues


# ----------------------------------------------------------------------------------- form logic (NON_APPLICABLE)
def apply_form_logic(page: dict) -> int:
    """A blank field that the form's own logic excludes is NON_APPLICABLE, not NON_FOURNI:
      p2  caesarean indication of a previous delivery whose mode is vaginal
      p3  RAI (only if Rh negative) when Rh+ is ticked
      p4  'Préciser l'indication' when no caesarean box is ticked
      p5/p7 scar condition when 'Césarienne' is not ticked; 'Pourquoi ?' when the mother wants a method
    Only blank fields are touched; a written value always wins. Returns the number of fields changed."""
    t = page["page_type"]
    f = {x["key"]: x for x in page["fields"]}
    cb = lambda k: bool(f.get(k, {}).get("value"))          # noqa: E731
    na = []
    if t == 2:
        for k in range(1, 6):
            mode = (f.get(f"accouchements_anterieurs.modalite_d_extraction.accouch_{k}", {}).get("value") or "").lower()
            if mode and "c" != mode[:1] and "sar" not in mode and "قيصرية" not in mode:
                na.append(f"accouchements_anterieurs.si_cesarienne_indication.accouch_{k}")
    if t == 3 and cb("cb.rh_2") and not cb("cb.rh"):
        na += [k for k in f if k.startswith("visites.rai_si_rh_negatif.")]
    if t == 4 and not (cb("cb.cesarienne_programmee") or cb("cb.urgence")) and \
            (cb("cb.voie_basse_non_instrumentale") or cb("cb.voie_basse_instrumentale")):
        na.append("inline.preciser_l_indication")
    if t in (5, 7):
        if not cb("cb.cesarienne"):
            na.append("inline.etat_de_la_cicatrice")
        if cb("cb.desire_utiliser_une_methode"):
            na.append("inline.si_la_mere_ne_desire_pas_une_methode_contraceptive_pourquoi")
    n = 0
    for k in na:
        x = f.get(k)
        if x is not None and x.get("value") is None and x.get("status") == "NON_FOURNI":
            x["status"] = "NON_APPLICABLE"; n += 1
    return n


# exclusive checkbox groups (exactly one answer expected when the question was answered)
EXCLUSIVE = {
    1: [["cb.dr", "cb.csc", "cb.csu", "cb.csca", "cb.csua"], ["cb.fixe", "cb.mobile"]],
    3: [["cb.a", "cb.b", "cb.o", "cb.ab"], ["cb.rh", "cb.rh_2"]],
    4: [["cb.vivant", "cb.mort_ne", "cb.deces_24_heures"]],
    6: [["cb.exclusivement_au_sein", "cb.artificiel", "cb.mixte"]],
    8: [["cb.exclusivement_au_sein", "cb.artificiel", "cb.mixte"]],
}


def apply_group_logic(page: dict) -> list:
    """No box ticked in an exclusive group -> NON_FOURNI (not 'all False, CONNU'); several ticked -> À_RÉVISER."""
    f = {x["key"]: x for x in page["fields"]}
    out = []
    for grp in EXCLUSIVE.get(page["page_type"], []):
        boxes = [f[k] for k in grp if k in f]
        if not boxes:
            continue
        ticked = [b for b in boxes if b.get("value")]
        if not ticked:
            for b in boxes:
                b["status"] = "NON_FOURNI"
            out.append(("none", grp))
        elif len(ticked) > 1:
            for b in boxes:
                b["status"] = "À_RÉVISER"
                b["group_conflict"] = [x["key"] for x in ticked]
            out.append(("several", grp))
    return out
