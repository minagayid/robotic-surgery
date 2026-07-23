# Regulatory and Quality Plan

> A qualified regulatory team must map the actual intended use and deployment
> countries. This file is a planning baseline, not a classification decision.

## Quality system from day one

Operate the surgical program under a medical-device quality management system
before clinical prototypes. Maintain design/development planning, requirements,
risk management, architecture, reviews, verification/validation, configuration,
suppliers, production/service, complaints, corrective/preventive action, training,
and controlled records.

In the United States, FDA's Quality Management System Regulation became effective
February 2, 2026 and incorporates ISO 13485:2016:
<https://www.fda.gov/medical-devices/postmarket-requirements-devices/quality-management-system-regulation-qmsr>.

## Standards baseline to confirm with regulators

- ISO 13485 — medical-device quality management;
- ISO 14971 — medical-device risk management;
- IEC 62304 — medical-device software life cycle;
- IEC 62366-1 — usability engineering;
- IEC 60601-1 and applicable collateral/particular standards — electrical safety;
- IEC 80601-2-77:2019 + AMD1:2023 (Edition 1.1 consolidated) — basic safety
  and essential performance of robotically assisted surgical equipment;
- IEC 81001-5-1 and current regulator cybersecurity guidance;
- ISO 10993 series where patient-contact biocompatibility applies;
- ISO 14155 or jurisdictional good clinical practice for device investigations;
- sterilization, packaging, reprocessing, EMC, laser, radiation, and energy-device
  standards appropriate to the actual product.

As of July 2026, FDA recognition 6-510 covers IEC 80601-2-77 Edition 1.1.
Recognition of Edition 1.0 remains in transition only until July 2, 2028:
<https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfstandards/detail.cfm?standard__identification_no=46090>.

## Intended use and submission strategy

Define one indication, procedure segment, population, user, setting, instrument
set, and autonomy level. Request early regulator feedback before locking pivotal
architecture or clinical endpoints. Determine classification and pathway from the
claim and risk; do not infer it from another robot's marketing authorization.

AI components require lifecycle documentation, representative evaluation,
human-AI interaction, update control, and monitoring. FDA's January 2025 AI device
lifecycle document is draft guidance and should be treated as non-binding current
thinking rather than a final requirement:
<https://www.fda.gov/regulatory-information/search-fda-guidance-documents/artificial-intelligence-enabled-device-software-functions-lifecycle-management-and-marketing>.

## Sterility, reprocessing, and biocompatibility

- Identify patient-contact type/duration and material compatibility.
- Separate disposable, limited-use, and reusable parts.
- Design out inaccessible soil traps and ambiguous assembly.
- Validate cleaning, disinfection/sterilization, drying, packaging, transport,
  storage, use-life, and instructions with representative worst-case contamination.
- Track instrument use count and reject expired, incompatible, or unverified tools.

FDA notes that inadequate cleaning can leave biological debris and permit microbes
to survive disinfection or sterilization:
<https://www.fda.gov/medical-devices/reprocessing-reusable-medical-devices/how-are-reusable-medical-devices-reprocessed>.

## Human, dental, and veterinary separation

- Human and dental claims follow the applicable medical/dental device pathway in
  each market; dentistry is not automatically lower risk.
- Veterinary devices require country-specific review. In the US, FDA generally
  does not require premarket 510(k) or PMA for animal-only devices, while the
  manufacturer remains responsible for safety, effectiveness, and labeling:
  <https://www.fda.gov/animal-veterinary/animal-health-literacy/how-fda-regulates-animal-devices>.
- Animal research requires institutional and legal approvals independent of the
  commercial veterinary device pathway.

## Postmarket and incident readiness

Maintain complaint intake, reportability assessment, investigation, trend
analysis, corrective/preventive action, field action/recall, site notification,
software/model rollback, and registry strategy. US manufacturers must report
certain deaths, serious injuries, and reportable malfunctions under 21 CFR Part
803:
<https://www.fda.gov/medical-devices/medical-device-safety/medical-device-reporting-mdr-how-report-medical-device-problems>.

## Required controlled artifacts

- intended-use and regulatory strategy;
- user and system requirements;
- architecture and cybersecurity threat model;
- hazard analysis, FMEA/FTA/STPA as appropriate, and risk-benefit file;
- data/model provenance and evaluation reports;
- software bill of materials and supplier evidence;
- verification, validation, human-factors, and clinical reports;
- manufacturing, acceptance, calibration, servicing, and reprocessing procedures;
- labeling, contraindications, training, and emergency/conversion instructions;
- surveillance, vigilance, field action, and end-of-support plans.
