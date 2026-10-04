# l2c-rebar: from plans to shop drawings

Checks rebar shop drawings (dessins d'atelier) against the structural plans of a reinforced-concrete
building and tells the engineer where they disagree.

For one project it produces:

| Output | File | What it is |
|---|---|---|
| JSON database | `<project>_elements.json` | Every rebar annotation found on the plans and the shop drawings, in the Appendix A schema (sheet, page, x, y, element, bars) |
| Comparison | `<project>_comparaison.json` | Each element classified: compliant, non-compliant (with the discrepancy), missing from the shop drawings, added in the shop drawings |
| PDF report | `<project>_rapport.pdf` | Counts per plan sheet, then each non-conformity with its location and an image extract of both drawings |
| Annotated PDFs | `annotes/*_annote.pdf` | Copies of the plan and shop drawings with each finding circled and linked to its counterpart |
| Details | `<project>_details.json` | What the schema has no room for: confidence, raw text, bounding boxes, storey |

Everything runs on the local machine. No document, text or image is sent anywhere.

## Quick start

```
python -m venv .venv
.venv\Scripts\activate            # Linux / macOS: source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

python -m l2c_rebar run path\to\PROJECT                  # writes outputs\PROJECT\
python -m l2c_rebar evaluate path\to\PROJECT known.xlsx  # score against documented non-conformities
python -m l2c_rebar ui                                   # interface, with validation of uncertain findings
python -m l2c_rebar diff old.pdf new.pdf                 # what changed between two revisions of a shop drawing
pytest                                                   # tests (add -m "not slow" to skip the OCR test)
```

The project folder is expected as handed out for the challenge:

```
PROJECT/
  L2C_PLAN_STR_PROJECT.pdf          the structural plans (one PDF, one sheet per page)
  DA/
    Colonnes/*.pdf                  shop drawings, grouped by element type
    Dalles/*.pdf
    Fondations/*.pdf  ...
```

Useful options of `run`: `--ocr off` (skip pages without text, a few seconds per project), `--no-crops`
(report without image extracts), `--config file.json` (override any field of `Config`, see
`src/l2c_rebar/config.py`).

To try the tool without any confidential data, `notebooks/demo.ipynb` builds a made-up project with planted
errors and runs the whole pipeline on it.

### Reading sheets that have no text

Many shop drawings are CAD plots without a text layer. They are read by a local OCR model, in three steps
that each raised the share of callouts read exactly on a benchmark page (a sheet that has both drawn text and a
text layer, used as ground truth):

| Setting | Callouts read exactly |
|---|---|
| PP-OCRv4, 200 dpi (models bundled in the wheel; automatic fallback) | 57% |
| PP-OCRv5 with the English recogniser, 200 dpi | 79% |
| Same at 300 dpi (default) | 85% |

On vector plots the page is first redrawn with only its character-sized paths, so that dimension lines and bars
no longer cross the lettering (`pdf/vector.py`). Text that AutoCAD stores beside stroke lettering as
"AutoCAD SHX Text" comments is read directly when a plot kept it.

The PP-OCRv5 models are fetched once by `rapidocr` on first use and then cached; run once with a network
connection before a demonstration. With a DirectX 12 GPU, a sheet takes 15 to 25 seconds instead of minutes:

```
pip uninstall -y onnxruntime
pip install onnxruntime-directml
```

OCR results are cached in `outputs/<project>/.ocr-cache/`, so a second run takes seconds.

## How it works

```
PDFs ──> text lines with coordinates ──> rebar callouts ──> elements ──> matching ──> comparison ──> report
         (text layer, else local OCR)    (grammar)          (layout,     (name or grid
                                                             grid)       crossing, else content)
```

| Step | Module | What it does |
|---|---|---|
| Read | `pdf/text.py`, `pdf/ocr.py`, `pdf/vector.py` | Text lines in displayed page coordinates (page rotation applied). A page with fewer than 25 words is read by OCR, tile by tile |
| Identify the sheet | `pdf/sheets.py`, `parsing/elements.py` | Sheet number from the PDF bookmark or the title block. Element type from the series (S-100 foundation, S-300 beam, S-400 shear wall, S-500 column, S-600 slab). For shop drawings, type and storey come from folder and file names |
| Parse callouts | `parsing/rebar.py` | Quantity, size, spacing, length, mark. Plans: `8-25M`, `12(6)-15M`, `10M@300 c/c`, `10M@12" c/c`. Shop drawings: `24 15M 15A12 @12"`, `2x4 25M 25A301`, `24 15M 20-6`. Spacings and lengths are converted to millimetres |
| Locate on the grid | `extract/grid.py` | On a column plan a column has no name: it is a filled rectangle at a grid crossing with a tag beside it. The grid is rebuilt from its bubbles, each tag is paired with its rectangle, and the column is named by its crossing (`B-3`), which is how shop drawings refer to it (`B-3`, `B/3`, `B-12, B-13`) |
| Group into elements | `extract/layout.py`, `extract/document.py` | Elsewhere, a callout belongs to the label above it in a schedule, on its row in a table, or next to it in a detail. Names written as a list share one detail. Callouts without a name become elements named by sheet zone |
| Match | `compare.py` | By element name or grid crossing when plan and shop drawings share them. Otherwise by content (size, quantity, spacing) within the same element type and storey |
| Compare | `compare.py` | Only attributes present on both sides. A plan quantity may be split over several shop marks; a plan in millimetres and a shop drawing in inches agree within 2% |
| Report | `report/` | ReportLab PDF, image extracts, annotated PDFs |
| Score | `evaluate.py` | Against a spreadsheet of documented non-conformities (sheet, grid location, plan value, shop value): recall, and for each miss the stage where it was lost |

### Classification and severity

Each element gets one of the four statuses required by the rules. Each discrepancy has a severity:

| Severity | Meaning |
|---|---|
| critique | Less steel than designed: fewer bars, smaller size, wider spacing |
| majeur | Bars not found, larger size substituted, shorter length |
| mineur | More steel than designed |

Each result carries a confidence between 0 and 1. Below 0.60 it is flagged "à valider": text read by OCR, match
by content, uncertain storey. The interface lets the engineer confirm or reject those, and regenerates the report.

### Calibrated by agreement

Detailers have their own habits, and a new project brings new ones. Instead of fixed assumptions, the tool
relies on one fact: most of a shop drawing agrees with its plan. Where a convention is open, it tries the
readings and keeps the one that agrees most often.

1. **Names are used only when both sides share them.** If plan and shop drawings have no element name or grid
   crossing in common for a type, that type is compared by content instead.
2. **Storeys.** A shop sheet named `NIV 2@3` may detail the plan storey 2 or 3, and a building may skip a floor
   number. Shop storey names are mapped to plan storeys, in order, so as to agree as often as possible.
3. **Schedule or details.** A sheet of named elements is read both as a schedule (names in a header, bars under
   them) and as rows of details (each titled close by); the better reading is kept, per element type.
4. **Per element or totals.** A detail drawn once for several elements (`B-12, B-13`) may list the bars of one
   or the total for all; the reading that agrees most is kept. A shop quantity that is an exact multiple of the
   plan quantity is taken as such a shared detail, not as a surplus.
5. **Mass disagreement means a wrong pairing.** If fewer than half of the pairs made by name agree for a type,
   the pairing is abandoned for that type and stated in the report.
6. **Missing elements are reported only where the sheet was read well.** When fewer than half of a sheet's
   elements are found in the shop drawings, the report says so once instead of listing each element.

## The JSON database

`<project>_elements.json` is a list of records with exactly the keys of Appendix A, validated by pydantic
(`models.Record`). `x`, `y` are PDF points from the top-left corner of the displayed page, at the centre of the
annotation. `source` is `plan` or `atelier`.

```json
{
  "id": "S-501_B-2@RDC_plan", "source": "plan", "fichier": "L2C_PLAN_STR_GRILLE.pdf", "feuillet": "S-501",
  "page": 1, "x": 416.9, "y": 372.9, "type_element": "colonne", "element": "B-2",
  "armature": [
    {"repere": null, "diametre": "25M", "quantite": 12, "espacement_mm": null, "longueur_mm": null},
    {"repere": null, "diametre": "10M", "quantite": null, "espacement_mm": 300, "longueur_mm": null}
  ]
}
```

For shop drawings, `feuillet` is the file name (plus the page for multi-page files), since those sheets carry no
plan sheet number.

## Assumptions

- Bar sizes are Canadian metric (10M to 55M). Spacing may be in millimetres or inches; both are stored in mm.
- Sheet series follow the rules: S-1xx foundations, S-3xx beams, S-4xx shear walls, S-5xx columns, S-6xx slabs.
  Other sheets are typed by their title, or extracted as `autre` and not compared.
- Shop drawing folders or file names contain the element type (Colonnes, Dalles, Fondations, Poutres, Murs,
  Refends, Semelles, Radiers) and, where relevant, the storey (`NIV 2`, `RDC`, `SS1`, `2@3`).
- Grid bubbles of a plan view are the largest short labels on the sheet, letters in one direction and numbers
  in the other.
- In `12(6)-15M` the number in brackets is a subset of the quantity, not a length.
- In a shop callout `24 15M 20-6`, `20-6` is a length in feet and inches; a three-digit number after the size
  is a bar mark.
- A shop drawing details more than the plan shows. A shop callout without a name and without a plan twin is
  counted, not reported as an addition.

## Known limitations

These are stated plainly because they decide how far the output can be trusted.

- **Slabs, foundations and beams are confirmed, not contradicted, by position.** Every callout of a plan view is
  placed on the building grid, and a plan callout whose twin is drawn within half a bay on the shop drawing is
  reported compliant. A different number at the same place is not reported: measured on a development project,
  only one slab callout in five has its twin that close (a detailer writes a bar where it starts, an engineer
  where it is needed), so it would mostly raise false alarms. What position cannot confirm falls back to
  matching by content within the storey, where a wrong quantity goes unnoticed if another callout carries it.
  On the one development project that came with a list of documented non-conformities, the tool finds the two
  column cases (right location, right values) and misses the slab, foundation and wall cases for this reason.
- **Slab callouts written without a bar size** (a bare `12(6)`) are read into the JSON and confirmed by position
  when possible; otherwise they are counted as not verified. A plain number beside a bar is not read yet.
- **The order of reinforcement layers is not compared** (plan "layer 1" against the shop drawing's layering).
- **OCR is imperfect.** Even at 85% of callouts read exactly, a dense sheet carries misreads. Every result that
  rests on OCR text is flagged "à valider". On one development project the column sheets read by OCR disagree
  with the plan for a third of the columns, which is not credible: those findings need the engineer.
- **Layout rules are heuristics.** A callout is given to the nearest plausible label; dense sheets can mislead it.
- **Development was done almost entirely without reading the drawings.** The confidentiality rule forbids
  sending documents to external AI services, and this tool was written with an AI coding assistant. The
  assistant did not open the drawings or the list of known non-conformities: it worked from counts, from masked
  notation patterns (every digit replaced by 9, every letter by A), from a team member's description of a
  column tag (including one tag quoted as an example), and from the score returned by `evaluate`. One exception:
  a team member sent the assistant a screenshot of part of a slab plan. Nothing from it was copied into the
  code, the tests or this repository; it only confirmed that slab callouts are written along their bars.
- No model was trained. The OCR models are pre-trained, open-source ones (PP-OCR, Apache 2.0).

## Bonus features

- **Annotated PDFs**: findings circled on both documents, with a link from each tag to its counterpart.
- **Confidence score and validation**: `python -m l2c_rebar ui`; verdicts are saved in `validations.json`.
- **Revision comparison**: `python -m l2c_rebar diff old.pdf new.pdf --out changes.json`.

## Repository layout

```
src/l2c_rebar/
  cli.py  pipeline.py  config.py  models.py  compare.py  evaluate.py  validation.py  revisions.py
  synthetic.py  app.py
  pdf/        text.py  ocr.py  vector.py  sheets.py
  parsing/    rebar.py  elements.py
  extract/    layout.py  grid.py  document.py
  report/     pdf_report.py  crops.py  annotate.py
tests/        grammar, layout, grid, comparison, interface, end-to-end on two made-up projects
notebooks/    demo.ipynb (generated by build_notebook.py)
```

## Confidentiality

The project PDFs and everything derived from them (`outputs/`, OCR cache) are excluded from git by `.gitignore`.
Delete them from the workstation at the end of the event, as the rules require.
