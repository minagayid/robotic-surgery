# Virtual Surgical Training Videos

These are silent, captioned, non-clinical demonstrations:

| Video | Duration | Content |
|---|---:|---|
| `virtual-surgical-simulation.avi` | 20 s | Platform, locked configuration, virtual room, S2 run, stale-camera safe hold, evidence review |
| `virtual-procedure-walkthrough.avi` | 20 s | Verify, prepare interfaces, position, dock, coordinate blunt tools, exchange, undock and debrief |

Format: Motion JPEG AVI, 960 × 540, 12 fps. Poster PNGs are provided for
preview. The videos contain no audio, patient anatomy, surgical technique, energy
delivery, cutting, suturing, drilling, or clinical complication management.

Regenerate them with:

```powershell
python tools/build_surgical_media.py
```

The optional media build requires Pillow. The main RobotX runtime does not depend
on Pillow.

See [storyboards and narration constraints](../../docs/surgical/quickstart/VIDEO_STORYBOARDS.md).
