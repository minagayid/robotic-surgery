# Phase 1 host-reference safety case

> Research and simulation only. This is not a medical-device safety case and
> does not authorize hardware, patient, animal, or clinical use.

## Claim

Within the tested host simulator, motion proposals are either rejected, stopped,
approved, or velocity-clamped according to explicit deterministic limits. The
runtime has no external-action path.

## Safety argument

| Hazard | Local control | Evidence |
|---|---|---|
| Replayed command | Per-source monotonic sequence check | `test_replayed_sequence_is_rejected` |
| Stale state/heartbeat | Freshness timeout | `test_stale_heartbeat_is_rejected` |
| Expired command | Expiry and duration-fit checks | expiry tests |
| Wrong source or calibration | Allowlist and calibration identity | `test_unknown_source_and_calibration_are_rejected` |
| Excess velocity | Clamp to configured limit | `test_excess_velocity_is_clamped_without_raising_limits` |
| Position or force over-limit | Reject before simulated execution | limit checks in safety supervisor |
| Unsafe proximity or sensor fault | Reject before execution | proximity and sensor-health gates |
| Emergency stop | Latched stop requiring explicit reset | emergency-stop tests |
| Event tampering | Hash-chain verification | journal tamper test |
| Model-generated unsafe action | Model client is outside runtime/safety path | local-model contract and architecture |
| Extremity proposal contaminates another extremity | Disjoint joint ownership and per-extremity validation | `test_all_four_processors_and_orchestrator_admit_atomically` |
| Partial multi-extremity command | Final orchestrator requires all four processors and one orchestration ID | missing-processor and atomic-bundle tests |
| Camera perception hallucination | Clear requires fresh independent evidence including a wave modality | spatial fusion tests |
| Wave or camera contradiction | Unknown snapshot with `stop_required`; orchestrator rejects it | contradiction test |
| Oversized advisory context | Explicit compaction at 45% default threshold | context policy tests |

## Residual risks

The host reference does not prove physical stopping distance, actuator behavior,
electrical safety, timing determinism, sensor correctness, sterility,
human-factors usability, clinical effectiveness, or regulatory compliance. Those
require a defined device, independent safety hardware, controlled test fixtures,
quality-system records, and procedure-specific evidence.

The five-processor implementation also does not prove isolation under process
crash, shared-memory corruption, scheduler starvation, network faults, or
common-cause sensor failures. Those are promotion blockers for any physical
implementation.

## Promotion rule

No code in this package may be promoted to hardware control merely because the
unit tests or benchmark pass. Promotion requires a new hazard review,
independent safety-controller design, hardware-in-loop testing, fault-injection,
configuration control, and the appropriate clinical, ethics, quality, and
regulatory approvals.
