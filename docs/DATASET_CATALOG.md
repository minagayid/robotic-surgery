# Offline surgical dataset catalog

Updated 2026-09-09. This is a research-inventory and ingestion guide, not an
approval to use any dataset for patient care or robot actuation. Availability,
release contents, consent scope, licensing, and challenge rules can change;
pin the exact provider release and re-check the terms before downloading.

## The important boundary

Public surgical video can teach visual representations, workflow phases,
instrument identity, scene understanding, and skill-assessment signals. It does
not, by itself, teach a safe robot policy. A human POV frame is not a calibrated
robot pose, a tissue-force measurement, or permission to move an instrument.

The offline training pipeline must therefore follow these rules:

- admit only a manifest-registered archive whose SHA-256 matches the local
  bytes;
- record the provider URL, exact version, license, ethics/consent basis,
  de-identification evidence, and leakage-resistant split key;
- split by procedure/patient/session, and preferably also audit surgeon/site
  leakage before training;
- use video for perception and representations, and use instrumented phantom,
  ex-vivo, simulation, or exact-system teleoperation data for geometry,
  kinematics, contact, and control research;
- never train a model to emit direct motor commands from uncalibrated POV video;
  learned outputs remain proposals behind deterministic limits, spatial
  uncertainty gates, an independent stop path, and clinician supervision;
- do not update model weights online during a case.

The repository's `OfflineDatasetManifest` and `OfflineDatasetRegistry` enforce
the software part of this boundary. They do not replace an IRB/ethics review,
data-use agreement, privacy review, license review, or data-custodian signoff.

## Candidate datasets

### Clinical endoscopic or egocentric video

