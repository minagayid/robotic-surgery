# DARPA Surgical Competition - Qualification Gap Assessment

**Review date:** 8 November 2026  
**Status:** not qualified; no application submitted.  
**Deadline:** 13 November 2026, 16:00 Eastern Time (11:00 p.m. Cairo time on the deadline date). Confirm the portal's displayed time zone before the final hour.

## Official qualification packet

The DARPA Surgical Competition qualification guide v1.2 requires a technical whitepaper and linked demonstration videos through the Central Florida Tech Grove portal. The packet includes team and organisation information, a full roster and affiliations, contact details, foreign-national declarations, technical approach sections, and video links. Video descriptions are limited to 100 words each.

A team must demonstrate safe robotic motion and an emergency-stop capability, and demonstrate at least three skills selected from the qualification list. Listed skills include tissue retraction, suction, irrigation, lighting adjustment, instrument passing, cauterization, suturing, vessel clamping, skin incision, and tissue lifting. Low-fidelity tissue models may be used; the robotic system still needs to carry out the physical task. The robot may be teleoperated or autonomous for qualification demonstrations.

## Repository comparison

| Qualification evidence | Evidence in this repository | Assessment |
|---|---|---|
| Robotic movement | Host-side deterministic checks and a toy kinematic simulator | Does not demonstrate physical robotic movement |
| Emergency stop | Software stop latch in the simulation runtime | Not a hardwired hardware emergency stop or independent safety function |
| Three surgical skills | Documentation and research architecture only | No physical skill demonstration available |
| End-effectors and instruments | No physical robot/end-effector configuration documented | Missing |
| Sensing and calibration | Typed/synthetic records and simulated spatial data | No calibrated hardware sensor evidence |
| Teleoperation/autonomy | Research roadmap and simulated interfaces | No physical teleoperation or autonomy demonstration |
| Local compute | Offline-first design intent | No audited local hardware/configuration evidence |
| Team and supply chain | No full roster, affiliations, manufacturing/service disclosures, or audit packet in repository | Must be prepared and verified |
| Video submission | No qualification videos identified | Missing |

The repository's own README explicitly describes the project as research/simulation only, without hardware drivers, real-time guarantees, validated surgical workflows, or clinical approval. It describes mock source adapters and synthetic frames. Its software safety supervisor is not an independent physical safety controller. These distinctions must remain explicit.

## Qualification blockers

1. **Physical robotic platform:** a real robot, compatible instruments/end-effectors, and physical tissue/task fixtures are required for convincing qualification evidence.
2. **Hardware emergency stop:** provide a clearly identified, reachable, hardwired hardware E-stop or kill switch that actually stops all robot motion; the software stop latch is not a substitute.
3. **Three physical skills:** choose at least three feasible tasks and record repeatable, unedited demonstrations with an operator/robot setup consistent with the guide.
4. **Safety and integration:** document fail-safe behavior, motion limits, communications/power-loss response, local compute, and the test setup.
5. **Administrative/eligibility:** complete the full team roster, organisation/contact information, all foreign nationals, required supply-chain attestations, insurance and any required legal forms. Confirm prize payment and international team requirements directly with DARPA/competition administrators.
6. **Videos and packet:** prepare the detailed technical whitepaper, team and technical sections, and video links; the portal submission must be completed by the deadline.

The rules also describe an in-person final assessment at a U.S. military installation, local-only compute/network restrictions during the assessment, hardware and software supply-chain restrictions, and additional insurance and site requirements. These conditions need written confirmation by the competition administrators for an Egypt-based team before committing travel or purchasing equipment.

## Recommendation

Do not submit this repository as though it proves hardware capabilities. Based on the current recorded evidence, the physical-motion, E-stop and three-skill gates are unfulfilled. A software-only whitepaper and simulated video would risk rejection and would misrepresent the state of the project.

The repository remains useful as a longer-term software benchmark and simulation reference. For this cycle, proceed only if a team already has access to a physical surgical-robotics platform and can create genuine qualification videos and the administrative/supply-chain evidence before the deadline. Otherwise, document this cycle as not feasible and use the qualification guide as a development benchmark for a later competition.

## Authoritative references

- DARPA competition page: https://www.darpa.mil/research/challenges/surgical
- Qualification guide v1.2: https://www.darpa.mil/sites/default/files/attachment/2026-10/darpa-competition-surgical-qualification-guide.pdf
- Competition rules v1.2: https://www.darpa.mil/sites/default/files/attachment/2026-10/darpa-competition-surgical-rules.pdf
- Resources and FAQs: https://www.darpa.mil/research/challenges/surgical/resources
