#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerbil - tools: inventory of a documentation folder as CSV (photos, drawings, 3D models) and thumbnails
in batch for databases.
© 2026 Eloïs CHARBONNEL
Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE.
This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to
redistribute it under the conditions of the licence.

Inventory: one row per file, the columns chosen (file, folder, kind, size, date, the fields read from
the name with a template such as {site}_{us}_{number}, image size, resolution, date taken, camera). The
PowerShell line that does the same (without the image information) is given too, for learning.

Thumbnails: a reduced copy of each image (PNG, transparency kept, or JPEG on white), the transparent
margin of the outlined objects cut off.

Usage:
  py -3 gerbil_tools.py inventory FOLDER [-o inventory.csv] [--template "{site}_{us}_{number}"]
  py -3 gerbil_tools.py thumbnails FOLDER [--size 512] [--format png|jpg] [--only-outlined]
"""
import argparse
import csv
import datetime
import os
import re
import sys

KINDS = {
    "photos": (".jpg", ".jpeg", ".tif", ".tiff", ".png", ".dng", ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".orf",
               ".rw2", ".raf", ".pef", ".srw", ".3fr", ".iiq"),
    "drawings": (".ai", ".svg", ".pdf", ".eps"),
    "3d": (".ply", ".obj", ".stl", ".glb", ".gltf", ".dae", ".fbx", ".e57", ".las", ".laz"),
}
FILE_COLUMNS = ["file", "folder", "kind", "variant", "extension", "size_kb", "modified"]
# suffixes added by Gerbil to the output name: left out before reading the fields (column "variant")
GERBIL_SUFFIX = r"(_outlined(_scale)?|_to_control)?(_to_be_verified)?(_thumb)?$"
IMAGE_COLUMNS = ["width_px", "height_px", "dpi", "date_taken", "camera"]
SKIP_DIRS = {"gerbil_review", "gerbil_edits", "to_control", "thumbnails", "plates"}


def kind_of(name):
    ext = os.path.splitext(name)[1].lower()
    return next((k for k, exts in KINDS.items() if ext in exts), None)


def template_regex(template):
    """{site}_{us}_{number} -> ^(?<site>.+?)_(?<us>.+?)_(?<number>.+?)$ (fields, literal text kept).
    Returns (Python pattern, PowerShell / .NET pattern, field names)."""
    parts, names, pos = [], [], 0
    for m in re.finditer(r"\{(\w+)\}", template):
        parts.append(re.escape(template[pos:m.start()]))
        name = m.group(1)
        parts.append(f"(?P<{name}>.+?)" if name not in names else ".+?")
        names.append(name)
        pos = m.end()
    parts.append(re.escape(template[pos:]))
    py = "^" + "".join(parts) + "$"
    return py, py.replace("(?P<", "(?<"), list(dict.fromkeys(names))


def list_files(folders, kinds, recursive=True):
    out = []
    for folder in folders:
        if os.path.isfile(folder):
            out.append(folder)
            continue
        for root, dirs, files in os.walk(folder):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS) if recursive else []
            out += [os.path.join(root, f) for f in sorted(files) if kind_of(f) in kinds]
    return out


def image_info(path):
    """Size, resolution, date taken and camera of an image (empty when it cannot be read)."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
            dpi = im.info.get("dpi")
            exif = im.getexif()
            sub = exif.get_ifd(0x8769)
            make, model = str(exif.get(0x010F) or "").strip("\x00 "), str(exif.get(0x0110) or "").strip("\x00 ")
            camera = model if make and model.lower().startswith(make.lower().split()[0]) else f"{make} {model}".strip()
            return {"width_px": w, "height_px": h, "dpi": f"{float(dpi[0]):.0f}" if dpi else "",
                    "date_taken": str(sub.get(0x9003) or "").strip("\x00 "), "camera": camera}
    except Exception:
        return {}


