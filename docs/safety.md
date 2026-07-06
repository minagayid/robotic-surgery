# Safety & Sim-to-Real (Layer 5)

> **Never deploy retargeted human-video policies straight to hardware.**

Policies pretrained on human video (and weak pseudo-demos) are validated in
simulation first, then rolled out on hardware only in stages, under hard limits
that the code *enforces* rather than merely recommends.

## The safety envelope

`robotx.sim2real.safety.SafetyEnvelope` wraps every commanded action before it
reaches sim or hardware. `clamp()` cannot return an out-of-envelope action:

- **Speed limit** — Cartesian end-effector displacement per step is capped at
  `max_ee_speed * dt`. Overspeed commands are scaled down and logged.
- **Force / torque limit** — during early trials the gripper cannot command
  more than `torque_limit_frac` of hardware max closing force; excess is
  floored and logged.
- **Kill switch** — if `require_kill_switch` is set and the switch is engaged,
  `preflight()` raises `SafetyViolation` and nothing is commanded.

Defaults are deliberately conservative (`torque_limit_frac=0.25`,
`max_ee_speed=0.15 m/s`, `force_limit_n=10`).

## Simulation validation with domain randomization

`robotx.sim2real.validation.SimValidator` rolls the policy out in a randomized
sim (friction, lighting, goal position) and reports a success rate plus how often
the safety envelope had to intervene. Swap the built-in kinematic sim for
MuJoCo / Isaac Sim behind the same interface.

## Staged rollout, gated on sim

`robotx.sim2real.rollout.StagedRollout.gate()` **refuses** to run on hardware
unless the sim success rate cleared `min_sim_success_rate`. During rollout every
step passes through the safety envelope and is logged; a completed episode
converts into a (high-value) `RobotDemonstration`.

## Closing the loop (Layer 6)

`robotx.ops.feedback.FeedbackLoop` folds rollout outcomes back into the dataset:

- **Successes** become new fine-tuning demonstrations.
- **Failures / aborts** become prioritized re-collection requests — because real
  robot experience is worth more than more human video.

## Content-level safety (Layer 6)

Imitation learning "will happily learn bad habits along with good ones," so
`robotx.ops.filters.SafetyContentFilter` removes clips whose action labels match
an unsafe-action blocklist (throw, smash, hit, …) **before** anything reaches the
policy. `BiasFilter` caps any single (source, task-family) stratum's share so the
dataset's demographic/environment/task skew does not dominate training.
