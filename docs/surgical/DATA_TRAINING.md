# Surgical Data and Training Plan

## Data hierarchy

| Tier | Source | Primary use | Limitation |
|---|---|---|---|
| D0 | Synthetic scenes and scripted simulation | Interfaces, fault tests, basic policies | Reality gap |
| D1 | Public/licensed surgical video | Workflow and representation learning | Usually lacks forces/actions/outcomes |
| D2 | Instrumented phantom procedures | Control learning and repeatable ground truth | Simplified tissue/anatomy |
| D3 | Cadaver or ethically sourced ex-vivo material | Anatomy, access, instrument interaction | No living physiology/healing |
| D4 | Approved veterinary data | Species-specific veterinary development | Not a surrogate for humans |
| D5 | Surgeon teleoperation and clinical investigation | Target-system behavior and outcomes | High cost, privacy and risk |
| D6 | Authorized postmarket cases | Monitoring and improvement hypotheses | Selection bias; changes require control |

## Required synchronized channels

- stereo/endoscopic and external video where approved;
- preoperative and intraoperative imaging and registration;
- instrument, camera, robot, and table pose;
- joint, drive, force/torque, tactile, temperature, and energy state;
- suction, irrigation, insufflation, cautery, and accessory state as applicable;
- workflow phase, surgeon control/confirmation, takeover, alarms, and conversion;
- anatomy/tissue annotations with uncertainty and annotator qualification;
- complications, postoperative outcomes, and relevant follow-up;
- complete hardware, software, model, calibration, instrument, and site manifest.

## Governance

- Obtain ethics/IRB or animal-welfare review, consent/authorization, data-use
  agreements, and jurisdiction-specific privacy review before collection.
- Separate identifying clinical records from de-identified engineering datasets.
- Preserve consent scope, provenance, access, retention, withdrawal, and deletion
  obligations in the manifest.
- Prohibit unlicensed scraping and uncontrolled reuse of clinical media.
- Maintain immutable raw data, curated versions, label audit trails, and leakage-
  resistant patient/site/operator splits.
- Evaluate representation across anatomy, demographics, pathology, site, equipment,
  surgeon experience, species, and body size where clinically relevant.

## Learning strategy

1. Pretrain perception and workflow representations on compliant video.
2. Train geometry, tracking, and contact estimation with instrumented D0–D3 data.
3. Learn surgeon motion priors from exact-system teleoperation; never treat video
   hand motion as ground-truth robot actuation.
4. Train short, interruptible task policies with explicit constraints and aborts.
5. Use simulation randomization and adversarial/fault scenarios to expose failure.
6. Fine-tune on reviewed, procedure-specific demonstrations.
7. Calibrate uncertainty and out-of-distribution detectors on locked test sets.
8. Distill/quantize only after equivalence and worst-case latency evaluation.
9. Freeze and sign model, software, calibration, configuration, and evidence as one
   release unit.

No online weight update occurs during clinical operation. Case data enters a
separate review pipeline and can influence only a future controlled release.

## Evaluation

Report distributions and confidence intervals rather than only averages:

- completion and conversion/takeover rates;
- tissue injury, boundary violation, bleeding/thermal proxies, and force exposure;
- path, placement, depth, registration, and closure accuracy;
- latency, jitter, missed deadlines, memory, power, and thermal behavior;
- sensor/calibration failure sensitivity;
- performance by patient/species/site/operator/equipment slice;
- uncertainty calibration and false-safe/false-alarm behavior;
- comparison with clinician and conventional standard-of-care baselines.

Clinical endpoint selection and noninferiority/superiority margins require
specialty clinicians, biostatisticians, ethics review, and regulator agreement.

## Data contingencies

- **Consent or provenance defect:** quarantine derived samples and models; assess
  whether retraining is required.
- **Label disagreement:** adjudicate with qualified clinicians and preserve both
  original labels and resolution.
- **Split leakage:** invalidate affected results, rebuild splits, and repeat tests.
- **Site/domain shift:** restrict intended use or collect prospective evidence;
  do not silently normalize it away.
- **Rare catastrophic event scarcity:** use mechanistic simulation, fault injection,
  expert scenarios, and conservative rules rather than claiming learned mastery.

