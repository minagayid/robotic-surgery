# Learning-pipeline source adapter boundary

> The bundled adapters produce mock references. They neither download media
> through platform APIs nor read files from a local video directory. The current
> frame reader synthesizes RGB arrays from a seed.

The `data.sources` module provides deterministic examples of four source types:

| Type | Adapter class | Current behavior |
|---|---|---|
| `official_api` | `OfficialAPISource` | Produces an `official-api://` mock reference; makes no network request. |
| `research` | `ResearchDatasetSource` | Produces a mock path and research label; does not check the dataset's files or access agreement. |
| `licensed` | `LicensedPartnerSource` | Produces a synthetic reference from caller-provided identifiers; does not validate a contract. |
| `first_party` | `FirstPartyCaptureSource` | Produces a synthetic reference from a directory label; does not inspect media or consent records. |

The `LicenseGate` trusts the `LicenseStatus` stored in each clip's provenance.
It is a software contract check, not a license, consent, ethics, copyright, or
data-use verification service. Never label real data `CLEARED` without the
actual applicable authorization and an accountable review.

## Work required for real data

Each concrete adapter needs a documented provider/access basis, applicable
terms and license checks, human-subject and privacy review where relevant,
consent/de-identification evidence, file decoding and corruption handling,
checksums, source attribution, retention/deletion policy, and a dataset audit
trail. Real video readers and learned models need separate evaluation against
ground truth and privacy requirements. None of those integrations is present in
this reference pipeline.
