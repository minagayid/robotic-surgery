# Simulation fault-injection report

Run `python -m robotic_surgery.fault_benchmark` for eight deterministic scenarios against the actual SafetySupervisor: healthy control, sensor dropout, stale heartbeat, invalid pose dimensions, target outside joint workspace, unauthorized controller source, emergency stop and replayed sequence. Unsafe decisions must reject/stop and emit zero effective velocities. The source fixture and report preserve reasons.

Reproduce: `python -m pytest tests/test_fault_benchmark.py -q`. This complements the existing journal/replay and safety suites. It does not measure collision safety, a physical controller, medical-device performance or clinical feasibility. Workspace collision sweeps, safety timing and richer replay perturbations remain simulation research gates.
