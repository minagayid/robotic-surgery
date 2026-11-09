# Collaboration and Partner Outreach Plan

**Prepared:** 9 November 2026  
**Status:** prospect mapping only. No organisation has been contacted or agreed to collaborate. No application has been submitted.

## Collaboration thesis

The Robotic Surgery repository is currently a research/simulation software prototype. It has no physical robot, clinical system access, instrument set, hardware emergency stop, or real-world surgical demonstration. The highest-probability route is to partner with an established research facility that already controls the physical testbed, then add suitable hardware and sensor companies.

Two workstreams should remain distinct:

1. **Surgical robotics / DARPA:** work with a facility or existing team that already has a robot, end-effectors, a hardware emergency stop, and the ability to record physical demonstrations. The software can contribute simulation, perception, task orchestration, logging, replay and evaluation, subject to partner review.
2. **Dexterity / ARIA:** work with tactile-sensor and dexterous-hand developers plus independent robotics test sites to validate an interoperable tactile record schema and reproducible dexterity benchmark. The software-only nature of the present project is not by itself disqualifying, but the proposal must show real cross-technology validation and a credible UK benefit.

## Highest-priority physical test facilities

### 1. University of Leeds - STORM Lab / Robotics at Leeds

**Why first:** The lab publicly lists a da Vinci Research Kit and two KUKA LBR Med medical robotic manipulators. Its surgical robotics research page lists Intuitive Surgical and KUKA as industrial partners, and the lab explicitly welcomes new collaborations. The LBR Med is a medically certified general-purpose manipulator, not proof that a surgical task or competition demonstration is already available.

**Best fit:** Both workstreams. Most promising surgical testbed for a joint software/physical demonstration, and a credible UK research collaborator for an ARIA consortium.

**Ask:** A research collaboration or hosted demonstrator; access conditions, safety/controls restrictions, available end-effectors, demonstrable tasks, facility costs, staff supervision, and whether the lab is already part of a DARPA team or willing to discuss a team role before the current deadline.

**Public contacts:**  
- STORM Lab: https://stormlabuk.com/contact/  
- Professor Pietro Valdastri: https://eps.leeds.ac.uk/staff/863/professor-pietro-valdastri  
- Surgical robotics overview: https://robotics.leeds.ac.uk/research/medical-robotics/surgical-robotics/  
- Research assets: https://robotics.leeds.ac.uk/facilities/research-assets/

### 2. Imperial College London - Hamlyn Centre for Robotic Surgery

**Why:** The Centre publicly lists a da Vinci Surgical System and research assets including the da Vinci Research Kit, RAVEN II, KUKA iiwa and motion-capture/VR facilities. The Centre states that equipment is accessible to academic and industrial organisations and provides an external-access route with a transparent booking/charging process. Access is subject to equipment availability, risk review, supervision and fees; this is not an offer of free access or guaranteed availability.

**Best fit:** DARPA-oriented research demonstrator, clinical/preclinical surgical robotics validation, and a second independent facility for reproducibility.

**Ask:** A hosted software evaluation on the existing testbed, external access or co-supervised collaboration, exact robot/end-effector availability, and the route for joining an already-formed competition team.

**Public contacts:**  
- Facilities access: https://www.imperial.ac.uk/hamlyn-centre/facilities/access/  
- Facility enquiries: https://www.imperial.ac.uk/hamlyn-centre/facilities/  
- Open-access equipment: https://www.imperial.ac.uk/hamlyn-centre/facilities/open-access-equipment--training/

### 3. Bristol Robotics Laboratory - Tactile Robotics Group

**Why:** The University of Bristol describes BRL as the UK's largest robotics laboratory and the home of its Tactile Robotics Group, including TacTip tactile sensing. Professor Nathan Lepora is publicly listed as the group's lead. ARIA also lists an Imperial/Bristol co-design project in its Robot Dexterity programme.

**Best fit:** ARIA sensor interoperability, data schema review, tactile test protocols and independent manipulation benchmark validation.

