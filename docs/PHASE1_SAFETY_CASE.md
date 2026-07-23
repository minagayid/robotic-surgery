# Phase 1 Safety Case (Draft)

This draft covers only the simulated deterministic skeleton. It is not a
certification claim and does not authorize physical motion.

| Claim | Current control | Evidence | Remaining gap |
|---|---|---|---|
| An expired or replayed command cannot move the simulator | Expiry, bounded duration, and per-source monotonic sequence checks | `test_expired_proposal_is_rejected_without_latching_stop`, `test_execution_must_fit_inside_expiry`, `test_replayed_sequence_is_rejected` | Authenticate transport and persist anti-replay state across restart |
| Loss of required safety state stops motion | Heartbeat, state freshness, hardware-ready, configuration, and E-stop gates; STOP latches | `test_stale_heartbeat_stops_and_latches`, `test_stop_decision_forces_zero_velocity` | Independent watchdog hardware and measured stop time |
| A proposal cannot raise configured motion limits | Immutable runtime limits and deterministic velocity clamp | `test_clamps_velocity_without_changing_limits` | Signed configuration and enforcement in certified drive/safety controller |
| Known unsafe numeric state cannot become actuator motion | Schema, calibration, dimension, confidence, finite-value, position, effort, and proximity checks | `test_calibration_mismatch_stops`, `test_non_finite_input_stops`, fault suite | Fuzzing, redundant encoders, calibrated force/proximity hardware |
| A short command cannot cross a known joint bound under the simple model | End-of-horizon prediction after velocity clamping | `test_predicted_limit_crossing_is_rejected` | Braking-distance model, acceleration/jerk limits, tracking-error bounds |
| Recovery from a stop requires deliberate safe action | Latched stop and acknowledged reset with fresh, still, clear state | `test_stop_reset_requires_deliberate_acknowledgement` | Physical reset circuit, role authorization, reset procedure validation |
| Recorded decisions expose later modification | SHA-256 hash chain verified on read | `test_journal_detects_tampering` | Signed checkpoints, protected storage, capacity controls, export ceremony |

## Fail-safe classification

- `REJECT` handles a proposal that is invalid while trusted state remains safe;
  it produces zero motion for that proposal but does not latch the system.
- `STOP` handles loss or contradiction of safety-relevant state; it produces zero
  motion and latches until explicit, safe reset.
- `CLAMP` never expands a command. It can only reduce velocity to immutable
  configured limits.
- Any exception or process death must be treated by the external watchdog as
  heartbeat loss and result in a controlled stop or power removal.

## Known limitations

The predictive check currently assumes constant velocity over one command
horizon. It does not model acceleration, jerk, brake delay, payload dynamics,
contacts, Cartesian workspace, self-collision, obstacle motion, or controller
tracking error. These must be added and measured before hardware execution.
