"""Generate sample "camera" videos and "sensor" time series for development.

We have no real cameras or sensors, so a camera is an .mp4 in data/toy/media/videos/ and a
sensor is a .json in data/defaults/sensors/ (shared by every mode): {"t": <ms between samples>, "value": [samples...]}.

Run from src/website:  .venv/Scripts/python tools/make_samples.py
"""
import json
import sys
import math
import random
import subprocess
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = ROOT / "data" / "toy" / "media" / "videos"
SENSORS = ROOT / "data" / "defaults" / "sensors"

W, H, FPS = 320, 180, 2


def lizard_x(t_s, duration_s):
    """Horizontal position as a fraction of the width (0 = left): basks, explores, hides."""
    phase = t_s / duration_s
    return 0.5 + 0.38 * math.sin(2 * math.pi * phase) * math.cos(2 * math.pi * phase * 0.5) \
        + 0.04 * math.sin(t_s / 7)


def draw_top(t_s, duration_s):
    img = Image.new("RGB", (W, H), (214, 196, 160))
    d = ImageDraw.Draw(img)
    d.ellipse((-60, -40, 110, 120), fill=(236, 214, 150))          # basking spot, left (hot side)
    d.rectangle((250, 20, 310, 70), fill=(120, 96, 70))           # hide, right
    d.ellipse((255, 120, 300, 160), fill=(150, 190, 210))         # water bowl
    x = lizard_x(t_s, duration_s) * (W - 40) + 20
    y = H / 2 + 25 * math.sin(t_s / 40)
    ang = math.sin(t_s / 25) * 0.6
    dx, dy = math.cos(ang), math.sin(ang)
    d.line((x - 30 * dx, y - 30 * dy, x - 55 * dx, y - 50 * dy), fill=(70, 55, 35), width=5)  # tail
    d.ellipse((x - 22, y - 8, x + 22, y + 8), fill=(60, 48, 30))  # body
    d.ellipse((x + 16 * dx - 7, y + 16 * dy - 6, x + 16 * dx + 9, y + 16 * dy + 6), fill=(45, 36, 22))
    return img


def draw_side(t_s, duration_s):
    img = Image.new("RGB", (W, H), (200, 214, 222))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 140, W, H), fill=(170, 140, 100))             # substrate
    d.polygon([(10, 140), (60, 110), (110, 140)], fill=(140, 130, 120))  # rock under lamp, left
    d.ellipse((20, -30, 70, 10), fill=(255, 230, 150))            # lamp glow
    d.rectangle((240, 100, 310, 140), fill=(110, 90, 70))         # hide
    x = lizard_x(t_s, duration_s) * (W - 40) + 20
    y = 132 - (18 if x < 90 else 0)
    d.ellipse((x - 24, y - 7, x + 24, y + 7), fill=(60, 50, 30))
    d.line((x - 22, y, x - 50, y + 4), fill=(70, 55, 35), width=4)
    d.ellipse((x + 16, y - 10, x + 32, y + 2), fill=(45, 36, 22))
    return img


def write_video(path, draw, minutes):
    duration = minutes * 60
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "30",
           "-g", str(FPS * 10), "-movflags", "+faststart", str(path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(duration * FPS):
        proc.stdin.write(draw(i / FPS, duration).tobytes())
    proc.stdin.close()
    proc.wait()
    print("wrote", path.name, f"{minutes} min")


def write_series(path, mean, daily_amp, noise, days=7, step_s=300, spike=None, seed=0):
    rnd = random.Random(seed)
    values = []
    for k in range(int(days * 86400 / step_s)):
        t = k * step_s
        v = mean + daily_amp * math.sin(2 * math.pi * (t / 86400 - 0.25)) + rnd.gauss(0, noise)
        if spike and spike[0] <= t / 86400 < spike[1]:
            v += spike[2]
        values.append(round(v, 1))
    path.write_text(json.dumps({"t": step_s * 1000, "value": values}))
    print("wrote", path.name)


if __name__ == "__main__":
    VIDEOS.mkdir(parents=True, exist_ok=True)
    SENSORS.mkdir(parents=True, exist_ok=True)
    if "--sensors-only" not in sys.argv:
        write_video(VIDEOS / "gecko-top.mp4", draw_top, 15)
        write_video(VIDEOS / "skink-side.mp4", draw_side, 40)
        write_video(VIDEOS / "short-clip-top.mp4", draw_top, 3)
    write_series(SENSORS / "hot-temp-f.json", 90, 4, 0.6, spike=(3.0, 3.3, 9), seed=1)
    write_series(SENSORS / "cold-temp-f.json", 75, 3, 0.5, seed=2)
    write_series(SENSORS / "hot-temp-c.json", 32, 2, 0.3, seed=3)
    write_series(SENSORS / "cold-temp-c.json", 24, 1.5, 0.3, seed=4)
    write_series(SENSORS / "hot-humidity-rh.json", 25, 4, 1.0, seed=5)
    write_series(SENSORS / "cold-humidity-rh.json", 35, 5, 1.2, seed=6)
