# Robotics engineering foundations and implementation gates

This curriculum is a design checklist for future engineering work. The current
repository implements only the specific items marked **implemented** below;
it is not a complete robot controller or a medical device.

## Mechanics and machine design

- **Levers and statics.** For a force `F` applied at offset `r` from a pivot,
  moment is `tau = r x F`; in a planar perpendicular load, `|tau| = F r_perp`.
  An ideal gear train with ratio `G` and efficiency `eta` has the approximate
  relation `tau_motor = tau_joint / (G eta)`. Real motor sizing also needs
  acceleration, reflected inertia, friction, backlash, thermal duty, fatigue,
  and a documented service/load case.
- **Manipulator statics.** For an end-effector force `F`, ideal joint loads are
  `tau = J(q)^T F`, with Jacobian `J(q) = dx/dq`. The implemented
  [`mechanics.py`](../robotic_surgery/mechanics.py) calculates `r x F`, ideal
  lever force, gearbox input torque, and planar two-link forward position and
  external-force joint torques. This is a calculator for explicit assumptions,
  not an actuator selection or validation tool.
- **Structure and manufacture.** A real design needs material and process
  selection, stress/fatigue and buckling analysis, bearing/fastener sizing,
  tolerances and datum schemes, cable routing, service access, surface/cleaning
  requirements, inspection criteria, supplier controls, and traceability. None
  of these are represented by the calculator.

## Geometry, kinematics, and motion

The broader robotics baseline is rigid-body transforms and reference frames,
forward/inverse kinematics, open/closed chains, Jacobians, singularity analysis,
trajectory generation, motion planning, grasping, and mobile manipulation. The
two-link helper covers only a small planar example. It does not contain an arm
model, inverse kinematics, collision geometry, workspace limits, or a surgical
remote-center-of-motion mechanism.

Before selecting a robot or middleware, define a physical robot model, joint
names and units, frame convention, calibrated tool transform, joint limits,
collision geometry, end-effector/tool, and a simulator matching the intended
configuration. Servo command limits and collision/singularity checks need
measured joint feedback and a validated robot model; this repository has none.

## Dynamics, actuation, and control

Robot dynamics generally require a model such as

```text
M(q) q_ddot + C(q, q_dot) q_dot + g(q) + tau_friction
    = tau_actuator + J(q)^T F_external
```

and a calibrated actuator/drive model. A control curriculum should then cover
sampling and latency budgets, state estimation, trajectory tracking, PID and
feed-forward control, impedance/admittance and force control where appropriate,
acceleration/jerk limits, saturation, stability, disturbance rejection, watchdogs,
and fault transitions. The present Python runtime checks typed proposals and
simulated position/velocity/force-limit fields; it does not implement torque
control, force feedback, dynamics, real-time scheduling, or a motor protocol.

## Sensors, calibration, and uncertainty

Robotics needs synchronized encoders, drive current/temperature, force/torque
sensing, end-effector state, and task-dependent vision or other perception.
Calibration must tie sensor, robot, tool, and world frames to traceable
procedures with residual/error limits, age, version, and invalidation events.
State estimates need uncertainty and stale-data behavior. The repository has
typed sensor-health, age, calibration, and provenance fields plus a synthetic
spatial fusion example; it has no sensor driver or measurement validation.

## Safety, manufacturing quality, and operations

Engineering begins with intended use and hazard analysis, then derives verified
requirements, independent limits, fault responses, human interfaces, system
integration tests, manufacturing acceptance, configuration/change control,
maintenance, service, complaint handling, and post-market monitoring. NIST's
robot performance framework organizes measurable evidence across perception,
mobility, dexterity, and safety. OSHA's industrial robotics material stresses a
task/application risk assessment and site-acceptance checks. These are useful
process references, but industrial requirements do not substitute for medical
device requirements.

