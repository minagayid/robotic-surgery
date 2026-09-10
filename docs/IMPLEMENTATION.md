# Current implementation boundary

## Delivered slice

The `robotic_os` package is a small offline reference runtime for research and
simulation. It provides:

- typed motion proposals, robot state, safety limits, and safety decisions;
- finite-number and dimension validation at contract boundaries;
- source allowlists, calibration identity checks, sequence replay protection,
  heartbeat freshness, sensor-health gating, proximity gating, position/force
  limits, velocity clamping, and expiry-before-completion checks;
- a latched emergency-stop state that requires an explicit operator reset;
- a deterministic clock for reproducible scenarios;
- a simulated actuator boundary that applies only approved or clamped commands;
- four independent extremity processors, upper/lower regional coordinators, and a
  fifth logical main movement orchestrator;
- a concrete `robotx-reference-four-extremity-v1` workcell profile with explicit
  frames, rates, simulator, compute target, and no-hardware actuation policy;
- an independent final safety-gate reference model exercised after host-side
  validation, plus deterministic stale-heartbeat, sensor, and emergency-stop
  fault injection helpers;
- expiry-aware calibration manifests and a registry that rejects unknown,
  expired, or dimension-incompatible calibration state;
- a fail-closed actuator/HAL boundary with a simulation adapter and a ROS2
  message-shape contract that cannot open a ROS connection;
- a process-isolated safety-worker prototype that stops on timeout, malformed
  responses, or worker failure; and
- a deterministic long-duration soak harness that runs paired host/independent
  checks and periodic sensor faults without external actuation;
- a release-gate evaluator that requires target hardware, certified safety,
  approved calibration, independent HIL evidence, untampered soak evidence,
  and separate review before it can report review eligibility;
- versioned JSON telemetry records suitable for local replay or a downstream
  ingest adapter;
- conservative fusion of camera/depth and wave-based spatial observations
  (ultrasonic, mmWave radar, and Wi-Fi CSI); and
- an explicit advisory-context compaction policy that triggers at 45% by default
  and blocks oversized requests until an explicit summary is supplied;
- an append-only local JSONL event journal with a SHA-256 hash chain;
- an offline dataset manifest/registry that requires provenance, de-identification,
  permitted-use checks, and local archive checksum verification before a bounded
  research training workflow can admit data; and
- a demo, benchmark, and standard-library unittest suite; and
- an optional loopback-only OpenAI-compatible advisory client.

## Run it

```powershell
python -m unittest discover -s tests -v
python -m robotic_os demo --json
python -m robotic_os five-heart-demo --json
python -m robotic_os workcell-info --json
python -m robotic_os benchmark --iterations 1000
python -m robotic_os soak --iterations 10000 --fault-interval 1000
python -m robotic_os release-gate docs/production-gate-manifest.example.json --json
```

The default demo journal is written under `runtime-data/`, which is ignored by
Git. Pass `--journal <path>` to select another local path.

## Deliberate non-features

This milestone contains no hardware drivers, actuator protocol, network
middleware, ROS dependency, real-time guarantee, surgical procedure logic,
patient/animal data, clinical workflow, online learning, deployment mechanism,
or remote service. The dataset registry stores metadata and verifies local
archives; it does not contain or download clinical data and does not replace
ethics, privacy, license, or data-use review. The package must not be connected
to a robot or used to make clinical decisions.

The optional language-model client accepts only loopback endpoints, enforces the
early context-compaction policy, and returns untrusted advisory text. It is
intentionally not imported by the motion or safety path.

## Next engineering gate

The concrete profile and independent gate close the software-side selection gate
for repeatable SIL tests. The calibration registry, HAL, isolated worker, and
soak harness extend that evidence, but do not close the hardware gate.
Hardware-in-loop work is still a separate gate: select the actual robot and
sensors, map these contracts to a certified safety PLC/drive function, define
the hazard-analysis owner, and implement a reviewed ROS2/HAL adapter. The host
reference runtime is evidence for software behavior only; it is not evidence of
certified safety or hard real-time timing.
