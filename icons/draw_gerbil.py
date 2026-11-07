"""Purple gerbil holding a small teal camera, on a mint disc: the Gerbil icon.
Usage: py draw_gerbil.py OUTPUT_FOLDER  (writes gerbil.ico and PNG previews)
© 2026 Eloïs CHARBONNEL - GPL-3.0-or-later, see LICENSE."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFilter

S = 2048                       # drawing size (supersampled), 1 unit = S / 1024
k = S / 1024
OUT = sys.argv[1]

MINT, MINT_DARK = (171, 214, 180, 255), (128, 186, 141, 255)
LAV, LAV_DARK, LAV_DEEP = (165, 150, 214, 255), (124, 105, 190, 255), (88, 70, 150, 255)
BELLY = (214, 205, 240, 255)
PINK, PINK_IN = (240, 160, 175, 255), (226, 140, 160, 255)
TERRA, TERRA_DARK = (214, 158, 137, 255), (176, 112, 90, 255)
INK = (35, 28, 58, 255)


def P(pts):
    return [(x * k, y * k) for x, y in pts]


def ell(d, cx, cy, rx, ry, fill, outline=None, width=0):
    d.ellipse([(cx - rx) * k, (cy - ry) * k, (cx + rx) * k, (cy + ry) * k], fill=fill,
              outline=outline, width=int(width * k))


def bezier(p0, p1, p2, p3, n=60):
    out = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d_ = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d_ * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d_ * p3[1]))
    return out


img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# background disc
ell(d, 512, 512, 500, 500, MINT)
ell(d, 512, 512, 500, 500, None, outline=MINT_DARK, width=14)

# tail: long, curving behind the body, with a dark tuft
tail = bezier((640, 760), (900, 800), (930, 520), (820, 330), 80)
for i, (x, y) in enumerate(tail):
    r = 26 - 14 * i / len(tail)
    ell(d, x, y, r, r, LAV_DARK)
for i, (x, y) in enumerate(tail[-18:]):
    r = 20 + 6 * math.sin(i / 17 * math.pi)
    ell(d, x, y, r, r, LAV_DEEP)

# body (sitting, pear-shaped)
ell(d, 545, 640, 210, 215, LAV)
ell(d, 500, 520, 170, 170, LAV)
# belly
ell(d, 470, 650, 120, 150, BELLY)
# hind foot
ell(d, 600, 845, 120, 34, LAV_DARK)
ell(d, 430, 848, 70, 26, LAV_DARK)

# head
ell(d, 420, 365, 165, 140, LAV)
# snout (pointed toward the left)
d.polygon(P([(300, 300), (205, 395), (250, 440), (340, 455), (380, 420)]), fill=LAV)
ell(d, 265, 410, 62, 52, LAV)
# ear
ell(d, 505, 235, 70, 92, LAV_DARK)
ell(d, 505, 245, 44, 64, PINK_IN)
# eye
ell(d, 380, 345, 40, 44, INK)
ell(d, 366, 330, 13, 13, (255, 255, 255, 255))
# nose and mouth
ell(d, 213, 412, 20, 17, PINK)
d.line(P(bezier((222, 432), (240, 455), (262, 458), (282, 447), 20)), fill=INK, width=int(7 * k))
# whiskers
for (x0, y0, x1, y1) in ((250, 405, 120, 360), (252, 418, 112, 418), (250, 430, 125, 475)):
    d.line([(x0 * k, y0 * k), (x1 * k, y1 * k)], fill=LAV_DEEP, width=int(5 * k))

# small camera held in the front paws (lens toward the viewer)
TEAL, TEAL_DARK, LENS = (33, 83, 83, 255), (17, 45, 46, 255), (52, 36, 90, 255)
d.rounded_rectangle([262 * k, 482 * k, 330 * k, 520 * k], radius=12 * k, fill=TEAL, outline=TEAL_DARK, width=int(10 * k))
d.rounded_rectangle([238 * k, 505 * k, 468 * k, 680 * k], radius=30 * k, fill=TEAL, outline=TEAL_DARK, width=int(12 * k))
d.line([(262 * k, 535 * k), (444 * k, 535 * k)], fill=(58, 122, 112, 255), width=int(10 * k))
ell(d, 353, 600, 62, 62, (201, 194, 214, 255), outline=TEAL_DARK, width=12)
ell(d, 353, 600, 36, 36, LENS)
ell(d, 340, 586, 11, 11, (255, 255, 255, 255))
ell(d, 432, 552, 11, 11, (159, 211, 207, 255))
# paws over the camera
ell(d, 410, 530, 42, 34, LAV_DARK)
ell(d, 405, 640, 42, 34, LAV_DARK)

big = img
for size in (512, 256):
    big.resize((size, size), Image.Resampling.LANCZOS).save(os.path.join(OUT, f"gerbil_{size}.png"))
ico = big.resize((256, 256), Image.Resampling.LANCZOS)
ico.save(os.path.join(OUT, "gerbil.ico"), format="ICO",
         sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
# preview of the small sizes
prev = Image.new("RGBA", (16 + 24 + 32 + 48 + 64 + 128 + 256 + 8 * 8, 260), (246, 244, 251, 255))
x = 8
for s in (16, 24, 32, 48, 64, 128, 256):
    prev.alpha_composite(big.resize((s, s), Image.Resampling.LANCZOS), (x, 256 - s))
    x += s + 8
prev.save(os.path.join(OUT, "gerbil_sizes.png"))
print("ok")
