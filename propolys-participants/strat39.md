# Propolys · Strategy 39: PartTrace — secure provenance checks for replacement components

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P3 / 3 h |
| Dependency | Fictional component manifest and supplier documents |
| Source | NIST supply-chain risk management resources |
| Work folder | `propolys-participants/work/strat39/` |

## 1. Context and local evidence

The [results overview](../RESULTS_OVERVIEW.md) records no Propolys market validation. Procurement fraud (1) analyzes bidders/contracts; DepGuard (10) analyzes software package risks; FirmwareWitness (35) checks embedded firmware release records. PartTrace addresses physical replacement parts used by a small water, power or manufacturing operator: receiving staff need to reconcile a part serial, approved vendor and work order before installing an item in a safety/security-relevant asset. No counterfeit-parts incident or market size is asserted.

## 2. Idea and novelty

**PartTrace** is a receiving workflow for maintenance supervisors at smaller operators. It reads a packing slip, supplier certificate and work order, extracts part number, serial, lot and approved supplier, and highlights inconsistencies against the asset bill of materials. AI assists with varied document layouts and flags conflicting descriptions; deterministic matching and supplier registry checks provide the review basis. Unresolved items go to a human hold queue; the tool never declares a part counterfeit. Revenue assumption: subscription per maintenance site plus initial catalog mapping.

Nearest concepts are ProcureGuard and DocTrust. ProcureGuard seeks procurement fraud patterns across contract networks; DocTrust checks applicant document authenticity. PartTrace reconciles the identity of one physical maintenance component at point of receipt, using the approved asset configuration as reference.

## 3. Why it fits the rubric

Connects AI extraction to operational asset integrity, with a demo that makes “wrong part before install” immediately legible. NIST's [cybersecurity supply-chain risk resources](https://csrc.nist.gov/projects/cyber-supply-chain-risk-management) provide general context, not a claim that this workflow is required or demanded.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat39/pitch.md` (three-slide outline and script), `propolys-participants/work/strat39/demo.html` (synthetic click-through), and `propolys-participants/work/strat39/validation.md` (interview guide, baseline and proposed gates).

In `work/strat39/`, create slides for a fictional work order and mismatched delivered part, a source-linked receiving check, and a maintenance buyer with per-site subscription assumption. Demonstrate fabricated PDFs/images and clearly mark extracted fields as candidates; no real supplier is named.

## 5. Proposed validation

Interview 8 maintenance/receiving leads. Use 30 synthetic orders with seeded wrong model, serial mismatch and document naming variation; measure baseline manual checks and missed inconsistencies. Adopt if 6/8 report manual reconciliation and the mock flags all seeded identifier mismatches while producing no more than 3 false holds per 30 clean deliveries. Kill if supplier/asset catalogs cannot be maintained or the result is treated as certification.

## 6. Risks and limits

Valid suppliers may use inconsistent certificates; accurate fields do not prove authenticity or fit-for-purpose. False holds disrupt repairs; false acceptance can create hazards. Human supplier confirmation and safety-engineering review remain essential.

## 7. Combines with

Could relate to ProcureGuard through supplier master data, but product decision and unit of analysis are different.

## 8. Results log

NOT RUN. No interviews, physical parts, document corpus or integration tested. Metrics are future evaluation criteria.
