"""Command-line entrypoint for the offline reference runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import run_benchmark
from .mechanics import planar_two_link_static_load
from .scenarios import run_demo, run_five_heart_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Robotic Surgery offline simulation runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run the deterministic safety demo")
    demo.add_argument("--journal", type=Path, default=Path("runtime-data") / "demo-events.jsonl")
    demo.add_argument("--json", action="store_true", help="emit compact JSON")

    five_heart = subparsers.add_parser(
        "five-heart-demo",
        help="run the four-extremity plus orchestration simulation",
    )
    five_heart.add_argument("--journal", type=Path, default=Path("runtime-data") / "five-heart-events.jsonl")
    five_heart.add_argument("--json", action="store_true", help="emit compact JSON")

    benchmark = subparsers.add_parser("benchmark", help="benchmark local safety decisions")
    benchmark.add_argument("--iterations", type=int, default=1_000)
    benchmark.add_argument("--json", action="store_true", help="emit compact JSON")

    mechanics = subparsers.add_parser(
        "mechanics-demo", help="calculate idealized static loads for a planar two-link arm"
    )
    mechanics.add_argument("--links-m", nargs=2, type=float, default=(0.2, 0.18), metavar=("L1", "L2"))
    mechanics.add_argument("--angles-rad", nargs=2, type=float, default=(0.0, 0.0), metavar=("Q1", "Q2"))
    mechanics.add_argument("--force-n", nargs=2, type=float, default=(0.0, 5.0), metavar=("FX", "FY"))
    mechanics.add_argument("--json", action="store_true", help="emit compact JSON")

    learning = subparsers.add_parser("learning", help="run the offline data and learning pipeline")
    learning.add_argument("learning_args", nargs=argparse.REMAINDER)

    args = parser.parse_args(argv)
    if args.command == "learning":
        from .learning_pipeline.cli import main as learning_main

        return learning_main(args.learning_args)
    if args.command == "demo":
        result = run_demo(args.journal)
    elif args.command == "five-heart-demo":
        result = run_five_heart_demo(args.journal)
    elif args.command == "mechanics-demo":
        result = {
            "model": "planar_two_link_static_external_force",
            "units": {"length": "m", "force": "N", "torque": "N*m", "angles": "rad"},
            "assumptions": [
                "rigid planar two-link arm",
                "static external end-effector force only",
                "gravity, inertia, friction, compliance, and contact uncertainty omitted",
                "analysis only; output is not an actuator command or safety limit",
            ],
            **planar_two_link_static_load(args.links_m, args.angles_rad, args.force_n).to_dict(),
        }
    else:
        result = run_benchmark(args.iterations)
    print(json.dumps(result, separators=(",", ":") if args.json else None, indent=None if args.json else 2))
    return 0
