# Surgical Robot Hardware Requirements

> **Controlled planning baseline — not a build authorization or instructions for
> patient use.** Release requirements must be derived from a named intended use,
> hazard analysis, usability work, applicable standards, and regulator feedback.
> Values marked **TBR** are “to be resolved” in the procedure dossier. A passing
> research prototype is not a medical device authorization.

## 1. Intended platform

RobotX Surgical is a modular, surgeon-controlled system for research and eventual
procedure-specific authorization. The reference system contains:

1. a surgeon console with stereoscopic display, two master controllers, clutch,
   mode controls, and guarded energy pedals;
2. a medical compute and visualization cart;
3. an independent real-time safety and power-control unit;
4. one visualization arm and two or three instrument/assistant arms on locked
   mobile bases;
5. sterile adapters, drapes, instruments, endoscopes, and approved third-party
   energy/fluid accessories; and
6. manual release tools and conventional-conversion equipment.

This is a platform architecture, not a claim that one configuration can perform
every surgery. Each release is one locked cell in the capability matrix:

```text
procedure × segment × anatomy/site × patient/species population
× arm arrangement × instrument/accessory set × imaging/sensor set
× autonomy level × trained user × operating environment
```

## 2. Reference configurations

| Configuration | Physical setup | Initial permitted role | Separate evidence required |
|---|---|---|---|
| Multi-port minimally invasive | 3–4 bedside arms, trocar/remote-center constraints, stereo endoscope | S1 navigation and S2 teleoperation/shared control | Every procedure, port plan, population, instrument and energy set |
| Open/cooperative | 1–2 force-sensing arms holding a clinician-selected instrument | Instrument stabilization and constrained cooperative motion | Each specialty, instrument family and access corridor |
| Microsurgical | Short-reach low-inertia arms, microscope integration, fine master scaling | Tremor filtering and motion scaling | Anatomy, optical chain, force envelope and instrument set |
| Rigid-anatomy dental/orthopedic | Rigid guide/drill arm plus registered imaging and hard depth/trajectory limits | Navigation and shared-control alignment | Site, imaging, registration, drill/bur and implant system |
| Endoluminal/transoral | Flexible or narrow-shaft instrument module with scope tracking | Visualization and navigation first | Access path, flexible instrument, insufflation/fluid and tissue model |
| Veterinary | Species- and size-specific version of one configuration above | Same or lower autonomy as the validated model | Species, weight range, anatomy, procedure and facility |

The first hardware program should implement only the multi-port research bench and
one cooperative arm. Flexible endoluminal, microsurgical, dental/orthopedic, and
veterinary variants remain separate design projects until their procedure dossiers
are approved.

## 3. System-level design inputs

| ID | Requirement | Verification |
|---|---|---|
| HWR-SYS-001 | The system shall boot only a signed, compatible hardware/software/model/calibration manifest and shall record its identity in the case log. | Negative compatibility tests; signature and rollback tests |
| HWR-SYS-002 | No patient-side motion or energy shall be possible until the responsible operator, procedure configuration, instruments, calibration, sterile status, and emergency controls are confirmed. | State-machine and simulated-use tests |
| HWR-SYS-003 | The clinical runtime shall operate without an Internet route and shall not depend on a cloud service for essential performance. | Network isolation and loss-of-network tests |
| HWR-SYS-004 | A safety controller independent from the planning computer shall supervise motion enable, drive health, command age, speed, force/torque, workspace, collision, energy permission, emergency controls, and safety communications. | Independence review; fault injection; common-cause analysis |
| HWR-SYS-005 | Loss of the console, display, planning computer, control network, tracking, or command stream shall produce the instrument-specific validated safe state without uncontrolled motion or energy. | Single- and multiple-fault tests |
| HWR-SYS-006 | Safe state shall be specified per instrument and task as hold/brake, de-energize, compliant release, or clinician-directed withdrawal; automatic retraction shall not be a universal response. | Hazard trace and scenario tests |
| HWR-SYS-007 | Hardware travel, velocity, torque, temperature, and energy limits shall remain effective when application software is unavailable. | Boundary and power-cycle tests |
| HWR-SYS-008 | The bedside team shall be able to stop all hazardous output and mechanically release or move each patient-side arm using a validated method after loss of main power. | Timed simulated-use test in worst-case pose |
| HWR-SYS-009 | The system shall prevent arm, table, staff, patient, and cable collisions within the validated sensing envelope and shall stop when the envelope is unknown. | Geometric, sensor-degradation, and occlusion tests |
| HWR-SYS-010 | One fault shall not silently enable motion or energy; redundant channels shall be sufficiently independent for the risk-control claim they support. | FMEA, FTA/STPA, schematic and software review |
| HWR-SYS-011 | Essential functions shall meet specified behavior during normal power, brownout, loss of mains, emergency power transfer, thermal stress, and electromagnetic disturbance. | Electrical safety, EMC, thermal and power-transfer tests |
| HWR-SYS-012 | All safety-critical events shall be time-synchronized, append-only, integrity checked, and recoverable after a crash. | Power-pull, storage-full and replay tests |

