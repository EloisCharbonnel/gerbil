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

Deposit: the check of a folder before it is handed over to an archive - formats accepted, names without
spaces or accents, naming rule of the project, empty files, files present twice - with an inventory
(CSV), the SHA-256 checksum of every file and a report. Nothing is copied, moved or changed.

Usage:
  py -3 gerbil_tools.py inventory FOLDER [-o inventory.csv] [--template "{site}_{us}_{number}"]
  py -3 gerbil_tools.py thumbnails FOLDER [--size 512] [--format png|jpg] [--only-outlined]
  py -3 gerbil_tools.py deposit FOLDER [--formats "tif, jpg, pdf"] [--lang fr]
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import sys

KINDS = {
    "photos": (".jpg", ".jpeg", ".tif", ".tiff", ".png", ".dng", ".cr2", ".cr3", ".crw", ".nef", ".nrw", ".arw",
               ".sr2", ".srf", ".orf", ".rw2", ".raw", ".rwl", ".raf", ".pef", ".srw", ".3fr", ".fff", ".iiq", ".mos",
               ".mef", ".erf", ".mrw", ".dcr", ".kdc"),
    "drawings": (".ai", ".svg", ".pdf", ".eps"),
    "3d": (".ply", ".obj", ".stl", ".glb", ".gltf", ".dae", ".fbx", ".e57", ".las", ".laz"),
}
FILE_COLUMNS = ["file", "folder", "kind", "variant", "extension", "size_kb", "modified"]
# suffixes added by Gerbil to the output name: left out before reading the fields (column "variant")
GERBIL_SUFFIX = r"(_outlined(_scale)?|_to_control)?(_to_be_verified)?(_thumb)?$"
IMAGE_COLUMNS = ["width_px", "height_px", "dpi", "date_taken", "camera"]
SKIP_DIRS = {"gerbil_review", "gerbil_edits", "to_control", "thumbnails", "plates"}


def kind_of(name):
    """Kind of a file from its extension: photos, drawings, 3d or None."""
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
    """Files of the chosen kinds in the folders (sub-folders if wanted, Gerbil's work
    folders left out)."""
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
    """A text between single quotes for PowerShell (quotes doubled)."""
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


# --------------------------------------------------------------------------
# Deposit: check of a folder before it goes to an archive
# --------------------------------------------------------------------------

DEPOSIT_DIR = "deposit_check"       # written inside the folder checked
DEPOSIT_FORMATS = ("tif", "tiff", "jpg", "jpeg", "png", "dng", "pdf", "svg", "csv", "txt", "xml", "json", "odt",
                   "ods", "ply", "obj")   # open, documented formats usually asked for; the list can be changed
DEPOSIT_SKIP = {"gerbil_review", "gerbil_edits", DEPOSIT_DIR}     # Gerbil's working data: not deposited
DEPOSIT_NAME = re.compile(r"^[A-Za-z0-9_.\-]+$")                  # no space, accent or special character
DEPOSIT_PATH = 240                  # characters: longer paths break on Windows and on many archives
DEPOSIT_TEXT = {
    "title": ("Contrôle avant versement", "Check before deposit"),
    "folder": ("Dossier", "Folder"), "date": ("Date", "Date"),
    "files": ("fichier(s)", "file(s)"), "size": ("taille totale", "total size"),
    "ok": ("fichier(s) sans remarque", "file(s) without a remark"),
    "bad": ("fichier(s) à revoir", "file(s) to look at"),
    "formats": ("Formats acceptés", "Formats accepted"),
    "by_format": ("Fichiers par format", "Files by format"),
    "problems": ("Remarques", "Remarks"),
    "metadata": ("image(s) sans métadonnées XMP ou IPTC", "image(s) without XMP or IPTC metadata"),
    "skipped": ("Dossiers de travail de Gerbil laissés de côté", "Gerbil's working folders left out"),
    "written": ("Fichiers écrits", "Files written"),
    "nothing": ("Rien n'a été copié, déplacé ni modifié.", "Nothing was copied, moved or changed."),
    "format": ("format hors de la liste acceptée", "format outside the accepted list"),
    "name": ("nom avec espace, accent ou caractère spécial", "name with a space, an accent or a special character"),
    "rule": ("nom hors de la règle de nommage du projet", "name off the naming rule of the project"),
    "empty": ("fichier vide", "empty file"),
    "long": ("chemin de plus de 240 caractères", "path longer than 240 characters"),
    "twice": ("même contenu que", "same content as"),
}


