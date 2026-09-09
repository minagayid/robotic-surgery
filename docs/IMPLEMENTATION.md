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
- four independent extremity processors plus a fifth atomic movement orchestrator;
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
python -m robotic_os benchmark --iterations 1000
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

Before hardware work, select and document one robot/workcell, coordinate-frame
convention, compute target, simulator, middleware, independent safety controller,
sensor set, and hazard-analysis owner. Then add hardware-in-loop adapters behind
the existing contracts. The host reference runtime is evidence for software
behavior only; it is not evidence of certified safety or hard real-time timing.