For a surgical robot, IEC 80601-2-77 addresses basic safety and essential
performance of robotically assisted surgical equipment and systems. FDA's
overview describes currently authorized RAS systems and their intended use,
including direct surgeon control. The RAS premarket document dated 2026-09-25
is a draft for comment, not an implementation requirement or authorization.
These references do not establish this repository's applicability or
compliance. The applicable current regulatory pathway, standards, quality
system, clinical evidence, and jurisdiction must be confirmed by qualified
regulatory/clinical owners for a specific device and intended use.

## Research and reference curriculum

1. **Mechanics foundations:** free-body diagrams, levers, torque, friction,
   power, gears, bearings, stress, fatigue, thermal behavior, and actuator
   selection.
2. **Robot geometry:** coordinate frames, rigid transforms, forward/inverse
   kinematics, Jacobians, statics, singularities, and calibration.
3. **Dynamics and controls:** rigid-body dynamics, trajectory generation,
   feedback, force/compliance control, sampling, latency, and fault handling.
4. **Perception and planning:** sensing, uncertainty, collision scenes, motion
   planning, grasping, and safe teleoperation.
5. **Embedded and systems engineering:** encoders/drives, real-time loops,
   hardware abstraction, communication failures, power, EMC, cybersecurity,
   and independent safety functions.
6. **Verification and operations:** requirements traceability, simulation
   validity, bench and hardware-in-loop fixtures, repeatability, capability
   metrics, supplier/manufacturing controls, maintenance, service, and change
   management.
7. **Medical-device lifecycle:** device-specific risk management, usability,
   sterile/reprocessed instrument lifecycle, clinical evaluation, quality
   records, regulatory submissions, adverse-event handling, and post-market
   surveillance.

Primary sources used for this curriculum are linked below. A useful broad
textbook outline is Northwestern's *Modern Robotics*: rigid-body motion,
kinematics/statics, dynamics, trajectories, planning, control, grasping, and
mobile robots. MIT OpenCourseWare adds mechanics, dynamics/control, mechanical
design, and programming assignments. ROS 2 Control and MoveIt are candidate
implementation references only; neither is currently a project dependency.

## Primary references

- Northwestern University, [*Modern Robotics* chapter outline and free preprint](https://hades.mech.northwestern.edu/index.php/Modern_Robotics).
- MIT OpenCourseWare, [Introduction to Robotics course material](https://ocw.mit.edu/courses/2-12-introduction-to-robotics-fall-2005/), which includes mechanics, dynamics/control, mechanical design, notes, assignments, and projects.
- ROS 2 Control, [controller manager documentation](https://control.ros.org/jazzy/doc/ros2_control/controller_manager/doc/userdoc.html); candidate architecture only, not integrated here.
- MoveIt, [Servo overview](https://moveit.picknik.ai/main/doc/examples/realtime_servo/realtime_servo_tutorial.html), describing joint/end-effector command interfaces, limits, collision checks, and singularity handling.
- NIST, [Performance Assessment Framework for Robotic Systems](https://www.nist.gov/programs-projects/performance-assessment-framework-robotic-systems), for measurable perception, mobility, dexterity, and safety performance.
- OSHA, [Technical Manual: Industrial Robot System Safety](https://www.osha.gov/otm/section-4-safety-hazards/chapter-4), for application risk assessment, integrator/operator duties, and site acceptance; industrial guidance is not medical-device approval.
- IEC, [80601-2-77:2019+AMD1:2023](https://webstore.iec.ch/en/publication/89957), particular requirements for basic safety and essential performance of robotically assisted surgical equipment and systems.
- FDA, [Computer-Assisted Surgical Systems](https://www.fda.gov/medical-devices/surgery-devices/computer-assisted-surgical-systems), describing currently authorized RAS device use and direct surgeon control.
- FDA, [Draft guidance on RAS device premarket submissions, issued 2026-09-25](https://www.fda.gov/media/194987/download); this source is explicitly a draft for comment and not for implementation.
