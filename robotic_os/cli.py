"""Command-line entrypoint for the offline reference runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import run_benchmark
from .scenarios import run_demo, run_five_heart_demo
from .workcell import DEFAULT_WORKCELL_PROFILE


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

    workcell = subparsers.add_parser(
        "workcell-info",
        help="show the concrete simulation workcell and safety boundary",
    )
    workcell.add_argument("--json", action="store_true", help="emit compact JSON")

    benchmark = subparsers.add_parser("benchmark", help="benchmark local safety decisions")
    benchmark.add_argument("--iterations", type=int, default=1_000)
    benchmark.add_argument("--json", action="store_true", help="emit compact JSON")

    args = parser.parse_args(argv)
    if args.command == "demo":
        result = run_demo(args.journal)
    elif args.command == "five-heart-demo":
        result = run_five_heart_demo(args.journal)
    elif args.command == "workcell-info":
        result = DEFAULT_WORKCELL_PROFILE.to_dict()
    else:
        result = run_benchmark(args.iterations)
    print(json.dumps(result, separators=(",", ":") if args.json else None, indent=None if args.json else 2))
    return 0
