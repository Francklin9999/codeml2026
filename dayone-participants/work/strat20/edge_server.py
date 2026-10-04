"""Strategy 20: on-site edge processing box (local Wi-Fi, no internet) + central-sync stub.

Serves the phone app (strategy 15, WhatsApp-style chat) and exposes:
  POST /process               photo + idempotency key + session id -> extraction (statuses, confidences,
                              evidence crops of uncertain fields; identifiers masked before reading)
  POST /session/{sid}/finalize booklet-level consistency rules over the session's pages (strategy 7/13)
  POST /match/propose          code + non-identifying facts -> candidate patients (strategy 10)
  POST /match/decide           midwife's button -> patient id (never auto-created when a match is plausible)
  POST /records                idempotent upsert of a validated record (stands for the central server)
  GET  /records/stats          what the central store holds (demo / tests)
  GET  /health
Retries are safe: every POST is idempotent on its key. Data never leaves the facility.

uvicorn edge_server:app --host 0.0.0.0 --port 8765   (env DAYONE_CRNN, DAYONE_OMR, DAYONE_CAL, DAYONE_STATE)
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import threading
import uuid
from pathlib import Path

import cv2
import numpy as np
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile

W = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(W / s) for s in ("shared", "strat2", "strat5", "strat6", "strat7", "strat8", "strat10", "strat11", "strat18")]

app = FastAPI(title="DayOne edge box")
_APP_DIR = W / "strat15" / "app"         # the phone PWA (strategy 15) is served by the box on the local Wi-Fi
from common import MODELS  # noqa: E402  (repo models/ by default)
STATE = Path(os.environ.get("DAYONE_STATE", Path.home() / "dayone_local" / "edge_state"))
_lock = threading.Lock()
_cache: dict[str, dict] = {}
_sessions: dict[str, list] = {}
_proposals: dict[str, dict] = {}
_ext = None
_registry = None
PAGE_NAMES = {1: "Fiche de surveillance", 2: "Identification et antécédents", 3: "Grossesse actuelle",
              4: "Accouchement", 5: "Post-partum précoce · mère", 6: "Post-partum précoce · nouveau-né",
              7: "Post-partum tardif · mère", 8: "Post-partum tardif · nouveau-né"}


def extractor():
    global _ext
    if _ext is None:
        from calibrate import Calibrator
        from extract_zonal import Extractor
        from omr import OMR
        from recognizer import Recognizer
        rec = Recognizer(os.environ.get("DAYONE_CRNN", str(MODELS / "crnn_final.pt")))
        omr_p = os.environ.get("DAYONE_OMR", str(MODELS / "omr_v2.pt"))
        cal_p = os.environ.get("DAYONE_CAL", str(MODELS / "calibrator.joblib"))
        _ext = Extractor(rec, OMR(omr_p) if Path(omr_p).exists() else None,
                         Calibrator.load(cal_p) if Path(cal_p).exists() else None)
    return _ext


class Vault:
    """Encrypted-at-rest JSON documents for the box state (AES-GCM, key from DAYONE_BOX_KEY via scrypt)."""

    def __init__(self, root: Path):
        from offline import Crypto
        root.mkdir(parents=True, exist_ok=True)
        salt_f = root / "salt.bin"
        if not salt_f.exists():
            salt_f.write_bytes(os.urandom(16))
        self.root = root
        self.c = Crypto(os.environ.get("DAYONE_BOX_KEY", "demo-box-key-change-me"), salt_f.read_bytes())

    def load(self, name, default):
        f = self.root / f"{name}.bin"
        return json.loads(self.c.dec(f.read_bytes(), name)) if f.exists() else default

    def save(self, name, obj):
        tmp = self.root / f"{name}.tmp"
        tmp.write_bytes(self.c.enc(json.dumps(obj, ensure_ascii=False).encode(), name))
        os.replace(tmp, self.root / f"{name}.bin")        # atomic: a crash never leaves a half-written file


_vault = None


def vault():
    global _vault, _cache, _sessions
    if _vault is None:
        _vault = Vault(STATE)
        _cache.update(_vault.load("cache", {}))
        for sid, items in _vault.load("sessions", {}).items():
            _sessions.setdefault(sid, []).extend(dict(it, lp={}) for it in items)
    return _vault


def _persist_sessions():
    vault().save("cache", _cache)
    vault().save("sessions", {sid: [dict(key=it["key"], page=it["page"]) for it in items] for sid, items in _sessions.items()})


def registry():
    """Patient registry of the facility: random internal ids, registry code + non-identifying facts only."""
    global _registry
    if _registry is None:
        from privacy_linking import Registry
        _registry = Registry()
        _registry.patients = vault().load("registry", {})
    return _registry


def _save_registry():
    vault().save("registry", registry().patients)


def _crop_b64(warped, t, key, pad=(14, 10, 30, 10)):
    from crops import TEMPLATES, zone_box
    z = TEMPLATES[str(t)]["zones"][key]
    if z["type"] == "checkbox":
        x0, y0, x1, y1 = [int(v) for v in z["zone_px"]]
        box = (x0 - 60, y0 - 20, x1 + 300, y1 + 20)
    else:
        box = zone_box(t, key, pad)
    x0, y0, x1, y1 = max(0, box[0]), max(0, box[1]), box[2], box[3]
    c = warped[y0:y1, x0:x1]
    if c.size == 0:
        return None
    sc = min(1.0, 90 / c.shape[0])
    c = cv2.resize(c, (max(8, int(c.shape[1] * sc)), max(8, int(c.shape[0] * sc))), interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(c, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 80])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


def masked_original(photo_bgr, page):
    """Original photo with every identifier zone (name, husband, CIN, phone, address) painted over, using the
    inverse registration homography. This is the image kept in the record; the raw photo is discarded."""
    from crops import TEMPLATES, zone_box
    from extract_zonal import is_identifier
    t = page["page_type"]
    Hinv = np.linalg.inv(np.array(page["registration"]["H"], dtype=np.float64))
    out = photo_bgr.copy()
    for key, z in TEMPLATES[str(t)]["zones"].items():
        if z["type"] == "text" and is_identifier(key):
            x0, y0, x1, y1 = zone_box(t, key, (4, 6, 40, 6))
            pts = cv2.perspectiveTransform(np.float32([[[x0, y0], [x1, y0], [x1, y1], [x0, y1]]]), Hinv)[0]
            cv2.fillPoly(out, [pts.astype(np.int32)], (90, 90, 90))
    # printed header line "MÈRE — <name>" on postpartum pages is an identifier too
    if t in (5, 7):
        pts = cv2.perspectiveTransform(np.float32([[[195, 118], [780, 118], [780, 170], [195, 170]]]), Hinv)[0]
        cv2.fillPoly(out, [pts.astype(np.int32)], (90, 90, 90))
    ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode()


@app.get("/health")
def health():
    return dict(ok=True, models=dict(crnn=os.environ.get("DAYONE_CRNN", "crnn_final.pt")))


@app.post("/process")
async def process(image: UploadFile = File(...), idempotency_key: str = Form(...), midwife_id: str = Form(...),
                  session_id: str = Form("default")):
    data = await image.read()
    vault()
    if idempotency_key in _cache:
        return _cache[idempotency_key]
    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if arr is None:
        raise HTTPException(422, "image illisible")
    from extract_zonal import RULE_KEYS
    from privacy_linking import leak_guard
    with _lock:                                    # one GPU job at a time
        ext = extractor()
        page = ext.extract(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))
        warped = ext.last_warped
        lps = {k: [x.half() for x in v] for k, v in ext.last_lp.items() if RULE_KEYS.search(k)}
    t = page["page_type"]
    for f in page["fields"]:
        f.pop("feats", None)
        if f.get("status") in ("À_RÉVISER", "ILLISIBLE") or (f["type"] == "checkbox" and f.get("status") != "CONNU"):
            f["evidence"] = _crop_b64(warped, t, f["key"])
    incidents = leak_guard(page)
    page["page_name"] = PAGE_NAMES.get(t, str(t))
    masked = masked_original(arr, page) if page.get("page_status") != "PAGE_NON_RECONNUE" else None
    res = dict(page=page, image_sha256=hashlib.sha256(data).hexdigest(), midwife_id=midwife_id,
               state="TRAITÉ_IA", leak_incidents=len(incidents), masked_image=masked)
    _cache[idempotency_key] = res
    _sessions.setdefault(session_id, []).append(dict(key=idempotency_key, page=page, lp=lps))
    _persist_sessions()
    return res


@app.post("/session/{sid}/finalize")
def finalize(sid: str, body: dict = Body(default={})):
    """Booklet-level rules across the pages of one session (dates, ages, same fact on two pages), applied to
    the pages as reviewed by the midwife (body.pages: {idempotency_key: page}); values she confirmed are
    never changed silently, only flagged with a suggestion."""
    from validator import validate_booklet
    lps = {it["key"]: it["lp"] for it in _sessions.get(sid, [])}
    pages = body.get("pages") or {it["key"]: it["page"] for it in _sessions.get(sid, [])}
    for k, p in pages.items():
        p["_lp"] = lps.get(k, {})
    with _lock:
        issues = validate_booklet(list(pages.values()), extractor().rec)
    for p in pages.values():
        p.pop("_lp", None)
    return dict(issues=issues, pages=pages)


@app.post("/match/propose")
def match_propose(body: dict = Body(...)):
    reg = registry()
    prop = reg.propose(body.get("code", ""), body.get("facts", {}))
    pid = uuid.uuid4().hex
    _proposals.update(vault().load("proposals", {}))
    _proposals[pid] = dict(prop, code=body.get("code", ""), facts=body.get("facts", {}))
    vault().save("proposals", _proposals)                 # a box restart never strands a pending decision
    view = [dict(rank=i + 1, code=c["code"], dist=round(c["dist"], 2), agree=c["agree"], clash=c["clash"],
                 facts={k: reg.patients[c["pid"]]["facts"].get(k) for k in ("ddr", "date_prevue")})
            for i, c in enumerate(prop["candidates"])]
    return dict(proposal_id=pid, kind=prop["kind"], candidates=view, buttons=prop["buttons"])


@app.post("/match/decide")
def match_decide(body: dict = Body(...)):
    prop = _proposals.get(body["proposal_id"]) or vault().load("proposals", {}).get(body["proposal_id"])
    if prop is None:
        raise HTTPException(404, "proposition inconnue")
    pid, state = registry().decide(prop, body["choice"], prop["code"], prop["facts"])
    _save_registry()
    return dict(patient_id=pid, state=state)


@app.post("/records")
def upsert_record(body: dict = Body(...)):
    """Central store stub: idempotent on record_id:version; refuses identifier values (defence in depth)."""
    from privacy_linking import leak_guard
    key = f"{body['record_id']}:{body.get('version', 0)}"
    central = vault().load("central", [])
    if any(r["key"] == key for r in central):
        return dict(ok=True, duplicate=True)
    leaks = sum(len(leak_guard(p)) for p in body.get("pages", []))
    central.append(dict(key=key, record_id=body["record_id"], patient_id=body.get("patient_id"),
                        pages=body.get("pages", []), leaks_removed=leaks))
    vault().save("central", central)
    return dict(ok=True, duplicate=False, leaks_removed=leaks)


@app.get("/records/stats")
def record_stats():
    rows = vault().load("central", [])
    return dict(records=len(rows), unique_records=len({r["record_id"] for r in rows}),
                patients=len(registry().patients))


@app.get("/records/previous")
def previous_record(patient_id: str, page_type: int, exclude: str = ""):
    """Strategy 13: last validated version of this page for this patient (re-digitisation diff)."""
    rows = [r for r in vault().load("central", []) if r["patient_id"] == patient_id and r["record_id"] != exclude
            and any(p.get("page_type") == page_type for p in r["pages"])]
    if not rows:
        return dict(found=False)
    page = next(p for p in rows[-1]["pages"] if p.get("page_type") == page_type)
    return dict(found=True, record_id=rows[-1]["record_id"], page=page)


@app.get("/dashboard")
def dashboard():
    """Strategy 19: anonymised aggregates from the synced records (k=5 suppression, missing counts shown)."""
    from fastapi.responses import HTMLResponse
    sys.path.insert(0, str(W / "strat19"))
    from dashboard import by_age, html, indicators, indicators_from_records, load
    rows = vault().load("central", [])
    rec = indicators_from_records(rows)
    page = html(indicators(load()), by_age(load()))
    page = page.replace("<h1>", f"<h2>Dossiers numérisés ({len(rows)} pages synchronisées)</h2>{rec.to_html(index=False)}<h1>", 1)
    return HTMLResponse(page)


@app.post("/admin/seed")
def seed(body: dict = Body(...)):
    """Demo helper: pre-register patients (code + facts) as if they had been seen at earlier visits."""
    reg = registry()
    for p in body.get("patients", []):
        reg.create(p["code"], p.get("facts", {}))
    _save_registry()
    return dict(patients=len(reg.patients))


if _APP_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_APP_DIR), html=True), name="pwa")
