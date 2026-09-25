"""Vision-Language-Action policy (OpenVLA / Octo style) -- Section 4.

The low-level control policy consumes (image observation, language instruction)
and emits a :class:`RobotAction`. Per the design doc, directly imitating human
video does not transfer reliably, so the recipe is:

    pretrain on human-video representations  (weak pseudo-demos)
        -> fine-tune on real robot teleop demos (ground truth)

The mock policy is nearest-neighbor retrieval over mock training records. It
exercises API plumbing only; it is not a validated vision-language-action
model or robot controller. OpenVLA and Octo are candidates for future
integration, not bundled backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

from ..retargeting.representation import VisualEncoder, cosine
from ..types import (
    FrameStack,
    PseudoDemonstration,
    RobotAction,
    RobotDemonstration,
)


def _text_embed(text: str, dim: int = 32) -> np.ndarray:
    """Cheap deterministic bag-of-hashes text embedding for the mock policy."""
    v = np.zeros(dim)
    for tok in text.lower().split():
        v[hash(tok) % dim] += 1.0
    n = np.linalg.norm(v)
    return v / n if n > 0 else v


@dataclass
class _Transition:
    obs_embed: np.ndarray
    text_embed: np.ndarray
    action: RobotAction
    weak: bool


@dataclass
class TrainReport:
    pretrain_transitions: int = 0
    finetune_transitions: int = 0
    epochs: int = 0
    history: list[float] = field(default_factory=list)


class VLAPolicy(ABC):
    @abstractmethod
    def pretrain(self, demos: list[PseudoDemonstration], clips) -> None: ...
    @abstractmethod
    def finetune(self, demos: list[RobotDemonstration], epochs: int = 1) -> TrainReport: ...
    @abstractmethod
    def act(self, obs: FrameStack, instruction: str) -> RobotAction: ...


class MockVLAPolicy(VLAPolicy):
    def __init__(self, encoder: VisualEncoder, text_dim: int = 32):
        self.encoder = encoder
        self.text_dim = text_dim
        self._memory: list[_Transition] = []
        self.report = TrainReport()

    # -- pretraining on weak pseudo-demos ---------------------------------
    def pretrain(self, demos: list[PseudoDemonstration], clips) -> None:
        clip_by_id = {c.clip_id: c for c in clips}
        for demo in demos:
            clip = clip_by_id.get(demo.clip_id)
            if clip is None:
                continue
            frame_embeds = self.encoder.encode_frames(clip.frames)
            txt = _text_embed(demo.language_label, self.text_dim)
            for t, action in enumerate(demo.actions):
                fe = frame_embeds[min(t, len(frame_embeds) - 1)]
                self._memory.append(_Transition(fe, txt, action, weak=True))
        self.report.pretrain_transitions = len(self._memory)

    # -- fine-tuning on real robot demos (ground truth) -------------------
    def finetune(self, demos: list[RobotDemonstration], epochs: int = 1) -> TrainReport:
        added = 0
        for demo in demos:
            txt = _text_embed(demo.language_instruction, self.text_dim)
            for obs, action in zip(demo.observations, demo.actions):
                fe = self.encoder.encode(obs)
                self._memory.append(_Transition(fe, txt, action, weak=False))
                added += 1
        self.report.finetune_transitions = added
        self.report.epochs = epochs
        # report shrinking train error as a stand-in learning curve
        self.report.history = [round(1.0 / (e + 1), 4) for e in range(epochs)]
        return self.report

    # -- inference ---------------------------------------------------------
    def act(self, obs: FrameStack, instruction: str) -> RobotAction:
        if not self._memory:
            # untrained: no-op hold pose, gripper open
            return RobotAction(ee_pose=np.eye(4), gripper=1.0)
        qe = self.encoder.encode(obs)
        qt = _text_embed(instruction, self.text_dim)
        best, best_score = None, -np.inf
        for tr in self._memory:
            # real demos weighted higher than weak pseudo-demos
            w = 1.0 if not tr.weak else 0.5
            score = w * (cosine(qe, tr.obs_embed) + cosine(qt, tr.text_embed))
            if score > best_score:
                best, best_score = tr, score
        return best.action

    def rollout(self, obs_seq: list[FrameStack], instruction: str) -> list[RobotAction]:
        return [self.act(o, instruction) for o in obs_seq]


def build_policy(backend: str, encoder: VisualEncoder) -> VLAPolicy:
    if backend == "mock":
        return MockVLAPolicy(encoder)
    raise NotImplementedError(
        f"Policy backend {backend!r} has no registered implementation. "
        "Only 'mock' is bundled; optional dependencies do not add integrations."
    )
