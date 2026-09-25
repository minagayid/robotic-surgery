# Robotic Surgery

An offline research codebase combining a deterministic host-side safety
reference, robotics mechanics calculations, and an absorbed mock-first video
learning pipeline.

> Scope: research and simulation only. This repository has no hardware driver,
> real-time guarantee, validated surgical workflow, or clinical-use approval.

## Run locally

Python 3.10 or newer is required. Install runtime dependencies from
`requirements.txt`; the core simulator uses the standard library, while the
learning pipeline uses NumPy and PyYAML.

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m robotic_surgery demo --json
python -m robotic_surgery five-heart-demo --json
python -m robotic_surgery benchmark --iterations 1000
python -m robotic_surgery mechanics-demo --force-n 0 10 --json
python -m robotic_surgery learning sources
python -m robotic_surgery learning run --limit 2
```

The data/learning pipeline can also be started from Python via
`robotic_surgery.learning_pipeline.Pipeline`. The default source adapters return
mock references and synthetic frames; they do not read video files or contact
platform APIs. A passing run checks interfaces and pipeline plumbing; it does
not establish task competence, license clearance, or physical safety.

## Implemented flow

```text
mock source references and synthetic frames
    -> mock provenance labels and label-only gate
    -> synthetic sampling, quality/privacy fixtures, mock feature extraction
    -> weak human-to-robot pose retargeting
    -> mock representation/policy training and task planning
    -> simple randomized kinematic simulation
    -> dataset feedback and versioning

typed motion proposal + robot/sensor state
    -> deterministic source/time/calibration/limit checks
    -> four-group simulation gate + spatial evidence gate
    -> simulated execution and append-only event journal
```

The mechanics helper calculates idealized static moments and planar two-link
Jacobian loads. Those results are analysis outputs; they do not enter the motion
runtime or choose motor commands.

## Engineering and safety boundaries

- Human video retargeting produces weak pseudo-demonstrations. It contains no
  robot joint truth, calibrated force data, validated contact response, or
  procedure-specific clinical evidence.
- The built-in simulation is a goal-reaching kinematic toy model, not a
  physics-validated simulator. Its scores are useful only for checking program
  flow.
- The host motion runtime can exercise deterministic gates. It does not connect
  to actuators, surgical instruments, patients, animals, or real-time safety
  hardware.
- Force/torque analysis in the mechanics helper assumes a rigid planar two-link
  arm and a known external force. It omits gravity, inertia, friction, compliance,
  backlash, contact uncertainty, singularity handling, structural stress,
  thermal limits, and actuator dynamics.
- Medical robot requirements need a device-specific risk process, independent
  safety hardware, verified manufacturing and reprocessing controls, and the
  required clinical and regulatory evidence. Industrial robot standards do not
  by themselves establish medical-device compliance.

The pipeline CLI's source listing names mock adapter types; it does not imply
those external sources are contacted or that their rights are checked. See the
[learning pipeline boundary](docs/learning-pipeline/architecture.md) for detail.

See [engineering foundations](docs/ENGINEERING_FOUNDATIONS.md),
[implemented boundary](docs/IMPLEMENTATION.md),
[surgical program charter](SURGICAL_PROGRAM.md),
[dataset catalog](docs/DATASET_CATALOG.md), and
[surgical operations](docs/surgical/OPERATIONS.md). Third-party license notices
for absorbed code are in [LICENSES](LICENSES/MIT-LICENSE.txt).
