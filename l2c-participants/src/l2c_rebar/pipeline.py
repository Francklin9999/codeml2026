"""End-to-end run on one project folder: read, extract, compare, export."""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from .compare import Coverage, compare_project, summarize
from .config import Config
from .extract.document import (PageData, assign_ids, extract_pages, label_vocabulary, pages_needing_ocr,
                               read_document, types_sharing_labels)
from .models import CONFORME, SOURCE_PLAN, SOURCE_SHOP, STATUSES, Element, Result
from .parsing.elements import find_levels, type_from_text
from .pdf import ocr as ocr_mod

Progress = Callable[[str], None]


@dataclass
class ProjectFiles:
    name: str
    root: Path
    plans: list[Path]
    shops: list[Path]


@dataclass
class RunOutput:
    project: str
    out_dir: Path
    plan_elements: list[Element]
    shop_elements: list[Element]
    results: list[Result]
    coverage: Coverage
    stats: dict = field(default_factory=dict)
    files: dict[str, Path] = field(default_factory=dict)


def discover(project_dir: Path) -> ProjectFiles:
    """Plans are the PDFs at the project root; shop drawings are every PDF below it.

    Matches the layout handed out for the challenge:
        <PROJECT>/L2C_PLAN_STR_<PROJECT>.pdf
        <PROJECT>/DA/<type d'élément>/*.pdf
    """
    project_dir = Path(project_dir)
    if not project_dir.is_dir():
        raise FileNotFoundError(f"Project folder not found: {project_dir}")
    pdfs = sorted(project_dir.rglob("*.pdf"))
    root_pdfs = [p for p in pdfs if p.parent == project_dir]
    plans = [p for p in root_pdfs if "PLAN" in p.name.upper()] or root_pdfs
    shops = [p for p in pdfs if p not in plans]
    if not plans:
        raise FileNotFoundError(f"No plan PDF found at the root of {project_dir}")
    return ProjectFiles(project_dir.name, project_dir, plans, shops)


def shop_file_hints(path: Path, root: Path) -> tuple[str | None, tuple[str, ...]]:
    """Element type and storeys of a shop drawing, from its folder and file names."""
    folders = [p.name for p in path.relative_to(root).parents if p.name and p.name.upper() != "DA"]
    type_element = type_from_text(*folders) or type_from_text(path.stem)
    return type_element, find_levels(path.stem)


