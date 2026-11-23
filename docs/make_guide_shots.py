"""Screenshots of the interface for the guides (docs/guide_images/ui_<lang>_<name>.jpg), green light theme.

The program is driven from inside (no click on the screen): synthetic photos of the tests, an example site
profile in a temporary library, a batch renaming, a real cut-out, then every step and the main windows are
shot. Nothing of the user's settings or profiles is touched. Needs a screen. Run again after a change of the
interface: py -3 docs/make_guide_shots.py [fr] [en]"""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

DOCS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DOCS)
OUT = os.path.join(DOCS, "guide_images")

EXAMPLE = {
    "fr": dict(name="Exemple", description="Exemple de profil : un site fictif, ses champs et son modèle de nom",
               fields=[("site", "Site", True, "Code du site, par exemple EX24"),
                       ("us", "US", True, "Unité stratigraphique, le numéro seul"),
                       ("number", "Numéro", False, "Numéro d'inventaire de l'objet"),
                       ("material", "Matière", False, "céramique, métal, verre, os…")],
               values=[("EX24", "1043", "1", "céramique"), ("EX24", "1043", "2", "céramique"),
                       ("EX24", "1051", "3", "métal"), ("EX24", "1051", "4", "")]),
    "en": dict(name="Example", description="Example profile: a made-up site, its fields and its name template",
               fields=[("site", "Site", True, "Site code, e.g. EX24"),
                       ("us", "Context", True, "Stratigraphic unit, the number only"),
                       ("number", "Number", False, "Inventory number of the object"),
                       ("material", "Material", False, "pottery, metal, glass, bone…")],
               values=[("EX24", "1043", "1", "pottery"), ("EX24", "1043", "2", "pottery"),
                       ("EX24", "1051", "3", "metal"), ("EX24", "1051", "4", "")]),
}


def photos(folder):
    """Six synthetic photos: light and dark backgrounds, a label, a cast shadow."""
    sys.path[:0] = [ROOT, os.path.join(ROOT, "tests")]
    import synthetic
    from PIL import Image
    kinds = [dict(seed=1), dict(seed=2, shadow=True), dict(seed=3, dark=True, label=True), dict(seed=4),
             dict(seed=5, dark=True), dict(seed=6)]
    for k, kw in enumerate(kinds, 1):
        rgb = synthetic.photo(px_cm=80.0, size=(1600, 2400), **kw)[0]
        Image.fromarray(rgb).save(os.path.join(folder, f"IMG_{k:04d}.jpg"), quality=92)