## 4. Patient-side carts and arms

| ID | Requirement | Verification |
|---|---|---|
| HWR-ARM-001 | Each mobile base shall have a low center of gravity, transport and operating modes, positive wheel locks, cable management, and a stability margin for the worst allowed arm pose and applied load. | Tip/stability test in all required orientations |
| HWR-ARM-002 | Base lock status shall be directly sensed; surgical motion shall be inhibited if required locks or floor contact are not confirmed. | Sensor bypass and partial-lock tests |
| HWR-ARM-003 | Each proximal arm shall provide sufficient degrees of freedom to place and orient the instrument interface while avoiding singularities and maintaining the prescribed access constraint. | Workspace and singularity map |
| HWR-ARM-004 | Actuated joints shall use absolute or retained position sensing plus an independent plausibility channel where loss of position could cause unacceptable risk. | Encoder disagreement and restart tests |
| HWR-ARM-005 | Each gravity-loaded axis shall have a power-off holding strategy and a controlled manual-release method that does not drop the arm or load the patient. | Rated-load brake and release tests |
| HWR-ARM-006 | Pinch, crush, shear, entanglement, and trapping hazards shall be designed out where practical and otherwise guarded, detected, labeled, and validated with representative users. | Mechanical inspection and usability validation |
| HWR-ARM-007 | Surfaces near the sterile field shall be compatible with the specified cleaning/disinfection agents and shall not shed, flake, corrode, or expose absorbent seams over claimed life. | Material compatibility and accelerated-life tests |
| HWR-ARM-008 | Manual positioning shall be gravity compensated and intentionally enabled; releasing the enable control shall return the arm to a stable state. | Simulated-use and stuck-control tests |
| HWR-ARM-009 | The arm shall provide service access without exposing calibration or safety adjustments to clinical users. | Service and misuse inspection |
| HWR-ARM-010 | Arm reach, payload, joint torque, stiffness, backlash, repeatability, speed, and thermal limits shall be defined for each configuration using the design-budget method in `ROBOT_AND_EXTREMITIES_DESIGN.md`. | Requirements trace and worst-case test |

## 5. Access constraint and distal extremity

For a minimally invasive instrument, the “extremity” is a controlled chain:

```text
proximal arm → access/remote-center alignment → sterile adapter
→ instrument drive unit → shaft/cannula → distal wrist → end effector
```

