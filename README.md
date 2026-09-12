# RobotX OS

An offline-first robotics platform for learning human-like manipulation from
licensed first-person data and acting from a continuously fused spatial world
model.

> Status: planning and architecture. No component is yet approved for unattended
> or safety-critical operation.

This repository also contains a runnable, dependency-free host reference slice.
It is simulation-only: it does not connect to motors, surgical instruments,
patients, animals, networks, or real-time safety hardware.

## Run the local reference slice

From the repository root, with Python 3.10 or newer:

```powershell
python -m unittest discover -s tests -v
python -m robotic_os demo --json
python -m robotic_os five-heart-demo --json
python -m robotic_os spatial-4d-demo --mode normal --json
python -m robotic_os workcell-info --json
python -m robotic_os benchmark --iterations 1000
python -m robotic_os soak --iterations 10000 --fault-interval 1000
python -m robotic_os release-gate docs/production-gate-manifest.example.json --json
```

The demo exercises an approved command, a velocity-clamped command, an expired
command, and a tamper-evident local event journal. It reports
`simulation_only` and performs no external actions. Runtime code uses only the
Python standard library; `requirements.txt` is intentionally empty of packages.

Optional advisory text can use a local OpenAI-compatible server such as Ollama,
vLLM, llama.cpp, or another loopback service configured through
`ROBOTX_LOCAL_LLM_BASE_URL`. The client is not part of the motion runtime, and
its output has no authority over safety decisions or actuation.

## Mission

Build a modular robotics stack that can:

1. learn useful representations and task priors from large, legally sourced POV
   datasets;
2. adapt those priors to a specific robot using simulation and real robot data;
3. perceive geometry, motion, occupancy, and uncertainty through multiple sensor
   types;
4. plan and execute movement within hard physical safety limits; and
5. operate without an Internet connection in production.

The first product target is **one fixed robot, one controlled room, and a small
set of manipulation tasks**. General-purpose humanoid behavior is a research
direction, not the first milestone.

## What “OS” means here

RobotX OS is a complete robotics platform above a hardened Linux/real-time base.
It includes device abstraction, messaging, time synchronization, world state,
planning, control, learning, safety, observability, and signed offline updates.
It does not initially replace the computer kernel or hardware drivers.

## Design principles

- **Offline by default:** the robot runtime has no Internet route, cloud
  dependency, telemetry upload, or remote shell.
- **Safety outside AI:** a small independent safety controller can stop motion
  even when the main computer or learned policy fails.
- **Uncertainty is data:** every observation and map element carries confidence,
  age, and provenance.
- **Learn proposals, verify commands:** learned models suggest goals or short
  action chunks; deterministic constraints approve, clamp, or reject them.
- **Efficient by architecture:** low-rate semantic reasoning is separated from
  high-rate control, and sensors are processed only at the rate their information
  value requires.
- **Replaceable components:** stable typed contracts allow models, simulators,
  sensors, and robot bodies to change independently.
- **Hierarchical movement gate:** left/right arm and left/right leg processors
  validate independently, upper/lower coordinators aggregate their active
  members, and a main orchestrator admits only complete, mutually consistent
  bundles for the requested subset.
- **Early context compaction:** optional advisory context is compacted at a
  configurable 40–50% threshold (45% by default) before it can consume a large
  model window.

## Proposed system

```text
POV data + robot demos -> offline training -> signed model bundle
                                               |
RGB/depth + ultrasonic/mmWave/Wi-Fi evidence -> time sync -> modality adapters
                                           -> fused spatial world model
                                               |
Goal -> task planner -> four extremity processors -> upper/lower coordinators
                                                      -> main orchestrator
                                                      -> safety supervisor -> controller
                                               ^                                      |
                                               +----------- execution feedback -------+
```

See [Architecture](docs/ARCHITECTURE.md), [Sensor Fusion](docs/SENSOR_FUSION.md),
[Learning Plan](docs/LEARNING.md), [Security and Safety](SECURITY.md), and the
[Roadmap](ROADMAP.md). For the runnable boundary and its safety case, see
[Implementation](docs/IMPLEMENTATION.md) and
[Phase 1 safety case](docs/PHASE1_SAFETY_CASE.md). The offline surgical-data
inventory and ingestion controls are in the [dataset catalog](docs/DATASET_CATALOG.md).

