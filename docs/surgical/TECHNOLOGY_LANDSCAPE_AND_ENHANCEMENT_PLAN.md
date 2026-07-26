# Surgical Robotics Technology Landscape and Enhancement Plan

> **Design-research note — not a clinical claim, clearance strategy, or operating
> instruction.** RobotX remains surgeon controlled. Every proposed feature below
> is disabled until it is included in a locked, procedure-specific configuration
> and supported by its own risk, verification, usability, and regulatory evidence.

## 1. Why this update exists

Current surgical-robot platforms show several durable architecture patterns:

| Observed pattern | Representative public source | RobotX response |
|---|---|---|
| Surgeon console, patient-side arms, and supporting equipment remain the common RAS architecture; the surgeon retains direct control. | [FDA computer-assisted surgical systems overview](https://www.fda.gov/medical-devices/surgery-devices/computer-assisted-surgical-systems) | Preserve the independent safety controller and prohibit independent patient-side task execution. |
| Modular arm carts can support procedure- and patient-specific room layouts. | [Medtronic Hugo RAS system](https://www.medtronic.com/en-us/healthcare-professionals/specialties/surgical-robotics/hugo-robotic-assisted-surgery/products-and-system.html); [Versius system manual](https://cmrsurgical.com/wp-content/uploads/2022/11/U-00009v15-VersiusSurgicalSystem-UserManual-English-UK.pdf) | Make cart/arm placement, identities, and collision envelope a verified configuration rather than a manual convention. |
| Distal instrument sensing can provide force information at the console. | [Intuitive da Vinci 5 Force Feedback](https://www.intuitive.com/en-us/about-us/newsroom/Force%20Feedback) | Develop an optional distal-sensing instrument path, with sensing integrity and safe degradation before any feedback claim. |
| High-quality 3D visualization, fluorescence-capable imaging, and team-facing visual output are active product directions. | [Intuitive da Vinci 5](https://www.intuitive.com/en-us/products-and-services/da-vinci/5); [CMR Versius Plus ecosystem](https://us.cmrsurgical.com/) | Introduce image-quality awareness and an advisory-only overlay pipeline that cannot conceal the native image. |
| Intraoperative measurement/replay features can support review and training. | [Intuitive real-time surgical insights](https://isrg.intuitive.com/news-releases/news-release-details/intuitive-introduces-real-time-surgical-insights-da-vinci-5) | Extend the existing deterministic case log into privacy-governed replay and simulator scenarios; do not infer clinical benefit from analytics alone. |

This is a technology scan, not a comparison or an endorsement. Marketing claims
are not evidence for RobotX performance, safety, or regulatory authorization.

## 2. Design decisions

### 2.1 P0 — Configuration-aware room and patient-side setup

Add a signed **case configuration package** covering the permitted procedure
segment, carts, arm roles, instrument interfaces, imaging chain, operating table
pose envelope, workspace/collision model, and software/calibration identifiers.
At setup, the system must read back the physical identities and reject a mismatch
or an unknown placement state. A placement planner may advise the team, but its
output is not authority to move an arm or select access points.

**Why first:** modularity expands room-layout choices and therefore setup and
collision failure modes. Treating layout as data makes it testable, reviewable,
and replayable.

### 2.2 P0 — Sensor and display integrity as a first-class state

Promote visual, tracking, force, and access-load quality from diagnostic values to
an explicit **evidence state**: valid, degraded, invalid, or unknown. The safety
controller receives bounded age, uncertainty, calibration, and dependency data;
the console explains the resulting restriction in plain language. No feature may
silently continue using frozen imagery, stale tracking, implausible force data, or
an unvalidated registration.

**Why first:** a sophisticated display or force estimate cannot improve safety if
the operator cannot see when it is untrustworthy.

### 2.3 P1 — Optional distal sensing and bounded feedback

Create a separate force-feedback instrument family rather than estimating tissue
load only from motor current. The instrument record must specify sensing location,
range, resolution, overload behavior, calibration, drift, sterility/reprocessing
life, and the operator feedback mapping. Start with a non-clinical visual force
indicator on phantoms; haptic feedback is enabled only after a dedicated human-
factors and risk case shows it does not mask visual or alarm cues.

Force feedback is supplementary information. It must never authorize motion,
override a force limit, substitute for visualization, or turn an uncertain force
estimate into a precise-looking number.

### 2.4 P1 — Trustworthy visualization enhancement

Define a separate, advisory **visual enhancement pipeline** for image quality,
annotation, and registered overlays. Every overlay must show source, age,
calibration/registration error, confidence, and status; it must be instantly
hideable, recorded in the case log, and unable to cover the native image. An
invalid or stale overlay withdraws without moving the robot or changing energy
permission.

Fluorescence, segmentation, and anatomy labels are separate functions with
separate indications and evidence. The initial release should measure image
quality and record frames, not claim anatomy recognition.

### 2.5 P1 — Team-centred console and bedside coordination

Add a read-only team display with the selected arm/instrument, motion-enable,
energy, sensor-health, and alarm state. Pair it with a closed-loop verbal/readback
protocol in simulator scenarios. The display is a communication aid; the
validated console and bedside emergency controls remain authoritative.

### 2.6 P2 — Digital twin, replay, and training evidence

Extend the virtual simulator with a **configuration digital twin**: room layout,
cart pose, arm reach/collision envelope, instrument identity, timing log, and
fault injections. Use it to rehearse setup, visibility loss, sensor disagreement,
power loss, manual release, and conventional conversion. A simulator score may
support training decisions only after correlation and governance studies; it is
not a credential by itself.

### 2.7 P2 — Constrained software evolution

Keep the clinical runtime offline for essential performance. If a future release
includes AI-enabled image or decision-support functions, freeze the inputs,
outputs, intended population, performance measures, bias analysis, monitoring,
rollback, and allowed modification scope before deployment. FDA's current
[PCCP guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence)
is a useful planning reference; it is not a substitute for product-specific
regulatory advice.

## 3. Explicit non-goals

RobotX will not claim or pursue these through this enhancement plan:

- autonomous completion of a surgical step, diagnosis, or treatment;
- generic "all surgeries" capability or unvalidated procedure/population transfer;
- remote Internet dependence for motion, energy, or essential visualization;
- hidden image manipulation, opaque confidence, or analytics presented as a
  clinical recommendation; or
- reuse of third-party interfaces, patents, data, labels, or performance claims.

The FDA describes marketed RAS as requiring direct human control and emphasizes
training and credentialing for the particular model and use. Its page also notes
that no RAS system has US marketing authorization specifically to prevent or
treat cancer. Those boundaries remain in force for all RobotX planning.

## 4. Evidence and release gates

| Enhancement | Minimum evidence before a clinical-intent release | Safe response when evidence is unavailable in a case |
|---|---|---|
| Configuration-aware layout | Identified carts/arms, placement tolerance, collision and human-factors tests across permitted rooms/table poses | Do not enable patient-side motion; reconfigure or use the approved conventional workflow. |
| Distal sensing / feedback | Tip-level traceable metrology, drift/overload/life tests, feedback mapping and simulated-use validation | Withdraw feedback; retain only the validated base control mode. |
| Visual enhancement / overlay | Ground truth, registration/latency/error budgets, display usability and failure-injection tests | Remove overlay; native image and base controls remain available only if otherwise valid. |
| Team display and replay | Alarm/readback usability, privacy/security, traceability, and representative team simulation | Fall back to validated console/bedside controls and standard documentation. |
| Analytics or AI function | Locked intended use, dataset provenance, subgroup performance, prospective evaluation, monitoring and rollback plan | Disable the function; never substitute an unreviewed model or cloud service. |

## 5. Implementation order

1. Implement the new requirements in `HARDWARE_REQUIREMENTS.md` and add their
   fault scenarios to `VALIDATION_CLINICAL.md`.
2. Build the configuration digital twin and sensor/display-health replay on the
   non-clinical phantom bench.
3. Select one blunt, non-energy research instrument for distal-sensing bench
   experiments; keep it physically and procedurally separate from any clinical-
   intent instrument program.
4. Run formative human-factors studies with representative console and bedside
   users before freezing screen design or feedback mappings.
5. Review findings through quality, clinical, regulatory, privacy, and
   cybersecurity governance before promoting any function.

## 6. Additional primary references

- [FDA modular RAS classification (SDD)](https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPCD/classification.cfm?id=SDD)
- [FDA 2026 cybersecurity guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-management-system-considerations-and-content-premarket)
- [FDA human factors guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/applying-human-factors-and-usability-engineering-medical-devices)
- [FDA 2025 AI-enabled device PCCP guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/marketing-submission-recommendations-predetermined-change-control-plan-artificial-intelligence)
