"""``robotx`` command-line interface.

Subcommands
-----------
* ``robotx run``       -- run the full 6-layer pipeline end-to-end (mock backends).
* ``robotx sources``   -- list built-in compliant source types.
* ``robotx plan GOAL`` -- show the high-level planner's task decomposition.
* ``robotx config``    -- print the effective configuration as YAML.
"""

from __future__ import annotations

import argparse
import json
import sys

from .config import dump_config, load_config
from .data.sources import build_source
from .learning.planner import HighLevelPlanner
from .movement import demo_selective_movement
from .spatial_4d import SpatialRecognitionSystem
from .pipeline import Pipeline

_DEFAULT_SOURCES = [
    {"type": "research", "name": "ego4d", "root": "datasets"},
    {"type": "first_party", "capture_dir": "captures"},
]


def _cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    specs = json.loads(args.sources) if args.sources else _DEFAULT_SOURCES
    sources = [build_source(s) for s in specs]
    report = Pipeline(cfg).run(
        sources,
        per_source_limit=args.limit,
        eval_instruction=args.instruction,
    )
    print(json.dumps(report.summary(), indent=2, default=str))
    return 0


def _cmd_sources(_: argparse.Namespace) -> int:
    print("Compliant source types (Layer 1):")
    for name, desc in [
        ("official_api", "Public video via an official platform API (YouTube Data API, ...)"),
        ("research", "Pre-licensed egocentric datasets (ego4d, epic_kitchens, ssv2, ...)"),
        ("licensed", "Creator video licensed for AI training with consent/royalties"),
        ("first_party", "Our own paid, consented head/chest-cam captures (cleanest)"),
    ]:
        print(f"  {name:14s} {desc}")
    return 0


def _cmd_plan(args: argparse.Namespace) -> int:
    plan = HighLevelPlanner().plan(args.goal)
    print(f"Goal: {plan.goal}")
    for i, s in enumerate(plan.subtasks, 1):
        obj = f"  [grounds: {s.grounded_object}]" if s.grounded_object else ""
        print(f"  {i}. {s.instruction}{obj}")
    return 0


def _cmd_config(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    dump_config(cfg, "/dev/stdout")
    return 0


def _cmd_spatial_demo(args: argparse.Namespace) -> int:
    engine = SpatialRecognitionSystem(mode=args.mode)
    snapshot = engine.fuse(
        engine.demo_measurements(),
        now_ns=1_000,
        calibration_id="demo-cal",
        region_id="demo",
        mode=args.mode,
    )
    print(json.dumps(snapshot.to_dict(), indent=2))
    return 0


def _cmd_movement_demo(_: argparse.Namespace) -> int:
    print(json.dumps(demo_selective_movement().to_dict(), indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="robotx",
                                description="POV Video -> Robot Learning System")
    sub = p.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run the full pipeline end-to-end")
    run.add_argument("--config", help="path to a YAML config", default=None)
    run.add_argument("--sources", help="JSON list of source specs", default=None)
    run.add_argument("--limit", type=int, default=2, help="clips per source")
    run.add_argument("--instruction", default="pick up cup", help="eval instruction")
    run.set_defaults(func=_cmd_run)

    src = sub.add_parser("sources", help="list compliant source types")
    src.set_defaults(func=_cmd_sources)

    pl = sub.add_parser("plan", help="show high-level task decomposition")
    pl.add_argument("goal", help="e.g. 'make coffee'")
    pl.set_defaults(func=_cmd_plan)

    cf = sub.add_parser("config", help="print effective config as YAML")
    cf.add_argument("--config", default=None)
    cf.set_defaults(func=_cmd_config)

    spatial = sub.add_parser("spatial-demo", help="run the offline 360 4D spatial reference slice")
    spatial.add_argument("--mode", choices=["eco", "normal", "degraded"], default="normal")
    spatial.set_defaults(func=_cmd_spatial_demo)

    movement = sub.add_parser("movement-demo", help="run the offline selective extremity-brain demo")
    movement.set_defaults(func=_cmd_movement_demo)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
