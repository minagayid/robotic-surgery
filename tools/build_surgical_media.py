"""Build silent, captioned, non-clinical surgical robotics walkthrough videos.

The output is Motion JPEG AVI so the media can be generated with only Pillow and
the Python standard library. No patient anatomy or surgical technique is shown.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import math
import os
import struct

from PIL import Image, ImageDraw, ImageEnhance, ImageFont


ROOT = Path(__file__).resolve().parents[1]
RENDERS = ROOT / "assets" / "surgical" / "renders"
OUTPUT = Path(os.environ.get("ROBOTX_MEDIA_OUTPUT", ROOT / "media" / "surgical"))
WIDTH, HEIGHT, FPS = 960, 540, 12
SCENE_SECONDS = 2.5


@dataclass(frozen=True)
class Scene:
    image: str
    title: str
    caption: str
    accent: tuple[int, int, int] = (74, 205, 238)


SIMULATION = [
    Scene("robotx-surgical-system.png", "VIRTUAL SURGICAL SIMULATION", "Synthetic-phantom training only — no patient use"),
    Scene("robotx-surgical-system.png", "1  PLATFORM READY", "Console, safety core, visualization arm, and instrument carts"),
    Scene("robotx-extremity-exploded.png", "2  CONFIGURATION LOCKED", "Arm, adapter, instrument, software, calibration, and limits agree"),
    Scene("robotx-simulator-ui.png", "3  ROOM + WORKSPACE CHECK", "Carts locked; bedside and conversion paths remain clear"),
    Scene("robotx-simulator-ui.png", "4  SURGEON-CONTROLLED S2", "Blunt tools move only inside the validated synthetic workspace"),
    Scene("robotx-simulator-ui.png", "5  FAULT INJECTION", "Stale camera detected — new motion rejected — safe hold", (255, 171, 85)),
    Scene("robotx-manufacturing-line.png", "6  EVIDENCE + REPLAY", "Timing, limits, interventions, and configuration are sealed for review"),
    Scene("robotx-surgical-system.png", "END STATE", "Motion disabled · tools removed · arms parked · run debriefed", (83, 224, 187)),
]


WALKTHROUGH = [
    Scene("robotx-surgical-system.png", "VIRTUAL PROCEDURE WALKTHROUGH", "Robot operation tutorial — clinical technique intentionally omitted"),
    Scene("robotx-manufacturing-line.png", "1  VERIFY + INSPECT", "Approved training case, team, hardware, instruments, and fallback drill"),
    Scene("robotx-extremity-exploded.png", "2  PREPARE INTERFACES", "Training drape, keyed sterile adapter, and instrument identity"),
    Scene("robotx-surgical-system.png", "3  POSITION + LOCK", "Camera cart first; one arm at a time; clear bedside lane"),
    Scene("robotx-simulator-ui.png", "4  DOCK + CLEARANCE", "Align access markers and complete the low-speed collision check"),
    Scene("robotx-simulator-ui.png", "5  ENABLE + COORDINATE", "Confirm live view, neutral masters, correct pair, S2, and limits"),
    Scene("robotx-extremity-exploded.png", "6  EXCHANGE ONE TOOL", "Safe exchange pose; motion off; inspect, identify, latch, and recheck"),
    Scene("robotx-surgical-system.png", "7  UNDOCK + REVIEW", "Remove tools, count parts, park arms, seal logs, and debrief", (83, 224, 187)),
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = [
        "C:/Windows/Fonts/seguisb.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for name in names:
        if Path(name).exists():
            return ImageFont.truetype(name, size)
    return ImageFont.load_default()


TITLE = font(34, True)
CAPTION = font(21)
BADGE = font(16, True)
SMALL = font(15)


def cover(image: Image.Image, scale: float, pan_x: float, pan_y: float) -> Image.Image:
    image = image.convert("RGB")
    base = max(WIDTH / image.width, HEIGHT / image.height) * scale
    resized = image.resize((round(image.width * base), round(image.height * base)), Image.Resampling.LANCZOS)
    max_x = max(0, resized.width - WIDTH)
    max_y = max(0, resized.height - HEIGHT)
    left = round(max_x * min(1, max(0, pan_x)))
    top = round(max_y * min(1, max(0, pan_y)))
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def rounded(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def frame_for(scene: Scene, index: int, total: int, phase: float, images: dict[str, Image.Image]) -> Image.Image:
    zoom = 1.02 + 0.055 * phase
    pan_x = 0.35 + 0.25 * phase
    pan_y = 0.45 + 0.08 * math.sin(phase * math.pi)
    frame = cover(images[scene.image], zoom, pan_x, pan_y)
    frame = ImageEnhance.Contrast(frame).enhance(0.94)
    shade = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle((0, 0, WIDTH, 112), fill=(3, 15, 27, 222))
    sd.rectangle((0, HEIGHT - 112, WIDTH, HEIGHT), fill=(3, 15, 27, 235))
    sd.rectangle((0, 112, WIDTH, HEIGHT - 112), fill=(3, 15, 27, 28))
    frame = Image.alpha_composite(frame.convert("RGBA"), shade)
    draw = ImageDraw.Draw(frame)

    accent = scene.accent
    rounded(draw, (30, 24, 188, 55), 15, (*accent, 235))
    draw.text((109, 39), "ROBOTX SURGICAL", font=BADGE, fill=(3, 20, 30), anchor="mm")
    draw.text((30, 72), scene.title, font=TITLE, fill="white")
    draw.text((30, HEIGHT - 87), scene.caption, font=CAPTION, fill=(235, 245, 250))
    draw.text((WIDTH - 30, HEIGHT - 28), "PLANNING / SIMULATION ONLY", font=SMALL, fill=(178, 202, 215), anchor="rs")

    y = HEIGHT - 48
    gap = 10
    bar_w = (WIDTH - 60 - gap * (total - 1)) / total
    for i in range(total):
        x0 = 30 + i * (bar_w + gap)
        color = (*accent, 255) if i <= index else (91, 116, 132, 210)
        draw.rounded_rectangle((x0, y, x0 + bar_w, y + 5), radius=3, fill=color)

    # Fade at scene boundaries without hiding safety text.
    alpha = min(1.0, phase / 0.12, (1.0 - phase) / 0.12)
    if alpha < 1:
        fade = Image.new("RGBA", frame.size, (3, 15, 27, round(255 * (1 - alpha))))
        frame = Image.alpha_composite(frame, fade)
    return frame.convert("RGB")


def jpeg_bytes(frame: Image.Image) -> bytes:
    buffer = BytesIO()
    frame.save(buffer, format="JPEG", quality=74, optimize=False, progressive=False, subsampling=1)
    return buffer.getvalue()


def chunk(tag: bytes, data: bytes) -> bytes:
    return tag + struct.pack("<I", len(data)) + data + (b"\0" if len(data) & 1 else b"")


def list_chunk(kind: bytes, data: bytes) -> bytes:
    return b"LIST" + struct.pack("<I", len(data) + 4) + kind + data + (b"\0" if len(data) & 1 else b"")


def write_mjpeg_avi(path: Path, frames: list[bytes], fps: int) -> None:
    max_frame = max(map(len, frames))
    avih = struct.pack(
        "<14I", round(1_000_000 / fps), max_frame * fps, 0, 0x10,
        len(frames), 0, 1, max_frame, WIDTH, HEIGHT, 0, 0, 0, 0,
    )
    strh = struct.pack(
        "<4s4sIHH8I4h", b"vids", b"MJPG", 0, 0, 0, 0, 1, fps, 0,
        len(frames), max_frame, 0xFFFFFFFF, 0, 0, 0, WIDTH, HEIGHT,
    )
    strf = struct.pack("<IiiHH4sIiiII", 40, WIDTH, HEIGHT, 1, 24, b"MJPG", WIDTH * HEIGHT * 3, 0, 0, 0, 0)
    hdrl = list_chunk(b"hdrl", chunk(b"avih", avih) + list_chunk(b"strl", chunk(b"strh", strh) + chunk(b"strf", strf)))

    movi_data = bytearray()
    index = bytearray()
    offset = 4  # offsets are relative to the LIST payload beginning at "movi"
    for data in frames:
        encoded = chunk(b"00dc", data)
        movi_data.extend(encoded)
        index.extend(struct.pack("<4sIII", b"00dc", 0x10, offset, len(data)))
        offset += len(encoded)
    body = b"AVI " + hdrl + list_chunk(b"movi", bytes(movi_data)) + chunk(b"idx1", bytes(index))
    path.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)


def build(name: str, scenes: list[Scene]) -> None:
    images = {scene.image: Image.open(RENDERS / scene.image) for scene in scenes}
    per_scene = round(SCENE_SECONDS * FPS)
    encoded: list[bytes] = []
    poster: Image.Image | None = None
    for index, scene in enumerate(scenes):
        for n in range(per_scene):
            frame = frame_for(scene, index, len(scenes), n / (per_scene - 1), images)
            if poster is None and n == per_scene // 2:
                poster = frame.copy()
            encoded.append(jpeg_bytes(frame))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_mjpeg_avi(OUTPUT / f"{name}.avi", encoded, FPS)
    assert poster is not None
    poster.save(OUTPUT / f"{name}-poster.png", optimize=True)
    for image in images.values():
        image.close()


def main() -> None:
    build("virtual-surgical-simulation", SIMULATION)
    build("virtual-procedure-walkthrough", WALKTHROUGH)


if __name__ == "__main__":
    main()
