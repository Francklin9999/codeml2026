"""Edge box API test with a stub extractor (the real model is exercised in run_eval)."""
import sys
from pathlib import Path

import cv2
import numpy as np
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent))
import edge_server  # noqa: E402


class Stub:
    calls = 0
    last_lp = {}

    def extract(self, rgb):
        import numpy as np
        Stub.calls += 1
        self.last_warped = np.full((2339, 1654, 3), 200, np.uint8)
        return dict(page_type=3, page_status="PAGE_NON_RECONNUE", registration=dict(score=0.1, H=np.eye(3).tolist()),
                    fields=[dict(key="inline.ddr", type="text", value="26/04/2025", status="CONNU", feats={}),
                            dict(key="inline.cin", type="text", value="CB609814", status="CONNU")])


def test_process_idempotent_and_leak_guard(tmp_path, monkeypatch):
    monkeypatch.setattr(edge_server, "STATE", tmp_path)
    edge_server._vault = None
    edge_server._ext = Stub()
    c = TestClient(edge_server.app)
    img = cv2.imencode(".jpg", np.full((100, 70, 3), 200, np.uint8))[1].tobytes()
    r1 = c.post("/process", files={"image": ("p.jpg", img, "image/jpeg")}, data={"idempotency_key": "rec1:1", "midwife_id": "sf-01"})
    assert r1.status_code == 200
    body = r1.json()
    assert body["state"] == "TRAITÉ_IA" and body["leak_incidents"] == 1
    assert [f for f in body["page"]["fields"] if f["key"] == "inline.cin"][0]["value"] is None
    r2 = c.post("/process", files={"image": ("p.jpg", img, "image/jpeg")}, data={"idempotency_key": "rec1:1", "midwife_id": "sf-01"})
    assert r2.json() == body and Stub.calls == 1          # retry served from cache, processed once
    bad = c.post("/process", files={"image": ("p.jpg", b"nope", "image/jpeg")}, data={"idempotency_key": "x", "midwife_id": "sf"})
    assert bad.status_code == 422


def test_match_and_records_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(edge_server, "STATE", tmp_path)
    edge_server._vault = None; edge_server._registry = None
    c = TestClient(edge_server.app)
    c.post("/admin/seed", json={"patients": [{"code": "2026-823-001", "facts": {"ddr": "26/04/2025"}}]})
    p = c.post("/match/propose", json={"code": "2026-823-007", "facts": {"ddr": "26/04/2025"}}).json()
    assert p["candidates"] and "Aucune, créer" in p["buttons"] and "Je ne sais pas" in p["buttons"]
    d = c.post("/match/decide", json={"proposal_id": p["proposal_id"], "choice": "Patiente 1"}).json()
    assert d["state"] == "PATIENTE_LIÉE" and d["patient_id"]
    body = {"record_id": "r1", "version": 1, "patient_id": d["patient_id"],
            "pages": [{"page_type": 3, "fields": [{"key": "inline.ddr", "value": "26/04/2025"}, {"key": "inline.cin", "value": "CB609814"}]}]}
    a, b = c.post("/records", json=body).json(), c.post("/records", json=body).json()
    assert a["duplicate"] is False and a["leaks_removed"] == 1 and b["duplicate"] is True
    assert c.get("/records/stats").json()["unique_records"] == 1
    prev = c.get(f"/records/previous?patient_id={d['patient_id']}&page_type=3&exclude=other").json()
    assert prev["found"] and prev["page"]["fields"][1]["value"] is None          # identifier never stored
    raw = b"".join(f.read_bytes() for f in tmp_path.glob("*.bin"))
    assert b"26/04/2025" not in raw and b"2026-823" not in raw                    # box state encrypted at rest
