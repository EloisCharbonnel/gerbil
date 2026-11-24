#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerbil - conversion of RAW photos to DNG, with their metadata and new names (the "Convert RAW to DNG" protocol
of the MAFKF / QSR mission, by Eloïs Charbonnel, brought into Gerbil).
© 2026 Eloïs CHARBONNEL
Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE.

For every RAW photo given (or of the folders given, sub-folders included):
  1. shooting date read from the EXIF (ExifTool; otherwise the date of the file);
  2. conversion to DNG by Adobe DNG Converter (free, installed separately) with the settings of the protocol
     (DNG 1.7, uncompressed, medium preview, fast load data, original RAW embedded), under the output name
     of the batch renaming of its folder (given by the interface, GERBIL_PROJECTS, or a gerbil_project.json),
     in <folder>\\<date>\\DNG\\<sub-folders>;
  3. the XMP sidecar next to the RAW (IMG.xmp or IMG.CR3.xmp: development settings, technical data of the
     camera, keywords already given) embedded in the DNG;
  4. the information of the batch renaming written into the DNG as IPTC (XMP): a field given in Gerbil
     replaces the one of the sidecar, the keywords are added to those already there; the RAW and the values
     given are also kept in the DNG (XMP "gerbil"), so that nothing is written next to the photos;
  5. a JPG (the ~1024 px preview of the DNG, or developed at full size) and, if asked, a 16-bit TIFF, with the
     same metadata, in <date>\\JPG and <date>\\TIFF;
  6. a CSV report at the root of the folder.
The RAW files are never modified. Running again only does what is missing: a DNG already there is found by
the RAW it carries, renamed if its name changed, and its metadata written again when the values or the
sidecar changed. Fields left empty are only mentioned ("not mentioned"), required ones are doubts.

Usage:
  py -3 gerbil.py --dng FOLDER_OR_RAW [...] [--jpg preview|full|none] [--tiff]
  py -3 gerbil_dng.py FOLDER_OR_RAW [...] [--jpg ...] [--tiff] [--converter PATH] [--exiftool PATH]
