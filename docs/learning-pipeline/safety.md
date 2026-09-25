# Simulation bounds and deployment boundary

> The absorbed pipeline is research code. It cannot drive a real robot and does
> not establish physical or clinical safety.

## What the code actually checks

- `SafetyEnvelope` bounds Cartesian step distance only when it has an explicit
  measured starting end-effector position. A first command with no such pose is
  rejected rather than treated as zero velocity.
- The gripper scalar is a normalized travel command (`0` closed, `1` open). The
  configured closure fraction caps travel only. The code has no force/torque
  transducer or actuator model, so it makes no Newton or newton-metre safety
  claim.
- A simulated stop latch rejects the next command. It is not a hardware
  emergency stop or an independent safety controller.
- Follow-on rollout requires a non-empty simulation report and an environment
  explicitly marked `simulation_only`. This marker is an API misuse check, not
  a security boundary.

## What remains unsupported

The built-in validator uses synthetic images and a tiny goal-reaching kinematic
toy model. Its domain randomization covers a few scalar toy parameters, not a
robot's dynamics or a validated digital twin. No hard real-time guarantees,
collision checking, joint/torque control, instrument interface, safety-rated
stop, hardware-in-loop test, manufacturing acceptance, or clinical evidence is
provided. Simulation scores are plumbing checks only; they are not readiness
gates for hardware or patient use.

Any hardware work requires a selected robot and sensors, qualified model and
calibration, independent safety design, application-specific hazard analysis,
verification on the exact manufactured configuration, and the applicable
medical-device quality and regulatory pathway. A learned model must never
replace these controls.
