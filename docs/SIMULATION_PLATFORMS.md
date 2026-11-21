# Simulation platform trial: Isaac Sim and free alternatives

Trial date: 2026-11-21. Goal: try this repository's software on NVIDIA Isaac
Sim via the cloud, spending nothing (no subscriptions, no payments), and
record what runs, what does not, and the concrete path forward.

## Verdict, corrected after account checks and a real Kaggle run

**Isaac Sim 6.0.1 installed and basic headless physics ran on a free Kaggle
T4 session, but GPU rendering failed and shutdown segfaulted.** This tested
environment is not a demonstrated GPU-rendered Isaac Sim setup. This is a
bounded finding, not proof that every free route is impossible.
Isaac Sim software is free, but cloud compute can still be paid. Its open-source
extensions and additional NVIDIA/Omniverse components have separate terms.

On 21 November 2026, `launchpad.nvidia.com` redirected to NVIDIA Brev. The
Isaac Launchable listing offered Isaac Sim 6.0.1 and Isaac Lab
3.0.0-beta2-post1 on one AWS L40S (48 GB VRAM) at $3.65/hour. No deployment,
payment or subscription was made. This listing is paid, not a free lab.

- Isaac listing: https://brev.nvidia.com/launchable/deploy/now?launchableID=env-35JP2ywERLgqtD0b0MIeK1HnF46
- Official launchable repository and hourly-billing caveat:
  https://github.com/isaac-sim/isaac-launchable
- NVIDIA scope/licensing and cloud-cost explanation:
  https://developer.nvidia.com/isaac/sim

**Correction:** the earlier version wrongly said T4 GPUs have no RT cores and
therefore ruled out all free T4 notebooks. NVIDIA staff describes T4 and A10
as RTX-capable, and NVIDIA publishes a T4 cloud deployment guide. Those
sources do not establish compatibility with the current Isaac version or any
particular hosted notebook. Driver, Vulkan/graphics exposure, Python, GLIBC,
memory and disk support still need an actual run. P100 is a different GPU
and must not be conflated with T4.

- NVIDIA T4 discussion:
  https://forums.developer.nvidia.com/t/issac-sim-rtx-requirements-for-t4-cloud-gpu-and-omniverse-streaming-client/323564
- NVIDIA T4 cloud guide, whose older operating-system example should not be
  treated as a current-version support guarantee:
  https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_advanced_cloud_setup_tencent.html
- Current requirements:
  https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html
- Version-pinned Python installation instructions (6.0.1 requires Python 3.12
  and Linux GLIBC 2.35+):
  https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/install_python.html

## Free Kaggle T4 trial: measured outcome

A private notebook received two Tesla T4 GPUs (15,360 MiB each), NVIDIA driver
580.178.04, and GLIBC 2.39. The test used one active GPU and an isolated
Python 3.12.3 environment, rather than the notebook's default Python 3.13.

- The first serial pip attempt hit its 20-minute time bound downloading the
  large extension caches. That was a download timeout, not a GPU verdict.
- A cached parallel retry installed 166 packages successfully, including the
  Isaac Sim 6.0.1.0 packages. Installation returned exit code 0.
- A real `SimulationApp(headless=True, multi_gpu=False, active_gpu=0)` was
  created. A world with a ground plane and a 0.1 m dynamic cube starting at
  z=1 m ran for 120 steps. The final cube position was approximately
  `[0.000896, -0.003717, 0.049997]` m, satisfying the smoke test's resting-height
  check. This establishes basic rigid-body physics execution, not surgical
  capability or GPU-accelerated physics performance.
- Graphics initialization reported `ERROR_INCOMPATIBLE_DRIVER`, failed
  `vkCreateInstance`, failed to create any GPU devices, and reported that GPU
  Foundation was not initialized. Extension import errors also occurred.
- The script called `world.step(render=True)`, but those calls and the smoke
  test's unfortunately named `ISAAC_WORLD_120_RENDERED_STEPS_OK` marker are
  **not proof of successful rendering**. No valid GPU-rendered image was
  established, and the graphics errors explicitly show initialization failure.
- After the physics check, extension shutdown ended in a Python segmentation
  fault during garbage collection, process exit code -11. A clean process exit
  was not achieved.

Conclusion: package installation and basic headless physics are feasible in
this allocated session. A usable GPU-rendered Isaac Sim 6.0.1 environment was
not achieved in this Kaggle image. The observed problem is graphics/driver
exposure and runtime stability, not evidence that T4 has no RT capability.
This trial does not identify the exact host/container configuration repair,
prove all free providers fail, or validate the repository's robot in Isaac.
The notebook session was stopped after evidence collection. No paid compute,
subscription, or purchase was used.

