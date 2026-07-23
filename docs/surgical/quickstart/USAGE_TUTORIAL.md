# Usage Tutorial: First Virtual Case

> Goal: complete a non-clinical synthetic-phantom session while demonstrating
> correct configuration control, teleoperation, safe hold, and recovery.

## Scenario

- One visualization arm and two blunt instrument arms.
- Neutral synthetic phantom with three visible target markers.
- S2 surgeon-controlled teleoperation only.
- No cutting, energy, medication, anatomy, or living subject.

## Walkthrough

### 1. Select and lock the configuration

Open the simulator, select the training configuration, and confirm the arm,
instrument, software, calibration, workspace, speed, and force manifest. The
session cannot start if any identity is unknown or incompatible.

### 2. Run readiness checks

Place all arms in parked mode. Test emergency stops, base-lock sensing, brakes,
master neutral state, camera freshness, command expiry, storage, logs, and the
safe-state response to a disconnected instrument.

### 3. Arrange the virtual room

Position the camera cart first, then the two instrument carts. Maintain a clear
bedside lane and prevent arm-arm and arm-table collisions. Lock each cart and
confirm the indicators.

### 4. Dock to the phantom

In setup-compliant mode, position one arm at a time. Align each access/remote-
center marker, attach the identified blunt instrument, and run the low-speed
workspace/clearance check. Return to docked standby.

### 5. Enable surgeon control

Confirm the camera is live, masters are neutral, the correct arm pair is selected,
and S2 is displayed. Hold enable and move the two tool tips to the first marker.
Use clutch to recenter without moving the tips.

### 6. Complete the coordination task

Move a virtual ring between the three markers while remaining inside the cyan safe
workspace and below the simulated force limit. Stop if the view freezes, tracking
residual rises, a tool stalls, or the access-load indicator changes to amber.

### 7. Exchange an instrument

Move to the safe exchange pose, disable the selected arm, remove the first blunt
tool, inspect/count it, attach the second identified tool, and complete the
low-speed function check before re-enabling.

### 8. Demonstrate a safe hold

Inject a stale-camera fault. Verify that new hazardous motion is rejected, the
system enters safe hold, and the event log records the trigger. Restore the camera,
repeat required checks, and obtain trainer authorization before resuming.

### 9. End and review

Return tools to the exchange pose, disable motion, remove instruments, undock,
park, seal the log, and review timing, interventions, warnings, limit margins, and
whether every team member stated the correct mode and authority.

## Pass criteria

- No boundary, speed, force, collision, configuration, or identity violation.
- All mode/authority changes announced correctly.
- Correct safe response to the injected fault.
- Instrument exchange completed without moving the access interface.
- Complete, integrity-checked replay of the session.
