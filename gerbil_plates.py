#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerbil - plates: the outlined objects of a results folder laid out on pages at a chosen scale
(1:1, 1:2, 1:3...), written as SVG files that open in Illustrator or Inkscape.
© 2026 Eloïs CHARBONNEL
Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE.
This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to
redistribute it under the conditions of the licence.

Each object keeps its true size at the plate scale (read from the resolution of its _outlined.tif,
which is 1:1). The objects are placed in rows, in the chosen order, with a caption under each one
(its name, or the fields of the batch renaming) and a graphic scale bar on every page. The images are
embedded: an SVG file can be sent alone.

The page is first described as a list of shapes in millimetres (Drawing), then written as SVG or
drawn with Pillow for the preview of the interface: both always show the same thing.

Usage:  py -3 gerbil_plates.py RESULTS_FOLDER [--ratio 2] [--page A4] [--landscape] [-o FOLDER]
"""
import argparse
import base64
import csv
import hashlib
import itertools
import shutil
import subprocess
import tempfile
import io
import json
import math
import os
import re
import sys
from dataclasses import asdict, dataclass, field, fields as dc_fields, replace

from PIL import Image, ImageDraw, ImageFont

PAGES = {"A4": (210.0, 297.0), "A3": (297.0, 420.0), "A5": (148.0, 210.0), "Letter": (215.9, 279.4)}
PT = 25.4 / 72.0                      # one typographic point in mm
REPORT = "outlined_report.csv"
TIFF_SUFFIXES = ("_outlined.tif", "_outlined_to_be_verified.tif")
BAR_STYLES = ("single box", "double box", "line ticks up", "line ticks down", "line ticks middle",
              "stepped line", "hollow")
FONTS = {                              # family -> (regular, bold) font files of Windows, for the preview
    "Arial": ("arial.ttf", "arialbd.ttf"),
    "Calibri": ("calibri.ttf", "calibrib.ttf"),
    "Segoe UI": ("segoeui.ttf", "segoeuib.ttf"),
    "Verdana": ("verdana.ttf", "verdanab.ttf"),
    "Times New Roman": ("times.ttf", "timesbd.ttf"),
    "Georgia": ("georgia.ttf", "georgiab.ttf"),
    "Garamond": ("GARA.TTF", "GARABD.TTF"),
}


@dataclass
class ScaleBar:
    """Graphic scale bar, in the manner of the QGIS print layouts. Lengths in real centimetres,
    sizes on the paper in millimetres, text sizes in points."""
    style: str = "single box"
    length_cm: float = 0.0             # 0: chosen from the plate scale (1, 2, 5, 10, 20 or 50 cm)
    segments: int = 0                  # 0: one per cm up to 10 cm, otherwise 4 or 5
    subdivisions: int = 0              # the first segment cut in that many parts (e.g. 10 = millimetres)
    height_mm: float = 2.0
    line_mm: float = 0.2
    fill: str = "#000000"
    fill2: str = "#FFFFFF"
    line: str = "#000000"
    labels: str = "ends"               # "ends" (0 and the end), "all" (every segment), "none"
    label_position: str = "below"      # "below" or "above"
    unit: str = "cm"                   # written after the last number ("mm": numbers in millimetres)
    font: str = "Arial"
    font_pt: float = 7.0
    bold: bool = False
    font_color: str = "#000000"
    show_ratio: bool = False           # "1:2" written after the bar
    position: str = "bottom right"     # on the page: "bottom right", "bottom left", "bottom centre"


@dataclass
class PlateSettings:
    """All the settings of the plates (page, scale, captions, title, drawings, options) and the
    scale bar; saved as JSON (interface settings, plates_settings.json)."""
    ratio: float = 1.0                 # 1:ratio
    page: str = "A4"
    width_mm: float = 210.0            # page "custom"
    height_mm: float = 297.0
    landscape: bool = False
    margin_mm: float = 15.0
    gap_mm: float = 6.0                # between objects
    order: str = "name"                # "name" or a field of the report
    group: str = ""                    # a field: each value starts a new row (or a new page)
    group_new_page: bool = False
    caption: str = "{name}"            # {name} or {field} of the report; empty: no caption
    caption_font: str = "Arial"
    caption_pt: float = 8.0
    caption_color: str = "#000000"
    title: str = ""                    # top of each page; {page}, {pages}, {group}
    title_pt: float = 11.0
    title_align: str = "left"          # "left", "centre", "right"
    file_name: str = "plate_{page}"    # name of the SVG files; {page} (01, 02…), {pages}, {group}
    dpi: int = 600                     # resolution of the embedded images on the paper
    include_doubtful: bool = False     # also the _to_be_verified files
    fit_large: bool = True             # an object too large for the page at 1:ratio goes to 1:2, 1:3...
    object_ratios: dict = field(default_factory=dict)   # output name -> its own scale (1:r), chosen by hand
    by_material: bool = False          # scale of each object from its material (material_ratios)
    material_field: str = "Material"   # column of the report holding the material
    material_ratios: str = ("ceramic=1/3; céramique=1/3; pottery=1/3; glass=1/3; verre=1/3; "
                            "iron=2/3; fer=2/3; stone=1/3; pierre=1/3")   # publication reductions (DMS 2009)
    mix_scales: bool = False           # several scales on one plate (scale in the caption, one bar each)
    drawings_folder: str = ""          # drawings of the objects (.svg, .ai, .pdf, .eps), placed beside the photos
    drawings_match: str = "{name}"     # names of the drawings: {name} = output name, or fields ({site}_{number})
    drawings_ratio: float = 1.0        # the drawings are at 1:drawings_ratio on their paper
    drawings_side: str = "left"        # drawing on the left (or right) of the photo
    measurements: bool = False         # width and height of each object as guides, on a hidden layer
    measure_color: str = "#0096C8"
    bar: ScaleBar = field(default_factory=ScaleBar)

    @staticmethod
    def from_dict(d):
        """Settings rebuilt from a dictionary (saved settings); unknown keys
        ignored, so that older files still load."""
        d = dict(d or {})
        bar = ScaleBar(**{k: v for k, v in (d.pop("bar", None) or {}).items()
                          if k in {f.name for f in dc_fields(ScaleBar)}})
        s = PlateSettings(**{k: v for k, v in d.items() if k in {f.name for f in dc_fields(PlateSettings)}})
        s.bar = bar
        return s

    def to_dict(self):
        """Settings as a dictionary (to save them as JSON)."""
        return asdict(self)

    def page_size(self):
        """Width and height of the page in mm, turned for landscape."""
        w, h = (self.width_mm, self.height_mm) if self.page == "custom" else PAGES.get(self.page, PAGES["A4"])
        return (max(w, h), min(w, h)) if self.landscape else (min(w, h), max(w, h))


# --------------------------------------------------------------------------
# Objects of a results folder
# --------------------------------------------------------------------------

@dataclass
class Item:
    """An outlined object of a results folder: output name, TIFF file, real size (cm), row of
    the report, doubtful or not, box of the object in the TIFF, drawing found for it."""
    name: str                          # output name (file name without the suffix)
    path: str
    width_cm: float
    height_cm: float
    values: dict                       # row of the report (fields of the batch renaming included)
    doubtful: bool = False
    bbox: tuple = None                 # the object in the TIFF (pixels): its margins are left out
    drawing: dict = None               # drawing of the object (attach_drawings): svg file, real size


def natural_key(text):
    """Sort key where numbers count as numbers: "2" before "10"."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", str(text))]