| ID | Requirement | Verification |
|---|---|---|
| HWR-EXT-001 | The access constraint shall be implemented by a documented mechanical, kinematic, or hybrid remote-center design and independently monitored. | Pivot-error mapping under load |
| HWR-EXT-002 | The system shall bound lateral load and motion at the access site and stop on loss of the access constraint. | Instrumented port/fixture testing |
| HWR-EXT-003 | The instrument shall be keyed against incorrect insertion, orientation, incomplete latch, and incompatible drive coupling. | Misassembly and forced-error tests |
| HWR-EXT-004 | Instrument identity, lot/serial, type, dimensions, sterile/reprocessing state, calibration, software compatibility, and remaining use life shall be verified before enable. | Database, spoofing, expired-life and offline tests |
| HWR-EXT-005 | Each drive channel shall detect commanded-versus-measured motion disagreement, cable/tendon slip or breakage where applicable, stall, overtravel, and excessive load. | Fault-seeded instruments and endurance tests |
| HWR-EXT-006 | The sterile adapter and drape shall provide a validated barrier while transmitting only the intended mechanical, optical, electrical, or fluid interfaces. | Barrier integrity and simulated-use tests |
| HWR-EXT-007 | Tool jaws/blades/needles and any detachable component shall remain retained over worst-case use and reprocessing life, with a defined detection and retrieval response for breakage. | Retention, fatigue, misuse and inspection tests |
| HWR-EXT-008 | The distal mechanism shall have defined position, force, temperature, and energy error budgets at the working tip rather than only at the motors. | Tip-level metrology under representative load |
| HWR-EXT-009 | The instrument shall support a clinician-controlled release method for grasped tissue or a trapped object after loss of power. | Timed release test under worst-case load |
| HWR-EXT-010 | Reusable lumens, joints, crevices, and disassemblies shall be designed for validated cleaning and sterilization; inaccessible soil traps are prohibited. | Design inspection and worst-case reprocessing validation |

## 6. Instrument and accessory classes

Each instrument is its own controlled device/accessory record. No generic
“surgical tool” permission is allowed.

| Class | Examples | Additional controls |
|---|---|---|
| Visualization | Stereo endoscope, microscope camera, ultrasound probe | Image age/quality, calibration, thermal/light output, fog/smoke detection |
| Atraumatic manipulation | Grasper, forceps, retractor | Jaw force, slip, crush limit, release after power loss |
| Cutting/dissection | Scissors, cold blade, dissector | Edge retention, closing/shear load, fragment containment |
| Needle/suture | Needle driver, clip applier, stapling accessory | Needle/clip presence, closing force, firing lockout, count support |
| Energy | Monopolar/bipolar/RF/ultrasonic/laser-compatible holder | Independent enable, guarded pedal, return-path/accessory checks, time/temperature limits |
| Fluid/field management | Suction, irrigation, smoke evacuation | Pressure/flow bounds, occlusion, cross-connection prevention |
| Rigid drilling/guidance | Drill/bur guide, implant driver | Registration confidence, hard depth/trajectory stop, runout, heat and debris controls |

RobotX should initially integrate legally marketed energy and imaging devices
through approved interfaces rather than designing generators, anesthesia,
insufflation, or medication-delivery systems into the first platform.

## 7. Sensing and metrology

| ID | Requirement | Verification |
|---|---|---|
| HWR-SNS-001 | Every safety-relevant sensor sample shall carry source, synchronized timestamp, sequence, calibration ID, health, and uncertainty. | Interface conformance and stale-data tests |
| HWR-SNS-002 | Joint position and drive current/torque shall be sampled at a rate justified by the control and hazard analysis; asynchronous or stale data shall not be treated as current. | Timing and overload test |
| HWR-SNS-003 | Tip force estimation shall not rely on motor current alone when friction, tendon hysteresis, or external shaft contact can mask tissue load. | Comparative force testing |
| HWR-SNS-004 | Registration and tool tracking shall expose target registration error, tracking residuals, field coverage, age, and invalidation conditions to the safety supervisor. | Displacement, occlusion and distortion tests |
| HWR-SNS-005 | Cameras shall report frame age, drop rate, calibration, exposure/occlusion, and optical-chain state; frozen imagery shall be detected. | Frozen/replayed/delayed frame tests |
| HWR-SNS-006 | Safety functions shall define which sensors are independent and which share power, clock, optics, computation, communication, or calibration. | Dependency and common-cause analysis |

