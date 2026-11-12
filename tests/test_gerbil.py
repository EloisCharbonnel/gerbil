"""Automatic checks of Gerbil on synthetic photos (tests/synthetic.py): scale, cut-out, labels on a dark
background, learned scales, IPTC metadata, plates, inventory. Run: py -3 -m pytest tests"""
import csv
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

import numpy as np
import pytest
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.dirname(HERE), HERE]

import gerbil as g                      # noqa: E402
import gerbil_plates as gp              # noqa: E402
import gerbil_tools as gt               # noqa: E402
import synthetic as sy                  # noqa: E402


def save(path, rgb):
    Image.fromarray(rgb).save(path, quality=95)


def run(folder, *args):
    out = os.path.join(folder, "out")
    assert g.main([folder, "-o", out, "-j", "1", "--no-psd", *args]) in (0, None)
    with open(os.path.join(out, "outlined_report.csv"), encoding="utf-8-sig") as fh:
        rows = {r["file"]: r for r in csv.DictReader(fh, delimiter=";")}
    return out, rows


def number(text):
    return float(str(text).replace(",", "."))


@pytest.fixture(scope="module")
def light(tmp_path_factory):
    d = tmp_path_factory.mktemp("light")
    rgb, mask, px = sy.photo(px_cm=100.0)
    save(os.path.join(d, "sherd_A.jpg"), rgb)
    out, rows = run(str(d))
    return d, out, rows, mask


def test_scale_read_exactly(light):
    _, _, rows, _ = light
    r = rows["sherd_A.jpg"]
    assert r["scale_found"] == "yes" and r["scale_type"] == "checkerboard"
    assert abs(number(r["px_per_cm"]) - 100.0) < 0.5
    assert number(r["scale_length_cm"]) == 10


def test_cutout_matches_the_sherd(light):
    _, out, rows, mask = light
    tif = os.path.join(out, "sherd_A_outlined.tif")
    assert os.path.exists(tif), rows["sherd_A.jpg"]
    alpha = np.asarray(Image.open(tif))[..., 3] > 127
    assert abs(alpha.sum() - mask.sum()) / mask.sum() < 0.03          # same area within 3 %
    dpi = Image.open(tif).info["dpi"][0]
    assert abs(dpi - 254.0) < 1.5                                       # 100 px/cm = 254 ppi: true size


def test_dark_background_label_discarded(tmp_path):
    rgb, mask, _ = sy.photo(px_cm=100.0, dark=True, label=True)
    save(os.path.join(tmp_path, "felt.jpg"), rgb)
    out, rows = run(str(tmp_path))
    r = rows["felt.jpg"]
    assert r["pieces"] == "1" and "paper label discarded" in r["notes"]
    alpha = np.asarray(Image.open(os.path.join(out, "felt_outlined.tif")))[..., 3] > 127
    assert abs(alpha.sum() - mask.sum()) / mask.sum() < 0.04          # no dark outline around the sherd


def test_no_scale_still_discards_the_scale(tmp_path):
    rgb, mask, _ = sy.photo(px_cm=100.0)
    save(os.path.join(tmp_path, "sherd_B.jpg"), rgb)
    out, rows = run(str(tmp_path), "--no-scale")
    r = rows["sherd_B.jpg"]
    assert r["pieces"] == "1" and "scale, label or card discarded" in r["notes"]
    alpha = np.asarray(Image.open(os.path.join(out, "sherd_B_outlined.tif")))[..., 3] > 127
    assert abs(alpha.sum() - mask.sum()) / mask.sum() < 0.03          # the sherd alone, not the scale


def test_cast_shadow_removed(tmp_path):
    rgb, mask, _ = sy.photo(px_cm=100.0, shadow=True)
    save(os.path.join(tmp_path, "shadowed.jpg"), rgb)
    out, rows = run(str(tmp_path))
    r = rows["shadowed.jpg"]
    assert "cast shadow removed" in r["notes"]
    alpha = np.asarray(Image.open(os.path.join(out, "shadowed_outlined.tif")))[..., 3] > 127
    assert abs(alpha.sum() - mask.sum()) / mask.sum() < 0.03          # the sherd, not its shadow


