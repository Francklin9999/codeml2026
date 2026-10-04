import sys
from pathlib import Path

import pytest

RIG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RIG))

import make_board  # noqa: E402


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Run the generator once into a temporary folder (never touches rig/out or app/public)."""
    out = tmp_path_factory.mktemp("board")
    app = out / "app_board_spec.json"
    assert make_board.main(["--fixtures", "--out", str(out), "--app-spec", str(app)]) == 0
    return out, app
