# Learning pipeline architecture

This is an offline research plumbing demo. Built-in source adapters return
mock references and the frame reader synthesizes RGB arrays. Perception,
representation, policy, and planner components are deterministic mocks. The
toy simulator is kinematic. No stage connects to a robot or establishes
performance on real video, hardware, or clinical tasks.

## Current end-to-end flow

```text
mock source references
  -> synthetic RGB frames and mock clip annotations
  -> provenance-label gate, filters, deduplication, manifest bookkeeping
  -> mock representation training
  -> weak mock retargeting records
  -> mock policy pretraining and optional robot-demo fine-tuning
  -> template planner
  -> randomized planar kinematic toy simulation
  -> follow-on simulation gate and travel-command cap
  -> simulation log and feedback bookkeeping
```

The provenance labels are fixtures, not evidence of license, consent, ethics
approval, or data-use rights. The license gate checks the labels in records;
it does not verify documents. The rollout's `simulation_only` marker and
success-rate gate catch API misuse; they are not a security boundary or a
hardware safety function. The simulator is not a validated physics model.

## Contracts and current limits

`ClipRecord` carries frames, pose/tracking/depth/action annotations, a language
label, provenance, and quality fields. These shapes allow plumbing among
pipeline stages. They do not imply those annotations came from real sensors or
validated perception. The bundled reader creates synthetic frames; no local
video decoder is present.

The retargeting stage produces weak records using mock pose inputs, not
calibrated target-robot kinematics. The encoder, policy, and planner are toy
implementations. Optional names in `BackendConfig` are placeholders: installing
the ML extras does not make those integrations available. See
[`backends.md`](backends.md).

The randomized simulator exercises control-flow and report contracts only.
The gripper closure fraction is a normalized travel-command cap, not a force or
torque limit. Its success score must not authorize hardware or clinical use.
The base reference runtime elsewhere in this repository is also a local
simulation; it has no hardware driver, validated robot model, deterministic
real-time loop, or independent safety controller.

## Research directions

Human-video perception and robot-action learning require separate evidence.
Real work needs lawfully acquired data, decoders and perception models tested
against appropriate ground truth, and a calibrated target robot model. Weak
retargeted records need comparison with true robot teleoperation data. Policy
evaluation needs a validated simulator plus bench and hardware-in-loop tests
for a specific configuration. A high-level planner should remain outside any
deterministic low-level control loop and have bounded, evaluated failure
behavior. None of those integrations or evidence is part of this demo.

## Extension boundary

Candidate interfaces live in `data/`, `preprocessing/extractors.py`,
`retargeting/representation.py`, and `learning/`. New adapters require explicit
registration, tests for contracts/failures, provenance and calibration
handling, and task-specific evaluation. Keep them in an offline workflow until
the robot, intended use, risk controls, and verification plan are defined.
