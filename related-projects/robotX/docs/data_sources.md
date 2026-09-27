# Compliant Data Sourcing (Layer 1)

Scraping platforms (X, Instagram, TikTok, Facebook, YouTube) by bypassing their
APIs generally **violates each platform's Terms of Service**, and training on
other people's video without a license raises **copyright** questions —
independent of whether it is technically "hacking." robotX does not scrape. It
sources video only through legitimate channels, each of which stamps a
`Provenance` with a `LicenseStatus` so downstream code can enforce what is
allowed.

## The four sanctioned sources

| Source (`type`) | Class | Default license | Notes |
|---|---|---|---|
| `official_api` | `OfficialAPISource` | `RESEARCH_ONLY` | YouTube Data API v3, X API, Meta Graph API, TikTok Research API. Rate-limited; you must honor each platform's content-use terms. |
| `research` | `ResearchDatasetSource` | `RESEARCH_ONLY` | Pre-licensed egocentric corpora — **what most real robot-learning-from-video work uses.** |
| `licensed` | `LicensedPartnerSource` | `CLEARED` | Creator video licensed for AI training with consent/royalties. |
| `first_party` | `FirstPartyCaptureSource` | `CLEARED` | You pay people to wear a head/chest camera doing the target tasks. Cleanest legally and cleaner data. |

### Research datasets supported by `ResearchDatasetSource`

`ego4d`, `ego_exo4d`, `epic_kitchens`, `ssv2` (Something-Something-V2),
`howto100m`, `yt8m` (YouTube-8M, features only). Ego4D / Ego-Exo4D alone provide
~3,700 hrs of egocentric video across many tasks and are pre-licensed for
research.

## The realistic blend

A production dataset mixes **research datasets for pretraining** (broad coverage,
already licensed) with **first-party capture for the specific task distribution**
you want the robot good at (targeted, cleanest license, highest-value data):

```python
from robotx.data.sources import ResearchDatasetSource, FirstPartyCaptureSource
sources = [
    ResearchDatasetSource("ego4d", "datasets"),      # broad pretraining
    ResearchDatasetSource("epic_kitchens", "datasets"),
    FirstPartyCaptureSource("captures/coffee_task"), # targeted, CLEARED
]
```

## Enforcement: the license gate

`robotx.data.licensing.LicenseGate` is the single checkpoint every clip passes
before training. `PENDING` and `BLOCKED` clips are dropped with a recorded
reason. For a **commercial** deployment, construct it with
`allow_research_only=False` so only `CLEARED` (licensed / first-party) data is
used:

```python
from robotx.data.licensing import LicenseGate
kept, result = LicenseGate(allow_research_only=False).filter(clips)
```

## Adding a source

Subclass `VideoSource`, implement `fetch()`, and stamp `Provenance` with the
correct `SourceKind` and `LicenseStatus`. Never emit `CLEARED` for data you do
not actually have rights to.