def run_project(project_dir: Path, out_dir: Path, cfg: Config | None = None, progress: Progress | None = None,
                plans: list[Path] | None = None, shops: list[Path] | None = None) -> RunOutput:
    cfg = cfg or Config()
    say = progress or (lambda _msg: None)
    t0 = time.time()
    files = discover(Path(project_dir)) if plans is None else ProjectFiles(Path(project_dir).name, Path(project_dir),
                                                                             plans, shops or [])
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = out_dir / ".ocr-cache"

    # 1. OCR what has no text layer (cached, parallel).
    ocr_tasks: list[tuple[Path, int]] = []
    if cfg.ocr != "off" and ocr_mod.ocr_available():
        for path, source in [(p, SOURCE_PLAN) for p in files.plans] + [(p, SOURCE_SHOP) for p in files.shops]:
            ocr_tasks += [(path, i) for i in pages_needing_ocr(path, cfg, source)]
        if ocr_tasks:
            say(f"OCR local : {len(ocr_tasks)} pages sans couche texte")
            ocr_mod.ocr_pages(ocr_tasks, cfg, cache_dir,
                              progress=lambda done, total: say(f"OCR {done}/{total}") if done % 5 == 0 else None)

    # 2. Read every page.
    say("Lecture des plans et des dessins d'atelier")
    plan_pages: list[PageData] = []
    shop_pages: list[PageData] = []
    page_stats: Counter = Counter()
    for path in files.plans:
        pages, st = read_document(path, SOURCE_PLAN, cfg, cache_dir)
        plan_pages += pages
        page_stats.update({"plan_pages": st.pages, "plan_pages_ocr": st.pages_ocr, "plan_pages_vides": st.pages_empty})
    for path in files.shops:
        type_hint, levels = shop_file_hints(path, files.root)
        pages, st = read_document(path, SOURCE_SHOP, cfg, cache_dir, type_hint, levels)
        shop_pages += pages
        page_stats.update({"atelier_pages": st.pages, "atelier_pages_ocr": st.pages_ocr,
                           "atelier_pages_vides": st.pages_empty})

    # 3. Labels written on both sides are element names, whatever their prefix.
    plan_vocab, shop_vocab = label_vocabulary(plan_pages), label_vocabulary(shop_pages)
    shared = {t: plan_vocab[t] & shop_vocab[t] for t in set(plan_vocab) & set(shop_vocab)}

    # 4. Extract, compare.
    say("Extraction des armatures")

    def extract_and_compare(types: set[str] | None, pulls: dict[str, float] | None = None):
        plan = extract_pages(plan_pages, cfg, shared, types, pulls)
        shop = extract_pages(shop_pages, cfg, shared, types, pulls)
        assign_ids(plan)
        assign_ids(shop)
        return plan, shop, *compare_project(plan, shop, cfg)

    def agreement(results: list[Result], type_element: str) -> tuple[int, int]:
        pairs = [r for r in results if r.type_element == type_element and r.methode == "repere" and r.atelier]
        return sum(r.statut == CONFORME for r in pairs), len(pairs)

    # Element names (C-12, or a grid crossing such as B-3) are trusted for a type only
    # when plan and shop drawings turn out to share some: read once with names
    # everywhere, then keep them for the types that pass.
    first_plan = extract_pages(plan_pages, cfg, shared, None)
    first_shop = extract_pages(shop_pages, cfg, shared, None)
    names: dict[str, dict[str, set[str]]] = {}
    for side, elements in (("plan", first_plan), ("atelier", first_shop)):
        for e in elements:
            if e.label:
                names.setdefault(e.type_element, {"plan": set(), "atelier": set()})[side].add(e.label)
    common = {t: sides["plan"] & sides["atelier"] for t, sides in names.items()}
    label_types = {t for t, labels in common.items() if len(labels) >= cfg.min_shared_labels}

    say("Comparaison plan / atelier")
    # A sheet of named elements is either a schedule (names in a header, bars under them)
    # or rows of details (each titled close by).  Most of a shop drawing agrees with its
    # plan, so read each element type both ways and keep the reading that agrees most.
    pulls: dict[str, float] = {}
    if label_types and len(cfg.header_pulls) > 1:
        trial = {pull: extract_and_compare(label_types, {t: pull for t in label_types})[2] for pull in cfg.header_pulls}
        for type_element in label_types:
            pulls[type_element] = max(cfg.header_pulls, key=lambda pull: agreement(trial[pull], type_element)[0])
    plan_elements, shop_elements, results, coverage = extract_and_compare(label_types, pulls)

    # When nearly every pair made by name disagrees, the pairing is at fault (callouts
    # given to the wrong name), not the drawing: compare that type by content instead.
    distrusted = set()
    for type_element in label_types:
        agree, total = agreement(results, type_element)
        if total >= cfg.min_label_pairs and agree < cfg.min_label_agreement * total:
            distrusted.add(type_element)
    if distrusted:
        plan_elements, shop_elements, results, coverage = extract_and_compare(label_types - distrusted, pulls)
        coverage.reperes_non_fiables = sorted(distrusted)
    coverage.lecture = {t: ("tableau" if pull == min(cfg.header_pulls) else "details") for t, pull in pulls.items()
                        if t not in distrusted}

    stats = dict(page_stats)
    stats.update(
        plan_elements=len(plan_elements), atelier_elements=len(shop_elements),
        plan_barres=sum(len(e.bars) for e in plan_elements), atelier_barres=sum(len(e.bars) for e in shop_elements),
        plan_reperes=sum(e.labeled for e in plan_elements), atelier_reperes=sum(e.labeled for e in shop_elements),
        reperes_communs=sum(len(v) for v in common.values()),
        feuillets=len({p.feuillet for p in plan_pages}),
        **{s: sum(r.statut == s for r in results) for s in STATUSES},
        a_valider=sum(r.a_valider for r in results),
        apparies_par_repere=sum(r.methode == "repere" for r in results),
        duree_s=round(time.time() - t0, 1),
    )
    stats["par_type"] = _stats_by_type(plan_pages, shop_pages, plan_elements, shop_elements, common, results)
    out = RunOutput(files.name, out_dir, plan_elements, shop_elements, results, coverage, stats)
    out.files.update(export_json(out))
    return out


