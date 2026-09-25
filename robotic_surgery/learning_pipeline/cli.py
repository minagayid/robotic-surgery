"""Learning subcommands exposed through the ``robotic-surgery`` CLI.

Subcommands
-----------
* ``robotic-surgery learning run``       -- run the full pipeline end-to-end (mock backends).
* ``robotic-surgery learning sources``   -- list configured source types.
* ``robotic-surgery learning plan GOAL`` -- show the high-level planner's task decomposition.
* ``robotic-surgery learning config``    -- print the effective configuration as YAML.
"""

from __future__ import annotations

import argparse
import json
import sys

import yaml

from .config import load_config
from .data.sources import build_source
from .learning.planner import HighLevelPlanner
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
    print("Source adapter types (mock references only; no network or video-file reader):")
    for name, desc in [
        ("official_api", "Mock reference type; no platform API request"),
        ("research", "Synthetic dataset label; does not inspect local files or access rights"),
        ("licensed", "Synthetic caller reference; does not verify licensing or consent"),
        ("first_party", "Synthetic directory label; does not inspect media or consent"),
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
    sys.stdout.write(yaml.safe_dump(cfg.to_dict(), sort_keys=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="robotic-surgery learning",
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
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
