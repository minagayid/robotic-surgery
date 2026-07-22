# Open Decisions

Record each decision as an ADR with context, options, measurements, choice,
consequences, owner, and review date.

| ID | Decision | Candidates | Evidence required | Status |
|---|---|---|---|---|
| ADR-001 | Base OS and real-time strategy | Hardened Linux; Linux + PREEMPT_RT; split MCU/Linux | Control jitter, driver support, update model | Open |
| ADR-002 | Local middleware | ROS 2/DDS profiles; Zenoh/local IPC; custom minimal bus | Latency, memory, isolation, offline discovery | Open |
| ADR-003 | Simulation stack | MuJoCo; Isaac Sim; Gazebo; mixed | Robot support, sensor fidelity, reproducibility | Open |
| ADR-004 | World geometry | Occupancy/OctoMap; TSDF; voxel hash | Update latency, memory, collision-query quality | Open |
| ADR-005 | Model runtime | PyTorch; ONNX Runtime; TensorRT; OpenVINO | Target hardware benchmark and licensing | Open |
| ADR-006 | Event storage | MCAP/rosbag2; custom append-only log | Throughput, schema evolution, replay | Open |
| ADR-007 | Safety controller | Safety PLC; certified drive functions; custom MCU prototype | Hazard analysis and required integrity level | Open |
| ADR-008 | RF sensing | Wi-Fi CSI hardware; mmWave radar; no RF in MVP | Incremental accuracy, interference, legal review | Open |

## Decisions already made for planning

- Production runtime is offline-first; training and bundle creation happen in a
  separate engineering zone.
- Safety enforcement is independent of learned models and the main compute.
- The MVP is one robot and a restricted tabletop workcell.
- Human video supplies representations and weak priors, not ground-truth robot
  actuation.
- Wi-Fi CSI stays off the critical path until experimentally justified.

