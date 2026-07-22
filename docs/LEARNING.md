# Data and Learning Plan

## Key correction

Large POV video can teach visual representations, object affordances, temporal
structure, and useful task priors. It does **not** directly provide robot joint
commands, forces, gripper state, accurate metric depth, or the robot's embodiment
constraints. Human-like movement therefore requires a staged bridge, not direct
imitation.

## Dataset layers

1. **Human POV:** licensed or first-party video with provenance, privacy redaction,
   action segments, hand/object tracks, camera motion, language, and quality.
2. **Simulation:** robot-state/action trajectories across randomized geometry,
   lighting, friction, mass, latency, and sensor noise.
3. **Teleoperation:** high-quality demonstrations on the exact robot embodiment.
4. **Autonomous experience:** successes, interventions, aborts, near misses, and
   recovery attempts from gated deployment.

Keep immutable manifests that bind every sample to consent/license status,
processing version, sensor calibration, robot configuration, and train/validation
split. Do not place datasets in Git.

## Training recipe

1. Pretrain perception/representation models on compliant POV data.
2. Learn hand-object interaction and temporal affordances.
3. Produce weak retargeted trajectories only as auxiliary supervision.
4. Train in simulation with the target robot's kinematics and constraints.
5. Fine-tune on teleoperated robot demonstrations.
6. Apply offline reinforcement or preference learning only from reviewed logs.
7. Distill/quantize a bounded inference model for the target computer.
8. Sign the model, configuration, evaluation report, and compatibility manifest as
   one deployment bundle.

## Model separation

- **Perception models** estimate objects, hands, depth, motion, and affordances.
- **Task model** decomposes goals at low frequency and may be a local VLM/LLM.
- **Policy model** proposes short action chunks conditioned on robot state.
- **Motion planner/controller** enforces robot geometry and timing.
- **Safety system** remains deterministic and independently testable.

No language model belongs in the servo loop.

## Evaluation gates

A model cannot advance only because average task success improves. Its release
report must include:

- held-out task success with confidence intervals;
- collision, limit-clamp, emergency-stop, and human-intervention rates;
- performance by object, lighting, layout, operator, and sensor-degradation slice;
- worst-case and p95 inference latency, memory, power, and thermal behavior;
- calibration sensitivity and out-of-distribution detection;
- deterministic replay of all failures and comparison with the previous release.

The initial acceptance target is set per demonstrator in the roadmap. Any safety
regression blocks release regardless of average success.

## Data governance

- Use official APIs, research datasets with compatible terms, creator licenses,
  or first-party capture.
- Preserve provenance and deletion/withdrawal capability.
- Redact bystanders and identifiers before long-term storage.
- Separate raw, curated, training, and evaluation stores.
- Require human review for unsafe-action filtering and dataset split leakage.
- Document model licenses and redistribution restrictions in the bundle manifest.

