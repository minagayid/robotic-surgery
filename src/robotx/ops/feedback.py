"""Failure-case feedback loop -- closes the ops loop (Section 6).

Real robot experience is higher-value than more human video, so rollout
failures are prioritised for re-collection: each failed episode becomes a
targeted request for more first-party capture / teleop on that instruction, and
successes are added directly to the fine-tuning set.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from ..sim2real.rollout import RolloutLog
from ..types import RobotDemonstration


@dataclass
class FeedbackResult:
    new_finetune_demos: list[RobotDemonstration] = field(default_factory=list)
    recollect_requests: Counter = field(default_factory=Counter)   # instruction -> count
    num_success: int = 0
    num_failure: int = 0

    def priorities(self) -> list[tuple[str, int]]:
        """Instructions ranked by how badly we need more data for them."""
        return self.recollect_requests.most_common()


class FeedbackLoop:
    def ingest(self, logs: list[RolloutLog],
               demos: list[RobotDemonstration] | None = None) -> FeedbackResult:
        result = FeedbackResult()
        demos = demos or []
        demo_by_instr: dict[str, list[RobotDemonstration]] = {}
        for d in demos:
            demo_by_instr.setdefault(d.language_instruction, []).append(d)

        for log in logs:
            if log.success and not log.aborted:
                result.num_success += 1
                for d in demo_by_instr.get(log.instruction, []):
                    result.new_finetune_demos.append(d)
            else:
                result.num_failure += 1
                # prioritise re-collecting data for the failed/aborted task
                result.recollect_requests[log.instruction] += 1
        return result
