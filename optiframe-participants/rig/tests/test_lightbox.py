from pathlib import Path

HTML = (Path(__file__).resolve().parents[2] / "app" / "public" / "lightbox.html").read_text(encoding="utf-8")


def test_lightbox_features_and_no_dependency():
    for needle in ["requestFullscreen", "wakeLock", "luminosité", "papier calque", "moiré"]:
        assert needle in HTML
    assert "src=" not in HTML and "http://" not in HTML and "https://" not in HTML
    assert "background: #fff" in HTML
