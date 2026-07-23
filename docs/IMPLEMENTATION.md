# Implementation Guide

## Current executable slice

The repository now contains a dependency-free Python reference runtime in
`src/robotx_os`. It establishes contracts and safety semantics before hardware,
middleware, and hard real-time technologies are selected.

Implemented:

- immutable, versioned body-state and motion-proposal contracts;
- monotonic timestamps, command expiry, bounded execution duration, source
  allowlists, sequence replay rejection, calibration identity, confidence, and
  finite-number checks;
- joint position, velocity, effort, proximity, heartbeat, hardware-ready,
  configuration, and physical E-stop gates;
- predictive joint-limit checking over each short command horizon;
- latched stops with deliberate operator acknowledgement and safe-reset checks;
- a fail-closed actuator interface with a deterministic simulation adapter;
- a local hash-chained event journal with integrity-checked replay; and
- offline unit and fault-injection tests.

Not implemented or approved:

- a physical actuator driver or independent safety-controller firmware;
- hard real-time scheduling or bounded worst-case execution time;
- authenticated IPC, process isolation, secure boot, signed bundles, or A/B
  updates;
- collision geometry beyond the redundant nearest-obstacle gate;
- perception, sensor fusion, planning, learned inference, or ROS integration;
- hardware use of any kind, including supervised trials.

## Why the reference runtime is Python

The current environment has Python 3.12 but no Rust/C++ toolchain. Python lets us
execute and test the safety state machine offline now. It is a contract and
behavior reference, not the final servo-loop implementation. ADR-001 remains
open; the measured target-hardware benchmark will select Rust, C++, or another
appropriate compiled implementation for real-time control. Contract fixtures and
fault tests must be reused across that implementation so behavior cannot drift.

## Run completely offline

Python 3.11 or newer is the only requirement. No package download is needed.

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
python -m unittest discover -s tests -v
python -m robotx_os.demo
python benchmarks/safety_supervisor.py
```

The demo deliberately requests too much velocity. The expected result is a
`clamp` decision, bounded velocities, a short simulated movement, and a verified
local event-log path.

The benchmark reports observed host-side decision latency. It is useful for
regression detection only; it is not a worst-case timing guarantee.

## Runtime trust boundary

```text
Untrusted cognitive zone
  MotionProposal
        |
        v
Host SafetySupervisor ---- local hash-chained audit journal
  schema / source / sequence / freshness / calibration
  confidence / duration / position / velocity / effort / proximity
        |
        v only APPROVE or CLAMP
Real-time actuator adapter
        |
        v
Independent MCU/PLC safety zone ---- physical E-stop / drive power removal
```

The Python supervisor can reject host commands, but it cannot be the sole safety
mechanism. A separate MCU, safety PLC, or certified drive function must enforce
the final limits and remove power when the main computer fails.

## Performance rules already encoded

- Contracts use immutable slotted records to reduce allocation overhead and
  accidental mutation.
- Safety evaluation is a bounded linear pass over a fixed joint count.
- Motion is accepted only as short, expiring velocity horizons.
- No network, dynamic plugin, model, or third-party package participates in the
  safety decision.
- The audit journal is local and can trade throughput for `fsync` durability via
  an explicit setting; critical deployment mode defaults to durable writes.

## Next implementation gate

Do not connect this runtime to motors. First select the arm, drive safety
functions, E-stop circuit, safety controller, encoders, and target compute. Then:

1. freeze physical units, joint ordering, coordinate frames, safe work envelope,
   and measured limits;
2. implement a separate watchdog protocol and normally-safe enable line on the
   MCU/PLC;
3. add an actuator adapter that can only consume `SafetyDecision` output;
4. measure p50/p95/p99/max loop time, scheduling jitter, stop latency, thermal
   throttling, and bus saturation;
5. replay these same tests plus injected packet loss, clock faults, stuck sensors,
   encoder divergence, and drive faults in simulation and hardware-in-loop; and
6. permit powered bench motion only after the hazard controls and test evidence
   are reviewed.
