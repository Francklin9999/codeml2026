# Propolys · Strategy 32: SignScan — QR sign inventory and tamper response

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Printed mock signage and safe destination URLs |
| Source | CISA phishing awareness resources (QR-specific guidance to verify before pitch) |
| Work folder | `propolys-participants/work/strat32/` |

## 1. Context and local evidence

No local market or product results exist for Propolys, per [RESULTS_OVERVIEW](../RESULTS_OVERVIEW.md). Existing strategy 2 handles payment impersonation, 6 handles scam calls, 11 detects drones and 14 verifies media provenance. SignScan covers the physical-to-digital link created when a person scans a posted QR code in a campus, clinic or event venue. The scenario is distinct from email/social phishing, but QR attack prevalence and buyer urgency are not established here; avoid any numeric claim.

## 2. Idea and novelty

**SignScan** helps university facilities/security teams inventory organization-issued QR signs and detect replaced overlays during routine rounds. Each authorized sign has a signed inventory record, approved destination and owner. A staff phone app scans the visible code, compares destination and sign identity to inventory, and submits an image for computer-vision mismatch review; AI prioritizes likely overlays or changed placement, but staff confirm the sign before removal. A public user-facing safe destination resolver is an optional later feature. Revenue assumption: per-campus annual subscription plus installation audit.

Nearest old strategy is SkyWatch's multi-sensor drone detection; both use physical sensors, but SignScan is a controlled inspection workflow for fixed access prompts and destination integrity. Unlike CallBack, there is no payment approval or caller identity decision.

## 3. Why it fits the rubric

The live demo is understandable and visibly prevents a malicious destination. CISA phishing resources can ground the broad social-engineering security frame, but a QR-specific threat claim requires checking current official guidance: [CISA phishing guidance](https://www.cisa.gov/secure-our-world/recognize-and-report-phishing).

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat32/pitch.md` (three-slide outline and script), `propolys-participants/work/strat32/demo.html` (synthetic click-through), and `propolys-participants/work/strat32/validation.md` (interview guide, baseline and proposed gates).

Slide 1: fictional event QR poster with a sticker overlay. Slide 2: scan shows destination mismatch and routes a facilities ticket. Slide 3: campus facilities/security buyer, subscription assumption, pilot walk-through. Use printed fictional signs and harmless domains; do not scan or deploy unknown codes.

## 5. Proposed validation

Interview 8 campus or venue facilities/security staff. Test 30 mock signs with seeded overlays and legitimate changes. Baseline their existing sign inventory/rounding method. Adopt if 6/8 report no reliable QR inventory and prototype detects every seeded destination swap while correctly accepting at least 27/30 legitimate codes. Kill if mobile scan access, signage ownership or response authority is unclear.

## 6. Risks and limits

Image glare, stickers and benign maintenance can cause errors. Inventory goes stale; legitimate codes can themselves point to compromised websites. Avoid claiming safe browsing or phishing prevention. Protect location/image data and route unresolved findings to staff.

## 7. Combines with

May connect with a facilities ticket system but is unrelated to SkyWatch's aerial-sensor operations.

## 8. Results log

NOT RUN. No interviews, scan trials, campus inventory, integrations or threat prevalence research completed. Thresholds are proposed.
