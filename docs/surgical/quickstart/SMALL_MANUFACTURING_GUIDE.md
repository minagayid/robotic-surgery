# Small Manufacturing Guide

> Research hardware only. Clinical-intent hardware requires controlled design
> transfer, qualified suppliers, validated processes, and formal quality release.

## Build sequence

1. **Freeze the configuration.** Approve the BOM, drawings, materials, firmware,
   calibration method, risk controls, and acceptance limits for one prototype.
2. **Qualify suppliers.** Trace motors, encoders, brakes, bearings, structural
   parts, force sensors, cables, sterile materials, and critical firmware.
3. **Inspect incoming parts.** Verify revision, lot/serial, certificates, critical
   dimensions, finish, shelf life, damage, and change status; quarantine failures.
4. **Build joint modules.** Assemble bearings, transmission, motor, brake,
   encoders, temperature sensor, hard stops, and harness. Record preload, backlash,
   torque, lubricant/adhesive lot, fastener torque, and test results.
5. **Assemble the arm.** Build from base outward in a datum fixture. Verify cable
   bend radius, guards, joint zero, brake holding, manual release, and protective
   earth before powered motion.
6. **Build sterile interfaces separately.** Use controlled clean assembly for
   adapters and instruments. Inspect latch features, tendon pretension, retained
   parts, output travel, tip force, insulation, and manual release.
7. **Provision software and calibration.** Install only a signed compatible
   bundle. Generate calibration with traceable metrology and bind it to the exact
   arm/instrument serial number.
8. **Run end-of-line acceptance.** Test build identity, electrical safety, locks,
   brakes, workspace, loaded tip accuracy, thermal behavior, instrument identity,
   stale commands, sensor disagreement, power loss, emergency stop, logging, and
   recovery.
9. **Release or quarantine.** Quality reviews the complete build record. Failed or
   incomplete units cannot be used, repaired, or recalibrated without disposition.

## Minimum controlled stations

| Station | Main controls |
|---|---|
| Receiving/quarantine | Part identity, certificates, lot/serial, damage and segregation |
| Mechanical assembly | Calibrated torque tools, fixtures, cleanliness and traveler |
| ESD electronics | Grounding, approved firmware, crimp/solder controls |
| Clean instrument area | Material and process trace, particle/soil prevention |
| Guarded motion cell | Physical guarding, remote enable, emergency stop and metrology |
| Provisioning/release | Signed builds, calibration binding and independent quality review |

## Never improvise

- substitute a material, supplier, motor, encoder, brake, lubricant, adhesive,
  coating, cable, connector, firmware, sterilization process, or calibration;
- compensate a bad dimension with an undocumented calibration adjustment;
- bypass a failed safety test to complete a build;
- reuse a single-use part or over-cycle a reusable part; or
- connect a research unit to a person or animal.

For the full process, see [Manufacturing and Assembly Guide](../MANUFACTURING_AND_ASSEMBLY_GUIDE.md).
