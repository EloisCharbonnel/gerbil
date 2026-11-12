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