def network(monkeypatch, objects):
    """Stands for the BiRefNet network: it answers `objects` (mask of what it would see as objects)."""
    import types
    import cv2
    seen = cv2.resize(objects.astype(np.uint8) * 255, (g.AI_SIZE, g.AI_SIZE), interpolation=cv2.INTER_AREA)
    seen = cv2.GaussianBlur(seen, (0, 0), 1.5)
    monkeypatch.setitem(sys.modules, "onnxruntime", types.ModuleType("onnxruntime"))
    monkeypatch.setattr(g, "ai_model_path", lambda model: "")
    monkeypatch.setattr(g, "ai_providers", lambda device, model: ["CPUExecutionProvider"])
    monkeypatch.setattr(g, "ai_mask", lambda rgb, opts: seen)


def test_cutout_drawn_from_the_ai(tmp_path, monkeypatch):
    """The network sees the sherd and the label as objects, neither the shadow nor the scale. Gerbil
    must discard the label and draw the edge of the sherd from the photo."""
    rgb, mask, px = sy.photo(px_cm=100.0, shadow=True, label=True)
    save(os.path.join(tmp_path, "by_ai.jpg"), rgb)
    H, W = mask.shape
    objects = mask.copy()
    ly, lx = int(H * 0.12), int(W * 0.08)
    objects[ly:ly + int(2.5 * px), lx:lx + int(4 * px)] = True              # the label
    network(monkeypatch, objects)
    out, rows = run(str(tmp_path), "--cutout", "ai")
    r = rows["by_ai.jpg"]
    assert r["status"] == "ok" and r["pieces"] == "1", r
    assert "cut-out drawn from the AI" in r["notes"] and "paper label discarded" in r["notes"]
    alpha = np.asarray(Image.open(os.path.join(out, "by_ai_outlined.tif")))[..., 3] > 127
    assert abs(alpha.sum() - mask.sum()) / mask.sum() < 0.03          # the sherd: no label, no shadow


def test_white_object_kept_by_the_ai(tmp_path, monkeypatch):
    """A sherd of the colour of the background: the colour rule cannot see it, the network can."""
    rgb, mask, _ = sy.photo(px_cm=100.0)
    rng = np.random.default_rng(5)
    white = np.clip(rng.normal(0, 3, rgb.shape) + (236, 233, 226), 0, 255).astype(np.uint8)
    rgb = np.where(mask[..., None], white, rgb)
    save(os.path.join(tmp_path, "white.jpg"), rgb)
    network(monkeypatch, mask)
    out, rows = run(str(tmp_path), "--cutout", "ai")
    r = rows["white.jpg"]
    assert r["status"] == "ok" and r["pieces"] == "1", r
    alpha = np.asarray(Image.open(os.path.join(out, "white_outlined.tif")))[..., 3] > 127
    assert abs(alpha.sum() - mask.sum()) / mask.sum() < 0.04          # the whole sherd


def test_colours_balanced_on_a_white(tmp_path):
    """A photo with a colour cast: balanced on the white of its scale, the sherd gets its colour back; the
    cut-out is the same with and without the correction; without the white asked for, nothing changes."""
    rgb, mask, _ = sy.photo(px_cm=100.0)
    light = g.srgb_to_linear(rgb / 255.0) * (1.0, 0.85, 0.65)                              # warm light
    cast = np.round(g.linear_to_srgb(light) * 255).astype(np.uint8)
    for name in ("plain", "balanced", "chart"):
        os.makedirs(os.path.join(tmp_path, name))
        save(os.path.join(tmp_path, name, "cast.jpg"), cast)
    _, rows0 = run(os.path.join(tmp_path, "plain"))
    _, rows1 = run(os.path.join(tmp_path, "balanced"), "--colour", "balance", "--white", "scale")
    _, rows2 = run(os.path.join(tmp_path, "chart"), "--colour", "balance")       # no chart in the photo
    assert "colours balanced on the white of the scale" in rows1["cast.jpg"]["notes"]
    assert "colours not corrected: no colour chart" in rows2["cast.jpg"]["notes"]
    tifs = [np.asarray(Image.open(os.path.join(tmp_path, n, "out", "cast_outlined.tif"))).astype(np.float32)
            for n in ("plain", "balanced", "chart")]
    assert np.array_equal(tifs[0][..., 3], tifs[1][..., 3])                       # same cut-out
    assert np.array_equal(tifs[0], tifs[2])                                       # nothing changed without a chart
    inside = tifs[0][..., 3] > 250

    def hue(colour):                                  # red and blue against green, in linear light
        lin = g.srgb_to_linear(np.asarray(colour, np.float64) / 255.0)
        return np.array([lin[0] / lin[1], lin[2] / lin[1]])
    true = hue([176, 126, 92])                                                    # the sherd of the synthetic photo
    error = [np.abs(hue(t[..., :3][inside].mean(axis=0)) / true - 1).max() for t in tifs[:2]]
    assert error[1] < 0.05 < error[0], error                                      # the cast is gone


