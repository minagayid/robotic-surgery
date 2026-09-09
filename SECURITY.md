# Security and Safety Model

Offline operation reduces remote exposure but does not remove cyber risk. USB
media, supply-chain packages, compromised training data, malicious model files,
maintenance laptops, and physical access remain attack paths.

## Production network policy

- No default route to the Internet and no required cloud account.
- Local interfaces are allowlisted; unused radios and services are disabled.
- If Wi-Fi CSI sensing is researched, place the radio in a dedicated sensing
  segment with no route to control or maintenance networks.
- No inbound remote shell in normal operation.
- Inter-process identities and least-privilege permissions are mandatory even on
  a single machine.

## Offline update ceremony

1. Build on a controlled engineering workstation from pinned dependencies.
2. Generate an SBOM, hashes, tests, evaluation report, and signed manifest.
3. Scan and write the bundle to dedicated transfer media.
4. Verify signature, hardware/model compatibility, version monotonicity, and
   required approvals at the robot.
5. Install into an inactive slot, reboot, self-test, and retain rollback.
6. Record who approved and installed the bundle without storing secret keys on
   the robot.

Unsigned code, models, calibration, or configuration never execute.

## Safety invariants

- Physical emergency stop always works without the main computer.
- Loss of heartbeat, stale state, unknown calibration, corrupt model, or safety
  controller disagreement produces a controlled stop.
- Learned outputs cannot raise speed, force, torque, workspace, or payload limits.
- A multi-extremity bundle is admitted only after all four extremity processors
  and the final orchestrator agree; one failed processor denies the whole bundle.
- All motion commands have an expiry time and are rejected when late.
- Spatial clearance is denied when wave evidence is missing, stale, weak, or
  contradictory; Wi-Fi CSI is never a sole collision-safety input.
- Startup is motionless until self-tests, calibration identity, and safety
  handshake pass.
- Recovery after an emergency stop requires a deliberate human action.

## Threats to test

- malformed or adversarial sensor input;
- replayed/out-of-order messages and clock manipulation;
- model/data poisoning and unsafe serialized model formats;
- dependency or firmware compromise;
- USB/maintenance-laptop malware;
- unauthorized physical access or calibration replacement;
- denial of service through message floods, disk exhaustion, or GPU starvation;
- false free-space evidence caused by sensor spoofing or interference.

## Verification

Use unit tests, interface compatibility tests, simulation scenarios,
hardware-in-loop tests, fault injection, fuzzing of parsers, static analysis,
dependency review, reproducible builds, and periodic recovery drills. Safety cases
must trace hazards to controls, tests, evidence, and responsible owners.

## Responsible deployment

Early phases are supervised research in a restricted workcell. No deployment near
untrained people, public spaces, medical care, weapons, security enforcement, or
other high-consequence use is in scope. Applicable machinery, electrical, radio,
privacy, and workplace rules must be reviewed for the deployment country.

