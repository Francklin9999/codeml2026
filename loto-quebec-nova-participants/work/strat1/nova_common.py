"""Shared helpers for the strat1 scripts (extract.py, check.py, build.py).

Importable from anywhere:  sys.path.insert(0, ".../work/strat1"); import nova_common
"""
import json
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent            # .../loto-quebec-nova-participants/work/strat1
ROOT = HERE.parents[1]                            # .../loto-quebec-nova-participants
ZIP_PATH = ROOT / "NOVA_ETUDIANTS.zip"
LOCAL = ROOT / "work" / "_local"                  # git-ignored, regenerable
CORPUS = LOCAL / "corpus"
TEXT = LOCAL / "text"
ATTACH = LOCAL / "attachments"
IMAGES = LOCAL / "images"
LOCATORS = LOCAL / "locators.jsonl"
FILES_INDEX = LOCAL / "files_index.json"
TRANSCRIPTIONS = HERE / "transcriptions"
FACTS = HERE / "facts.yaml"
EXPORT = LOCAL / "strat1" / "export"

TOP_DIR = "Projet360_NOVA_ETUDIANTS/"             # prefix inside the zip, stripped on extraction


def norm(s: str) -> str:
    """Normalisation used by every integrity check: NFC, NBSP->space, curly->straight quotes,
    '**' markdown removed, whitespace collapsed. Case and accents are kept (verbatim check)."""
    s = unicodedata.normalize("NFC", s)
    s = s.replace(" ", " ").replace(" ", " ")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("**", "")
    return re.sub(r"\s+", " ", s).strip()


def text_path(rel: str) -> Path:
    """source_file (path relative to the corpus root) -> extracted text file."""
    return TEXT / (rel + ".txt")


def load_locators() -> dict:
    """locators.jsonl -> {id: record}"""
    out = {}
    with open(LOCATORS, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                out[rec["id"]] = rec
    return out
