# robotX — POV Video → Robot Learning System

A compliant, end-to-end pipeline for learning robot manipulation policies from
**egocentric ("point-of-view") human video**. It implements the full six-layer
design: acquire video through *legitimate* channels, turn it into structured
per-clip records, bridge the human→robot embodiment gap, pretrain + fine-tune a
Vision-Language-Action policy, validate in simulation under hard safety limits,
and close the loop by feeding real-robot failures back into the dataset.

> **Sourcing note (read this first).** Scraping X, Instagram, TikTok, Facebook,
> or YouTube directly generally violates each platform's Terms of Service, and
> using other people's video without a license raises copyright issues. robotX
> is therefore built around **compliant sourcing** — official APIs, pre-licensed
> research datasets, licensed creator partnerships, and first-party capture —
> not a scraper. See [`docs/data_sources.md`](docs/data_sources.md).

## Why it runs out of the box

Every heavy ML component (hand-pose, depth, detection/tracking, the visual
encoder, the VLA policy, the VLM planner) sits behind a small interface with a
**deterministic mock backend**. So the entire pipeline runs and is fully tested
with just `numpy` + `pyyaml` — no GPU, no model weights, no video files. Swap in
the real models (MediaPipe, Depth-Anything, Grounding DINO + SAM2, R3M/VIP/VC-1,
OpenVLA/Octo) by flipping a config field. See [`docs/backends.md`](docs/backends.md).

The mock backends exercise the *plumbing and data contracts* end-to-end; they do
not deliver task performance (e.g. sim success rate is expectedly ~0 until a real
policy backend is installed). That distinction is deliberate and documented.

## Architecture (the six layers)

```
 Layer 1  data/          Compliant acquisition ── official APIs · research datasets
                         · licensed partners · first-party capture (+ provenance)
 Layer 2  preprocessing/ Ingest ── shot segmentation → sample (2-8 fps) → quality
                         filter → privacy redaction → per-clip extraction → ClipRecord
 Layer 3  retargeting/   Human→robot ── (A) self-supervised visual representation
                         (R3M/VIP/VC-1)  (B) kinematic retarget → weak pseudo-demos
 Layer 4  learning/      Representation pretrain · VLA policy (OpenVLA/Octo style,
                         pretrain-on-video + finetune-on-teleop) · high-level planner
 Layer 5  sim2real/      Sim validation + domain randomization · safety envelope
                         (torque/speed/force limits, kill switch) · staged rollout
 Layer 6  ops/           Dataset versioning · near-dedup · bias/safety filters ·
                          failure-case feedback loop
 Spatial  spatial_4d.py  Offline 360° multimodal fusion · observed/inferred
                         tracks · motion prediction · emission-aware modes
 Movement movement.py    Selective extremity brains with atomic inactive-joint hold
```

See [`docs/architecture.md`](docs/architecture.md) for the full data flow and the
central `ClipRecord` contract.

## Quick start

```bash
pip install -r requirements.txt          # numpy + pyyaml only
export PYTHONPATH=src                     # or: pip install -e .

# list the compliant source types
python -m robotx.cli sources

# high-level task decomposition (planner)
python -m robotx.cli plan "make coffee"

# run the whole 6-layer pipeline end-to-end on mock backends
python -m robotx.cli run --limit 2 --instruction "pick up cup"

# run the offline 360° 4D spatial reference slice
python -m robotx.cli spatial-demo --mode normal

# prove right-arm-only activation with inactive-joint hold
python -m robotx.cli movement-demo
```

Or from Python:

```python
from robotx import Pipeline, PipelineConfig
from robotx.data.sources import ResearchDatasetSource, FirstPartyCaptureSource

sources = [ResearchDatasetSource("ego4d", "datasets"),
           FirstPartyCaptureSource("captures")]        # the realistic blend
report = Pipeline(PipelineConfig()).run(sources, per_source_limit=4)
print(report.summary())
```

A runnable version of this is in [`examples/run_pipeline.py`](examples/run_pipeline.py).

## The central artifact: `ClipRecord`

Each clip becomes one structured record, exactly as in the design:

```python
ClipRecord(
    clip_id, provenance,          # where it came from + license status
    frames,                       # sampled RGB frames (privacy-redacted)
    hand_pose,                    # (T, 21, 3) 3D hand joints
    camera,                       # (T, 4, 4) ego-motion trajectory
    object_tracks,                # open-vocab detections tracked over time
    depth,                        # monocular relative depth
    actions,                      # atomic action segments (temporal localization)
    language_label,               # VLM caption -> task description
)
```

Everything downstream consumes this type, which is what lets the heavy backends
be swapped without touching orchestration.

## Safety & compliance are enforced, not advisory

- **License gate** — clips that are `PENDING`/`BLOCKED` cannot reach training
  (`robotx.data.licensing.LicenseGate`).
- **Privacy before storage** — bystander faces / plates are redacted *before* a
  clip is ever written (`robotx.preprocessing.privacy`).
- **Action-safety filter** — unsafe/destructive actions are removed before the
  policy can imitate them (`robotx.ops.filters.SafetyContentFilter`).
- **Safety envelope** — every commanded action is clamped to conservative
  speed/force limits and gated behind a kill switch and a passing sim-validation
  bar (`robotx.sim2real`). See [`docs/safety.md`](docs/safety.md).

## Development

```bash
pip install -r requirements.txt pytest
PYTHONPATH=src python -m pytest -q      # 44 tests, all green, no GPU needed
```

## Project layout

```
src/robotx/
  types.py          config.py         pipeline.py        cli.py
  data/             preprocessing/     retargeting/
  learning/         sim2real/          ops/
tests/              docs/              examples/          configs/
```

## Status & roadmap

This is a faithful, tested **reference implementation of the architecture**. The
orchestration, data contracts, compliance controls, safety envelope, and ops
loop are real and exercised; the heavy perception/policy models are mocked
behind stable interfaces. The natural next steps are wiring the real backends in
`requirements-ml.txt` one at a time (start with the visual encoder and hand-pose
estimator) — each is an isolated, drop-in replacement.

The offline 360 4D reference slice is documented in
[`docs/SRV_4D_PLAN.md`](docs/SRV_4D_PLAN.md). It uses deterministic sensor
measurements, explicit sector coverage, uncertainty, occlusion, and one-second
motion prediction. Selective movement activates only the requested extremity
brains and keeps every inactive joint unchanged. These are simulation contracts,
not claims of physical, exposure, clinical, or through-wall safety.
