# 360 4D Spatial Recognition System

## Scope

This plan turns the shared Spatial Recognition Vision design into a bounded
reference implementation for both `robotX` and `robotic-surgery-os`. It is a
software-in-the-loop capability: it does not connect to motors, surgical
instruments, patients, animals, networks, or real-time safety hardware.

The system answers five separate questions instead of pretending that one wave
can see everything:

1. What evidence is directly observed?
2. What motion is measured and what motion is only predicted?
3. Which of the full 360-degree sectors are covered, stale, contradictory, or
   unknown?
4. Which sensor emissions are permitted in the current operating mode?
5. Is the resulting snapshot safe to hand to a movement gate?

## Reference architecture

```text
sensor adapters -> timestamp/calibration/health checks -> modality evidence
       -> sector coverage + track association -> 4D world snapshot
       -> observed/inferred + uncertainty + prediction -> safety snapshot
       -> selective extremity brains -> regional coordinators -> main gate
```

The reference engine uses deterministic tuples and standard-library logic. Real
RGB/NIR, thermal, LiDAR, mmWave/UWB, acoustic, IMU, and Wi-Fi CSI adapters can
be added behind the same measurement contract later. Active sensing remains
policy-controlled; the engine never promotes hidden inference to direct
observation.

## Sensor and mode policy

| Mode | Passive inputs | Active inputs | Intended use |
| --- | --- | --- | --- |
| ECO | RGB/NIR, thermal, microphone, IMU, listen-first Wi-Fi CSI | intermittent eye-safe LiDAR only | minimum unnecessary emission |
| NORMAL | all available passive inputs | bounded LiDAR, ultrasonic, mmWave/UWB | normal reference operation |
| DEGRADED | thermal, microphone, IMU, any healthy passive input | adaptive LiDAR and bounded radar/sonar | darkness, dust, fog, rain, or visual occlusion |

The mode is not a hardware exposure certification. It is an explicit software
policy that rejects active measurements disabled for the current mode and records
the reason. Compliance and exposure validation remain hardware-specific gates.

## 4D world model

Each immutable snapshot contains:

- timestamp and calibration identity;
- covered and unknown 360-degree sectors;
- tracked objects with position, velocity, one-second predicted position,
  confidence, source modalities, observed/inferred state, occlusion, and a
  deterministic uncertainty estimate;
- contradiction and degradation reasons;
- active emission accounting and `stop_required`.

Clearance is conservative: stale, unhealthy, mismatched, contradictory, weak,
or incomplete evidence cannot clear a movement region. A hidden target is
represented as an inference with uncertainty, never as a fabricated visible
mesh.

## Movement integration

Each extremity has an independent local processor (“brain”) with disjoint joint
ownership and its own source/sequence/safety validation. The main orchestrator
accepts an `active_processors` subset. Unrequested processors are not required,
not validated, and their joints remain at the current state. Regional
coordinators aggregate only the active members of their region. The final gate
still requires fresh spatial clearance, independent safety checks, atomic
commit, and replay protection.

## Offline acceptance slice

The demonstrator will run with no model weights, ROS binding, sensor driver,
network route, or cloud service. It will show a 360-degree snapshot with a
moving observed object and an occluded inferred object, exercise emission modes,
and prove that a right-arm-only movement leaves all other joints unchanged.

## Evidence gates

- contract validation: invalid modality, sector, timestamp, confidence, or
  vector data is rejected;
- fusion behavior: stale/calibration/health/contradiction/unknown coverage is
  fail-closed and predictions remain labeled;
- movement behavior: selective activation, disjoint ownership, safety limits,
  and atomic commit are tested;
- offline behavior: CLI/demo and test runs complete using local code only;
- release behavior: final diff review, test output, commit id, and remote branch
  verification are recorded separately for each repository.

## Deferred work

Real sensor drivers, hardware clock synchronization, calibration tooling,
occupancy/TSDF storage, learned association, ROS2 message bindings, exposure
compliance testing, HIL validation, clinical quality-system evidence, and
procedure-specific surgical validation are intentionally deferred.
