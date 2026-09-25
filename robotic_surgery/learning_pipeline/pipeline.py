"""End-to-end orchestration of the six-layer Robotic Surgery system.

    sources ─▶ ingest/preprocess ─▶ license gate ─▶ dataset filters
            ─▶ dedup + manifest ─▶ representation pretrain
            ─▶ retarget (weak pseudo-demos) ─▶ VLA pretrain
            ─▶ VLA finetune on robot demos ─▶ sim validation
            ─▶ staged rollout ─▶ failure feedback

Runs entirely on mock backends by default, so ``Pipeline(cfg).run(sources)``
executes the whole loop offline and returns a structured report.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .config import PipelineConfig
from .data.licensing import LicenseGate
from .data.manifest import DatasetManifest
from .data.sources import VideoSource, collect
from .learning.planner import HighLevelPlanner
from .learning.pretrain import RepresentationTrainer
from .learning.vla_policy import build_policy
from .ops.feedback import FeedbackLoop
from .ops.filters import apply_dataset_filters
from .ops.versioning import DatasetVersioner
from .preprocessing.clip_builder import ClipBuilder
from .retargeting.kinematic import KinematicRetargeter
from .retargeting.representation import build_encoder
from .sim2real.rollout import RolloutLog, StagedRollout
from .sim2real.safety import SafetyViolation
from .sim2real.validation import SimValidator
from .types import ClipRecord, RobotDemonstration


@dataclass
class PipelineReport:
    stages: dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, k: str) -> Any:
        return self.stages[k]

    def summary(self) -> dict[str, Any]:
        return self.stages


class Pipeline:
    def __init__(self, cfg: PipelineConfig | None = None):
        self.cfg = cfg or PipelineConfig()
        self.encoder = build_encoder(self.cfg.backends.encoder, seed=self.cfg.seed)
        self.manifest = DatasetManifest()
        self.clip_builder = ClipBuilder(self.cfg)
        self.license_gate = LicenseGate(allow_research_only=True)
        self.retargeter = KinematicRetargeter(self.cfg.retarget)
        self.versioner = DatasetVersioner(self.encoder, self.cfg.ops, self.manifest)
        self.planner = HighLevelPlanner()

    # -- individual stages -------------------------------------------------
    def ingest(self, sources: list[VideoSource], per_source_limit: int | None = None
               ) -> list[ClipRecord]:
        refs = collect(sources, per_source_limit=per_source_limit)
        clips: list[ClipRecord] = []
        for ref in refs:
            built, _ = self.clip_builder.build(ref)
            clips.extend(built)
        return clips

    def curate(self, clips: list[ClipRecord]) -> tuple[list[ClipRecord], dict]:
        report: dict[str, Any] = {}
        licensed, gate = self.license_gate.filter(clips)
        report["license"] = {"allowed": gate.num_allowed, "rejected": gate.rejected}
        filtered, filt_report = apply_dataset_filters(licensed, self.cfg.ops)
        report["filters"] = {k: len(v) for k, v in filt_report.items()}
        commit = self.versioner.commit(filtered)
        report["dataset"] = commit
        return filtered, report

    # -- full loop ---------------------------------------------------------
    def run(self, sources: list[VideoSource], *, per_source_limit: int | None = None,
            robot_demos: list[RobotDemonstration] | None = None,
            eval_instruction: str = "pick up cup",
            validation_episodes: int = 8) -> PipelineReport:
        report = PipelineReport()

        # 1-2. acquire + preprocess
        clips = self.ingest(sources, per_source_limit=per_source_limit)
        report.stages["ingest"] = {"clips": len(clips)}

        # 6 (curation) + 1 (license gate)
        clips, curate_report = self.curate(clips)
        report.stages["curate"] = curate_report

        # 4A. representation pretraining
        pre = RepresentationTrainer(self.encoder).fit(clips, epochs=1)
        report.stages["representation_pretrain"] = {
            "clips": pre.num_clips, "contrastive_margin": pre.contrastive_margin,
        }

        # 3. retarget -> weak pseudo-demos
        pseudo = self.retargeter.retarget_many(clips)
        report.stages["retarget"] = {
            "pseudo_demos": len(pseudo),
            "mean_confidence": round(
                sum(p.confidence for p in pseudo) / len(pseudo), 4) if pseudo else 0.0,
        }

        # 4. Mock policy plumbing; robot_demos defaults to an empty list.
        policy = build_policy(self.cfg.backends.policy, self.encoder)
        policy.pretrain(pseudo, clips)
        robot_demos = robot_demos or []
        ft = policy.finetune(robot_demos, epochs=2)
        report.stages["vla"] = {
            "pretrain_transitions": ft.pretrain_transitions,
            "finetune_transitions": ft.finetune_transitions,
        }

        # high-level planner demo
        plan = self.planner.plan(eval_instruction, clips[0] if clips else None)
        report.stages["planner"] = {
            "goal": plan.goal, "subtasks": [s.instruction for s in plan.subtasks],
        }

        # 5. sim validation
        validator = SimValidator(self.cfg.safety, domain_randomize=True)
        val = validator.validate(policy, eval_instruction, episodes=validation_episodes)
        report.stages["sim_validation"] = {
            "episodes": val.episodes, "success_rate": round(val.success_rate, 3),
            "safety_clamps": val.safety_clamps,
        }

        # 5. staged rollout (gated on sim), then 6. feedback
        rollout = StagedRollout(self.cfg.safety)
        from .sim2real.validation import _KinematicSim
        env = _KinematicSim(seed=self.cfg.seed, randomize=False)

        class _Env:
            simulation_only = True

            @property
            def ee_position_m(self_inner):
                return tuple(env.ee)

            def observe(self_inner):
                return env.observe()

            def step(self_inner, action):
                done = env.step(action)
                return done, done

        try:
            log = rollout.run(policy, _Env(), eval_instruction, val)
        except SafetyViolation as exc:
            log = RolloutLog(instruction=eval_instruction, aborted=True, abort_reason=str(exc))
        report.stages["rollout"] = {
            "steps": len(log.steps), "success": log.success, "aborted": log.aborted,
            "reason": log.abort_reason,
        }
        fb = FeedbackLoop().ingest([log], robot_demos)
        report.stages["feedback"] = {
            "successes": fb.num_success, "failures": fb.num_failure,
            "recollect": fb.priorities(),
        }
        return report
