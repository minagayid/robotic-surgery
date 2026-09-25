"""Approach A -- visual representation learning (R3M / VIP / VC-1 style).

A :class:`VisualEncoder` maps frames to an embedding. A real encoder could be
evaluated on human video, but this module does not establish that such features
transfer to a robot or reduce its demonstration needs.

The mock encoder is a deterministic, fixed random projection of a compact frame
descriptor. It exercises plumbing and supplies the mock dedup embedding; it is
not a learned visual representation. R3M/VIP/VC-1 are candidate integrations,
not bundled backends.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

import numpy as np

from ..types import FrameStack


class EncoderBackend(str, Enum):
    MOCK = "mock"
    R3M = "r3m"
    VIP = "vip"
    VC1 = "vc1"


class VisualEncoder(ABC):
    embed_dim: int

    @abstractmethod
    def encode(self, stack: FrameStack) -> np.ndarray:
        """Return a per-clip embedding of shape (embed_dim,)."""

    def encode_frames(self, stack: FrameStack) -> np.ndarray:
        """Return per-frame embeddings (T, embed_dim). Default: broadcast clip embed."""
        e = self.encode(stack)
        return np.tile(e, (stack.num_frames, 1))


class MockVisualEncoder(VisualEncoder):
    def __init__(self, embed_dim: int = 128, seed: int = 0):
        self.embed_dim = embed_dim
        rng = np.random.default_rng(seed)
        # fixed random projection from a 48-d frame descriptor
        self._proj = rng.standard_normal((48, embed_dim)) / np.sqrt(48)

    def _descriptor(self, frame: np.ndarray) -> np.ndarray:
        # 4x4 spatial grid x 3 channels = 48-d colour-layout descriptor
        h, w = frame.shape[0], frame.shape[1]
        gh, gw = max(1, h // 4), max(1, w // 4)
        cells = []
        for i in range(4):
            for j in range(4):
                cell = frame[i * gh:(i + 1) * gh, j * gw:(j + 1) * gw]
                cells.append(cell.reshape(-1, 3).mean(axis=0) if cell.size else np.zeros(3))
        return np.concatenate(cells) / 255.0

    def encode(self, stack: FrameStack) -> np.ndarray:
        frames = stack.frames
        desc = np.mean([self._descriptor(f) for f in frames], axis=0)
        emb = desc @ self._proj
        norm = np.linalg.norm(emb)
        return emb / norm if norm > 0 else emb


def build_encoder(backend: str, embed_dim: int = 128, seed: int = 0) -> VisualEncoder:
    if backend == EncoderBackend.MOCK:
        return MockVisualEncoder(embed_dim=embed_dim, seed=seed)
    raise NotImplementedError(
        f"Encoder backend {backend!r} has no registered implementation. "
        "Only 'mock' is bundled; optional dependencies do not add integrations."
    )


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))