def test_colours_balanced_on_a_chart_of_patches(tmp_path):
    """A chart of the SpyderCheckr kind (black frame, grey column, colours) beside the sherd, under a warm
    light: the chart is discarded, its white patch is found among greys, a yellow and pastel tints, and
    the sherd gets its colour back."""
    import cv2
    rgb, mask, _ = sy.photo(px_cm=100.0)
    patches = [[(245, 245, 245), (0, 140, 180), (240, 120, 30), (110, 200, 180)],
               [(200, 200, 200), (200, 70, 150), (40, 60, 150), (130, 120, 190)],
               [(160, 160, 160), (250, 220, 40), (210, 70, 80), (70, 90, 40)],
               [(120, 120, 120), (180, 40, 40), (70, 40, 90), (60, 110, 160)],
               [(80, 80, 80), (60, 150, 70), (250, 245, 200), (230, 170, 140)],
               [(40, 40, 40), (30, 50, 130), (240, 140, 40), (110, 60, 40)]]
    x0, y0, size, gap = 120, 380, 130, 22
    cv2.rectangle(rgb, (x0, y0), (x0 + 4 * (size + gap) + gap, y0 + 6 * (size + gap) + gap), (25, 25, 25), -1)
    for r, line in enumerate(patches):
        for c, colour in enumerate(line):
            px, py = x0 + gap + c * (size + gap), y0 + gap + r * (size + gap)
            rgb[py:py + size, px:px + size] = colour
    light = g.srgb_to_linear(rgb / 255.0) * (1.0, 0.85, 0.65)                              # warm light
    save(os.path.join(tmp_path, "chart.jpg"), np.round(g.linear_to_srgb(light) * 255).astype(np.uint8))
    out, rows = run(str(tmp_path), "--colour", "balance")
    r = rows["chart.jpg"]
    assert r["pieces"] == "1" and "colour chart discarded" in r["notes"], r
    assert "colours balanced on the white of the colour chart" in r["notes"], r
    tif = np.asarray(Image.open(os.path.join(out, "chart_outlined.tif"))).astype(np.float64)
    lin = g.srgb_to_linear(tif[..., :3][tif[..., 3] > 250].mean(axis=0) / 255.0)
    true = g.srgb_to_linear(np.array([176, 126, 92]) / 255.0)
    assert abs(lin[0] / lin[1] / (true[0] / true[1]) - 1) < 0.05 and abs(lin[2] / lin[1] / (true[2] / true[1]) - 1) < 0.05


def test_learned_scale(tmp_path):
    rgb, _, _ = sy.photo(px_cm=100.0)
    H, W = rgb.shape[:2]
    y = int(H * 0.72) + int(round(0.15 * 100)) + 50                    # middle of the scale band
    x0 = (W - (1000 + 30)) // 2 + 15
    model = g.learn_scale(rgb, {"p1": [x0, y], "p2": [x0 + 1000, y], "cm": 10.0, "width_cm": 1.0})
    profile = os.path.join(tmp_path, "profile.json")
    with open(profile, "w", encoding="utf-8") as fh:
        json.dump({"name": "test", "scales": [model]}, fh)
    other, _, _ = sy.photo(px_cm=120.0, seed=2)
    sc = g.detect_learned_scale(other, g.load_profile(profile)["_models"])
    assert sc is not None and sc.kind == "learned"
    assert abs(sc.px_cm - 120.0) / 120.0 < 0.005