**Public contacts:**  
- Group: https://www.bristol.ac.uk/research/groups/tactile-robotics/  
- Professor Nathan Lepora: https://www.bristol.ac.uk/people/person/Nathan-Lepora-83045353-295f-488f-8720-e19648954fba/

## Hardware, tactile and AI collaborators

### 4. Touchlab (UK)

**Why:** Touchlab develops TACTO tactile sensing/robotic fingertips and leads ARIA's GRIT tactile-intelligence project. ARIA reports that TACTO has been integrated with Shadow Robot's Dexterous Hand. This is a particularly direct match for the proposed vendor-neutral tactile schema and cross-hardware benchmark.

**Ask:** TACTO data format/SDK or sample data, sensor evaluation, calibration/uncertainty semantics, permission to build a reference adapter, and participation in a multi-sensor ARIA consortium.

**Contact:** https://www.touchlab.io/ (public contact: info@touchlab.io)

### 5. Shadow Robot Company (UK)

**Why:** Its Dexterous Hand is a research platform with ROS integration, tactile sensing options and a teleoperation ecosystem. Shadow offers an academic partnership programme with research support and a published academic discount. The product is a dexterous hand, not a surgical end-effector by default; suitability for any DARPA surgical skill must be evaluated with clinicians and the host facility.

**Ask:** Evaluation access to a hand/teleoperation setup, tactile-data adapter validation, potential joint benchmark tests with Touchlab, and a possible research/industry partner role.

**Contact:** https://shadowrobot.com/contact-us/  
**Academic programme:** https://shadowrobot.com/academic-partnerships/

### 6. Manufacturing Technology Centre (MTC), Coventry (UK)

**Why:** MTC is listed by ARIA as the Solution Partner for Robot Dexterity. Its Robot Experience Centre is a vendor-neutral robotics and automation facility for testing and validating solutions. It is not a surgical robotics laboratory, but could support the non-clinical dexterity benchmark, integration and translation work.

**Ask:** A scoped benchmark pilot at the Robot Experience Centre, advice on a cross-vendor test protocol, introductions to ARIA programme creators, and whether MTC is considering a role in the 16 December 2026 Translation Partner call.

**Contact:** https://www.the-mtc.org/locations-and-contact-us  
**Robot Experience Centre:** https://www.the-mtc.org/robot-experience-centre

### 7. CMR Surgical (UK)

**Why:** CMR develops the Versius surgical system and publicly describes an NVIDIA collaboration using Cosmos-H simulation to train and validate robotic intelligence for Versius. This creates a relevant route to pitch simulation, evaluation, replay and data interoperability.

**Ask:** A non-clinical software integration discussion, simulation/evaluation interoperability, and whether an R&D collaboration route exists. Do not ask for patient access or clinical control; begin with offline/simulated data and a non-clinical proof of concept.

**Contact:** https://cmrsurgical.com/contact-us/

### 8. NVIDIA / robot-brain ecosystem

**Why:** NVIDIA's 16 March 2026 GTC announcement names CMR Surgical, Johnson & Johnson MedTech and Medtronic in healthcare robotics. It also describes Skild AI partnering with ABB Robotics and Universal Robots. The 31 May 2026 GR00T humanoid reference design combines a Unitree H2 Plus body, Sharpa Wave tactile hands, Jetson Thor compute and NVIDIA GR00T software.

**Potential software collaborators:** NVIDIA Isaac ecosystem; Skild AI; Lightwheel; PTC/Onshape.  
**Potential industrial robot hardware partners:** ABB Robotics, FANUC, KUKA, Universal Robots, YASKAWA.  
**Potential surgical platform partners:** CMR Surgical, Johnson & Johnson MedTech, Medtronic.