## What did run, free

**The repository itself, on a plain CPU machine (no GPU, no cost).** All
commands from the README were executed and passed on Python 3.10:

- `python -m unittest discover -s tests` - 65 tests, all passing.
- `python -m robotic_surgery demo --json` - deterministic gate demo: one
  proposal approved, one clamped, one rejected as expired; journal verified.
- `python -m robotic_surgery five-heart-demo --json` - four extremity
  processors plus motion orchestrator, spatial snapshot clear, bundle
  approved in simulation-only mode.
- `python -m robotic_surgery benchmark --iterations 1000` - 1000/1000
  approved, p50 4.3 us, p99 6.7 us, no hardware or network access.
- `python -m robotic_surgery mechanics-demo --force-n 0 10 --json` - planar
  two-link static force analysis, units and assumptions labeled.
- `python -m robotic_surgery learning run --limit 2` - mock learning pipeline
  end to end (ingest, curate, pretrain, retarget, VLA) with mock sources.

**MuJoCo as a free physics backend, on the same CPU machine.** MuJoCo is
free, open source (Apache-2.0), and runs headless on CPU, so it works on
Colab/Kaggle free tiers and ordinary laptops. A new example,
`examples/mujoco_two_link_demo.py`, swings the same planar two-link arm the
mechanics helper analyzes, under real rigid-body dynamics. It checks three
properties that matter to this repository: the arm swings down to hanging
under gravity, energy dissipates under damping, and two identical runs
produce bit-identical final states (the replay determinism the event journal
relies on). All three checks pass with MuJoCo 3.17.0.

## Remaining access paths, without assuming availability

1. **Free hosted T4 notebook:** this Kaggle image failed the GPU-rendering
   check described above. Another environment still needs an actual current-
   version run. Free-tier GPU allocation is not guaranteed, and graphics
   drivers/OS restrictions can differ from ordinary cloud VMs.
2. **Existing suitable local or institution-provided RTX hardware:** software
   access does not itself supply hardware or authorize use of another person's
   computer.
3. **Supermicro LaunchPad evaluation:** the partner still advertises free
   remote evaluation on approval. The form requires first/last name, business
   email, organization, industry, job title, GPU choice and workload summary.
   A specialist follows up. Isaac availability, region eligibility and approval
   are not established; no application was submitted.
   https://www.supermicro.com/en/accelerators/nvidia/launchpad
4. **Paid Brev:** explicitly outside this free-only trial. The actual offered
   Isaac configuration was $3.65/hour, not the earlier aggregator's cheapest
   general GPU price. Do not infer the Isaac price from a provider-wide floor.

The old NVIDIA LaunchPad free-lab catalog is not a verified current Isaac
access route. A discontinued Morpheus lab is documented by NVIDIA staff, but
that statement is specific to Morpheus and must not be generalized into proof
that every partner evaluation has ended.
https://forums.developer.nvidia.com/t/morpheus-ai-and-launchpad/352493

## Roadmap: simulation backends

- **Phase A (free, now):** introduce a `robotic_surgery` physics-backend
  interface (`step(state, control) -> observation`) with the existing
  kinematic simulator and the mock adapters as reference implementations, and
  a MuJoCo adapter as the first physics-accurate backend, following the
  pattern in `examples/mujoco_two_link_demo.py`. Route physics runs through
  the event journal so sessions replay identically.
- **Phase B (free):** cross-validate the deterministic gates kinematic vs
  MuJoCo on the five-heart demo scenario; log every divergence; extend the
  dexterity benchmark with contact/force records from MuJoCo as a tactile
  proxy.
- **Phase C (needs RTX access):** export the reference robot as URDF, build
  the tabletop workcell scene in Isaac Sim/Isaac Lab, replay the same
  scenarios, and use Isaac synthetic data for the POV learning pipeline;
  compare learned-policy results against the MuJoCo baseline.
- **Phase D:** hardware-in-the-loop, per ROADMAP.md Phases 3-6, unchanged.

## Boundary

Nothing in this trial changes the repository's scope statement: research and
simulation only, no hardware driver, no real-time guarantee, no validated
surgical workflow, no clinical-use approval. Simulation success - in the
toy kinematic model, in MuJoCo, or eventually in Isaac Sim - is not evidence
of physical or clinical capability.
