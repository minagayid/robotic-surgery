# Surgical System Architecture

## Safety structure

```text
Clinical team and emergency controls
                 |
Patient/anatomy model -> task supervisor -> motion/energy proposal
                 |              |
                 +---- independent constraint monitor
                                |
                    real-time command arbiter
                                |
         instrument drives, energy devices, imaging, table
                                |
             hardwired safety controller / power isolation
```

The cognitive computer can propose but cannot override the constraint monitor,
real-time arbiter, drive safety functions, or hardwired emergency controls.

## Zones

### Sterile patient zone

Patient-contact instruments, drapes, sterile adapters, trocar/access interfaces,
irrigation/suction paths, and patient-side emergency release. Every component has
identity, lot/serial, use count, compatible procedure, and reprocessing status.

### Real-time actuation zone

Motor control, brakes, trajectory execution, force/torque/energy limiting,
collision monitoring, watchdogs, and safe-stop/withdrawal primitives. No general
language model or online learning executes here.

### Perception and planning zone

Endoscopic/stereo imaging, ultrasound or other approved imaging, instrument
tracking, anatomy estimation, workflow state, task policy, and motion planning.
All estimates include uncertainty, calibration identity, age, and source.

### Clinical interface zone

Surgeon console, displays, alarms, foot/hand controls, confirmation checkpoints,
team status, manual takeover, and conversion checklist. Controls must communicate
who has authority and what the robot will do next.

### Evidence and operations zone

Immutable event log, synchronized video/state, configuration manifest, maintenance
records, training status, complaint/adverse-event intake, and signed offline
update/rollback. Clinical records and engineering logs are separated according to
privacy and retention policy.

## Surgical state model

The world model extends the general Robotic Surgery scene graph with:

- patient and procedure identity confirmed through a clinical workflow;
- registered preoperative/intraoperative anatomy;
- critical structures, margins, safe corridors, and uncertainty volumes;
- tissue/contact state and estimated deformation;
- instruments, accessories, energy state, pose, force, temperature, and life;
- surgical phase, completed checkpoints, pending verification, and conversion state;
- physiologic interlock inputs supplied by approved clinical systems;
- visibility, smoke/fluids, occlusion, and contamination status.

No command is valid across patient registration, calibration, instrument, model,
or procedure-state changes.

## Command contract

Every surgical command contains:

- intended procedure segment and authorized autonomy level;
- target anatomy and protected-structure constraints;
- instrument/accessory and calibration identifiers;
- pose/force/speed/energy bounds;
- expected contact and tissue response;
- maximum duration and expiration timestamp;
- preconditions, completion criteria, and abort conditions;
- safe-stop or withdrawal behavior;
- issuing model/software version and approving clinician action.

The real-time arbiter rejects incomplete, stale, conflicting, or unauthorized
commands.

## Independence and diversity

- The primary planner and independent constraint monitor use separate code paths
  and, where practical, different sensing/algorithms for critical boundaries.
- Hardware travel, speed, torque, and energy limits remain below software limits.
- Emergency stop, brakes, and power removal work when the main computer is lost.
- A display or console failure cannot silently leave actuation enabled.
- Logging failure causes a defined capability reduction or procedure stop; it does
  not erase the event history already committed.

## Offline cybersecurity

The procedure network has no Internet route. Devices authenticate locally;
services are allowlisted; unused radios/ports are disabled; removable media is
controlled; bundles are signed; secrets live in protected hardware when
available; and the system supports vulnerability response and emergency rollback.
Offline status is verified before the sterile case starts.

The FDA treats cybersecurity as part of medical-device safety and quality-system
design, including premarket documentation:
<https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-management-system-considerations-and-content-premarket>.

