# Adversarial Peer Review: five-processor spatially guarded reference runtime

## Review contract

| Field | Record |
|---|---|
| Frozen version | Local branch `feat/five-heart-spatial-guards`, working-tree revision, 2026-09-09 |
| Purpose and decision | Decide whether the host reference slice correctly rejects the identified unsafe proposal path and whether the requested architecture is represented as a deterministic simulation |
| Scope | `robotic_os/`, tests, CLI demo, movement orchestration, spatial fusion, advisory context policy, and related safety documentation |
| Exclusions | Physical stopping distance, real-time scheduling, sensor accuracy, process isolation, hardware, clinical use, regulatory compliance, and model truthfulness |
| Risk level | High-consequence research software; simulation-only implementation |
| Domain references | `docs/ARCHITECTURE.md`, `docs/SENSOR_FUSION.md`, `docs/IMPLEMENTATION.md`, `docs/PHASE1_SAFETY_CASE.md`, `SECURITY.md`, and the code-review criteria |
| Round cap | Two critique-and-repair rounds plus a final verification pass |
| Reversal condition | Any reproducible accepted out-of-limit command, partial bundle admission, clear snapshot from invalid evidence, or context request crossing the configured early threshold without a compaction error |

## Claim and evidence ledger

| ID | Claim/invariant | Evidence class | Evidence status | Decision relevance |
|---|---|---|---|---|
| C1 | Position and force violations remain rejection reasons | Computational | Demonstrated by targeted unit tests | Fixes the original PR safety defect |
| C2 | Four disjoint extremity processors and one final orchestrator admit bundles atomically in the reference runtime | Computational | Demonstrated by orchestration tests and CLI demo | Load-bearing for the requested movement architecture |
| C3 | A clear spatial snapshot requires fresh calibrated evidence, two modalities, and wave evidence | Computational/documentary | Demonstrated within finite fusion tests | Prevents camera-only or ambiguous clearance from authorizing the bundle |
| C4 | Advisory context requests compact at the default 45% threshold | Computational | Demonstrated by context-policy tests | Bounds long-lived advisory context; does not make model text factual |
| C5 | The implementation is simulation-only and has no external action path | Documentary/code inspection | Supported by current package boundary and tests | Prevents overclaiming readiness for hardware or clinical use |

## Round 1

### Flags

| ID | Severity | Location | Claim/invariant | Attack | Why it matters | Evidence status | Repair test |
|---|---|---|---|---|---|---|---|
| R1-1 | Major | `robotic_os/safety.py`, `SafetySupervisor.authorize` | All hard-limit failures reject a proposal | The implementation collected position/force failures, then replaced the reason list with velocity-clamp reasons; an out-of-range target with in-range requested velocity could therefore be approved | A safety limit can be bypassed in the host reference | Demonstrated by code inspection | Preserve hard-limit reasons and add out-of-range position/force regressions |
| R1-2 | Major | `robotic_os/runtime.py`, `submit_orchestrated` | The new bundle path respects the runtime safety boundary | A separate entry point could bypass the global emergency-stop latch and full-vector limits while calling only per-extremity supervisors | A safety architecture is weakened by an alternate path | Demonstrated by adversarial inspection | Check global stop first and re-check aggregate limits before simulated execution |
| R1-3 | Major | `robotic_os/movement.py`, `FiveHeartOrchestrator` | A complete bundle cannot rely on camera-only or stale evidence | A caller could construct a superficially clear snapshot with one modality or stale timestamp and pass it to orchestration | Spatial inference could be mistaken for verified clearance | Demonstrated by adversarial inspection | Require freshness, two independent modalities, and a wave modality at the final gate |
| R1-4 | Major | `robotic_os/local_model.py` | Advisory context is bounded before it becomes large | The optional advisory client had no early context policy, so a long-lived prompt could consume most of a model window before caller intervention | Long context increases stale/inconsistent advisory state; motion must remain unaffected | Demonstrated by code inspection | Add a 40–50% policy with default 45%, explicit compaction, and threshold tests |

### Resolutions

