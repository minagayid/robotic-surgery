# Operating Guide

> Simulation and approved research use only. This is a robot operating guide,
> not a surgical-procedure guide.

## Before the run

1. Confirm the exact approved configuration, trained roles, synthetic phantom,
   instruments, software/calibration, and emergency/conversion drill objective.
2. Inspect carts, arms, locks, covers, cables, adapters, controls, display, pedals,
   emergency stops, release tools, and instrument life/status.
3. Power on with the workspace clear. Pass configuration, brake, base-lock,
   encoder, camera, storage, network-isolation, emergency-stop, and backup-power
   checks.
4. Position carts with a clear bedside and exit path. Engage and verify locks.
5. Install the training drape/adapter and blunt instruments. Confirm identity,
   orientation, complete latch, calibration, and low-speed clearance.

## During the run

- Announce the active mode, controlling user, selected arm pair, and next action.
- Verify live visualization and neutral master controls before enabling motion.
- Use clutch to recenter; never push through a fixture, force limit, collision,
  stall, repeated warning, or lost registration.
- Pause on unknown visualization, tracking, access load, instrument state, team
  authority, power, timing, or log status.
- Exchange one instrument at a time in the defined safe exchange pose with motion
  and energy disabled.
- Energy outputs remain disabled in this repository's simulations.

## Stop and recovery

1. Neutralize controls and request safe hold.
2. Announce the stop and identify every arm/instrument state.
3. Use emergency stop for uncontrolled or potentially hazardous output.
4. Never assume emergency stop retracts a tool; inspect the simulated field first.
5. Manual release is performed only after motion is disabled, the arm is supported,
   and the trainer directs the instrument-specific release.
6. Resume only after the cause and configuration are understood and all required
   checks pass; otherwise end the run.

## After the run

Disable motion, remove instruments one arm at a time, inspect/count components,
undock, remove the training drape, park the arms, seal logs, record faults and
interventions, clean approved surfaces, and lock out damaged or failed equipment.

For the complete workflow, see [Use and Operations Guide](../USER_AND_OPERATIONS_GUIDE.md).
