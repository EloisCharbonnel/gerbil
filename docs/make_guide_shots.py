"""Screenshots of the interface for the guides (docs/guide_images/ui_<lang>_<name>.jpg), green light theme;
also a full run of every function of the interface, whose results are printed.

The program is driven from inside (no click on the screen): photos (synthetic ones of the tests, or copies of
the JPEG photos of a folder given with --photos), an example site profile in a temporary library, a batch
renaming, a real cut-out, the review, the manual scale, a conversion of RAW photos (--raw FOLDER, needs Adobe
DNG Converter), the final review and the deposit check, the plates, free plates, contact sheets, inventory and
thumbnails, the profile window, the dark theme. Everything is written in a neutral folder (C:\\Gerbil_demo),
deleted at the end; the photos given are only read. Nothing of the user's settings or profiles is touched.
Needs a screen.

    py -3 docs/make_guide_shots.py [fr] [en] [--photos FOLDER] [--raw FOLDER] [--out FOLDER] [--colour] [--stop-after SHOT] [--keep]"""
import glob
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

DOCS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DOCS)
OUT = os.path.join(DOCS, "guide_images")

MATERIAL = {"fr": ("céramique", "céramique glaçurée"), "en": ("pottery", "glazed pottery")}
EXAMPLE = {
    "fr": dict(name="Exemple", description="Exemple de profil : un site fictif, ses champs et son modèle de nom",
               fields=[("site", "Site", True, "Code du site, par exemple EX24"),
                       ("us", "US", True, "Unité stratigraphique, le numéro seul"),
                       ("number", "Numéro", False, "Numéro d'inventaire de l'objet"),
                       ("material", "Matière", False, "céramique, métal, verre, os…")],
               folder="EX24_mobilier", raw="EX24_terrain"),
    "en": dict(name="Example", description="Example profile: a made-up site, its fields and its name template",
               fields=[("site", "Site", True, "Site code, e.g. EX24"),
                       ("us", "Context", True, "Stratigraphic unit, the number only"),
                       ("number", "Number", False, "Inventory number of the object"),
                       ("material", "Material", False, "pottery, metal, glass, bone…")],
               folder="EX24_finds", raw="EX24_field"),
}


def synthetic_photos(folder):
    """Six synthetic photos: light and dark backgrounds, a label, a cast shadow."""
    sys.path[:0] = [ROOT, os.path.join(ROOT, "tests")]
    import synthetic
    from PIL import Image
    kinds = [dict(seed=1), dict(seed=2, shadow=True), dict(seed=3, dark=True, label=True), dict(seed=4),
             dict(seed=5, dark=True), dict(seed=6)]
    for k, kw in enumerate(kinds, 1):
        rgb = synthetic.photo(px_cm=80.0, size=(1600, 2400), **kw)[0]
        Image.fromarray(rgb).save(os.path.join(folder, f"IMG_{k:04d}.jpg"), quality=92)


def window_image(widget):
    """The picture of a Gerbil window, asked from Windows itself (PrintWindow), not read from the screen:
    another window in front, or a screen gone to sleep, never shows in it. None if it cannot be read."""
    import ctypes
    from ctypes import wintypes
    from PIL import Image
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
    H = wintypes.HANDLE                                                      # 64-bit handles: declared
    user32.GetAncestor.argtypes, user32.GetAncestor.restype = [wintypes.HWND, ctypes.c_uint], wintypes.HWND
    user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetDC.argtypes, user32.GetDC.restype = [wintypes.HWND], H
    user32.ReleaseDC.argtypes = [wintypes.HWND, H]
    user32.PrintWindow.argtypes = [wintypes.HWND, H, ctypes.c_uint]
    gdi32.CreateCompatibleDC.argtypes, gdi32.CreateCompatibleDC.restype = [H], H
    gdi32.CreateCompatibleBitmap.argtypes, gdi32.CreateCompatibleBitmap.restype = [H, ctypes.c_int, ctypes.c_int], H
    gdi32.SelectObject.argtypes, gdi32.SelectObject.restype = [H, H], H
    gdi32.GetDIBits.argtypes = [H, H, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint]
    gdi32.DeleteObject.argtypes = [H]
    gdi32.DeleteDC.argtypes = [H]
    hwnd = user32.GetAncestor(wintypes.HWND(widget.winfo_id()), 2)          # GA_ROOT: the top window
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    if w <= 0 or h <= 0:
        return None
    hdc = user32.GetDC(hwnd)
    mem = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mem, bmp)
    ok = user32.PrintWindow(hwnd, mem, 1 | 2)                                # PW_CLIENTONLY | PW_RENDERFULLCONTENT

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32), ("biHeight", ctypes.c_int32),
                    ("biPlanes", ctypes.c_uint16), ("biBitCount", ctypes.c_uint16),
                    ("biCompression", ctypes.c_uint32), ("biSizeImage", ctypes.c_uint32),
                    ("biXPelsPerMeter", ctypes.c_int32), ("biYPelsPerMeter", ctypes.c_int32),
                    ("biClrUsed", ctypes.c_uint32), ("biClrImportant", ctypes.c_uint32)]
    info = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    lines = gdi32.GetDIBits(mem, bmp, 0, h, buf, ctypes.byref(info), 0)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mem)
    user32.ReleaseDC(hwnd, hdc)
    if not ok or lines != h:
        return None
    im = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    return None if im.getextrema() == ((0, 0), (0, 0), (0, 0)) else im


