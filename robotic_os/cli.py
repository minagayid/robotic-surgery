"""Command-line entrypoint for the offline reference runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import run_benchmark
from .scenarios import run_demo, run_five_heart_demo
from .soak import run_soak
from .release_gate import evaluate_release, load_manifest
from .workcell import DEFAULT_WORKCELL_PROFILE
from .spatial_4d import SpatialRecognitionSystem


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="RobotX offline simulation runtime")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="run the deterministic safety demo")
    demo.add_argument("--journal", type=Path, default=Path("runtime-data") / "demo-events.jsonl")
    demo.add_argument("--json", action="store_true", help="emit compact JSON")

    five_heart = subparsers.add_parser(
        "five-heart-demo",
        help="run the hierarchical extremity-coordination simulation",
    )
    five_heart.add_argument("--journal", type=Path, default=Path("runtime-data") / "five-heart-events.jsonl")
    five_heart.add_argument("--json", action="store_true", help="emit compact JSON")

    spatial = subparsers.add_parser(
        "spatial-4d-demo",
        help="run the offline 360-degree 4D spatial recognition simulation",
    )
    spatial.add_argument("--mode", choices=["eco", "normal", "degraded"], default="normal")
    spatial.add_argument("--json", action="store_true", help="emit compact JSON")

    workcell = subparsers.add_parser(
        "workcell-info",
        help="show the concrete simulation workcell and safety boundary",
    )
    workcell.add_argument("--json", action="store_true", help="emit compact JSON")

    benchmark = subparsers.add_parser("benchmark", help="benchmark local safety decisions")
    benchmark.add_argument("--iterations", type=int, default=1_000)
    benchmark.add_argument("--json", action="store_true", help="emit compact JSON")

    soak = subparsers.add_parser("soak", help="run deterministic safety soak and fault checks")
    soak.add_argument("--iterations", type=int, default=10_000)
    soak.add_argument("--fault-interval", type=int, default=1_000)
    soak.add_argument("--json", action="store_true", help="emit compact JSON")

    gate = subparsers.add_parser("release-gate", help="evaluate production evidence without granting approval")
    gate.add_argument("manifest", type=Path)
    gate.add_argument("--minimum-soak-iterations", type=int, default=86_400)
    gate.add_argument("--json", action="store_true", help="emit compact JSON")

    args = parser.parse_args(argv)
    if args.command == "demo":
        result = run_demo(args.journal)
    elif args.command == "five-heart-demo":
        result = run_five_heart_demo(args.journal)
    elif args.command == "spatial-4d-demo":
        engine = SpatialRecognitionSystem(mode=args.mode)
        result = engine.fuse(
            engine.demo_measurements(),
            now_ns=1_000,
            calibration_id="demo-cal",
            region_id="demo",
            mode=args.mode,
        ).to_dict()
    elif args.command == "workcell-info":
        result = DEFAULT_WORKCELL_PROFILE.to_dict()
    elif args.command == "benchmark":
        result = run_benchmark(args.iterations)
    elif args.command == "soak":
        result = run_soak(iterations=args.iterations, fault_interval=args.fault_interval)
    else:
        result = evaluate_release(load_manifest(args.manifest), minimum_soak_iterations=args.minimum_soak_iterations).to_dict()
    print(json.dumps(result, separators=(",", ":") if args.json else None, indent=None if args.json else 2))
    return 0
