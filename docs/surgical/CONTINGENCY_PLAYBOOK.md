# Surgical Contingency Playbook

This playbook is a design input and training framework. Each procedure dossier and
clinical site must turn it into approved, role-specific instructions consistent
with the device labeling and local clinical policy.

## Response hierarchy

1. **Prevent:** design constraints, redundancy, sterile workflow, qualification.
2. **Detect:** independent monitoring, plausibility checks, alarms, team observation.
3. **Contain:** freeze energy, stop or hold motion, preserve access and sterility.
4. **Recover:** clinician takeover, safe release/withdrawal, alternate instrument.
5. **Convert:** proceed conventionally or abort under the clinical team's authority.
6. **Learn:** seal logs, quarantine, report, investigate, correct, and revalidate.

The correct response is not always automatic withdrawal: moving a tool can worsen
bleeding or tissue injury. Every instrument/procedure defines whether the safe
state is hold, brake, release, withdraw along a verified path, remove power, or
immediate clinician control.

## Technical contingencies

| Condition | Detection | Immediate response | Fallback and follow-up |
|---|---|---|---|
| Main compute crash | Watchdog/heartbeat | Reject new commands; execute validated device-specific safe state | Manual takeover or conversion; quarantine bundle/logs |
| Power loss/brownout | Independent monitor | Controlled stop on backup power; maintain brakes/release path | Manual release/conversion; inspect before reuse |
| Control-bus loss or stale command | Sequence/deadline checks | Reject motion/energy; safe state | Local manual control if validated; investigate timing |
| Motor/encoder disagreement | Redundant plausibility checks | Stop affected axis and energy | Manual release; inspect drive, instrument, patient impact |
| Brake or release failure | Startup/in-case diagnostics | Stop other motion; clinician-directed recovery | Conversion with dedicated release tools; service lockout |
| Camera/endoscope loss | Frame health/independent view | Stop autonomous motion and energy | Restore/replace scope; manual visualization; convert |
| Tracking/registration drift | Landmarks/residuals/redundant sensors | Freeze navigation/autonomy | Re-register and re-confirm or revert to manual technique |
| Force sensor failure/saturation | Range and cross-sensor checks | Stop contact task; conservative hardware limits remain | Replace/calibrate; inspect tissue and tool |
| Instrument mismatch/expired life | Identity and lifecycle registry | Prevent arming | Replace with verified instrument; investigate inventory |
| Tool breakage/detached part | Force/vision/continuity anomaly | Stop, preserve field, alert team | Locate/retrieve clinically; counts and imaging as needed |
| Instrument stuck in tissue | Motion/force discrepancy | Hold; do not auto-retract | Surgeon-controlled release, alternate access, conversion |
| Energy device stuck on/thermal rise | Independent energy/time/temperature monitor | Hard-disable energy | Tissue assessment, conventional hemostasis, device quarantine |
| Overtemperature/smoke | Sensors and vision quality | Disable energy; stop autonomous motion | Suction/irrigation/manual response; assess fire/injury |
| Storage/logging exhaustion | Capacity/write integrity | Block new autonomous segment | Finish manually if clinically appropriate; seal partial record |
| Software/model/calibration mismatch | Signed manifest and compatibility checks | Refuse startup or disable capability | Install verified bundle only outside case; no ad-hoc override |

## Clinical contingencies

| Condition | Immediate robot behavior | Clinical fallback |
|---|---|---|
| Unexpected bleeding | Stop energy/motion in defined safe state; present unobstructed view | Surgeon controls hemostasis; convert if threshold met |
| Anatomy differs from plan | Freeze affected plan and boundary assumptions | Re-image/re-register or proceed conventionally |
| Tissue tears/perforation suspicion | Stop task and release only if validated safe | Surgeon assesses and repairs; trigger event review |
| Patient movement or table shift | Stop autonomy; invalidate registration as required | Stabilize, re-register, or convert |
| Physiologic/anesthesia instability | Stop/pause at predefined safe state | Anesthesia and surgical teams manage patient; abort/convert |
| Wrong patient/site/procedure signal | Prevent arming or stop before action | Restart clinical verification; report near miss |
| Sterile barrier breach | Stop affected interaction | Replace/re-drape/reprocess or abort per infection-control policy |
| Surgical fire risk/event | Immediate energy/gas behavior defined with OR policy | Team executes fire protocol and patient rescue |
| Loss of insufflation/access | Stop task and protect instruments/tissue | Restore access or convert |
| Unrecognized pathology | No improvisation or claim expansion | Clinician decides biopsy, alternate plan, or abort |
| Surgeon incapacitation | Stop at validated safe state | Credentialed backup assumes control or converts |

## Human-interface contingencies

- **Ambiguous authority:** motion is disabled until the controlling user is clear.
- **Conflicting commands:** safest authorized command wins; team resolves verbally.
- **Alarm overload:** prioritize by required action and suppress duplicates without
  hiding unresolved hazards.
- **Failed takeover:** independent emergency control stops actuation; bedside team
  uses manual release/conversion tools.
- **Operator confusion:** stop the segment; do not rely on training alone to cover a
  recurring interface hazard.

## Cybersecurity and data contingencies

- Suspected compromise: isolate interfaces, disable affected capability, preserve
  evidence, switch to verified conventional workflow, and activate response team.
- Invalid signature or unknown media: reject before installation or data import.
- Patient-data misassociation: stop before use, quarantine records, notify privacy
  and clinical owners, and assess affected cases/models.
- Training-data poisoning or provenance defect: quarantine datasets and derivative
  models, determine release impact, retrain/revalidate if needed.
- Vulnerability without immediate fix: risk-assess compensating controls, restrict
  features/sites, or remove the version from service.

## Program-level contingencies

| Trigger | Program action |
|---|---|
| Serious/unanticipated harm | Suspend affected study/capability; clinical care first; notify required authorities |
| Repeated near miss | Treat as a safety signal; pause promotion and investigate common cause |
| Endpoint failure | Do not tune on the test cohort and retry; reassess design/protocol |
| Supplier component change | Quarantine change until impact assessment and verification |
| Key clinical partner loss | Pause claims requiring their expertise/data; do not lower oversight |
| Funding/schedule pressure | Preserve safety/quality gates; reduce scope rather than evidence |
| Regulatory pathway changes | Reassess intended use, evidence, labeling, and release plan |
| Inability to service securely | Stop new deployments and plan controlled end-of-support/recall |

## Site emergency kit and drills

Each approved site maintains compatible manual release tools, conventional
instruments, emergency power, required visualization/access equipment, spare
verified instruments, contact tree, current conversion instructions, and incident
forms. Teams drill power loss, failed takeover, bleeding, fire, sterile breach,
instrument breakage, and conventional conversion before first use and periodically.

## After any contingency

1. stabilize and care for the patient/animal;
2. preserve device, instruments, media, logs, video, and configuration evidence;
3. record factual timeline and actions without editing original data;
4. assess adverse-event, ethics, privacy, and regulator reporting timelines;
5. quarantine affected assets and determine study/deployment pause;
6. perform multidisciplinary root-cause and risk reassessment;
7. implement corrective/preventive actions and verify effectiveness;
8. update labeling, training, design, tests, and playbooks;
9. resume only after documented approvals.

