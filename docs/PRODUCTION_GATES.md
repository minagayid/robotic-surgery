# Production gate evidence

`robotic_os.release_gate` is an evidence evaluator, not a certifier. It returns
`blocked` until the exact target robot/workcell, certified safety controller,
approved calibration, independently verified hardware-in-loop run, long-duration
soak report, and separate release review are all present. Even a complete
manifest returns `production_approved: false`; approval belongs to the named
safety, quality, and operational authorities.

Run the evaluator with:

```powershell
python -m robotic_os release-gate docs/production-gate-manifest.example.json --json
```

The soak report includes an evidence digest and must include at least one
rejected injected fault. Editing its result, iteration count, or fault outcome
makes the long-duration check fail. The current default requires 86,400
deterministic iterations (a 24-hour virtual workload); it does not claim 24
hours of real-time or hardware evidence.

The following remain external gates and cannot be satisfied by this repository
alone:

1. select and freeze the robot, drives, sensors, workcell, and intended use;
2. complete the hazard analysis and map the independent controller to a
   certified safety PLC/drive function and physical emergency-stop circuit;
3. approve target-hardware calibration and configuration provenance;
4. execute independent HIL fault, timing, recovery, and endurance validation;
5. complete quality, safety, clinical/operational, and change-control review.
