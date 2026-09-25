# Backend status and future integration points

The pipeline currently ships deterministic mock implementations only. The
model names in `BackendConfig` and this page are research candidates, not
working adapters. Installing `requirements-ml.txt` does not activate them.
Selecting an unregistered backend raises `NotImplementedError`; the pipeline
must not be treated as ingesting real video, extracting real perception, or
training a real robot policy.

| Component | Interface | Candidate to evaluate later | Current implementation |
|---|---|---|---|
| Hand pose | `HandPoseEstimator` (`preprocessing/extractors.py`) | MediaPipe Hands, HaMeR | Deterministic mock |
| Ego-motion | `EgoMotionEstimator` | Optical-flow VO, DROID-SLAM | Deterministic mock |
| Detection/tracking | `ObjectTrackerDetector` | Grounding DINO, SAM2 | Deterministic mock |
| Depth | `DepthEstimator` | Depth Anything | Deterministic mock |
| Action segmentation | `ActionSegmenter` | ActionFormer | Deterministic mock |
| Language grounding | `LanguageGrounder` | LLaVA, Qwen-VL | Deterministic mock |
| Visual representation | `VisualEncoder` (`retargeting/representation.py`) | R3M, VIP, VC-1 | Deterministic mock |
| Policy | `VLAPolicy` (`learning/vla_policy.py`) | OpenVLA, Octo | Nearest-neighbor mock |
| Planner | `HighLevelPlanner` (`learning/planner.py`) | Evaluated language model | Template mock |

## Requirements before implementing a real backend

For each component, define and test the interface contract, data provenance,
units and coordinate frames, expected failures, model/version/weight
provenance, calibration, latency, deterministic behavior where required, and
evaluation against task-relevant ground truth. Real source readers need
separate provider, rights, privacy, consent, and deletion controls. A real
policy needs target-robot teleoperation data and a validated simulator; none of
the model extras supply those inputs or assurances.

Potential source interfaces are located under `data/`, preprocessing protocols
in `preprocessing/extractors.py`, and encoder/policy/planner protocols in
`retargeting/representation.py` and `learning/`. An implementation should be
added behind those contracts, explicitly registered, covered by focused tests,
and evaluated in an isolated non-hardware workflow before changing defaults.
Do not connect a learned component directly to hardware based on this pipeline
or a simulation score.
