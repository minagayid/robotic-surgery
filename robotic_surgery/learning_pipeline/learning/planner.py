"""High-level reasoning / planning (Section 4).

A separate VLM/LLM module that decomposes a high-level instruction ("make
coffee") into a sequence of atomic subtasks the low-level VLA policy can
execute, grounds each subtask in the current scene, and replans on failure.
Kept separate from low-level control because it runs at a much lower frequency.

The mock planner decomposes via a small task library and simple label matching
against mock scene records. Language models are potential future integrations,
not bundled backends.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..types import ClipRecord, ObjectTrack

# a tiny hand-authored task -> subtask library (an LLM generates this in prod)
_TASK_LIBRARY: dict[str, list[str]] = {
    "make coffee": [
        "pick up cup", "place cup under machine", "press brew button",
        "wait for brew", "pick up cup",
    ],
    "clear the table": ["pick up plate", "place plate in rack", "wipe surface"],
    "pour a drink": ["pick up bottle", "pour liquid", "put down bottle"],
}


@dataclass
class Subtask:
    instruction: str
    grounded_object: str | None = None
    status: str = "pending"          # pending | active | done | failed


@dataclass
class Plan:
    goal: str
    subtasks: list[Subtask] = field(default_factory=list)

    @property
    def next_pending(self) -> Subtask | None:
        for s in self.subtasks:
            if s.status in ("pending", "active"):
                return s
        return None

    @property
    def complete(self) -> bool:
        return all(s.status == "done" for s in self.subtasks)


class HighLevelPlanner:
    def decompose(self, goal: str) -> list[str]:
        """LLM-style task decomposition (mock: nearest library entry)."""
        g = goal.lower().strip()
        if g in _TASK_LIBRARY:
            return list(_TASK_LIBRARY[g])
        # fuzzy: match on shared keywords
        best, best_overlap = None, 0
        goal_words = set(g.split())
        for key, steps in _TASK_LIBRARY.items():
            overlap = len(goal_words & set(key.split()))
            if overlap > best_overlap:
                best, best_overlap = steps, overlap
        return list(best) if best else [goal]

    def ground(self, subtask: str, scene_objects: list[ObjectTrack]) -> str | None:
        """VLM-style grounding: bind a subtask to a visible object."""
        labels = [o.label for o in scene_objects]
        for label in labels:
            if label in subtask:
                return label
        return labels[0] if labels else None

    def plan(self, goal: str, scene: ClipRecord | None = None) -> Plan:
        objs = scene.object_tracks if scene else []
        subtasks = [
            Subtask(instruction=s, grounded_object=self.ground(s, objs))
            for s in self.decompose(goal)
        ]
        return Plan(goal=goal, subtasks=subtasks)

    def replan(self, plan: Plan, failed: Subtask, scene: ClipRecord | None = None) -> Plan:
        """Error recovery: mark the failed subtask and retry it once at the front."""
        failed.status = "failed"
        objs = scene.object_tracks if scene else []
        retry = Subtask(instruction=failed.instruction,
                        grounded_object=self.ground(failed.instruction, objs))
        idx = plan.subtasks.index(failed)
        plan.subtasks.insert(idx + 1, retry)
        return plan