def test_iptc_and_lossless_jpeg(tmp_path):
    pr = {"iptc": {"title": "{name}", "keywords": "{site}, US {us}", "copyright": "© test"}}
    vals = {"site": "QSR25", "us": "7549"}
    iptc = g.iptc_values(pr, vals, "QSR25_US7549_187")
    assert iptc == {"title": "QSR25_US7549_187", "keywords": ["QSR25", "US 7549"], "copyright": "© test"}
    xmp = g.make_xmp("scale", {}, {"Site": "QSR25"}, "QSR25_US7549_187", iptc)
    ET.fromstring(re.sub(rb"<\?xpacket[^>]*\?>", b"", xmp).strip())     # well-formed
    rgb, _, _ = sy.photo()
    path = os.path.join(tmp_path, "copy.jpg")
    save(path, rgb)
    before = np.asarray(Image.open(path)).copy()
    assert g.embed_xmp_jpeg(path, xmp)
    assert np.array_equal(before, np.asarray(Image.open(path)))        # the image is untouched
    assert b"QSR25_US7549_187" in open(path, "rb").read()


def test_plates_svg(light, tmp_path):
    _, out, _, _ = light
    files, _ = gp.write_plates(out, gp.PlateSettings(ratio=2, title="Plate {page} - {scale}"), str(tmp_path))
    assert files
    root = ET.parse(files[0]).getroot()
    assert root.get("width") == "210mm" and root.get("viewBox") == "0 0 210 297"
    image = root.find(".//{http://www.w3.org/2000/svg}image")
    item = gp.collect(out)[0]
    assert abs(float(image.get("width")) - item.width_cm * 10 / 2) < 0.01  # true size at 1:2


def test_plates_tiff_and_jpeg(light, tmp_path):
    _, out, _, _ = light
    st = gp.PlateSettings(svg=False, tiff=True, jpeg=True, raster_dpi=100)
    files, _ = gp.write_plates(out, st, str(tmp_path))
    assert [os.path.splitext(f)[1] for f in files] == [".tif", ".jpg"]
    for f in files:
        with Image.open(f) as im:                                         # A4 at 100 dpi
            assert im.size == (827, 1169) and round(im.info["dpi"][0]) == 100


def test_free_plates_of_photos(tmp_path):
    """Whole photos on plates at a common scale: scale given by two points, or by a world file; a photo
    without a scale is left out; the fields of the folder make the captions."""
    for name, size in (("SP1.jpg", (800, 600)), ("SP2.jpg", (600, 900)), ("SP3.jpg", (500, 500)),
                       ("SP1_outlined.tif", (50, 50))):
        Image.new("RGB", size, (150, 120, 90)).save(os.path.join(tmp_path, name))
    with open(os.path.join(tmp_path, gp.MANUAL_SCALES), "w", encoding="utf-8") as fh:
        json.dump({"SP1.jpg": {"p1": [100, 300], "p2": [500, 300], "cm": 100}}, fh)     # 4 px per cm
    with open(os.path.join(tmp_path, "SP2.jgw"), "w") as fh:
        fh.write("0.005\n0\n0\n-0.005\n0\n0\n")                                      # 5 mm per pixel
    with open(os.path.join(tmp_path, gp.PROJECT_FILE), "w", encoding="utf-8") as fh:
        json.dump({"fields": [{"key": "type", "label": "Type"}], "common": {"type": "cist"},
                   "photos": {"SP2.jpg": {"type": "pit"}}}, fh)
    items, unscaled = gp.collect_images(str(tmp_path))
    assert [(it.name, round(it.width_cm), round(it.height_cm)) for it in items] == [("SP1", 200, 150), ("SP2", 300, 450)]
    assert unscaled == ["SP3.jpg"] and [it.values["Type"] for it in items] == ["cist", "pit"]
    st = gp.PlateSettings(ratio=20, page="A3", landscape=True, caption="{name} {Type}")
    st.bar.unit = "m"
    files, warnings = gp.write_plates(str(tmp_path), st, images=True)
    assert len(files) == 1 and any("without a scale" in w for w in warnings)
    root = ET.parse(files[0]).getroot()
    assert root.get("width") == "420mm"
    widths = sorted(float(i.get("width")) for i in root.iter("{http://www.w3.org/2000/svg}image"))
    assert [round(w, 1) for w in widths] == [100.0, 150.0]                # 2 m and 3 m at 1:20
    texts = [t.text for t in root.iter("{http://www.w3.org/2000/svg}text")]
    assert "SP1 cist" in texts and "SP2 pit" in texts and any(t and t.endswith(" m") for t in texts)