def read_report(folder):
    """Rows of outlined_report.csv by output name (fields of the photos)."""
    try:
        with open(os.path.join(folder, REPORT), encoding="utf-8-sig", newline="") as fh:
            return {r.get("output_name") or os.path.splitext(r.get("file", ""))[0]: r
                    for r in csv.DictReader(fh, delimiter=";")}
    except OSError:
        return {}


def collect(folder, include_doubtful=False):
    """The outlined objects of a results folder, with their real size (from the TIFF resolution)."""
    report = read_report(folder)
    items = []
    for n in sorted(os.listdir(folder), key=natural_key):
        suffix = next((s for s in TIFF_SUFFIXES if n.endswith(s)), None)
        if suffix is None:
            continue
        doubtful = suffix != TIFF_SUFFIXES[0]
        if doubtful and not include_doubtful:
            continue
        path = os.path.join(folder, n)
        try:
            with Image.open(path) as im:
                dpi = (im.info.get("dpi") or (0, 0))[0]
                if not dpi or dpi <= 1:
                    continue               # no real size (no scale): not on a plate
                # the object itself, without the transparent margin of the TIFF (white background: all)
                bbox = (im.getchannel("A").getbbox() if "A" in im.getbands() else None) or (0, 0) + im.size
        except OSError:
            continue
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        name = n[:-len(suffix)]
        items.append(Item(name, path, w / dpi * 2.54, h / dpi * 2.54, report.get(name, {}), doubtful, bbox))
    return items


def field_value(item, key):
    """Value of a column of the report for the object: its exact name, else the same letters and digits
    (case, spaces and underscores aside), else a field of the batch renaming ending so ("number" for
    "Object number")."""
    if key in ("name", "output_name"):
        return item.name
    if key in item.values:
        return str(item.values.get(key) or "")
    k = re.sub(r"[^0-9a-z]", "", key.lower())
    cols = {re.sub(r"[^0-9a-z]", "", c.lower()): c for c in item.values}
    if k in cols:
        return str(item.values[cols[k]] or "")
    for c in list(item.values)[STANDARD_COLUMNS:]:
        if re.sub(r"[^0-9a-z]", "", c.lower()).endswith(k):
            return str(item.values[c] or "")
    return ""


STANDARD_COLUMNS = 19                  # columns of the report written by Gerbil itself (the fields follow)


def caption_text(template, item):
    """Caption of an object: the template with {field} replaced by its values."""
    if not template:
        return ""
    return re.sub(r"\{(\w+)\}", lambda m: field_value(item, m.group(1)), template).strip()


def report_fields(items):
    """Fields usable for the order, the groups and the captions."""
    keys = ["name"]
    for it in items:
        for k in it.values:
            if k not in keys and k not in ("file", "output_name", "notes", "duration_s"):
                keys.append(k)
    return keys


# --------------------------------------------------------------------------
# Drawing: shapes in millimetres, written as SVG or drawn with Pillow
# --------------------------------------------------------------------------

class Drawing:
    """A page described as shapes in millimetres, by layer: written as SVG (write_svg) or drawn
    with Pillow for the preview (render), so that both always show the same thing."""
    def __init__(self, width, height):
        """An empty page of width x height mm."""
        self.width, self.height = width, height
        self.layers = {}               # name -> list of shapes, in drawing order
        self.hidden = set()            # layers written hidden (shown on demand in Illustrator / Inkscape)

    def add(self, layer, *shape):
        """Adds a shape (a tuple: kind, coordinates in mm, style) to a layer."""
        self.layers.setdefault(layer, []).append(shape)


_font_cache = {}


def pil_font(family, size_px, bold=False):
    """A Pillow font of the family at a size in pixels (cached), for the preview and to
    measure texts."""
    key = (family, round(size_px), bold)
    if key not in _font_cache:
        files = FONTS.get(family, FONTS["Arial"])
        font = None
        for f in (files[1 if bold else 0], files[0], "arial.ttf"):
            try:
                font = ImageFont.truetype(f, max(1, round(size_px)))
                break
            except OSError:
                continue
        _font_cache[key] = font or ImageFont.load_default()
    return _font_cache[key]


def text_width_mm(text, family, pt, bold=False):
    """Width of a text on the paper (measured with the font at 100 px per mm)."""
    if not text:
        return 0.0
    f = pil_font(family, pt * PT * 100, bold)
    return f.getlength(text) / 100.0


