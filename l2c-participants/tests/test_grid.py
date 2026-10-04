"""Elements located by their place on the building grid (made-up project, no confidential data)."""

import pytest

from l2c_rebar.config import Config
from l2c_rebar.evaluate import axes_of_plan, load_known, score_run, summarize_scores
from l2c_rebar.extract.document import read_document
from l2c_rebar.extract.grid import GridAxes, link_tags, placement_modes
from l2c_rebar.models import NON_CONFORME
from l2c_rebar.parsing.elements import find_grid_refs, find_labels
from l2c_rebar.parsing.rebar import find_bars
from l2c_rebar.pipeline import discover, run_project
from l2c_rebar.synthetic import GRID_PLANTED, build_grid_project, write_known_list


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    return build_grid_project(tmp_path_factory.mktemp("grid"))


@pytest.fixture(scope="module")
def run(project, tmp_path_factory):
    return run_project(project, tmp_path_factory.mktemp("out"), Config(ocr="off"))


def test_grid_references_as_written_on_shop_drawings():
    assert [l.label for l in find_grid_refs("COL. B-12, B-13")] == ["B-12", "B-13"]
    assert [l.label for l in find_grid_refs("B/3")] == ["B-3"]
    assert [l.label for l in find_grid_refs("C.1-12")] == ["C.1-12"]
    assert find_grid_refs("25MPa / C-1") == [] and find_grid_refs("1/2") == [] and find_grid_refs("c/c") == []
    assert [l.label for l in find_labels("COL. B-2", "colonne", grid_refs=True)] == ["B-2"]


def test_shop_quantity_forms():
    two_sets = find_bars("2x4 25M 25A301")[0]
    assert (two_sets.quantite, two_sets.repere) == (8, "25A301")
    numbered = find_bars("V: 8 25M 360")[0]
    assert (numbered.quantite, numbered.longueur_mm, numbered.repere) == (8, None, "360")
    assert find_bars("8 25M 3600")[0].longueur_mm == 3600


def test_grid_is_read_from_its_bubbles(project):
    pages, _ = read_document(discover(project).plans[0], "plan", Config(ocr="off"), None)
    axes = pages[0].axes
    assert [label for label, _ in sorted(axes.vertical, key=lambda it: it[1])] == ["1", "2", "3", "4"]
    assert [label for label, _ in sorted(axes.horizontal, key=lambda it: it[1])] == ["A", "B", "C"]
    assert not axes.letters_are_vertical
    assert len(pages[0].marks) == 12


def test_a_point_off_the_grid_has_no_name():
    axes = GridAxes(vertical=[("1", 100.0), ("2", 300.0)], horizontal=[("A", 100.0), ("B", 300.0)])
    assert axes.name(104.0, 296.0)[0] == "B-1"
    assert axes.name(200.0, 100.0) is None


def test_tags_follow_their_usual_place_beside_the_column():
    centres = [100 + 200 * i for i in range(6)]
    marks = [(x - 6, 91, x + 6, 109) for x in centres]
    tags = [(x - 85, 95, x - 55, 115) for x in centres]  # each tag left of its column
    tags[3] = (centres[3] + 100, 95, centres[3] + 130, 115)  # one had to go on the right, nearer the next column
    assert len(placement_modes(tags, marks)) == 1  # one usual place: 70 pt to the left
    assert link_tags(tags, marks) == [0, 1, 2, 3, 4, 5]


def test_plan_columns_are_named_by_their_grid_crossing(run):
    named = {(e.feuillet, e.label): e for e in run.plan_elements if e.label}
    assert len(named) == 24  # 12 columns on each of the two storeys
    assert [b.describe() for b in named[("S-501", "B-2")].bars] == ["12-25M", "10M @ 300"]
    assert named[("S-502", "C-1")].bars[0].describe() == "6-20M"
    assert named[("S-501", "A-1")].levels == ("RDC",)


def test_only_the_planted_discrepancies_are_reported(run):
    found = {(r.feuillet, r.plan.label, e.attribut) for r in run.results if r.statut == NON_CONFORME for e in r.ecarts}
    assert found == {(p["feuillet"], p["lieu"], p["attribut"]) for p in GRID_PLANTED}


def test_a_detail_shared_by_two_columns_counts_for_both(run):
    shared = [r for r in run.results if r.plan and r.plan.label in ("A-2", "A-3") and r.feuillet == "S-501"]
    assert len(shared) == 2 and all(r.statut == "conforme" for r in shared)
    assert all(r.atelier.multiplicity == 2 for r in shared)


def test_score_against_a_list_of_known_non_conformities(run, project, tmp_path):
    known = load_known(write_known_list(tmp_path / "known.xlsx", GRID_PLANTED))
    pages, _ = read_document(discover(project).plans[0], "plan", Config(ocr="off"), None)
    scores = score_run(known, run.plan_elements, run.results, axes_of_plan(pages))
    assert summarize_scores(scores) == {"connues": 3, "feuillet_lu": 3, "valeur_plan_extraite": 3,
                                        "valeur_plan_au_bon_endroit": 3, "signalees": 3, "memes_valeurs": 3}


def test_evaluate_command_prints_the_score_and_nothing_from_the_list(project, tmp_path, capsys):
    from l2c_rebar.cli import main

    known = write_known_list(tmp_path / "known.xlsx", GRID_PLANTED)
    assert main(["evaluate", str(project), str(known), "--out", str(tmp_path / "out"), "--ocr", "off"]) == 0
    printed = capsys.readouterr().out
    assert "connues : 3" in printed and "avec les mêmes valeurs : 3" in printed
    assert printed.count("trouvée, mêmes valeurs") == 3
    assert "8-25M" not in printed and "C-3" not in printed  # stage flags only, no content of the list
