#!/usr/bin/env python3
"""Render demo-video.mp4 from REAL output of the PayGate demo command.

Frames are pages of actual CLI output (captured by running the demo),
rendered with Pillow onto 1280x720 frames and encoded with ffmpeg.
No output text is invented: the title/close frames are the only
non-CLI frames, and they are labelled as title/close cards.
Usage: python3 demo/render_video.py  (run from the repo root)
Output: demo/demo-video.mp4
"""

import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
W, H = 1280, 720


def run_demo() -> str:
    """Full demo transcript: clean audit, flagged audit, gated
    recovery, trail verify — all real CLI output, concatenated."""
    trail = str(ROOT / "demo" / "demo-trail.jsonl")
    chunks = []
    for argv, ok_codes in [
        (["--trail", trail, "audit", "--checkout",
          "examples/checkout-clean.json"], (0,)),
        (["--trail", trail, "audit", "--checkout",
          "examples/checkout-flagged.json"], (0, 2)),
        (["--trail", trail, "demo", "--approve-demo"], (0,)),
        (["--trail", trail, "trail", "--verify"], (0,)),
    ]:
        result = subprocess.run(
            [sys.executable, "-m", "paygate.cli", *argv],
            cwd=ROOT, capture_output=True, text=True, timeout=120)
        assert result.returncode in ok_codes, result.stdout + result.stderr
        chunks.append("$ paygate " + " ".join(argv) + "\n" + result.stdout)
    return "\n".join(chunks)


def make_frame(lines, title, frames_dir, index):
    img = Image.new("RGB", (W, H), (12, 18, 28))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 64], fill=(0, 120, 110))
    draw.text((32, 16), title, font=ImageFont.truetype(FONT_BOLD, 28),
              fill=(255, 255, 255))
    font = ImageFont.truetype(FONT, 19)
    y = 88
    for line in lines:
        draw.text((32, y), line, font=font, fill=(220, 230, 235))
        y += 27
    path = frames_dir / f"frame-{index:03d}.png"
    img.save(path)
    return path


def main():
    output = run_demo()
    wrapped = []
    for raw in output.splitlines():
        wrapped.extend(textwrap.wrap(raw, width=105) or [""])
    frames_dir = ROOT / "demo" / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for old in frames_dir.glob("frame-*.png"):
        old.unlink()
    pages, index = [], 0
    # Title card
    make_frame(["PayGate Audit Agent",
                "",
                "Audit before you pay.",
                "Never retry without a human.",
                "",
                "Sandbox only. Mock data by default.",
                "Real PayPal path: sandbox credentials required."],
               "PayGate Audit Agent — demo", frames_dir, index)
    index += 1
    # Pages of real output, 20 lines each
    for start in range(0, len(wrapped), 20):
        make_frame(wrapped[start:start + 20],
                   "PayGate demo — real CLI output", frames_dir, index)
        index += 1
    make_frame(["Sandbox only. Mock by default.",
                "Human approves every retry.",
                "Every decision logged in a hash-chained trail.",
                "",
                "Run it:  python3 -m pytest -q   then   ./DEMO.sh"],
               "PayGate Audit Agent — close", frames_dir, index)
    total_frames = index + 1
    # ~6 seconds per frame keeps the video well under 3 minutes.
    subprocess.run([
        "ffmpeg", "-y", "-framerate", "1/6", "-i",
        str(frames_dir / "frame-%03d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(ROOT / "demo" / "demo-video.mp4"),
    ], check=True, capture_output=True)
    print(f"frames={total_frames} duration~{total_frames * 6}s "
          f"output=demo/demo-video.mp4")


if __name__ == "__main__":
    main()