def sha256_of(path):
    """SHA-256 checksum of a file (read by blocks of 1 MB)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(1 << 20):
            h.update(block)
    return h.hexdigest()


def has_metadata(path):
    """True when an image holds an XMP packet or IPTC data (looked for in its first and last megabyte)."""
    try:
        with open(path, "rb") as fh:
            data = fh.read(1 << 20)
            size = os.path.getsize(path)
            if size > 2 << 20:
                fh.seek(size - (1 << 20))
                data += fh.read()
    except OSError:
        return False
    return b"<x:xmpmeta" in data or b"http://ns.adobe.com/xap/1.0/" in data or b"Photoshop 3.0\x008BIM" in data


def project_rule(folder, cache):
    """Naming rule of the batch renaming of a folder (gerbil_project.json), compiled as PowerShell reads
    it (case-insensitive, .NET named groups), or None."""
    if folder not in cache:
        cache[folder] = None
        try:
            with open(os.path.join(folder, "gerbil_project.json"), encoding="utf-8") as fh:
                rule = (json.load(fh).get("rule") or "").strip()
            if rule:
                rule = re.sub(r"\(\?<(?![=!])", "(?P<", rule)
                cache[folder] = re.compile(rule[5:]) if rule.startswith("(?-i)") else re.compile(rule, re.IGNORECASE)
        except (OSError, ValueError, AttributeError, re.error):
            pass
    return cache[folder]


def deposit(folder, out_dir=None, formats=DEPOSIT_FORMATS, lang="en", progress=None):
    """Checks a folder before its deposit in an archive, without changing anything in it. For every
    file (sub-folders included, Gerbil's working folders left out): its format against the accepted
    list, its name (no space, accent or special character; the naming rule of the project of its
    folder, for photos), an empty file, a path too long, the same content present twice (SHA-256).
    Writes in out_dir (default: FOLDER/deposit_check) deposit_inventory.csv (one row per file, with
    its size, date, checksum, metadata and remarks), checksums.sha256 (the format of sha256sum, to
    check the deposit after its transfer) and deposit_report.txt (in French or English: lang).
    Returns {"files", "bytes", "problems" (files with a remark), "out_dir"}."""
    t = lambda key: DEPOSIT_TEXT[key][0 if lang == "fr" else 1]
    folder = os.path.abspath(folder)
    out_dir = os.path.abspath(out_dir or os.path.join(folder, DEPOSIT_DIR))
    accepted = {str(f).strip().lower().lstrip(".") for f in formats if str(f).strip()}
    files = []
    for root, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in DEPOSIT_SKIP and os.path.abspath(os.path.join(root, d)) != out_dir)
        files += [os.path.join(root, n) for n in sorted(names)]
    rows, seen, rules, by_format, no_meta, total = [], {}, {}, {}, 0, 0
    for i, f in enumerate(files, 1):
        rel = os.path.relpath(f, folder).replace(os.sep, "/")
        stem, ext = os.path.splitext(os.path.basename(f))
        ext = ext.lower().lstrip(".")
        st = os.stat(f)
        total += st.st_size
        by_format[ext or "-"] = by_format.get(ext or "-", 0) + 1
        problems = []
        if ext not in accepted:
            problems.append(t("format") + f" (.{ext})")
        if not DEPOSIT_NAME.match(os.path.basename(f)):
            problems.append(t("name"))
        kind = kind_of(f)
        if kind == "photos":
            rule = project_rule(os.path.dirname(f), rules) or project_rule(os.path.dirname(os.path.dirname(f)), rules)
            if rule and not rule.search(re.sub(GERBIL_SUFFIX, "", stem, count=1)):
                problems.append(t("rule"))
        if st.st_size == 0:
            problems.append(t("empty"))
        if len(f) > DEPOSIT_PATH:
            problems.append(t("long"))
        digest = sha256_of(f)
        if st.st_size and digest in seen:
            problems.append(f"{t('twice')} {seen[digest]}")
        seen.setdefault(digest, rel)
        meta = ""
        if kind == "photos" and ext in ("jpg", "jpeg", "tif", "tiff", "png", "dng"):
            meta = "yes" if has_metadata(f) else "no"
            no_meta += meta == "no"
        rows.append({"file": rel, "format": ext, "size_bytes": st.st_size,
                     "modified": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M"),
                     "sha256": digest, "metadata": meta, "remarks": " ; ".join(problems)})
        if progress:
            progress(i, len(files))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "deposit_inventory.csv"), "w", encoding="utf-8-sig", newline="") as fh:
        wr = csv.DictWriter(fh, ["file", "format", "size_bytes", "modified", "sha256", "metadata", "remarks"], delimiter=";")
        wr.writeheader()
        wr.writerows(rows)
    with open(os.path.join(out_dir, "checksums.sha256"), "w", encoding="utf-8", newline="\n") as fh:
        fh.writelines(f"{r['sha256']} *{r['file']}\n" for r in rows)
    bad = [r for r in rows if r["remarks"]]
    counts = {}
    for r in bad:
        for remark in r["remarks"].split(" ; "):
            key = re.sub(r" \(\.\w*\)$", "", remark)
            key = t("twice") if key.startswith(t("twice")) else key
            counts[key] = counts.get(key, 0) + 1
    lines = [t("title"), "=" * len(t("title")), f"{t('folder')} : {folder}",
             f"{t('date')} : {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", "",
             f"{len(rows)} {t('files')}, {t('size')} {total / 1e6:.1f} Mo" if lang == "fr"
             else f"{len(rows)} {t('files')}, {t('size')} {total / 1e6:.1f} MB",
             f"{len(rows) - len(bad)} {t('ok')}", f"{len(bad)} {t('bad')}", "",
             f"{t('formats')} : {', '.join(sorted(accepted))}", "",
             f"{t('by_format')} :"] + [f"  .{k} : {v}" for k, v in sorted(by_format.items())] + ["", f"{t('problems')} :"]
    lines += [f"  {v} x {k}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])] or ["  -"]
    if no_meta:
        lines += ["", f"{no_meta} {t('metadata')}"]
    lines += ["", f"{t('skipped')} : gerbil_review, gerbil_edits", "",
              f"{t('written')} : deposit_inventory.csv, checksums.sha256, deposit_report.txt", t("nothing")]
    if bad:
        lines += ["", f"{t('bad')} :"] + [f"  {r['file']} : {r['remarks']}" for r in bad[:200]]
        if len(bad) > 200:
            lines.append(f"  … (+{len(bad) - 200}, deposit_inventory.csv)")
    with open(os.path.join(out_dir, "deposit_report.txt"), "w", encoding="utf-8-sig", newline="\r\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return {"files": len(rows), "bytes": total, "problems": len(bad), "out_dir": out_dir}


def main(argv=None):
    """Command line: "inventory", "thumbnails" or "deposit"."""
    p = argparse.ArgumentParser(description="Gerbil tools: CSV inventory, thumbnails, check before a deposit.")
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
    d = sub.add_parser("deposit", help="check of a folder before its deposit in an archive")
    d.add_argument("folder")
    d.add_argument("-o", "--output", help=f"where the inventory, checksums and report go (default: FOLDER/{DEPOSIT_DIR})")
    d.add_argument("--formats", default=", ".join(DEPOSIT_FORMATS), help="formats accepted (comma separated)")
    d.add_argument("--lang", choices=["en", "fr"], default="en", help="language of the report")
    a = p.parse_args(argv)
    if a.cmd == "deposit":
        r = deposit(a.folder, a.output, a.formats.split(","), a.lang)
        print(f"{r['files']} file(s), {r['bytes'] / 1e6:.1f} MB, {r['problems']} to look at -> {r['out_dir']}")
        return 0
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