## Surgical robotics program

RobotX Surgical is the proposed high-risk medical extension for human, dental,
and veterinary procedures. It is a clinician-led program that advances from
navigation and shared control to supervised task autonomy one validated
procedure segment at a time. It does not authorize patient or animal use.

Start with the [Surgical Program Charter](SURGICAL_PROGRAM.md), then review the
[medical architecture](docs/surgical/ARCHITECTURE.md),
[procedure portfolio](docs/surgical/PROCEDURE_PORTFOLIO.md),
[data and training plan](docs/surgical/DATA_TRAINING.md) and its
[public dataset catalog](docs/DATASET_CATALOG.md),
[validation pathway](docs/surgical/VALIDATION_CLINICAL.md),
[quality and regulatory plan](docs/surgical/REGULATORY_QUALITY.md),
[operating model](docs/surgical/OPERATIONS.md), and
[contingency playbook](docs/surgical/CONTINGENCY_PLAYBOOK.md).

Full-procedure autonomy is a long-term research objective, not the first product.
Every clinical capability must have a named supervising clinician, bounded
intended use, evidence package, takeover path, and conventional fallback.

## Relationship to existing projects

- [`robotX`](https://github.com/minagayid/robotX) is the seed for compliant POV
  acquisition, `ClipRecord`, human-to-robot retargeting, VLA interfaces,
  simulation gates, and failure feedback.
- [`TouchAir`](https://github.com/minagayid/TouchAir) is the seed for spatial
  event contracts, tracked object state, confidence gating, and temporal gesture
  stabilization.
- `spatial-mesh` is intended to inform wave-based spatial mapping, but it was not
  accessible while this plan was prepared. Integration waits for an interface
  and license review.

These repositories remain independent during Phase 0. Reuse happens through
documented interfaces or extracted packages, not by copying entire codebases.

## First demonstrator

The recommended first demonstrator is tabletop pick-and-place:

- one 6/7-DoF arm and simple gripper;
- fixed RGB-D camera, wrist camera, joint/force telemetry, and one ultrasonic or
  mmWave safety sensor;
- three known objects in a controlled workcell;
- “pick object A and place it in zone B”;
- offline operation, physical emergency stop, speed/force limits, and automatic
  abort on stale or contradictory perception.

Success means at least 90% completion across a held-out test layout, zero safety
limit violations, and reproducible recovery from expected perception failures.

The current code implements a host-side safety/reference slice behind this
demonstrator. The `robotx-reference-four-extremity-v1` profile now fixes the
simulation, coordinate frames, rates, compute target, and no-hardware policy.
Every accepted command also passes an independent final safety-gate model, and
versioned telemetry can be written for local replay or downstream ingest.
These are SIL/reference controls, not hardware drivers or clinical capabilities.
The package now also includes expiry-aware calibration manifests, a single
fail-closed actuator/HAL injection point, a ROS2 message-shape contract with no
runtime binding, a process-isolated safety-worker prototype, and a deterministic
long-duration soak/fault harness. Hardware-in-loop integration remains a
separate phase requiring the selected robot, sensors, certified safety
controller, and independent verification evidence.

The `release-gate` command evaluates those external production prerequisites
and fails closed when any evidence is missing or tampered. It can report
eligibility for independent production review, but never grants production or
clinical approval itself. See [Production gates](docs/PRODUCTION_GATES.md).

The `spatial-4d-demo` command exercises the offline 360-degree reference slice.
It fuses timestamped multimodal evidence into observed and inferred moving
entities, records unknown/contradictory sectors, applies ECO/NORMAL/DEGRADED
emission policy, and exposes a legacy safety snapshot for the movement gate.
The four extremity processors can be activated selectively; omitted limbs remain
at their current positions and do not receive a sequence commit. See the
[360 4D plan](docs/SRV_4D_PLAN.md) and
[`robotic_os/spatial_4d.py`](robotic_os/spatial_4d.py).

## Repository policy

This planning repository contains no training data, credentials, private model
weights, or hardware secrets. Future implementation repositories should use
signed releases, dependency lockfiles, reproducible builds, and a documented
software bill of materials.
