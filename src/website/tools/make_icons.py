"""Draw the app icons (static/icons/) from the brand mark in templates/index.html: a lizard seen from above,
white on the RepTracker green. Run from src/website:   .venv/Scripts/python tools/make_icons.py

The brand mark is drawn on a 32 x 32 grid; here it is drawn 16 times larger and scaled down, for smooth edges.
"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "static" / "icons"
GREEN, WHITE, AMBER = (63, 125, 58, 255), (255, 255, 255, 255), (224, 160, 42, 255)
S = 16   # px per brand-mark unit while drawing


def _Bezier(p0, p1, p2, p3, steps=24):
    return [tuple((1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t ** 2 * c + t ** 3 * d
                  for a, b, c, d in zip(p0, p1, p2, p3)) for t in (i / steps for i in range(steps + 1))]


def Lizard():
    """The brand mark (32 units) in white with amber spots, on a transparent 512 x 512 layer, turned like the logo."""
    layer = Image.new("RGBA", (32 * S, 32 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    px = lambda pts: [(x * S, y * S) for x, y in pts]
    for leg in ([(13.6, 11.2), (9.4, 9.2), (8.4, 6.4)], [(18.4, 11.2), (22.6, 9.2), (23.6, 6.4)],
                [(13.6, 18), (9.4, 20), (8.4, 22.8)], [(18.4, 18), (22.6, 20), (23.6, 22.8)]):
        d.line(px(leg), fill=WHITE, width=2 * S, joint="curve")
    tail = _Bezier((16, 20.5), (16, 25.7), (20.6, 27.1), (22, 24.3), 160) + _Bezier((22, 24.3), (22.9, 22.4), (21.2, 21.2), (20, 22.3), 80)[1:]
    for x, y in tail:   # a round brush along the curve: a smooth, even stroke 2.4 units wide
        d.ellipse([(x - 1.2) * S, (y - 1.2) * S, (x + 1.2) * S, (y + 1.2) * S], fill=WHITE)
    for x, y in [(8.4, 6.4), (23.6, 6.4), (8.4, 22.8), (23.6, 22.8), (9.4, 9.2), (22.6, 9.2), (9.4, 20), (22.6, 20)]:
        d.ellipse([(x - 1.0) * S, (y - 1.0) * S, (x + 1.0) * S, (y + 1.0) * S], fill=WHITE)   # rounded joints and ends
    for cx, cy, r in [(8.3, 6, 1.3), (23.7, 6, 1.3), (8.3, 23.2, 1.3), (23.7, 23.2, 1.3)]:
        d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=WHITE)
    for cx, cy, rx, ry in [(16, 6.8, 3.3, 3.7), (16, 14.8, 3.8, 6.3)]:
        d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=WHITE)
    for cx, cy, r in [(14.7, 12.6, 0.9), (17.3, 15, 0.9), (15, 17.6, 0.8)]:
        d.ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=AMBER)
    return layer.rotate(18, resample=Image.BICUBIC)   # the logo is turned 18 degrees counterclockwise


def Icon(size, art=0.78, rounded=True):
    """A square icon: the lizard filling `art` of it on green. rounded: corners for "any" icons; maskable and
    Apple icons are full squares (the phone cuts its own shape)."""
    big = size * 4
    icon = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    ImageDraw.Draw(icon).rounded_rectangle([0, 0, big - 1, big - 1], radius=big // 5 if rounded else 0, fill=GREEN)
    lizard = Lizard().resize((round(big * art),) * 2, Image.LANCZOS)
    offset = (big - lizard.width) // 2
    icon.alpha_composite(lizard, (offset, offset))
    return icon.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    Icon(192).save(OUT / "icon-192.png")
    Icon(512).save(OUT / "icon-512.png")
    Icon(512, art=0.62, rounded=False).save(OUT / "maskable-512.png")   # inside the 80% safe zone
    Icon(180, art=0.72, rounded=False).convert("RGB").save(OUT / "apple-touch-icon.png")
    # Android's status bar shows notification badges as a white shape: the lizard alone, no background
    Lizard().resize((96, 96), Image.LANCZOS).save(OUT / "badge-96.png")
    print("Wrote", ", ".join(sorted(p.name for p in OUT.glob("*.png"))))
