#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerbil - archaeological photo toolkit (formerly SherdCut): outlining of finds photographed with a
scale, at their real size (1:1).
© 2026 Eloïs CHARBONNEL
Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE.
This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to
redistribute it under the conditions of the licence.

For each photo NAME.JPG, in an "outlined_result" folder next to the photos:
  * NAME.JPG                        copy of the original photo;
  * NAME.psd                        layers "Original photo" (hidden), "Scale", "Ceramic"
                                    (editable layer masks in Photoshop);
  * NAME_outlined.tif               outlined ceramic;
  * NAME_outlined_scale.tif         ceramic + scale;
  * to_control/NAME_to_control.jpg  control preview;
  * outlined_report.csv             one row per photo.
When something is doubtful, the output files get the "_to_be_verified" suffix.

The scale (1 cm squares, or a ruler graduated in millimetres; 5 or 10 cm) gives the real
resolution of each photo. It is stored in the files: dropped into Illustrator, they show at 1:1.

Optional (--ai, needs onnxruntime): an AI second opinion (IS-Net or BiRefNet) that may only remove
background kept by the colour rule (perforations, gaps between sherds, halos), never add anything.

Usage:
  py gerbil.py FOLDER_OR_PHOTOS [...] [options]
  py gerbil.py --help
  (or the interface: Gerbil.bat / gerbil_gui.pyw)
