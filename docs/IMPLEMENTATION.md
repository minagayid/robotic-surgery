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
- an append-only local JSONL event journal with a SHA-256 hash chain;
- a demo, benchmark, and standard-library unittest suite; and
- an optional loopback-only OpenAI-compatible advisory client.

## Run it

```powershell
python -m unittest discover -s tests -v
python -m robotic_os demo --json
python -m robotic_os benchmark --iterations 1000
```

The default demo journal is written under `runtime-data/`, which is ignored by
Git. Pass `--journal <path>` to select another local path.

## Deliberate non-features

This milestone contains no hardware drivers, actuator protocol, network
middleware, ROS dependency, real-time guarantee, surgical procedure logic,
patient/animal data, clinical workflow, online learning, deployment mechanism,
or remote service. It must not be connected to a robot or used to make clinical
decisions.

The optional language-model client accepts only loopback endpoints and returns
untrusted advisory text. It is intentionally not imported by the safety or
runtime modules.

## Next engineering gate

Before hardware work, select and document one robot/workcell, coordinate-frame
convention, compute target, simulator, middleware, independent safety controller,
sensor set, and hazard-analysis owner. Then add hardware-in-loop adapters behind
the existing contracts. The host reference runtime is evidence for software
behavior only; it is not evidence of certified safety or hard real-time timing.