| Dataset | What it provides | Best offline use | Safety / access note |
|---|---|---|---|
| [EgoSurgery-Phase](https://papers.miccai.org/miccai-2024/264-Paper0627.html) / [EgoSurgery repository](https://github.com/Fujiry0/EgoSurgery) | 15 hours of real open-surgery video, nine phases, an egocentric head-mounted camera, and eye-gaze information | POV representation learning, phase recognition, gaze-conditioned attention, out-of-distribution tests | The paper announces public availability, but verify the current release, consent scope, and license before ingestion. It has no robot kinematics or force ground truth. |
| [Cholec80](https://camma.u-strasbg.fr/datasets/) | 80 cholecystectomy videos from 13 surgeons; phase labels at 25 fps and tool-presence labels at 1 fps | Workflow-phase recognition, temporal segmentation, tool presence, hard-negative mining | CAMMA lists CC BY-NC-SA 4.0. Treat the non-commercial/share-alike terms as binding and verify the exact downloaded release. |
| [CholecT50 / CholecT45](https://github.com/CAMMA-public/cholect50) and [CholecTriplet challenge](https://cholectriplet2022.grand-challenge.org/data/) | CholecT50 has 50 laparoscopic cholecystectomy videos with instrument-verb-target triplets, phase labels, and a bounding-box subset; CholecT45 is the public training subset | Instrument/action/target recognition, phase-aware event grounding, temporal anticipation | The challenge describes 45 training videos and a private five-video test set. Keep the private test private; the repository lists CC BY-NC-SA 4.0. |
| [PhaKIR](https://phakir.re-mic.de/) / [data access](https://phakir.re-mic.de/data/) | The challenge description reports 13 real-world human cholecystectomy videos from three hospitals, with 19 instrument categories, instrument keypoints, instance segmentation, and eight phases | Instrument localization, keypoint/visibility estimation, phase recognition, robust perception across sites | Access is through a controlled release/Zenodo record and the site lists CC BY-NC-SA. Pin the Zenodo release and reconcile the exact released-video count before training. |
| [Endoscapes](https://camma.u-strasbg.fr/datasets/) | 201 laparoscopic videos with scene segmentation, object detection, and Critical View of Safety assessment annotations | Surgical-scene understanding, safety-relevant visual state estimation, calibrated abstention | Use only the provider-approved release and terms. Critical View labels are not a clinical decision rule. |
| [MultiBypass140](https://camma.u-strasbg.fr/datasets/) | Multicentric laparoscopic Roux-en-Y gastric bypass video with phases, steps, and intraoperative adverse-event annotations | Procedure-specific workflow recognition and rare-event retrieval | Verify access conditions and annotation definitions with CAMMA; do not transfer labels across procedures without validation. |
| [CholecTrack20](https://camma.u-strasbg.fr/datasets/) | 20 laparoscopic cholecystectomy videos with multi-tool tracking, visibility, intracorporeal movement, trajectories, phases, and visual-challenge labels | Tracking, temporal association, occlusion handling, uncertainty/OOD evaluation | Small and procedure-specific; split by complete video/procedure, never by random frames. |
| [M2CAI16 workflow](https://camma.u-strasbg.fr/datasets/) and [M2CAI16 tool](https://camma.u-strasbg.fr/datasets/) | 41 workflow videos and 15 tool videos from laparoscopic cholecystectomy | Baseline workflow and tool-detection experiments | CAMMA lists request forms. Audit overlap with other cholecystectomy corpora to prevent train/test leakage. |

### Operating-room context, not surgical POV

| Dataset | What it provides | Best offline use | Limitation |
|---|---|---|---|
| [MVOR](https://github.com/CAMMA-public/MVOR) | 732 synchronized frames from three RGB-D cameras in a hybrid OR, with calibration, 4,699 bounding boxes, 2D/3D keypoints, and interventions such as vertebroplasty and lung biopsy | External OR occupancy, staff/instrument context, human-pose and calibration checks | It is multi-view external OR context, not an endoscopic POV stream or robot-control dataset. CAMMA lists CC BY-NC-SA 4.0. |

### Phantom, ex-vivo, geometry, and kinematics

| Dataset | What it provides | Best offline use | Safety / interpretation note |
|---|---|---|---|
| [JIGSAWS](https://cirl.lcsr.jhu.edu/research/hmm/datasets/jigsaws_release/) | IRB-approved bench-top da Vinci study: eight surgeons, suturing/knot-tying/needle-passing, stereo endoscopic video, kinematics, gesture labels, and skill scores | Gesture segmentation, teleoperation representation learning, repeatable kinematic benchmarks | It is phantom/training data, not patient surgery. JHU states academic research only and requires an access form; it is not commercial authorization. |
| [SCARED](https://endovissub2019-scared.grand-challenge.org/About/) | Fresh porcine-cadaver abdominal anatomy using a da Vinci Xi endoscope, structured-light depth, multiple views, stereo calibration, and kinematics | Depth/pose/SLAM, anatomy geometry, camera calibration, registration and reconstruction | Ex-vivo porcine material is not living human tissue and cannot establish clinical safety. |
| [EndoSLAM](https://github.com/CapsuleEndoscope/EndoSLAM) | Ex-vivo and synthetic endoscopy with timed 6-DoF pose and high-precision 3D maps across 35 subdatasets | Visual odometry, mapping, pose uncertainty, and synthetic-to-real robustness | The code repository's MIT license must not be assumed to cover every dataset asset; verify the data terms separately. |
| [SurgVU / EndoVis](https://opencas.dkfz.de/endovis/) | Surgical-training videos from a da Vinci system; the current challenge description reports 280 long videos, 155 sessions, 60 fps, 720p, and over 840 hours, with tool-presence and task labels | Large-scale representation, tool presence, task recognition, weak-label noise handling | This is training-exercise data, not patient clinical data. EndoVis access is challenge-specific and rules/signatures may apply. |

## Recommended staged use

1. **Perception pretraining:** Cholec80, CholecT45, PhaKIR, Endoscapes, and
   EgoSurgery-Phase. Train phase/tool/scene representations and calibrated
   abstention, not actuation.
2. **Temporal and skill research:** CholecT triplets, CholecTrack20, and JIGSAWS.
   Keep phantom skill labels separate from clinical outcome claims.
3. **Spatial estimation:** MVOR, SCARED, and EndoSLAM for pose, calibration,
   mapping, and occlusion tests. None of these public corpora supplies a
   validated surgical Wi-Fi, ultrasonic, or mmWave sensing channel; wave fusion
   must be calibrated on the target hardware with controlled ground truth.
4. **Safety and control evidence:** collect new procedure-specific, multimodal
   data under the appropriate ethics/IRB, consent, privacy, and data-use
   controls. Synchronize endoscope, robot state, force/tactile channels, wave
   sensors, calibration, clinician commands, stops/takeovers, and outcomes.
5. **Offline bundle release:** preserve raw data read-only, derive versioned
   labels, verify checksums, sign the model/configuration/calibration/evaluation
   bundle, and deploy only to simulation or a separately approved supervised
   research environment.

## Ingestion checklist

For each provider release, create one manifest and quarantine the archive until
all checks pass:

```text
provider URL + exact release/version
SHA-256 of the locally cached archive
license and permitted-use interpretation
ethics / consent / de-identification evidence
data custodian and access expiry or withdrawal process
clinical_status: clinical_endoscopic, clinical_or, phantom, ex_vivo, or synthetic
split_key: patient_id, procedure_id, session_id, surgeon_id, or site_id
annotator/version/label-audit metadata
known overlap with other corpora
evaluation-only and private challenge files excluded
```

The registry rejects missing provenance, non-deidentified manifests, forbidden
direct-actuation uses, and archives whose checksum has not been verified. A
successful admission means “approved for the named offline research use”; it
does not mean the source is clinically validated or safe to deploy.

## Sources and release caveats

The [CAMMA dataset index](https://camma.u-strasbg.fr/datasets/) is the primary
source for several laparoscopic corpora above. The [JHU JIGSAWS release page](https://cirl.lcsr.jhu.edu/research/hmm/datasets/jigsaws_release/)
is the authority for its phantom/kinematic access terms. [EndoVis](https://opencas.dkfz.de/endovis/)
and individual challenge pages govern their own release rules. Dataset counts
and labels are release-specific; the local catalog must be version-pinned and
reviewed again before any training job.