def arg(name):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def main(lang):
    import tkinter  # noqa: F401  (fails early without a screen)
    from PIL import Image
    ex = EXAMPLE[lang]
    src_photos, src_raw, out_dir = arg("--photos"), arg("--raw"), arg("--out") or OUT
    os.makedirs(out_dir, exist_ok=True)
    # a neutral path, shown in the pictures (no user name): C:\Gerbil_demo, else the temporary folder
    tmp = os.path.join((os.environ.get("SystemDrive") or "C:") + os.sep, "Gerbil_demo")
    try:
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
    except OSError:
        tmp = tempfile.mkdtemp(prefix="gerbil_shots_")
    folder = os.path.join(tmp, ex["folder"])
    os.makedirs(folder)
    if src_photos:
        for f in sorted(glob.glob(os.path.join(src_photos, "*"))):
            if os.path.splitext(f)[1].lower() in (".jpg", ".jpeg", ".tif", ".tiff", ".png"):
                shutil.copy2(f, folder)
    else:
        synthetic_photos(folder)
    raw_folder = None
    if src_raw:
        raw_folder = os.path.join(tmp, ex["raw"])
        os.makedirs(raw_folder)
        for f in sorted(glob.glob(os.path.join(src_raw, "*")))[:3]:
            if os.path.isfile(f):
                shutil.copy2(f, raw_folder)
    names = sorted(os.listdir(folder))
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        # keep the screen on while it runs: a screen gone to sleep gives black screenshots
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000002 | 0x00000001)
    except Exception:                                   # noqa: BLE001
        pass
    sys.path.insert(0, ROOT)                            # gerbil, gerbil_dng, gerbil_plates… as for the interface
    gui = os.path.join(ROOT, "gerbil_gui.pyw")
    loader = importlib.machinery.SourceFileLoader("gerbil_gui", gui)
    spec = importlib.util.spec_from_loader("gerbil_gui", loader)
    gg = importlib.util.module_from_spec(spec)
    loader.exec_module(gg)
    gg.PROFILES_DIR = os.path.join(tmp, "profiles")
    os.makedirs(gg.PROFILES_DIR)
    fields = [{"key": k, "label": lab, "required": req, "meaning": m, "iptc": ""} for k, lab, req, m in ex["fields"]]
    profile = {"name": ex["name"], "background": "auto", "learned_first": False, "scales": [], "settings": {},
               "description": ex["description"],
               "project": {"fields": fields, "template": "{site}_US{us}_{number}_{material}", "rule": "",
                           "ascii_names": True,
                           "common": {}, "photos": {}, "iptc": {"creator": "", "copyright": ""}}}
    with open(gg.profile_path(ex["name"]), "w", encoding="utf-8") as fh:
        json.dump(profile, fh, ensure_ascii=False)
    messages = []
    gg.App.save_settings = lambda self: None
    gg.os.startfile = lambda p: messages.append(("open", p))
    for name in ("showinfo", "showwarning", "showerror"):
        setattr(gg.messagebox, name, lambda *a, n=name, **k: messages.append((n, a[1] if len(a) > 1 else a)))
    for name in ("askyesno", "askokcancel", "askyesnocancel"):
        setattr(gg.messagebox, name, lambda *a, **k: False)
    chosen_dir = {"value": ""}
    gg.filedialog.askdirectory = lambda *a, **k: chosen_dir["value"]
    gg.filedialog.asksaveasfilename = lambda *a, **k: os.path.join(tmp, "inventory.csv")
    gg.load_settings = lambda: dict(gg.DEFAULTS, lang=lang, theme="green", dark=False, profile=ex["name"],
                                    output_mode="next", output_dir="", last_dir="", jobs=2, open=False,
                                    cutout="colour" if "--colour" in sys.argv else gg.DEFAULTS["cutout"])
    tops, made = [], []
    top_init = gg.tk.Toplevel.__init__

    def track(self, *a, **k):
        top_init(self, *a, **k)
        tops.append(self)
    gg.tk.Toplevel.__init__ = track
    proj_init = gg.ProjectWindow.__init__

    def track_project(self, *a, **k):
        made.append(self)
        proj_init(self, *a, **k)
    gg.ProjectWindow.__init__ = track_project

    root = gg.tk.Tk()
    app = gg.App(root, [folder])
    app.apply_profile()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = int(1280 * app.k), int(800 * app.k)
    root.geometry(f"{min(w, sw - 40)}x{min(h, sh - 80)}+20+20")
    report = []

    def note(*parts):
        line = " ".join(str(p) for p in parts)
        report.append(line)
        print("  >", line, flush=True)

    def shot(widget, name, crop=None):
        widget.update_idletasks()
        widget.update()
        widget.lift()
        widget.attributes("-topmost", True)
        widget.update()
        widget.after(300)
        widget.update()
        im = window_image(widget)
        for _ in range(8):                              # Windows may not draw for a moment (screen off): retry
            if im is not None:
                break
            time.sleep(1.5)
            widget.update()
            im = window_image(widget)
        if im is None:
            note("shot", name, "NOT TAKEN (the window could not be read)")
            widget.attributes("-topmost", False)
            return
        if crop:
            im = im.crop(crop(im.size))
        if im.width > 1600:                             # enough for a page 18 cm wide; lighter files
            im = im.resize((1600, round(im.height * 1600 / im.width)), Image.Resampling.LANCZOS)
        im.save(os.path.join(out_dir, f"ui_{lang}_{name}.jpg"), quality=86, optimize=True)
        widget.attributes("-topmost", False)
        print("   shot", name, im.size, flush=True)
        if name == arg("--stop-after"):                 # only the shots up to this one
            steps.clear()

    def new_tops(n):
        return [t for t in tops[n:] if t.winfo_exists()]

    def close(n):
        for t in new_tops(n):
            t.destroy()

    steps = []

    def then(fn):
        steps.append(fn)
        return fn

    def go(delay=400):
        if not steps:
            finish()
            return
        fn = steps.pop(0)

        def safe():                                     # a step that fails is noted, the next ones still run
            try:
                fn()
            except Exception as e:                      # noqa: BLE001
                note("ERROR in", getattr(fn, "__name__", "step"), f"{type(e).__name__}: {e}")
                go()
        root.after(delay, safe)

    def wait_for(pred, timeout, label):
        start = time.time()

        def poll():
            if pred():
                note(label, f"done in {time.time() - start:.0f} s")
                go(300)
            elif time.time() - start > timeout:
                note(label, "TIMEOUT")
                go(300)
            else:
                root.after(500, poll)
        root.after(500, poll)

    # ------------------------------------------------------------------ 01 sources, profile
    @then
    def s_sources():
        app.show_page(gg.P_SOURCES)
        shot(root, "sources")
        shot(root, "rail", crop=lambda s: (0, 0, int(290 * app.k), s[1]))
        note("step 01:", app.step_sub[0].get())
        n = len(tops)
        gg.ProfileWindow(app, ex["name"])
        root.update()
        root.after(700, lambda: (shot(new_tops(n)[0], "profile") if new_tops(n) else note("profile window missing"),
                                 close(n), go()))

    # ------------------------------------------------------------------ 02 batch renaming
    @then
    def s_project():
        app.project()
        root.after(1200, s_project_fill)

    def s_project_fill():
        pw = made[-1]
        mat, glazed = MATERIAL[lang]
        for k, name in enumerate(pw.photos):
            if k == len(pw.photos) - 1 and len(pw.photos) > 3:
                pw.pr["photos"][name] = {"number": str(k + 1)}          # one left incomplete: to verify
                continue
            us = ("1043", "1051", "1062")[min(2, k * 3 // max(1, len(pw.photos)))]
            pw.pr["photos"][name] = {"us": us, "number": str(k + 1),
                                     "material": glazed if "9118" in name else mat}
        pw.pr["common"].update(site="EX24")
        pw.rebuild()
        pw.fill()
        kids = pw.tree.get_children()
        if kids:
            pw.tree.selection_set(kids[0])
            pw.tree.see(kids[0])
        root.after(900, lambda: (shot(pw.win, "project"), pw.save(), pw.win.destroy(), go()))

    @then
    def s_naming():
        app.show_page(gg.P_NAMING)
        shot(root, "naming")
        note("step 02:", app.step_sub[1].get())
        app.show_page(gg.P_META)
        kids = app.meta_tree.get_children()
        if kids:
            app.meta_tree.selection_set(kids[-1])
        shot(root, "meta")
        rows = [app.meta_tree.item(k, "values") for k in kids]
        note("check the metadata:", len(rows), "rows;", sum(1 for r in rows if "rifier" in str(r) or "verify" in str(r)),
             "to verify")
        for r in rows[:3] + rows[-1:]:
            note("   ", " | ".join(str(v) for v in r))
        go()

    # ------------------------------------------------------------------ 03 cut-out
    @then
    def s_cutout():
        app.show_page(gg.P_CUTOUT)
        shot(root, "cutout_ready")
        app.run(kind="cutout")
        root.after(1000, lambda: shot(root, "cutout_running"))
        wait_for(lambda: app.proc is None, 1200, "cut-out of " + str(len(names)) + " photos")

    @then
    def s_results():
        app.show_page(gg.P_CUTOUT)
        t = app.runs["cutout"]["table"]
        rows = [t.item(k, "values") for k in t.get_children()]
        for r in rows:
            note("   ", " | ".join(str(v) for v in r))
        if t.get_children():
            t.selection_set(t.get_children()[0])
        shot(root, "cutout")
        note("step 03:", app.step_sub[3].get(), "| status:", app.status.get())
        res = os.path.join(folder, "outlined_result")
        note("outlined_result:", len(os.listdir(res)) if os.path.isdir(res) else "missing", "entries")
        app.show_page(gg.P_REVIEW)
        shot(root, "review_page")
        n = len(tops)
        app.review()
        root.update()
        root.after(2500, lambda: (shot(new_tops(n)[0], "review") if new_tops(n) else note("review window missing"),
                                  close(n), go()))

    @then
    def s_scale():
        n = len(tops)
        app._open_scale(os.path.join(folder, names[0]))
        root.update()
        root.after(1500, lambda: (shot(new_tops(n)[0], "scale") if new_tops(n) else note("scale window missing"),
                                  close(n), go()))

    # ------------------------------------------------------------------ 04 conversion
    @then
    def s_convert():
        app.show_page(gg.P_CONVERT)
        if not raw_folder:
            shot(root, "convert")
            go()
            return
        app.add_paths([raw_folder])
        app.dng_vars["tiff"].set(False)
        app.run(kind="dng")
        wait_for(lambda: app.proc is None, 900, "conversion of the RAW photos")

    @then
    def s_convert_done():
        if raw_folder:
            t = app.runs["dng"]["table"]
            for k in t.get_children():
                note("    dng:", " | ".join(str(v) for v in t.item(k, "values")))
            if t.get_children():
                t.selection_set(t.get_children()[0])
            shot(root, "convert")
            note("step 04:", app.step_sub[5].get())
            note("raw folder:", sorted(os.listdir(raw_folder)))
        go()

    # ------------------------------------------------------------------ 05 final review, deposit
    @then
    def s_final():
        app.show_page(gg.P_FINAL)
        shot(root, "final")
        note("step 05:", app.step_sub[6].get())
        n = len(tops)
        gg.DepositWindow(app)
        root.update()
        root.after(800, lambda: s_deposit(n))

    def s_deposit(n):
        win = new_tops(n)
        if not win:
            note("deposit window missing")
            go()
            return
        shot(win[0], "deposit")
        obj = deposit_obj[-1] if deposit_obj else None
        if obj is None:
            close(n)
            go()
            return
        obj.folder.set(os.path.join(folder, "outlined_result"))
        obj.run()
        wait_for(lambda: str(obj.btn.state()).find("disabled") < 0 and obj.msg.get() not in ("", gg.tr("Working…")),
                 300, "deposit check")
        steps.insert(0, lambda: (note("deposit:", obj.msg.get()), shot(win[0], "deposit_done"), close(n), go()))

    deposit_obj = []
    dep_init = gg.DepositWindow.__init__

    def track_dep(self, *a, **k):
        deposit_obj.append(self)
        dep_init(self, *a, **k)
    gg.DepositWindow.__init__ = track_dep

    # ------------------------------------------------------------------ 06 publication
    @then
    def s_publication():
        app.show_page(gg.P_PUBLICATION)
        shot(root, "publication")
        app.results = [os.path.join(folder, "outlined_result")]
        n = len(tops)
        app.plates()
        root.update()
        root.after(2500, lambda: s_plates(n))

    plates_obj = []
    pl_init = gg.PlatesWindow.__init__

    def track_pl(self, *a, **k):
        plates_obj.append(self)
        pl_init(self, *a, **k)
    gg.PlatesWindow.__init__ = track_pl

    def s_plates(n):
        win = new_tops(n)
        if not win or not plates_obj:
            note("plates window missing")
            go()
            return
        shot(win[0], "plates")
        pw = plates_obj[-1]
        pw.write()
        wait_for(lambda: "write_btn" in pw.__dict__ and "disabled" not in str(pw.write_btn.state()), 600,
                 "plates")
        steps.insert(0, lambda: (note("plates:", pw.msg.get()), shot(win[0], "plates_done"), close(n), go()))

    @then
    def s_free():
        chosen_dir["value"] = folder
        n = len(tops)
        app.free_plates()
        root.update()
        root.after(3000, lambda: (shot(new_tops(n)[0], "free_plates") if new_tops(n) else note("free plates missing"),
                                  close(n), go()))

    def tool(cls, name, action, done):
        objs = []
        init = cls.__init__

        def track_tool(self, *a, **k):
            objs.append(self)
            init(self, *a, **k)
        cls.__init__ = track_tool

        def start():
            n = len(tops)
            cls(app)
            root.update()

            def after_open():
                win = new_tops(n)
                if not win or not objs:
                    note(name, "window missing")
                    go()
                    return
                shot(win[0], name)
                o = objs[-1]
                action(o)
                wait_for(lambda: done(o), 600, name)
                steps.insert(0, lambda: (note(name + ":", getattr(o, "msg", None) and o.msg.get()),
                                         shot(win[0], name + "_done"), close(n), go()))
            root.after(1200, after_open)
        then(start)

    tool(gg.ContactWindow, "contact", lambda o: (o.folder.set(folder), o.run()),
         lambda o: "disabled" not in str(o.btn.state()))
    tool(gg.InventoryWindow, "inventory", lambda o: o.write(),
         lambda o: os.path.exists(os.path.join(tmp, "inventory.csv")))
    tool(gg.ThumbnailsWindow, "thumbnails", lambda o: (o.folder.set(os.path.join(folder, "outlined_result")),
                                                       o.run()),
         lambda o: "thumbnail" in o.msg.get() or "vignette" in o.msg.get())

    # ------------------------------------------------------------------ dark theme
    @then
    def s_dark():
        app.set_theme("green", True)
        app.show_page(gg.P_CUTOUT)
        root.after(600, lambda: (shot(root, "dark"), go()))

    def finish():
        note("messages:", messages)
        for sub in ("outlined_result", "outlined_result/plates", "contact_sheets", "outlined_result/deposit_check"):
            p = os.path.join(folder, sub)
            if os.path.isdir(p):
                note("folder", sub, ":", len(os.listdir(p)), "entries", sorted(os.listdir(p))[:6])
        with open(os.path.join(out_dir, f"run_{lang}.txt"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(report))
        root.destroy()

    go(1500)
    root.mainloop()
    if "--keep" not in sys.argv:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    langs = [a for a in sys.argv[1:] if a in ("fr", "en")] or ["fr", "en"]
    rest = [a for a in sys.argv[1:] if a not in ("fr", "en")]
    if len(langs) > 1:                       # one process per language: a fresh module and window each time
        for lg in langs:
            subprocess.run([sys.executable, os.path.abspath(__file__), lg] + rest, check=True)
    else:
        print(langs[0], flush=True)
        main(langs[0])
