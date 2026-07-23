# ADR-009: Phase 1 Reference Runtime Language

- Status: Provisional
- Date: 2026-07-23
- Review trigger: target compute and robot selected

## Context

The deterministic contracts and fail-closed behavior need executable evidence
now. The available offline environment includes Python 3.12 and no Rust or C++
compiler. ADR-001 has not selected the production real-time platform.

## Decision

Build the first host-side behavior reference in dependency-free Python. Keep all
hardware access behind a narrow actuator protocol, use monotonic time, and test
the safety state machine entirely offline. Do not run Python in the final hard
real-time servo or independent safety zone without evidence that it meets the
required timing and assurance level.

## Consequences

- Safety behavior, contracts, replay fixtures, and fault cases become executable
  before a hardware choice.
- The current code is portable and needs no package registry or Internet route.
- Timing results from this implementation cannot establish hard real-time
  suitability.
- The production controller will likely be reimplemented in a compiled language;
  it must pass the same contract and fault fixtures plus target-specific timing
  tests.
