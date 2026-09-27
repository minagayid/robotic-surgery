# Architecture

robotX turns egocentric human video into robot manipulation policies through six
layers. Each layer is an independent package under `src/robotx/`; they
communicate only through the typed contracts in `robotx/types.py`, so any single
component can be replaced without disturbing the rest.

## End-to-end data flow

```
                        ┌──────────────────────────── Layer 1: data/ ───────────┐
 official APIs ─┐       │ VideoSource.fetch() → VideoRef(+Provenance)            │
 research sets ─┤──────▶│ (license status stamped at the source)                │
 licensed  ─────┤       └───────────────────────────────────────────────────────┘
 first-party ───┘                         │  list[VideoRef]
                                          ▼
                        ┌──────────────────────────── Layer 2: preprocessing/ ──┐
                        │ read → segment_shots → sample_frames(2-8 fps)          │
                        │ → QualityFilter → PrivacyRedactor → extractors         │
                        │   {hand pose, ego-motion, tracks, depth, actions, cap} │
                        │ → ClipRecord                                           │
                        └───────────────────────────────────────────────────────┘
                                          │  list[ClipRecord]
                     ┌────────────────────┼─────────────────────────┐
                     ▼                    ▼                          ▼
        ┌─ Layer 6: ops/ ──┐   ┌─ Layer 3: retargeting/ ─┐  (curation happens first:
        │ LicenseGate      │   │ A. VisualEncoder        │   license gate → safety/bias
        │ safety+bias      │   │    (R3M/VIP/VC-1)        │   filters → near-dedup →
        │ filters          │   │ B. KinematicRetargeter  │   manifest version bump)
        │ near-dedup       │   │    → PseudoDemonstration │
        │ manifest version │   └─────────────────────────┘
        └──────────────────┘                │  weak pseudo-demos + encoder
                     │                       ▼
                     │          ┌─ Layer 4: learning/ ────────────────────────┐
                     │          │ RepresentationTrainer (self-supervised)      │
                     │          │ VLAPolicy.pretrain(pseudo) .finetune(teleop) │
                     │          │ HighLevelPlanner.plan(goal) / .replan()      │
                     │          └──────────────────────────────────────────────┘
                     │                       │  trained policy
                     │                       ▼
                     │          ┌─ Layer 5: sim2real/ ─────────────────────────┐
                     │          │ SimValidator (domain randomization)          │
                     │          │ SafetyEnvelope (clamp speed/force, kill sw.)  │
                     │          │ StagedRollout (gated on sim success)          │
                     │          └──────────────────────────────────────────────┘
                     │                       │  RolloutLog (success/failure)
                     └───────────◀───────────┘  FeedbackLoop folds failures back
```

## The `ClipRecord` contract

`ClipRecord` is the pipeline's spine. It realizes the design's per-clip record —
`{frames, hand_pose_traj, object_tracks, depth, camera_pose, language_label}` —
plus provenance, action segments, and a quality score. Because every layer after
preprocessing reads and writes only this type (and the retargeting/learning
types derived from it), swapping a perception backend is a local change.

## Why the human→robot gap needs two approaches (Layer 3)

Human video contains **no robot actions**. robotX addresses this exactly as the
research literature does:

- **A — Representation learning** (`retargeting/representation.py`): train a
  visual encoder on the human video, self-supervised, so the robot's vision
  backbone already understands grasping/pouring. The policy then needs far fewer
  real robot demos. (R3M / VIP / VC-1.)
- **B — Kinematic retargeting** (`retargeting/kinematic.py`): map the estimated
  human wrist/finger trajectory onto the robot end-effector to produce a
  *pseudo-demonstration*. It is noisy (monocular pose, no depth ground truth), so
  it is flagged `weak=True` and used only for pretraining / auxiliary loss —
  never as ground-truth robot actions.

## Learning recipe (Layer 4)

Directly imitating human-video actions does not transfer reliably, so:

1. **Pretrain** the VLA on the human-video representations + weak pseudo-demos.
2. **Fine-tune** on a smaller set of real robot teleop trajectories (ground
   truth), which the feedback loop keeps growing.
3. A **separate, lower-frequency planner** (VLM/LLM) decomposes high-level goals
   into atomic subtasks and replans on failure — kept out of the tight control
   loop.

## Extending

- Add a perception backend: implement the relevant interface in
  `preprocessing/extractors.py` (or `retargeting/representation.py`), register it,
  and select it in `BackendConfig`. See [`backends.md`](backends.md).
- Add a data source: subclass `robotx.data.sources.VideoSource` and stamp
  `Provenance` with the correct `LicenseStatus`.
