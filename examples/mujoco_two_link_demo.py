"""Free physics-simulation demo for the robotic-surgery research codebase.

Runs a planar two-link arm under MuJoCo physics on CPU only. This example
exists because the simulation-platform trial (docs/SIMULATION_PLATFORMS.md)
found that NVIDIA Isaac Sim cannot currently run free in the cloud: it
requires an NVIDIA GPU with RT cores, which free cloud GPUs (Colab, Kaggle)
do not provide. The repository still needs a physics-accurate validation
backend beyond its built-in kinematic toy simulator, and MuJoCo is free,
open source (Apache-2.0), and runs headless on CPU.

What the demo checks, mirroring the repository's replay ethos:

1. Gravity works: released from horizontal, the damped arm swings down to
   the vertical hanging position.
2. Energy dissipates: joint motion at the end of the run is far below the
   peak motion during the fall.
3. Replay is deterministic: two identical runs produce bit-identical final
   states, the property the event journal relies on for session replay.

Boundary: this is a generic rigid-body physics check, not a surgical model.
It does not validate contact-rich manipulation, tissue interaction, force
limits, or any safety-critical property, and its output is not an actuator
command.

Requires: pip install mujoco   (free, Apache-2.0; CPU is sufficient)
"""

from __future__ import annotations

import json
import math

LINK_LENGTH_M = 0.19  # per link, matching the mechanics helper's planar arm scale
STEPS = 10000
TIMESTEP_S = 0.001
START_ANGLE_RAD = math.pi / 2.0  # arm starts horizontal, far from rest
# At qpos=0 the links point upward in this model, so hanging rest is pi rad.

ARM_XML = """
<mujoco>
  <option timestep="{timestep}"/>
  <worldbody>
    <body name="link1" pos="0 0 0.6">
      <joint name="joint_0" type="hinge" axis="0 1 0" damping="0.5"/>
      <geom type="capsule" size="0.01 {half}" pos="0 0 {half}" mass="0.1"/>
      <body name="link2" pos="0 0 {link}">
        <joint name="joint_1" type="hinge" axis="0 1 0" damping="0.5"/>
        <geom type="capsule" size="0.01 {half}" pos="0 0 {half}" mass="0.1"/>
      </body>
    </body>
  </worldbody>
</mujoco>
"""


def _single_run() -> dict:
    import mujoco

    half = LINK_LENGTH_M / 2.0
    xml = ARM_XML.format(timestep=TIMESTEP_S, half=half, link=LINK_LENGTH_M)
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)

    data.qpos[0] = START_ANGLE_RAD
    data.qpos[1] = 0.0

    peak_abs_qvel = 0.0
    closest_to_hanging = START_ANGLE_RAD
    for step in range(STEPS):
        mujoco.mj_step(model, data)
        abs_qvel = max(abs(float(v)) for v in data.qvel)
        peak_abs_qvel = max(peak_abs_qvel, abs_qvel)
        dist = abs(abs(float(data.qpos[0])) - math.pi)
        closest_to_hanging = min(closest_to_hanging, dist)
        if step == STEPS - 1000:
            # Marker: start of the final second of simulated time.
            qvel_final_window_start = abs_qvel

    tail_abs_qvel = max(abs(float(v)) for v in data.qvel)
    return {
        "final_qpos": [float(v) for v in data.qpos],
        "final_qvel": [float(v) for v in data.qvel],
        "peak_abs_qvel": peak_abs_qvel,
        "closest_to_hanging_rad": closest_to_hanging,
        "tail_abs_qvel": max(tail_abs_qvel, qvel_final_window_start),
    }


def run_demo() -> dict:
    try:
        import mujoco
    except ImportError as exc:  # pragma: no cover - dependency is optional
        raise SystemExit(
            "MuJoCo is not installed. Run: pip install mujoco"
        ) from exc

    first = _single_run()
    second = _single_run()

    deterministic = (
        first["final_qpos"] == second["final_qpos"]
        and first["final_qvel"] == second["final_qvel"]
    )
    swung_down = first["closest_to_hanging_rad"] < 0.05
    dissipated = first["tail_abs_qvel"] < 0.1 * first["peak_abs_qvel"]

    return {
        "mode": "simulation_only",
        "engine": f"mujoco {mujoco.__version__}",
        "hardware_or_network_access": False,
        "model": "planar_two_link_unactuated_damped",
        "units": {"length": "m", "angles": "rad", "time": "s"},
        "steps": STEPS,
        "timestep_s": TIMESTEP_S,
        "checks": {
            "swung_down_to_hanging": swung_down,
            "energy_dissipated": dissipated,
            "replay_deterministic": deterministic,
        },
        "all_checks_passed": swung_down and dissipated and deterministic,
        "detail": {
            "peak_abs_joint_velocity": round(first["peak_abs_qvel"], 6),
            "tail_abs_joint_velocity": round(first["tail_abs_qvel"], 6),
            "closest_distance_to_hanging_rad": round(
                first["closest_to_hanging_rad"], 6
            ),
            "final_joint_positions": [
                round(v, 6) for v in first["final_qpos"]
            ],
        },
        "boundary": (
            "generic rigid-body physics check only; not a surgical model; "
            "no contact-rich manipulation, tissue, or force-limit validation"
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))