**Important DARPA supply-chain caution:** the June 2026 Section 1260H update is reported by U.S. university export-control resources to include Hangzhou Yushu Technology (Unitree). The DARPA competition rules bar systems/components from entities on the applicable Section 1260H list. Therefore, do not propose Unitree hardware for DARPA without written clearance. The Unitree/Sharpa/NVIDIA reference design may still be relevant to ARIA's non-defence dexterity benchmark, subject to ARIA procurement and security policies.

## Competition-specific strategy

### DARPA Surgical Competition

The qualification requires genuine video evidence of:
- safe physical robotic motion and end-effector operation;
- an on-board hardware emergency stop or equivalent hardware kill switch stopping all robot motion; and
- at least three listed surgical skills, using low-fidelity simulated tissue if desired.

The rules allow teleoperation for qualification and do not require FDA approval. The team roster must list foreign nationals. The competition's current public pages have been inconsistent: the DARPA opportunity page and Tech Grove update state 13 November 2026 at 16:00 ET, while an older DARPA challenge page still displays 30 October 2026. Written confirmation is needed immediately.

**Realistic approach:** seek a role in an already hardware-capable team, not a new software-only qualification. Ask the host facility whether it has submitted a qualification package and whether it can add a software collaborator. Do not claim physical demonstrations that have not occurred.

**International participation:** the published competition information says participation is open to all nationalities subject to eligibility and screening, but foreign-national administrative requirements and on-site military-installation access must be confirmed with DARPA. A prior industry-day Form 60 cutoff has passed; ask whether it applies to new team members joining at this stage.

**Official contact:** SurgicalCompetition@darpa.mil  
**Challenge:** https://www.darpa.mil/work-with-us/opportunities/darpa-sn-27-02

### ARIA Robot Dexterity - Standards and Benchmarks

Deadline: **1 December 2026, 13:00 GMT**. Clarification questions close **24 November 2026, 13:00 GMT**. The call seeks reusable standards, interfaces, benchmarks and shared testing infrastructure validated across independently developed technologies and sites. A broad consortium is encouraged.

**Realistic approach:** position the project as the software/data/benchmark layer in a consortium led or materially delivered by a UK organisation. Seek Touchlab, Shadow Robot, Bristol/Imperial/Cambridge, MTC and at least two independent test sites. Secure named roles, test-platform access, permission to publish data/results, and a budget before submission.

### ARIA Robot Dexterity - Translation Partner

Deadline: **16 December 2026, 13:00 GMT**. This is a different opportunity: ARIA seeks a partner to establish and operate a physical hub with facilities, technical expertise, training, industrial networks and a sustainable operating model. It is more naturally led by an experienced UK facility/operator than by an individual software project. MTC is the first organisation to approach; the user's software could form one part of a hub's digital evaluation stack.

## Proposed collaboration offer

The project should be pitched as a research software contribution, not as an already validated surgical robot:

- Offline-first software and simulated motion runtime.
- Deterministic host-side motion proposal checks and software emergency-stop latch (not a hardware E-stop).
- Replayable event journal and fault scenarios.
- Vendor-neutral tactile data schema and trial metadata.
- Deterministic dexterity trial metrics and an open benchmark harness.
- Adapters and physical demonstrations to be developed jointly with partners.

Repo: https://github.com/minagayid/robotic-surgery  
Current benchmark branch/PR: https://github.com/minagayid/robotic-surgery/pull/5

## Actions before submission

1. Contact STORM Lab and Hamlyn Centre first about physical surgical-robot access.
2. Contact Touchlab and Shadow Robot about a joint tactile-hand benchmark.
3. Contact MTC about the Robot Experience Centre and 16 December Translation Partner call.
4. Ask CMR Surgical whether it has a non-clinical R&D software integration route.
5. Email DARPA immediately about the deadline discrepancy, ability to join an existing team, foreign-national clearance and supply-chain screening.
6. Confirm ARIA applicant/contracting entity, UK delivery split, budget, partner commitments, test sites and IP/data rights.

**No company has been approached yet. No robot, facility access, collaboration, team membership, prize eligibility or grant funding has been secured.**