def inventory(folders, out_csv, kinds=("photos", "drawings", "3d"), template="", image_columns=True,
              recursive=True, progress=None):
    """Writes the inventory; returns (number of rows, columns)."""
    py, _, names = template_regex(template) if template.strip() else (None, None, [])
    rx = re.compile(py, re.IGNORECASE) if py else None
    files = list_files(folders, kinds, recursive)
    columns = FILE_COLUMNS + names + (IMAGE_COLUMNS if image_columns else [])
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as fh:
        wr = csv.DictWriter(fh, columns, delimiter=";", extrasaction="ignore")
        wr.writeheader()
        for i, f in enumerate(files, 1):
            st = os.stat(f)
            stem, ext = os.path.splitext(os.path.basename(f))
            row = {"file": os.path.basename(f), "folder": os.path.dirname(f), "kind": kind_of(f) or "",
                   "extension": ext.lower(), "size_kb": round(st.st_size / 1024),
                   "modified": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")}
            base = re.sub(GERBIL_SUFFIX, "", stem, count=1)
            row["variant"] = stem[len(base):].strip("_")
            m = rx.match(base) if rx else None
            if m:
                row.update({k: v for k, v in m.groupdict().items()})
            if image_columns and row["kind"] == "photos":
                row.update(image_info(f))
            wr.writerow(row)
            if progress:
                progress(i, len(files))
    return len(files), columns


def ps_quote(s):
    return "'" + str(s).replace("'", "''") + "'"


def powershell_line(folders, out_csv, kinds=("photos", "drawings", "3d"), template="", recursive=True):
    """The same inventory in PowerShell (file columns and fields of the name; no image information)."""
    include = ",".join("*" + e for k in kinds for e in KINDS[k])
    paths = ",".join(ps_quote(os.path.join(f, "*") if not recursive else f) for f in folders)
    cols = ["Name", "DirectoryName", "Extension",
            "@{n='SizeKB';e={[math]::Round($_.Length/1KB)}}", "LastWriteTime"]
    if template.strip():
        _, net, names = template_regex(template)
        for n in names:
            cols.append(f"@{{n='{n}';e={{if (($_.BaseName -replace {ps_quote(GERBIL_SUFFIX)},'') -match {ps_quote(net)}) "
                        f"{{$Matches['{n}']}}}}}}")
    return (f"Get-ChildItem -Path {paths}{' -Recurse' if recursive else ''} -File -Include {include} | "
            f"Select-Object {', '.join(cols)} | "
            f"Export-Csv -Path {ps_quote(out_csv)} -Delimiter ';' -Encoding UTF8 -NoTypeInformation")


def thumbnails(folders, out_dir=None, size=512, fmt="png", only_outlined=False, trim=True, recursive=False,
               progress=None):
    """Writes NAME_thumb.png / .jpg (longest side `size`) in out_dir (default: a "thumbnails" folder in
    each source folder). Returns the list of files written."""
    from PIL import Image
    files = [f for f in list_files(folders, ("photos",), recursive)
             if not only_outlined or os.path.splitext(f)[0].endswith(("_outlined", "_outlined_to_be_verified"))]
    written = []
    for i, f in enumerate(files, 1):
        try:
            if os.path.splitext(f)[1].lower() in KINDS["photos"][7:]:          # RAW: developed by rawpy
                import rawpy
                with rawpy.imread(f) as raw:
                    im = Image.fromarray(raw.postprocess(use_camera_wb=True, output_bps=8, half_size=True))
            else:
                from PIL import ImageOps
                with Image.open(f) as src:
                    src.draft("RGB", (size * 2, size * 2))
                    im = ImageOps.exif_transpose(src)
                    im = im.convert("RGBA" if "A" in im.getbands() else "RGB")
            if trim and im.mode == "RGBA":
                box = im.getchannel("A").getbbox()
                if box:
                    im = im.crop(box)
            im.thumbnail((size, size), Image.LANCZOS)
            if fmt == "jpg" and im.mode == "RGBA":
                bg = Image.new("RGB", im.size, "white")
                bg.paste(im, mask=im.getchannel("A"))
                im = bg
            dest_dir = out_dir or os.path.join(os.path.dirname(f), "thumbnails")
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, os.path.splitext(os.path.basename(f))[0] + "_thumb." + fmt)
            if fmt == "jpg":
                im.save(dest, "JPEG", quality=90, optimize=True)
            else:
                im.save(dest, "PNG", optimize=True)
            written.append(dest)
        except Exception as e:
            print(f"{os.path.basename(f)}: not read ({type(e).__name__}: {e})")
        if progress:
            progress(i, len(files))
    return written


def main(argv=None):
    p = argparse.ArgumentParser(description="Gerbil tools: CSV inventory, thumbnails.")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("inventory", help="inventory of a folder as CSV")
    a.add_argument("folders", nargs="+")
    a.add_argument("-o", "--output", default="inventory.csv")
    a.add_argument("--kinds", default="photos,drawings,3d", help="photos, drawings, 3d (comma separated)")
    a.add_argument("--template", default="", help='fields of the names, e.g. "{site}_{us}_{number}"')
    a.add_argument("--no-image-info", action="store_true")
    a.add_argument("--powershell", action="store_true", help="print the equivalent PowerShell line")
    t = sub.add_parser("thumbnails", help="thumbnails in batch")
    t.add_argument("folders", nargs="+")
    t.add_argument("-o", "--output", help="folder of the thumbnails (default: 'thumbnails' in each folder)")
    t.add_argument("--size", type=int, default=512)
    t.add_argument("--format", choices=["png", "jpg"], default="png")
    t.add_argument("--only-outlined", action="store_true", help="only the _outlined.tif files")
    a = p.parse_args(argv)
    if a.cmd == "inventory":
        kinds = [k.strip() for k in a.kinds.split(",") if k.strip() in KINDS]
        n, cols = inventory(a.folders, a.output, kinds, a.template, not a.no_image_info)
        print(f"{n} file(s), {len(cols)} columns -> {a.output}")
        if a.powershell:
            print(powershell_line(a.folders, a.output, kinds, a.template))
    else:
        files = thumbnails(a.folders, a.output, a.size, a.format, a.only_outlined)
        print(f"{len(files)} thumbnail(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
