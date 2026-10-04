import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import set_print_scale as sps

RIG = Path(__file__).resolve().parents[1]


@pytest.fixture
def copies(built, tmp_path):
    a, b = tmp_path / "a" / "board_spec.json", tmp_path / "b" / "board_spec.json"
    for p in (a, b):
        p.parent.mkdir()
        shutil.copy(built[0] / "board_spec.json", p)
    return [a, b]


def test_99_writes_both_copies(copies):
    before = json.loads(copies[0].read_text())
    assert sps.set_scale(99.0, copies) == 0.99
    for p in copies:
        spec = json.loads(p.read_text())
        assert spec["printScale"] == 0.99
        assert {k: v for k, v in spec.items() if k != "printScale"} == {k: v for k, v in before.items() if k != "printScale"}


@pytest.mark.parametrize("bad", [90, 110, 96.9, 103.1])
def test_rejects_out_of_range_and_leaves_files(copies, bad):
    with pytest.raises(ValueError):
        sps.set_scale(bad, copies)
    assert all(json.loads(p.read_text())["printScale"] == 1 for p in copies)


@pytest.mark.parametrize("ok", [97, 103])
def test_limits_accepted(copies, ok):
    assert sps.set_scale(ok, copies) == ok / 100


def test_cli_prints_value_and_exit_codes(copies):
    run = lambda v: subprocess.run([sys.executable, str(RIG / "set_print_scale.py"), str(v), "--files", *map(str, copies)],
                                   capture_output=True, text=True)
    r = run("99.0")
    assert r.returncode == 0 and "0.99" in r.stdout
    assert run("90").returncode != 0 and run("110").returncode != 0
    assert json.loads(copies[1].read_text())["printScale"] == 0.99


def test_missing_copy_is_an_error(copies):
    copies[1].unlink()
    with pytest.raises(FileNotFoundError):
        sps.set_scale(99, copies)
    assert json.loads(copies[0].read_text())["printScale"] == 1
