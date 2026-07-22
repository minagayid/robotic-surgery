# RobotX Surgical Program Charter

> Planning only. This document does not authorize clinical, dental, or animal
> use and is not medical or legal advice.

## Mission

Develop an offline-first, clinician-controlled robotic platform that can assist
with and eventually perform validated segments of human, dental, and veterinary
surgery while remaining interruptible, traceable, sterile, and bounded by
independent safety systems.

The phrase **full surgery** is treated as a system-of-systems goal. It includes
patient selection, planning, positioning, access, visualization, manipulation,
hemostasis, energy delivery, closure, instrument/accounting checks, complication
management, postoperative handoff, and the surrounding human team. A robot that
only moves instruments has not mastered a full procedure.

## Non-negotiable boundaries

- A licensed surgeon, dentist, or veterinarian remains the responsible operator
  for every investigational or clinical use.
- The robot never expands its own intended use, autonomy level, force envelope,
  energy setting, anatomical workspace, or instrument permissions.
- Anesthesia and physiologic management remain separate clinician-controlled
  systems. RobotX may consume approved status/interlock signals but does not
  independently administer anesthesia or medication.
- No Internet dependency is allowed during a procedure. Offline operation does
  not eliminate cybersecurity, supply-chain, removable-media, or insider risk.
- Patient use requires a locked and signed hardware/software/model/calibration
  configuration with traceable evidence and approvals.
- Veterinary development is not a regulatory or ethical shortcut to human use.
- A conventional surgical conversion plan, trained team, and required equipment
  must be present before any procedure begins.

## Capability is a matrix, not a model

Every released capability is identified by:

```text
procedure × procedure segment × anatomy/site × patient/species population
× instrument/accessory set × imaging/sensor set × autonomy level
× supervising-user qualification × operating environment
```

A change to any cell triggers impact assessment and may require new verification,
validation, training, or regulatory submission. Evidence from one specialty or
species is never assumed to transfer automatically.

## Autonomy ladder

| Level | Capability | Required supervision | Example |
|---|---|---|---|
| S0 | Measure, replay, simulate | Research team | Skill scoring on recorded data |
| S1 | Advise or visualize | Clinician decides and acts | Anatomy overlay, warning, navigation |
| S2 | Shared control | Continuous hands-on control | Tremor filtering, virtual fixture |
| S3 | Bounded task autonomy | Continuous observation and immediate takeover | Camera positioning, one suture throw |
| S4 | Authorized segment autonomy | Clinician confirms checkpoints and manages exceptions | Repeated closure pattern in defined tissue |
| S5 | Full-procedure autonomy | Long-term research; governance not yet defined | Complete procedure within a narrow indication |

The initial product target is S1/S2. S3 is an investigational milestone. S4 and
S5 require new governance decisions and evidence rather than automatic roadmap
promotion.

## Program tracks

### Shared platform

- medical-grade compute, time synchronization, logging, and signed releases;
- independent safety controller and power isolation;
- instrument identity, calibration, life-cycle, and sterility status;
- anatomy/world model with uncertainty and protected structures;
- force, motion, energy, temperature, and workspace supervision;
- surgeon console, foot/hand controls, alarms, takeover, and conversion support;
- simulation, digital twins, replay, fault injection, and evidence management.

### Human surgery

Begin with visualization, navigation, camera assistance, and shared control.
Advance to bounded manipulation only for a defined procedure and population after
bench, cadaver/ex-vivo, human-factors, regulatory, and clinical gates.

### Dental surgery

Exploit rigid anatomy and imaging for segmentation, implant-path planning,
orientation/depth constraints, and shared-control drilling. Begin on digital and
physical phantoms or extracted teeth; autonomous patient drilling is not an early
milestone.

### Veterinary surgery

Maintain species-, size-, anatomy-, and procedure-specific models. Begin with
simulation and non-living models, then proceed only through veterinary ethics and
facility approvals. Food-producing animals require additional residue and food
safety review where relevant.

## Governance

Create five independent sign-off authorities:

1. **Clinical:** specialty surgeons/dentists/veterinarians and anesthesia/nursing.
2. **Safety engineering:** hazard analysis and independent safety architecture.
3. **Quality/regulatory:** QMS, design controls, submissions, audits, and change control.
4. **Data/AI:** consent, privacy, bias, labeling, model evaluation, and drift.
5. **Ethics:** human-subject and animal-welfare review.

No project lead may waive a failed clinical or safety gate alone. Conflicts and
dissent are recorded in the decision file.

## Program stages and exit gates

| Stage | Work | Exit evidence |
|---|---|---|
| A — Foundation | Intended use, team, QMS, hazards, architecture | Approved charter, risk plan, regulatory strategy |
| B — Research bench | Simulation, phantoms, sensors, instruments, replay | Repeatable baseline and complete failure taxonomy |
| C — Assistance | S1/S2 navigation and shared control | Human-factors validation and bench performance |
| D — Task autonomy | One S3 task on non-living models | Locked design, worst-case and fault-injection evidence |
| E — Preclinical | Cadaver/ex-vivo and approved animal work if justified | Independent review, protocol endpoints met |
| F — Clinical study | Regulator/ethics-authorized staged investigation | Prespecified safety/effectiveness analysis |
| G — Marketed operation | Authorized indication and trained sites | Surveillance, complaint, recall, and update capability |
| H — Expansion | New segment/population/instrument | New or bridged evidence accepted by governance/regulator |

## Program stop rules

Pause the affected capability when any of the following occurs:

- death, serious injury, unanticipated adverse device effect, or credible near miss;
- unexplained violation of a protected anatomical boundary;
- loss of deterministic takeover or safe-stop behavior;
- sterile barrier, instrument integrity, calibration, or identity uncertainty;
- cybersecurity compromise or unverifiable software/model provenance;
- performance outside the prespecified clinical or demographic envelope;
- data-integrity or consent failure affecting training or evaluation evidence;
- repeated operator confusion involving a safety-critical control.

Restart requires documented investigation, corrective/preventive action, evidence
review, and the approvals appropriate to the stage.

## Full-scale success definition

Success is not a single demonstration. It is a portfolio of authorized,
procedure-specific capabilities with reproducible outcomes, independent safety,
trained clinical teams, sterile and serviceable hardware, secure offline updates,
transparent limitations, postmarket monitoring, and rapid rollback or recall.

