# Simulation platform trial: Isaac Sim and free alternatives

Trial date: 2026-11-21. Goal: try this repository's software on NVIDIA Isaac
Sim via the cloud, spending nothing (no subscriptions, no payments), and
record what runs, what does not, and the concrete path forward.

## Verdict

**Isaac Sim cannot currently run free in the cloud.** The software itself is
free and open source (Apache-2.0; Isaac Sim 6.0.1 and Isaac Lab at trial date),
but it requires an NVIDIA GPU with RT cores, and no free cloud tier provides
one:

- Minimum supported GPU is RTX 4080-class with 16 GB VRAM; GPUs without RT
  cores (A100, H100) are explicitly unsupported.
  Source: https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html
- Free cloud GPUs (Google Colab, Kaggle) are T4/P100 class - no RT cores, so
  Isaac Sim will not run on them.
- NVIDIA's own staff confirmed on the developer forums (Feb 2025): "I'm not
  aware of a completely free option for cloud deployment of Isaac Sim."
  Source: https://forums.developer.nvidia.com/t/how-can-i-use-nvidia-isaac-sim-on-cloud-free/324541
- The official Isaac Launchable path (VS Code + streamed Isaac Sim UI in the
  browser, via NVIDIA Brev) is pay-by-the-hour; its README says so directly
  and advises stopping instances when idle.
  Source: https://github.com/isaac-sim/isaac-launchable
- All other official cloud targets (AWS, Azure, GCP, Tencent, Alibaba, Baidu,
  Volcano Engine) are ordinary paid GPU instances.
  Source: https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_cloud.html

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

## Free paths to real Isaac Sim, ranked

1. **NVIDIA LaunchPad** (https://launchpad.nvidia.com) - free, time-boxed
   hands-on labs on NVIDIA-hosted infrastructure, accessed by application.
   Lab catalog changes over time; check whether an Isaac Sim lab is currently
   offered before counting on it.
2. **A local RTX machine** (university lab, workplace, or a friend's gaming
   PC with an RTX card) - the Isaac Sim download is free; the GPU is the only
   gate.
3. **Cheapest paid path when a small budget exists (not in scope for the
   free-only trial):** NVIDIA Brev Isaac Launchable on an L4/A10G-class
   instance. Third-party comparison lists Brev's cheapest on-demand rate at
   about $0.35/hr with per-second billing; verify current pricing on Brev
   before launching, and stop the instance when idle.
   Source: https://computecomparison.com/provider/brev-dev
4. **Not viable:** Colab/Kaggle free GPUs (no RT cores) and generic
   free-tier CPU VMs.

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