def pdf_pages(path):
    """Number of pages of a PDF written by Pillow (the last page tree written: pages are appended)."""
    with open(path, "rb") as fh:
        return int(re.findall(rb"/Count (\d+)", fh.read())[-1])


def test_plates_pdf_and_list_of_figures(light, tmp_path):
    _, out, _, _ = light
    st = gp.PlateSettings(svg=False, pdf=True, raster_dpi=72, title="Plate {page}", credit="Photos: test",
                          file_name="SITE_pl{page}")
    files, _ = gp.write_plates(out, st, str(tmp_path))
    assert [os.path.basename(f) for f in files] == ["SITE_pl.pdf"] and pdf_pages(files[0]) == 1
    with open(os.path.join(tmp_path, "figures.csv"), encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh, delimiter=";"))
    assert len(rows) == 1
    assert (rows[0]["figure"], rows[0]["title"], rows[0]["scale"], rows[0]["credit"]) == ("1", "Plate 1", "1:1", "Photos: test")
    assert rows[0]["caption"] == "sherd_A" and rows[0]["file"] == "SITE_pl01"


def test_contact_sheets(tmp_path):
    """Seven photos, two per row, grouped by a field: a page per group, all the pages in one PDF."""
    for i in range(7):
        Image.new("RGB", (400, 300), (40 * i, 120, 90)).save(os.path.join(tmp_path, f"P{i + 1}.jpg"))
    Image.new("RGB", (50, 50)).save(os.path.join(tmp_path, "P1_outlined.tif"))           # not a photo
    with open(os.path.join(tmp_path, gp.PROJECT_FILE), "w", encoding="utf-8") as fh:
        json.dump({"fields": [{"key": "us", "label": "US"}],
                   "photos": {f"P{i + 1}.jpg": {"us": "100" if i < 3 else "200"} for i in range(7)}}, fh)
    st = gp.PlateSettings(svg=True, pdf=True, raster_dpi=72, contact_columns=2, group="US", group_new_page=True,
                          title="US {group}", caption="{name}")
    files, warnings = gp.write_contact_sheets(str(tmp_path), st)
    names = sorted(os.path.basename(f) for f in files)
    assert names == ["contact_01.svg", "contact_02.svg", "contact_sheets.pdf"] and not warnings
    assert pdf_pages(os.path.join(tmp_path, gp.CONTACT_DIR, "contact_sheets.pdf")) == 2
    root = ET.parse(os.path.join(tmp_path, gp.CONTACT_DIR, "contact_02.svg")).getroot()
    texts = [t.text for t in root.iter("{http://www.w3.org/2000/svg}text")]
    assert "US 200" in texts and {"P4", "P5", "P6", "P7"} <= set(texts) and "P1" not in texts
    assert len(list(root.iter("{http://www.w3.org/2000/svg}image"))) == 4