## 8. Surgeon console and team controls

| ID | Requirement | Verification |
|---|---|---|
| HWR-HMI-001 | The console shall continuously show controlling user, mode/autonomy level, armed instruments, selected energy source, active limits, alarms, and whether motion is enabled. | Human-factors validation |
| HWR-HMI-002 | Master controls shall use deliberate enable/clutch behavior, neutral-state checks, motion scaling, tremor filtering, and bounded mapping to the selected instrument. | Mapping, clutch and stuck-input tests |
| HWR-HMI-003 | Mode, arm, instrument, or energy selection shall require unambiguous feedback and shall not change on a single accidental action. | Use-error testing |
| HWR-HMI-004 | Energy activation shall be guarded and independently gated by the valid instrument, accessory, operator input, task state, and safety controller. | Cross-pedal and stuck-pedal tests |
| HWR-HMI-005 | A second emergency stop shall be accessible at the patient side; emergency controls shall be visible, consistent, and operable with gloved hands. | Reach and simulated-emergency tests |
| HWR-HMI-006 | Loss, freezing, severe delay, or mismatch of the operative display shall disable new hazardous motion/energy and cause a distinct alarm. | Display-path fault injection |
| HWR-HMI-007 | Alarm priority shall map to a required action and time; duplicate alarms may be grouped but unresolved hazards shall not be hidden. | Alarm-system and simulated-use tests |

## 9. Performance budget template

Do not copy a competitor’s number or use the same number for every procedure.
Complete this table for each locked configuration. The **research bench target**
column is an engineering starting point for the multi-port phantom rig, not a
clinical performance claim.

| Parameter | Research bench target | Release value/owner |
|---|---:|---|
| Proximal joint servo update | ≥ 1 kHz, deterministic | TBR — controls/safety |
| Independent safety sampling | ≥ 1 kHz for motion channels | TBR — safety |
| Fresh command lifetime | ≤ 20 ms before rejection | TBR — timing hazard analysis |
| Master-input-to-drive-command latency | p99 ≤ 20 ms | TBR — controls/human factors |
| Motion-to-photon latency | p99 ≤ 100 ms | TBR — imaging/human factors |
| Instrument-tip repeatability, unloaded | ≤ 0.5 mm for general MIS bench | TBR — procedure/metrology |
| Absolute tip accuracy after registration | ≤ 1.0 mm for general MIS bench | TBR — procedure/clinical |
| Access-point lateral deviation | ≤ 1.0 mm on rigid phantom | TBR — access model/clinical |
| Force sensing range/resolution/bandwidth | Set from tissue/tool tests; no universal value | TBR — instrument owner |
| Maximum tip/jaw force and speed | Instrument- and tissue-specific | TBR — clinical/risk |
| Workspace and reach | Procedure layout + margin without unsafe singularity | TBR — mechanical/clinical |
| Payload | Instrument + adapter + cable loads + margin | TBR — mechanical |
| Manual release time | Scenario-specific proficiency target | TBR — human factors/clinical |
| Backup-power hold/controlled-stop time | Sufficient for validated safe state and release | TBR — electrical/clinical |

All thresholds require measurement uncertainty, environmental conditions,
instrument life state, load state, pass/fail rule, and statistical confidence.
Average performance cannot hide a harmful tail.

## 10. Electrical, EMC, thermal, and environmental requirements

- Separate medical-grade mains entry, protective earth, isolation, leakage-current
  control, equipotential provisions where required, and a documented applied-part
  classification shall be developed under the applicable IEC 60601 framework.
- Energy-device interfaces, imaging systems, tables, insufflators, pumps, and
  hospital IT are system interaction conditions and require compatibility testing.
- Cooling shall not direct unfiltered exhaust into the sterile field or create
  unacceptable noise, vibration, smoke movement, or thermal contact hazards.