"""
import argparse
import csv
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import time

import gerbil as g

RAW_EXT = {".cr2", ".cr3", ".crw", ".arw", ".srf", ".sr2", ".nef", ".nrw", ".raf", ".orf", ".rw2", ".pef", ".srw",
           ".3fr", ".fff", ".iiq", ".rwl", ".x3f", ".erf", ".mrw", ".dcr", ".kdc", ".mos", ".mef", ".raw", ".gpr",
           ".dng"}
# settings of the protocol: DNG 1.7 compatibility, uncompressed, medium JPEG preview, fast load data,
# original RAW embedded
DNG_SETTINGS = ["-dng1.7", "-u", "-p1", "-fl", "-e"]
# folders written by the conversion (and by ExifTool), left out of the search: <date>\DNG, <date>\JPG
OUTPUT_DIRS = re.compile(r"^(DNG|\d{4}-\d{2}-\d{2}[\\/](DNG|JPG|TIFF)|exiftool_files|exiftool-[^\\/]*)([\\/]|$)",
                         re.I)
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# Nothing is kept next to the photos: each DNG carries, in its own XMP (namespace "gerbil"), the RAW it comes from
# and the values given in Gerbil, so that a run finds it again (renamed when its name changed, metadata written
# again when the values changed) and the batch renaming can be read back from the DNG files.
EXIFTOOL_CONFIG = r"""%Image::ExifTool::UserDefined = (
    'Image::ExifTool::XMP::Main' => {
        gerbil => { SubDirectory => { TagTable => 'Image::ExifTool::UserDefined::gerbil' } },
    },
);
%Image::ExifTool::UserDefined::gerbil = (
    GROUPS => { 0 => 'XMP', 1 => 'XMP-gerbil', 2 => 'Image' },
    NAMESPACE => { 'gerbil' => 'https://github.com/EloisCharbonnel/gerbil/ns/1.0/' },
    WRITABLE => 'string',
    GerbilSource => { },
    GerbilFields => { },
);
1;
"""

# IPTC fields of the project -> ExifTool tags (XMP, read by Bridge, Lightroom and the Explorer)
EXIF_TAGS = {
    "title": "XMP-dc:Title", "headline": "XMP-photoshop:Headline", "description": "XMP-dc:Description",
    "creator": "XMP-dc:Creator", "date": "XMP-photoshop:DateCreated", "country_code": "XMP-iptcCore:CountryCode",
    "country": "XMP-photoshop:Country", "state": "XMP-photoshop:State", "city": "XMP-photoshop:City",
    "sublocation": "XMP-iptcCore:Location", "job": "XMP-photoshop:TransmissionReference",
    "instructions": "XMP-photoshop:Instructions", "credit": "XMP-photoshop:Credit", "source": "XMP-photoshop:Source",
    "copyright": "XMP-dc:Rights",
}


# --------------------------------------------------------------------------
# Tools: Adobe DNG Converter and ExifTool
# --------------------------------------------------------------------------

def find_converter(given=None):
    """Adobe DNG Converter (Windows), or None."""
    cands = [given] if given else []
    for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), r"C:\Program Files"):
        if base:
            cands.append(os.path.join(base, "Adobe", "Adobe DNG Converter", "Adobe DNG Converter.exe"))
    return next((c for c in cands if c and os.path.isfile(c)), None)


def find_exiftool(given=None, near=()):
    """ExifTool: the one given, else next to Gerbil (an "exiftool" folder, as extracted from its zip), else in
    a 1_Commons folder of a folder given or of one above it (where the mission keeps it), else in the PATH."""
    if given and os.path.isfile(given):
        return given
    here = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    bases = [here, os.path.join(here, "exiftool"), os.path.join(here, "third_party")]
    for start in near:
        d = os.path.abspath(start)
        while True:
            bases += [d, os.path.join(d, "1_Commons")]
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    for b in bases:
        if not os.path.isdir(b):
            continue
        for root, dirs, files in os.walk(b):
            depth = os.path.relpath(root, b).count(os.sep) + (root != b)
            dirs[:] = [x for x in dirs if depth < 2 and x.lower() != "exiftool_files"
                       and (x.lower().startswith("exiftool") or x == "1_Commons"
                            or root == b and x.lower().startswith(("raw_to_dng", "scripts_mafkf", "conversion_dng")))]
            for f in sorted(files):
                if f.lower() in ("exiftool.exe", "exiftool(-k).exe"):
                    return os.path.join(root, f)
    return shutil.which("exiftool")


class ExifTool:
    """One ExifTool process for the whole run (-stay_open mode), commands sent through its input."""

    def __init__(self, exe):
        import tempfile
        cfg = os.path.join(tempfile.gettempdir(), "gerbil_exiftool.config")   # the "gerbil" XMP tags
        try:
            with open(cfg, "w", encoding="ascii", newline="\n") as fh:
                fh.write(EXIFTOOL_CONFIG)
        except OSError:
            cfg = None
        self.p = subprocess.Popen([exe] + (["-config", cfg] if cfg else []) + ["-stay_open", "True", "-@", "-"],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
        self.n = 0

    def run(self, args):
        """Runs one command; returns (output, errors) - the errors come in the same stream, before the
        {readyN} marker ExifTool writes when the command is done."""
        self.n += 1
        lines = ["-charset", "filename=utf8"] + list(args) + [f"-execute{self.n}"]
        self.p.stdin.write(("\n".join(lines) + "\n").encode("utf-8"))
        self.p.stdin.flush()
        out = []
        while True:
            line = self.p.stdout.readline().decode("utf-8", "replace")
            if not line or line.strip() == f"{{ready{self.n}}}":
                break
            out.append(line)
        text = "".join(out)
        return text, "\n".join(x for x in text.splitlines() if x.startswith(("Error", "Warning")))

    def json(self, args):
        """First object of a JSON answer (-j), or {}."""
        out, _ = self.run(["-j"] + list(args))
        try:
            data = json.loads(out)
            return data[0] if data else {}
        except ValueError:
            return {}

    def json_all(self, args):
        """Every object of a JSON answer (-j), or []."""
        out, _ = self.run(["-q", "-j"] + list(args))       # (-q: no summary lines, which come in between)
        try:                                   # (the summary lines of ExifTool come around the JSON)
            return json.JSONDecoder().raw_decode(out[out.find("["):])[0] if "[" in out else []
        except ValueError:
            return []

    def close(self):
        try:
            self.p.stdin.write(b"-stay_open\nFalse\n\n")     # (the "(-k)" version waits for Enter)
            self.p.stdin.flush()
            self.p.stdin.close()
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def problem(out, err):
    """The first error or warning line of ExifTool, in a few words."""
    for line in (err + "\n" + out).splitlines():
        if line.startswith(("Error", "Warning")):
            return re.sub(r"^(Error|Warning)\s*:?\s*", "", line).strip()
    return "unknown problem"


# --------------------------------------------------------------------------
# Photos, projects and names
# --------------------------------------------------------------------------

def list_raws(folder):
    """RAW photos of a folder and its sub-folders (the folders written by the conversion left out)."""
    out = []
    for root, dirs, files in os.walk(folder):
        rel = os.path.relpath(root, folder)
        dirs[:] = sorted(d for d in dirs if not OUTPUT_DIRS.match(os.path.join(rel, d) if rel != "." else d))
        out += [os.path.join(root, f) for f in sorted(files) if os.path.splitext(f)[1].lower() in RAW_EXT]
    return out


def project_of(raw, root, cache):
    """Batch renaming that applies to a photo: the gerbil_project.json of its folder, else of a folder above
    it, up to the folder given. Returns (project or None, its folder)."""
    d = os.path.dirname(raw)
    while True:
        if d not in cache:
            cache[d] = g.load_project(d)
        if cache[d] is not None or os.path.normcase(d) == os.path.normcase(root):
            return cache[d], d
        parent = os.path.dirname(d)
        if parent == d:
            return None, d
        d = parent


def find_sidecar(raw):
    """XMP sidecar of a RAW: IMG.xmp or IMG.CR3.xmp, or None."""
    stem = os.path.splitext(raw)[0]
    for c in (stem + ".xmp", raw + ".xmp", stem + ".XMP", raw + ".XMP"):
        if os.path.isfile(c):
            return c
    return None


def metadata_args(iptc):
    """ExifTool arguments writing the IPTC fields of the project: a field given replaces the one already in
    the file, the keywords (and their hierarchy) are added to those already there."""
    args = []
    for key, value in iptc.items():
        if key == "keywords":
            for k in value:
                args += [f"-XMP-dc:Subject-={k}", f"-XMP-dc:Subject+={k}"]
        elif key == "hierarchical":
            for k in value:
                args += [f"-XMP-lr:HierarchicalSubject-={k}", f"-XMP-lr:HierarchicalSubject+={k}"]
        elif key in EXIF_TAGS:
            tag = EXIF_TAGS[key]
            if isinstance(value, list):         # (several assignments in one command: the list is replaced)
                args += [f"-{tag}={v}" for v in value]
            else:
                args.append(f"-{tag}={value}")
            if key == "copyright":
                args.append("-XMP-xmpRights:Marked=True")
    return args


# --------------------------------------------------------------------------
# Conversion
# --------------------------------------------------------------------------

def say(text):
    """One line of progress, written at once (the interface reads it as it comes)."""
    print(text, flush=True)


def convert(inputs, converter=None, exiftool=None, jpg="preview", tiff=False, settings=DNG_SETTINGS, progress=say):
    """Converts the RAW photos given (photos, or folders with their sub-folders); prints one line per photo (as
    the engine does, so that the interface reads it) and writes conversion_report_<date>.csv at the root of
    each folder. jpg: "preview" (the ~1024 px preview of the DNG, as the protocol), "full" (developed at full
    size), "none"; tiff: also a 16-bit TIFF developed at full size. Returns 0, or 1 when Adobe DNG Converter is
    missing."""
    if jpg is True:
        jpg = "preview"
    elif jpg is False:
        jpg = "none"
    conv = find_converter(converter)
    if not conv:
        progress("Adobe DNG Converter is not installed: install it (free, from Adobe), then run again.")
        return 1
    groups = {}                                  # folder -> None (all its photos) or the names of those given
    for p in inputs:
        p = os.path.abspath(p)
        if os.path.isdir(p):
            groups[p] = None
        elif os.path.isfile(p) and os.path.splitext(p)[1].lower() in RAW_EXT:
            d = os.path.dirname(p)
            if d not in groups or groups[d] is not None:
                groups.setdefault(d, set()).add(os.path.basename(p).lower())
    exe = find_exiftool(exiftool, list(groups))
    et = ExifTool(exe) if exe else None
    progress(f"Adobe DNG Converter: {conv}")
    progress(f"ExifTool: {exe or 'not found (no date from the EXIF, no XMP, no metadata, no JPG preview)'}")
    try:
        for folder, only in groups.items():
            convert_folder(folder, conv, et, jpg, settings, progress, only=only, tiff=tiff)
    finally:
        if et:
            et.close()
    return 0


def previous_outputs(folder, et):
    """The DNG files already written in <folder>\\<date>\\DNG: the RAW each comes from (relative path, lower
    case) -> (DNG path, the values written into it). DNG files made before Gerbil recorded their RAW are found
    by the name of their original RAW file (key "orig:<sub-folder>/<name>")."""
    roots = [os.path.join(folder, d, "DNG") for d in sorted(os.listdir(folder))
             if re.match(r"^\d{4}-\d{2}-\d{2}$", d) and os.path.isdir(os.path.join(folder, d, "DNG"))]
    out = {}
    if not roots or not et:
        return out
    for t in et.json_all(["-r", "-ext", "dng", "-XMP-gerbil:GerbilSource", "-XMP-gerbil:GerbilFields",
                          "-OriginalRawFileName"] + roots):
        path = os.path.normpath(t.get("SourceFile", ""))
        if not path:
            continue
        if t.get("GerbilSource"):
            out[str(t["GerbilSource"]).replace("/", os.sep).lower()] = (path, str(t.get("GerbilFields", "")))
        elif t.get("OriginalRawFileName"):
            root = next((r for r in roots if os.path.normcase(path).startswith(os.path.normcase(r) + os.sep)), None)
            sub = os.path.relpath(os.path.dirname(path), root) if root else ""
            key = "orig:" + os.path.join("" if sub == "." else sub, str(t["OriginalRawFileName"])).lower()
            out.setdefault(key, (path, ""))
    return out


def read_back(folder, exiftool=None):
    """The values given in Gerbil for the photos of a folder, read back from the DNG files already written:
    {photo name: {field: value}} (the batch renaming of a folder converted before)."""
    exe = find_exiftool(exiftool, [folder])
    if not exe:
        return {}
    et = ExifTool(exe)
    try:
        found = previous_outputs(folder, et)
    finally:
        et.close()
    out = {}
    for rel, (_, fields) in found.items():
        if rel.startswith("orig:") or not fields:
            continue
        try:
            vals = json.loads(fields).get("values") or {}
        except (ValueError, AttributeError):
            continue
        out[os.path.basename(rel)] = vals                    # (names in lower case)
    return out


def develop_to(dng, path, bits):
    """The DNG developed by LibRaw at full size, turned upright, written as JPEG (8 bits) or TIFF (16 bits)."""
    import rawpy
    with rawpy.imread(dng) as raw:
        rgb = raw.postprocess(use_camera_wb=True, output_bps=bits)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if bits == 16:
        import cv2
        ok, buf = cv2.imencode(".tif", rgb[:, :, ::-1].copy())
        if not ok:
            raise RuntimeError("TIFF not encoded")
        with open(path, "wb") as fh:
            fh.write(buf.tobytes())
    else:
        from PIL import Image
        Image.fromarray(rgb).save(path, quality=95)


def convert_folder(folder, conv, et, jpg, settings, progress, only=None, tiff=False):
    """Converts one folder (see convert); only: the names (lower case) of the photos to convert, None for all."""
    raws = [r for r in list_raws(folder) if only is None or os.path.basename(r).lower() in only]
    progress(f"{len(raws)} photo(s) -> {folder}")
    before = previous_outputs(folder, et)
    projects, rows, used, t_all = {}, [], {}, time.time()
    counts = {"ok": 0, "to verify": 0, "failed": 0}
    for i, raw in enumerate(raws, 1):
        t0 = time.time()
        rel = os.path.relpath(raw, folder)
        name = os.path.basename(raw)
        pr, _ = project_of(raw, folder, projects)
        key = name                                               # (the values of a photo: by its file name)
        base = (g.project_name(pr, key) if pr else None) or os.path.splitext(name)[0]
        doubts = g.project_checks(pr, key, base) if pr else []
        used_key = (os.path.dirname(rel).lower(), base.lower())
        used[used_key] = used.get(used_key, 0) + 1
        if used[used_key] > 1:
            base = f"{base}_{used[used_key]}"
            doubts.append(f"output name already used by another photo (suffix _{used[used_key]} added)")
        vals = g.photo_values(pr, key) if pr else {}
        iptc = g.iptc_values(pr, vals, base) if pr else {}
        notes, row = [], {"file": rel, "output_name": base}
        if pr:                                    # fields left empty: said, not a doubt (they are not required)
            empty = [f.get("label", f["key"]) for f in pr.get("fields", [])
                     if not f.get("required") and not vals.get(f["key"])]
            if empty:
                notes.append("not mentioned: " + ", ".join(empty))
        fields = json.dumps({"name": base, "values": vals}, ensure_ascii=False, sort_keys=True)
        status = "ok"
        try:
            # 1. shooting date
            date, source = None, "file"
            if et:
                d = et.json(["-d", "%Y-%m-%d", "-DateTimeOriginal", "-CreateDate", raw])
                for t in ("DateTimeOriginal", "CreateDate"):
                    if re.match(r"^\d{4}-\d{2}-\d{2}$", str(d.get(t, ""))) and not str(d[t]).startswith("0000"):
                        date, source = d[t], "EXIF"
                        break
            if not date:
                date = datetime.date.fromtimestamp(os.path.getmtime(raw)).isoformat()
                if et:
                    notes.append("no shooting date in the EXIF: date of the file used")
            if not et:
                doubts.append("ExifTool not found: no metadata, no XMP, no JPG preview")
            sub = os.path.dirname(rel)
            dirs = {k: os.path.join(folder, date, k, sub) for k in ("DNG", "JPG", "TIFF")}
            dng = os.path.join(dirs["DNG"], base + ".dng")
            jpg_path = os.path.join(dirs["JPG"], base + ".jpg")
            tif_path = os.path.join(dirs["TIFF"], base + ".tif")
            row.update(date=date, date_source=source)

            # 2. DNG: already there (renamed with its JPG and TIFF if the name changed), or converted
            prev, prev_fields = before.get(rel.lower()) or before.get(f"orig:{rel}".lower()) or (None, "")
            if prev and os.path.normcase(prev) != os.path.normcase(dng) and os.path.isfile(prev) \
                    and not os.path.exists(dng):
                old_stem = os.path.splitext(os.path.basename(prev))[0]
                os.makedirs(dirs["DNG"], exist_ok=True)
                os.replace(prev, dng)
                for k, ext, new in (("JPG", ".jpg", jpg_path), ("TIFF", ".tif", tif_path)):
                    old = os.path.join(os.path.dirname(prev).replace(os.sep + "DNG", os.sep + k, 1),
                                       old_stem + ext)
                    if os.path.isfile(old) and not os.path.exists(new):
                        os.makedirs(os.path.dirname(new), exist_ok=True)
                        os.replace(old, new)
                notes.append("DNG renamed (new name)")
            fresh = False
            if os.path.isfile(dng):
                row["dng_status"] = "already converted"
            else:
                os.makedirs(dirs["DNG"], exist_ok=True)
                r = subprocess.run([conv] + list(settings) + ["-d", dirs["DNG"], "-o", base + ".dng", raw],
                                   capture_output=True, creationflags=NO_WINDOW, timeout=900)
                if r.returncode != 0 or not os.path.isfile(dng):
                    raise RuntimeError(f"DNG conversion failed (code {r.returncode})")
                row["dng_status"] = "converted"
                fresh = True
            dng_time = os.path.getmtime(dng)

            # 3. XMP sidecar, then 4. the information given in Gerbil (and the RAW, to find the DNG again)
            side = find_sidecar(raw)
            row["xmp_source"] = side or ""
            changed = fresh or bool(side and os.path.getmtime(side) > dng_time) or prev_fields != fields
            if not et:
                row["xmp_status"] = row["metadata_status"] = "ExifTool missing"
            elif not changed:
                row["xmp_status"] = "already embedded" if side else "no XMP"
                row["metadata_status"] = "already written"
            else:
                if side:
                    out, err = et.run(["-m", "-overwrite_original", "-tagsfromfile", side, "-xmp:all", dng])
                    if "No writable tags set" in out:
                        row["xmp_status"] = "error: empty or unreadable"
                        doubts.append("XMP sidecar not embedded: empty or unreadable")
                    elif re.search(r"\b1 image files (updated|unchanged)", out):
                        row["xmp_status"] = "embedded"
                    else:
                        row["xmp_status"] = "error: " + problem(out, err)
                        doubts.append("XMP sidecar not embedded: " + problem(out, err))
                else:
                    row["xmp_status"] = "no XMP"
                ok_side = not any(d.startswith("XMP sidecar not embedded") for d in doubts)
                args = metadata_args(iptc) + [f"-XMP-gerbil:GerbilSource={rel.replace(os.sep, '/')}",
                                              # (a failed sidecar: written again at the next run)
                                              f"-XMP-gerbil:GerbilFields={fields if ok_side else ''}"]
                out, err = et.run(["-m", "-overwrite_original"] + args + [dng])
                if re.search(r"\b1 image files (updated|unchanged)", out):
                    row["metadata_status"] = "written" if iptc else "nothing to write"
                else:
                    row["metadata_status"] = "error: " + problem(out, err)
                    doubts.append("metadata not written: " + problem(out, err))

            # 5. JPG (preview of the DNG, or developed at full size) and 16-bit TIFF, with the same metadata
            meta = ["-m", "-overwrite_original", "-tagsfromfile", dng, "-exif:all", "-xmp:all", "--xmp-crs:all"]
            if jpg == "none":
                row["jpg_status"] = "not requested"
            elif not et:
                row["jpg_status"] = "ExifTool missing"
            elif os.path.isfile(jpg_path) and not changed and os.path.getmtime(jpg_path) >= os.path.getmtime(dng):
                row["jpg_status"] = "already done"
            else:
                os.makedirs(dirs["JPG"], exist_ok=True)
                if os.path.isfile(jpg_path):
                    os.remove(jpg_path)
                developed = False
                if jpg == "full":
                    try:
                        develop_to(dng, jpg_path, 8)
                        developed = True
                    except Exception as e:
                        notes.append(f"JPG not developed: {e}")
                else:
                    pattern = dirs["JPG"].replace("%", "%%") + os.sep + "%f.jpg"
                    for tag, src in (("PreviewImage", dng), ("PreviewImage", raw), ("JpgFromRaw", raw)):
                        out_file = os.path.join(dirs["JPG"], os.path.splitext(os.path.basename(src))[0] + ".jpg")
                        et.run(["-b", "-" + tag, "-w!", pattern, src])
                        if os.path.isfile(out_file) and os.path.getsize(out_file) > 0:
                            if os.path.normcase(out_file) != os.path.normcase(jpg_path):
                                os.replace(out_file, jpg_path)
                            if src == raw:
                                notes.append("JPG preview taken from the RAW (none in the DNG)")
                            break
                    else:
                        try:                               # no preview at all: developed by LibRaw
                            from PIL import Image
                            Image.fromarray(g.develop_raw(dng, half=True)).save(jpg_path, quality=90)
                            developed = True
                            notes.append("JPG preview developed from the DNG (no preview in it)")
                        except Exception as e:
                            notes.append(f"JPG preview not developed: {e}")
                if not os.path.isfile(jpg_path) or os.path.getsize(jpg_path) == 0:
                    row["jpg_status"] = "error: no preview in the DNG"
                    doubts.append("JPG preview not created")
                else:
                    out, err = et.run(meta + (["-Orientation#=1"] if developed else []) + [jpg_path])
                    row["jpg_status"] = "created" if re.search(r"\b1 image files (updated|unchanged)", out) \
                        else "created (no metadata)"
            if not tiff:
                row["tiff_status"] = "not requested"
            elif os.path.isfile(tif_path) and not changed and os.path.getmtime(tif_path) >= os.path.getmtime(dng):
                row["tiff_status"] = "already done"
            else:
                try:
                    develop_to(dng, tif_path, 16)
                    if et:
                        et.run(meta + ["-Orientation#=1", tif_path])
                    row["tiff_status"] = "created"
                except Exception as e:
                    row["tiff_status"] = f"error: {e}"
                    doubts.append(f"TIFF not created: {e}")
            row["dng"] = os.path.relpath(dng, folder)
            row["jpg"] = os.path.relpath(jpg_path, folder) if os.path.isfile(jpg_path) else ""
            row["tiff"] = os.path.relpath(tif_path, folder) if os.path.isfile(tif_path) else ""
            row["dng_size_mb"] = f"{os.path.getsize(dng) / 1e6:.1f}"
            status = "to verify" if doubts else "ok"
        except Exception as e:
            status = "failed"
            notes.append(f"{type(e).__name__}: {e}")
        counts[status] = counts.get(status, 0) + 1
        row.update(status=status, to_verify=" ; ".join(doubts), notes=" ; ".join(notes),
                   duration_s=f"{time.time() - t0:.1f}", **{f["label"]: vals.get(f["key"], "")
                                                            for f in (pr or {}).get("fields", [])})
        rows.append(row)
        what = row.get("dng_status", "DNG not made")
        detail = " | ".join(x for x in (row["to_verify"], row["notes"]) if x)
        progress(f"[{i}/{len(raws)}] {name}: {status} (DNG {what}, {row['duration_s']} s, {row['output_name']}.dng)"
                 + (f" | {detail}" if detail else ""))
    if rows:
        report = os.path.join(folder, f"conversion_report_{datetime.datetime.now():%Y-%m-%d_%H-%M}.csv")
        cols = ["file", "output_name", "status", "to_verify", "date", "date_source", "dng_status", "xmp_status",
                "metadata_status", "jpg_status", "tiff_status", "dng", "jpg", "tiff", "dng_size_mb", "xmp_source",
                "notes", "duration_s"]
        cols += [k for r in rows for k in r if k not in cols and not cols.append(k)]
        with open(report, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.DictWriter(fh, cols, delimiter=";", extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        progress(f"Report: {report}")
    progress(f"\nDone in {time.time() - t_all:.0f} s: {counts['ok']} ok, {counts['to verify']} to verify, "
             f"{counts['failed']} failed, out of {len(rows)} photo(s).")
    progress(f"Results: {folder}")


def main(argv=None):
    """Command line."""
    p = argparse.ArgumentParser(description="Gerbil: RAW photos to DNG, with their metadata and new names.")
    p.add_argument("inputs", nargs="+", help="RAW photos, or folders of RAW photos (sub-folders included)")
    p.add_argument("--jpg", choices=["preview", "full", "none"], default="preview",
                   help="JPG beside the DNG: its preview (~1024 px, default), developed at full size, or none")
    p.add_argument("--no-jpg", action="store_true", help="no JPG (same as --jpg none)")
    p.add_argument("--tiff", action="store_true", help="also a 16-bit TIFF developed at full size")
    p.add_argument("--converter", help="path of Adobe DNG Converter.exe")
    p.add_argument("--exiftool", help="path of exiftool.exe")
    p.add_argument("-v", "--verbose", action="store_true", help="(accepted, as by the engine)")
    a = p.parse_args(argv)
    return convert(a.inputs, a.converter, a.exiftool, "none" if a.no_jpg else a.jpg, a.tiff)


if __name__ == "__main__":
    sys.exit(main())
