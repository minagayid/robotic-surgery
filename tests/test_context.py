from __future__ import annotations

import unittest

from robotic_surgery.context import AdvisoryContext, ContextCompactionPolicy


class ContextCompactionTests(unittest.TestCase):
    def test_compaction_is_required_at_early_threshold(self) -> None:
        policy = ContextCompactionPolicy(max_tokens=100, trigger_ratio=0.45, hard_limit_ratio=0.50)
        self.assertFalse(policy.assess(44).compaction_required)
        decision = policy.assess(45)
        self.assertTrue(decision.compaction_required)
        self.assertFalse(decision.hard_limit_reached)

    def test_context_requires_explicit_compaction_and_preserves_recent_turns(self) -> None:
        context = AdvisoryContext(ContextCompactionPolicy(max_tokens=100, trigger_ratio=0.45, hard_limit_ratio=0.50))
        context.append("system", "Safety rules")
        context.append("user", "x" * 200)
        with self.assertRaises(RuntimeError):
            context.require_compacted()
        context.compact("Prior context was summarized by the caller.", keep_last=0)
        context.require_compacted()
        self.assertEqual(context.messages[-1][0], "compaction_summary_untrusted")


if __name__ == "__main__":
    unittest.main()
