from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"


def read(relative: str) -> str:
    return (APP / relative).read_text(encoding="utf-8")


def test_static_assets_exist_and_have_no_remote_dependencies() -> None:
    html = read("index.html")
    assert (APP / "assets/app.css").is_file()
    assert (APP / "assets/app.js").is_file()
    assert (APP / "nova-data.js").is_file()
    assert not re.search(r'''(?:src|href)=["']https?://''', html, re.I)
    assert "fetch(" not in read("assets/app.js")


def test_all_required_views_are_navigable() -> None:
    html = read("index.html")
    required = {
        "brief", "questions", "timeline", "decisions", "contradictions",
        "actions", "risks", "sources", "limits", "versions",
    }
    assert required == set(re.findall(r'data-route="([a-z]+)"', html))
    js = read("assets/app.js")
    for route in required:
        assert f'"{route}"' in js


def test_accessibility_landmarks_and_keyboard_support() -> None:
    html = read("index.html")
    css = read("assets/app.css")
    assert 'lang="fr"' in html
    assert 'class="skip-link"' in html
    assert '<main id="contenu" tabindex="-1">' in html
    assert 'aria-label="Sections de la mémoire"' in html
    assert 'role="search"' in html
    assert 'aria-live="polite"' in html
    assert ":focus-visible" in css
    assert "@media (max-width: 800px)" in css


def test_print_styles_target_a_compact_one_page_brief() -> None:
    css = read("assets/app.css")
    html = read("index.html")
    assert "@page" in css and "size: A4 portrait" in css
    assert "@media print" in css
    assert 'body[data-view="brief"] .brief-grid' in css
    assert "data-print" in read("assets/app.js")
    assert "Imprimer le brief" in read("assets/app.js")
    assert 'data-view="brief"' in html


def test_search_is_local_deterministic_and_abstains() -> None:
    js = read("assets/app.js")
    assert "window.NOVA_DATA" in js
    assert "function search(query)" in js
    assert "localeCompare" in js
    assert "Non documenté dans le corpus" in js
    assert "aucune donnée n’est envoyée" in read("index.html")
    assert 'var stop = ["a", "au", "aux"' in js


def test_evidence_links_use_expected_contract_and_reject_network_urls() -> None:
    js = read("assets/app.js")
    docs = (ROOT / "docs/UI.md").read_text(encoding="utf-8")
    assert "evidenceHref" in js
    assert "evidenceHref" in docs
    assert "safeHref" in js
    assert "[a-z][a-z0-9+.-]*:" in js
    assert "evidence_path" in js


def test_fact_ledger_can_feed_timeline_and_state_views() -> None:
    js = read("assets/app.js")
    assert "data.timeline || data.events || data.facts" in js
    for fact_type in ("proposal", "decision", "delivery", "validation", "contradiction", "risk"):
        assert f'"{fact_type}"' in js


def test_contradictions_render_both_claims_and_resolution() -> None:
    js = read("assets/app.js")
    assert "function renderContradictions()" in js
    assert "Affirmation A" in js
    assert "Affirmation B" in js
    assert "Résolution" in js


def test_empty_data_file_contains_no_project_claims() -> None:
    empty_data = read("nova-data.js")
    assert "window.NOVA_DATA = window.NOVA_DATA || {};" in empty_data
    assert "$" not in empty_data
    assert not re.search(r"\b20\d{2}-\d{2}-\d{2}\b", empty_data)
