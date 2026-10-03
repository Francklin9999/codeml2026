# Propolys · Strategy 35: FirmwareWitness — verify embedded-device update provenance

| Field | Proposal |
|---|---|
| Status | NOT STARTED |
| Priority / effort | P2 / 3 h |
| Dependency | Mock firmware release records and hashes; no device flashing |
| Source | NIST SP 800-193 platform firmware resiliency guidance |
| Work folder | `propolys-participants/work/strat35/` |

## 1. Context and local evidence

The local [results overview](../RESULTS_OVERVIEW.md) records no Propolys customer or device security work. DepGuard (10) screens open-source software packages; ModelSeal (31) tracks AI model releases. FirmwareWitness focuses on how a small industrial equipment operator receives and verifies firmware updates from a device supplier, including version, signature status, source and approved maintenance ticket. No real firmware, equipment or manufacturer integration has been tested. NIST platform-firmware resiliency guidance is a technical reference and does not indicate local demand.

## 2. Idea and novelty

**FirmwareWitness** provides an update intake and approval ledger for small manufacturers with connected machinery. It ingests vendor release notes and an update artifact manifest, verifies available signatures and hashes against manufacturer-published trust material, compares the target device model/version to the maintenance record, and routes ambiguity to the equipment owner. AI summarizes release notes and flags unexplained version/model inconsistencies; deterministic cryptographic checks perform integrity validation. It never flashes equipment or infers a clean firmware image from prose. Revenue assumption: annual site subscription plus onboarding with an industrial integrator.

Nearest old idea is DepGuard, which analyzes third-party code packages before developer installation. FirmwareWitness is for device fleet maintainers, not software build pipelines; the gate is supplier release-to-maintenance approval rather than package behavioral analysis.

## 3. Why it fits the rubric

The demo shows a mismatched update stopped before an operational change. Use [NIST SP 800-193](https://csrc.nist.gov/pubs/sp/800/193/final) for platform firmware resiliency context, without claiming the proposed product meets its recommendations.

## 4. Pitch files and three-minute demo

Create `propolys-participants/work/strat35/pitch.md` (three-slide outline and script), `propolys-participants/work/strat35/demo.html` (synthetic click-through), and `propolys-participants/work/strat35/validation.md` (interview guide, baseline and proposed gates).

Slides: incoming fictional update; signature/version check against a device record; industrial maintenance manager buyer, site subscription hypothesis and integrator pilot. Demo fabricated manifests and simulated signature verification; no device connection or update occurs.

## 5. Proposed validation

Interview 8 industrial maintenance or OT security managers. Review 12 synthetic update packets with seeded wrong model, unexpected version and absent signature. Adopt if 6/8 confirm a manual intake/approval step and every seeded mismatch is flagged while all valid synthetic signatures verify. Kill if suppliers do not publish verifiable trust material or the workflow would require active network access to OT assets.

## 6. Risks and limits

Signature verification depends on correct trusted keys and revocation; valid signatures do not ensure an update is safe or compatible. Incorrect data can stop maintenance or admit a compromised release. Preserve manual vendor confirmation and site change control.

## 7. Combines with

WaterSentinel may use it as a vendor-update record for water sites, but FirmwareWitness is a general update intake workflow, not monitoring.

## 8. Results log

NOT RUN. No industrial interviews, vendor manifests, cryptographic review or equipment action took place. Metrics are proposed.
