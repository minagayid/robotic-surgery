# Swapping in Real ML Backends

Every heavy model in robotX sits behind an interface with a deterministic
**mock** backend, selected via `robotx.config.BackendConfig`. The mocks let the
whole pipeline run and be tested with only `numpy` + `pyyaml`. To use real
models, install the extras and register the real backend.

```bash
pip install -r requirements-ml.txt
```

## Backend map

| `BackendConfig` field | Interface (file) | Real model it stands in for |
|---|---|---|
| `hand_pose` | `HandPoseEstimator` (`preprocessing/extractors.py`) | MediaPipe Hands / FrankMocap / HaMeR |
| `egomotion` | `EgoMotionEstimator` | optical-flow VO / DROID-SLAM |
| `detector` + `tracker` | `ObjectTrackerDetector` | Grounding DINO (open-vocab) + SAM2 |
| `depth` | `DepthEstimator` | Depth-Anything-V2 |
| `action_seg` | `ActionSegmenter` | ActionFormer (temporal localization) |
| `captioner` | `LanguageGrounder` | LLaVA / Qwen-VL (VLM) |
| `encoder` | `VisualEncoder` (`retargeting/representation.py`) | R3M / VIP / VC-1 |
| `policy` | `VLAPolicy` (`learning/vla_policy.py`) | OpenVLA / Octo |
| `planner` | `HighLevelPlanner` (`learning/planner.py`) | an LLM |

## How to register a real backend

1. **Implement the interface.** For example, a MediaPipe hand-pose estimator:

   ```python
   # robotx/preprocessing/backends_mediapipe.py
   import mediapipe as mp
   from robotx.preprocessing.extractors import HandPoseEstimator
   from robotx.types import HandPoseTrajectory

   class MediaPipeHandPose(HandPoseEstimator):
       def estimate(self, stack) -> HandPoseTrajectory:
           ...  # run MediaPipe over stack.frames, return (T, 21, 3) joints
   ```

2. **Register it** in the relevant `_REGISTRY` (extractors) or `build_*` factory
   (encoder/policy):

   ```python
   from robotx.preprocessing import extractors
   extractors._REGISTRY["hand_pose"]["mediapipe"] = MediaPipeHandPose
   ```

3. **Select it** in config:

   ```yaml
   backends:
     hand_pose: mediapipe
   ```

Because everything communicates through the `robotx/types.py` contracts, this is
a strictly local change — no other layer needs to know.

## Suggested order of adoption

1. `encoder` (R3M/VIP/VC-1) — biggest single lever; enables real representation
   pretraining and meaningful near-dedup.
2. `hand_pose` — unlocks realistic kinematic retargeting.
3. `detector`/`tracker` + `depth` — better object grounding and 3D structure.
4. `policy` (OpenVLA/Octo) — the actual control model; needs real robot teleop
   demos to fine-tune, per the recipe in `docs/architecture.md`.
