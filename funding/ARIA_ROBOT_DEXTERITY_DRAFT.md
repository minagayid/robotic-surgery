# ARIA Robot Dexterity - Proposal Readiness Draft

**Internal preparation document - NOT submitted.**  
**Call:** Standards and benchmarks for dexterous robotics  
**Proposed title:** OPEN-TACTILE: Open Tactile Data and Reproducible Dexterity Evaluation  
**Lead applicant / contracting entity:** [CONFIRM legal name and eligibility]  
**UK lead organisation / delivery partner:** [NOT IDENTIFIED OR COMMITTED]  
**Other partners and test sites:** [NOT IDENTIFIED OR COMMITTED]  
**Requested amount and cost model:** [TO BE COSTED AND APPROVED]

## 1. Opportunity and hard requirements

The published call deadline is **1 December 2026 at 13:00 GMT**. Clarification questions are due by **24 November 2026 at 13:00 GMT**. The call offers up to **£3 million per project** for up to **24 months**, with up to four awards. A proposal is limited to **five numbered pages plus references**, in Arial 10 or larger. Matched funding is not required. These are programme ceilings, not a recommended project budget.

International applicants are welcomed. ARIA's general applicant guidance says that, as a general rule, more than 50% of project work, cost and personnel should be in the UK. A proposal delivered mainly outside the UK must explain the credible net benefit to the UK programme. The final applicant/organisation model, location of work, partner roles, and cost split must be agreed before submission.

The RFP gives inconsistent historic target dates for contract start (February 2026) and award (January 2026), which precede the October 2026 call publication and December 2026 deadline. Obtain written clarification from ARIA before relying on those dates.

## 2. Executive summary - draft

OPEN-TACTILE will develop and independently evaluate an open, vendor-neutral data contract and reproducible benchmark infrastructure for tactile sensing and contact-rich dexterous manipulation. The project addresses a shared bottleneck: results from tactile sensors and dexterous robots are difficult to compare or reproduce when sensor records, calibration metadata, coordinate frames, timestamps, uncertainty, task protocols, and scoring conventions differ.

The project will co-design a versioned tactile-data schema, conformance tests, reference software, reusable task protocols, and a benchmark harness with sensor developers, robot-platform teams, and independent test laboratories. It will validate the resulting interfaces across distinct sensing technologies, robot configurations, and test sites, publish open tools and governed reference datasets, and establish a maintenance and adoption route beyond the funded period.