def svg_escape(s):
    """Escapes a text for SVG / XML."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def num(v):
    """A number written short for SVG (3 decimals at most, no trailing zeros)."""
    return f"{v:.3f}".rstrip("0").rstrip(".")


def write_svg(drawing, path, layer_names=None):
    """Writes a Drawing as an SVG file in millimetres, one Inkscape / Illustrator layer per
    layer of the drawing, hidden layers hidden."""
    w, h = drawing.width, drawing.height
    out = [f'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
           f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
           f'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" version="1.1" '
           f'width="{num(w)}mm" height="{num(h)}mm" viewBox="0 0 {num(w)} {num(h)}">\n'
           f'<!-- Gerbil plate: units of the drawing = millimetres -->\n']
    for layer, shapes in drawing.layers.items():
        label = svg_escape((layer_names or {}).get(layer, layer))
        hide = ' style="display:none"' if layer in drawing.hidden else ""
        out.append(f'<g id="{svg_escape(layer)}" inkscape:groupmode="layer" inkscape:label="{label}"{hide}>\n')
        for s in shapes:
            out.append(svg_shape(s))
        out.append("</g>\n")
    out.append("</svg>\n")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("".join(out))


_svg_ids = itertools.count(1)


def svg_shape(s):
    """One shape of the drawing as SVG: rectangle, polygon / line, text, vertical text,
    image (PNG embedded in base64) or drawing (nested SVG)."""
    kind = s[0]
    if kind == "rect":
        _, x, y, w, h, fill, stroke, sw = s
        return (f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" '
                f'fill="{fill or "none"}" stroke="{stroke or "none"}" stroke-width="{num(sw)}"/>\n')
    if kind == "poly":
        _, pts, fill, stroke, sw, closed = s
        p = " ".join(f"{num(x)},{num(y)}" for x, y in pts)
        tag = "polygon" if closed else "polyline"
        return (f'<{tag} points="{p}" fill="{fill or "none"}" stroke="{stroke or "none"}" '
                f'stroke-width="{num(sw)}" stroke-linejoin="miter" stroke-linecap="square"/>\n')
    if kind == "text":
        _, x, y, text, family, pt, color, anchor, bold = s
        a = {"l": "start", "m": "middle", "r": "end"}[anchor]
        return (f'<text x="{num(x)}" y="{num(y)}" font-family="{svg_escape(family)}" '
                f'font-size="{num(pt * PT)}" fill="{color}" text-anchor="{a}"'
                + (' font-weight="bold"' if bold else "") + f'>{svg_escape(text)}</text>\n')
    if kind == "vtext":                    # text read from bottom to top, centred on (x, y) along it
        _, x, y, text, family, pt, color = s
        return (f'<text x="{num(x)}" y="{num(y)}" font-family="{svg_escape(family)}" font-size="{num(pt * PT)}" '
                f'fill="{color}" text-anchor="middle" transform="rotate(-90 {num(x)} {num(y)})">'
                f'{svg_escape(text)}</text>\n')
    if kind == "svgfile":                  # a drawing, kept as vectors: nested <svg>, its ids prefixed
        _, x, y, w, h, svg, title = s
        with open(svg, encoding="utf-8", errors="ignore") as fh:
            tag, inner = svg_root(fh.read())
        if tag is None:
            return ""
        attr = dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))
        vb = attr.get("viewBox")
        if not vb:
            sz = svg_size_mm(svg)
            vb = f"0 0 {num(sz[0] / UNITS_MM['px'])} {num(sz[1] / UNITS_MM['px'])}" if sz else None
        ns = " ".join(f'{k}="{v}"' for k, v in attr.items() if k.startswith("xmlns:"))
        pre = f"d{next(_svg_ids)}_"
        inner = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{pre}{m.group(1)}"', inner)
        inner = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{pre}{m.group(1)})", inner)
        inner = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{pre}{m.group(1)}"', inner)
        return (f'<svg x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"'
                + (f' viewBox="{vb}"' if vb else "") + f' preserveAspectRatio="xMidYMid meet" {ns}>'
                f'<title>{svg_escape(title)} (drawing)</title>{inner}</svg>\n')
    if kind == "image":
        _, x, y, w, h, img, title = s
        buf = io.BytesIO()
        img.save(buf, "PNG", compress_level=6)
        data = base64.b64encode(buf.getvalue()).decode("ascii")
        return (f'<image x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" '
                f'preserveAspectRatio="none" xlink:href="data:image/png;base64,{data}">'
                f'<title>{svg_escape(title)}</title></image>\n')
    raise ValueError(kind)


def render(drawing, px_per_mm, hidden=(), show_hidden=False):
    """The page as a Pillow image (preview); the hidden layers only with show_hidden."""
    W, H = max(1, round(drawing.width * px_per_mm)), max(1, round(drawing.height * px_per_mm))
    page = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(page)
    k = px_per_mm
    for layer, shapes in drawing.layers.items():
        if layer in hidden or (layer in drawing.hidden and not show_hidden):
            continue
        for s in shapes:
            kind = s[0]
            if kind == "rect":
                _, x, y, w, h, fill, stroke, sw = s
                box = [x * k, y * k, (x + w) * k, (y + h) * k]
                if fill:
                    d.rectangle(box, fill=fill)
                if stroke and sw > 0:
                    d.rectangle(box, outline=stroke, width=max(1, round(sw * k)))
            elif kind == "poly":
                _, pts, fill, stroke, sw, closed = s
                p = [(x * k, y * k) for x, y in pts]
                if closed and fill:
                    d.polygon(p, fill=fill)
                if stroke and sw > 0:
                    d.line(p + ([p[0]] if closed else []), fill=stroke, width=max(1, round(sw * k)), joint="curve")
            elif kind == "text":
                _, x, y, text, family, pt, color, anchor, bold = s
                d.text((x * k, y * k), text, fill=color, font=pil_font(family, pt * PT * k, bold),
                       anchor={"l": "ls", "m": "ms", "r": "rs"}[anchor])
            elif kind == "vtext":
                _, x, y, text, family, pt, color = s
                f = pil_font(family, pt * PT * k)
                tw = max(1, round(f.getlength(text)))
                asc, desc = f.getmetrics()
                tile = Image.new("RGBA", (tw, asc + desc), (255, 255, 255, 0))
                ImageDraw.Draw(tile).text((tw / 2, asc), text, fill=color, font=f, anchor="ms")
                tile = tile.rotate(90, expand=True)          # baseline at (x, y): the tile right of it
                page.paste(tile, (round(x * k - asc), round(y * k - tw / 2)), tile)
            elif kind == "svgfile":
                _, x, y, w, h, svg, _ = s
                png = drawing_png(svg, max(2.0, min(16.0, k * 1.5)))
                box = [x * k, y * k, (x + w) * k, (y + h) * k]
                if png:
                    with Image.open(png) as im:
                        im = im.convert("RGBA").resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
                    page.paste(im, (round(x * k), round(y * k)), im)
                else:
                    d.rectangle(box, outline="#8E84B8", width=1)
                    d.line([box[0], box[1], box[2], box[3]], fill="#C9C1E3")
            elif kind == "image":
                _, x, y, w, h, img, _ = s
                size = (max(1, round(w * k)), max(1, round(h * k)))
                small = img.resize(size, Image.LANCZOS) if img.size != size else img
                page.paste(small, (round(x * k), round(y * k)), small if small.mode == "RGBA" else None)
    return page


# --------------------------------------------------------------------------
# Scale bar
# --------------------------------------------------------------------------

NICE_LENGTHS = (1, 2, 5, 10, 20, 50, 100)


def bar_geometry(bar, ratio, max_mm):
    """Length (real cm) and segments of the bar: given, or chosen so that it stays under max_mm."""
    length = bar.length_cm
    if length <= 0:
        fitting = [n for n in NICE_LENGTHS if n * 10 / ratio <= max_mm]
        length = fitting[-1] if fitting else NICE_LENGTHS[0]
        length = min(length, 10) if ratio <= 1 else length
    n = bar.segments
    if n <= 0:
        n = int(round(length)) if length <= 10 and abs(length - round(length)) < 1e-6 else (
            4 if length in (20, 100) else 5)
    return float(length), max(1, int(n))


def fmt(v):
    """A number written without useless decimals (3, 1.5)."""
    return str(int(round(v))) if abs(v - round(v)) < 1e-6 else f"{v:g}"


def draw_bar(dr, bar, ratio, x0, y0, max_mm, layer="Scale bar"):
    """Draws the bar with its top-left corner at (x0, y0) (labels included). Returns (width, height)."""
    length, n = bar_geometry(bar, ratio, max_mm)
    L = length * 10.0 / ratio                  # paper length (mm)
    seg = L / n
    h, lw = bar.height_mm, bar.line_mm
    text_h = bar.font_pt * PT
    label_gap = 0.8
    above = bar.label_position == "above" and bar.labels != "none"
    yb = y0 + (text_h + label_gap if above else 0.0)          # top of the bar
    # boundaries: the first segment subdivided if wanted
    edges = [i * seg for i in range(n + 1)]
    sub = [j * seg / bar.subdivisions for j in range(bar.subdivisions + 1)] if bar.subdivisions > 1 else []
    # cells (start, end, colour index): the subdivisions of the first segment alternate among themselves,
    # the next segments keep the colours they have without subdivisions
    cells = ([(sub[j], sub[j + 1], j) for j in range(len(sub) - 1)] if sub else [(0.0, edges[1], 0)])
    cells += [(edges[i], edges[i + 1], i) for i in range(1, n)]
    st = bar.style
    if st in ("single box", "hollow"):
        for a, b, i in cells:
            dr.add(layer, "rect", x0 + a, yb, b - a, h, bar.fill2, None, 0)
            if i % 2 == 0:
                if st == "single box":
                    dr.add(layer, "rect", x0 + a, yb, b - a, h, bar.fill, None, 0)
                else:                                          # hollow: half-height band
                    dr.add(layer, "rect", x0 + a, yb + h / 4, b - a, h / 2, bar.fill, None, 0)
        for a, b, _ in cells:
            dr.add(layer, "rect", x0 + a, yb, b - a, h, None, bar.line, lw)
    elif st == "double box":
        for a, b, i in cells:
            top, bottom = (bar.fill, bar.fill2) if i % 2 == 0 else (bar.fill2, bar.fill)
            dr.add(layer, "rect", x0 + a, yb, b - a, h / 2, top, None, 0)
            dr.add(layer, "rect", x0 + a, yb + h / 2, b - a, h / 2, bottom, None, 0)
        for a, b, _ in cells:
            dr.add(layer, "rect", x0 + a, yb, b - a, h / 2, None, bar.line, lw)
            dr.add(layer, "rect", x0 + a, yb + h / 2, b - a, h / 2, None, bar.line, lw)
    elif st.startswith("line ticks"):
        ticks = sorted({a for a, _, _ in cells} | {L})
        if st == "line ticks up":
            base, t0, t1 = yb + h, yb + h, yb
        elif st == "line ticks down":
            base, t0, t1 = yb, yb, yb + h
        else:
            base, t0, t1 = yb + h / 2, yb, yb + h
        dr.add(layer, "poly", [(x0, base), (x0 + L, base)], None, bar.line, lw, False)
        for t in ticks:
            if any(abs(t - e) < 1e-9 for e in edges):         # segment: full tick
                a, b = t0, t1
            elif st == "line ticks middle":                  # subdivision: half tick
                a, b = base - h / 4, base + h / 4
            else:
                a, b = base, base + (t1 - t0) / 2
            dr.add(layer, "poly", [(x0 + t, a), (x0 + t, b)], None, bar.line, lw, False)
    elif st == "stepped line":
        pts = [(x0, yb + h)]
        for a, b, i in cells:
            y = yb if i % 2 == 0 else yb + h
            pts += [(x0 + a, y), (x0 + b, y)]
        pts.append((x0 + L, yb + h))
        dr.add(layer, "poly", pts, None, bar.line, lw, False)
    # labels (real values)
    width = L
    if bar.labels != "none":
        ty = (y0 + text_h) if above else (yb + h + label_gap + text_h * 0.8)
        places = [0.0, L] if bar.labels == "ends" else edges
        if bar.labels == "all" and sub:
            places = sorted(set(edges) | {sub[-1]})
        for p in places:
            value = p * ratio / 10.0 * (10.0 if bar.unit.strip() == "mm" else 1.0)
            text = fmt(value) + (f" {bar.unit}" if p == places[-1] and bar.unit else "")
            # the unit does not shift the number: the number stays centred on its tick
            if p == places[-1] and bar.unit:
                wnum = text_width_mm(fmt(value), bar.font, bar.font_pt, bar.bold)
                dr.add(layer, "text", x0 + p - wnum / 2, ty, text, bar.font, bar.font_pt, bar.font_color, "l", bar.bold)
                width = max(width, p + wnum / 2 + text_width_mm(" " + bar.unit, bar.font, bar.font_pt, bar.bold))
            else:
                dr.add(layer, "text", x0 + p, ty, text, bar.font, bar.font_pt, bar.font_color, "m", bar.bold)
    if bar.show_ratio:
        r = f"1:{fmt(ratio)}"
        tx = x0 + width + 2.5
        dr.add(layer, "text", tx, yb + h / 2 + text_h * 0.35, r, bar.font, bar.font_pt, bar.font_color, "l", bar.bold)
        width = width + 2.5 + text_width_mm(r, bar.font, bar.font_pt, bar.bold)
    height = h + (text_h + label_gap if bar.labels != "none" else 0) + (text_h * 0.25 if not above else 0)
    return width, height


def bar_size(bar, ratio, max_mm):
    """Width and height of a scale bar, measured by drawing it on an empty page."""
    probe = Drawing(1, 1)
    return draw_bar(probe, bar, ratio, 0, 0, max_mm)


# --------------------------------------------------------------------------
# Drawings (vector: SVG, or .ai / .pdf / .eps converted by Inkscape)
# --------------------------------------------------------------------------

DRAWING_EXTS = (".svg", ".ai", ".pdf", ".eps")
GERBIL_SUFFIX = r"(_outlined(_scale)?|_to_control)?(_to_be_verified)?(_thumb)?$"
UNITS_MM = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72, "pc": 25.4 / 6, "px": 25.4 / 96, "": 25.4 / 96}
_cache_dir = os.path.join(tempfile.gettempdir(), "gerbil_drawings")


def inkscape():
    """Inkscape command line, if installed (converts .ai / .pdf / .eps and renders the previews)."""
    for c in (shutil.which("inkscape"), r"C:\Program Files\Inkscape\bin\inkscape.exe",
              r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe", "/Applications/Inkscape.app/Contents/MacOS/inkscape"):
        if c and os.path.isfile(c):
            return c
    return None


def _cached(path, ext):
    """Path of a file in the cache of drawings, named from the source path, size and date
    (a changed drawing is converted again)."""
    st = os.stat(path)
    key = hashlib.sha1(f"{os.path.abspath(path)}|{st.st_size}|{st.st_mtime}".encode()).hexdigest()[:16]
    os.makedirs(_cache_dir, exist_ok=True)
    return os.path.join(_cache_dir, key + ext)


def drawing_svg(path):
    """SVG of a drawing: the file itself, or its conversion by Inkscape (cached). None if impossible."""
    if path.lower().endswith(".svg"):
        return path
    out = _cached(path, ".svg")
    if not os.path.exists(out):
        exe = inkscape()
        if not exe:
            return None
        subprocess.run([exe, path, "--export-type=svg", "--export-plain-svg", f"--export-filename={out}"],
                       capture_output=True, timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return out if os.path.exists(out) else None


def drawing_png(svg, px_per_mm=8.0):
    """Raster of a drawing for the preview (Inkscape, cached), or None."""
    out = _cached(svg, f"_{px_per_mm:g}.png")
    if not os.path.exists(out):
        exe = inkscape()
        if not exe:
            return None
        subprocess.run([exe, svg, "--export-type=png", f"--export-dpi={px_per_mm * 25.4:.0f}",
                        "--export-background-opacity=0", f"--export-filename={out}"],
                       capture_output=True, timeout=180, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return out if os.path.exists(out) else None


def _length_mm(value):
    """An SVG length ("12.5mm", "300pt", "800") in mm (pixels at 96 per inch)."""
    m = re.match(r"\s*([0-9.]+)\s*([a-z%]*)", value or "")
    if not m or m.group(2) == "%":
        return None
    return float(m.group(1)) * UNITS_MM.get(m.group(2), UNITS_MM["px"])


def svg_root(text):
    """(start tag of the root <svg>, inner content) of an SVG document."""
    m = re.search(r"<svg\b[^>]*>", text)
    end = text.rfind("</svg>")
    return (m.group(0), text[m.end():end]) if m and end > m.end() else (None, None)


def svg_size_mm(svg):
    """Width and height of the drawing on its paper (mm), from the root width / height (else viewBox at
    96 px per inch)."""
    with open(svg, encoding="utf-8", errors="ignore") as fh:
        tag, _ = svg_root(fh.read())
    if not tag:
        return None
    attr = dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))
    w, h = _length_mm(attr.get("width")), _length_mm(attr.get("height"))
    if (w is None or h is None) and attr.get("viewBox"):
        vb = [float(v) for v in re.split(r"[\s,]+", attr["viewBox"].strip())]
        w, h = vb[2] * UNITS_MM["px"], vb[3] * UNITS_MM["px"]
    return (w, h) if w and h else None


def norm(text):
    """A value compared without case, spaces, punctuation or leading zeros ("0187" = "187")."""
    return re.sub(r"[^0-9a-z]", "", str(text).lower()).lstrip("0") or "0"


def attach_drawings(items, s):
    """Each object gets the drawing of the same object found in s.drawings_folder: a drawing whose name
    (Gerbil's suffixes left out) is the output name (template "{name}"), or whose fields, read with the
    template (e.g. {site}_{number}), are those of the object (leading zeros ignored)."""
    for it in items:
        it.drawing = None
    folder = s.drawings_folder.strip()
    if not folder or not os.path.isdir(folder):
        return
    template = s.drawings_match.strip() or "{name}"
    rx = None
    if template != "{name}":
        parts, pos = [], 0
        for m in re.finditer(r"\{(\w+)\}", template):
            parts.append(re.escape(template[pos:m.start()]) + f"(?P<{m.group(1)}>.+?)")
            pos = m.end()
        rx = re.compile("^" + "".join(parts) + re.escape(template[pos:]) + "$", re.IGNORECASE)
    drawings = []
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if f.lower().endswith(DRAWING_EXTS):
                stem = re.sub(GERBIL_SUFFIX, "", os.path.splitext(f)[0], count=1)
                if rx is None:
                    drawings.append((os.path.join(root, f), {"name": norm(stem)}))
                elif (m := rx.match(stem)):
                    drawings.append((os.path.join(root, f), {k: norm(v) for k, v in m.groupdict().items()}))
    for it in items:
        for path, keys in drawings:
            if all(norm(field_value(it, k)) == v for k, v in keys.items()):
                svg = drawing_svg(path)
                size = svg_size_mm(svg) if svg else None
                if size:
                    it.drawing = {"path": path, "svg": svg, "width_cm": size[0] / 10 * s.drawings_ratio,
                                  "height_cm": size[1] / 10 * s.drawings_ratio}
                break


# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------

@dataclass
class Placed:
    """An object placed on a plate: its photo (x, y, w, h in mm), caption, scale, drawing box
    and the box of photo + drawing."""
    item: Item
    x: float                           # the photo
    y: float
    w: float
    h: float
    caption: str
    ratio: float = 1.0                 # scale of the object (1:ratio)
    draw: tuple = None                 # the drawing (x, y, w, h), beside the photo
    box: tuple = None                  # photo + drawing (x0, y0, x1, y1): the caption goes under it


def sort_items(items, s):
    """Objects sorted by group, then by the order field, then by name."""
    keys = [k for k in (s.group, s.order) if k]
    return sorted(items, key=lambda it: [natural_key(field_value(it, k)) for k in keys] + [natural_key(it.name)])


RATIOS = (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 15, 20)   # usual plate scales (1:r)


def page_room(s):
    """Width and height (mm) an object and its caption may take on a page of these settings."""
    W, H = s.page_size()
    cw = W - 2 * s.margin_mm
    title_h = s.title_pt * PT * 1.6 if s.title else 0.0
    bar_h = bar_size(s.bar, s.ratio, 0.3 * cw)[1]
    cap_h = s.caption_pt * PT * 1.5 if s.caption else 0.0
    return cw, H - 2 * s.margin_mm - title_h - bar_h - s.gap_mm - (5.0 if s.measurements else 0.0) - cap_h


def parse_ratio(text):
    """'1/3', '1:3', '3' -> 3 (plate scale 1:3); '2/3' -> 1.5."""
    t = str(text).strip().replace(",", ".")
    try:
        if "/" in t or ":" in t:
            a, b = re.split(r"[/:]", t, maxsplit=1)
            return float(b) / float(a)
        return float(t)
    except (ValueError, ZeroDivisionError):
        return None


def material_ratio(item, s):
    """Scale given by the material of the object (s.material_ratios: 'word=1/3; …', the word found in
    the material), or None."""
    mat = field_value(item, s.material_field).lower()
    if not mat:
        return None
    for rule in re.split(r"[;\n]+", s.material_ratios or ""):
        if "=" in rule:
            word, value = rule.split("=", 1)
            r = parse_ratio(value)
            if word.strip().lower() and word.strip().lower() in mat and r:
                return r
    return None


def object_mm(item, r, s):
    """Size on the paper of an object at 1:r (photo, and its drawing beside it): (width, height, photo
    width, photo height, drawing width, drawing height) in mm."""
    wp, hp = item.width_cm * 10 / r, item.height_cm * 10 / r
    if not item.drawing:
        return wp, hp, wp, hp, 0.0, 0.0
    wd, hd = item.drawing["width_cm"] * 10 / r, item.drawing["height_cm"] * 10 / r
    return wp + wd + s.gap_mm / 2, max(hp, hd), wp, hp, wd, hd


def object_ratio(item, s):
    """Scale of an object: the one chosen for it, else the one of its material (by_material), else the
    plate scale - and, when it does not fit on the page (fit_large), the first usual scale at which it
    does."""
    if item.name in (s.object_ratios or {}):
        return float(s.object_ratios[item.name])
    r0 = (material_ratio(item, s) if s.by_material else None) or s.ratio
    if not s.fit_large:
        return float(r0)
    for r in [r0] + [r for r in RATIOS if r > r0]:
        cw, ch = page_room(replace(s, ratio=r))
        w, h = object_mm(item, r, s)[:2]
        if w <= cw and h <= ch:
            return float(r)
    return float(RATIOS[-1])


def layout(items, s):
    """Pages of placed objects, one scale per page: the objects at the plate scale first, then those
    reduced (too large, or a scale chosen for them), each scale on its own pages with its own bar.
    Returns (pages, warnings); a page is (group, [Placed], ratio)."""
    attach_drawings(items, s)
    if s.mix_scales:                        # several scales on one plate: the scale in each caption
        ratios = {it.name: object_ratio(it, s) for it in items}
        p, w = layout_one(items, s, lambda it: ratios[it.name], bars=len(set(ratios.values())))
        return [(g, placed, s.ratio) for g, placed in p], w
    by_ratio = {}
    for it in items:
        by_ratio.setdefault(object_ratio(it, s), []).append(it)
    pages, warnings = [], []
    for r in sorted(by_ratio):
        base = {it.name: (material_ratio(it, s) if s.by_material else None) or s.ratio for it in by_ratio[r]}
        names = [it.name for it in by_ratio[r] if it.name not in (s.object_ratios or {}) and r != base[it.name]]
        if names:
            warnings.append(f"{len(names)} object(s) too large for the page: shown at 1:{fmt(r)}")
        p, w = layout_one(by_ratio[r], replace(s, ratio=r))
        pages += [(g, placed, r) for g, placed in p]
        warnings += w
    return pages, warnings


def layout_one(items, s, ratio_of=None, bars=1):
    """Pages of placed objects at one scale (or at the scale ratio_of gives each, the scale then written
    in the captions; `bars` scale bars stacked at the bottom): rows filled from left to right, centred,
    the images of a row aligned on their bottom edge, the drawing beside the photo, captions under them.
    Returns (pages, warnings); a page is (group, [Placed])."""
    W, H = s.page_size()
    m = s.margin_mm
    cw = W - 2 * m
    title_h = s.title_pt * PT * 1.6 if s.title else 0.0
    bar_w, bar_h = bar_size(s.bar, s.ratio, 0.3 * cw)
    top, bottom = m + title_h, H - m - bars * bar_h - (bars - 1) * 2.0 - s.gap_mm
    if s.measurements:
        top += 5.0                         # room for the width guides of the first row
    cap_h = s.caption_pt * PT * 1.5 if s.caption else 0.0
    pages, warnings = [], []
    rows, row, row_w = [], [], 0.0         # rows of the current page

    def row_height(r):
        return max(p[2] for p in r) + cap_h if r else 0.0

    def flush_page(group):
        nonlocal rows
        if rows:
            pages.append((group, place_rows(rows)))
        rows = []

    def place_rows(rs):
        placed, y = [], top
        for r in rs:
            rh = max(p[2] for p in r)
            total = sum(max(p[1], p[3]) for p in r) + s.gap_mm * (len(r) - 1)
            x = m + (cw - total) / 2
            for it, w, h, cap_w, cap, ratio, wp, hp, wd, hd in r:
                cell = max(w, cap_w)
                x0, yb = x + (cell - w) / 2, y + rh             # the pair, bottom-aligned
                if wd:
                    left = s.drawings_side != "right"
                    dx = x0 if left else x0 + wp + s.gap_mm / 2
                    px = x0 + wd + s.gap_mm / 2 if left else x0
                    placed.append(Placed(it, px, yb - hp, wp, hp, cap, ratio, (dx, yb - hd, wd, hd),
                                         (x0, yb - h, x0 + w, yb)))
                else:
                    placed.append(Placed(it, x0, yb - h, w, h, cap, ratio, None, (x0, yb - h, x0 + w, yb)))
                x += cell + s.gap_mm
            y += rh + cap_h + s.gap_mm
        return placed

    def used_height(rs):
        return sum(row_height(r) for r in rs) + s.gap_mm * max(0, len(rs) - 1)

    group = None
    for it in sort_items(items, s):
        g = field_value(it, s.group) if s.group else ""
        if s.group and g != group and group is not None:
            if row:
                rows.append(row)
            row, row_w = [], 0.0
            if s.group_new_page:
                flush_page(group)
        group = g
        ratio = ratio_of(it) if ratio_of else s.ratio
        w, h, wp, hp, wd, hd = object_mm(it, ratio, s)
        cap = caption_text(s.caption, it)
        if ratio_of and ratio != s.ratio:
            cap = (cap + " " if cap else "") + f"(1:{fmt(ratio)})"
        cap_w = text_width_mm(cap, s.caption_font, s.caption_pt)
        cell = max(w, cap_w)
        if w > cw or h + cap_h > bottom - top:
            warnings.append(f"{it.name}: larger than the page at 1:{fmt(s.ratio)}")
        entry = (it, w, h, cap_w, cap, ratio, wp, hp, wd, hd)
        if row and row_w + s.gap_mm + cell > cw:          # row full
            rows.append(row)
            row, row_w = [], 0.0
        if not row and rows and used_height(rows) + s.gap_mm + h + cap_h > bottom - top:
            flush_page(group)                              # page full
        if row:
            trial = rows + [row + [entry]]
            if used_height(trial) > bottom - top:          # the row grows too high for the page
                rows.append(row)
                row, row_w = [], 0.0
                flush_page(group)
        row.append(entry)
        row_w += (s.gap_mm if len(row) > 1 else 0.0) + cell
    if row:
        rows.append(row)
    flush_page(group)
    return pages, warnings


def load_image(item, w_mm, h_mm, dpi):
    """The object image at `dpi` on the paper (never enlarged)."""
    with Image.open(item.path) as im:
        im = im.convert("RGBA")
        if item.bbox:
            im = im.crop(item.bbox)
        target = (max(1, round(w_mm / 25.4 * dpi)), max(1, round(h_mm / 25.4 * dpi)))
        return im.resize(target, Image.LANCZOS) if target[0] < im.width else im.copy()


def page_drawing(s, page, number, total, images=True, dpi=None):
    """Drawing of one page. images: True (files read at the plate dpi), False (grey boxes) or a function
    (item, w_mm, h_mm) -> image (the interface gives its cached thumbnails)."""
    group, placed, *rest = page
    if rest:
        s = replace(s, ratio=rest[0])              # the scale of this page (bar, {scale})
    W, H = s.page_size()
    m = s.margin_mm
    dr = Drawing(W, H)
    dpi = dpi or s.dpi
    for p in placed:
        if images:
            im = images(p.item, p.w, p.h) if callable(images) else load_image(p.item, p.w, p.h, dpi)
            dr.add("Objects", "image", p.x, p.y, p.w, p.h, im, p.item.name)
        else:
            dr.add("Objects", "rect", p.x, p.y, p.w, p.h, "#D8D2EA", "#8E84B8", 0.2)
        if p.draw:
            dr.add("Drawings", "svgfile", *p.draw, p.item.drawing["svg"], p.item.name)
        x0, _, x1, y1 = p.box or (p.x, p.y, p.x + p.w, p.y + p.h)
        if p.caption:
            dr.add("Captions", "text", (x0 + x1) / 2, y1 + s.caption_pt * PT * 1.25, p.caption,
                   s.caption_font, s.caption_pt, s.caption_color, "m", False)
        if s.measurements:
            draw_measures(dr, p, s.measure_color, s.caption_font)
    if s.title:
        t = plate_text(s.title, number, total, group, scale=s.ratio)
        a = {"centre": "m", "right": "r"}.get(s.title_align, "l")
        tx = {"m": W / 2, "r": W - m}.get(a, m)
        dr.add("Title", "text", tx, m + s.title_pt * PT, t, s.caption_font, s.title_pt, s.caption_color, a, True)
    cw = W - 2 * m
    ratios = sorted({p.ratio for p in placed}) if s.mix_scales and placed else [s.ratio]
    bar = replace(s.bar, show_ratio=True) if len(ratios) > 1 else s.bar      # one bar per scale, named
    y = H - m
    for r in reversed(ratios):
        bw, bh = bar_size(bar, r, 0.3 * cw)
        pos = bar.position
        bx = m if pos == "bottom left" else (m + (cw - bw) / 2 if pos == "bottom centre" else W - m - bw)
        draw_bar(dr, bar, r, bx, y - bh, 0.3 * cw)
        y -= bh + 2.0
    dr.hidden.add(MEASURES)
    return dr


MEASURES = "Measurements"


def draw_measures(dr, p, color, font, pt=6.0, off=2.5, tick=1.0, lw=0.15):
    """Width and height of the object (real cm, as it lies on the plate) as dimension lines, above and on
    the left of it, on the hidden "Measurements" layer: layout guides, not data."""
    x0, y0, x1, y1 = p.x, p.y, p.x + p.w, p.y + p.h
    y = y0 - off
    dr.add(MEASURES, "poly", [(x0, y), (x1, y)], None, color, lw, False)
    for x in (x0, x1):
        dr.add(MEASURES, "poly", [(x, y - tick), (x, y + tick)], None, color, lw, False)
    dr.add(MEASURES, "text", (x0 + x1) / 2, y - 0.8, f"{p.item.width_cm:.1f} cm", font, pt, color, "m", False)
    x = x0 - off
    dr.add(MEASURES, "poly", [(x, y0), (x, y1)], None, color, lw, False)
    for yy in (y0, y1):
        dr.add(MEASURES, "poly", [(x - tick, yy), (x + tick, yy)], None, color, lw, False)
    dr.add(MEASURES, "vtext", x - 0.8, (y0 + y1) / 2, f"{p.item.height_cm:.1f} cm", font, pt, color)


def plate_text(template, number, total, group, pad=False, scale=None):
    """Title or file name of a plate: {page}, {pages}, {group} and {scale} replaced (page on 2 digits
    and scale written 1-2 for files, 1:2 in a title)."""
    page = f"{number:02d}" if pad else str(number)
    sc = "" if scale is None else ("1-" if pad else "1:") + fmt(scale)
    return (template.replace("{page}", page).replace("{pages}", str(total)).replace("{group}", group or "")
            .replace("{scale}", sc))


BAD_CHARS = set('<>:"/|?*' + chr(92))     # not allowed in a Windows file name


def plate_file_names(s, pages):
    """File names of the plates (without folder): from the template, the characters not allowed in a
    Windows file name replaced by "_"; the page number added when the template has none."""
    names, seen = [], set()
    for i, (group, _, *rest) in enumerate(pages, 1):
        template = s.file_name.strip() or "plate_{page}"
        if "{page}" not in template and len(pages) > 1 and "{group}" not in template:
            template += "_{page}"
        n = plate_text(template, i, len(pages), group, True, rest[0] if rest else s.ratio)
        n = "".join("_" if c in BAD_CHARS or ord(c) < 32 else c for c in n).strip(" .")
        n = n or f"plate_{i:02d}"
        base, k = n, 2
        while n.lower() in seen:               # two plates of the same group: numbered
            n, k = f"{base}_{k}", k + 1
        seen.add(n.lower())
        names.append(n + ".svg")
    return names


LAYER_NAMES = {"Objects": "Objects", "Drawings": "Drawings", "Captions": "Captions", "Title": "Title",
               "Scale bar": "Scale bar",
               MEASURES: "Measurements (guides)"}


def write_plates(folder, s, out_dir=None, progress=None):
    """Writes plate_01.svg, plate_02.svg... Returns (list of files, warnings)."""
    items = collect(folder, s.include_doubtful)
    if not items:
        return [], ["no outlined object with a real size in this folder"]
    pages, warnings = layout(items, s)
    out_dir = out_dir or os.path.join(folder, "plates")
    os.makedirs(out_dir, exist_ok=True)
    files = []
    names = plate_file_names(s, pages)
    for i, page in enumerate(pages, 1):
        if progress:
            progress(i - 1, len(pages))
        path = os.path.join(out_dir, names[i - 1])
        write_svg(page_drawing(s, page, i, len(pages)), path, LAYER_NAMES)
        files.append(path)
    if progress:
        progress(len(pages), len(pages))
    with open(os.path.join(out_dir, "plates_settings.json"), "w", encoding="utf-8") as fh:
        json.dump(s.to_dict(), fh, indent=1, ensure_ascii=False)
    return files, warnings


def main(argv=None):
    """Command line of the plates: options or a settings file, then write_plates."""
    p = argparse.ArgumentParser(description="Gerbil plates: outlined objects laid out at a chosen scale (SVG).")
    p.add_argument("folder", help="results folder (outlined_result)")
    p.add_argument("-o", "--output", help="folder of the plates (default: FOLDER/plates)")
    p.add_argument("--ratio", type=float, default=1.0, help="plate scale 1:RATIO")
    p.add_argument("--page", default="A4", choices=list(PAGES) + ["custom"])
    p.add_argument("--size", help="custom page size in mm, WxH")
    p.add_argument("--landscape", action="store_true")
    p.add_argument("--caption", default="{name}", help="caption template ({name} or a report column)")
    p.add_argument("--title", default="", help="title of each plate ({page}, {pages}, {group})")
    p.add_argument("--name", default="plate_{page}", help="name of the SVG files ({page}, {pages}, {group})")
    p.add_argument("--order", default="name")
    p.add_argument("--group", default="")
    p.add_argument("--dpi", type=int, default=600)
    p.add_argument("--doubtful", action="store_true", help="include the _to_be_verified files")
    p.add_argument("--measurements", action="store_true",
                   help="width and height of each object as guides, on a hidden layer")
    p.add_argument("--settings", help="JSON file of plate settings (as written in plates_settings.json)")
    a = p.parse_args(argv)
    if a.settings:
        with open(a.settings, encoding="utf-8") as fh:
            s = PlateSettings.from_dict(json.load(fh))
    else:
        s = PlateSettings(ratio=a.ratio, page=a.page, landscape=a.landscape, caption=a.caption, order=a.order,
                          group=a.group, dpi=a.dpi, include_doubtful=a.doubtful, measurements=a.measurements,
                          title=a.title, file_name=a.name)
        if a.size:
            s.page = "custom"
            s.width_mm, s.height_mm = (float(v) for v in a.size.lower().split("x"))
    files, warnings = write_plates(a.folder, s, a.output, lambda i, n: print(f"plate {i}/{n}", flush=True))
    for w in warnings:
        print("warning:", w)
    print(f"{len(files)} plate(s)" + (f" in {os.path.dirname(files[0])}" if files else ""))
    return 0 if files else 1


if __name__ == "__main__":
    sys.exit(main())
