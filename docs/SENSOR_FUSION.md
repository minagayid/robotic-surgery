# Multimodal Spatial Perception

The goal is not to make every sensor produce an image. The goal is to combine
independent evidence about occupancy, range, motion, material interaction, and
uncertainty.

The reference implementation is `robotic_surgery.spatial.SpatialFusionEngine`. It
accepts camera, depth, force, lidar, ultrasonic, mmWave radar, and Wi-Fi CSI
observations, but it never treats an inferred scene as ground truth.

## Proposed modalities

| Modality | Strength | Important limitation | Initial role |
|---|---|---|---|
| RGB cameras | Semantics, texture, fine manipulation | Lighting, occlusion, privacy | Object/hand recognition |
| Depth/stereo | Direct local geometry | Reflective/transparent surfaces | Near-field shape |
| Joint + force/torque | Body/contact truth | Only after or near contact | State and contact detection |
| Ultrasonic/sonar | Cheap range in darkness | Wide beam, multipath, low detail | Proximity redundancy |
| mmWave radar | Motion/range through dust and poor light | Sparse, calibration complexity | Dynamic obstacle detection |
| LiDAR (optional) | Accurate geometry | Cost, reflective failure modes | Navigation/workcell map |
| Wi-Fi CSI (research) | Coarse motion/presence from RF changes | Environment-specific, low spatial resolution, radio/regulatory constraints | Presence/change evidence only |

Wi-Fi sensing must not be a sole safety sensor or be described as “seeing through
everything.” It is probabilistic RF inference that usually requires controlled
transmitters/receivers, synchronized channel-state measurements, per-environment
calibration, and careful privacy/legal review.

## Wave-evidence admission rule

For the simulation movement gate, a `clear` spatial snapshot requires:

1. fresh, healthy observations in the requested region and calibration;
2. at least two independent modality types;
3. at least one wave modality (ultrasonic, mmWave radar, or Wi-Fi CSI); and
4. every contributing clear observation above the configured confidence floor.

An occupied observation, stale source, calibration mismatch, sensor fault, weak
modality, or high-confidence contradiction yields `occupied` or `unknown` with
`stop_required=true`. A camera-only result cannot clear the gate. These are
software acceptance rules for simulation, not a claim that any sensor is safe for
clinical or physical deployment.

## Fusion pipeline

```text
hardware timestamps -> clock alignment -> calibration transforms
-> modality-specific filtering -> observations with covariance
-> association/tracking -> occupancy + scene graph
-> consistency checks -> immutable WorldSnapshot
```

Use a common robot/world coordinate frame. Never silently fuse observations with
unknown clock offset or calibration. Late data can update historical logs but
must not rewrite a control snapshot already used for a command.

## World representation

Use two linked structures:

1. a local geometric map (voxel/TSDF/occupancy or equivalent) for collision and
   free-space reasoning;
2. a semantic scene graph for objects, agents, relations, affordances, and task
   state.

Each element stores source modalities, last update, uncertainty, and conflict
status. Safety decisions use conservative occupancy when sensors disagree.

## Confidence and degradation

- Define minimum modality sets per behavior. A task may require RGB-D plus robot
  state; a safety stop may rely on radar/sonar plus hardware limits.
- Detect sensor dropout, frozen frames, time drift, calibration change, saturation,
  and contradictory free/occupied evidence.
- Degrade capability rather than guessing: slow down, restrict workspace, return
  home, or stop.
- Record raw references and fusion decisions for deterministic replay.

## Experiments before integration

1. Build a timestamped sensor rig and measure clock drift and end-to-end latency.
2. Create a ground-truth room with static, moving, transparent, dark, and soft
   objects.
3. Compare every modality alone and in combinations using occupancy precision,
   recall, range error, latency, and missed-obstacle rate.
4. Test lighting loss, occlusion, multipath, RF interference, sensor freeze, and
   calibration displacement.
5. Admit a modality to safety-relevant fusion only after its failure envelope is
   documented.

