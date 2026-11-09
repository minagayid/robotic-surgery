# Tactile Data and Dexterity Benchmark (Research Draft)

**Status:** experimental research reference, schema v0.1.0. This is not an adopted standard, validated test method, calibrated sensor interface, medical-device specification, or safety limit.

## Purpose

The ARIA Robot Dexterity call identifies tactile sensing records, benchmarking, performance evaluation, interoperability, and shared test infrastructure as programme-level needs. This document describes a small, inspectable starting point in this repository. It is intended to support discussion with sensor developers, robot-platform teams, independent laboratories, and standards communities; it does not claim that those groups have endorsed the design.

## Implemented in this repository

- `robotic_surgery/dexterity_benchmark.py` defines immutable `TactileFrame`, `DexterityTrial`, and `BenchmarkSummary` records.
- Tactile records include a sensor identifier/model, timestamp and sequence, calibration identifier, coordinate frame, force and torque vectors, uncertainty vectors, and contact probability.
- Values use explicit SI units: force in N, torque in N*m, time in ns. The parser rejects unsupported schema versions, non-SI units, malformed vectors, non-finite values, and negative uncertainty.
- Trial records link tactile frames to a task, platform, trial window, success outcome, operator interventions, and dropped-object count. They enforce per-sensor timestamp/sequence ordering and trial-window bounds.
- `evaluate_trials` provides deterministic trial count, success rate, median duration, mean operator interventions, trial-level drop rate, tactile frame count, maximum and nearest-rank p95 force magnitude, and optional exceedance counts against a caller-supplied benchmark threshold.

The implementation is deliberately standard-library-only. It does not ingest hardware streams, establish calibration validity, determine clinically safe force thresholds, communicate with robot controllers, or prove sensor accuracy.

## Proposed record contract

The v0.1.0 JSON record is versioned and names its units rather than relying on conventions:

```json
{
  "schema_version": "0.1.0",
  "sensor": {"id": "sensor-01", "model": "model-name"},
  "time": {"timestamp_ns": 123456789, "sequence": 42},
  "calibration_id": "calibration-revision",
  "coordinate_frame": "tool0",
  "units": {"force": "N", "torque": "N*m", "time": "ns"},
  "force_n": [0.0, 0.0, 1.2],
  "torque_nm": [0.0, 0.0, 0.03],
  "force_uncertainty_n": [0.1, 0.1, 0.2],
  "torque_uncertainty_nm": [0.01, 0.01, 0.02],
  "contact_probability": 0.95
}
```

This is a minimal proposal, not a complete sensor standard. A production interchange specification would need community decisions about sensor modality/type, sample rate, clock synchronization and clock quality, calibration method and validity interval, coordinate transforms, saturation/clipping flags, missing-data encoding, raw versus processed signals, contact patch representation, temperature/drift, uncertainty semantics, data dictionaries, privacy, provenance, and backwards compatibility.

## Benchmark protocol proposal

The current code scores recorded trial summaries. A full benchmark should add controlled task definitions, fixtures, robot/platform descriptions, object/material properties, test environment constraints, reset rules, operator qualifications, repetitions, data-quality gates, and pre-registered scoring. Candidate non-clinical dexterity tasks include:

1. constrained pick-and-place with contact-aware grasping;
2. in-hand reorientation and stable regrasp;
3. compliant insertion/alignment under limited visibility;
4. surface following or tracing with controlled contact;
5. slip detection and recovery during object transfer.

Tasks must be selected with participating users and test sites. No single task score should be presented as a general measure of dexterity.

## Metrics and reporting

Report per-task and per-platform results, not only a pooled leaderboard:

- task completion success and failure taxonomy;
- completion-time median and distribution;
- operator intervention and takeover rate;
- dropped-object and recovery rates;
- force/torque distributions, peak and p95 values;
- benchmark-threshold exceedance count (explicitly a research metric, never a medical safety limit);
- tactile data completeness, timestamp monotonicity, calibration coverage, sensor dropout and clipping;
- repeatability across trials, operators, platforms, and test sites;
- confidence intervals and sample counts.

A benchmark release should publish raw or appropriately governed data, task protocol, analysis code, metadata, known limitations, and a reproducible environment. Comparisons must disclose hardware/software versions, sensor configuration, calibration, operator experience, trial exclusions, and any use of synthetic or simulated data.

## Validation required before claiming interoperability

1. Review the schema with multiple sensor and robot developers.
2. Produce independent writers/readers and machine-readable conformance tests.
3. Test at least three distinct sensing implementations and two robot/platform configurations, where access is secured.
4. Run the same task protocol at two independent test sites.
5. Quantify data loss, calibration/coordinate-frame ambiguity, timing error, repeatability, and score sensitivity.
6. Publish a versioned validation report and change-control process.

These are proposed project targets, not completed validation. The current repository contains no tactile hardware adapters, robotic platform drivers, real sensor datasets, or multi-site evidence.

## Safety and scope

This is a general dexterous-robotics research benchmark. It is not a surgical task specification and must not be used to set patient-contact force limits or authorize medical autonomy. Any surgical application requires a separate intended-use definition, clinical and regulatory review, independent device-specific risk controls, and appropriate bench/preclinical/clinical evidence. The project's existing surgical safety boundaries remain in force.

## Related files

- [Implemented software boundary](../README.md)
- [Surgical program charter](../SURGICAL_PROGRAM.md)
- [Research and clinical validation boundaries](surgical/VALIDATION_CLINICAL.md)
- [Security and safety model](../SECURITY.md)