| Flag | Action | Artifact/test changed | Why this addresses the attack | What it does not establish |
|---|---|---|---|---|
| R1-1 | Repair | `robotic_os/safety.py`; `tests/test_safety.py` | Hard-limit reasons are checked before velocity clamping and remain rejection reasons | It does not certify physical limits or actuator behavior |
| R1-2 | Repair | `robotic_os/runtime.py`; `tests/test_runtime.py` | Orchestrated submissions honor the global stop latch and aggregate position/force/velocity limits | It does not provide independent hardware safety or process isolation |
| R1-3 | Repair | `robotic_os/movement.py`, `robotic_os/spatial.py`; `tests/test_spatial.py`, `tests/test_movement.py` | Final admission denies missing, weak, stale, contradictory, camera-only, or wave-free clearance | It does not validate any real sensor, RF environment, or calibration procedure |
| R1-4 | Repair | `robotic_os/context.py`, `robotic_os/local_model.py`, `docs/CONTEXT_COMPACTION.md`; `tests/test_context.py` | Requests crossing the early threshold fail until an explicit caller-supplied compaction is performed | Compaction is not fact verification and does not remove model hallucination risk |

### Round decision

Proceed to re-attack after the repairs. The original safety defect and three
related boundary gaps have concrete regression coverage.

## Round 2

### Flags

| ID | Severity | Location | Claim/invariant | Attack | Why it matters | Evidence status | Repair test |
|---|---|---|---|---|---|---|---|
| R2-1 | Minor | `robotic_os/context.py`, `AdvisoryContext.compact` | `keep_last=0` drops all non-system messages | Python’s `[-0:]` slice keeps the entire list, so a caller asking for no recent turns could fail to compact below the threshold | It blocks a valid deterministic recovery operation | Demonstrated by the first test run | Handle zero explicitly and retain a regression test |

### Resolutions

| Flag | Action | Artifact/test changed | Why this addresses the attack | What it does not establish |
|---|---|---|---|---|
| R2-1 | Repair | `robotic_os/context.py`; `tests/test_context.py` | Zero now means an empty recent-message set, allowing the explicit summary to reduce context | It does not judge whether a human- or model-supplied summary is accurate |

### Round decision

Proceed to final verification. No Critical or Major flag remains within scope.

## Final verification pass

| Lens | Attack performed | Result | Residual risk |
|---|---|---|---|
| Soundness | Ran the complete unittest suite, compile check, targeted hard-limit tests, wave contradiction/dropout tests, bundle atomicity tests, and CLI demo | 43 tests pass; package compiles; demo reports approved only for a fresh two-wave clear snapshot | Timing and physical dynamics are not modeled |
| Safety and integrity | Tried out-of-limit targets, over-force proposals, stale/weak/contradictory/camera-only evidence, missing processors, replayed bundles, global stop, malformed health/schema inputs, and oversized advisory context | All tested cases fail closed; journal remains verified in demos | Common-cause failures, process crashes, memory corruption, spoofing, and hardware E-stop behavior remain untested |
| Completeness | Checked that the new path is exported, reachable from the CLI, journaled, documented, and covered by CI | Complete for the host reference slice | No hardware-in-loop, fuzz, soak, or independent-controller evidence exists |
| Coherence | Compared README, architecture, sensor-fusion, implementation, safety case, security notes, roadmap, code, and tests | Claims consistently remain simulation/research-only and treat waves as evidence rather than “seeing” | Clinical documentation still requires procedure-specific governance and review |

## Residual evidence-gap ledger

| Item | Status | Why unresolved | Reversal condition | Owner/next evidence |
|---|---|---|---|---|
| Independent process/hardware safety controller | Out of scope | This repository has only a host reference runtime | Hardware-in-loop tests show bounded stop behavior under main-computer failure | Robotics safety engineering; selected controller and hazard analysis |
| Wave sensing accuracy and failure envelope | Unresolved | No target hardware, room, calibration rig, or ground truth dataset is supplied | Controlled sensor bench demonstrates defined missed-obstacle and false-clear bounds | Perception/sensing workstream |
| Clinical effectiveness, sterility, human factors, and regulation | Out of scope | No device, procedure, patient population, or quality system is specified | Independent clinical, quality, ethics, and regulatory evidence | Clinician-led medical-device program |
| Advisory-model truthfulness | Unresolved | Compaction bounds context size but does not verify generated text | Deterministic downstream contracts continue to reject unsupported actions; model remains advisory | ML evaluation and safety-case owners |

## Verdict

**Repairable with residual risks**

Scope-qualified conclusion: the host reference now repairs the identified
position/force safety bug and implements the requested four-extremity plus final
orchestrator pattern with conservative camera-plus-wave spatial gating and an
early context-compaction policy. The result is suitable for offline simulation
and further research review only. It is not evidence of physical, clinical,
real-time, or regulatory readiness. The verdict changes if any tested fail-closed
invariant is contradicted by hardware-in-loop or adversarial integration
evidence.
