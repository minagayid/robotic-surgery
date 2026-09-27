from robotx.movement import EXTREMITY_NAMES, ExtremityBrain, ExtremityCommand, MovementOrchestrator


def _orchestrator():
    brains = {
        name: ExtremityBrain(name, (offset * 2, offset * 2 + 1), ((-1.0, 1.0),) * 2, (1.0, 1.0))
        for offset, name in enumerate(EXTREMITY_NAMES)
    }
    return MovementOrchestrator(brains)


def _commands(active=EXTREMITY_NAMES, orchestration_offset=0):
    return {
        name: ExtremityCommand(name, 1 + orchestration_offset, 0, 1_000,
                               (0.1, -0.1), (0.5, 0.5))
        for name in active
    }


def test_selective_brain_activation_holds_inactive_joints():
    decision = _orchestrator().orchestrate(
        _commands(("right_arm",)), (0.0,) * 8, now_ns=100,
        active_extremities=("right_arm",),
    )
    assert decision.status == "approved"
    assert decision.active_extremities == ("right_arm",)
    assert decision.effective_joint_positions == (0.0, 0.0, 0.1, -0.1, 0.0, 0.0, 0.0, 0.0)


def test_one_brain_failure_blocks_atomic_bundle():
    commands = _commands()
    commands["left_leg"] = ExtremityCommand(
        "left_leg", 1, 0, 1_000, (2.0, 0.0), (0.5, 0.5)
    )
    decision = _orchestrator().orchestrate(commands, (0.0,) * 8, now_ns=100)
    assert decision.status == "rejected"
    assert any("left_leg:joint_0_position_limit" in reason for reason in decision.reasons)
    assert decision.effective_joint_positions == (0.0,) * 8