- Temperature sensors and independent cutoffs shall protect motors, drives,
  instruments, optical sources, batteries, skin-contact surfaces, and drapes.
- The device shall be tested for the claimed OR temperature, humidity, altitude,
  vibration, shock, transport, storage, ingress/cleaning, and electromagnetic
  environment.
- Batteries/UPS shall be replaceable and health monitored under controlled service;
  a failed battery shall not create an uncontrolled arm drop or energy output.

## 11. Sterility, biocompatibility, and reprocessing

1. Classify every patient-contacting material by contact nature and duration.
2. Freeze the exact material, colorant, lubricant, adhesive, residue, cleaning
   agent, and manufacturing process before biocompatibility evaluation.
3. Separate non-sterile reusable capital equipment, disinfected surfaces,
   sterilizable reusable adapters/instruments, and sterile single-use components.
4. Validate worst-case soil, drying time, disassembly, cleaning, rinsing, drying,
   inspection, packaging, sterilization, storage, maximum cycles, and functionality.
5. Prevent the system from accepting an expired, over-cycled, incompatible, or
   unverified instrument; no service override is available during a case.
6. Treat drapes and sterile adapters as safety-critical interfaces with barrier,
   fit, tear, particle, and coupling requirements.

## 12. Verification and acceptance hierarchy

| Level | Required evidence |
|---|---|
| Component | Material certificates, dimensions, surface finish, calibration, electrical and mechanical characterization |
| Subassembly | Joint/drive endurance, brake and release, cable/tendon life, thermal, ingress/cleanability, fault response |
| Arm/cart | Workspace, payload, accuracy/repeatability, stability, collision, manual handling, transport, power loss |
| Instrument | Tip metrology, force/energy/fluid behavior, retention, use life, cleaning/sterilization, packaging |
| Integrated system | Timing, EMC, electrical safety, interaction conditions, alarms, state machine, common-cause faults |
| Simulated use | Representative team, room, draping, docking, operation, tool changes, emergencies, conversion, reprocessing |
| Procedure configuration | Anatomical model, worst-case population, clinical workflow, endpoints and locked configuration |

## 13. Standards and regulatory baseline

Confirm editions and jurisdictional recognition for the actual submission:

- IEC 80601-2-77:2019 + AMD1:2023 for robotically assisted surgical equipment;
- IEC 60601-1 and applicable collateral/particular standards;
- ISO 14971 risk management; ISO 13485 quality management;
- IEC 62304 software life cycle; IEC 62366-1 usability engineering;
- IEC 81001-5-1 and applicable regulator cybersecurity guidance;
- ISO 10993 series for biocompatibility;
- applicable sterilization, aseptic processing, packaging, reprocessing, laser,
  radiation, energy-device, and clinical-investigation standards.

As of July 2026, FDA recognition 6-510 covers IEC 80601-2-77 Edition 1.1
(2019 + AMD1:2023), and the older recognition has a transition period ending
July 2, 2028. FDA’s current modular electromechanical surgical-system
classification describes a surgeon console, multiple fully positionable bedside
units/arms, instruments, and accessories. These sources support the architecture;
they do not determine RobotX’s final classification or clearance pathway.

## 14. Primary references

- [FDA recognition 6-510 — IEC 80601-2-77 Edition 1.1](https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfstandards/detail.cfm?standard__identification_no=46090)
- [IEC 80601-2-77 publication page](https://webstore.iec.ch/en/publication/29933)
- [FDA modular electromechanical surgical system classification (SCV)](https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpcd/classification.cfm?ID=SCV)
- [FDA overview of computer-assisted surgical systems](https://www.fda.gov/medical-devices/surgery-devices/computer-assisted-surgical-systems)
- [FDA EMC guidance for medical devices](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/electromagnetic-compatibility-emc-medical-devices)
- [FDA reusable-device reprocessing guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/reprocessing-medical-devices-health-care-settings-validation-methods-and-labeling)
