"""Deterministic context-budget policy for optional advisory reasoning.

This policy is intentionally outside the motion path. It prevents long-lived
advisory context from silently consuming the model window and requires an
explicit, caller-supplied summary before a request crosses the early-compaction
threshold.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def estimate_tokens(text: str) -> int:
    """Return a conservative, dependency-free token estimate for UTF-8 text."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return max(0, math.ceil(len(text.encode("utf-8")) / 4))


@dataclass(frozen=True)
class CompactionDecision:
    estimated_tokens: int
    max_tokens: int
    usage_ratio: float
    compaction_required: bool
    hard_limit_reached: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "estimated_tokens": self.estimated_tokens,
            "max_tokens": self.max_tokens,
            "usage_ratio": round(self.usage_ratio, 6),
            "compaction_required": self.compaction_required,
            "hard_limit_reached": self.hard_limit_reached,
        }


@dataclass(frozen=True)
class ContextCompactionPolicy:
    """Mandate compaction at a configurable 40–50% early threshold."""

    max_tokens: int = 8_192
    trigger_ratio: float = 0.45
    hard_limit_ratio: float = 0.50

    def __post_init__(self) -> None:
        if self.max_tokens < 1:
            raise ValueError("max_tokens must be positive")
        if not 0.40 <= self.trigger_ratio <= 0.50:
            raise ValueError("trigger_ratio must be between 0.40 and 0.50")
        if not self.trigger_ratio <= self.hard_limit_ratio <= 1.0:
            raise ValueError("hard_limit_ratio must be >= trigger_ratio and <= 1")

    def assess(self, estimated_tokens: int) -> CompactionDecision:
        if estimated_tokens < 0:
            raise ValueError("estimated_tokens must not be negative")
        ratio = estimated_tokens / self.max_tokens
        return CompactionDecision(
            estimated_tokens=estimated_tokens,
            max_tokens=self.max_tokens,
            usage_ratio=ratio,
            compaction_required=ratio >= self.trigger_ratio,
            hard_limit_reached=ratio >= self.hard_limit_ratio,
        )

    def assess_text(self, *parts: str) -> CompactionDecision:
        return self.assess(sum(estimate_tokens(part) for part in parts))


@dataclass
class AdvisoryContext:
    """Small explicit context buffer that cannot silently cross the threshold."""

    policy: ContextCompactionPolicy = field(default_factory=ContextCompactionPolicy)
    messages: list[tuple[str, str]] = field(default_factory=list)

    def append(self, role: str, content: str) -> CompactionDecision:
        if not role.strip() or not content.strip():
            raise ValueError("role and content must not be empty")
        candidate = [*self.messages, (role, content)]
        decision = self.policy.assess_text(*(item[1] for item in candidate))
        self.messages.append((role, content))
        return decision

    def assess(self) -> CompactionDecision:
        return self.policy.assess_text(*(item[1] for item in self.messages))

    def require_compacted(self) -> None:
        decision = self.assess()
        if decision.compaction_required:
            raise RuntimeError("advisory context compaction is required before continuing")

    def compact(self, summary: str, *, keep_last: int = 4) -> CompactionDecision:
        if not summary.strip():
            raise ValueError("an explicit summary is required for compaction")
        if keep_last < 0:
            raise ValueError("keep_last must not be negative")
        system_messages = [item for item in self.messages if item[0] == "system"]
        non_system_messages = [item for item in self.messages if item[0] != "system"]
        recent_messages = non_system_messages[-keep_last:] if keep_last else []
        compacted = [*system_messages, ("compaction_summary_untrusted", summary), *recent_messages]
        decision = self.policy.assess_text(*(item[1] for item in compacted))
        if decision.compaction_required:
            raise ValueError("compaction summary does not fit below the early threshold")
        self.messages = compacted
        return decision