def _stats_by_type(plan_pages, shop_pages, plan_elements, shop_elements, shared, results) -> dict[str, dict[str, int]]:
    """Counts per element type: shows at a glance where extraction or matching is thin."""
    table: dict[str, dict[str, int]] = {}

    def row(type_element: str) -> dict[str, int]:
        return table.setdefault(type_element, Counter())  # type: ignore[arg-type]

    for page in plan_pages:
        row(page.type_element)["plan_pages"] += 1
    for page in shop_pages:
        row(page.type_element)["atelier_pages"] += 1
        row(page.type_element)["atelier_pages_ocr"] += page.origin == "ocr"
    for side, elements in (("plan", plan_elements), ("atelier", shop_elements)):
        for e in elements:
            row(e.type_element)[f"{side}_elements"] += 1
            row(e.type_element)[f"{side}_reperes"] += e.labeled
            row(e.type_element)[f"{side}_barres"] += len(e.bars)
    for type_element, labels in shared.items():
        row(type_element)["reperes_communs"] = len(labels)
    for r in results:
        row(r.type_element)[r.statut] += 1
        row(r.type_element)["par_repere"] += r.methode == "repere"
    return {t: dict(c) for t, c in sorted(table.items())}


# ------------------------------------------------------------------ export

def _bar_details(el: Element) -> list[dict]:
    return [{"texte": b.raw, "role": b.role, "niveau": b.level, "confiance": b.conf,
             "bbox": [round(v, 1) for v in b.bbox]} for b in el.bars]


def result_to_dict(r: Result) -> dict:
    return {
        "id": r.id, "statut": r.statut, "feuillet": r.feuillet, "type_element": r.type_element, "element": r.element,
        "confiance": r.confiance, "a_valider": r.a_valider, "methode": r.methode, "note": r.note,
        "plan_id": r.plan.id if r.plan else None, "atelier_id": r.atelier.id if r.atelier else None,
        "ecarts": [{"attribut": e.attribut, "plan": e.plan, "atelier": e.atelier, "gravite": e.gravite,
                    "message": e.message} for e in r.ecarts],
    }


def export_json(out: RunOutput) -> dict[str, Path]:
    """Write the Appendix A database, the side-car details and the comparison."""
    elements = out.plan_elements + out.shop_elements
    records = [e.to_record().model_dump() for e in elements]
    paths = {
        "elements": out.out_dir / f"{out.project}_elements.json",
        "details": out.out_dir / f"{out.project}_details.json",
        "comparaison": out.out_dir / f"{out.project}_comparaison.json",
    }
    paths["elements"].write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    details = {e.id: {"confiance": e.conf, "niveaux": list(e.levels), "repere_normalise": e.label,
                      "avec_repere": e.labeled, "barres": _bar_details(e)} for e in elements}
    paths["details"].write_text(json.dumps(details, ensure_ascii=False, indent=1), encoding="utf-8")
    comparison = {
        "projet": out.project,
        "statistiques": out.stats,
        "couverture": asdict(out.coverage),
        "par_feuillet": summarize(out.results),
        "resultats": [result_to_dict(r) for r in out.results],
    }
    paths["comparaison"].write_text(json.dumps(comparison, ensure_ascii=False, indent=1), encoding="utf-8")
    return paths