"""

import argparse
import base64
import csv
import hashlib
import io
import json
import re
import math
import os
import shutil
import struct
import sys
import time
import traceback
import unicodedata
import urllib.request
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from fractions import Fraction

try:
    import numpy as np
    import cv2
    from PIL import Image, ImageCms, ImageDraw, ImageFont, ImageOps
except ImportError as _e:
    _package = {"cv2": "opencv-python-headless", "PIL": "pillow"}.get(_e.name, _e.name)
    sys.exit(f"Missing Python package: {_package}.\n"
             f"Install the required packages once: double-click Install.bat, or run\n"
             f'  py -3 -m pip install -r "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")}"')

VERSION = "2.1"
EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".png"}
RAW_EXTENSIONS = {".dng", ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".orf", ".rw2", ".raf", ".pef", ".srw", ".3fr", ".iiq"}
EXTENSIONS |= RAW_EXTENSIONS
ANALYSIS_SIZE = 1500           # longest side of the reduced image used for the analysis
BG_DEGREE = 2                  # degree of the polynomial modelling the background gradient
LOW_T, HIGH_T = 8.0, 18.0      # object / background thresholds (Lab colour distance)
L_WEIGHT = 0.5                 # weight of lightness: keeps soft shadows out of the object


# --------------------------------------------------------------------------
# Image and metadata loading
# --------------------------------------------------------------------------

@dataclass
class Photo:
    """A photo as the engine uses it: path, RGB pixels (upright), ICC profile, EXIF, shooting
    information (camera, lens, date) kept for the report and the metadata."""
    path: str
    rgb: np.ndarray
    icc: bytes
    exif: Image.Exif
    info: dict


def _txt(v):
    """EXIF value as clean text: bytes decoded (Latin-1), trailing zeros and spaces removed."""
    if v is None:
        return ""
    if isinstance(v, bytes):
        v = v.decode("latin-1", "replace")
    return str(v).strip("\x00 ")


def _rational(v):
    """EXIF number written as an XMP fraction ("1/125"), as XMP expects."""
    try:
        fr = Fraction(float(v)).limit_denominator(100000)
        return f"{fr.numerator}/{fr.denominator}"
    except Exception:
        return ""


def _xmp_date(v):
    """EXIF date "2025:12:01 21:03:55" turned into the XMP form "2025-12-01T21:03:55"."""
    v = _txt(v)
    if len(v) >= 19 and v[4] == ":" and v[7] == ":":
        return v[:4] + "-" + v[5:7] + "-" + v[8:10] + "T" + v[11:19]
    return ""


def develop_raw(path, half=False):
    """RAW photo developed by LibRaw (rawpy): white balance of the camera, sRGB, 8 bits, turned upright
    (the interface develops it the same way, so that the coordinates match)."""
    try:
        import rawpy
    except ImportError:
        raise RuntimeError("RAW photos need the rawpy package (py -3 -m pip install rawpy)")
    with rawpy.imread(path) as raw:
        return raw.postprocess(use_camera_wb=True, output_bps=8, half_size=half)


def load_photo(path):
    """Opens a photo as the engine needs it: RGB pixels (8 bits, turned upright by the EXIF
    orientation; RAW files developed by develop_raw), EXIF, ICC colour profile, and the
    shooting information kept for the report and the XMP. Returns a Photo."""
    if os.path.splitext(path)[1].lower() in RAW_EXTENSIONS:
        rgb = np.ascontiguousarray(develop_raw(path))
        try:                                       # metadata: most RAW files are TIFF-based
            with Image.open(path) as im:               # read now: the sub-directories are read lazily
                exif = Image.Exif()
                exif.load(im.getexif().tobytes())
        except Exception:
            exif = Image.Exif()
        icc = None
    else:
        im = Image.open(path)
        exif = im.getexif()
        icc = im.info.get("icc_profile")
        im = ImageOps.exif_transpose(im)
        rgb = np.ascontiguousarray(np.asarray(im.convert("RGB")))
    sub = exif.get_ifd(0x8769)
    make, model = _txt(exif.get(0x010F)), _txt(exif.get(0x0110))
    if make and model.lower().startswith(make.lower().split()[0]):
        make = ""
    focal = sub.get(0x920A)
    info = {
        "camera": f"{make} {model}".strip(),
        "lens": _txt(sub.get(0xA434)),
        "focal_mm": f"{float(focal):g}" if focal else "",
        "date": _txt(sub.get(0x9003)),
        # copied as XMP into the output PSD and TIFF files
        "xmp": {
            "tiff:Make": _txt(exif.get(0x010F)),
            "tiff:Model": _txt(exif.get(0x0110)),
            "exif:DateTimeOriginal": _xmp_date(sub.get(0x9003)),
            "photoshop:DateCreated": _xmp_date(sub.get(0x9003)),
            "exif:ExposureTime": _rational(sub.get(0x829A)) if sub.get(0x829A) else "",
            "exif:FNumber": _rational(sub.get(0x829D)) if sub.get(0x829D) else "",
            "exif:FocalLength": _rational(focal) if focal else "",
            "exif:ISOSpeedRatings": _txt(sub.get(0x8827)),
            "aux:Lens": _txt(sub.get(0xA434)),
            "exifEX:LensModel": _txt(sub.get(0xA434)),
            "aux:SerialNumber": _txt(sub.get(0xA431)),
            "exifEX:BodySerialNumber": _txt(sub.get(0xA431)),
            "dc:source": os.path.basename(path),
        },
    }
    return Photo(path, rgb, icc, exif, info)


def srgb_profile():
    """Standard sRGB colour profile (ICC), embedded when the photo has none."""
    return ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()


def output_exif(exif, dpi):
    """Copy of the shooting metadata, updated for the outlined file."""
    if exif is None or len(exif) == 0:
        return None
    try:
        e = Image.Exif()
        e.load(exif.tobytes())
        e[0x0112] = 1                      # orientation: the image is already upright
        e[0x011A] = float(dpi)
        e[0x011B] = float(dpi)
        e[0x0128] = 2                      # inches
        e[0x0131] = f"Gerbil {VERSION}"
        sub = e.get_ifd(0x8769)
        for t in (0x927C, 0xA002, 0xA003):  # MakerNote, original dimensions
            sub.pop(t, None)
        return e
    except Exception:
        return None


# --------------------------------------------------------------------------
# Background model and "object / background" map
# --------------------------------------------------------------------------

def to_lab(rgb):
    """RGB image -> CIELAB (L* 0-100, a* and b* around 0): colour differences in Lab match
    what the eye sees, which makes "different from the background" measurable."""
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    lab[..., 0] *= 100.0 / 255.0
    lab[..., 1:] -= 128.0
    return lab


def distance(lab, ref, l_weight=L_WEIGHT):
    """Colour distance of every pixel to the background model (Lab), lightness weighted by
    l_weight (shadows change the lightness more than the colour)."""
    dl = (lab[..., 0] - ref[..., 0]) * l_weight
    da = lab[..., 1] - ref[..., 1]
    db = lab[..., 2] - ref[..., 2]
    return np.sqrt(dl * dl + da * da + db * db)


def poly_terms(x, y, deg=BG_DEGREE):
    """Terms x^i * y^j of a 2D polynomial of degree deg: the background model is such a
    polynomial fitted on the background, so that a lighting gradient is followed."""
    return np.stack([(x ** i) * (y ** j) for i in range(deg + 1) for j in range(deg + 1 - i)], -1)


class BackgroundModel:
    """Background colour (Lab) modelled by a polynomial in x, y (lighting gradient)."""

    def __init__(self, lab):
        """Fits the background colour of the photo: a polynomial surface per Lab channel,
        fitted by least squares on the pixels that look like background (iterated, the
        object and the scale left out); decides whether the background is dark."""
        h, w = lab.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        T = poly_terms((xx + 0.5) / w, (yy + 0.5) / h)
        T = T.reshape(-1, T.shape[-1])
        flat = lab.reshape(-1, 3)
        med = np.median(flat, 0)
        # when the object fills most of the frame, the median is its colour: the edges of the
        # photo (band of 3 %) are then mostly background
        b = max(2, round(0.03 * min(h, w)))
        med_edges = np.median(np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
                                              lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)]), 0)
        if float(distance(med[None, None, :], med_edges[None, None, :])[0, 0]) > 12:
            med = med_edges
        bg = distance(lab, med[None, None, :]).ravel() < 12
        if bg.sum() < 0.05 * bg.size:
            bg = distance(lab, med[None, None, :]).ravel() < 25
        self.coefs = np.zeros((T.shape[1], 3), np.float32)
        for _ in range(4):
            idx = np.flatnonzero(bg)[::5]
            for c in range(3):
                self.coefs[:, c] = np.linalg.lstsq(T[idx], flat[idx, c], rcond=None)[0]
            model = (T @ self.coefs).reshape(h, w, 3)
            bg = distance(lab, model).ravel() < 6
        self.small_model = model
        self.dark = float(np.median(model[..., 0])) < 35       # black velvet, rather than a light background

    def evaluate(self, x0, y0, w, h, W, H, step=8):
        """Background colour over the area [x0, x0+w[ x [y0, y0+h[ of a W x H image."""
        gw, gh = max(2, w // step + 2), max(2, h // step + 2)
        xs = (x0 + np.linspace(0, w, gw, dtype=np.float32) + 0.5) / W
        ys = (y0 + np.linspace(0, h, gh, dtype=np.float32) + 0.5) / H
        xx, yy = np.meshgrid(xs, ys)
        g = (poly_terms(xx, yy) @ self.coefs).astype(np.float32)
        return cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)


def hysteresis(d, low, high):
    """Hysteresis threshold: keeps the regions above `low` that contain at least one pixel
    above `high` (a faint edge is kept when it belongs to a clear object)."""
    weak = (d > low).astype(np.uint8)
    n, lab = cv2.connectedComponents(weak, connectivity=8)
    keep = np.zeros(n, bool)
    keep[np.unique(lab[d > high])] = True
    keep[0] = False
    return keep[lab]


TRUE_HOLE_T = 2.5   # mean background distance under which a hole shows the background (handle, perforation)
SUPPORT_T = 15.0    # background distance under which a region attached to the edge is a translucent support


def local_texture(L, k=5):
    """Local spread (standard deviation) of the lightness over k x k pixels: the grain of a surface."""
    mu = cv2.blur(L, (k, k))
    return np.sqrt(np.maximum(cv2.blur(L * L, (k, k)) - mu * mu, 0))


def fill_holes(m, d=None, min_true_hole_area=None, keep_open=None):
    """Fills the holes of the mask (gloss reflections, light concretions), except true openings:
    holes large enough whose mean colour is the background colour (handle, perforation)."""
    inv = (~m).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    border = np.zeros(n, bool)
    border[np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]])] = True
    fill = ~border
    fill[0] = False
    if d is not None and min_true_hole_area:
        mean = np.bincount(lab.ravel(), weights=d.ravel(), minlength=n) / np.maximum(stats[:, cv2.CC_STAT_AREA], 1)
        true_hole = (stats[:, cv2.CC_STAT_AREA] >= min_true_hole_area) & (mean < TRUE_HOLE_T)
        fill &= ~true_hole
    if keep_open is not None and keep_open.any():
        fill[np.unique(lab[keep_open])] = False
    return m | fill[lab]


SHADOW_K = (0.3, 0.92)  # cast shadow: lightness between these fractions of the background lightness
SHADOW_CD = 6.0         # ... and the colour of the darkened background (distance to it, a* b*)
SHADOW_TEX = 2.5        # ... smooth: local spread of L* under this many times that of the background
SHADOW_TOUCH, SHADOW_SOFT = 0.15, 0.5
# a shadow lies along the outline (at least SHADOW_TOUCH of its own outline against the background) and
# fades into the background (gradient on that edge under SHADOW_SOFT of the object's own edge): on open
# photos of finds, shadows 0.21-0.66 and 0.07-0.40; dark smooth patches of objects (black gloss,
# obsidian, grey flint) touch the background on 0-5 % of their outline
SHADOW_DEEP_CD = 12.0   # the darkest part of a shadow, against the object, is followed up to this colour
                        # distance (light reflected by the object tints it: 3-9.5 measured), as long as
                        # it stays smooth (gradient under SHADOW_SOFT of the object's edge)
SHADOW_DEEP_MAX = 1.0   # ... and adds at most this fraction of the shadow found (a spindle whorl's: 0.56;
                        # more is a dark, smooth object - green glass - not the end of a shadow)


def cast_shadows(obj, lab, model):
    """Light background: the cast shadows kept by the colour rule (darker than the background by a
    shadow, of its colour, smooth, along the outline, fading into the background). Returns their mask,
    or None."""
    L = lab[..., 0]
    k = (L + 1) / (model[..., 0] + 1)
    cd = np.hypot(lab[..., 1] - k * model[..., 1], lab[..., 2] - k * model[..., 2])
    tex = local_texture(L)
    around = cv2.dilate(obj.astype(np.uint8), disk(5)) > 0
    if around.all():
        return None
    limit = max(1.5, SHADOW_TEX * float(np.median(tex[~around])))
    cand = obj & (k > SHADOW_K[0]) & (k < SHADOW_K[1]) & (cd < SHADOW_CD) & (tex < limit)
    cand = cv2.morphologyEx(cand.astype(np.uint8), cv2.MORPH_OPEN, disk(2))
    n, lab_c, stats, _ = cv2.connectedComponentsWithStats(cand, connectivity=8)
    if n <= 1:
        return None
    grad = np.hypot(cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)) / 8
    edge_bg = ~obj & (cv2.dilate(obj.astype(np.uint8), disk(1)) > 0)       # background touching the mask
    shadows = np.zeros(obj.shape, bool)
    min_area = max(50, 0.002 * obj.sum())
    sharp = 0.0                                 # gradient of the object's own edge (the sharpest seen)
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if a < min_area:
            continue
        r = lab_c == i
        contact = edge_bg & (cv2.dilate(r.astype(np.uint8), disk(2)) > 0)      # its edge on the background
        ring = (cv2.dilate(r.astype(np.uint8), disk(1)) > 0) & ~r
        if not contact.any() or contact.sum() < SHADOW_TOUCH * ring.sum():
            continue
        rest = edge_bg & ~(cv2.dilate(r.astype(np.uint8), disk(6)) > 0)        # the object's own edge
        if rest.any() and grad[contact].mean() < SHADOW_SOFT * np.median(grad[rest]):
            shadows |= r
            sharp = max(sharp, float(np.median(grad[rest])))
    if not shadows.any():
        return None
    # the darkest part of a shadow, against the object, is less of the background's colour (light
    # reflected by the object): the shadow is followed into it, up to the sharp edge of the object
    deep = (obj & ~shadows & (k > SHADOW_K[0]) & (k < SHADOW_K[1]) & (cd < SHADOW_DEEP_CD)
            & (grad < SHADOW_SOFT * sharp))
    nd, lab_d = cv2.connectedComponents((deep | shadows).astype(np.uint8), connectivity=8)
    base = np.bincount(lab_d[shadows], minlength=nd)
    added = np.bincount(lab_d[deep & ~shadows], minlength=nd)
    # followed only where it adds less than the shadow itself (more: a dark, smooth object - glass)
    linked = (base > 0) & (added <= SHADOW_DEEP_MAX * base)
    linked[0] = False
    return shadows | (linked[lab_d] & deep)


def disk(r):
    """Disc-shaped structuring element of radius r for the morphology (erosion, dilation...)."""
    r = max(1, int(round(r)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))


# --------------------------------------------------------------------------
# Scale detection and measurement (squares)
# --------------------------------------------------------------------------

def scale_ink_classes(rgb, white):
    """Black and vivid red pixels (coloured squares of an archaeological scale)."""
    rgb = rgb.astype(np.int16)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    black = mx < 0.42 * white
    red = (r > 0.45 * white) & (g < 0.42 * white) & (b < 0.5 * white) & (r - np.maximum(g, b) > 0.3 * white)
    return black, red


def straighten(img, center, theta, size, interp=cv2.INTER_LINEAR):
    """Extracts a crop of size=(w, h) centred on `center`, rotated so that the direction
    `theta` (radians, image frame) becomes horizontal."""
    wc, hc = size
    c, s = math.cos(theta), math.sin(theta)
    dx, dy = (wc - 1) / 2.0, (hc - 1) / 2.0
    M = np.array([[c, -s, center[0] - (c * dx - s * dy)],
                  [s, c, center[1] - (s * dx + c * dy)]], np.float64)
    out = cv2.warpAffine(img, M, (wc, hc), flags=interp | cv2.WARP_INVERSE_MAP,
                         borderMode=cv2.BORDER_REPLICATE)
    return out, M


def apply_affine(M, pts):
    """Applies the 2 x 3 affine matrix M to points (N x 2): rotation / scale / translation."""
    pts = np.asarray(pts, np.float64)
    return pts @ M[:, :2].T + M[:, 2]


def _runs(state):
    """Runs of equal values in a 1D array: [[value, start, end], ...] (reading the squares)."""
    chg = np.flatnonzero(np.diff(state)) + 1
    start = np.r_[0, chg]
    end = np.r_[chg, len(state)]
    return [[int(state[a]), int(a), int(b)] for a, b in zip(start, end)]


def _merge_runs(R):
    """Joins consecutive runs of the same value."""
    out = []
    for r in R:
        if out and out[-1][0] == r[0]:
            out[-1][2] = r[2]
        else:
            out.append(list(r))
    return out


def _clean_runs(R, min_len):
    """Removes the shortest inner runs (noise, digits) until all are at least min_len long."""
    R = _merge_runs(R)
    while len(R) > 2:
        lengths = [r[2] - r[1] for r in R]
        i = min(range(1, len(R) - 1), key=lambda k: lengths[k])
        if lengths[i] >= min_len:
            break
        neighbour = i - 1 if lengths[i - 1] >= lengths[i + 1] else i + 1
        R[i][0] = R[neighbour][0]
        R = _merge_runs(R)
    return R


def _crossing(p, x, direction):
    """Sub-pixel position where the profile p crosses 0.5 near x (direction +1: rising to the right)."""
    n = len(p)
    if direction > 0:
        for k in range(max(1, x - 3), min(n, x + 4)):
            if p[k - 1] < 0.5 <= p[k]:
                return k - 1 + (0.5 - p[k - 1]) / max(p[k] - p[k - 1], 1e-6)
    else:
        for k in range(min(n - 2, x + 3), max(-1, x - 4), -1):
            if p[k + 1] < 0.5 <= p[k]:
                return k + (p[k] - 0.5) / max(p[k] - p[k + 1], 1e-6)
    return float(x) - 0.5 if direction > 0 else float(x) + 0.5


def analyze_pattern(crop, valid=None):
    """Analyses a crop where the scale is horizontal and centred.
    Returns the position of the printed face, the number of squares and their length.
    `valid`: pixels of the crop that come from inside the photo (None: all of them). Beyond the photo
    edge the straightening copies the edge pixels: nothing is read there, and a square cut by the edge
    is counted but left out of the measurement (n = complete squares, n_cut = cut ones)."""
    hc, wc = crop.shape[:2]
    mn = crop.min(axis=2)
    white = float(np.percentile(mn[int(hc * 0.2):int(hc * 0.8), int(wc * 0.1):int(wc * 0.9)], 98))
    if white < 60:
        return None
    black, red = scale_ink_classes(crop, white)
    ink = black | red
    xa, xb = int(wc * 0.12), int(wc * 0.88)
    fr = ink[:, xa:xb].mean(axis=1)
    za, zb = int(hc * 0.25), int(hc * 0.75)
    if zb <= za or fr[za:zb].max() < 0.3:
        return None
    y = za + int(np.argmax(fr[za:zb]))

    def extend(direction):
        # tolerates a short gap (thin white line between the two rows of squares)
        end, gap, k = y, 0, y + direction
        while 0 <= k < hc:
            if fr[k] > 0.25:
                end, gap = k, 0
            else:
                gap += 1
                if gap > max(3, int(0.02 * hc)):
                    break
            k += direction
        return end

    y0, y1 = extend(-1), extend(+1)
    hf = y1 - y0 + 1
    if hf < 4:
        return None
    ym = (y0 + y1) / 2.0
    m = max(1, int(round(hf * 0.12)))
    top = ink[y0 + m:int(math.floor(ym)) - m + 1]
    bottom = ink[int(math.ceil(ym)) + m:y1 - m + 1]
    if top.shape[0] < 1 or bottom.shape[0] < 1:
        return None
    pt, pb = top.mean(axis=0), bottom.mean(axis=0)
    state = (pt > 0.4).astype(np.int8) + 2 * (pb > 0.4).astype(np.int8)
    if valid is not None:
        # photo edge across the scale, on its middle line (a scale touching the photo edge along
        # its length is not cut): nothing is read beyond it
        cols_in = valid[int(round(ym))]
        state = np.where(cols_in, state, 0).astype(np.int8)
    R = _clean_runs(_runs(state), 3)
    for _ in range(3):
        # typical length of a square: length-weighted median (fragments caused by the
        # digits, the arrow or the graduations weigh little)
        lengths = np.sort([r[2] - r[1] for r in R if r[0] != 0])
        if len(lengths) < 3:
            return None
        cum = np.cumsum(lengths)
        R = _clean_runs(R, 0.35 * float(lengths[np.searchsorted(cum, cum[-1] / 2)]))
    idx = [k for k, r in enumerate(R) if r[0] != 0]
    if not idx:
        return None
    segs = R[idx[0]:idx[-1] + 1]
    vx0, vx1 = None, None                  # visible ends of squares cut by the photo edge
    if valid is not None:
        inside = np.flatnonzero(cols_in)
        if len(inside) and inside[0] > 0 and segs[0][1] <= inside[0] + 1:
            vx0, segs = float(inside[0]), segs[1:]
        if len(inside) and inside[-1] < wc - 1 and segs and segs[-1][2] >= inside[-1]:
            vx1, segs = float(inside[-1] + 1), segs[:-1]
    n = len(segs)
    if n < 3:
        return None
    s0, s1 = segs[0], segs[-1]
    p0 = pt if s0[0] & 1 else pb
    p1 = pt if s1[0] & 1 else pb
    xs = _crossing(p0, s0[1], +1)
    xe = _crossing(p1, s1[2] - 1, -1)
    seg = (xe - xs) / n
    deviations = [abs((r[2] - r[1]) - seg) / seg for r in segs]
    if seg < 3 or max(deviations) > 0.3 or not (0.15 <= hf / seg <= 3.0):
        return None
    # the light squares of a single-row scale must really be white
    # (otherwise: painted bands on a ceramic, not a scale)
    for r in segs:
        if r[0] == 0 and float(mn[y0:y1 + 1, r[1]:r[2]].mean()) < 0.75 * white:
            return None
    single_row = all(r[0] in (0, 3) for r in segs)
    nr = int(red[y0:y1 + 1].sum())
    flip = False
    if nr > 0.02 * hf * (xe - xs):
        yr = np.nonzero(red[y0:y1 + 1])[0].mean() + y0
        flip = yr > ym
    return {
        "y0": y0, "y1": y1, "xs": xs, "xe": xe, "n": n, "seg": seg, "hf": hf,
        "boundaries": [xs + k * seg for k in range(n + 1)],
        "irregularity": max(deviations), "flip": flip, "white": white, "single_row": single_row,
        "n_cut": (vx0 is not None) + (vx1 is not None),
        "vx0": xs if vx0 is None else vx0, "vx1": xe if vx1 is None else vx1,
    }


def _inside(shape, M, crop_shape):
    """Pixels of a straightened crop that come from inside the photo; None when they all do."""
    hc, wc = crop_shape[:2]
    H, W = shape[:2]
    c = apply_affine(M, [[0, 0], [wc - 1, 0], [0, hc - 1], [wc - 1, hc - 1]])
    if c[:, 0].min() >= 0 and c[:, 1].min() >= 0 and c[:, 0].max() <= W - 1 and c[:, 1].max() <= H - 1:
        return None
    yy, xx = np.mgrid[0:hc, 0:wc].astype(np.float32)
    x = M[0, 0] * xx + M[0, 1] * yy + M[0, 2]
    y = M[1, 0] * xx + M[1, 1] * yy + M[1, 2]
    return (x >= 0) & (x <= W - 1) & (y >= 0) & (y <= H - 1)


def _fit_comb(xs, step, min_n, tol=0.15):
    """Fits a regular sequence x_k = a0 + step * k to the positions xs (common phase by circular
    mean, then least squares rejecting the residuals above tol x step). Returns (a0, step, k, res)
    for the kept positions, or None."""
    if len(xs) < min_n or step <= 0:
        return None
    a0 = float(np.angle(np.exp(2j * np.pi * xs / step).mean()) / (2 * np.pi) * step)
    for _ in range(5):
        k = np.round((xs - a0) / step)
        ok = np.abs(xs - (a0 + step * k)) < tol * step
        if ok.sum() < min_n or len(np.unique(k[ok])) < 2:
            return None
        (a0, step), *_ = np.linalg.lstsq(np.column_stack([np.ones(ok.sum()), k[ok]]), xs[ok], rcond=None)
    k = np.round((xs - a0) / step)
    res = xs - (a0 + step * k)
    ok = np.abs(res) < tol * step
    if ok.sum() < min_n:
        return None
    return float(a0), float(step), k[ok].astype(int), res[ok]


CARD_CHROMA = 20.0    # max chroma (median) of the white of a scale card, second reading
                      # (cards measured 3 to 11, an orange sherd under written strokes 42)


def analyze_comb(crop, valid=None):
    """Second reading of a checkerboard (crop where the scale is horizontal and centred), used only
    when analyze_pattern fails. Robust to digits printed inside the squares ("5", "10", "cm") and
    to any number of squares: the boundaries between squares are where the signed profile
        q(x) = ink(top row) - ink(bottom row)      (two rows), or 2 ink(row) - 1 (single row)
    changes sign between two plateaus (|q| > 0.3). A digit only lowers |q| inside its square: the
    sign, hence the boundaries, do not change. The boundaries are fitted by a regular comb
    x_k = a0 + square x k (as the ruler ticks), so that the square length is measured over the whole
    scale; the end squares (no sign change against the card or the background) are added when their
    sign continues the alternation. Same result fields as analyze_pattern."""
    hc, wc = crop.shape[:2]
    mn = crop.min(axis=2)
    white = float(np.percentile(mn[int(hc * 0.2):int(hc * 0.8), int(wc * 0.1):int(wc * 0.9)], 98))
    if white < 60:
        return None
    black, red = scale_ink_classes(crop, white)
    ink = black | red
    fr = ink[:, int(wc * 0.12):int(wc * 0.88)].mean(axis=1)
    za, zb = int(hc * 0.25), int(hc * 0.75)
    if zb <= za or fr[za:zb].max() < 0.3:
        return None
    y = za + int(np.argmax(fr[za:zb]))

    def extend(direction):
        end, gap, k = y, 0, y + direction
        while 0 <= k < hc:
            if fr[k] > 0.25:
                end, gap = k, 0
            else:
                gap += 1
                if gap > max(3, int(0.02 * hc)):
                    break
            k += direction
        return end

    y0, y1 = extend(-1), extend(+1)
    hf = y1 - y0 + 1
    if hf < 4:
        return None
    ym = (y0 + y1) / 2.0
    m = max(1, int(round(hf * 0.12)))
    top = ink[y0 + m:int(math.floor(ym)) - m + 1]
    bottom = ink[int(math.ceil(ym)) + m:y1 - m + 1]
    if top.shape[0] < 1 or bottom.shape[0] < 1:
        return None
    pt, pb = top.mean(axis=0), bottom.mean(axis=0)
    cols_in = valid[int(round(ym))] if valid is not None else np.ones(wc, bool)
    chroma = None

    def read(q, single_row):
        nonlocal chroma
        q = np.where(cols_in, cv2.GaussianBlur(q.reshape(1, -1).astype(np.float32), (0, 0), 1.0).ravel(), 0)
        idx = np.flatnonzero(np.abs(q) > 0.3)
        if len(idx) < 2:
            return None
        sg = q[idx] > 0
        xs = []
        for c in np.flatnonzero(sg[1:] != sg[:-1]):
            a, b = idx[c], idx[c + 1]
            j = a + np.flatnonzero((q[a:b] > 0) != (q[a + 1:b + 1] > 0))
            if len(j) != 1:
                continue
            j = int(j[0])
            xs.append(j + q[j] / (q[j] - q[j + 1]))
        xs = np.array(xs)
        if len(xs) < 3:
            return None
        fit = _fit_comb(xs, float(np.median(np.diff(xs))), 3)
        if fit is None:
            return None
        a0, seg, k, res = fit
        if seg < 3 or float(np.sqrt(np.mean(res ** 2))) > 0.08 * seg:
            return None

        def mean_q(kk, visible_only=False):
            a, b = a0 + seg * kk, a0 + seg * (kk + 1)
            a, b = int(round(a + 0.2 * seg)), int(round(b - 0.2 * seg))
            if a < 0 or b > wc or b <= a:
                return None
            v = cols_in[a:b]
            if visible_only:
                return float(q[a:b][v].mean()) if v.sum() >= 0.3 * (b - a) else None
            return float(q[a:b].mean()) if v.all() else None

        # squares between fitted boundaries: the longest run of squares whose sign alternates
        # (a boundary found on an object near the scale lies outside this run); a square holding
        # digits ("10", "cm") keeps its sign but a weaker |q|
        best, run = (0, 0, 0), None
        for kk in range(int(k.min()), int(k.max()) + 1):
            v = mean_q(kk) if kk < k.max() else None
            if v is not None and abs(v) >= 0.12 and run and (v > 0) != (run[2] > 0):
                run = (run[0], kk + 1, v)
            elif v is not None and abs(v) >= 0.3:
                run = (kk, kk + 1, v)
            else:
                run = None
            if run and run[1] - run[0] > best[1] - best[0]:
                best = run
        k0, k1 = best[0], best[1]                    # squares k0 .. k1 - 1
        if k1 - k0 < 2:
            return None
        v0 = mean_q(k0)
        sign = 1 if v0 > 0 else -1                   # square kk has the sign: sign x (-1)^(kk - k0)
        kref = k0
        vx0 = vx1 = None
        # end squares of a two-row checkerboard: no sign change against the card or the background
        # (both rows alike there: q = 0); a single row ends with boundaries on both sides
        end_t = 0.15 if not single_row else float("inf")
        while True:
            want = sign * (-1) ** ((k0 - 1) - kref)
            v = mean_q(k0 - 1)
            if v is not None and v * want > end_t:
                k0 -= 1
                continue
            a = a0 + seg * (k0 - 1)
            if a < wc and int(a0 + seg * k0) > 0 and not cols_in[max(0, int(a)):max(1, int(a0 + seg * k0))].all():
                vis = mean_q(k0 - 1, visible_only=True)
                if vis is not None and vis * want > max(0.4, end_t):
                    vx0 = float(np.flatnonzero(cols_in)[0])
            break
        while True:
            want = sign * (-1) ** (k1 - kref)
            v = mean_q(k1)
            if v is not None and v * want > end_t:
                k1 += 1
                continue
            b = a0 + seg * (k1 + 1)
            if b > 0 and int(a0 + seg * k1) < wc and not cols_in[max(0, int(a0 + seg * k1)):min(wc, int(b) + 1)].all():
                vis = mean_q(k1, visible_only=True)
                if vis is not None and vis * want > max(0.4, end_t):
                    vx1 = float(np.flatnonzero(cols_in)[-1] + 1)
            break
        n = k1 - k0
        if n < 3:
            return None
        # the light squares of a single-row scale must really be white (not painted bands)
        if single_row:
            for kk in range(k0, k1):
                if sign * (-1) ** (kk - kref) < 0:
                    a, b = int(a0 + seg * kk + 0.2 * seg), int(a0 + seg * (kk + 1) - 0.2 * seg)
                    if float(mn[y0:y1 + 1, a:b].mean()) < 0.75 * white:
                        return None
        else:
            # two rows: the row that is not inked must be the white of a card, uncoloured (not the
            # surface of a sherd under painted or written strokes); digits only cover part of it
            if chroma is None:
                lab = to_lab(cv2.GaussianBlur(crop, (5, 5), 0))
                chroma = np.hypot(lab[..., 1], lab[..., 2])
            light = []
            for kk in range(k0, k1):
                a, b = int(a0 + seg * kk + 0.2 * seg), int(a0 + seg * (kk + 1) - 0.2 * seg)
                if a < 0 or b > wc or b <= a:
                    continue
                rows = (slice(int(math.ceil(ym)) + m, y1 - m + 1) if sign * (-1) ** (kk - kref) > 0
                        else slice(y0 + m, int(math.floor(ym)) - m + 1))
                light.append(np.median(chroma[rows, a:b]))
            if not light or float(np.median(light)) > CARD_CHROMA:
                return None
        inner = (k >= k0) & (k <= k1)
        kk = np.sort(k[inner])
        xk = np.sort((a0 + seg * k + res)[inner])
        dev = [abs((xk[i + 1] - xk[i]) / (kk[i + 1] - kk[i]) - seg) / seg
               for i in range(len(kk) - 1) if kk[i + 1] - kk[i] == 1]
        xs_, xe_ = a0 + seg * k0, a0 + seg * k1
        return {"y0": y0, "y1": y1, "xs": xs_, "xe": xe_, "n": n, "seg": seg, "hf": hf,
                "boundaries": [xs_ + i * seg for i in range(n + 1)],
                "irregularity": max(dev) if dev else 0.0, "white": white, "single_row": single_row,
                "n_cut": (vx0 is not None) + (vx1 is not None),
                "vx0": xs_ if vx0 is None else vx0, "vx1": xe_ if vx1 is None else vx1}

    found = [r for r in (read(pt - pb, False), read(pt + pb - 1.0, True)) if r is not None]
    if not found:
        return None
    res = max(found, key=lambda r: (r["n"], not r["single_row"]))
    if not (0.15 <= res["hf"] / res["seg"] <= 3.0):
        return None
    # never turned over: the side of the red row differs between makes of scale (red on top for
    # the DDN scales, below for others, where the digits are then upright): the scale keeps its
    # orientation in the photo
    res["flip"] = False
    return res


@dataclass
class Scale:
    """A scale found (or given): px/cm, number of squares, length, angle, outline in the photo
    (poly), enlarged zone (holder, putty), straightened crop and its matrix M, reading details
    (pattern), note, doubts and kind (checkerboard, ruler, manual, learned)."""
    found: bool = False
    px_cm: float = 0.0
    n_squares: int = 0
    length_cm: float = 0.0
    theta: float = 0.0
    center: tuple = (0.0, 0.0)
    crop_size: tuple = (0, 0)
    M: np.ndarray = None          # straightened crop -> original image
    crop: np.ndarray = None       # straightened crop (full resolution)
    rect: tuple = None            # outline of the scale (x0, y0, x1, y1) in the crop
    pattern: dict = None
    poly: np.ndarray = None       # outline in the original image (4 x 2)
    zone: np.ndarray = None       # enlarged zone (holder, putty) in the original image
    note: str = ""
    doubts: list = None           # reasons to check the measurement
    kind: str = ""                # "checkerboard" or "ruler"


def _rect_axis(rect):
    """Angle of the long side of a rotated rectangle (radians, -pi/2..pi/2), and its long and
    short sides."""
    pts = cv2.boxPoints(rect)
    e1, e2 = pts[1] - pts[0], pts[2] - pts[1]
    L, S = (e1, e2) if np.hypot(*e1) >= np.hypot(*e2) else (e2, e1)
    theta = math.atan2(L[1], L[0])
    if theta > math.pi / 2:
        theta -= math.pi
    elif theta <= -math.pi / 2:
        theta += math.pi
    return theta, float(np.hypot(*L)), float(np.hypot(*S))


def _single_row_groups(ink):
    """Single-row scale: its black squares do not touch. Looks for solid blobs of the same
    size, aligned and evenly spaced. Returns lists of points."""
    n, lab, stats, cents = cv2.connectedComponentsWithStats(ink, connectivity=8)
    ids = [i for i in range(1, n)
           if stats[i, 4] >= 40 and stats[i, 4] >= 0.55 * stats[i, 2] * stats[i, 3]]
    if len(ids) < 3:
        return []
    C = cents[ids]
    A = stats[ids, 4].astype(float)
    seen, groups = set(), []
    for a_i in range(len(ids)):
        d = np.hypot(*(C - C[a_i]).T)
        side = math.sqrt(A[a_i])
        for b in np.argsort(d)[1:5]:
            step = d[b]
            if max(A[a_i], A[b]) > 1.6 * min(A[a_i], A[b]) or not (1.2 * side <= step <= 3.5 * side):
                continue
            u = (C[b] - C[a_i]) / step
            v = C - C[a_i]
            t = v @ u / step
            offset = np.abs(v[:, 0] * u[1] - v[:, 1] * u[0])
            ok = ((offset < 0.3 * side) & (np.abs(t - np.round(t)) < 0.15)
                  & (A < 1.6 * A[a_i]) & (A > A[a_i] / 1.6))
            q = sorted({int(round(t[k])): k for k in np.flatnonzero(ok)}.items())
            pos = [p for p, _ in q]
            if 0 not in pos:
                continue
            lo = hi = pos.index(0)
            while lo > 0 and pos[lo - 1] == pos[lo] - 1:
                lo -= 1
            while hi < len(pos) - 1 and pos[hi + 1] == pos[hi] + 1:
                hi += 1
            members = frozenset(ids[q[k][1]] for k in range(lo, hi + 1))
            if len(members) >= 3 and members not in seen:
                seen.add(members)
                pts = [np.column_stack(np.nonzero(
                    lab[stats[m, 1]:stats[m, 1] + stats[m, 3], stats[m, 0]:stats[m, 0] + stats[m, 2]] == m))[:, ::-1]
                    + [stats[m, 0], stats[m, 1]] for m in members]
                groups.append(np.vstack(pts).astype(np.float32))
    return groups


def _card_side(crop, res):
    """Single-row scale ending with a white square: side where the card continues
    (-1 left, +1 right, 0 undecided). Each end is compared with the white of the
    inner white squares of the scale."""
    lab = to_lab(cv2.GaussianBlur(crop, (5, 5), 0))
    mn = crop.min(axis=2)
    wc = crop.shape[1]
    y0, y1, xs, seg, n = res["y0"], res["y1"], res["xs"], res["seg"], res["n"]
    m = max(1, int(0.2 * seg))
    whites = []
    for k in range(n):
        a, b = int(xs + k * seg) + m, int(xs + (k + 1) * seg) - m
        if b > a and mn[y0:y1 + 1, a:b].mean() > 0.75 * res["white"]:
            whites.append(lab[y0:y1 + 1, a:b].reshape(-1, 3))
    if not whites:
        return 0
    ref = np.median(np.vstack(whites), axis=0)

    def deviation(a, b):
        a, b = max(0, int(a)), min(wc, int(b))
        if b - a < 2:
            return None
        return float(np.median(np.linalg.norm(lab[y0:y1 + 1, a:b] - ref, axis=2)))

    left = deviation(xs - 0.8 * seg, xs - 0.2 * seg)
    right = deviation(res["xe"] + 0.2 * seg, res["xe"] + 0.8 * seg)
    if left is None or right is None:
        return 0
    if right < 0.5 * left and left > 4:
        return 1
    if left < 0.5 * right and right > 4:
        return -1
    return 0


def _scale_on_dark(rgb, small, f, forced_cm):
    """Dark background (black velvet): the black squares merge with the background. The scale is
    looked for from its light squares: for each large, elongated group of light areas, everything
    outside the rectangle around it (and beyond the photo edge) is painted white, so that the scale
    looks as it does on a light background; then the usual detection runs (without the ruler)."""
    H, W = rgb.shape[:2]
    grey = small.min(axis=2)
    light = (grey > 0.55 * float(np.percentile(grey, 99.5))).astype(np.uint8)
    light_all = light.copy()
    # light squares elongated across the scale (bands): what is much thicker than them (label
    # stuck to the scale, light sherd) is set aside
    k, labc, stc, _ = cv2.connectedComponentsWithStats(light, connectivity=8)
    widths = []
    for j in range(1, k):
        x, y, w, h, a = stc[j]
        if a >= 30:
            ys, xs = np.nonzero(labc[y:y + h, x:x + w] == j)
            _, L, S = _rect_axis(cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32)))
            if L >= 2 * S and a >= 0.6 * L * S:
                widths.append(S)
    if len(widths) >= 3:
        # a label is thick once the writing inside it is filled (closed holes only: the black squares
        # of the scale reach its edge)
        outside = np.pad(1 - light, 1, constant_values=1)
        cv2.floodFill(outside, None, (0, 0), 2)
        solid = light | (outside[1:-1, 1:-1] == 1).astype(np.uint8)
        thick = cv2.morphologyEx(solid, cv2.MORPH_OPEN, disk(max(2, round(0.75 * float(np.median(widths))))))
        thick &= light
        light &= (cv2.dilate(thick, disk(2)) == 0).astype(np.uint8)
    def cards_of(light, stretch=1.0):
        # the white squares only touch at their corners: grouped by a slight dilation
        n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(light, disk(3)), connectivity=8)
        cards = []
        for i in sorted(range(1, n), key=lambda k: -st[k, 4])[:6]:
            x, y, w, h, a = st[i]
            if a < 100:
                break
            ys, xs = np.nonzero((lab[y:y + h, x:x + w] == i) & (light[y:y + h, x:x + w] > 0))
            pts = np.column_stack([xs + x, ys + y]).astype(np.float32)
            rect = cv2.minAreaRect(pts)
            _, L, S = _rect_axis(rect)
            if L < 1.6 * max(S, 1.0):
                continue
            # the rectangle around the light squares also covers the black squares of the corners
            if stretch != 1.0:              # lengthened along the scale (group covering part of it)
                (rw, rh) = rect[1]
                rect = (rect[0], (rw * stretch, rh) if rw >= rh else (rw, rh * stretch), rect[2])
            card = np.zeros(small.shape[:2], np.uint8)
            cv2.fillConvexPoly(card, np.round(cv2.boxPoints(rect)).astype(np.int32), 1)
            card = cv2.dilate(card, disk(2))
            card[[0, -1], :] = 0                    # white frame: what lies beyond the photo edge
            card[:, [0, -1]] = 0                    # (copied by the straightening) is white too
            cards.append(card)
        return cards

    cards = cards_of(light)
    # every group with the usual reading first, then with the second reading (analyze_comb), which
    # also tries the groups of all the light areas (large white squares, not bands, are "thick"), each
    # rectangle lengthened 3 times along the scale: digits ("10", "cm") split the light squares, and a
    # group may cover only part of the scale (the reading stops where the squares stop)
    fallback = None
    for comb in (False, True):
        for card in (cards_of(light, 3.0) + cards_of(light_all, 3.0) if comb else cards):
            small_w = small.copy()
            small_w[card == 0] = 255
            card_big = cv2.resize(card, (W, H), interpolation=cv2.INTER_NEAREST)
            card_big[[0, -1], :] = 0
            card_big[:, [0, -1]] = 0
            rgb_w = rgb.copy()
            rgb_w[card_big == 0] = 255
            scale = detect_scale(rgb_w, small_w, f, forced_cm, min_ratio=2.0, ruler=False,
                                 comb="only" if comb else False)
            if not scale.found:
                continue
            # the first scale of a usual length is kept; failing that, the first one found by the
            # usual reading, or else the second reading with the most squares (doubtful length)
            if scale.length_cm in SCALE_LENGTHS:
                return scale
            if fallback is None or (comb and fallback.note.startswith("squares read")
                                    and scale.n_squares > fallback.n_squares):
                fallback = scale
    return fallback or Scale(note="scale not detected")


GLYPH_FONTS = ("arial.ttf", "arialbd.ttf", "calibri.ttf", "calibrib.ttf", "verdana.ttf", "verdanab.ttf",
               "tahoma.ttf", "tahomabd.ttf", "segoeui.ttf", "segoeuib.ttf", "times.ttf", "timesbd.ttf")
GLYPH_CHARS = "0123456789cm"   # signs printed on scales
GLYPH_SIZE = 24                # side of the normalised sign images
GLYPH_MARGIN = 0.08            # a sign votes only if one side matches better by more than this
_glyph_templates = None        # drawn once per process


def _glyph_vector(g):
    """Sign cropped to its box, scaled into GLYPH_SIZE x GLYPH_SIZE, centred, zero mean, unit norm."""
    ys, xs = np.nonzero(g)
    if len(ys) == 0:
        return None
    g = g[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.float32)
    h, w = g.shape
    s = GLYPH_SIZE / max(h, w)
    g = cv2.resize(g, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA)
    out = np.zeros((GLYPH_SIZE, GLYPH_SIZE), np.float32)
    oy, ox = (GLYPH_SIZE - g.shape[0]) // 2, (GLYPH_SIZE - g.shape[1]) // 2
    out[oy:oy + g.shape[0], ox:ox + g.shape[1]] = g
    v = out - out.mean()
    return v / (float(np.linalg.norm(v)) + 1e-6)


def _glyph_templates_get():
    """Templates of GLYPH_CHARS drawn with the fonts of Windows (empty list when none is found)."""
    global _glyph_templates
    if _glyph_templates is None:
        _glyph_templates = []
        folder = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        for name in GLYPH_FONTS:
            try:
                font = ImageFont.truetype(os.path.join(folder, name), 64)
            except OSError:
                continue
            for ch in GLYPH_CHARS:
                im = Image.new("L", (100, 100), 0)
                ImageDraw.Draw(im).text((18, 5), ch, fill=255, font=font)
                v = _glyph_vector(np.asarray(im) > 127)
                if v is not None:
                    _glyph_templates.append(v)
        if _glyph_templates:
            _glyph_templates = np.stack(_glyph_templates).reshape(len(_glyph_templates), -1)
    return _glyph_templates


def digits_upside_down(crop, res):
    """Is the scale of this straightened crop upside down, judging from the signs printed in its
    squares ("5", "10", "cm")? Each sign (dark ink in a light square, light ink in a dark or red one)
    is compared with templates of digits and of "c", "m" drawn with common fonts, as it is and turned
    over (180 degrees): the side that looks more like a printed character gets the vote of the sign,
    when the difference exceeds GLYPH_MARGIN. Returns True / False, or None when undecided (no clear
    sign, no font). Used on the final crop, once the red row is on top: on 1,265 scales of known
    orientation, no error (2 % undecided at a margin of 0.05, 0.08 is used)."""
    T = _glyph_templates_get()
    if len(T) == 0:
        return None
    mn = crop.min(axis=2).astype(np.float32)
    white = res["white"]
    y0, y1 = int(res["y0"]), int(res["y1"])
    ym = (y0 + y1) / 2.0
    vote = 0.0
    for k in range(res["n"]):
        a, b = res["xs"] + k * res["seg"], res["xs"] + (k + 1) * res["seg"]
        mx = 0.12 * res["seg"]
        for r0, r1 in ((y0, int(ym)), (int(ym) + 1, y1)):
            my = int(0.12 * (r1 - r0))
            reg = mn[r0 + my:r1 - my + 1, int(a + mx):int(b - mx)]
            if reg.size < 50:
                continue
            light = float(np.median(reg)) > 0.6 * white
            g = (reg < 0.5 * white) if light else (reg > 0.7 * white)
            if not 0.03 < g.mean() < 0.45:
                continue
            n, lab, st, _ = cv2.connectedComponentsWithStats(g.astype(np.uint8), connectivity=8)
            if n < 2:
                continue
            hmax = st[1:, 3].max()
            for j in range(1, n):
                x, y, w, h, area = st[j]
                if h < 0.5 * hmax or area < 15 or h < 8 or w < 8:
                    continue
                c = lab[y:y + h, x:x + w] == j
                v, vr = _glyph_vector(c), _glyph_vector(c[::-1, ::-1])
                up, down = float((T @ v.ravel()).max()), float((T @ vr.ravel()).max())
                if abs(up - down) > GLYPH_MARGIN:
                    vote += up - down
    return None if vote == 0 else vote < 0


MANUAL_SCALES = "gerbil_scales.json"     # next to the photos: scales given by hand (two points)
OLD_MANUAL_SCALES = "sherdcut_scales.json"   # same file, written before the renaming (still read)


def manual_scale_entry(path):
    """Scale given by hand for this photo (interface: "Set scale…"), or None. The file MANUAL_SCALES,
    in the folder of the photo, maps a photo name to {"p1": [x, y], "p2": [x, y], "cm": length between
    the two points, "width_cm": width of the scale}; coordinates in pixels of the upright photo."""
    folder = os.path.dirname(os.path.abspath(path))
    entry = None
    for name in (MANUAL_SCALES, OLD_MANUAL_SCALES):
        try:
            with open(os.path.join(folder, name), encoding="utf-8") as fh:
                entry = json.load(fh).get(os.path.basename(path))
            break
        except (OSError, ValueError, AttributeError):
            continue
    try:
        p1, p2, cm = [float(v) for v in entry["p1"]], [float(v) for v in entry["p2"]], float(entry["cm"])
    except (TypeError, KeyError, ValueError):
        return None
    if cm <= 0 or len(p1) != 2 or len(p2) != 2 or math.dist(p1, p2) < 10:
        return None
    return {"p1": p1, "p2": p2, "cm": cm, "width_cm": float(entry.get("width_cm", 1.0))}


def manual_scale(rgb, entry):
    """Scale from two points of known distance: px/cm = distance / length. The scale layer is a band of
    the given width around the segment, straightened like a detected scale; centimetre marks every cm."""
    (x1, y1), (x2, y2) = entry["p1"], entry["p2"]
    theta = math.atan2(y2 - y1, x2 - x1)
    if theta > math.pi / 2:                    # keep the orientation of the photo (as _rect_axis)
        theta -= math.pi
    elif theta <= -math.pi / 2:
        theta += math.pi
    d = math.hypot(x2 - x1, y2 - y1)
    px_cm = d / entry["cm"]
    h = max(4.0, entry["width_cm"] * px_cm)
    center = ((x1 + x2) / 2, (y1 + y2) / 2)
    size = (int(d + 1.2 * px_cm) // 2 * 2 + 1, int(3 * h) // 2 * 2 + 1)
    crop, M = straighten(rgb, center, theta, size, interp=cv2.INTER_CUBIC)
    xs, ys = (size[0] - 1) / 2 - d / 2, (size[1] - 1) / 2 - h / 2
    x0, y0, x1, y1 = xs, ys, xs + d, ys + h
    poly = apply_affine(M, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    mx, my = 0.3 * px_cm, 0.5 * h
    zone = apply_affine(M, [[x0 - mx, y0 - my], [x1 + mx, y0 - my], [x1 + mx, y1 + my], [x0 - mx, y1 + my]])
    n = int(entry["cm"] + 1e-6)
    pattern = {"y0": int(round(y0)), "y1": int(round(y1)), "hf": max(1, int(round(h))), "seg": px_cm,
               "boundaries": [x0 + k * px_cm for k in range(n + 1)], "irregularity": 0.0}
    return Scale(True, px_cm, 0, entry["cm"], theta, center, size, M, crop, (x0, y0, x1, y1), pattern, poly,
                 zone, f"manual scale ({entry['cm']:g} cm between two points)", [], "manual")


SCALE_LENGTHS = (5, 10, 20)   # usual lengths of a checkerboard scale (cm); any other is doubtful


# --------------------------------------------------------------------------
# Site profiles and learned scales
# --------------------------------------------------------------------------

PROFILE_FILE = "gerbil_profile.json"    # next to the photos: the profile of the site (or --profile FILE)
LEARN_LEN = 2400                        # px: length of the image kept for a learned scale
LEARN_PHOTO = 3000                      # px: longest side of the photo when looking for a learned scale
LEARN_MIN_INLIERS = 8                   # matched points agreeing on one position of the scale
LEARN_MIN_CC = 0.80                     # correlation of the model with the photo after the fine alignment


def find_profile(path, given=None):
    """Profile of a photo: the file given (--profile), else PROFILE_FILE in the folder of the photo."""
    for f in ([given] if given else []) + [os.path.join(os.path.dirname(os.path.abspath(path)), PROFILE_FILE)]:
        if f and os.path.isfile(f):
            return f
    return None


_profiles = {}


def load_profile(file):
    """{"name", "background": "auto"|"light"|"dark", "learned_first": bool, "scales": [model...]}; models
    ready for matching (cached per process). A model: {"name", "cm", "width_cm", "px_cm", "image": PNG in
    base64}. learned_first: the learned scales are looked for before the usual detection (by default only
    when it fails or is doubtful: a learned 10 cm scale is also found inside a 20 cm one of the same make)."""
    if not file:
        return None
    key = (file, os.path.getmtime(file))
    if key in _profiles:
        return _profiles[key]
    with open(file, encoding="utf-8") as fh:
        pr = json.load(fh)
    sift = cv2.SIFT_create(nfeatures=8000)
    models = []
    for m in pr.get("scales") or []:
        try:
            img = np.asarray(Image.open(io.BytesIO(base64.b64decode(m["image"]))).convert("L"))
            kt, dt = sift.detectAndCompute(img, None)
            if dt is not None and len(kt) >= LEARN_MIN_INLIERS:
                models.append(dict(m, gray=img, kp=kt, desc=dt))
        except (KeyError, ValueError, OSError):
            continue
    pr["_models"] = models
    _profiles[key] = pr
    return pr


def learn_scale(rgb, entry, name=""):
    """Model of a scale from two points of known distance on a photo (entry as manual_scale): the band
    of the scale between the two points, straightened, kept LEARN_LEN pixels long, and its px/cm."""
    sc = manual_scale(rgb, entry)
    x0, y0, x1, y1 = sc.rect
    band = sc.crop[max(0, int(round(y0))):int(round(y1)) + 1, max(0, int(round(x0))):int(round(x1)) + 1]
    k = LEARN_LEN / band.shape[1]
    band = cv2.resize(band, None, fx=k, fy=k, interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    buf = io.BytesIO()
    Image.fromarray(band).save(buf, "PNG")
    return {"name": name or f"{entry['cm']:g} cm scale", "cm": entry["cm"], "width_cm": entry["width_cm"],
            "px_cm": band.shape[1] / entry["cm"], "image": base64.b64encode(buf.getvalue()).decode("ascii")}


def detect_learned_scale(rgb, models):
    """Looks for the learned scales on the photo. Coarse: points matched between each model and the
    photo (SIFT), one position, size and angle agreed by RANSAC; fine: the model correlated with the
    photo (ECC, affine) refines the length to better than 0.1 % when it is the same physical scale.
    The best model (correlation) gives two points at its ends: the scale is then built as a manual one."""
    if not models:
        return None
    H, W = rgb.shape[:2]
    f = min(1.0, LEARN_PHOTO / max(H, W))
    grey = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    small = cv2.resize(grey, None, fx=f, fy=f, interpolation=cv2.INTER_AREA) if f < 1 else grey
    kp, dp = cv2.SIFT_create(nfeatures=20000).detectAndCompute(small, None)
    if dp is None or len(kp) < LEARN_MIN_INLIERS:
        return None
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    best = None
    for m in models:
        pairs = [a for a, b in (x for x in matcher.knnMatch(m["desc"], dp, k=2) if len(x) == 2)
                 if a.distance < 0.8 * b.distance]
        if len(pairs) < LEARN_MIN_INLIERS:
            continue
        src = np.float32([m["kp"][a.queryIdx].pt for a in pairs])
        dst = np.float32([kp[a.trainIdx].pt for a in pairs])
        A, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=3)
        if A is None or inl is None or int(inl.sum()) < LEARN_MIN_INLIERS:
            continue
        A = A / f                                       # model -> photo (full size)
        h, w = m["gray"].shape
        length = w * math.hypot(A[0, 0], A[1, 0])
        if not 0.05 * max(H, W) <= length <= 1.5 * max(H, W):
            continue                                    # absurd size: wrong matches
        warped = cv2.warpAffine(grey, A, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP)
        E = np.eye(2, 3, dtype=np.float32)
        try:
            cc, E = cv2.findTransformECC(cv2.GaussianBlur(m["gray"], (5, 5), 0).astype(np.float32),
                                         cv2.GaussianBlur(warped, (5, 5), 0).astype(np.float32), E,
                                         cv2.MOTION_AFFINE,
                                         (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), None, 1)
        except cv2.error:
            continue
        if cc < LEARN_MIN_CC:
            continue
        T = (np.vstack([A, [0, 0, 1]]) @ np.vstack([E, [0, 0, 1]]))[:2]
        p1, p2 = apply_affine(T, [[0, h / 2], [w, h / 2]])
        if best is None or cc > best[0]:
            best = (cc, m, p1, p2, int(inl.sum()))
    if best is None:
        return None
    cc, m, p1, p2, n_in = best
    sc = manual_scale(rgb, {"p1": list(p1), "p2": list(p2), "cm": float(m["cm"]), "width_cm": float(m["width_cm"])})
    sc.kind = "learned"
    sc.note = f"learned scale '{m.get('name', '')}' (correlation {cc:.3f})"
    if cc < 0.9:
        sc.doubts = [f"learned scale matched loosely (correlation {cc:.2f}): another copy of the scale?"]
    return sc


def detect_scale(rgb, small, f, forced_cm=None, dark=False, min_ratio=2.5, ruler=True, comb=True):
    """comb: also try the second reading (analyze_comb) when the usual one finds nothing;
    "only": the second reading alone."""
    if dark:
        return _scale_on_dark(rgb, small, f, forced_cm)
    H, W = rgb.shape[:2]
    white = float(np.percentile(small.min(axis=2), 98))
    black, red = scale_ink_classes(small, white)
    ink = (black | red).astype(np.uint8)
    blob = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, disk(3))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(blob, connectivity=8)

    def evaluate(pts, reader=analyze_pattern):
        rect = cv2.minAreaRect(pts)
        theta, L, S = _rect_axis(rect)
        if S < 3 or L / S < min_ratio:
            return None
        crop, Mc = straighten(small, rect[0], theta, (int(L * 1.3) + 12, int(S * 4) + 12))
        res = reader(crop, _inside(small.shape, Mc, crop.shape))
        if res is None:
            return None
        return (res["n"] * 10 + L / max(W * f, 1) - res["irregularity"] * 5, rect, theta, L, S, res)

    blobs = []
    for i in range(1, n):                     # checkerboard: the squares touch at their corners
        x, y, w, h, a = stats[i]
        if a < 120:
            continue
        sub = (lab[y:y + h, x:x + w] == i) & (ink[y:y + h, x:x + w] > 0)
        ys, xs = np.nonzero(sub)
        if len(xs) < 60:
            continue
        blobs.append(np.column_stack([xs + x, ys + y]).astype(np.float32))
    candidates = [c for c in map(evaluate, blobs) if c] if comb != "only" else []
    if not candidates:                        # otherwise: single row of separate black squares
        singles = _single_row_groups(ink)
        candidates = [c for c in map(evaluate, singles) if c] if comb != "only" else []
        blobs += singles
    reader = analyze_pattern
    if not candidates:                        # no squares: graduated ruler?
        found = ruler and (detect_ruler(rgb) or detect_ruler(rgb, robust=True))
        if found:
            return found
        # second reading (digits inside the squares, any number of squares)
        candidates = [c for c in (evaluate(p, analyze_comb) for p in blobs) if c] if comb else []
        if not candidates:
            return Scale(note="scale not detected")
        reader = analyze_comb
    candidates.sort(key=lambda c: -c[0])
    _, rect, theta, L, S, _ = candidates[0]

    # Precise measurement at full resolution
    cx, cy = (rect[0][0] + 0.5) / f - 0.5, (rect[0][1] + 0.5) / f - 0.5
    Lf, Sf = L / f, S / f
    size = (int(Lf * 1.25) // 2 * 2 + 41, int(Sf * 4.5) // 2 * 2 + 41)   # odd: exact copy when straight
    res, by_digits = None, False
    for _ in range(2):
        if abs(theta) < math.radians(0.1):
            theta, cx, cy = 0.0, round(cx), round(cy)
        crop, M = straighten(rgb, (cx, cy), theta, size)
        res = reader(crop, _inside(rgb.shape, M, crop.shape))
        if res is None or not res["flip"]:
            break
        theta = theta + math.pi if theta <= 0 else theta - math.pi
    if res is None and reader is analyze_pattern:
        found = ruler and (detect_ruler(rgb) or detect_ruler(rgb, robust=True))
        if found or not comb:
            return found or Scale(note="scale spotted but unreadable at full resolution")
        res = analyze_comb(crop, _inside(rgb.shape, M, crop.shape))
        reader = analyze_comb
    if res is None:
        return Scale(note="scale spotted but unreadable at full resolution")
    if reader is analyze_comb:
        # the group found at low resolution may cover only part of the scale: the crop is
        # lengthened, centred on the squares read, as long as they reach its ends
        for _ in range(3):
            seg = res["seg"]
            if res["xs"] > 1.5 * seg and res["xe"] < size[0] - 1.5 * seg:
                break
            c2 = apply_affine(M, [[(res["xs"] + res["xe"]) / 2, (res["y0"] + res["y1"]) / 2]])[0]
            size2 = (int(res["xe"] - res["xs"] + 8 * seg) // 2 * 2 + 1, size[1])
            crop2, M2 = straighten(rgb, c2, theta, size2)
            r2 = analyze_comb(crop2, _inside(rgb.shape, M2, crop2.shape))
            if r2 is None or r2["n"] + r2["n_cut"] <= res["n"] + res["n_cut"]:
                break
            res, crop, M, size = r2, crop2, M2, size2
    # re-centre on the printed face (final crop well centred)
    face_center = apply_affine(M, [[(res["xs"] + res["xe"]) / 2, (res["y0"] + res["y1"]) / 2]])[0]
    cx, cy = face_center
    if theta == 0.0:
        cx, cy = round(cx), round(cy)
    crop, M = straighten(rgb, (cx, cy), theta, size, interp=cv2.INTER_CUBIC)
    res2 = reader(crop, _inside(rgb.shape, M, crop.shape))
    if res2 is not None and res2["n"] == res["n"] and res2["n_cut"] == res["n_cut"]:
        res = res2
        if reader is analyze_pattern and digits_upside_down(crop, res):
            # the red row put on top, the digits printed in the squares read upside down: the side
            # of the red row differs between makes of scale; the digits, when clear, decide
            theta3 = theta + math.pi if theta <= 0 else theta - math.pi
            crop3, M3 = straighten(rgb, (cx, cy), theta3, size, interp=cv2.INTER_CUBIC)
            res3 = reader(crop3, _inside(rgb.shape, M3, crop3.shape))
            if res3 is not None and res3["n"] == res["n"] and res3["n_cut"] == res["n_cut"]:
                theta, crop, M, res, by_digits = theta3, crop3, M3, res3, True

    length_px = res["xe"] - res["xs"]
    n_seen, n_cut = res["n"], res["n_cut"]   # complete squares (measured), squares cut by the photo edge
    doubts, note = [], ""
    if n_cut:
        note = f"scale cut by the photo edge: measured on its {n_seen} complete squares"
    if reader is analyze_comb:
        note = "squares read by their boundaries (second reading)" + (f"; {note}" if note else "")
    if by_digits:
        note = "scale turned by reading its digits" + (f"; {note}" if note else "")
    if forced_cm:
        length_cm = float(forced_cm)
        px_cm = length_px / (n_seen if n_cut else length_cm)
        note = f"forced scale length ({forced_cm:g} cm)" + (f"; {note}" if note else "")
    else:
        px_cm = length_px / n_seen               # one square = 1 cm
        length_cm = float(n_seen + n_cut)
        if res["single_row"] and not n_cut and n_seen not in (5, 10) and n_seen + 1 in (5, 10):
            # single row ending with a white square, invisible on the white card:
            # the measurement (px/cm) is already right, the square is added for the outline.
            side = _card_side(crop, res)
            if side:
                seg = res["seg"]
                xs = res["xs"] - (seg if side < 0 else 0)
                xe = res["xe"] + (seg if side > 0 else 0)
                res = dict(res, xs=xs, xe=xe, n=n_seen + 1, vx0=xs, vx1=xe,
                           boundaries=[xs + k * seg for k in range(n_seen + 2)])
                length_cm = float(n_seen + 1)
                note = "single-row scale: white end square inferred"
        if length_cm not in SCALE_LENGTHS:
            # doubtful length: strokes on a sherd (written number) may look like a few squares,
            # while the true scale is a ruler; a ruler of a usual length is then preferred
            found = ruler and (detect_ruler(rgb) or detect_ruler(rgb, robust=True))
            if found and found.length_cm in (5, 10) and not found.doubts:
                return found
            doubts.append(f"{n_seen + n_cut} squares detected (not 5, 10 or 20)")
    if res["irregularity"] > 0.15:
        doubts.append("irregular scale squares")

    # outline of the scale: flush with the printed face (without the edge or the card border);
    # a square cut by the photo edge is kept up to that edge
    rect_out = (res["vx0"], res["y0"] - 0.5, res["vx1"], res["y1"] + 0.5)
    x0, y0, x1, y1 = rect_out
    poly = apply_affine(M, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
    hf = res["hf"]
    margin_x, margin_y = 0.35 * res["seg"], 1.3 * hf
    zone = apply_affine(M, [[x0 - margin_x, y0 - margin_y], [x1 + margin_x, y0 - margin_y],
                            [x1 + margin_x, y1 + margin_y], [x0 - margin_x, y1 + margin_y]])
    return Scale(True, px_cm, res["n"] + n_cut, length_cm, theta, (cx, cy), size, M, crop,
                 rect_out, res, poly, zone, note, doubts, "checkerboard")



# --------------------------------------------------------------------------
# Graduated ruler (millimetre ticks on a light card)
# --------------------------------------------------------------------------

def _thin_ticks(grey):
    """Thin, elongated dark strokes (graduations): list of (cx, cy, theta, length)."""
    bh = cv2.morphologyEx(grey, cv2.MORPH_BLACKHAT, disk(4))
    B = (bh > 22).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(B, connectivity=8)
    ticks = []
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 5 or a > 2500 or max(w, h) < 5:
            continue
        ys, xs = np.nonzero(lab[y:y + h, x:x + w] == i)
        rect = cv2.minAreaRect(np.column_stack([xs + x, ys + y]).astype(np.float32))
        L, S = max(rect[1]), min(rect[1])
        if S > 6 or L < 2.5 * max(S, 1.0):
            continue
        theta, _, _ = _rect_axis(rect)
        ticks.append((rect[0][0], rect[0][1], theta, L))
    return ticks


def _tick_combs(ticks, long_ticks=False):
    """Groups parallel strokes lying side by side and evenly spaced (graduations).
    long_ticks: grid cell sized on the longest strokes instead of the 95th percentile of all of them
    (long graduations among many short strokes of a sherd surface: neighbours further apart)."""
    if len(ticks) < 15:
        return []
    T = np.array(ticks, np.float64)
    n = len(T)
    parent = list(range(n))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    cell = max(16.0, float(T[:, 3].max() if long_ticks else np.percentile(T[:, 3], 95)) * 1.7)   # covers 1.6 x the tick length
    grid = {}
    for i, (cx, cy, _, _) in enumerate(T):
        grid.setdefault((int(cx // cell), int(cy // cell)), []).append(i)
    for i, (cx, cy, th, L) in enumerate(T):
        v = np.array([math.cos(th), math.sin(th)])
        gx, gy = int(cx // cell), int(cy // cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    if j <= i:
                        continue
                    d = abs((T[j, 2] - th + math.pi / 2) % math.pi - math.pi / 2)
                    if d > math.radians(10):
                        continue
                    dd = T[j, :2] - (cx, cy)
                    le = max(L, T[j, 3])
                    if abs(dd @ v) > 0.6 * le or abs(dd[0] * v[1] - dd[1] * v[0]) > 1.6 * le:
                        continue
                    parent[root(i)] = root(j)
    groups = {}
    for i in range(n):
        groups.setdefault(root(i), []).append(i)

    def describe(G):
        th = float(np.median(G[:, 2]))
        u = np.array([-math.sin(th), math.cos(th)])          # axis of the ruler
        t = np.sort(G[:, :2] @ u)
        dt = np.diff(t)
        step = float(np.median(dt)) if len(dt) else 0.0
        reg = float(np.mean(np.abs(dt - step) < 0.25 * step)) if step > 0 else 0.0
        return {"members": G, "tick_theta": th, "step": step, "n": len(G), "reg": reg, "u": u, "t": t}

    combs = [describe(T[m]) for m in groups.values() if len(m) >= 8]
    combs = [p for p in combs if p["step"] > 2 and p["reg"] >= 0.6]
    # slightly bent ruler: two pieces aligned end to end, same step
    merged = True
    while merged:
        merged = False
        for a in range(len(combs)):
            for b in range(a + 1, len(combs)):
                p, q = combs[a], combs[b]
                if abs((p["tick_theta"] - q["tick_theta"] + math.pi / 2) % math.pi - math.pi / 2) > math.radians(4):
                    continue
                if abs(p["step"] - q["step"]) > 0.05 * p["step"]:
                    continue
                cp, cq = p["members"][:, :2].mean(0), q["members"][:, :2].mean(0)
                d = cq - cp
                if abs(d[0] * p["u"][1] - d[1] * p["u"][0]) > 0.8 * float(np.median(p["members"][:, 3])):
                    continue
                tq = q["members"][:, :2] @ p["u"]
                gap = max(tq.min() - p["t"].max(), p["t"].min() - tq.max())
                if gap > 8 * p["step"]:                # tolerated gap: holder lying on the ruler
                    continue
                combs[a] = describe(np.vstack([p["members"], q["members"]]))
                del combs[b]
                merged = True
                break
            if merged:
                break
    combs = [p for p in combs if p["n"] >= 15 and p["reg"] >= 0.6]
    combs.sort(key=lambda p: -p["n"] * p["reg"])
    return combs


def _peaks(profile, step):
    """Local maxima of a profile, at least 0.55 step apart, sub-pixel position."""
    p = cv2.GaussianBlur(profile.reshape(1, -1).astype(np.float32), (0, 0), max(0.6, step * 0.08)).ravel()
    threshold = float(np.percentile(p, 50) + 0.35 * (p.max() - np.percentile(p, 50)))
    cand = [i for i in range(1, len(p) - 1) if p[i] >= p[i - 1] and p[i] > p[i + 1] and p[i] > threshold]
    cand.sort(key=lambda i: -p[i])
    kept = []
    for i in cand:
        if all(abs(i - j) >= 0.55 * step for j in kept):
            kept.append(i)
    out = []
    for i in sorted(kept):
        a, b, c = p[i - 1], p[i], p[i + 1]
        den = a - 2 * b + c
        out.append(i + (0.5 * (a - c) / den if den != 0 else 0.0))
    return np.array(out)


def analyze_ruler(crop, step_estimate, robust=False):
    """Straightened crop: horizontal ruler, vertical graduations.
    Returns the measurement (millimetre step, centimetre ticks) or None.
    robust (second pass): the band of the ticks is measured against the 90th percentile of the row
    densities instead of their maximum, and short dips are crossed (thick ticks hanging from the card
    edge: the top rows, darker, and a light line under the edge, would make the band a few rows)."""
    hc, wc = crop.shape[:2]
    grey = crop.min(axis=2).astype(np.float32)
    bh = cv2.morphologyEx(grey, cv2.MORPH_BLACKHAT, disk(max(3, int(step_estimate * 0.25))))
    ink = bh > 22
    xa, xb = int(wc * 0.1), int(wc * 0.9)
    rows = ink[:, xa:xb].mean(axis=1)
    # band where all the ticks are present: maximum density, near the centre of the
    # crop (centred on the graduations found at low resolution)
    za, zb = int(hc * 0.36), int(hc * 0.64)
    dmax = float(rows[za:zb].max())
    if dmax < 0.04:
        return None
    yc = za + int(np.argmax(rows[za:zb]))
    ya = yb = yc
    if robust:
        t, max_gap = 0.6 * float(np.percentile(rows[za:zb], 90)), max(3, int(0.25 * step_estimate))
        for direction in (-1, 1):
            y, end, gap = yc + direction, yc, 0
            while 0 <= y < hc and gap <= max_gap:
                if rows[y] > t:
                    end, gap = y, 0
                else:
                    gap += 1
                y += direction
            ya, yb = (end, yb) if direction < 0 else (ya, end)
    else:
        while ya > 0 and rows[ya - 1] > 0.6 * dmax:
            ya -= 1
        while yb < hc - 1 and rows[yb + 1] > 0.6 * dmax:
            yb += 1
    h_tk = yb - ya + 1
    m = max(1, int(0.15 * h_tk))
    profile = (bh[ya + m:yb - m + 1] if yb - m >= ya + m else bh[ya:yb + 1]).mean(axis=0)
    xs = _peaks(profile, step_estimate)
    if len(xs) < 15:
        return None
    # fit x = a0 + step * k, robust to spurious peaks: common phase of all the peaks
    step = float(np.median(np.diff(xs)))
    ang = 2 * np.pi * xs / step
    a0 = float(np.angle(np.exp(1j * ang).mean()) / (2 * np.pi) * step)
    for _ in range(5):
        k = np.round((xs - a0) / step)
        res = xs - (a0 + step * k)
        ok = np.abs(res) < 0.2 * step
        if ok.sum() < 15:
            return None
        A = np.column_stack([np.ones(ok.sum()), k[ok]])
        (a0, step), *_ = np.linalg.lstsq(A, xs[ok], rcond=None)
    k = np.round((xs - a0) / step)
    res = xs - (a0 + step * k)
    ok = np.abs(res) < 0.2 * step
    xs, k, res = xs[ok], k[ok].astype(int), res[ok]
    if len(xs) < 15 or float(np.sqrt(np.mean(res ** 2))) > 0.08 * step:
        return None
    # ends of each tick, from the middle of the band (small gaps tolerated)
    y_lo, y_hi = max(0, ya - 2 * h_tk), min(hc, yb + 2 * h_tk)
    middle = (ya + yb) // 2 - y_lo
    max_gap = max(2, int(0.03 * h_tk))
    tops, bottoms = [], []
    for x in xs:
        c = ink[y_lo:y_hi, max(0, int(round(x)) - 2):int(round(x)) + 3].any(axis=1)
        ends = []
        for direction in (-1, 1):
            y, end, gap = middle, middle, 0
            while 0 <= y < len(c) and gap <= max_gap:
                if c[y]:
                    end, gap = y, 0
                else:
                    gap += 1
                y += direction
            ends.append(end + y_lo)
        tops.append(ends[0])
        bottoms.append(ends[1])
    tops, bottoms = np.array(tops, float), np.array(bottoms, float)
    lengths = bottoms - tops + 1
    # the ticks are aligned along the edge of the card: this edge must be at the top
    flip = float(np.std(tops)) > float(np.std(bottoms))
    phases = [(float(np.mean(lengths[(k - k.min()) % 10 == ph])) if np.any((k - k.min()) % 10 == ph) else 0, ph)
              for ph in range(10)]
    lmax, phase = max(phases)
    short = float(np.median(lengths))
    if lmax < 1.3 * short:
        return None
    k_cm = sorted(int(kk) for kk in k if (kk - k.min()) % 10 == phase)
    if len(k_cm) < 2:
        return None
    n_cm = (k_cm[-1] - k_cm[0]) // 10
    x_cm = [a0 + step * kk for kk in range(k_cm[0], k_cm[-1] + 1, 10)]
    return {
        "mm_step": float(step), "n_cm": n_cm, "x_cm": x_cm,
        "y_edge": float(np.median(tops)), "y_long": float(np.percentile(bottoms, 95)),
        "x0": a0 + step * k.min(), "x1": a0 + step * k.max(), "flip": flip,
        "irregularity": float(np.sqrt(np.mean(res ** 2)) / step), "n_ticks": len(xs),
    }


def ruler_outline(crop, res):
    """Edges of the ruler card (straightened crop, graduations at the top)."""
    hc, wc = crop.shape[:2]
    lab = to_lab(cv2.GaussianBlur(crop, (5, 5), 0))
    grey = crop.min(axis=2).astype(np.float32)
    step = res["mm_step"]
    ink = cv2.morphologyEx(grey, cv2.MORPH_BLACKHAT, disk(max(3, int(step * 0.25)))) > 22
    ye, yl = int(round(res["y_edge"])), int(round(res["y_long"]))
    h = max(4, yl - ye)
    xa, xb = max(0, int(res["x0"])), min(wc, int(res["x1"]) + 1)
    # card colour, measured between the graduations
    free = ~cv2.dilate(ink[ye:yl, xa:xb].astype(np.uint8), disk(2)).astype(bool)
    ref = np.median(lab[ye:yl, xa:xb][free].reshape(-1, 3), axis=0)
    d = np.linalg.norm(lab - ref, axis=2)
    rows = np.median(d[:, xa:xb], axis=1)
    threshold = max(3.0, 2.0 * float(np.median(rows[ye:yl])))
    top = ye
    for y in range(ye - 1, max(-1, int(ye - 0.3 * h)), -1):
        if rows[y] >= threshold:
            break
        top = y
    # digits under the graduations, then the card edge (a label often touches the ruler)
    dens = ink[:, xa:xb].mean(axis=1)
    lim = min(hc, ye + int(2.8 * h))
    y = yl + 1
    while y < lim and dens[y] < 0.01:
        y += 1
    start, end, gap = y, yl, 0
    while y < lim:
        if dens[y] >= 0.01:
            end, gap = y, 0
        else:
            gap += 1
            if gap > 0.15 * h:
                break
        y += 1
    if end > start:
        first, ceiling = end, min(hc - 1, end + int(0.6 * (end - start)))
    else:
        first, ceiling = yl, min(hc - 1, yl + h)
    bottom = first
    for y in range(first + 1, ceiling + 1):
        if rows[y] >= threshold:
            break
        bottom = y
    # a column is "card" if at least half of its pixels have the card colour;
    # the search starts just past the first and last ticks (ink) to reach the margins
    cols = (d[top:bottom + 1] < threshold).mean(axis=0)
    start_l, start_r = int(xa - 0.5 * step), int(xb + 0.5 * step)
    left, right = start_l + 1, start_r - 1
    for x in range(start_l, max(-1, int(xa - 12 * step)), -1):
        if cols[x] < 0.5:
            break
        left = x
    for x in range(start_r, min(wc, int(xb + 12 * step))):
        if cols[x] < 0.5:
            break
        right = x
    return (left - 0.5, top - 0.5, right + 0.5, bottom + 0.5)


def detect_ruler(rgb, robust=False):
    """Ruler graduated in millimetres: measures the millimetre step over the whole length.
    Returns a Scale, or None when no ruler is found. robust: second pass (thick, long ticks:
    _tick_combs(long_ticks) and analyze_ruler(robust)), used when the first one finds nothing."""
    H, W = rgb.shape[:2]
    r = min(1.0, 3000 / max(H, W))
    g = cv2.resize(rgb, (round(W * r), round(H * r)), interpolation=cv2.INTER_AREA).min(axis=2)
    for comb in _tick_combs(_thin_ticks(g), long_ticks=robust)[:3]:
        G = comb["members"]
        theta = (comb["tick_theta"] + math.pi) % math.pi - math.pi / 2     # axis = ticks + 90 degrees
        u = np.array([math.cos(theta), math.sin(theta)])
        t = G[:, :2] @ u
        center = (G[:, :2].mean(axis=0) + 0.5) / r - 0.5
        L = (t.max() - t.min()) / r
        Lt = G[:, 3].max() / r
        step = comb["step"] / r
        size = (int(L * 1.3 + 10 * step) // 2 * 2 + 1, int(Lt * 6) // 2 * 2 + 1)
        res = None
        for _ in range(2):
            if abs(theta) < math.radians(0.1):
                theta, center = 0.0, np.round(center)
            crop, M = straighten(rgb, center, theta, size)
            res = analyze_ruler(crop, step, robust)
            if res is None or not res["flip"]:
                break
            theta = theta + math.pi if theta <= 0 else theta - math.pi
        if res is None or res["flip"]:
            continue
        # the group of ticks found at low resolution may cover only part of the ruler (object or
        # shadow over it): the crop is lengthened, centred on the ticks read, as long as they reach
        # its ends (otherwise the first or last centimetre tick is missed: "3 cm read")
        for _ in range(3):
            if res["x0"] > 2 * step and res["x1"] < size[0] - 1 - 2 * step:
                break
            c3 = apply_affine(M, [[(res["x0"] + res["x1"]) / 2, (res["y_edge"] + res["y_long"]) / 2]])[0]
            size3 = (int(res["x1"] - res["x0"] + 24 * step) // 2 * 2 + 1, size[1])
            crop3, M3 = straighten(rgb, c3, theta, size3)
            r3 = analyze_ruler(crop3, step, robust)
            if r3 is None or r3["flip"] or r3["n_ticks"] <= res["n_ticks"]:
                break
            crop, M, res, center, size = crop3, M3, r3, c3, size3
        # final crop centred on the graduations, finer interpolation
        center2 = apply_affine(M, [[(res["x0"] + res["x1"]) / 2, (res["y_edge"] + res["y_long"]) / 2]])[0]
        if theta == 0.0:
            center2 = np.round(center2)
        crop2, M2 = straighten(rgb, center2, theta, size, interp=cv2.INTER_CUBIC)
        res2 = analyze_ruler(crop2, step, robust)
        if res2 is not None and not res2["flip"] and res2["n_cm"] == res["n_cm"]:
            crop, M, res, center = crop2, M2, res2, center2
        n_cm = res["n_cm"]
        doubts = []
        if n_cm not in (5, 10):
            doubts.append(f"ruler: {n_cm} cm read (neither 5 nor 10)")
        if res["irregularity"] > 0.03:
            doubts.append("irregular graduations (warped ruler?)")
        if res["n_ticks"] < 0.8 * (10 * n_cm + 1):
            doubts.append("graduations partly hidden")
        rect = ruler_outline(crop, res)
        x0, y0, x1, y1 = rect
        hr = y1 - y0
        poly = apply_affine(M, [[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
        zone = apply_affine(M, [[x0 - 0.2 * hr, y0 - 0.5 * hr], [x1 + 0.2 * hr, y0 - 0.5 * hr],
                                [x1 + 0.2 * hr, y1 + 0.3 * hr], [x0 - 0.2 * hr, y1 + 0.3 * hr]])
        pattern = {"y0": int(res["y_edge"]), "y1": int(res["y_long"]),
                   "hf": max(1, int(res["y_long"] - res["y_edge"])), "boundaries": res["x_cm"],
                   "seg": 10 * res["mm_step"], "irregularity": res["irregularity"]}
        return Scale(True, 10 * res["mm_step"], n_cm, float(n_cm), theta, tuple(center), size, M, crop,
                     rect, pattern, poly, zone, "", doubts, "ruler")
    return None


# --------------------------------------------------------------------------
# Ceramic outlining
# --------------------------------------------------------------------------

def poly_mask(shape, poly, aa=True):
    """Mask of a polygon (sub-pixel coordinates), anti-aliased or not."""
    m = np.zeros(shape, np.uint8)
    pts = np.round((np.asarray(poly) + 0.5) * 16 - 8).astype(np.int32)  # sub-pixel (shift = 4)
    cv2.fillPoly(m, [pts], 255, lineType=cv2.LINE_AA if aa else cv2.LINE_8, shift=4)
    return m


def discard_labels(keep, lab, stats, f, scale, dark=False):
    """Discards what is not ceramic (modifies `keep`):
      * what lies entirely on the other side of the scale from the main object
        (labels, notes placed under the ruler);
      * elements that are nowhere thicker than ~1.7 mm (felt-pen writing, printed lines
        of a bag, threads) or that are very long and narrow (lines);
      * small isolated elements, far from the object (thick letter on a label or a bag), except on a
        dark background (a dark letter does not stand out there: what does is a small sherd).
    Returns the outlines (image frame) of the small isolated elements discarded."""
    cand = [i for i in range(1, len(keep)) if keep[i]]
    if not cand:
        return []
    main = max(cand, key=lambda i: stats[i, cv2.CC_STAT_AREA])
    normal = scale.M[:, 1] / np.linalg.norm(scale.M[:, 1])
    x0, y0, x1, y1 = scale.rect
    center = apply_affine(scale.M, [[(x0 + x1) / 2, (y0 + y1) / 2]])[0]
    half = (y1 - y0) / 2
    cm = scale.px_cm * f                        # analysis pixels per cm
    r_min = 0.085 * cm                          # minimal inscribed radius (0.85 mm)

    def pixels(i):
        x, y, w, h, _ = stats[i]
        m = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        ys, xs = np.nonzero(m)
        return m, (np.column_stack([xs + x, ys + y]) + 0.5) / f - 0.5

    _, p = pixels(main)
    side = 1.0 if float(((p - center) @ normal).mean()) >= 0 else -1.0
    far_from_main = cv2.distanceTransform((lab != main).astype(np.uint8), cv2.DIST_L2, 5)
    a_main = stats[main, cv2.CC_STAT_AREA]
    isolated = []
    for i in cand:
        if i == main:
            continue
        m, p = pixels(i)
        if float((side * ((p - center) @ normal)).max()) < -half:
            keep[i] = False
            continue
        thickness = cv2.distanceTransform(cv2.copyMakeBorder(m, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0),
                                          cv2.DIST_L2, 5).max()
        L, S = sorted(cv2.minAreaRect(np.column_stack(np.nonzero(m)).astype(np.float32))[1], reverse=True)
        if thickness < r_min or (S < 0.5 * cm and L > 12 * max(S, 1.0)):
            keep[i] = False
            continue
        x, y, w, h, a = stats[i]
        if not dark and a < 0.08 * a_main and far_from_main[y:y + h, x:x + w][m > 0].min() > 0.8 * cm:
            keep[i] = False
            if a >= 0.04 * a_main:              # (smaller: discarded without reporting it)
                cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                isolated += [(c.reshape(-1, 2) + [x, y] + 0.5) / f - 0.5 for c in cs]
    return isolated


def translucent_supports(obj, d_small, dl_small, db_small, cm_small):
    """Plexiglass (translucent) supports: regions whose colour stays close to the background colour
    (distance < SUPPORT_T, whereas the ceramic differs clearly), at least 0.015 cm² in area,
    which stick out of the object (at least half of their perimeter on the background or an opening).
    A reflection of the background on a black gloss also has the background colour, but it runs
    along the ceramic, it is clearly darker and of the same hue; a support is as light as the
    background, or whiter than it (lavender background). Returns their mask (low resolution) or None."""
    weak = ((obj > 0) & (d_small < SUPPORT_T)).astype(np.uint8)
    weak = cv2.morphologyEx(weak, cv2.MORPH_OPEN, disk(max(1.0, 0.025 * cm_small)))
    n, lab, st, _ = cv2.connectedComponentsWithStats(weak, connectivity=8)
    sup = np.zeros(obj.shape, bool)
    for i in range(1, n):
        x, y, w, h, a = st[i]
        if a < 0.015 * cm_small ** 2:
            continue
        x0, y0 = max(0, x - 2), max(0, y - 2)
        c = lab[y0:y + h + 2, x0:x + w + 2] == i
        ring = (cv2.dilate(c.astype(np.uint8), disk(1)) > 0) & ~c
        on_background = int((ring & (obj[y0:y + h + 2, x0:x + w + 2] == 0)).sum())
        if on_background < 0.5 * max(1, int(ring.sum())):
            continue
        if (float(dl_small[y0:y + h + 2, x0:x + w + 2][c].mean()) < -8
                and float(db_small[y0:y + h + 2, x0:x + w + 2][c].mean()) < 6):
            continue
        sup[y0:y + h + 2, x0:x + w + 2] |= c
    if not sup.any():
        return None
    return (cv2.dilate(sup.astype(np.uint8), disk(2)) > 0) & (d_small < SUPPORT_T + 3)


CHART_CHROMA = 30.0   # chroma above which a pixel counts as a saturated (printed) colour
CHART_HUES = 5        # number of 30° hue sectors a colour chart covers at least
CHART_SECTOR = 0.1    # cm²: minimal area of a hue sector
SHADOW_T = 6.0        # colour distance to the darkened background under which a pixel is a shadow


def colour_chart(lab, m, sector_px):
    """Colour chart (Pantone colorimeter, ColorChecker...): its saturated pixels (chroma > CHART_CHROMA)
    cover at least CHART_HUES hue sectors of 30° (each one at least `sector_px` pixels, i.e. CHART_SECTOR),
    among the warm hues (red, orange, yellow, magenta), the greens and the blues alike.
    A ceramic, even glazed or painted, stays within a few neighbouring hues (2 sectors at most
    over 1763 photos, against 5 to 9 for the charts).
    Returns None (not a chart), "alone" (regular, convex outline: the chart only)
    or "attached" (irregular outline: the chart touches something else, e.g. the ceramic)."""
    a, b = lab[..., 1][m], lab[..., 2][m]
    sat = np.hypot(a, b) > CHART_CHROMA
    hue = (np.degrees(np.arctan2(b[sat], a[sat])) + 360.0) % 360.0
    sectors = np.bincount((hue // 30).astype(int) % 12, minlength=12) >= sector_px
    warm, green, blue = sectors[[0, 1, 2, 3, 11]].any(), sectors[4:7].any(), sectors[7:11].any()
    if sectors.sum() < CHART_HUES or not (warm and green and blue):
        return None
    cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    solidity = cv2.contourArea(c) / max(1.0, cv2.contourArea(cv2.convexHull(c)))
    return "alone" if solidity >= 0.95 else "attached"


def chart_disc(lab, m):
    """Circle of a round colour chart (Pantone colorimeter) inside the mask m, fitted on its printed
    inks whose hue is foreign to ceramics (pinks, yellows, greens, blues: chroma > 40, hue outside
    30-90°). Algebraic circle fit (x² + y² + Dx + Ey + F = 0, least squares), refitted on the points of
    the coloured ring; the inks must surround the centre (at least 20 of 36 sectors of 10°: under a warm
    light the yellow turns orange and joins the excluded hues) and the disc must be filled by the mask.
    Returns (cx, cy, r) in the frame of m, or None."""
    a, b = lab[..., 1], lab[..., 2]
    hue = (np.degrees(np.arctan2(b, a)) + 360.0) % 360.0
    ys, xs = np.nonzero(m & (np.hypot(a, b) > 40) & ((hue < 30) | (hue >= 90)))
    if len(xs) < 50:
        return None
    xs, ys = xs.astype(np.float64), ys.astype(np.float64)
    keep = np.ones(len(xs), bool)
    for _ in range(2):
        A = np.column_stack([xs[keep], ys[keep], np.ones(int(keep.sum()))])
        (D, E, _F), *_ = np.linalg.lstsq(A, -(xs[keep] ** 2 + ys[keep] ** 2), rcond=None)
        cx, cy = -D / 2, -E / 2
        rho = np.hypot(xs - cx, ys - cy)
        med = np.median(rho[keep])
        keep = np.abs(rho - med) < 0.35 * med
    ang = np.degrees(np.arctan2(ys[keep] - cy, xs[keep] - cx)) + 180.0
    if len(np.unique((ang // 10).astype(int) % 36)) < 20:
        return None
    r = float(np.percentile(rho[keep], 99.5)) + 1.5
    disc = cv2.circle(np.zeros(m.shape, np.uint8), (round(cx), round(cy)), round(r), 1, -1) > 0
    if disc.sum() == 0 or (m & disc).sum() < 0.6 * np.pi * r * r:
        return None
    return cx, cy, r


def remove_charts(obj, lab_small, bg_small, f, cm_small):
    """Removes the colour charts from the analysis mask `obj` (in place): a chart alone is discarded
    whole; a round chart touching the ceramic is cut out along its circle, together with its cast
    shadow (the chart is a thick disc). Shadow = pixels of the object having the colour of the
    background darkened (a* and b* of the background scaled by the lightness ratio, distance < SHADOW_T),
    within 1.6 radius, connected to the edge of the disc. Returns the outlines to show (image frame),
    the circles cut out (polygons, image frame, also applied at full resolution) and whether a chart
    touching the ceramic could not be separated."""
    charts, discs, attached = [], [], False
    hp, wp = obj.shape
    n, lab, stats, _ = cv2.connectedComponentsWithStats(obj, connectivity=8)
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if a < 0.25 * cm_small ** 2:
            continue
        m = lab[y:y + h, x:x + w] == i
        kind = colour_chart(lab_small[y:y + h, x:x + w], m, CHART_SECTOR * cm_small ** 2)
        if kind == "alone":
            obj[y:y + h, x:x + w][m] = 0
            cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            charts += [(c.reshape(-1, 2) + [x, y] + 0.5) / f - 0.5 for c in cs]
        elif kind == "attached":
            circle = chart_disc(lab_small[y:y + h, x:x + w], m)
            if circle is None:
                attached = True
                continue
            cx, cy, r = circle[0] + x, circle[1] + y, circle[2]
            t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
            pts = np.column_stack([cx + r * np.cos(t), cy + r * np.sin(t)])
            obj[poly_mask(obj.shape, pts, aa=False) > 0] = 0
            # its cast shadow, grown from the edge of the disc
            x0, y0 = max(0, int(cx - 1.7 * r)), max(0, int(cy - 1.7 * r))
            x1, y1 = min(wp, int(cx + 1.7 * r) + 1), min(hp, int(cy + 1.7 * r) + 1)
            lw, bw, o = lab_small[y0:y1, x0:x1], bg_small[y0:y1, x0:x1], obj[y0:y1, x0:x1]
            k = np.clip(lw[..., 0] / np.maximum(bw[..., 0], 1.0), 0.0, 1.2)
            dark_bg = ((np.hypot(lw[..., 1] - bw[..., 1] * k, lw[..., 2] - bw[..., 2] * k) < SHADOW_T)
                       & (lw[..., 0] < bw[..., 0] - 3))
            yy, xx = np.ogrid[y0:y1, x0:x1]
            rho = np.hypot(xx - cx, yy - cy)
            near = rho < 1.6 * r
            cand = (o > 0) & dark_bg & near
            _, ls = cv2.connectedComponents(cand.astype(np.uint8), connectivity=8)
            seeds = np.unique(ls[cand & (rho < r + 3)])
            o[np.isin(ls, seeds[seeds > 0])] = 0
            opened = cv2.morphologyEx(o, cv2.MORPH_OPEN, disk(2))  # remains of the shadow
            o[near] = opened[near]
            poly = (pts + 0.5) / f - 0.5
            charts.append(poly)
            discs.append(poly)
    return charts, discs, attached


LABEL_L, LABEL_C, LABEL_FILL = 78.0, 12.0, 0.85   # paper label: lightness, chroma, rectangle filling
LABEL_BLUE_C, LABEL_BLUE_L = 30.0, 72.0   # bluish white paper (optical brighteners): b* < 0, |a*| <= 5,
                                          # chroma up to LABEL_BLUE_C, from L* LABEL_BLUE_L (a turquoise glaze has a* << 0)
LABEL_BRIGHT_L, LABEL_BRIGHT_C = 90.0, 25.0   # very bright paper (pale yellow note): chroma up to this
LABEL_SQUARE_FILL, LABEL_SQUARE_L = 0.95, 70.0  # very rectangular and light: a label whatever its colour
PRINT_RECT, PRINT_C, PRINT_FILL, PRINT_INKS = 0.6, 15.0, 0.9, 0.3
# printed element (no scale measured): an outline mostly of long straight sides parallel or perpendicular
# to each other (at least PRINT_RECT of it) and the content of a print - uncoloured (median chroma up to
# PRINT_C), a near-perfect rectangle (PRINT_FILL), or black and white (PRINT_INKS of the pixels)
PRINT_RECT_LOW, PRINT_PALE_C, PRINT_LIGHT, PRINT_TWO_TONE = 0.4, 8.0, 0.6, 0.15
# ... or less straight but plainly a print: uncoloured (PRINT_PALE_C) and white (PRINT_LIGHT: label,
# ruler card) or black AND white (PRINT_TWO_TONE of each: checkerboard). On 191 open photos of finds
# (562 pieces), objects reach 0.74 of straight outline at most (a pin); a black blade (all dark, no
# white) stays an object
PRINT_STRAIGHT = 0.85
# ... or, whatever its colours (wooden or yellow ruler), straight (PRINT_STRAIGHT of the outline) and a
# full rectangle once closed (PRINT_STRAIGHT of it): a pin or an awl is straight but tapers
NEAR_SCALE_CM, NEAR_SCALE_D = 0.8, 18.0
# object in the scale zone, kept: reaches at least NEAR_SCALE_CM from the printed face and its mean
# background distance is at least NEAR_SCALE_D (on 1,764 reference photos, what the zone discards
# reaching that far is a translucent support, mean distance <= 13.2)


def label_card(lab_small, m, origin):
    """Paper label on a dark background: white (L* >= LABEL_L), uncoloured (chroma <= LABEL_C) - or
    bluish (paper with optical brighteners: b* < 0, chroma <= LABEL_BLUE_C), or very bright (L* >=
    LABEL_BRIGHT_L, chroma <= LABEL_BRIGHT_C: pale yellow note) - and rectangular (it fills at least
    LABEL_FILL of its minimum-area rectangle). A pale sherd is warm (b* > 0), darker, or not that
    rectangular. Very rectangular (LABEL_SQUARE_FILL) and light (L* >= LABEL_SQUARE_L): a label of
    any colour (sticky note) - a broken sherd never fills its rectangle that much."""
    ys, xs = np.nonzero(m)
    if len(xs) < 50:
        return False
    px = lab_small[ys + origin[1], xs + origin[0]]
    L, a, b = np.median(px, axis=0)
    c = math.hypot(a, b)
    w, h = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))[1]
    fill = len(xs) / max(w * h, 1.0)
    if fill >= LABEL_SQUARE_FILL and L >= LABEL_SQUARE_L:
        return True
    bluish = b < 0 and abs(a) <= 5 and c <= LABEL_BLUE_C and L >= LABEL_BLUE_L
    if not bluish and (L < LABEL_L or not (c <= LABEL_C or (L >= LABEL_BRIGHT_L and c <= LABEL_BRIGHT_C))):
        return False
    return fill >= LABEL_FILL


def straight_outline(m, origin, size):
    """Share of the outline of a piece (away from the photo border) made of long straight sides parallel
    or perpendicular to its main direction: near 1 for a scale bar, a ruler, a label or a chart (even
    L-shaped), lower for a broken sherd, a coin or a tool. The outline is closed first, so that the
    ticks of a ruler or the squares of a scale make a straight side. Returns (that share, how much of
    its minimum-area rectangle the closed outline fills)."""
    m = m.astype(np.uint8)
    root = math.sqrt(max(int(m.sum()), 1))
    r = max(2, round(0.012 * root))
    m = cv2.morphologyEx(cv2.copyMakeBorder(m, r, r, r, r, cv2.BORDER_CONSTANT, value=0), cv2.MORPH_CLOSE,
                         disk(r))[r:-r, r:-r]
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    root = math.sqrt(max(cv2.contourArea(c), 1.0))
    poly = cv2.approxPolyDP(c, max(1.5, 0.006 * root), True).reshape(-1, 2).astype(float) + origin
    _, (rw, rh), angle = cv2.minAreaRect(c)
    fill = root ** 2 / max(rw * rh, 1.0)
    W, H = size
    total = straight = 0.0
    for p, q in zip(poly, np.roll(poly, -1, axis=0)):
        if (max(p[0], q[0]) <= 1 or max(p[1], q[1]) <= 1 or min(p[0], q[0]) >= W - 2
                or min(p[1], q[1]) >= H - 2):
            continue                                    # along the photo border: says nothing
        length = float(np.hypot(*(q - p)))
        total += length
        dev = abs(((math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])) - angle) % 90 + 45) % 90 - 45)
        if length >= 0.08 * root and dev <= 4:
            straight += length
    return (straight / total if total else 0.0), fill


def printed_element(lab_small, m, origin, size):
    """A scale bar, ruler, label or colour card, recognised without measuring it (no scale found):
    straight-sided, and the content of a print (see PRINT_*)."""
    ys, xs = np.nonzero(m)
    if len(xs) < 50:
        return False
    rect, fill = straight_outline(m, origin, size)
    if rect < PRINT_RECT_LOW:
        return False
    if rect >= PRINT_STRAIGHT and fill >= PRINT_STRAIGHT:
        return True                                     # a straight, full rectangle: a ruler of any colour
    px = lab_small[ys + origin[1], xs + origin[0]]
    L, chroma = px[:, 0], np.hypot(px[:, 1], px[:, 2])
    c = float(np.median(chroma))
    dark = float(((L < 35) & (chroma < 12)).mean())
    light = float(((L > 80) & (chroma < 12)).mean())
    if rect >= PRINT_RECT:
        w, h = cv2.minAreaRect(np.column_stack([xs, ys]).astype(np.float32))[1]
        if c <= PRINT_C or len(xs) / max(w * h, 1.0) >= PRINT_FILL or dark + light >= PRINT_INKS:
            return True
    return c <= PRINT_PALE_C and (light >= PRINT_LIGHT or min(dark, light) >= PRINT_TWO_TONE)


def split_labels(obj, lab_small, f):
    """Dark background: a paper label touching an object by a narrow join (a corner, a point) forms
    one blob with it, neither label-coloured nor rectangular. Each blob that is not a label as a whole
    is cut at its narrow joins (opening, disc of 2 % of its size); a part that is a label is removed from
    the mask. Returns the mask and the outlines of the labels removed (photo coordinates)."""
    obj = obj.copy()
    outlines = []
    n, lab, stats, _ = cv2.connectedComponentsWithStats(obj, connectivity=8)
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if a < 400:
            continue
        comp = (lab[y:y + h, x:x + w] == i).astype(np.uint8)
        if label_card(lab_small, comp > 0, (x, y)):
            continue                                    # a label alone: handled by the usual sorting
        r = max(3, round(0.02 * math.sqrt(a)))
        parts = cv2.morphologyEx(comp, cv2.MORPH_OPEN, disk(r))
        k, pl, ps, _ = cv2.connectedComponentsWithStats(parts, connectivity=8)
        if k <= 2:
            continue                                    # no narrow join
        for j in range(1, k):
            if ps[j, cv2.CC_STAT_AREA] < max(200, 0.02 * a):   # (a label may be small beside a large sherd)
                continue
            region = (cv2.dilate((pl == j).astype(np.uint8), disk(r)) > 0) & (comp > 0)
            if label_card(lab_small, region, (x, y)):
                obj[y:y + h, x:x + w][region] = 0
                cs, _ = cv2.findContours(region.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                outlines += [(c.reshape(-1, 2) + [x, y] + 0.5) / f - 0.5 for c in cs]
    return obj, outlines


def edge_at_half_contrast(m, d, depth):
    """Dark background: the edge of a light object is a ramp several pixels wide (blur, shadow at its
    foot), and the threshold LOW_T keeps it almost down to the dark background (dark outline). In the
    outer band of the mask (depth pixels), the pixels whose distance to the background is under half
    that of the object nearby are removed, peeled from the outside only: the edge goes to the middle
    of the ramp. Dark areas inside the object (decoration) are not reached; where the object is
    hardly different from the background, LOW_T stays the threshold."""
    inner = cv2.erode(m.astype(np.uint8), disk(depth)) > 0
    if not inner.any():
        return m
    sig = 2.0 * depth                                   # contrast of the object near each edge pixel
    num = cv2.GaussianBlur(np.where(inner, d, 0).astype(np.float32), (0, 0), sig)
    den = cv2.GaussianBlur(inner.astype(np.float32), (0, 0), sig)
    ref = np.where(den > 0.05, num / np.maximum(den, 1e-3), 0)
    del num, den
    weak = m & ~inner & (d < np.maximum(LOW_T, 0.5 * ref))
    reach = (~m | weak).astype(np.uint8)                # outside + weak pixels, connected to the outside
    n, lab = cv2.connectedComponents(reach, connectivity=4)
    outside = np.zeros(n, bool)
    outside[np.unique(lab[~m])] = True
    outside[0] = False
    return m & ~(weak & outside[lab])


def outline_ceramic(photo, small, f, background, scale, ai=None):
    """The cut-out of the object(s): first mask on the reduced photo (colour distance to the
    background, hysteresis, holes filled), sorting of the pieces (scale zone, labels,
    supports, colour charts, isolated elements), refinement at full resolution, edge
    softened. Returns the alpha mask and what was discarded (see PSEUDOCODE §10)."""
    rgb = photo.rgb
    H, W = rgb.shape[:2]
    hp, wp = small.shape[:2]
    lab_small = to_lab(cv2.GaussianBlur(small, (3, 3), 0))
    d_small = distance(lab_small, background.small_model)
    obj = hysteresis(d_small, LOW_T, HIGH_T).astype(np.uint8)
    obj = cv2.morphologyEx(obj, cv2.MORPH_OPEN, disk(1))
    obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, disk(2))
    opening_area = 0.02 * (scale.px_cm * f) ** 2 if scale.found else 20      # at least 0.02 cm²
    obj = fill_holes(obj > 0, d_small, opening_area).astype(np.uint8)

    scale_zone = None
    if scale.found:
        scale_zone = poly_mask((hp, wp), (scale.zone + 0.5) * f - 0.5, aa=False) > 0
        scale_rect = poly_mask((hp, wp), (scale.poly + 0.5) * f - 0.5, aa=False)
        obj[cv2.dilate(scale_rect, disk(2)) > 0] = 0
    lab_dev = lab_small - background.small_model
    supports = (translucent_supports(obj, d_small, lab_dev[..., 0], lab_dev[..., 2], scale.px_cm * f)
                if scale.found else None)
    if supports is not None:
        obj[supports] = 0
    shadows = None if background.dark else cast_shadows(obj > 0, lab_small, background.small_model)
    if shadows is not None:
        obj[shadows] = 0
    charts, chart_discs, chart_attached = remove_charts(obj, lab_small, background.small_model, f,
                                                        (scale.px_cm if scale.found else 300 / 2.54) * f)

    labels = []                               # paper labels discarded (outlines, image frame)
    if background.dark:
        obj, labels = split_labels(obj, lab_small, f)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(obj, connectivity=8)
    if n <= 1:
        return None, "no object detected"
    areas = stats[1:, cv2.CC_STAT_AREA].astype(float)
    keep = np.zeros(n, bool)
    label_ids = []                            # components taken for paper labels
    printed, printed_ids = [], []             # scales, labels, cards recognised without a scale (outlines)
    face_dist, near_scale = None, 0           # distance to the printed face; objects kept near the scale
    px_cm_small = scale.px_cm * f if scale.found else None
    for i in range(1, n):
        x, y, w, h, a = stats[i]
        if scale_zone is not None:
            inside = scale_zone[y:y + h, x:x + w][lab[y:y + h, x:x + w] == i].mean()
            if inside > 0.5:
                # an object lying close to the scale is kept: it reaches far from the printed face
                # and stands out from the background (a support or the card edge stays near the face,
                # or keeps almost the background colour)
                if face_dist is None:
                    face_dist = cv2.distanceTransform((scale_rect == 0).astype(np.uint8), cv2.DIST_L2, 5)
                mi = lab[y:y + h, x:x + w] == i
                if (face_dist[y:y + h, x:x + w][mi].max() < NEAR_SCALE_CM * scale.px_cm * f
                        or d_small[y:y + h, x:x + w][mi].mean() < NEAR_SCALE_D):
                    continue
                near_scale += 1
        touches_border = x == 0 or y == 0 or x + w >= wp or y + h >= hp
        if touches_border and a < 0.3 * areas.max():
            continue
        if px_cm_small and a < 0.25 * px_cm_small ** 2:
            continue
        if not scale.found and printed_element(lab_small, lab[y:y + h, x:x + w] == i, (x, y), (wp, hp)):
            # no scale measured: the scale itself, a ruler, a label or a card is still not the object
            cs, _ = cv2.findContours((lab[y:y + h, x:x + w] == i).astype(np.uint8), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)
            printed += [(c.reshape(-1, 2) + [x, y] + 0.5) / f - 0.5 for c in cs]
            printed_ids.append(i)
            continue
        if background.dark and label_card(lab_small, lab[y:y + h, x:x + w] == i, (x, y)):
            # paper label on black velvet: white, uncoloured and rectangular
            cs, _ = cv2.findContours((lab[y:y + h, x:x + w] == i).astype(np.uint8), cv2.RETR_EXTERNAL,
                                     cv2.CHAIN_APPROX_SIMPLE)
            labels += [(c.reshape(-1, 2) + [x, y] + 0.5) / f - 0.5 for c in cs]
            label_ids.append(i)
            continue
        keep[i] = True
    label_kept = False
    if keep.sum() == 0 and printed_ids:
        # everything looks printed: rather a straight-sided object alone on the photo - kept, to check
        keep[printed_ids] = True
        printed, label_kept = [], True
    if keep.sum() == 0 and label_ids:
        # everything looks like a label: rather a small pale sherd alone on the photo - kept, to check
        keep[label_ids] = True
        labels, label_kept = [], True
    if keep.sum() == 0:
        return None, "no ceramic kept"
    isolated = discard_labels(keep, lab, stats, f, scale, background.dark) if scale.found else []
    a_max = max(stats[i, cv2.CC_STAT_AREA] for i in range(1, n) if keep[i])
    for i in range(1, n):
        if keep[i] and stats[i, cv2.CC_STAT_AREA] < 0.04 * a_max:
            keep[i] = False
    obj = keep[lab]
    n_pieces = int(keep.sum())
    # removed supports that touched the kept ceramic (for the preview and the report)
    support_outlines = []
    if supports is not None:
        near = cv2.dilate(obj.astype(np.uint8), disk(3)) > 0
        ns, ls = cv2.connectedComponents(supports.astype(np.uint8), connectivity=8)
        for i in range(1, ns):
            z = ls == i
            if (z & near).any():
                cs, _ = cv2.findContours(z.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                support_outlines += [(c.reshape(-1, 2) + 0.5) / f - 0.5 for c in cs]
    shadow_outlines = []                      # cast shadows removed along the kept objects (idem)
    if shadows is not None:
        near = cv2.dilate(obj.astype(np.uint8), disk(3)) > 0
        ns, ls = cv2.connectedComponents(shadows.astype(np.uint8), connectivity=8)
        for i in range(1, ns):
            z = ls == i
            if (z & near).any():
                cs, _ = cv2.findContours(z.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                shadow_outlines += [(c.reshape(-1, 2) + 0.5) / f - 0.5 for c in cs]

    # Refinement at full resolution over the useful area
    ys, xs = np.nonzero(obj)
    margin = int(0.03 * max(H, W)) + 8
    X0 = max(0, int(xs.min() / f) - margin)
    Y0 = max(0, int(ys.min() / f) - margin)
    X1 = min(W, int((xs.max() + 1) / f) + margin)
    Y1 = min(H, int((ys.max() + 1) / f) + margin)
    roi = rgb[Y0:Y1, X0:X1]
    h, w = roi.shape[:2]
    lab_roi = to_lab(cv2.GaussianBlur(roi, (3, 3), 0))
    model = background.evaluate(X0, Y0, w, h, W, H)
    d = distance(lab_roi, model)
    shade = None
    if shadows is not None:                   # pixels of the colour of a shadow on this background
        kr = (lab_roi[..., 0] + 1) / (model[..., 0] + 1)
        shade = ((kr > SHADOW_K[0]) & (kr < SHADOW_K[1])
                 & (np.hypot(lab_roi[..., 1] - kr * model[..., 1], lab_roi[..., 2] - kr * model[..., 2])
                    < SHADOW_DEEP_CD))
        del kr
    del lab_roi, model
    gx0, gy0 = (X0 + 0.5) * f - 0.5, (Y0 + 0.5) * f - 0.5
    Mup = np.array([[f, 0, gx0], [0, f, gy0]], np.float64)
    big = cv2.warpAffine(obj.astype(np.float32), Mup, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP) > 0.5
    r = int(math.ceil(1.5 / f)) + 2
    sure = (cv2.erode(big.astype(np.uint8), disk(r)) > 0) & (d >= 0.4 * LOW_T)   # background seen between two parts is never "sure"
    allowed = cv2.dilate(big.astype(np.uint8), disk(r)) > 0
    del big
    m = ((d > LOW_T) & allowed) | sure
    nlab, labm = cv2.connectedComponents(m.astype(np.uint8), connectivity=8)
    linked = np.zeros(nlab, bool)
    linked[np.unique(labm[sure])] = True
    linked[0] = False
    m = linked[labm]
    if scale.found:
        m[poly_mask((H, W), scale.poly)[Y0:Y1, X0:X1] > 0] = False
    chart_cut = np.zeros((h, w), bool)
    for poly in chart_discs:
        chart_cut |= poly_mask((h, w), poly - [X0, Y0]) > 0
    m &= ~chart_cut
    sup_big = None
    if supports is not None:
        sup_big = cv2.warpAffine(cv2.dilate(supports.astype(np.uint8), disk(2)).astype(np.float32), Mup, (w, h),
                                 flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP) > 0.5
        m &= ~(sup_big & (d < SUPPORT_T + 3))
    if shade is not None:                     # the shadows removed stay out at full resolution
        sh_big = cv2.warpAffine(cv2.dilate(shadows.astype(np.uint8), disk(1)).astype(np.float32), Mup, (w, h),
                                flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP) > 0.5
        m &= ~(sh_big & shade)
        del sh_big, shade
    hole_area =0.02 * scale.px_cm ** 2 if scale.found else 300
    m = fill_holes(m, d, hole_area, keep_open=sup_big)
    m &= ~chart_cut                                                 # (a ring of shadow may enclose it)
    if background.dark:
        m = edge_at_half_contrast(m, d, max(8, round(max(H, W) / 600)))
    ai_removed, ai_area = [], 0.0
    if ai is not None:
        # AI second opinion, subtraction only: background kept by the colour rule because it is
        # enclosed or shadowed (perforation, gap between two sherds, blurred halo), that the network
        # sees as background, whose colour stays close to the background (d < AI_D_MAX), 3 px away
        # from the edges it draws, at least AI_MIN_AREA. The network never adds anything.
        sx, sy = AI_SIZE / W, AI_SIZE / H
        Mai = np.array([[sx, 0, (X0 + 0.5) * sx - 0.5], [0, sy, (Y0 + 0.5) * sy - 0.5]], np.float64)
        fg = cv2.warpAffine(ai, Mai, (w, h), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP) > 127
        rem = m & ~(cv2.dilate(fg.astype(np.uint8), disk(3)) > 0) & (d < AI_D_MAX)
        rem = cv2.morphologyEx(rem.astype(np.uint8), cv2.MORPH_OPEN, disk(3))
        px_cm = scale.px_cm if scale.found else 300 / 2.54
        nr, lr, sr, _ = cv2.connectedComponentsWithStats(rem, connectivity=8)
        for i in range(1, nr):
            x, y, wr, hr, a = sr[i]
            if a < AI_MIN_AREA * px_cm ** 2:
                continue
            z = lr[y:y + hr, x:x + wr] == i
            m[y:y + hr, x:x + wr][z] = False
            ai_area += a / px_cm ** 2
            cs, _ = cv2.findContours(z.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            ai_removed += [c.reshape(-1, 2).astype(np.float64) + [X0 + x, Y0 + y] for c in cs]
        del fg, rem, lr
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, disk(2))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, disk(2))
    m = cv2.medianBlur(m * 255, 5)
    m = cv2.erode(m, disk(1))                                      # slight "contract": no halo
    alpha = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.8)
    alpha = np.clip(alpha + 0.5, 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(alpha > 0)
    if len(xs) == 0:
        return None, "empty outline"
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    return {
        "alpha": alpha[by0:by1, bx0:bx1],
        "box": (X0 + bx0, Y0 + by0, X0 + bx1, Y0 + by1),
        "pieces": n_pieces,
        "isolated": isolated,                   # small isolated elements discarded (outlines, image frame)
        "labels": labels,                       # paper labels discarded on a dark background (idem)
        "printed": printed,                     # scales, labels, cards discarded without a scale (idem)
        "dark": bool(background.dark),          # dark background: the colours of the edge are cleaned
        "label_kept": label_kept,               # the only object looked like a label: kept, to check
        "near_scale": near_scale,               # objects kept although lying in the scale zone
        "supports": support_outlines,           # translucent supports removed (outlines, image frame)
        "shadows": shadow_outlines,             # cast shadows removed (idem)
        "charts": charts,                       # colour charts discarded (outlines, image frame)
        "chart_attached": chart_attached,       # a colour chart seems to touch the kept ceramic
        "ai_removed": ai_removed,               # background removed on the AI's advice (outlines, image frame)
        "ai_area": ai_area,                     # ... and its area (cm²)
        "removed": [],
    }, ""


def find_putty(rgb, cer, px_cm):
    """Looks for a visible support (mounting putty) attached to the ceramic.

    A part of the outline is a candidate only if:
      * it separates from the rest at two concavities of the outline (straight cut between them);
      * it is clearly smoother than the ceramic (texture < 50 %);
      * its colour differs (Delta E > 6), it is less saturated (chroma < 80 %) and lighter.
    The pixels stay in the PSD layer: only the layer mask changes.
    Returns (cer without the putty, removed polygons in image coordinates, area in cm²)."""
    x0, y0, x1, y1 = cer["box"]
    alpha = cer["alpha"]
    hb, wb = alpha.shape
    s = min(1.0, 80.0 / px_cm)               # works at about 80 px/cm
    pw = px_cm * s
    pad = 4
    hw, ww = max(1, round(hb * s)), max(1, round(wb * s))
    r = cv2.resize(rgb[y0:y1, x0:x1], (ww, hw), interpolation=cv2.INTER_AREA)
    m = (cv2.resize(alpha, (ww, hw), interpolation=cv2.INTER_AREA) > 127).astype(np.uint8)
    r = cv2.copyMakeBorder(r, pad, pad, pad, pad, cv2.BORDER_REPLICATE)
    m = cv2.copyMakeBorder(m, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    g = cv2.cvtColor(r, cv2.COLOR_RGB2GRAY).astype(np.float32)
    hp = g - cv2.GaussianBlur(g, (0, 0), 1.2)
    tex = np.sqrt(np.maximum(cv2.blur(hp * hp, (7, 7)), 0))   # surface grain (shading excluded; >= 0: rounding)
    lab = to_lab(cv2.GaussianBlur(r, (5, 5), 0))

    parts = []
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for c in contours:
        if cv2.contourArea(c) < 0.5 * pw * pw:
            continue
        c2 = cv2.approxPolyDP(c, 1.0, True)
        pts = c2.reshape(-1, 2)
        if len(pts) < 5:
            continue
        try:
            defects = cv2.convexityDefects(c2, cv2.convexHull(c2, returnPoints=False))
        except cv2.error:
            continue
        if defects is None:
            continue
        hollows = [int(fi) for (_, _, fi, di) in defects.reshape(-1, 4) if di / 256.0 > 0.08 * pw]
        best = None
        for i in range(len(hollows)):
            for j in range(i + 1, len(hollows)):
                a, b = sorted((hollows[i], hollows[j]))
                p1, p2 = pts[a:b + 1], np.vstack([pts[b:], pts[:a + 1]])
                A1, A2 = abs(cv2.contourArea(p1)), abs(cv2.contourArea(p2))
                part, As, Ar = (p1, A1, A2) if A1 < A2 else (p2, A2, A1)
                if As < 0.2 * pw * pw or As > 0.45 * (As + Ar):
                    continue
                if best is not None and As <= best[1]:
                    continue
                ms = np.zeros_like(m)
                cv2.fillPoly(ms, [part.reshape(-1, 1, 2).astype(np.int32)], 1)
                ms = (ms > 0) & (m > 0)
                mr = (m > 0) & ~ms
                mse = cv2.erode(ms.astype(np.uint8), disk(3)) > 0
                mre = cv2.erode(mr.astype(np.uint8), disk(3)) > 0
                if mse.sum() < 20 or mre.sum() < 20:
                    continue
                ts, tr = float(np.median(tex[mse])), float(np.median(tex[mre]))
                ls, lr = lab[mse].mean(0), lab[mre].mean(0)
                dE = float(np.linalg.norm(ls - lr))
                Cs, Cr = float(np.hypot(ls[1], ls[2])), float(np.hypot(lr[1], lr[2]))
                if ts < 0.5 * tr and dE > 6 and Cs < 0.8 * Cr and ls[0] > max(45.0, lr[0]):
                    best = (part, As)
        if best is not None:
            parts.append(best)
    if not parts:
        return cer, [], 0.0

    rm = np.zeros((hb, wb), np.uint8)
    polys = []
    for part, _ in parts:
        pf = (part.astype(np.float64) - pad + 0.5) / s - 0.5
        rm = np.maximum(rm, poly_mask((hb, wb), pf))
        polys.append(pf + [x0, y0])
    a = (alpha.astype(np.float32) * (1 - rm.astype(np.float32) / 255) + 0.5).astype(np.uint8)
    # around the cut: remove the remaining filaments (fibres, putty smears)
    zone = cv2.dilate((rm > 0).astype(np.uint8), disk(0.15 * px_cm)) > 0
    opened = cv2.morphologyEx((a > 127).astype(np.uint8), cv2.MORPH_OPEN, disk(0.04 * px_cm))
    opened = cv2.dilate(opened, disk(2)) > 0
    a[zone & ~opened] = 0
    # remove the small pieces isolated by the cut
    n, lab_cc, st, _ = cv2.connectedComponentsWithStats((a > 127).astype(np.uint8), connectivity=8)
    if n > 1:
        areas = st[1:, cv2.CC_STAT_AREA]
        keep = np.zeros(n, bool)
        keep[1:] = areas >= 0.04 * areas.max()
        a[cv2.dilate(keep[lab_cc].astype(np.uint8), disk(2)) == 0] = 0
    ys, xs = np.nonzero(a > 0)
    if len(xs) == 0:
        return cer, [], 0.0
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    cer = dict(cer, alpha=a[by0:by1, bx0:bx1], box=(x0 + bx0, y0 + by0, x0 + bx1, y0 + by1), removed=polys)
    return cer, polys, sum(As for _, As in parts) / (pw * pw)


# --------------------------------------------------------------------------
# AI second opinion (optional, --ai): neural segmentation of the object
# --------------------------------------------------------------------------

# Same networks and same pre-processing as the rembg library, run directly with onnxruntime.
# name: (file, download address, MD5, mean, standard deviation, sigmoid on the output)
AI_MODELS = {
    "isnet": ("isnet-general-use",
              "https://github.com/danielgatis/rembg/releases/download/v0.0.0/isnet-general-use.onnx",
              "fc16ebd8b0c10d971d3513d564d01e29", (0.5, 0.5, 0.5), (1.0, 1.0, 1.0), False),
    "birefnet": ("birefnet-general",
                 "https://github.com/danielgatis/rembg/releases/download/v0.0.0/BiRefNet-general-epoch_244.onnx",
                 "7a35a0141cbbc80de11d9c9a28f52697", (0.485, 0.456, 0.406), (0.229, 0.224, 0.225), True),
}
AI_DIR = os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False)   # .exe version:
                      else os.path.dirname(os.path.abspath(__file__)), "models")         # next to the .exe
AI_SIZE = 1024        # input size of both networks
AI_D_MAX = 12.0       # the AI only removes what stays close to the background colour
AI_MIN_AREA = 0.02    # cm²: smaller disagreements are ignored (edges)
_ai_session = None    # one session per process


def ai_model_path(model):
    """Model file, in the 'models' folder next to the script; downloaded the first time
    (checked with its MD5 sum)."""
    file, url, md5 = AI_MODELS[model][:3]
    path = os.path.join(AI_DIR, file + ".onnx")
    if os.path.exists(path):
        return path
    os.makedirs(AI_DIR, exist_ok=True)
    print(f"Downloading the AI model {file} (once) from {url}", flush=True)
    tmp, h, done = path + ".part", hashlib.md5(), 0
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as out:
        total = int(r.headers.get("Content-Length") or 0)
        while chunk := r.read(1 << 20):
            out.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {done / total:6.1%} of {total / 1e6:.0f} MB", end="", flush=True)
    print()
    if h.hexdigest() != md5:
        os.remove(tmp)
        raise RuntimeError(f"corrupted download of {file} (MD5 mismatch), try again")
    os.replace(tmp, path)
    return path


def ai_providers(device, model):
    """Graphics card when onnxruntime offers one (CUDA, or DirectML on Windows), else the processor.
    BiRefNet (1 GB) is too large for DirectML on an 8 GB card: it fails, or crawls in shared memory;
    it only uses CUDA."""
    import onnxruntime as ort
    gpu = [p for p in ("CUDAExecutionProvider", "DmlExecutionProvider") if p in ort.get_available_providers()]
    if model == "birefnet":
        gpu = [p for p in gpu if p != "DmlExecutionProvider"]
    return ["CPUExecutionProvider"] if device == "cpu" or not gpu else [gpu[0], "CPUExecutionProvider"]


def _ai_open(model, providers, jobs):
    """Opens an ONNX model with onnxruntime (graphics card or processor), threads shared by the
    photos processed in parallel."""
    import onnxruntime as ort
    so = ort.SessionOptions()
    so.log_severity_level = 3
    so.intra_op_num_threads = max(1, (os.cpu_count() or 2) // max(1, jobs))   # processor shared by the workers
    if "DmlExecutionProvider" in providers:
        so.enable_mem_pattern = False                                         # required by DirectML
        so.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    return ort.InferenceSession(ai_model_path(model), sess_options=so, providers=providers)


def ai_mask(rgb, opts):
    """Object probability (0-255, AI_SIZE x AI_SIZE) for the whole photo, as in rembg: photo resized
    to 1024 x 1024 (Lanczos), values divided by their maximum, centred and scaled (mean, standard
    deviation of the network), network, sigmoid (BiRefNet), stretched to 0-1. On a failure of the
    graphics card (lack of memory), the processor takes over."""
    global _ai_session
    _, _, _, mean, std, sigmoid = AI_MODELS[opts.ai_model]
    if _ai_session is None:
        _ai_session = _ai_open(opts.ai_model, ai_providers(opts.ai_device, opts.ai_model), opts.jobs)
    im = np.asarray(Image.fromarray(rgb).resize((AI_SIZE, AI_SIZE), Image.Resampling.LANCZOS), np.float64)
    x = (im / max(float(im.max()), 1e-6) - np.array(mean)) / np.array(std)
    feed = {_ai_session.get_inputs()[0].name: x.transpose(2, 0, 1)[None].astype(np.float32)}
    try:
        out = _ai_session.run(None, feed)[0][0, 0]
    except Exception:
        if _ai_session.get_providers()[0] == "CPUExecutionProvider":
            raise
        _ai_session = _ai_open(opts.ai_model, ["CPUExecutionProvider"], opts.jobs)
        out = _ai_session.run(None, feed)[0][0, 0]
    if sigmoid:
        out = 1.0 / (1.0 + np.exp(-out))
    out = (out - out.min()) / max(float(out.max() - out.min()), 1e-12)
    return (out * 255).astype(np.uint8)


# --------------------------------------------------------------------------
# One-click cut-out (review window): Segment Anything, MobileSAM version
# --------------------------------------------------------------------------

# MobileSAM (MIT licence), ONNX export by Acly: image encoder + single-mask decoder; downloaded once
CLICK_MODELS = {
    "encoder": ("mobile_sam_image_encoder.onnx",
                "https://huggingface.co/Acly/MobileSAM/resolve/main/mobile_sam_image_encoder.onnx",
                "580f5fb648ea1062c0aabc26217aed56921985f03f0cbbd852bba81d760cc749"),
    "decoder": ("sam_mask_decoder_single.onnx",
                "https://huggingface.co/Acly/MobileSAM/resolve/main/sam_mask_decoder_single.onnx",
                "93915fc7c993ab9d59ab8c9ccd3bce37f7509c81ab4150a74abd4d2abbd8570d"),
}
CLICK_SIZE = 1024     # the encoder sees the photo reduced to this longest side


def click_model_path(part, progress=None):
    """File of the one-click model, in the 'models' folder; downloaded the first time (SHA-256 checked)."""
    file, url, sha = CLICK_MODELS[part]
    path = os.path.join(AI_DIR, file)
    if os.path.exists(path):
        return path
    os.makedirs(AI_DIR, exist_ok=True)
    tmp, h, done = path + ".part", hashlib.sha256(), 0
    with urllib.request.urlopen(url) as r, open(tmp, "wb") as out:
        total = int(r.headers.get("Content-Length") or 0)
        while chunk := r.read(1 << 20):
            out.write(chunk)
            h.update(chunk)
            done += len(chunk)
            if progress and total:
                progress(done / total)
    if h.hexdigest() != sha:
        os.remove(tmp)
        raise RuntimeError(f"corrupted download of {file}, try again")
    os.replace(tmp, path)
    return path


class ClickCutout:
    """Cut-out of the object the archaeologist clicks on. Segment Anything is told WHICH object to cut
    out (a click on it; a click with "remove" on what must not be kept): it no longer has to guess what
    is a sherd and what is a label, a shadow or the background, hence a more reliable result than the
    automatic way on difficult photos. Its own edge is coarse (it sees the photo at 1024 px): where the
    computed cut-out agrees with it, the edge of the computed cut-out is kept."""

    def __init__(self, progress=None):
        """Loads the two parts of MobileSAM (image encoder, mask decoder); downloads them
        the first time."""
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.log_severity_level = 3
        prov = ["CPUExecutionProvider"]
        self.encoder = ort.InferenceSession(click_model_path("encoder", progress), sess_options=so, providers=prov)
        self.decoder = ort.InferenceSession(click_model_path("decoder", progress), sess_options=so, providers=prov)
        self.embedding, self.size, self.k = None, None, 1.0

    def set_image(self, rgb):
        """Encodes the photo once (about a second); the clicks are then instant."""
        H, W = rgb.shape[:2]
        k = CLICK_SIZE / max(H, W)
        small = cv2.resize(rgb, (round(W * k), round(H * k)), interpolation=cv2.INTER_AREA)
        self.embedding = self.encoder.run(None, {"input_image": small.astype(np.float32)})[0]
        self.size, self.k = (H, W), k

    def mask(self, points, out_size=None):
        """Mask (bool) of the object for points [(x, y, keep)] in photo pixels; out_size (h, w) of the
        mask, by default the photo's."""
        h, w = out_size or self.size
        coords = [[x * self.k, y * self.k] for x, y, _ in points] + [[0.0, 0.0]]
        labels = [1.0 if keep else 0.0 for _, _, keep in points] + [-1.0]      # -1: no box
        out = self.decoder.run(None, {
            "image_embeddings": self.embedding,
            "point_coords": np.array([coords], np.float32),
            "point_labels": np.array([labels], np.float32),
            "mask_input": np.zeros((1, 1, 256, 256), np.float32),
            "has_mask_input": np.zeros(1, np.float32),
            "orig_im_size": np.array(self.size, np.float32)})
        m = out[0][0, 0] > 0
        if (h, w) != self.size:
            m = cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
        return m


def click_refine(sam, computed, band):
    """Edge of the clicked object: the computed cut-out where it agrees with Segment Anything (within
    `band` pixels of its edge), Segment Anything elsewhere (object missed by the computed cut-out)."""
    k = disk(max(1, band))
    inner = cv2.erode(sam.astype(np.uint8), k) > 0
    outer = cv2.dilate(sam.astype(np.uint8), k) > 0
    agree = computed & outer
    n, lab = cv2.connectedComponents(agree.astype(np.uint8), connectivity=8)
    if n > 1:                                   # the computed pieces that the click selects
        hits = np.bincount(lab[inner], minlength=n)
        sizes = np.bincount(lab.ravel(), minlength=n)
        good = (hits > 0.5 * sizes) & (np.arange(n) > 0)
        agree = good[lab]
    covered = agree.sum() / max(1, sam.sum())
    return (agree | inner) if covered > 0.8 else sam



# --------------------------------------------------------------------------
# Layers and compositing
# --------------------------------------------------------------------------

@dataclass
class Layer:
    """One layer of the output files: name, position on the canvas, pixels, mask (or None),
    visible or hidden."""
    name: str
    x: int
    y: int
    rgb: np.ndarray               # h x w x 3
    mask: np.ndarray = None       # h x w (layer mask), None = no mask
    visible: bool = True


def extract(rgb, x0, y0, x1, y1):
    """Crop, filled with white where the area goes beyond the image."""
    H, W = rgb.shape[:2]
    out = np.full((y1 - y0, x1 - x0, 3), 255, np.uint8)
    sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if sx1 > sx0 and sy1 > sy0:
        out[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = rgb[sy0:sy1, sx0:sx1]
    return out


def composite(layers, W, H):
    """Merges the visible layers (non-premultiplied rgb + alpha) over a transparent background."""
    acc = np.zeros((H, W, 3), np.float32)
    a_acc = np.zeros((H, W), np.float32)
    for c in layers:
        if not c.visible:
            continue
        h, w = c.rgb.shape[:2]
        x0, y0, x1, y1 = max(0, c.x), max(0, c.y), min(W, c.x + w), min(H, c.y + h)
        if x1 <= x0 or y1 <= y0:
            continue
        src = c.rgb[y0 - c.y:y1 - c.y, x0 - c.x:x1 - c.x].astype(np.float32)
        a = (c.mask[y0 - c.y:y1 - c.y, x0 - c.x:x1 - c.x].astype(np.float32) / 255.0
             if c.mask is not None else np.ones((y1 - y0, x1 - x0), np.float32))
        ad = a_acc[y0:y1, x0:x1]
        acc[y0:y1, x0:x1] = src * a[..., None] + acc[y0:y1, x0:x1] * (1 - a[..., None])
        a_acc[y0:y1, x0:x1] = a + ad * (1 - a)
    rgb = np.where(a_acc[..., None] > 0, acc / np.maximum(a_acc[..., None], 1e-6), 255)
    return np.clip(rgb + 0.5, 0, 255).astype(np.uint8), np.clip(a_acc * 255 + 0.5, 0, 255).astype(np.uint8)


EDGE_BAND = 3          # px: edge of a cut-out on a dark background whose colours are cleaned


def decontaminate_edge(rgb, mask, band=EDGE_BAND):
    """Dark background: the pixels of the edge (the half-transparent ones and the last `band` pixels
    inside) mix the colour of the object with the dark background: a thin dark line around the sherd,
    whatever the cut-out. Their colour is replaced by the colour of the object just inside (normalised
    Gaussian average of the inner pixels), where it is lighter - the outline (mask) is not changed."""
    solid = (mask >= 250).astype(np.uint8)
    core = cv2.distanceTransform(solid, cv2.DIST_L2, 3) > band
    edge = (mask > 0) & ~core
    if not edge.any() or not core.any():
        return rgb
    w = core.astype(np.float32)
    sig = max(1.5, band)
    num = cv2.GaussianBlur(rgb.astype(np.float32) * w[..., None], (0, 0), sig)
    den = cv2.GaussianBlur(w, (0, 0), sig)
    for _ in range(3):                         # thin parts: a wider average where the first one is empty
        if (den[edge] > 0.02).all():
            break
        sig *= 2
        num2 = cv2.GaussianBlur(rgb.astype(np.float32) * w[..., None], (0, 0), sig)
        den2 = cv2.GaussianBlur(w, (0, 0), sig)
        low = den <= 0.02
        num[low], den[low] = num2[low], den2[low]
    fill = num / np.maximum(den, 1e-6)[..., None]
    darker = rgb.astype(np.float32).mean(axis=2) < fill.mean(axis=2)
    out = rgb.copy()
    sel = edge & darker & (den > 0.02)
    out[sel] = np.clip(fill[sel] + 0.5, 0, 255).astype(np.uint8)
    return out


def layout(photo, cer, scale, opts):
    """Builds the layers of the output files: the object with its mask, the scale (straightened
    under the object, or where it was photographed), the whole photo (hidden layer); sizes of
    the canvas with the margins. Returns the layers of the PSD and those of the TIFF alone."""
    rgb = photo.rgb
    H, W = rgb.shape[:2]
    px_cm = scale.px_cm if scale.found else None
    margin = int(round(opts.margin_cm * px_cm)) if px_cm else int(0.02 * max(H, W))
    gap = int(round(opts.gap_cm * px_cm)) if px_cm else int(0.02 * max(H, W))
    border = max(4, int(round(0.15 * px_cm))) if px_cm else 20   # pixels kept around the mask

    cx0, cy0, cx1, cy1 = cer["box"]
    cw, ch = cx1 - cx0, cy1 - cy0
    angle = cer.get("angle", 0.0)
    if angle:
        # object turned as decided in the review window, around the centre of its box
        cer_rgb, cer_mask, cw, ch = rotated_ceramic(rgb, cer, border, angle)
        cx0, cy0 = int(round((cx0 + cx1 - cw) / 2)), int(round((cy0 + cy1 - ch) / 2))
        cx1, cy1 = cx0 + cw, cy0 + ch
    cer["size"] = (cw, ch)

    scale_rgb = scale_mask = None
    if scale.found and opts.layout == "recompose":
        x0, y0, x1, y1 = scale.rect
        bx0, by0 = int(math.floor(x0)) - 3, int(math.floor(y0)) - 3
        bx1, by1 = int(math.ceil(x1)) + 3, int(math.ceil(y1)) + 3
        scale_rgb = extract(scale.crop, bx0, by0, bx1, by1)
        m = poly_mask(scale.crop.shape[:2], [[x0, y0], [x1, y0], [x1, y1], [x0, y1]])
        scale_mask = extract(np.dstack([m] * 3), bx0, by0, bx1, by1)[..., 0]
        scale_mask[:3] = 0; scale_mask[-3:] = 0; scale_mask[:, :3] = 0; scale_mask[:, -3:] = 0
        ew, eh = bx1 - bx0, by1 - by0
        Wc = max(cw, ew - 6) + 2 * margin
        Hc = margin + ch + gap + (eh - 6) + margin
        cer_x, cer_y = (Wc - cw) // 2, margin
        scale_x, scale_y = (Wc - ew) // 2, margin + ch + gap - 3
        shift = (cer_x - cx0, cer_y - cy0)     # original image -> canvas
    else:
        boxes = [(cx0, cy0, cx1, cy1)]
        if scale.found:
            px, py = scale.poly[:, 0], scale.poly[:, 1]
            boxes.append((int(math.floor(px.min())), int(math.floor(py.min())),
                          int(math.ceil(px.max())) + 1, int(math.ceil(py.max())) + 1))
        ux0 = min(b[0] for b in boxes) - margin
        uy0 = min(b[1] for b in boxes) - margin
        ux1 = max(b[2] for b in boxes) + margin
        uy1 = max(b[3] for b in boxes) + margin
        Wc, Hc = ux1 - ux0, uy1 - uy0
        shift = (-ux0, -uy0)
        if scale.found:
            px0, py0, px1, py1 = boxes[1]
            px0 -= 3; py0 -= 3; px1 += 3; py1 += 3
            scale_rgb = extract(rgb, px0, py0, px1, py1)
            scale_mask = poly_mask((py1 - py0, px1 - px0), scale.poly - [px0, py0])
            scale_x, scale_y = px0 + shift[0], py0 + shift[1]

    # Ceramic layer: original pixels + layer mask (can be retouched)
    gx0, gy0, gx1, gy1 = cx0 - border, cy0 - border, cx1 + border, cy1 + border
    if not angle:
        cer_rgb = extract(rgb, gx0, gy0, gx1, gy1)
        cer_mask = np.zeros(cer_rgb.shape[:2], np.uint8)
        cer_mask[border:border + ch, border:border + cw] = cer["alpha"]

    if cer.get("dark"):
        cer_rgb = decontaminate_edge(cer_rgb, cer_mask)

    layers = []
    if not opts.no_original_layer:
        # the whole photo, placed where it falls on the canvas: what lies beyond the canvas (the scale
        # where it was photographed, the rest of the background) is kept in the file
        # (Photoshop: move the layer, or Image > Reveal All)
        layers.append(Layer("Original photo", shift[0], shift[1], rgb, None, visible=False))
    if scale_rgb is not None:
        layers.append(Layer("Scale", scale_x, scale_y, scale_rgb, scale_mask))
    layers.append(Layer("Ceramic", gx0 + shift[0], gy0 + shift[1], cer_rgb, cer_mask))

    # Version without the scale: ceramic alone, cropped
    Ws, Hs = cw + 2 * margin, ch + 2 * margin
    alone = [Layer("Ceramic", margin - border, margin - border, cer_rgb, cer_mask)]
    return layers, (Wc, Hc), alone, (Ws, Hs)


# --------------------------------------------------------------------------
# PSD writing (layers, layer masks, resolution, ICC profile, EXIF)
# --------------------------------------------------------------------------

def _packbits_block(a):
    """PackBits compression (the RLE of Photoshop) of a block of rows, vectorised with numpy."""
    h, w = a.shape
    flat = a.ravel()
    n = flat.size
    start = np.ones(n, bool)
    start[1:] = flat[1:] != flat[:-1]
    start[::w] = True
    rs = np.flatnonzero(start)
    rl = np.diff(np.append(rs, n))
    rep = rl >= 3
    row = rs // w
    prev_rep = np.r_[True, rep[:-1]]
    new_row = np.r_[True, row[1:] != row[:-1]]
    sd = rep | prev_rep | new_row
    ss = np.flatnonzero(sd)
    pos = rs[ss]
    length = np.diff(np.append(pos, n))
    srep = rep[ss]
    nch = (length + 127) // 128
    ci = np.repeat(np.arange(len(ss)), nch)
    k = np.arange(ci.size) - np.repeat(np.cumsum(nch) - nch, nch)
    cpos = pos[ci] + k * 128
    clen = np.minimum(128, length[ci] - k * 128)
    crep = srep[ci] & (clen >= 2)
    size = np.where(crep, 2, 1 + clen)
    header = np.where(crep, 257 - clen, clen - 1).astype(np.uint8)
    ostart = np.cumsum(size) - size
    out = np.empty(int(size.sum()), np.uint8)
    out[ostart] = header
    r = np.flatnonzero(crep)
    out[ostart[r] + 1] = flat[cpos[r]]
    lit = np.flatnonzero(~crep)
    L = clen[lit]
    off = np.arange(int(L.sum())) - np.repeat(np.cumsum(L) - L, L)
    out[np.repeat(ostart[lit] + 1, L) + off] = flat[np.repeat(cpos[lit], L) + off]
    counts = np.bincount(row[ss][ci], weights=size, minlength=h).astype(np.int64)
    return counts, out


def packbits(a, block=256):
    """PackBits compression of a whole channel, block by block; returns the row lengths and data."""
    a = np.ascontiguousarray(a, np.uint8)
    cs, ds = [], []
    for y in range(0, a.shape[0], block):
        c, d = _packbits_block(a[y:y + block])
        cs.append(c)
        ds.append(d)
    return np.concatenate(cs), np.concatenate(ds)


def rle_channel(a):
    """A channel as Photoshop stores it: compression flag 1 (RLE), row lengths, data."""
    c, d = packbits(a)
    return struct.pack(">H", 1) + c.astype(">u2").tobytes() + d.tobytes()


def _pascal(b, multiple):
    """Pascal string (length byte + text), padded, as in the PSD format."""
    s = bytes([len(b)]) + b
    return s + b"\x00" * ((-len(s)) % multiple)


def _resource(rid, data):
    """PSD image resource block ("8BIM", id, data padded to an even length)."""
    return (b"8BIM" + struct.pack(">H", rid) + b"\x00\x00" + struct.pack(">I", len(data)) + data
            + (b"\x00" if len(data) % 2 else b""))


def _unicode(s):
    """Unicode string of the PSD format (length + UTF-16 big-endian)."""
    return struct.pack(">I", len(s)) + s.encode("utf-16-be")


def _xml(s):
    """Escapes &, < and > for XML."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# IPTC Core fields (XMP): key -> (property, kind, label). kind: text, alt (one language), seq, bag (list)
IPTC_TARGETS = {
    "title": ("dc:title", "alt", "Title"),
    "headline": ("photoshop:Headline", "text", "Headline"),
    "description": ("dc:description", "alt", "Description"),
    "keywords": ("dc:subject", "bag", "Keywords"),
    "creator": ("dc:creator", "seq", "Creator"),
    "date": ("photoshop:DateCreated", "text", "Date Created"),
    "country_code": ("Iptc4xmpCore:CountryCode", "text", "Country Code"),
    "country": ("photoshop:Country", "text", "Country"),
    "state": ("photoshop:State", "text", "State / Province"),
    "city": ("photoshop:City", "text", "City"),
    "sublocation": ("Iptc4xmpCore:Location", "text", "Sublocation"),
    "job": ("photoshop:TransmissionReference", "text", "Job Identifier"),
    "instructions": ("photoshop:Instructions", "text", "Instructions"),
    "credit": ("photoshop:Credit", "text", "Credit Line"),
    "source": ("photoshop:Source", "text", "Source"),
    "copyright": ("dc:rights", "alt", "Copyright Notice"),
}
# default model (the one of the Shelby collection, adapted to the default fields): {field} = value of the
# field of the photo, {name} = output name; a text without braces is the same for every photo
DEFAULT_IPTC = {"title": "{name}", "keywords": "{site}, {sector}, {us}, {number}, {material}, {view}",
                "country_code": "{site}", "country": "{sector}", "sublocation": "{us}"}


def iptc_values(pr, values, name):
    """IPTC fields of a photo: the mapping of the project (else DEFAULT_IPTC) filled with its values."""
    mapping = pr.get("iptc") if isinstance(pr.get("iptc"), dict) else DEFAULT_IPTC
    out = {}
    for key, template in mapping.items():
        if key not in IPTC_TARGETS or not str(template).strip():
            continue
        v = re.sub(r"\{(\w+)\}", lambda m: name if m.group(1) == "name" else str(values.get(m.group(1), "") or ""),
                   str(template))
        if IPTC_TARGETS[key][1] in ("bag", "seq"):
            items = [x.strip() for x in v.split(",") if x.strip()]
            if items:
                out[key] = items
        else:
            v = re.sub(r"\s+", " ", v).strip(" _-,;")
            if v:
                out[key] = v
    return out


def _iptc_prop(prop, kind, value):
    """One XMP property as RDF: plain text, one-language alternative (Alt) or list (Bag/Seq)."""
    if kind == "alt":
        return f'<{prop}><rdf:Alt><rdf:li xml:lang="x-default">{_xml(value)}</rdf:li></rdf:Alt></{prop}>'
    if kind in ("bag", "seq"):
        tag = "Bag" if kind == "bag" else "Seq"
        return f"<{prop}><rdf:{tag}>" + "".join(f"<rdf:li>{_xml(v)}</rdf:li>" for v in value) + f"</rdf:{tag}></{prop}>"
    return f"<{prop}>{_xml(value)}</{prop}>"


def make_xmp(description, fields, meta=None, title=None, iptc=None, packet=True):
    """XMP packet: description of the scale + shooting information of the original photo + information of
    the project (title = output name; each field as gerbil:Name, and all of them as keywords) + the IPTC
    fields of the project (iptc_values), which take precedence. packet=False: no xpacket wrapper (sidecar
    .xmp file)."""
    iptc = dict(iptc or {})
    meta = {k: v for k, v in (meta or {}).items() if v}
    if "description" in iptc:                     # the scale description stays, after the one given
        iptc["description"] = iptc["description"] + " - " + description
    else:
        iptc["description"] = description
    if title and meta and "title" not in iptc:
        iptc["title"] = title
    if meta and "keywords" not in iptc:
        iptc["keywords"] = list(meta.values())
    props = [f"<xmp:CreatorTool>Gerbil {VERSION}</xmp:CreatorTool>"]
    for key, (prop, kind, _) in IPTC_TARGETS.items():
        if key in iptc:
            props.append(_iptc_prop(prop, kind, iptc[key]))
    if "copyright" in iptc:
        props.append("<xmpRights:Marked>True</xmpRights:Marked>")
    for k, v in meta.items():
        tag = "".join(w[:1].upper() + w[1:] for w in re.findall(r"[A-Za-z0-9]+", k)) or "Field"
        props.append(f"<gerbil:{tag}>{_xml(v)}</gerbil:{tag}>")
    taken = {IPTC_TARGETS[k][0] for k in iptc}
    for key, val in (fields or {}).items():
        if not val or key in taken:
            continue
        if key == "exif:ISOSpeedRatings":
            props.append(f"<{key}><rdf:Seq><rdf:li>{_xml(val)}</rdf:li></rdf:Seq></{key}>")
        else:
            props.append(f"<{key}>{_xml(val)}</{key}>")
    x = ('<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
         '<rdf:Description rdf:about="" xmlns:dc="http://purl.org/dc/elements/1.1/" '
         'xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmlns:tiff="http://ns.adobe.com/tiff/1.0/" '
         'xmlns:exif="http://ns.adobe.com/exif/1.0/" xmlns:aux="http://ns.adobe.com/exif/1.0/aux/" '
         'xmlns:exifEX="http://cipa.jp/exif/1.0/" xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/" '
         'xmlns:Iptc4xmpCore="http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/" '
         'xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/" '
         'xmlns:gerbil="https://gerbil.archaeology/ns/1.0/">'
         + "".join(props) +
         '</rdf:Description></rdf:RDF></x:xmpmeta>')
    if packet:
        x = '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\n' + x + '\n<?xpacket end="w"?>'
    return x.encode("utf-8")


XMP_APP1 = b"http://ns.adobe.com/xap/1.0/\x00"


def embed_xmp_jpeg(path, xmp):
    """Puts the XMP packet into a JPEG file without touching the image: the APP1 XMP segment is
    replaced or added after the EXIF / JFIF segments. False when the file is not a plain JPEG."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:2] != b"\xff\xd8" or len(xmp) + len(XMP_APP1) + 2 > 65535:
        return False
    out, i, inserted = [data[:2]], 2, False
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker = data[i + 1]
        if marker == 0xDA or not (0xE0 <= marker <= 0xEF or marker == 0xFE):
            break                                       # first segment that is not APPn / comment
        n = struct.unpack(">H", data[i + 2:i + 4])[0]
        seg = data[i:i + 2 + n]
        if not (marker == 0xE1 and seg[4:4 + len(XMP_APP1)] == XMP_APP1):
            out.append(seg)                             # the old XMP segment is dropped
        i += 2 + n
    payload = XMP_APP1 + xmp
    out.append(b"\xff\xe1" + struct.pack(">H", len(payload) + 2) + payload)
    out.append(data[i:])
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(b"".join(out))
    os.replace(tmp, path)
    return True


def write_sidecar(photo_path, xmp, folder=None):
    """NAME.xmp beside a photo (Bridge, Lightroom, darktable read it, above all for RAW files). A sidecar
    written by another program (Lightroom: develop settings) is never replaced. Returns the path or None."""
    sidecar = os.path.join(folder or os.path.dirname(photo_path), os.path.splitext(os.path.basename(photo_path))[0] + ".xmp")
    if os.path.exists(sidecar):
        try:
            with open(sidecar, encoding="utf-8", errors="ignore") as fh:
                if "Gerbil" not in fh.read(4000):
                    return None
        except OSError:
            return None
    with open(sidecar, "wb") as fh:
        fh.write(xmp)
    return sidecar


def write_psd(path, W, H, layers, comp_rgb, comp_a, dpi, icc, exif, xmp):
    """Writes the layered Photoshop file byte by byte: header, resolution in cm, ICC profile,
    EXIF and XMP, layers with their masks (PackBits), flattened image. See PSEUDOCODE §13."""
    res = b""
    fx = int(round(dpi * 65536))
    res += _resource(0x03ED, struct.pack(">IHHIHH", fx, 1, 2, fx, 1, 2))   # resolution, units in cm
    res += _resource(0x0421, struct.pack(">I", 1) + b"\x01" + _unicode("Gerbil")
                     + _unicode("Adobe Photoshop") + struct.pack(">I", 1))
    if icc:
        res += _resource(0x040F, icc)
    if exif is not None:
        try:
            eb = exif.tobytes()
            if eb.startswith(b"Exif\x00\x00"):
                eb = eb[6:]
            res += _resource(0x0422, eb)
        except Exception:
            pass
    res += _resource(0x0424, xmp)

    records, data = [], []
    for k, c in enumerate(layers):
        h, w = c.rgb.shape[:2]
        channels = [(-1, np.full((h, w), 255, np.uint8))] + [(i, c.rgb[..., i]) for i in range(3)]
        if c.mask is not None:
            channels.append((-2, c.mask))
        blocks = [rle_channel(np.ascontiguousarray(a)) for _, a in channels]
        r = struct.pack(">iiiiH", c.y, c.x, c.y + h, c.x + w, len(channels))
        for (cid, _), b in zip(channels, blocks):
            r += struct.pack(">hI", cid, len(b))
        flags = 0x08 | (0 if c.visible else 0x02)
        r += b"8BIMnorm" + struct.pack(">BBBB", 255, 0, flags, 0)
        ex = b""
        if c.mask is not None:
            ex += struct.pack(">IiiiiBBH", 20, c.y, c.x, c.y + h, c.x + w, 0, 0, 0)
        else:
            ex += struct.pack(">I", 0)
        ex += struct.pack(">I", 40) + b"\x00\x00\xff\xff" * 10
        ex += _pascal(c.name.encode("cp1252", "replace")[:255], 4)
        luni = struct.pack(">I", len(c.name)) + c.name.encode("utf-16-be")
        luni += b"\x00" * ((-len(luni)) % 4)
        ex += b"8BIMluni" + struct.pack(">I", len(luni)) + luni
        ex += b"8BIMlyid" + struct.pack(">II", 4, k + 2)
        r += struct.pack(">I", len(ex)) + ex
        records.append(r)
        data.extend(blocks)

    body = struct.pack(">h", -len(layers)) + b"".join(records)
    li_size = len(body) + sum(len(b) for b in data)
    pad = (-li_size) % 4
    li_size += pad

    white = comp_a.astype(np.float32)[..., None] / 255.0
    matted = np.clip(comp_rgb * white + 255 * (1 - white) + 0.5, 0, 255).astype(np.uint8)
    cs, ds = [], []
    for a in (matted[..., 0], matted[..., 1], matted[..., 2], comp_a):
        c, d = packbits(a)
        cs.append(c.astype(">u2").tobytes())
        ds.append(d.tobytes())

    with open(path, "wb") as fh:
        fh.write(struct.pack(">4sH6sHIIHH", b"8BPS", 1, b"\x00" * 6, 4, H, W, 8, 3))
        fh.write(struct.pack(">I", 0))
        fh.write(struct.pack(">I", len(res)) + res)
        fh.write(struct.pack(">I", 4 + li_size + 4))
        fh.write(struct.pack(">I", li_size))
        fh.write(body)
        for b in data:
            fh.write(b)
        fh.write(b"\x00" * pad)
        fh.write(struct.pack(">I", 0))
        fh.write(struct.pack(">H", 1))
        for c in cs:
            fh.write(c)
        for d in ds:
            fh.write(d)


# --------------------------------------------------------------------------
# TIFF writing
# --------------------------------------------------------------------------

TIFF_COMPRESSIONS = {"lzw": "tiff_lzw", "zip": "tiff_adobe_deflate", "none": None}


def write_tiff(path, rgb, a, dpi, icc, xmp, fields, description, background, compression):
    """Writes a TIFF (transparent or on white, LZW / ZIP / none) at the 1:1 resolution, with
    the ICC profile, the XMP and the main text tags."""
    if background == "white":
        al = a.astype(np.float32)[..., None] / 255.0
        img = Image.fromarray(np.clip(rgb * al + 255 * (1 - al) + 0.5, 0, 255).astype(np.uint8), "RGB")
    else:
        img = Image.fromarray(np.dstack([rgb, a]), "RGBA")
    # TIFF text tags are ASCII; the full text (accents) is in the XMP.
    ascii_ = unicodedata.normalize("NFKD", description).encode("ascii", "ignore").decode("ascii")
    info = {700: xmp, 305: f"Gerbil {VERSION}"}
    for tag, key in ((271, "tiff:Make"), (272, "tiff:Model")):
        if fields.get(key):
            info[tag] = fields[key]
    if fields.get("exif:DateTimeOriginal"):
        info[306] = fields["exif:DateTimeOriginal"].replace("-", ":").replace("T", " ")
    kw = {"dpi": (dpi, dpi), "description": ascii_}
    if TIFF_COMPRESSIONS[compression]:
        kw["compression"] = TIFF_COMPRESSIONS[compression]
        info[317] = 2                                     # horizontal predictor
    kw["tiffinfo"] = info
    if icc:
        kw["icc_profile"] = icc
    img.save(path, **kw)


# --------------------------------------------------------------------------
# Control preview
# --------------------------------------------------------------------------

def font(size):
    """A TrueType font for the texts of the control preview (Arial, Segoe UI, DejaVu...)."""
    for name in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            pass
    return ImageFont.load_default()


def control_image(path, photo, cer, scale, text_lines):
    """The control preview (to_control): reduced photo, outline of the cut-out in green,
    scale in magenta with its marks, what was discarded in red, removed by the AI in cyan,
    and the main information written on top."""
    rgb = photo.rgb
    H, W = rgb.shape[:2]
    k = 1600 / max(H, W)
    vis = cv2.resize(rgb, (round(W * k), round(H * k)), interpolation=cv2.INTER_AREA)
    vis = (vis.astype(np.float32) * 0.85 + 255 * 0.15).astype(np.uint8)
    if cer is not None:
        x0, y0, x1, y1 = cer["box"]
        m = (cer["alpha"] > 127).astype(np.uint8)
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cs = [np.round((c.astype(np.float32) + [x0, y0] + 0.5) * k - 0.5).astype(np.int32) for c in cs]
        cv2.drawContours(vis, cs, -1, (0, 200, 0), 2, cv2.LINE_AA)
        for pf in cer.get("supports", []) + cer.get("shadows", []):   # removed supports, shadows: blue
            cv2.polylines(vis, [np.round((pf + 0.5) * k - 0.5).astype(np.int32)], True, (30, 90, 255), 2, cv2.LINE_AA)
        for pf in (cer.get("isolated", []) + cer.get("charts", []) + cer.get("labels", [])
                   + cer.get("printed", [])):                                             # discarded: red
            cv2.polylines(vis, [np.round((pf + 0.5) * k - 0.5).astype(np.int32)], True, (230, 40, 40), 2, cv2.LINE_AA)
        for pf in cer.get("ai_removed", []):                          # background removed by the AI: cyan
            cv2.polylines(vis, [np.round((pf + 0.5) * k - 0.5).astype(np.int32)], True, (0, 220, 255), 2, cv2.LINE_AA)
        for pf in cer.get("removed", []) + cer.get("suspect", []):    # mounting putty: red area
            p = np.round((pf + 0.5) * k - 0.5).astype(np.int32)
            overlay = vis.copy()
            cv2.fillPoly(overlay, [p], (230, 40, 40))
            vis = cv2.addWeighted(overlay, 0.45, vis, 0.55, 0)
            cv2.polylines(vis, [p], True, (230, 40, 40), 2, cv2.LINE_AA)
    if scale.found:
        cv2.polylines(vis, [np.round((scale.poly + 0.5) * k - 0.5).astype(np.int32)], True, (255, 0, 255), 2, cv2.LINE_AA)
        y0m, y1m = scale.pattern["y0"], scale.pattern["y1"]
        for xf in scale.pattern["boundaries"]:
            p = apply_affine(scale.M, [[xf, y0m - 0.4 * scale.pattern["hf"]], [xf, y1m + 0.4 * scale.pattern["hf"]]])
            p = np.round((p + 0.5) * k - 0.5).astype(np.int32)
            cv2.line(vis, tuple(p[0]), tuple(p[1]), (255, 160, 0), 2, cv2.LINE_AA)
    im = Image.fromarray(vis)
    dr = ImageDraw.Draw(im)
    fnt = font(24)
    y = 8
    for t in text_lines:
        dr.text((10, y), t, font=fnt, fill=(0, 0, 0), stroke_width=3, stroke_fill=(255, 255, 255))
        y += 30
    im.save(path, quality=88)


# --------------------------------------------------------------------------
# Processing of one photo
# --------------------------------------------------------------------------

RESULT_DIR = "outlined_result"
CONTROL_DIR = "to_control"
DOUBT_SUFFIX = "_to_be_verified"
REPORT_NAME = "outlined_report.csv"

REPORT_FIELDS = ["file", "output_name", "status", "to_verify", "scale_found", "scale_type", "squares",
                 "scale_length_cm", "px_per_cm", "ppi_1_1", "ceramic_width_cm", "ceramic_height_cm",
                 "pieces", "camera", "lens", "focal_mm", "date_taken", "notes", "duration_s"]
DECIMAL_FIELDS = ("scale_length_cm", "px_per_cm", "ppi_1_1", "ceramic_width_cm", "ceramic_height_cm", "duration_s")
# column names written by version 1.0 of this script, so that its reports can be updated (the column
# of the former DDN naming rule, name_ok, is dropped)
LEGACY_COLUMNS = dict(zip(
    ["fichier", "statut", "a_verifier", "nom_conforme", "echelle_detectee", "type_echelle", "cases",
     "longueur_echelle_cm", "px_par_cm", "ppi_1_1", "largeur_ceramique_cm", "hauteur_ceramique_cm",
     "morceaux", "appareil", "objectif", "focale_mm", "date_prise", "remarques", "duree_s"],
    ["file", "status", "to_verify", "name_ok", "scale_found", "scale_type", "squares",
     "scale_length_cm", "px_per_cm", "ppi_1_1", "ceramic_width_cm", "ceramic_height_cm",
     "pieces", "camera", "lens", "focal_mm", "date_taken", "notes", "duration_s"]))

# end-of-run summary: the reasons for doubt, grouped (first matching pattern wins)
PROBLEMS = [
    ("Scale not found", ("scale not detected", "scale spotted but unreadable")),
    ("Scale doubtful (length, irregular or hidden graduations)",
     ("squares detected (not", "cm read (neither", "irregular scale squares", "irregular graduations",
      "graduations partly hidden")),
    ("No object kept", ("no ceramic kept", "no object detected", "empty outline")),
    ("Object cut by the photo edge", ("cut by the photo edge",)),
    ("Mounting putty (flagged or removed)", ("mounting putty",)),
    ("Colour chart touching the object", ("colour chart touching",)),
    ("Missing information (batch renaming)", ("missing information",)),
    ("Name off the naming rule", ("naming rule",)),
    ("Photo extension not in lowercase", ("photo extension not in lowercase",)),
    ("Output name used twice", ("output name already used",)),
]


def output_paths(folder, base, doubtful):
    """Paths of the files of a photo (PSD, TIFF, preview), with _to_be_verified when doubtful."""
    s = DOUBT_SUFFIX if doubtful else ""
    return {
        "psd": os.path.join(folder, f"{base}{s}.psd"),
        "outlined": os.path.join(folder, f"{base}_outlined{s}.tif"),
        "outlined_scale": os.path.join(folder, f"{base}_outlined_scale{s}.tif"),
        "control": os.path.join(folder, CONTROL_DIR, f"{base}_to_control{s}.jpg"),
    }


def remove_stale(folder, base, written):
    """After a new run, deletes the obsolete variant (with / without "_to_be_verified")
    of the files that have just been rewritten."""
    for doubtful in (False, True):
        for key, path in output_paths(folder, base, doubtful).items():
            if path in written:
                other = output_paths(folder, base, not doubtful)[key]
                if other not in written and os.path.exists(other):
                    os.remove(other)


def copy_original(path, folder):
    """Copy of the original photo in the result folder; returns its path (None: same file)."""
    dest = os.path.join(folder, os.path.basename(path))
    if os.path.normcase(os.path.abspath(dest)) == os.path.normcase(os.path.abspath(path)):
        return None
    if (os.path.exists(dest) and os.path.getsize(dest) == os.path.getsize(path)
            and int(os.path.getmtime(dest)) == int(os.path.getmtime(path))):
        return dest
    shutil.copy2(path, dest)
    return dest



# --------------------------------------------------------------------------
# Project: fields, naming template, naming rule, values of the photos (gerbil_project.json)
# --------------------------------------------------------------------------

PROJECT_FILE = "gerbil_project.json"   # in the folder of the photos, written by the interface ("Project…")
DEFAULT_FIELDS = [
    {"key": "site", "label": "Site", "required": True},
    {"key": "sector", "label": "Sector"},
    {"key": "us", "label": "US"},
    {"key": "number", "label": "Object number", "required": True},
    {"key": "material", "label": "Material", "choices": ["ceramic", "metal", "bone", "glass", "lithic", "other"]},
    {"key": "view", "label": "View", "choices": ["exterior", "interior", "profile", "top", "bottom"]},
]
NAME_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f\s]+')


def load_project(folder):
    """Project of a folder of photos, or None. Keys: fields (key, label, required, choices), template
    (e.g. "{site}_{us}_{number}"; empty: the names of the photos are kept), rule (regular expression
    the output names must match; empty: none), common (values of all the photos), photos (name ->
    values)."""
    path = os.path.join(folder, PROJECT_FILE)
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            pr = json.load(fh)
    except (OSError, ValueError) as e:
        print(f"Warning: {path} cannot be read ({e}): names and information of the project not used.")
        return None
    if not isinstance(pr, dict):
        print(f"Warning: {path} is not a project file: names and information of the project not used.")
        return None
    pr.setdefault("fields", DEFAULT_FIELDS)
    for k, v in (("template", ""), ("rule", ""), ("common", {}), ("photos", {})):
        pr.setdefault(k, v)
    return pr


def photo_values(project, name):
    """Values of a photo: those common to the project, completed / replaced by its own."""
    vals = {k: str(v).strip() for k, v in (project.get("common") or {}).items() if str(v).strip()}
    vals.update({k: str(v).strip() for k, v in ((project.get("photos") or {}).get(name) or {}).items()
                 if str(v).strip()})
    return vals


def project_name(project, name):
    """Output name (without extension) built from the template, or None (template empty or giving
    nothing). Forbidden characters and spaces become "_"; the separators left by empty fields are
    merged ("{site}_{us}_{number}" without US: "QSR25_12")."""
    template = (project or {}).get("template", "").strip()
    if not template:
        return None
    vals = dict(photo_values(project, name), photo=os.path.splitext(name)[0])
    out = re.sub(r"\{(\w+)\}", lambda m: vals.get(m.group(1), ""), template)
    out = NAME_FORBIDDEN.sub("_", out)
    out = re.sub(r"([_\-.])[_\-.]+", r"\1", out).strip("_-. ")
    return out or None


def rule_regex(rule):
    """The naming rule as PowerShell's -match reads it: .NET regular expression, case-insensitive, found
    anywhere in the name unless anchored with ^ and $. .NET named groups (?<name>...) are accepted, and
    (?-i) at the start makes the rule case-sensitive (as in PowerShell)."""
    rule = re.sub(r"\(\?<(?![=!])", "(?P<", rule)
    if rule.startswith("(?-i)"):
        return re.compile(rule[5:])
    return re.compile(rule, re.IGNORECASE)


def project_checks(project, name, out_name):
    """Reasons for doubt about the information of a photo: required fields empty, name off the rule."""
    doubts = []
    vals = photo_values(project, name)
    missing = [f.get("label", f["key"]) for f in project.get("fields", []) if f.get("required") and not vals.get(f["key"])]
    if missing:
        doubts.append("missing information: " + ", ".join(missing))
    if project.get("photo_ext_lower"):
        ext = os.path.splitext(name)[1]
        if ext != ext.lower():
            doubts.append(f"photo extension not in lowercase ({ext})")
    rule = (project.get("rule") or "").strip()
    if rule:
        try:
            if not rule_regex(rule).search(out_name or os.path.splitext(name)[0]):
                doubts.append("name does not match the naming rule")
        except re.error:
            doubts.append("naming rule is not a valid regular expression")
    return doubts


def plan_names(tasks):
    """Output name and information of every photo, decided before the processing: two photos of the same
    result folder cannot get the same name (a suffix _2, _3... is added, with a doubt)."""
    projects, plan, used = {}, {}, {}
    for fp, out_dir in tasks:
        folder = os.path.dirname(os.path.abspath(fp))
        if folder not in projects:
            projects[folder] = load_project(folder)
        pr = projects[folder]
        name = os.path.basename(fp)
        base = (project_name(pr, name) if pr else None) or os.path.splitext(name)[0]
        doubts = project_checks(pr, name, base) if pr else []
        key = (os.path.normcase(out_dir), base.lower())
        used[key] = used.get(key, 0) + 1
        if used[key] > 1:
            base = f"{base}_{used[key]}"
            doubts.append(f"output name already used by another photo (suffix _{used[key]} added)")
        meta, iptc = {}, {}
        if pr:
            vals = photo_values(pr, name)
            meta = {f.get("label", f["key"]): vals.get(f["key"], "") for f in pr.get("fields", [])}
            iptc = iptc_values(pr, vals, base)
        plan[fp] = {"base": base, "doubts": doubts, "meta": meta, "iptc": iptc,
                    "sidecar": bool(pr and pr.get("xmp_sidecar"))}
    return plan


# --------------------------------------------------------------------------
# Review window: data written for it, corrections read back
# --------------------------------------------------------------------------

REVIEW_DIR = "gerbil_review"      # in the result folder: mask and scale of each photo, for the review window
EDITS_DIR = "gerbil_edits"        # next to the photos: corrections made in the review window
EDITS_FILE = "gerbil_edits.json"  # in EDITS_DIR: {photo name: {"mask": true if corrected, "angle": degrees}}


def edits_entry(path):
    """Corrections made by hand for this photo: (mask or None, angle in degrees). The mask (full photo,
    0 / 255) replaces the computed cut-out; the angle turns the object (counterclockwise)."""
    folder = os.path.join(os.path.dirname(os.path.abspath(path)), EDITS_DIR)
    try:
        with open(os.path.join(folder, EDITS_FILE), encoding="utf-8") as fh:
            entry = json.load(fh).get(os.path.basename(path)) or {}
    except (OSError, ValueError, AttributeError):
        return None, 0.0
    mask = None
    if entry.get("mask"):
        try:
            with Image.open(os.path.join(folder, os.path.splitext(os.path.basename(path))[0] + "_mask.png")) as im:
                mask = np.asarray(im.convert("L"))
        except OSError:
            mask = None
    try:
        angle = float(entry.get("angle", 0.0)) % 360.0
    except (TypeError, ValueError):
        angle = 0.0
    return mask, angle


def cutout_from_mask(mask, cer):
    """Cut-out from a mask corrected by hand (photo size): same softened edge as outline_ceramic
    (Gaussian blur 0.8 px of the 0 / 255 mask). The other fields of `cer` are kept (or emptied)."""
    m = (mask > 127).astype(np.uint8)
    if not m.any():
        return None
    ys, xs = np.nonzero(m)
    pad = 3
    x0, y0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
    x1, y1 = min(m.shape[1], xs.max() + 1 + pad), min(m.shape[0], ys.max() + 1 + pad)
    alpha = cv2.GaussianBlur((m[y0:y1, x0:x1] * 255).astype(np.float32), (0, 0), 0.8)
    alpha = np.clip(alpha + 0.5, 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(alpha > 0)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    out = {"isolated": [], "labels": [], "printed": [], "near_scale": 0, "supports": [], "shadows": [],
           "charts": [], "chart_attached": False, "ai_removed": [], "ai_area": 0.0, "removed": []}
    out.update({k: v for k, v in (cer or {}).items()
                if k in ("isolated", "labels", "printed", "supports", "shadows", "charts", "dark")})
    n, _ = cv2.connectedComponents(m[y0:y1, x0:x1], connectivity=8)
    out.update({"alpha": alpha[by0:by1, bx0:bx1], "box": (x0 + bx0, y0 + by0, x0 + bx1, y0 + by1),
                "pieces": n - 1, "edited": True})
    return out


def write_review(out_dir, path, shape, cer, scale, status, doubts, angle, output=None):
    """Mask (photo size) and scale outline of the photo, for the review window of the interface."""
    folder = os.path.join(out_dir, REVIEW_DIR)
    os.makedirs(folder, exist_ok=True)
    base = os.path.splitext(os.path.basename(path))[0]
    H, W = shape[:2]
    m = np.zeros((H, W), np.uint8)
    if cer is not None:
        x0, y0, x1, y1 = cer["box"]
        m[y0:y1, x0:x1] = cer["alpha"]
    Image.fromarray(m).save(os.path.join(folder, base + "_mask.png"), compress_level=1)
    info = {"photo": os.path.abspath(path), "width": W, "height": H, "status": status, "to_verify": doubts,
            "scale": scale.poly.round(2).tolist() if scale.found else None,
            "px_cm": round(scale.px_cm, 4) if scale.found else None, "angle": angle,
            "edited": bool(cer and cer.get("edited")),
            "output": output or base}
    with open(os.path.join(folder, base + ".json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1)


def rotated_ceramic(rgb, cer, border, angle):
    """The object turned by `angle` degrees (counterclockwise, as decided in the review window): pixels
    (bicubic) and layer mask (bilinear) resampled once. Returns rgb, mask (with `border` around the
    object), and the width and height of the turned object."""
    x0, y0, x1, y1 = cer["box"]
    pad = border + 2
    region = extract(rgb, x0 - pad, y0 - pad, x1 + pad, y1 + pad)
    h, w = region.shape[:2]
    m = np.zeros((h, w), np.uint8)
    m[pad:pad + (y1 - y0), pad:pad + (x1 - x0)] = cer["alpha"]
    M = cv2.getRotationMatrix2D(((w - 1) / 2, (h - 1) / 2), angle, 1.0)
    cos, sin = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(math.ceil(h * sin + w * cos)), int(math.ceil(h * cos + w * sin))
    M[0, 2] += (nw - 1) / 2 - (w - 1) / 2
    M[1, 2] += (nh - 1) / 2 - (h - 1) / 2
    r = cv2.warpAffine(region, M, (nw, nh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT,
                       borderValue=(255, 255, 255))
    rm = cv2.warpAffine(m, M, (nw, nh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    ys, xs = np.nonzero(rm > 0)
    bx0, by0, bx1, by1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    out_rgb = extract(r, bx0 - border, by0 - border, bx1 + border, by1 + border)
    out_m = np.zeros(out_rgb.shape[:2], np.uint8)
    out_m[border:border + (by1 - by0), border:border + (bx1 - bx0)] = rm[by0:by1, bx0:bx1]
    return out_rgb, out_m, bx1 - bx0, by1 - by0


def process_photo(path, opts, out_dir, plan=None):
    """plan: output name, doubts and information of the photo decided by plan_names (project)."""
    t0 = time.time()
    name = os.path.basename(path)
    plan = plan or {}
    base = plan.get("base") or os.path.splitext(name)[0]
    row = {k: "" for k in REPORT_FIELDS}
    row.update({"_out_dir": out_dir, "file": name, "output_name": base, "_meta": plan.get("meta") or {}})
    notes, doubts, written = [], list(plan.get("doubts") or []), set()
    try:
        photo = load_photo(path)
        row.update({"camera": photo.info["camera"], "lens": photo.info["lens"],
                    "focal_mm": photo.info["focal_mm"], "date_taken": photo.info["date"]})
        rgb = photo.rgb
        H, W = rgb.shape[:2]
        f = min(1.0, ANALYSIS_SIZE / max(H, W))
        small = cv2.resize(rgb, (round(W * f), round(H * f)), interpolation=cv2.INTER_AREA)
        background = BackgroundModel(to_lab(cv2.GaussianBlur(small, (3, 3), 0)))
        profile = load_profile(find_profile(path, getattr(opts, "profile", None)))
        if profile and profile.get("background") in ("light", "dark"):
            background.dark = profile["background"] == "dark"      # said by the site profile

        manual = manual_scale_entry(path)
        if manual:                                   # given by hand in the interface: it prevails
            scale = manual_scale(rgb, manual)
            notes.append(scale.note)
        elif opts.no_scale:
            scale = Scale(note="scale detection disabled")
            notes.append(scale.note)
        else:
            # learned scales of the profile: as a second chance when the usual detection fails or is
            # doubtful, or first when the profile says so (a scale the usual detection reads badly)
            models = profile["_models"] if profile else []
            scale = detect_learned_scale(rgb, models) if models and profile.get("learned_first") else None
            if scale is None:
                scale = detect_scale(rgb, small, f, opts.scale_cm, dark=background.dark)
                if models and not profile.get("learned_first") and (not scale.found or scale.doubts):
                    scale = detect_learned_scale(rgb, models) or scale
            if not scale.found:
                doubts.append(scale.note)
            elif scale.note:
                notes.append(scale.note)
        if scale.found:
            doubts += scale.doubts or []
            ppi = scale.px_cm * 2.54
            row.update({"scale_found": "yes", "scale_type": scale.kind, "squares": scale.n_squares,
                        "scale_length_cm": f"{scale.length_cm:g}", "px_per_cm": f"{scale.px_cm:.2f}",
                        "ppi_1_1": f"{ppi:.1f}"})
        else:
            ppi = float(opts.default_ppi)
            row["scale_found"] = "no"

        ai = None
        if opts.ai:
            try:
                ai = ai_mask(rgb, opts)
            except Exception as e:
                notes.append(f"AI not used ({type(e).__name__}: {e})")
        cer, msg = outline_ceramic(photo, small, f, background, scale, ai)
        edited_mask, angle = edits_entry(path)
        if edited_mask is not None and edited_mask.shape[:2] == (H, W):
            # cut-out corrected by hand in the review window: it replaces the computed one
            cer, msg = cutout_from_mask(edited_mask, cer), ""
            notes.append("cut-out corrected by hand")
            if cer is None:
                msg = "no object kept (corrected by hand)"
        if msg:
            doubts.append(msg)
        if cer is not None and angle:
            cer["angle"] = angle
            notes.append(f"object turned by hand ({angle:g}°)")
        if cer is not None and scale.found and not cer.get("edited"):
            cer_without, polys, area = find_putty(rgb, cer, scale.px_cm)
            if polys and opts.remove_putty:
                cer = cer_without
                doubts.append(f"mounting putty removed ({area:.1f} cm²)")
            elif polys:
                cer = dict(cer, suspect=polys)
                doubts.append(f"possible mounting putty ({area:.1f} cm², red area in preview)")
        if cer is not None and cer.get("isolated"):
            notes.append("small isolated element discarded (red outline in preview)")
        if cer is not None and cer.get("labels"):
            notes.append("paper label discarded (red outline in preview)")
        if cer is not None and cer.get("printed"):
            notes.append("scale, label or card discarded (red outline in preview)")
        if cer is not None and cer.get("label_kept"):
            doubts.append("the only object looks like a paper label (kept: check it)")
        if cer is not None and cer.get("near_scale"):
            notes.append(f"{cer['near_scale']} object(s) lying close to the scale kept")
        if cer is not None and cer.get("supports"):
            notes.append("translucent support removed (blue outline in preview)")
        if cer is not None and cer.get("shadows"):
            notes.append("cast shadow removed (blue outline in preview)")
        if cer is not None and cer.get("charts"):
            notes.append("colour chart discarded (red outline in preview)")
        if cer is not None and cer.get("chart_attached"):
            doubts.append("colour chart touching the ceramic (kept with it)")
        if cer is not None and cer.get("ai_removed"):
            notes.append(f"AI ({AI_MODELS[opts.ai_model][0]}) removed background: {len(cer['ai_removed'])} area(s), "
                         f"{cer['ai_area']:.2f} cm² (cyan outline in preview)")
        if cer is not None:
            x0, y0, x1, y1 = cer["box"]
            if x0 <= 1 or y0 <= 1 or x1 >= W - 1 or y1 >= H - 1:
                doubts.append("ceramic cut by the photo edge")
        doubtful = bool(doubts)
        paths = output_paths(out_dir, base, doubtful)

        icc = photo.icc or srgb_profile()
        exif = output_exif(photo.exif, ppi)
        if scale.found:
            desc = (f"Scale detected ({scale.kind}): {scale.length_cm:g} cm, "
                    f"{scale.px_cm:.2f} px/cm, {ppi:.1f} ppi = real size (1:1). Source: {name}")
        else:
            desc = f"No scale: default resolution {ppi:g} ppi (real size unknown). Source: {name}"
        fields = photo.info["xmp"]
        xmp = make_xmp(desc, fields, row["_meta"], base, plan.get("iptc"))

        if cer is not None:
            row["pieces"] = cer["pieces"]
            layers, (Wc, Hc), alone, (Ws, Hs) = layout(photo, cer, scale, opts)
            if scale.found:
                w_px, h_px = cer["size"]            # (turned object: its new width and height)
                row["ceramic_width_cm"] = f"{w_px / scale.px_cm:.1f}"
                row["ceramic_height_cm"] = f"{h_px / scale.px_cm:.1f}"
            comp_rgb, comp_a = composite(layers, Wc, Hc)
            if not opts.no_psd:
                write_psd(paths["psd"], Wc, Hc, layers, comp_rgb, comp_a, ppi, icc, exif, xmp)
                written.add(paths["psd"])
            if scale.found:
                write_tiff(paths["outlined_scale"], comp_rgb, comp_a, ppi, icc, xmp, fields, desc,
                           opts.background, opts.compression)
                written.add(paths["outlined_scale"])
            del comp_rgb, comp_a
            s_rgb, s_a = composite(alone, Ws, Hs)
            write_tiff(paths["outlined"], s_rgb, s_a, ppi, icc, xmp, fields, desc,
                       opts.background, opts.compression)
            written.add(paths["outlined"])
            row["status"] = "to verify" if doubtful else "ok"
        else:
            row["status"] = "failed"

        if not opts.no_control:
            txt = [name]
            if scale.found:
                txt.append(f"{scale.kind.capitalize()} {scale.length_cm:g} cm: "
                           f"{scale.px_cm:.1f} px/cm = {ppi:.0f} ppi")
            if row["ceramic_width_cm"]:
                txt.append(f"Ceramic: {row['ceramic_width_cm']} x {row['ceramic_height_cm']} cm")
            txt += [f"TO VERIFY: {d}" for d in doubts] + notes
            control_image(paths["control"], photo, cer, scale, txt)
            written.add(paths["control"])
            write_review(out_dir, path, rgb.shape, cer, scale, row["status"], doubts, angle, base)
        iptc = plan.get("iptc")
        if not opts.no_original_copy:
            copy = copy_original(path, out_dir)
            if copy and iptc:                       # IPTC in the copy: JPEG without recompression, else NAME.xmp
                src_xmp = make_xmp(f"Original photo of {base}", photo.info["xmp"], row["_meta"], base, iptc)
                if not (copy.lower().endswith((".jpg", ".jpeg")) and embed_xmp_jpeg(copy, src_xmp)):
                    write_sidecar(copy, make_xmp(f"Original photo of {base}", photo.info["xmp"], row["_meta"],
                                                 base, iptc, packet=False))
        if iptc and plan.get("sidecar"):
            if not write_sidecar(path, make_xmp(f"Photo processed by Gerbil: {base}", {}, row["_meta"], base, iptc,
                                                packet=False)):
                notes.append("a .xmp file written by another program is next to the photo: not changed")
        remove_stale(out_dir, base, written)
    except Exception as e:
        row["status"] = "error"
        notes.append(f"{type(e).__name__}: {e}")
        if opts.verbose:
            traceback.print_exc()
    row["to_verify"] = " ; ".join(doubts)
    row["notes"] = " ; ".join(notes)
    row["duration_s"] = f"{time.time() - t0:.1f}"
    return row


def _init_worker():
    """Each worker process limits OpenCV to 2 threads (photos are already processed in
    parallel)."""
    cv2.setNumThreads(2)


GERBIL_OUTPUT = re.compile(r"_(outlined(_scale)?|to_control)(_to_be_verified)?\.[a-z]+$|_thumb\.[a-z]+$", re.I)


def list_photos(inputs):
    """Photos of the folders / files given. Gerbil's own results (NAME_outlined.tif, _to_control.jpg…)
    lying among the photos (result folder = photo folder) are left out: never processed again."""
    files, skipped = [], 0
    for e in inputs:
        if os.path.isdir(e):
            for name in sorted(os.listdir(e)):
                if os.path.splitext(name)[1].lower() in EXTENSIONS:
                    if GERBIL_OUTPUT.search(name):
                        skipped += 1
                        continue
                    files.append(os.path.join(e, name))
        elif os.path.isfile(e):
            files.append(e)
        else:
            print(f"Not found: {e}")
    if skipped:
        print(f"{skipped} result file(s) of Gerbil among the photos left out (choose a result folder other "
              "than the photo folder)")
    return files


class _HelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    """Shows the default value only when it is meaningful."""

    def _get_help_string(self, action):
        """Help of an option: its default value shown only when it means
        something."""
        if action.default in (None, False):
            return action.help
        return super()._get_help_string(action)


def main(argv=None):
    """Command line: reads the options, lists the photos, plans their output names (batch
    renaming), processes them in parallel (process_photo), writes the report and prints the
    summary of the problems."""
    try:
        if sys.stdout.isatty():
            sys.stdout.reconfigure(errors="replace")
        else:                       # read by the interface: UTF-8 (the .exe ignores PYTHONIOENCODING: cm²)
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    p = argparse.ArgumentParser(
        description="Gerbil - archaeological photo toolkit: outlining of finds photographed with a scale, at 1:1, with scale detection "
                    "(1 cm squares or millimetre ruler) and 1:1 resolution.",
        formatter_class=_HelpFormatter)
    p.add_argument("inputs", nargs="+", help="folder(s) and/or photo(s) to process")
    p.add_argument("-o", "--output", help=f"output folder (default: '{RESULT_DIR}' "
                                          "next to the photos, one per folder)")
    p.add_argument("--scale-cm", type=float, default=None,
                   help="force the scale length in cm (default: number of 1 cm squares counted)")
    p.add_argument("--background", choices=["transparent", "white"], default="transparent",
                   help="background of the TIFF files")
    p.add_argument("--remove-putty", action="store_true",
                   help="remove the suspected mounting putty (Patafix) automatically instead of only "
                        "flagging it")
    p.add_argument("--layout", choices=["recompose", "original"], default="recompose",
                   help="recompose: scale straightened and centred under the sherd; "
                        "original: scale left where it was photographed")
    p.add_argument("--margin-cm", type=float, default=0.5, help="margin around the objects")
    p.add_argument("--gap-cm", type=float, default=0.5, help="gap between sherd and scale")
    p.add_argument("--compression", choices=list(TIFF_COMPRESSIONS), default="lzw", help="TIFF compression")
    p.add_argument("--default-ppi", type=float, default=300, help="resolution used when no scale is found")
    p.add_argument("--ai", action="store_true",
                   help="AI second opinion (needs the onnxruntime package): the network may only remove "
                        "background the script kept (perforations, gaps, halos), never add anything")
    p.add_argument("--ai-model", choices=list(AI_MODELS), default="isnet",
                   help="isnet: fast, uses the graphics card; birefnet: more precise on perforations, much "
                        "slower. Downloaded once into the 'models' folder next to the script")
    p.add_argument("--ai-device", choices=["auto", "cpu"], default="auto",
                   help="auto: graphics card when available, else processor; cpu: processor only")
    p.add_argument("--no-scale", action="store_true", help="do not look for a scale")
    p.add_argument("--version", action="version", version=f"Gerbil {VERSION}")
    p.add_argument("--profile", metavar="FILE",
                   help=f"site profile (background, learned scales); default: {PROFILE_FILE} next to the photos")
    p.add_argument("--no-psd", action="store_true", help="do not write PSD files")
    p.add_argument("--no-original-layer", action="store_true",
                   help="lighter PSD files: no hidden 'Original photo' layer")
    p.add_argument("--no-original-copy", action="store_true",
                   help="do not copy the original photo into the result folder")
    p.add_argument("--no-control", action="store_true", help=f"do not write the {CONTROL_DIR} images")
    p.add_argument("-j", "--jobs", type=int, default=max(1, min(4, (os.cpu_count() or 2) // 2)),
                   help="number of photos processed in parallel")
    p.add_argument("--open", action="store_true", help="open the result folder(s) when done")
    p.add_argument("-v", "--verbose", action="store_true", help="print error details")
    opts = p.parse_args(argv)

    files = list_photos(opts.inputs)
    if not files:
        print("No photo to process.")
        return 1
    if opts.ai:
        try:
            import onnxruntime  # noqa: F401
        except ImportError:
            print("--ai needs the onnxruntime package. Install it once with:\n"
                  "  py -3 -m pip install onnxruntime-directml   (Windows: uses the graphics card)\n"
                  "  py -3 -m pip install onnxruntime            (processor only)")
            return 1
        try:
            ai_model_path(opts.ai_model)           # download it now, once, rather than in each worker
        except Exception as e:
            print(f"AI model not available: {e}")
            return 1
        device = ai_providers(opts.ai_device, opts.ai_model)[0].replace("ExecutionProvider", "")
        print(f"AI second opinion: {AI_MODELS[opts.ai_model][0]} ({'processor' if device == 'CPU' else device})")
    # result folder of each photo: forced (-o) or "outlined_result" next to the photo
    tasks = [(fp, os.path.abspath(opts.output) if opts.output else
              os.path.join(os.path.dirname(os.path.abspath(fp)), RESULT_DIR)) for fp in files]
    out_dirs = sorted({s for _, s in tasks})
    for s in out_dirs:
        os.makedirs(os.path.join(s, CONTROL_DIR), exist_ok=True)

    print(f"{len(files)} photo(s) -> {', '.join(out_dirs)}")
    plan = plan_names(tasks)                    # output names and information of the project
    previous = {fp: previous_output(fp, s) for fp, s in tasks}
    t0 = time.time()
    rows = []
    if opts.jobs > 1 and len(files) > 1:
        with ProcessPoolExecutor(max_workers=opts.jobs, initializer=_init_worker) as ex:
            futures = [ex.submit(process_photo, fp, opts, s, plan[fp]) for fp, s in tasks]
            for fu in as_completed(futures):
                row = fu.result()
                rows.append(row)
                print_row(row, len(rows), len(files))
    else:
        for fp, s in tasks:
            row = process_photo(fp, opts, s, plan[fp])
            rows.append(row)
            print_row(row, len(rows), len(files))

    remove_renamed(tasks, plan, previous)
    for s in out_dirs:
        write_report(os.path.join(s, REPORT_NAME),
                     [dict({k: r[k] for k in REPORT_FIELDS}, **r["_meta"]) for r in rows if r["_out_dir"] == s])
    n_ok = sum(1 for r in rows if r["status"] == "ok")
    n_check = sum(1 for r in rows if r["status"] == "to verify")
    print(f"\nDone in {time.time() - t0:.0f} s: {n_ok} ok, {n_check} to verify ({DOUBT_SUFFIX}), "
          f"{len(rows) - n_ok - n_check} failed, out of {len(rows)} photo(s).")
    print_summary(rows)
    for s in out_dirs:
        print(f"Results: {s}")
    if opts.open and hasattr(os, "startfile"):
        for s in out_dirs:
            os.startfile(s)
    return 0


def previous_output(path, out_dir):
    """Output name the photo had at its previous run (review data), or None."""
    try:
        with open(os.path.join(out_dir, REVIEW_DIR, os.path.splitext(os.path.basename(path))[0] + ".json"),
                  encoding="utf-8") as fh:
            return json.load(fh).get("output")
    except (OSError, ValueError, AttributeError):
        return None


def remove_renamed(tasks, plan, previous):
    """Files of a photo written under a former output name (the project name changed): removed, unless
    another photo now uses that name."""
    now = {(os.path.normcase(s), plan[fp]["base"].lower()) for fp, s in tasks}
    for fp, s in tasks:
        old = previous.get(fp)
        if not old or old == plan[fp]["base"] or (os.path.normcase(s), old.lower()) in now:
            continue
        for doubtful in (False, True):
            for f in output_paths(s, old, doubtful).values():
                if os.path.exists(f):
                    os.remove(f)


def write_report(report, rows):
    """CSV report (Excel: ";" separator, decimal comma). Rows already present for other
    photos are kept: the script can be run again on a few photos. The fields of the project come after
    the usual columns."""
    all_rows, extra = {}, []
    if os.path.exists(report):
        try:
            with open(report, newline="", encoding="utf-8-sig") as fh:
                rd = csv.DictReader(fh, delimiter=";")
                for r in rd:
                    r = {LEGACY_COLUMNS.get(k, k): v for k, v in r.items() if k is not None}
                    if r.get("file"):
                        all_rows[r["file"]] = {k: v for k, v in r.items() if k in REPORT_FIELDS or k not in LEGACY_COLUMNS.values()}
                extra = [k for k in (rd.fieldnames or []) if LEGACY_COLUMNS.get(k, k) not in REPORT_FIELDS
                         and LEGACY_COLUMNS.get(k, k) not in LEGACY_COLUMNS.values()]
        except Exception:
            pass
    for r in rows:
        all_rows[r["file"]] = {k: (str(v).replace(".", ",") if k in DECIMAL_FIELDS else v) for k, v in r.items()}
        extra += [k for k in r if k not in REPORT_FIELDS and k not in extra]
    with open(report, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.DictWriter(fh, fieldnames=REPORT_FIELDS + extra, delimiter=";", extrasaction="ignore")
        w.writeheader()
        for name in sorted(all_rows):
            w.writerow(all_rows[name])


def print_summary(rows):
    """What needs checking, grouped by problem, with the photos concerned (a photo may appear under
    several problems)."""
    groups = {}
    for r in sorted(rows, key=lambda r: r["file"]):
        reasons = [x.strip() for x in r["to_verify"].split(" ; ") if x.strip()]
        if r["status"] == "error":
            reasons.append("error: " + r["notes"])
        for reason in reasons:
            label = next((lab for lab, keys in PROBLEMS if any(k in reason for k in keys)), None)
            if label is None:
                label = "Error" if reason.startswith("error: ") else reason[:1].upper() + reason[1:]
            groups.setdefault(label, []).append(r["file"])
    if not groups:
        print("Nothing to check.")
        return
    print("To check:")
    order = [lab for lab, _ in PROBLEMS]
    for label in sorted(groups, key=lambda g: order.index(g) if g in order else len(order)):
        names = list(dict.fromkeys(groups[label]))
        shown = ", ".join(names[:12]) + (f", … (+{len(names) - 12})" if len(names) > 12 else "")
        print(f"  - {label} ({len(names)}): {shown}")


def print_row(row, i, n):
    """One line of progress for a photo: [i/n] name: status (scale, time) | doubts and notes."""
    info = (f"{row['scale_type']} {row['scale_length_cm']} cm, {row['px_per_cm']} px/cm"
            if row["scale_found"] == "yes" else "no scale")
    det = " | ".join(x for x in (row["to_verify"], row["notes"]) if x)
    print(f"[{i}/{n}] {row['file']}: {row['status']} ({info}, {row['duration_s']} s)"
          + (f" | {det}" if det else ""), flush=True)


def _own_console():
    """True when the program has a visible console to itself: .exe double-clicked, or folders dropped on it
    (not when the interface runs it, with its output redirected)."""
    try:
        import ctypes
        return (sys.stdin is not None and sys.stdin.isatty() and sys.stdout is not None and sys.stdout.isatty()
                and ctypes.windll.kernel32.GetConsoleProcessList((ctypes.c_uint * 4)(), 4) == 1)
    except Exception:
        return False


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()          # .exe version: the worker processes start here
    if getattr(sys, "frozen", False) and _own_console():
        try:
            code = main(sys.argv[1:] or ["--help"])
        except SystemExit as e:
            code = e.code
        try:
            input("\nPress Enter to close this window.")
        except EOFError:
            pass
        sys.exit(code)
    sys.exit(main())