The existing [robotic-surgery repository](https://github.com/minagayid/robotic-surgery) contributes an early software scaffold: versioned tactile/force records, trial metadata, and deterministic summary metrics. It is not hardware-connected and has not been validated across sensors, robots, or sites. The grant will fund the missing co-design, integration, physical evaluation, independent replication, and community governance. The project is a general dexterous-robotics benchmark; surgical use is not an intended outcome or validation claim of this proposal.

## 3. Problem, users, and technical approach

**Shared problem.** Sensor vendors and robot teams represent tactile/force data differently. Missing units, calibration provenance, clock semantics, coordinate frames, uncertainty and dropout metadata can make data unusable or make benchmark scores incomparable. Task descriptions and evaluation pipelines are also often tightly coupled to one platform.

**Users.** Tactile sensor makers; dexterous-hand and manipulator developers; embodied-AI and manipulation researchers; robotics integrators; benchmark organisers; independent robotics laboratories; and standards communities.

**Work packages.**

- **WP1 - Requirements and governance (Months 1-4).** Interview and workshop with users; map existing public formats and standards; define use cases, threat/privacy model, data rights, IP, governance, and adoption criteria. Publish a requirements matrix and design decisions.
- **WP2 - Interoperable tactile records (Months 2-9).** Evolve the current v0.1.0 schema into a reviewed versioned specification; define sensor capability descriptors, calibration and coordinate-frame records, timing, uncertainty, missingness, clipping, and provenance; release reference readers/writers and conformance suites.
- **WP3 - Reproducible benchmark infrastructure (Months 5-14).** Co-design task protocols and fixtures; release a platform-independent runner, metadata format, data-quality checks, scoring package, baselines, and reproducible reporting templates.
- **WP4 - Cross-technology validation (Months 10-20).** Integrate at least three distinct tactile-sensing implementations and two robot/platform configurations, subject to secured access; execute agreed tasks at two independent test sites; assess repeatability, timing/data integrity, sensor dropout, calibration ambiguity, and score sensitivity.
- **WP5 - Adoption and sustainability (Months 18-24).** Publish open reference implementations, benchmark protocols, validation reports and governed datasets; run public technical workshops; establish maintainers, versioning, issue triage, and an adoption roadmap.

**Technical outputs.** Versioned schema; conformance suite; Python reference SDK; benchmark runner; task and fixture specifications; baseline datasets and reference results; independent validation report; open governance and maintenance plan.

## 4. Evaluation and measurable success

Proposed acceptance targets, to be refined with independent test-site partners at project start:

| Area | Target by Month 24 |
|---|---|
| Interoperability | At least 3 distinct tactile sensor implementations pass published conformance tests |
| Platform coverage | At least 2 robot/hand/manipulator configurations complete the common task suite |
| Independent validation | Replication at 2 independent test sites, with protocol deviations published |
| Data integrity | 100% of released records identify schema version, units, timebase, sensor ID and calibration reference; malformed/ambiguous records fail conformance |
| Reproducibility | A second site can reproduce benchmark reports from the released protocol, data and software, with score differences and uncertainty reported |
| Openness | Public specification, reference code, task protocols, issue tracker and validation reports under a reviewed permissive licence, subject to partner IP and data rights |
| Adoption | At least 5 external organisations or teams trial the release; evidence must be documented, not inferred from downloads |

The benchmark will report success, time distributions, operator interventions, dropped-object/recovery rates, force/torque distributions, data completeness, timing, calibration coverage, and repeatability. Thresholds used for research scoring will not be presented as safety limits.

## 5. Delivery, UK benefit, openness and budget

**UK delivery plan.** The submitted plan should place more than 50% of project work, cost and personnel in the UK unless ARIA confirms an exception. A credible UK delivery model requires a named UK lead or substantial delivery partner, paid work packages, access to physical tactile/robotics testbeds, and independent evaluation. Potential organisations to approach include the University of Bristol Tactile Robotics Group / Bristol Robotics Laboratory and Imperial College London's Manipulation and Touch Lab. They are identified here only as research prospects based on their publicly described tactile and dexterity work; neither has agreed to participate. Their existing ARIA-linked activity and any overlap must be checked and disclosed.

**International contribution.** The Egyptian applicant/research team could contribute reference software, schema engineering, data tooling, and dissemination, but the scale and cost share of that work must be confirmed. The UK benefit should be measurable: open infrastructure maintained with UK partners, UK test-site capability, reusable benchmark assets, training, and international adoption that strengthens the UK's robotics ecosystem.

**Open outputs and IP.** Proposed outputs are openly accessible specifications, tests, reference implementation, task protocols, reproducibility scripts and non-restricted datasets. Confirm background IP, ownership of partner contributions, dataset licences/consent, third-party dependencies, and contribution agreements before submission. A licence decision is still required; the repository currently has no root project licence declared.

**Budget.** No credible budget has yet been supplied. Prepare a GBP cost model by work package, organisation, staff role/effort, equipment, sensor/robot access, test-site fees, fabrication/fixtures, travel, dissemination, overheads and VAT treatment. Map more than 50% of work/cost/personnel to UK delivery or provide a written ARIA-acceptable exception. Do not submit an invented figure or imply in-kind access that is not committed.

## 6. Team, risks and dependencies

The final proposal must name the applicant, contracting entity, PI/project lead, key technical leads, UK delivery partner, independent validation sites, and their actual roles and commitment status. Include relevant delivery track record, conflicts of interest, rights to use repository code and data, data-management and information-security plan, and continuity arrangements.

Critical dependencies:
- signed agreement for at least two physical robot configurations and three tactile sensor implementations;
- access to two independent test sites and named independent evaluators;
- UK lead/delivery arrangement and majority-UK work/cost/personnel plan;
- agreed IP and data rights, including rights to publish;
- costed work packages, staff availability, equipment procurement and VAT treatment;
- written clarification of call schedule inconsistencies and portal requirements.

Principal risks are low sensor interoperability, incompatible calibration semantics, missing/poor-quality data, test-site access delays, vendor lock-in, insufficient cross-site repeatability, partner withdrawal, and IP restrictions. Mitigations include early interface workshops, explicit missingness and uncertainty, independent implementations, staged test gates, open protocol design, data-rights agreements, and a fallback simulation track that is clearly separated from physical validation.

## 7. Submission readiness - outstanding, not attested

- [ ] Confirm applicant's legal name, country, applicant type, contact email and contracting route.
- [ ] Confirm eligibility and any security/conflict disclosures with ARIA.
- [ ] Secure a UK lead organisation or substantive delivery partner and written role/commitment.
- [ ] Secure physical test platforms, tactile sensors and two independent validation sites.
- [ ] Approve the GBP budget, UK work/cost/personnel share, VAT treatment and partner costs.
- [ ] Confirm background IP, project IP, software licence, dataset rights and publication permissions.
- [ ] Complete named team CVs, track record, roles and availability.
- [ ] Ask ARIA about the inconsistent contract start/award dates.
- [ ] Complete the portal only after the applicant has accessed the account and reviewed every field.
- [ ] Obtain applicant approval of all declarations and submit before 1 December 2026, 13:00 GMT.

**Current status:** a draft concept and repository scaffold exist; no partner, UK test site, budget, contracting entity, portal application, or applicant declaration has been confirmed. This document is not a completed application and must not be represented as submitted.
