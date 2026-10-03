# OptiFrame · Strategy 15: Interoperability exports (optical-lab tracer format, DXF, 1:1 PDF)

| | |
|---|---|
| **Status** | NOT STARTED |
| **Priority** | P3 (value for SN-SF after the hackathon; small scoring impact) |
| **Effort** | 2–3 h |
| **Depends on** | strategy 2 / 8 (contour in mm, boxing data) |
| **Rubric lines** | Contour quality (5: the SVG is one of several exports), Presentation (10: practical impact), Code (5) |
| **Differs from 1–10** | Strategy 9 exports an STL and an SVG. This makes the measured lens shape usable by **existing optical-lab equipment and CAD tools**: a tracer-data file in the optical industry's data-communication format, a DXF for laser cutters and CAD, and a print-ready 1:1 PDF |
| **Work folder** | `optiframe-participants/work/strat15/` |

---

## 1. Context you need

- Opticians normally get lens shapes from a **frame tracer** and send them to edgers / labs using the industry's data-communication standard maintained by The Vision Council (the "DCS", historically known as the OMA format): tracer data as radii at many angles around the boxing centre plus boxing dimensions (HBOX, VBOX, DBL, circumference…). **Check the current DCS specification** for exact record names, units and formats before implementing.
- SN-SF will test the prototype with sector specialists after the hackathon (brief §2: INOVA event in October 2026, SN-SF offices in November 2026). Interoperability with standard tools matters to them.

## 2. The idea

Add an "Exporter" menu with:
1. **Tracer file** (DCS / OMA-style): boxing data and radii at N equally spaced angles (e.g. 400 or 1000), for left and right lenses, with job metadata; plus a viewer that re-reads the file and overlays it on the photo (round-trip check).
2. **DXF** (R12, polylines in mm): contour, seat outline (contour + clearance), rim outline: for laser-cut templates or CAD.
3. **PDF 1:1** with the contour, a 50 mm scale bar and "imprimer à 100 %" (more reliable printing scale than SVG in some browsers).
4. **JSON** (our own): contour points, boxing, measurement metadata (phone, method, confidence).

## 3. Why it could score

It shows the jury and SN-SF a path to real-world use (labs, makers), costs little once contours exist, and the round-trip test doubles as a contour-integrity check.

## 4. Implementation plan

### 4.1 Files

```
work/strat15/
  export_dcs.py / .js    # radii resampling + record writer (after checking the spec)
  read_dcs.py            # parser for round-trip tests
  export_dxf.js          # e.g. with a small DXF writer (R12 LWPOLYLINE)
  export_pdf.js          # jsPDF with mm units
  samples/               # example exports for a test ellipse and a test rounded rectangle
```

### 4.2 Radii resampling

From the boxing centre, cast rays at angles θ_k = 2πk/N; intersect with the contour polygon (take the outermost intersection); store radii in the unit required by the spec (often 1/100 mm); define the angle origin and direction (nasal / temporal convention for left vs right eye) per the spec.

### 4.3 Validation

Open the DXF in a free CAD tool (LibreCAD, FreeCAD) and measure; print the PDF and measure the scale bar; parse the tracer file back and compare radii.

## 5. How to test it

| # | Test | Pass if |
|---|---|---|
| T1 | Round trip | contour → tracer file → parsed radii → contour: max deviation ≤ 0.05 mm |
| T2 | Spec conformance | file passes a checklist derived from the spec (record names, units, angle convention) |
| T3 | DXF | opens in LibreCAD / FreeCAD; measured width equals A within 0.01 mm |
| T4 | PDF print | printed scale bar 50.0 ± 0.2 mm on two printers |

## 6. Risks

Implementing the industry format from memory: **read the specification first**; if it is not accessible, ship DXF / PDF / JSON only and state the limitation.

## 7. Combines with

Strategy 2 / 8 (contours, boxing), 9 (frame), 10 (export menu in the app).

## 8. Results log

| Date | Who | Format | Round-trip error | Notes |
|---|---|---|---|---|
| | | | | |
