# Roadmap

Dates should be assigned only after target robot, budget, team, and available
compute are known. Progress is gate-based rather than calendar-based.

## Phase 0 — Decisions and measurements

**Goal:** remove foundational uncertainty before merging codebases.

- Select one robot, gripper, workcell, and three tabletop tasks.
- Inventory compute, power, thermal, latency, and sensor budgets.
- Benchmark middleware candidates and local inference runtimes.
- Define contracts, coordinate frames, clock requirements, and log format.
- Inspect `spatial-mesh`; decide whether to reuse, extract, or retire it.
- Produce hazard analysis, data governance rules, and evaluation protocol.

**Exit gate:** approved architecture decision records, bill of materials, baseline
latency measurements, and a reviewed safety concept.

## Phase 1 — Deterministic skeleton

**Goal:** move only in simulation using typed contracts and replayable logs.

- Device simulators, message bus, health service, event log, and replay.
- Robot model, kinematics, trajectory controller, and command expiry.
- Independent safety-controller prototype and heartbeat protocol.
- CI that works from a pinned dependency mirror without Internet access.

**Exit gate:** 24-hour simulated soak with no deadline/safety invariant failure;
recorded sessions replay to equivalent decisions.

The current repository includes a smaller host-reference slice for this phase:
typed contracts, fail-closed proposal checks, a deterministic simulator, local
event journaling, a demo, and fault-focused tests. It is not the full Phase 1
exit gate and does not provide hard real-time or hardware evidence.

## Phase 2 — Spatial world model

**Goal:** build a reliable local model before learned control.

- Integrate robot state, RGB-D, wrist camera, and force/torque.
- Add sonar or mmWave as redundant proximity/motion evidence.
- Implement calibration registry, time alignment, occupancy, tracking, and scene
  graph with uncertainty.
- Run sensor dropout, contradiction, and calibration-shift experiments.

**Exit gate:** no missed test obstacle in the restricted workcell; defined safe
degradation for every injected sensor fault. Exact numerical thresholds are set
from Phase 0 measurements.

## Phase 3 — Classical manipulation baseline

**Goal:** prove the full safe path without learning from POV data.

- Known-object detection, grasp library, motion planning, collision checking.
- Supervised tabletop pick-and-place on hardware at reduced speed/force.
- Automatic abort, reset procedure, and failure taxonomy.

**Exit gate:** at least 95% success on the fixed training layout, zero safety-limit
violations, and all failures reproducible from logs.

## Phase 4 — POV representation learning

**Goal:** show that POV pretraining improves a measurable baseline.

- Connect robotX compliant data pipeline and real perception backends.
- Pretrain representations/affordances; keep retargeted actions weak-labeled.
- Collect target-robot teleoperation demonstrations.
- Compare scratch, generic pretrained, and POV-pretrained policies on held-out
  objects/layouts using the same evaluation harness.

**Exit gate:** statistically credible improvement over the Phase 3/general
pretraining baseline with no latency or safety regression.

## Phase 5 — Learned short-horizon control

**Goal:** permit bounded learned proposals under deterministic supervision.

- Add local policy inference, OOD/uncertainty signal, and motion-proposal adapter.
- Validate in randomized simulation and hardware-in-loop fault scenarios.
- Run supervised hardware trials and feed interventions/failures back to training.

**Exit gate:** at least 90% on held-out demonstrator layouts, zero safety-limit
violations, bounded p95 latency on target hardware, and successful recovery from
the agreed fault suite.

## Phase 6 — Offline productization

**Goal:** operate and update the system securely without Internet connectivity.

- Reproducible build, local package/model mirror, SBOM, signed A/B bundles.
- Secure boot/full-disk protections where hardware permits.
- Installer, rollback, backup/restore, audit log, and recovery drills.
- Performance profiling, pruning/quantization, thermal and power validation.

**Exit gate:** clean-room rebuild and deployment from documented offline media;
rollback and disaster recovery demonstrated.

## Research track — Wi-Fi CSI

Run separately from the critical path. Establish lawful hardware/firmware access,
collect controlled ground truth, characterize generalization between rooms, and
compare incremental value over RGB-D/radar/sonar. Promote it only if it improves a
defined metric and has a documented failure envelope; never make it the sole
collision-safety input.

## Immediate next actions

1. Choose the target robot/workcell and available compute.
2. Restore or grant access to `spatial-mesh` for technical review.
3. Write five Phase 0 architecture decision records: middleware, base OS,
   simulator, world representation, and model runtime.
4. Build the sensor timing/latency bench before selecting fusion algorithms.
5. Create the first hazard log and tabletop evaluation scenario pack.

## Surgical extension

The surgical program runs as a separately governed medical-device workstream.
Its stages do not inherit approval from the general robotics roadmap:

1. establish a medical quality system, clinical governance board, intended-use
   statements, and procedure-specific hazard files;
2. build a research-only surgical bench with synthetic tissue, force sensing,
   stereo/endoscopic imaging, instrument tracking, and deterministic replay;
3. deliver navigation, camera control, tremor filtering, and virtual fixtures
   under continuous surgeon control;
4. validate bounded autonomous tasks such as needle positioning or camera
   alignment on phantoms and approved ex-vivo/cadaver models;
5. enter clinical investigation only after independent technical, clinical,
   ethics, quality, and regulatory approvals; and
6. expand one procedure, anatomy, instrument set, and population at a time.

See [`SURGICAL_PROGRAM.md`](SURGICAL_PROGRAM.md) for the full program and its
contingency gates.
