# Verification, Validation, and Clinical Pathway

## Evidence ladder

### V0 — Requirements and analysis

Trace intended use and hazards to system/software requirements, risk controls,
verification methods, clinical endpoints, labeling, training, and surveillance.
Create worst-case combinations rather than testing one variable at a time.

### V1 — Unit and subsystem verification

Drivers, timing, command expiry, limits, alarms, release, brakes, power isolation,
instrument recognition, calibration, logging, privacy, security, and update/rollback.
Fuzz parsers and inject corrupt, stale, replayed, and contradictory messages.

### V2 — Integrated bench and phantom

Anatomically meaningful phantoms, instrumented tissue analogues, motion rigs,
fluids/smoke, energy delivery, degraded visibility, patient/table motion, and
sterile workflow. Compare against clinician baselines and predefined specifications.

### V3 — Cadaver and ex-vivo

Evaluate access, anatomy registration, tissue interaction, instrument reach,
conversion, and realistic workflow. Document where these models cannot represent
perfusion, healing, physiology, or complication response.

### V4 — Approved animal work where necessary

Use only when justified by questions not answerable otherwise, with veterinary
oversight, welfare endpoints, humane stopping rules, and species-specific purpose.
Evidence does not automatically bridge to humans.

### V5 — Human factors and simulated use

Representative surgeons, dentists, veterinarians, nurses, technicians, and
reprocessing/service staff perform critical tasks and emergency scenarios in the
intended environment. Validate setup, sterile draping, alarms, takeover, conversion,
cleaning, training, labeling, and maintenance.

FDA emphasizes minimizing use-related risk and validating safe/effective use by
intended users in intended environments:
<https://www.fda.gov/regulatory-information/search-fda-guidance-documents/applying-human-factors-and-usability-engineering-medical-devices>.

### V6 — Early clinical feasibility

Only after regulator and ethics authorization, begin with a small staged cohort,
experienced investigators, predefined stopping rules, independent monitoring,
locked configuration, conventional backup, and enhanced follow-up. Significant-
risk US studies generally require IRB approval and an FDA-approved IDE before
enrollment:
<https://www.fda.gov/medical-devices/investigational-device-exemption-ide/ide-approval-process>.

### V7 — Pivotal and postmarket

Use a prespecified protocol, comparator, endpoints, sample-size/statistical plan,
site/training controls, subgroup analysis, and adverse-event definitions. After
authorization, maintain complaint handling, vigilance, registries where useful,
field correction/recall, cybersecurity response, and periodic benefit-risk review.

## Universal test scenarios

- nominal procedure across the full allowed anatomy and equipment envelope;
- boundary anatomy and poor visibility;
- camera, tracking, force, energy, drive, compute, display, control, and log faults;
- calibration displacement and wrong instrument/accessory;
- unexpected motion, tissue deformation, bleeding, smoke, contamination, and fire;
- lost power, brownout, thermal throttling, storage exhaustion, and bus flooding;
- malicious/corrupt bundle, replayed message, removable-media exposure;
- alarm overload, operator error, team miscommunication, and delayed takeover;
- conventional conversion under time pressure.

## Release gates

Release requires:

1. all safety-critical requirements verified on the exact build;
2. risk controls demonstrated effective and residual risk accepted;
3. unresolved anomalies assessed and none capable of uncontrolled harm;
4. worst-case latency and environmental limits met;
5. human-factors critical tasks validated;
6. clinical/statistical objectives met for the claimed indication;
7. manufacturing, sterilization/reprocessing, service, training, cybersecurity,
   and surveillance readiness;
8. independent sign-off from clinical, safety, quality/regulatory, and ethics roles.

## Failure and rollback

Every release retains the preceding authorized bundle and compatibility data.
Rollback cannot cross incompatible hardware, calibration, instrument, or patient-
data schema boundaries. A safety issue may require capability disablement, site
notification, field correction, recall, or study suspension—not merely a model
update.