def main(lang):
    import tkinter  # noqa: F401  (fails early without a screen)
    from PIL import Image, ImageGrab
    ex = EXAMPLE[lang]
    # a neutral path, shown in the pictures (no user name): C:\Gerbil_demo, else the temporary folder
    tmp = os.path.join((os.environ.get("SystemDrive") or "C:") + os.sep, "Gerbil_demo")
    try:
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
    except OSError:
        tmp = tempfile.mkdtemp(prefix="gerbil_shots_")
    folder = os.path.join(tmp, "EX24_mobilier" if lang == "fr" else "EX24_finds")
    os.makedirs(folder)
    photos(folder)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:                                   # noqa: BLE001
        pass
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
                           "common": {}, "photos": {}, "iptc": {"creator": "", "copyright": ""}}}
    with open(gg.profile_path(ex["name"]), "w", encoding="utf-8") as fh:
        json.dump(profile, fh, ensure_ascii=False)
    gg.App.save_settings = lambda self: None
    gg.os.startfile = lambda p: None
    for name in ("showinfo", "showwarning", "showerror"):
        setattr(gg.messagebox, name, lambda *a, **k: None)
    for name in ("askyesno", "askokcancel", "askyesnocancel"):
        setattr(gg.messagebox, name, lambda *a, **k: False)
    gg.filedialog.askdirectory = lambda *a, **k: ""
    gg.load_settings = lambda: dict(gg.DEFAULTS, lang=lang, theme="green", dark=False, profile=ex["name"],
                                    output_mode="next", output_dir="", last_dir="", jobs=2, open=False)
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

    def shot(widget, name, crop=None):
        widget.update_idletasks()
        widget.update()
        widget.lift()
        widget.attributes("-topmost", True)
        widget.update()
        widget.after(250)
        widget.update()
        x, y, ww, hh = widget.winfo_rootx(), widget.winfo_rooty(), widget.winfo_width(), widget.winfo_height()
        im = ImageGrab.grab(bbox=(x, y, x + ww, y + hh), all_screens=True).convert("RGB")
        if crop:
            im = im.crop(crop(im.size))
        if im.width > 1600:                             # enough for a page 18 cm wide; lighter files
            im = im.resize((1600, round(im.height * 1600 / im.width)), Image.Resampling.LANCZOS)
        im.save(os.path.join(OUT, f"ui_{lang}_{name}.jpg"), quality=86, optimize=True)
        widget.attributes("-topmost", False)
        print("  ", name, im.size, flush=True)

    def step(fn, delay=400):
        root.after(delay, fn)

    def s_sources():
        app.show_page(gg.P_SOURCES)
        shot(root, "sources")
        shot(root, "rail", crop=lambda s: (0, 0, int(290 * app.k), s[1]))
        app.project()
        step(s_project, 900)

    def s_project():
        pw = made[-1]
        names = pw.photos
        for name, vals in zip(names, ex["values"]):
            pw.pr["photos"][name] = dict(zip(("site", "us", "number", "material"), vals))
        pw.rebuild()
        pw.fill()
        kids = pw.tree.get_children()
        if kids:
            pw.tree.selection_set(kids[0])
        shot(pw.win, "project")
        pw.save()
        pw.win.destroy()
        step(s_naming)

    def s_naming():
        app.show_page(gg.P_NAMING)
        shot(root, "naming")
        app.show_page(gg.P_META)
        kids = app.meta_tree.get_children()
        if kids:
            app.meta_tree.selection_set(kids[-1])
        shot(root, "meta")
        app.show_page(gg.P_CUTOUT)
        shot(root, "cutout_ready")
        app.run(kind="cutout")
        step(wait, 1500)

    def wait():
        if app.proc is not None:
            root.after(800, wait)
            return
        step(s_results, 600)

    def s_results():
        app.show_page(gg.P_CUTOUT)
        t = app.runs["cutout"]["table"]
        if t.get_children():
            t.selection_set(t.get_children()[0])
        shot(root, "cutout")
        app.show_page(gg.P_REVIEW)
        shot(root, "review_page")
        n = len(tops)
        app.review()
        root.update()
        step(lambda: s_review(n), 1500)

    def s_review(n):
        new = [t for t in tops[n:] if t.winfo_exists()]
        if new:
            shot(new[0], "review")
            for t in new:
                t.destroy()
        app.show_page(gg.P_CONVERT)
        shot(root, "convert")
        app.show_page(gg.P_FINAL)
        shot(root, "final")
        app.show_page(gg.P_PUBLICATION)
        shot(root, "publication")
        n = len(tops)
        app.plates()
        root.update()
        step(lambda: s_plates(n), 1800)

    def s_plates(n):
        new = [t for t in tops[n:] if t.winfo_exists()]
        if new:
            shot(new[0], "plates")
            for t in new:
                t.destroy()
        app.set_theme("green", True)
        app.show_page(gg.P_CUTOUT)
        step(s_dark, 500)

    def s_dark():
        shot(root, "dark")
        root.destroy()

    root.after(1500, s_sources)
    root.mainloop()
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    langs = sys.argv[1:] or ["fr", "en"]
    if len(langs) > 1:                       # one process per language: a fresh module and window each time
        for lg in langs:
            subprocess.run([sys.executable, os.path.abspath(__file__), lg], check=True)
    else:
        print(langs[0], flush=True)
        main(langs[0])