def test_check_before_a_deposit(tmp_path):
    """Formats, names, empty file, same content twice; inventory, checksums and report; nothing changed."""
    folder = os.path.join(tmp_path, "site")
    os.makedirs(os.path.join(folder, "gerbil_review"))
    Image.new("RGB", (60, 40), (10, 20, 30)).save(os.path.join(folder, "SITE_001.tif"))
    Image.new("RGB", (60, 40), (10, 20, 30)).save(os.path.join(folder, "bad name é.jpg"))
    for name, data in (("SITE_002.psd", b"8BPS"), ("empty.txt", b""), ("notes.txt", b"hello"), ("copy.txt", b"hello"),
                       (os.path.join("gerbil_review", "work.json"), b"{}")):
        with open(os.path.join(folder, name), "wb") as fh:
            fh.write(data)
    before = sorted(os.listdir(folder))
    r = gt.deposit(folder, lang="fr")
    assert (r["files"], r["problems"]) == (6, 4) and sorted(os.listdir(folder)) == sorted(before + [gt.DEPOSIT_DIR])
    with open(os.path.join(r["out_dir"], "deposit_inventory.csv"), encoding="utf-8-sig") as fh:
        rows = {x["file"]: x for x in csv.DictReader(fh, delimiter=";")}
    assert rows["SITE_001.tif"]["remarks"] == "" and rows["copy.txt"]["remarks"] == ""
    assert "format" in rows["SITE_002.psd"]["remarks"] and "nom avec espace" in rows["bad name é.jpg"]["remarks"]
    assert "vide" in rows["empty.txt"]["remarks"] and rows["notes.txt"]["remarks"] == "même contenu que copy.txt"
    import hashlib
    with open(os.path.join(r["out_dir"], "checksums.sha256"), encoding="utf-8") as fh:
        sums = dict(reversed(line.rstrip("\n").split(" *", 1)) for line in fh)
    assert sums["notes.txt"] == hashlib.sha256(b"hello").hexdigest() and len(sums) == 6
    with open(os.path.join(r["out_dir"], "deposit_report.txt"), encoding="utf-8-sig") as fh:
        assert "4 fichier(s) à revoir" in fh.read()


def test_naming_refresh_and_extension_case(tmp_path):
    rgb, _, _ = sy.photo()
    photo = os.path.join(tmp_path, "sherd_B.JPG")
    save(photo, rgb)
    project = os.path.join(tmp_path, g.PROJECT_FILE)
    with open(project, "w", encoding="utf-8") as fh:
        json.dump({"fields": [], "photo_ext_lower": True}, fh)
    out, rows = run(str(tmp_path))
    assert rows["sherd_B.JPG"]["status"] == "to verify"                   # flagged for its extension only
    assert "sherd_B_outlined_to_be_verified.tif" in os.listdir(out)
    with open(project, "w", encoding="utf-8") as fh:                      # alert off, extensions in capitals
        json.dump({"fields": [], "photo_ext_lower": False, "ext_case": "upper"}, fh)
    changed, rerun = g.refresh_naming([(photo, out)])
    assert [(r["file"], r["status"], r["to_verify"]) for r in changed] == [("sherd_B.JPG", "ok", "")] and not rerun
    names = os.listdir(out)
    assert "sherd_B_outlined.TIF" in names and not any("to_be_verified" in n for n in names)
    assert g.read_report(os.path.join(out, g.REPORT_NAME))["sherd_B.JPG"]["status"] == "ok"
    assert g.refresh_naming([(photo, out)]) == ([], [])                   # nothing left to change
    with open(project, "w", encoding="utf-8") as fh:                      # a new name: to process again
        json.dump({"fields": [], "template": "X_{photo}"}, fh)
    assert g.refresh_naming([(photo, out)]) == ([], [photo])


def test_inventory_and_powershell(tmp_path):
    for n in ("QSR25_A5_US7549_187_ceramic_outlined.tif", "QSR25_A5_US7549_190_ceramic.ai"):
        open(os.path.join(tmp_path, n), "wb").close()
    out = os.path.join(tmp_path, "inv.csv")
    n, cols = gt.inventory([str(tmp_path)], out, template="{site}_{sector}_US{us}_{number}_{material}",
                           image_columns=False)
    assert n == 2 and "number" in cols
    with open(out, encoding="utf-8-sig") as fh:
        rows = {r["file"]: r for r in csv.DictReader(fh, delimiter=";")}
    r = rows["QSR25_A5_US7549_187_ceramic_outlined.tif"]
    assert (r["number"], r["material"], r["variant"]) == ("187", "ceramic", "outlined")
    line = gt.powershell_line([str(tmp_path)], out, template="{site}_{number}")
    assert line.startswith("Get-ChildItem") and "$Matches['number']" in line and "Export-Csv" in line
