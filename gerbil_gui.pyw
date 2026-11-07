#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerbil - archaeological photo toolkit (formerly SherdCut): graphical interface of gerbil.py
© 2026 Eloïs CHARBONNEL
Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE.
This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to
redistribute it under the conditions of the licence.

Choose the photos (folders or files) and the options, then "Run": the script runs in the
background and each processed photo shows up in the log. Double-click this file to open it;
folders or photos dropped on it are added to the list.

Missing Python packages (numpy, OpenCV, Pillow, rawpy) are detected and can be installed from the window.
Console use (Install.bat):  py -3 gerbil_gui.pyw --install   (or --check: exit code 1 if missing)
"""

import importlib.util
import json
import math
import os
import queue
import re
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

FROZEN = getattr(sys, "frozen", False)            # .exe version (PyInstaller): no Python needed
HERE = os.path.dirname(sys.executable) if FROZEN else os.path.dirname(os.path.abspath(__file__))
RESOURCES = getattr(sys, "_MEIPASS", HERE)
SCRIPT = os.path.join(HERE, "gerbil.py")
ENGINE = os.path.join(HERE, "gerbil_cli.exe")          # processing engine of the .exe version
README = os.path.join(HERE, "README.md")
ICONS = os.path.join(RESOURCES, "icons")
SETTINGS = os.path.join(os.path.expanduser("~"), ".gerbil.json")
OLD_SETTINGS = [os.path.join(os.path.expanduser("~"), n)       # earlier names: settings taken over
                for n in (".sherdcut.json", ".detourage_ceramique_gui.json")]
EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".png"}
RAW_EXTENSIONS = {".dng", ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".orf", ".rw2", ".raf", ".pef", ".srw", ".3fr", ".iiq"}
EXTENSIONS |= RAW_EXTENSIONS


def open_photo_image(path, small=False):
    """The photo upright, as the engine sees it (RAW: developed by rawpy the same way; small: half size,
    for previews). Returns a PIL image in RGB."""
    from PIL import Image, ImageOps
    if os.path.splitext(path)[1].lower() in RAW_EXTENSIONS:
        import rawpy
        with rawpy.imread(path) as raw:
            return Image.fromarray(raw.postprocess(use_camera_wb=True, output_bps=8, half_size=small))
    with Image.open(path) as im:
        if small:
            im.draft("RGB", (1400, 1400))
        return ImageOps.exif_transpose(im).convert("RGB")


CREDITS = "© 2026 Eloïs CHARBONNEL"
VERSION = "2.1"
REQUIRED = {"numpy": "numpy", "cv2": "opencv-python-headless", "PIL": "pillow",
            "rawpy": "rawpy"}   # module: pip package
AI_PACKAGE = "onnxruntime-directml" if sys.platform == "win32" else "onnxruntime"
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# palette: violet ink, ITINERA blue-green, light grey squared paper
VIOLET, VIOLET_2, LILAS, LILAS_2, LILAS_PALE = "#34245A", "#5B4794", "#DCD5EC", "#C9BFE3", "#F1EEF7"
TEAL, TERRA = "#215353", "#B5582F"
PAPER, GRID, GRID_2, LINE = "#F3F3F4", "#E5E5E8", "#D5D5DA", "#D3CEDC"
# the earlier names, used by the other windows
LAVENDER, MINT, TERRACOTTA = "#B5A8DA", "#9FD3CF", "#D9A58C"
LAVENDER_DARK, LAVENDER_PALE, LAVENDER_LINE = VIOLET, LILAS_PALE, LINE
MINT_DARK, TERRACOTTA_DARK = TEAL, TERRA
WINDOW_BG, CARD_BG, TEXT, MUTED, RED = PAPER, "#FFFFFF", "#1F1D24", "#66626E", "#A8322B"

# fonts: serif only (titles, text, typewriter numbers); the ones of the fonts folder when shipped, else the
# closest ones of the system
FONTS = os.path.join(RESOURCES, "fonts")
FONT_DISPLAY, FONT_SERIF, FONT_MONO = "Georgia", "Georgia", "Courier New"


def load_fonts(root):
    """The fonts of the interface: those shipped in the fonts folder (loaded for this program only), else
    the closest ones installed (Garamond, Cambria, Georgia, Courier New)."""
    global FONT_DISPLAY, FONT_SERIF, FONT_MONO
    if sys.platform == "win32" and os.path.isdir(FONTS):
        try:
            import ctypes
            for f in os.listdir(FONTS):
                if f.lower().endswith((".ttf", ".otf")):
                    ctypes.windll.gdi32.AddFontResourceExW(os.path.join(FONTS, f), 0x10, 0)   # FR_PRIVATE
        except (OSError, AttributeError):
            pass
    from tkinter import font as tkfont
    have = set(tkfont.families(root))
    pick = lambda names: next((n for n in names if n in have), names[-1])
    FONT_DISPLAY = pick(["Cormorant Garamond", "Garamond", "Georgia"])
    FONT_SERIF = pick(["Source Serif 4", "Source Serif Pro", "Cambria", "Georgia"])
    FONT_MONO = pick(["Courier Prime", "Courier New"])


# languages of the interface (main window): French or English
LANG = "fr"


def system_lang():
    """fr when Windows (or the locale) is in French, else en."""
    try:
        if sys.platform == "win32":
            import ctypes
            return "fr" if ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0xFF == 0x0C else "en"
        import locale
        return "fr" if (locale.getlocale()[0] or "").lower().startswith("fr") else "en"
    except Exception:
        return "en"


def T(fr, en):
    """The text in the language of the interface."""
    return fr if LANG == "fr" else en


try:                                                    # French texts of the other windows
    from gerbil_lang_fr import FR as FR_TEXT
except ImportError:
    FR_TEXT = {}


def tr(en):
    """An English text of the windows, in French when the interface is in French (gerbil_lang_fr.py)."""
    return FR_TEXT.get(en, en) if LANG == "fr" else en


STEPS = [("Photographies sources", "Source photographs"), ("Nommage et métadonnées", "Naming and metadata"),
         ("Traitement", "Processing"), ("Vérification", "Review"), ("Publication", "Publication")]

# settings of the processing: kind, label (fr, en), choices or (min, max, step)
OPTION_SPECS = {
    "psd": ("check", ("Fichier Photoshop (.psd)", "Photoshop file (.psd)"), None),
    "original_layer": ("check", ("Calque caché de la photographie entière", "Hidden layer of the whole photo"), None),
    "original_copy": ("check", ("Copie de la photographie originale", "Copy of the original photo"), None),
    "control": ("check", ("Aperçus de contrôle (to_control)", "Control previews (to_control)"), None),
    "background": ("choice", ("Fond des TIFF", "TIFF background"), ["transparent", "white"]),
    "compression": ("choice", ("Compression des TIFF", "TIFF compression"), ["lzw", "zip", "none"]),
    "jobs": ("number", ("Photographies en parallèle", "Photos in parallel"), (1, 64, 1)),
    "open": ("check", ("Ouvrir les résultats à la fin", "Open the results at the end"), None),
    "scale": ("check", ("Chercher l'échelle", "Look for the scale"), None),
    "scale_cm": ("choice", ("Longueur de l'échelle (cm)", "Scale length (cm)"), ["auto", "5", "10"]),
    "default_ppi": ("number", ("Sans échelle (ppp)", "Without scale (ppi)"), (50, 2400, 50)),
    "layout": ("choice", ("Place de l'échelle", "Scale placement"), ["recompose", "original"]),
    "margin_cm": ("number", ("Marge (cm)", "Margin (cm)"), (0, 5, 0.1)),
    "gap_cm": ("number", ("Écart objet / échelle (cm)", "Object / scale gap (cm)"), (0, 5, 0.1)),
    "remove_putty": ("check", ("Retirer la pâte à fixe", "Remove mounting putty"), None),
    "ai": ("check", ("Second avis de l'IA", "AI second opinion"), None),
    "ai_model": ("choice", ("Modèle d'IA", "AI model"), ["isnet", "birefnet"]),
    "ai_device": ("choice", ("Processeur de l'IA", "AI device"), ["auto", "cpu"]),
}
OPTION_KEYS = list(OPTION_SPECS)
ESSENTIAL_OPTIONS = ["psd", "background", "scale"]
ADVANCED_OPTIONS = [(("Fichiers", "Files"), ["original_layer", "original_copy", "control", "compression"]),
                    (("Traitement", "Run"), ["jobs", "open"]),
                    (("Échelle et mise en page", "Scale and layout"),
                     ["scale_cm", "default_ppi", "layout", "margin_cm", "gap_cm"]),
                    (("Nettoyage", "Cleaning"), ["remove_putty", "ai", "ai_model", "ai_device"])]


def option_value(key, v):
    """A setting in a comparable form (the fields give text)."""
    kind = OPTION_SPECS[key][0]
    if kind == "check":
        return v in (True, 1, "1", "True", "true")
    if kind == "number":
        return round(float(str(v).replace(",", ".")), 3)
    return str(v)


HELP_FR = {
    "background": "Fond des fichiers TIFF : transparent, ou blanc.",
    "compression": "Compression des TIFF, toutes sans perte : LZW (la plus compatible), ZIP (un peu plus petite), "
                   "aucune.",
    "psd": "Écrire NOM.psd avec les calques « Scale » et « Ceramic » (masques de fusion modifiables).",
    "original_layer": "Garder dans le PSD un calque caché de la photographie entière (décoché : PSD 2 à 4 fois "
                      "plus léger).",
    "original_copy": "Copier la photographie originale dans le dossier des résultats.",
    "control": "Écrire les aperçus de contrôle (dossier to_control).",
    "layout": "recompose : échelle redressée et centrée sous l'objet. original : échelle laissée où elle a été "
              "photographiée.",
    "margin_cm": "Marge autour des objets, en cm.",
    "gap_cm": "Écart entre l'objet et l'échelle, en cm.",
    "scale": "Chercher l'échelle (cases de 1 cm ou réglet millimétré) pour fixer la résolution 1:1.",
    "scale_cm": "Imposer la longueur de l'échelle si le compte des cases ne convient pas (auto : cases comptées).",
    "default_ppi": "Résolution utilisée quand aucune échelle n'est trouvée.",
    "remove_putty": "Retirer automatiquement la pâte à fixe soupçonnée (sinon elle est seulement signalée, zone "
                    "rouge sur l'aperçu).",
    "ai": "Second avis de l'IA : le réseau peut seulement retirer du fond que le script a gardé (perforations, "
          "écarts entre tessons, halos), jamais ajouter. Nécessite onnxruntime.",
    "ai_model": "IS-Net : rapide, utilise la carte graphique. BiRefNet : plus précis sur les perforations, "
                "beaucoup plus lent (processeur).",
    "ai_device": "auto : carte graphique si possible. cpu : processeur seulement.",
    "jobs": "Nombre de photographies traitées en même temps.",
    "open": "Ouvrir le ou les dossiers de résultats à la fin.",
}


def help_text(key):
    """Help bubble of a setting, in the language of the interface."""
    return HELP_FR[key] if LANG == "fr" else HELP[key]


def scale_text(s):
    """The scale part of an engine line ('checkerboard 10 cm, 100.00 px/cm, 1.3 s') in a few words."""
    first = s.split(",")[0].strip()
    if not first or first.startswith("no scale"):
        return ""
    for en, fr in (("checkerboard", "damier"), ("ruler", "réglet"), ("manual", "manuelle"), ("learned", "apprise")):
        if first.startswith(en):
            return T(fr, en) + first[len(en):]
    return first


DOUBTS = [("scale not detected", "Échelle non trouvée", "Scale not found"),
          ("scale spotted but unreadable", "Échelle illisible", "Scale unreadable"),
          ("squares detected (not", "Longueur d'échelle inhabituelle", "Unusual scale length"),
          ("neither 5 nor 10", "Longueur d'échelle inhabituelle", "Unusual scale length"),
          ("irregular", "Échelle irrégulière", "Irregular scale"),
          ("ceramic cut by the photo edge", "Objet coupé par le bord", "Object cut by the edge"),
          ("possible mounting putty", "Pâte à fixe possible", "Possible mounting putty"),
          ("mounting putty removed", "Pâte à fixe retirée", "Mounting putty removed"),
          ("colour chart touching", "Charte couleur contre l'objet", "Colour chart against the object"),
          ("missing information", "Information manquante", "Missing information"),
          ("name does not match", "Nom hors de la règle", "Name off the rule"),
          ("output name already used", "Nom déjà utilisé", "Name already used"),
          ("looks like a paper label", "Objet pris pour une étiquette", "Object taken for a label"),
          ("no object detected", "Aucun objet trouvé", "No object found"),
          ("no ceramic kept", "Aucun objet trouvé", "No object found"),
          ("cast shadow removed", "Ombre retirée", "Shadow removed"),
          ("translucent support removed", "Support retiré", "Support removed"),
          ("scale, label or card discarded", "Échelle ou étiquette écartée", "Scale or label set aside"),
          ("paper label discarded", "Étiquette écartée", "Label set aside"),
          ("colour chart discarded", "Charte couleur écartée", "Colour chart set aside"),
          ("lying close to the scale kept", "Objet près de l'échelle gardé", "Object near the scale kept"),
          ("small isolated element discarded", "Petit élément isolé écarté", "Small isolated element set aside"),
          ("squares read by their boundaries", "Échelle lue par ses limites", "Scale read by its boundaries"),
          ("scale turned by reading its digits", "Échelle retournée", "Scale turned upright")]


def doubt_text(s):
    """A doubt or a note of the engine in a few words, in the language of the interface."""
    low = s.lower()
    for key, fr, en in DOUBTS:
        if key in low:
            return T(fr, en)
    return s[:1].upper() + s[1:]

DEFAULTS = {
    "output_mode": "next", "output_dir": "", "background": "transparent", "compression": "lzw",
    "psd": True, "original_layer": True, "original_copy": True, "control": True,
    "layout": "recompose", "margin_cm": 0.5, "gap_cm": 0.5,
    "scale": True, "scale_cm": "auto", "default_ppi": 300, "remove_putty": False,
    "ai": False, "ai_model": "isnet", "ai_device": "auto",
    "jobs": max(1, min(4, (os.cpu_count() or 2) // 2)), "open": True, "last_dir": "",
    "plates": {}, "profile": "", "lang": "",
}

HELP = {
    "background": "Background of the TIFF files: transparent, or white.",
    "compression": "TIFF compression, all lossless: LZW (the most compatible), ZIP (a little smaller), none.",
    "psd": "Write NAME.psd with the layers 'Scale' and 'Ceramic' (editable layer masks).",
    "original_layer": "Keep a hidden 'Original photo' layer in the PSD (unticked: PSD 2 to 4 times lighter).",
    "original_copy": "Copy the original photo into the result folder.",
    "control": "Write the control previews (to_control folder).",
    "layout": "Recompose: scale straightened and centred under the sherd. "
              "Original: scale left where it was photographed.",
    "margin_cm": "Margin around the objects, in cm.",
    "gap_cm": "Gap between the sherd and the scale, in cm.",
    "scale": "Look for the scale (1 cm squares or millimetre ruler) to set the 1:1 resolution.",
    "scale_cm": "Force the scale length if the count of squares does not suit (auto: squares counted).",
    "default_ppi": "Resolution used when no scale is found.",
    "remove_putty": "Remove the suspected mounting putty automatically (otherwise it is only flagged, "
                    "red area in the preview).",
    "ai": "AI second opinion: the network may only remove background the script kept "
          "(perforations, gaps between sherds, halos), never add anything. Needs onnxruntime.",
    "ai_model": "IS-Net: fast, uses the graphics card. BiRefNet: more precise on perforations, "
                "much slower (processor).",
    "ai_device": "Auto: graphics card when available. CPU: processor only.",
    "jobs": "Number of photos processed at the same time.",
    "open": "Open the result folder(s) at the end.",
}


def python_exe():
    """Console Python of the running installation (the GUI itself may run under pythonw)."""
    p = os.path.join(os.path.dirname(sys.executable), "python.exe")
    return p if os.path.exists(p) else sys.executable


def missing_packages():
    """Python packages still to install (none in the .exe version, where all is inside)."""
    if FROZEN:                                        # everything is inside the .exe version
        return []
    importlib.invalidate_caches()
    return [pip for module, pip in REQUIRED.items() if importlib.util.find_spec(module) is None]


def has_ai():
    """True when onnxruntime (the AI engine) is available."""
    if FROZEN:
        return os.path.isdir(os.path.join(RESOURCES, "onnxruntime"))
    importlib.invalidate_caches()
    return importlib.util.find_spec("onnxruntime") is not None


def pip_command(packages):
    """Command that installs packages with pip, for the Python found."""
    return [python_exe(), "-m", "pip", "install", "--disable-pip-version-check", *packages]


def imports_ok(modules):
    """Checked in a new process: a package just installed in the user folder is seen there."""
    r = subprocess.run([python_exe(), "-c", "import " + ", ".join(modules)], capture_output=True,
                       creationflags=NO_WINDOW)
    return r.returncode == 0


def console_install():
    """Install.bat: installs what is missing, in the Python running this file."""
    try:
        sys.stdout.reconfigure(line_buffering=True)      # keeps the order with pip's own output
    except Exception:
        pass
    print("Gerbil - installation of the Python packages")
    print(f"Python {sys.version.split()[0]}  ({sys.executable})\n")
    if sys.version_info < (3, 9):
        print("Python 3.9 or newer is needed: install a recent Python from https://www.python.org/downloads/")
        return 1
    if importlib.util.find_spec("pip") is None:
        subprocess.call([python_exe(), "-m", "ensurepip", "--upgrade"])
    missing = missing_packages()
    if missing:
        print("Installing:", ", ".join(missing), "\n")
        if subprocess.call(pip_command(missing)) != 0:
            print("\nThe installation failed (internet connection? proxy?).")
            return 1
    if not imports_ok(REQUIRED):
        print("\nThe packages are installed but cannot be loaded. Please send this window to the author.")
        return 1
    print("\nRequired packages: OK.")
    if not has_ai():
        answer = input("\nAlso install the optional AI second opinion (onnxruntime, about 60 MB)? [y/N] ")
        if answer.strip().lower() in ("y", "yes", "o", "oui"):
            if subprocess.call(pip_command([AI_PACKAGE])) == 0:
                print("\nAI second opinion: OK (its model is downloaded at its first use).")
            else:
                print("\nThe AI installation failed; everything else works without it.")
    print("\nAll set: open the interface with Gerbil.bat.")
    return 0


def count_photos(folder):
    """Number of photos (known extensions) in a folder."""
    try:
        return sum(1 for n in os.listdir(folder) if os.path.splitext(n)[1].lower() in EXTENSIONS)
    except OSError:
        return 0


def load_settings():
    """Settings of the interface (~/.gerbil.json, or the files of older names), with the
    defaults for what is missing."""
    s = dict(DEFAULTS)
    for path in [SETTINGS] + OLD_SETTINGS:           # (settings saved before the renaming are taken over)
        try:
            with open(path, encoding="utf-8") as fh:
                s.update({k: v for k, v in json.load(fh).items() if k in DEFAULTS})
            break
        except (OSError, ValueError):
            continue
    return s


class Tooltip:
    """Help text shown when the mouse rests on a widget. It goes away when the mouse leaves the widget
    (checked every 250 ms: a drop-down list or a window opened meanwhile can swallow the "leave" event),
    on a click, and after 8 s at most; one bubble at a time."""

    current = None                              # the bubble shown, whatever the widget

    def __init__(self, widget, text):
        """Ties the bubble to the widget: shown when the mouse rests on it, hidden on leave,
        click, focus lost or destruction."""
        self.widget, self.text, self.tip, self.job = widget, text, None, None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        widget.bind("<FocusOut>", self._hide, add="+")
        widget.bind("<Destroy>", self._hide, add="+")

    def _schedule(self, _):
        """The mouse enters: the bubble is shown after 450 ms."""
        self._hide()
        self.job = self.widget.after(450, self._show)

    def _pointer_inside(self):
        """True when the mouse pointer is over the widget (or one of its children)."""
        try:
            x, y = self.widget.winfo_pointerxy()
            w = self.widget.winfo_containing(x, y)
        except (tk.TclError, KeyError):
            return False
        while w is not None:
            if w == self.widget:
                return True
            w = getattr(w, "master", None)
        return False

    def _show(self):
        """Shows the bubble under the widget, if the mouse is still there; one bubble at a time."""
        self.job = None
        if not self._pointer_inside():
            return
        if Tooltip.current and Tooltip.current is not self:
            Tooltip.current._hide()
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, justify="left", wraplength=340, bg=TEXT, fg="white",
                 font=(FONT_SERIF, 9), padx=8, pady=5).pack()
        Tooltip.current = self
        self.shown_at = time.time()
        self.job = self.widget.after(250, self._watch)

    def _watch(self):
        """Every 250 ms: hides the bubble when the mouse has left, or after 8 s."""
        self.job = None
        if self.tip and (not self._pointer_inside() or time.time() - self.shown_at > 8):
            self._hide()
        elif self.tip:
            self.job = self.widget.after(250, self._watch)

    def _hide(self, _=None):
        """Hides the bubble and cancels what was planned."""
        if self.job:
            try:
                self.widget.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None
        if self.tip:
            try:
                self.tip.destroy()
            except tk.TclError:
                pass
            self.tip = None
        if Tooltip.current is self:
            Tooltip.current = None


MANUAL_SCALES = "gerbil_scales.json"        # next to the photos; read by gerbil.py (manual_scale_entry)
OLD_MANUAL_SCALES = "sherdcut_scales.json"  # written before the renaming: taken over, then replaced
# reasons for doubt (engine output) after which the scale can be set by hand: not found, or doubtful
SCALE_PROBLEMS = ("scale not detected", "scale spotted but unreadable", "squares detected (not",
                  "cm read (neither", "irregular scale squares", "irregular graduations",
                  "graduations partly hidden")


class ScaleWindow:
    """Manual scale of one photo: two points of known distance, clicked on the photo (upright as the
    engine sees it). Saved in MANUAL_SCALES next to the photo; the engine then uses it instead of
    looking for the scale."""

    HANDLE = 9                                  # screen pixels: radius of the point markers

    def __init__(self, app, path, seq=None, on_saved=None, learn=None):
        """seq: series of photos corrected one after the other (see App.scale_series), or None.
        on_saved: called after saving instead of offering to process the photo (review window).
        learn: called with the two points instead of saving a manual scale (site profile: learn a scale)."""
        self.learn = learn
        from PIL import Image, ImageOps, ImageTk  # only here: the window needs Pillow
        self.Image, self.ImageTk = Image, ImageTk
        self.app, self.path, self.seq, self.on_saved = app, path, seq, on_saved
        im = open_photo_image(path)
        self.full = im
        self.W, self.H = im.size
        k = min(1.0, 2000 / max(self.W, self.H))
        self.preview = im.resize((round(self.W * k), round(self.H * k)), Image.Resampling.BILINEAR)
        self.k_preview = k
        self.points = []
        self.drag = None
        self.pan = None
        self.file = os.path.join(os.path.dirname(path), MANUAL_SCALES)
        self.old_file = os.path.join(os.path.dirname(path), OLD_MANUAL_SCALES)
        entry = self._load().get(os.path.basename(path))

        self.win = win = tk.Toplevel(app.root)
        count = f"{seq['total'] - len(seq['todo'])} / {seq['total']}" if seq else ""
        win.title((tr("Learn a scale - ") if learn else tr("Set scale - ")) + os.path.basename(path) + (f"  ({count})" if seq else ""))
        win.configure(bg=WINDOW_BG)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{int(sw * 0.8)}x{int(sh * 0.8)}+{int(sw * 0.1)}+{int(sh * 0.06)}")
        win.transient(app.root)

        side = ttk.Frame(win, style="Card.TFrame", padding=14)
        side.pack(side="right", fill="y")
        ttk.Label(side, text=tr("LEARN A SCALE") if learn else tr("MANUAL SCALE"), style="Section.TLabel").pack(anchor="w")
        ttk.Label(side, style="Muted.TLabel", justify="left", wraplength=250, text=(
            tr("Click the two ends of the scale (its 0 and its last mark, e.g. 0 and 10 cm), along its middle; "
            "give the width of its printed band.") if learn else
            tr("Click the two ends of a known length on the scale (for example its 0 and 5 cm), "
            "along its middle.")) + tr("\n\nDrag a point to adjust it. Mouse wheel: zoom. Right button: move "
            "the view. R: whole photo.")).pack(anchor="w", pady=(4, 12))
        last = seq or {}                        # in a series, the values of the previous photo
        self.cm = tk.StringVar(value=f"{entry['cm']:g}" if entry else last.get("cm") or "5")
        self.width_cm = tk.StringVar(value=f"{entry.get('width_cm', 1.0):g}" if entry
                                     else last.get("width_cm") or "1")
        for text, var in ((tr("Length between the points (cm)"), self.cm), (tr("Width of the scale (cm)"), self.width_cm)):
            ttk.Label(side, text=text).pack(anchor="w")
            e = ttk.Entry(side, textvariable=var, width=10)
            e.pack(anchor="w", pady=(2, 10))
            var.trace_add("write", lambda *_: self.redraw())
        self.readout = tk.StringVar()
        ttk.Label(side, textvariable=self.readout, justify="left").pack(anchor="w", pady=(0, 14))
        if seq:
            ttk.Label(side, text=T(f"PHOTOGRAPHIE {count}", f"PHOTO {count}"), style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        ttk.Button(side, text=tr("Learn this scale") if learn else (tr("Save and next") if seq else tr("Save")),
                   style="Run.TButton", command=self.save).pack(fill="x")
        if seq:
            ttk.Button(side, text=tr("Skip this photo"), command=self.skip).pack(fill="x", pady=(10, 0))
        self.remove_btn = ttk.Button(side, text=tr("Remove the manual scale"), command=self.remove)
        self.remove_btn.pack(fill="x", pady=(10, 0))
        if not entry:
            self.remove_btn.state(["disabled"])
        if learn:
            self.remove_btn.pack_forget()
        ttk.Button(side, text=tr("Stop") if seq else tr("Close"), command=self.close).pack(fill="x", pady=(10, 0))
        win.protocol("WM_DELETE_WINDOW", self.close)

        self.canvas = tk.Canvas(win, bg="#2B2738", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _: self.fit() if not hasattr(self, "zoom") else self.redraw())
        self.canvas.bind("<ButtonPress-1>", self.press)
        self.canvas.bind("<B1-Motion>", self.move)
        self.canvas.bind("<ButtonRelease-1>", lambda _: setattr(self, "drag", None))
        self.canvas.bind("<ButtonPress-3>", lambda e: setattr(self, "pan", (e.x, e.y, self.ox, self.oy)))
        self.canvas.bind("<B3-Motion>", self.pan_move)
        self.canvas.bind("<MouseWheel>", self.wheel)
        win.bind("<Key-r>", lambda _: self.fit())
        if entry:
            self.points = [list(entry["p1"]), list(entry["p2"])]

    # view: screen = (image - offset) * zoom
    def fit(self):
        """Whole photo in the window."""
        cw, ch = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        self.zoom = min(cw / self.W, ch / self.H)
        self.ox = (self.W - cw / self.zoom) / 2
        self.oy = (self.H - ch / self.zoom) / 2
        self.redraw()

    def to_screen(self, x, y):
        """Photo pixel -> window position (zoom and offset of the view)."""
        return (x - self.ox) * self.zoom, (y - self.oy) * self.zoom

    def to_image(self, sx, sy):
        """Window position -> photo pixel."""
        return sx / self.zoom + self.ox, sy / self.zoom + self.oy

    def redraw(self):
        """Draws the visible part of the photo, the two points, the line between them and
        the band of the scale."""
        if not hasattr(self, "zoom"):
            return
        c = self.canvas
        cw, ch = c.winfo_width(), c.winfo_height()
        x0, y0 = max(0.0, self.ox), max(0.0, self.oy)
        x1, y1 = min(self.W, self.ox + cw / self.zoom), min(self.H, self.oy + ch / self.zoom)
        c.delete("all")
        if x1 > x0 and y1 > y0:
            # the reduced copy is enough while it is not enlarged on screen
            src, k = (self.preview, self.k_preview) if self.zoom <= self.k_preview else (self.full, 1.0)
            box = (int(x0 * k), int(y0 * k), max(int(x0 * k) + 1, int(round(x1 * k))),
                   max(int(y0 * k) + 1, int(round(y1 * k))))
            sx0, sy0 = self.to_screen(box[0] / k, box[1] / k)
            sx1, sy1 = self.to_screen(box[2] / k, box[3] / k)
            size = (max(1, round(sx1 - sx0)), max(1, round(sy1 - sy0)))
            part = src.crop(box).resize(size, self.Image.Resampling.NEAREST if self.zoom > 2
                                        else self.Image.Resampling.BILINEAR)
            self.tkimg = self.ImageTk.PhotoImage(part)
            c.create_image(round(sx0), round(sy0), image=self.tkimg, anchor="nw")
        pts = [self.to_screen(*p) for p in self.points]
        if len(pts) == 2:
            px_cm, width = self.values()
            if px_cm:
                # band of the scale layer, as the engine will cut it
                (ax, ay), (bx, by) = self.points
                d = math.hypot(bx - ax, by - ay)
                nx, ny = -(by - ay) / d * width * px_cm / 2, (bx - ax) / d * width * px_cm / 2
                band = [self.to_screen(ax + nx, ay + ny), self.to_screen(bx + nx, by + ny),
                        self.to_screen(bx - nx, by - ny), self.to_screen(ax - nx, ay - ny)]
                c.create_polygon(*[v for p in band for v in p], outline="#FF00FF", fill="", width=2)
            c.create_line(*pts[0], *pts[1], fill="#FFB000", width=2)
        for sx, sy in pts:
            r = self.HANDLE
            c.create_oval(sx - r, sy - r, sx + r, sy + r, outline="#FFB000", width=2)
            c.create_line(sx - 2 * r, sy, sx + 2 * r, sy, fill="#FFB000")
            c.create_line(sx, sy - 2 * r, sx, sy + 2 * r, fill="#FFB000")
        self.update_readout()

    def values(self):
        """(px/cm, width cm) from the two points and the entries; px/cm None when not computable."""
        try:
            cm = float(self.cm.get().replace(",", "."))
            width = float(self.width_cm.get().replace(",", "."))
        except ValueError:
            return None, 1.0
        if len(self.points) < 2 or cm <= 0 or width <= 0:
            return None, width if width > 0 else 1.0
        return math.dist(*self.points) / cm, width

    def update_readout(self):
        """Text under the fields: distance in pixels, px/cm and ppi."""
        px_cm, _ = self.values()
        if len(self.points) < 2:
            self.readout.set(tr("Click the first point.") if not self.points else tr("Click the second point."))
        elif px_cm:
            self.readout.set(f"{math.dist(*self.points):.1f} px\n{px_cm:.2f} px/cm = {px_cm * 2.54:.0f} ppi")
        else:
            self.readout.set(tr("Give the length in cm."))

    def press(self, e):
        """Click: grabs a point near the click, or places a new point."""
        for i, p in enumerate(self.points):
            sx, sy = self.to_screen(*p)
            if math.hypot(e.x - sx, e.y - sy) <= 2 * self.HANDLE:
                self.drag = i
                return
        if len(self.points) < 2:
            x, y = self.to_image(e.x, e.y)
            self.points.append([min(max(x, 0), self.W - 1), min(max(y, 0), self.H - 1)])
            self.drag = len(self.points) - 1
            self.redraw()

    def move(self, e):
        """Drag: moves the grabbed point."""
        if self.drag is not None:
            x, y = self.to_image(e.x, e.y)
            self.points[self.drag] = [min(max(x, 0), self.W - 1), min(max(y, 0), self.H - 1)]
            self.redraw()

    def pan_move(self, e):
        """Right button held: moves the view."""
        if self.pan:
            x0, y0, ox, oy = self.pan
            self.ox, self.oy = ox - (e.x - x0) / self.zoom, oy - (e.y - y0) / self.zoom
            self.redraw()

    def wheel(self, e):
        """Wheel: zoom on the point under the mouse."""
        x, y = self.to_image(e.x, e.y)
        self.zoom = min(8.0, max(0.02, self.zoom * (1.25 if e.delta > 0 else 0.8)))
        self.ox, self.oy = x - e.x / self.zoom, y - e.y / self.zoom
        self.redraw()

    def _load(self):
        """Manual scales of the folder (gerbil_scales.json)."""
        try:
            with open(self.file if os.path.exists(self.file) else self.old_file, encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def _write(self, data):
        """Writes the manual scales (aside, then swapped); the file of the old name goes."""
        tmp = self.file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
        os.replace(tmp, self.file)
        if os.path.exists(self.old_file):                 # its entries are now in the new file
            os.remove(self.old_file)

    def save(self):
        """Saves the scale of the photo (or gives it to the profile when learning), then next
        photo of the series or offer to process it again."""
        px_cm, width = self.values()
        if not px_cm:
            messagebox.showwarning("Gerbil", tr("Click two points and give the length between them (cm)."),
                                   parent=self.win)
            return
        if self.learn:
            entry = {"p1": list(self.points[0]), "p2": list(self.points[1]),
                     "cm": float(self.cm.get().replace(",", ".")), "width_cm": width}
            self.win.destroy()
            self.learn(entry)
            return
        data = self._load()
        data[os.path.basename(self.path)] = {
            "p1": [round(v, 2) for v in self.points[0]], "p2": [round(v, 2) for v in self.points[1]],
            "cm": float(self.cm.get().replace(",", ".")), "width_cm": width}
        try:
            self._write(data)
        except OSError as e:
            messagebox.showerror("Gerbil", T(f"Impossible d'enregistrer l'échelle :\n{e}", f"Could not save the scale:\n{e}"), parent=self.win)
            return
        self.remove_btn.state(["!disabled"])
        if self.on_saved:
            self.on_saved()
            self.win.destroy()
        elif self.seq:
            self.seq["saved"].append(self.path)
            self.seq["cm"], self.seq["width_cm"] = self.cm.get(), self.width_cm.get()
            self.win.destroy()
            self.app.next_scale(self.seq)
        elif messagebox.askyesno("Gerbil", T(f"Échelle enregistrée : {px_cm:.2f} px/cm.\n\nRetraiter cette photographie maintenant ?",
                                   f"Scale saved: {px_cm:.2f} px/cm.\n\nProcess this photo again now?"),
                                 parent=self.win):
            self.win.destroy()
            self.app.run([self.path])

    def skip(self):
        """Series: leaves this photo without a scale and goes to the next one."""
        self.win.destroy()
        self.app.next_scale(self.seq)

    def close(self):
        """Close (single photo) or Stop (series: the photos already set may then be processed)."""
        self.win.destroy()
        if self.seq:
            self.seq["todo"].clear()
            self.app.next_scale(self.seq)

    def remove(self):
        """Removes the manual scale of the photo (the detection is used again)."""
        data = self._load()
        if data.pop(os.path.basename(self.path), None) is not None:
            try:
                if data:
                    self._write(data)
                else:
                    for f in (self.file, self.old_file):
                        if os.path.exists(f):
                            os.remove(f)
            except OSError as e:
                messagebox.showerror("Gerbil", T(f"Impossible de supprimer l'échelle :\n{e}", f"Could not remove the scale:\n{e}"), parent=self.win)
                return
        self.points = []
        self.remove_btn.state(["disabled"])
        self.redraw()


PROJECT_FILE = "gerbil_project.json"        # in the folder of the photos, read by gerbil.py (load_project)
# same defaults and same naming as gerbil.py (DEFAULT_FIELDS, project_name): keep them identical
DEFAULT_FIELDS = [
    {"key": "site", "label": "Site", "required": True},
    {"key": "sector", "label": "Sector"},
    {"key": "us", "label": "US"},
    {"key": "number", "label": "Object number", "required": True},
    {"key": "material", "label": "Material", "choices": ["ceramic", "metal", "bone", "glass", "lithic", "other"]},
    {"key": "view", "label": "View", "choices": ["exterior", "interior", "profile", "top", "bottom"]},
]


def load_project_file(folder):
    """Project of a folder (dict), a new one if there is none; None if the file cannot be read."""
    path = os.path.join(folder, PROJECT_FILE)
    if not os.path.exists(path):
        return {"fields": [dict(f) for f in DEFAULT_FIELDS], "template": "", "rule": "", "common": {}, "photos": {}}
    try:
        with open(path, encoding="utf-8") as fh:
            pr = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(pr, dict):
        return None
    pr.setdefault("fields", [dict(f) for f in DEFAULT_FIELDS])
    for k, v in (("template", ""), ("rule", ""), ("common", {}), ("photos", {})):
        pr.setdefault(k, v)
    return pr


def save_project_file(folder, pr):
    """Writes gerbil_project.json (written aside, then swapped: never half-written)."""
    path = os.path.join(folder, PROJECT_FILE)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(pr, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def project_values(pr, name):
    """Values of a photo: the common ones, replaced by its own."""
    vals = {k: str(v).strip() for k, v in (pr.get("common") or {}).items() if str(v).strip()}
    vals.update({k: str(v).strip() for k, v in ((pr.get("photos") or {}).get(name) or {}).items() if str(v).strip()})
    return vals


def project_output_name(pr, name):
    """Output name of a photo (as gerbil.py: project_name), or its own name without a template."""
    base = os.path.splitext(name)[0]
    template = (pr.get("template") or "").strip()
    if not template:
        return base
    vals = dict(project_values(pr, name), photo=base)
    out = re.sub(r"\{(\w+)\}", lambda m: vals.get(m.group(1), ""), template)
    out = re.sub(r'[<>:"/\\|?*\x00-\x1f\s]+', "_", out)
    out = re.sub(r"([_\-.])[_\-.]+", r"\1", out).strip("_-. ")
    return out or base


def rule_regex(rule):
    """The naming rule as PowerShell's -match reads it: .NET regular expression, case-insensitive, found
    anywhere in the name unless anchored with ^ and $. .NET named groups (?<name>...) are accepted, and
    (?-i) at the start makes the rule case-sensitive (as in PowerShell)."""
    rule = re.sub(r"\(\?<(?![=!])", "(?P<", rule)
    if rule.startswith("(?-i)"):
        return re.compile(rule[5:])
    return re.compile(rule, re.IGNORECASE)

# rule helper of the batch renaming window: (label, piece of PowerShell regular expression, case-sensitive)
RULE_PIECES = [
    ("Capital letters only (no lowercase)", "(?!.*[a-z])", True),
    ("Lowercase only (no capitals)", "(?!.*[A-Z])", True),
    ("Only letters, digits and _ (no space, accent, dash, dot)", "(?=[A-Za-z0-9_]+$)", False),
    ("Only letters, digits, _ and - (no space, accent, dot)", "(?=[A-Za-z0-9_-]+$)", False),
    ("No double separator (__, --, _-)", "(?!.*[_-]{2})", False),
    ("Ends with a number", "(?=.*\\d$)", False),
]


def ps_escape(text):
    """Text taken literally in a .NET / PowerShell regular expression (as [regex]::Escape)."""
    return re.sub(r"([\\.^$|?*+()\[\]{}#\s])", r"\\\1", text)


def build_rule(pieces, starts="", max_len=0):
    """PowerShell rule made of look-aheads (each one tests the whole name), e.g.
    (?-i)^(?!.*[a-z])(?=QSR25)(?=.{1,40}$): case-sensitive when a piece needs it."""
    parts = [p for _, p, _ in pieces]
    if starts:
        parts.append(f"(?={ps_escape(starts)})")
    if max_len:
        parts.append(f"(?=.{{1,{int(max_len)}}}$)")
    if not parts:
        return ""
    return ("(?-i)" if any(cs for _, _, cs in pieces) else "") + "^" + "".join(parts)



def read_table(path):
    """Rows (lists of strings) of a CSV file or of the first sheet of an Excel .xlsx file."""
    if path.lower().endswith((".xlsx", ".xlsm")):
        import zipfile
        import xml.etree.ElementTree as ET
        m = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        with zipfile.ZipFile(path) as z:
            shared = []
            if "xl/sharedStrings.xml" in z.namelist():
                for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(m + "si"):
                    shared.append("".join(t.text or "" for t in si.iter(m + "t")))
            sheets = sorted((n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n)),
                            key=lambda n: int(re.findall(r"\d+", n)[-1]))
            if not sheets:
                return []
            root = ET.fromstring(z.read(sheets[0]))
        rows = []
        for r in root.iter(m + "row"):
            cells = {}
            for c in r.findall(m + "c"):
                letters = re.match(r"[A-Z]+", c.get("r", "A")).group(0)
                col = 0
                for ch in letters:
                    col = col * 26 + ord(ch) - 64
                t, v = c.get("t"), c.find(m + "v")
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(m + "t"))
                else:
                    val = v.text if v is not None and v.text else ""
                    if re.fullmatch(r"-?\d+\.0+", val):
                        val = val.split(".")[0]          # whole numbers stored as 12.0
                cells[col - 1] = val
            if cells:
                rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
        return rows
    import csv
    for enc in ("utf-8-sig", "cp1252"):
        try:
            with open(path, newline="", encoding=enc) as fh:
                text = fh.read()
            break
        except UnicodeDecodeError:
            continue
    class Semicolon(csv.excel):
        delimiter = ";"
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=";,\t")
    except csv.Error:
        dialect = Semicolon
    return [r for r in csv.reader(text.splitlines(), dialect) if any(x.strip() for x in r)]


class FieldDialog:
    """Adds or edits a field of the project: label, key (name used in the template), required, choices."""

    def __init__(self, parent, field=None):
        """Small window to create or edit a field: label, key, required, choices."""
        self.result = None
        f = dict(field or {})
        self.win = win = tk.Toplevel(parent)
        win.title(tr("Field"))
        win.configure(bg=CARD_BG)
        win.transient(parent)
        frm = ttk.Frame(win, style="Card.TFrame", padding=14)
        frm.pack(fill="both", expand=True)
        self.label = tk.StringVar(value=f.get("label", ""))
        self.key = tk.StringVar(value=f.get("key", ""))
        self.required = tk.BooleanVar(value=bool(f.get("required")))
        self.choices = tk.StringVar(value=", ".join(f.get("choices") or []))
        for text, var, tip in ((tr("Label (column of the report)"), self.label, None),
                               (tr("Key (in the name template: {key})"), self.key, None),
                               (tr("Choices (comma-separated; empty: free text)"), self.choices, None)):
            ttk.Label(frm, text=text).pack(anchor="w")
            ttk.Entry(frm, textvariable=var, width=46).pack(anchor="w", pady=(2, 8))
        ttk.Checkbutton(frm, text=tr("Required (a photo without it is flagged)"), variable=self.required).pack(anchor="w")
        row = ttk.Frame(frm, style="Card.TFrame")
        row.pack(fill="x", pady=(12, 0))
        ttk.Button(row, text=tr("OK"), style="Run.TButton", command=self.ok).pack(side="left")
        ttk.Button(row, text=tr("Cancel"), command=win.destroy).pack(side="left", padx=8)
        if not f:
            self.label.trace_add("write", lambda *_: self.key.set(
                re.sub(r"[^a-z0-9]+", "_", self.label.get().lower()).strip("_")))
        win.grab_set()
        parent.wait_window(win)

    def ok(self):
        """Checks and returns the field (key made of letters, digits and _)."""
        label, key = self.label.get().strip(), re.sub(r"\W+", "_", self.key.get().strip().lower()).strip("_")
        if not label or not key:
            messagebox.showwarning("Gerbil", tr("Give a label and a key."), parent=self.win)
            return
        self.result = {"key": key, "label": label}
        if self.required.get():
            self.result["required"] = True
        choices = [c.strip() for c in self.choices.get().split(",") if c.strip()]
        if choices:
            self.result["choices"] = choices
        self.win.destroy()


class ProjectWindow:
    """Project of a folder of photos (gerbil_project.json next to them): fields, name template, naming rule,
    values common to all the photos, and a table with one row per photo (double-click a cell to edit it;
    several rows selected: "Set for selected", "Number the selected"); import of a CSV / Excel inventory.
    The output files of the photos take the names built from the template (the photos keep theirs)."""

    def __init__(self, app, folder):
        """The batch renaming window: fields, template, naming rule with its helper,
        common values, table of the photos with preview, buttons."""
        if os.path.basename(os.path.normpath(folder)).lower() == "outlined_result":
            folder = os.path.dirname(os.path.normpath(folder))      # the photos, not the copies of the results
        self.app, self.folder = app, folder
        pr = load_project_file(folder)
        if pr is None:
            raise ValueError(f"{PROJECT_FILE} cannot be read in {folder}")
        self.pr = pr
        self.photos = sorted(f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in EXTENSIONS)
        self.changed = False
        self.win = win = tk.Toplevel(app.root)
        win.title(T(f"Renommage en lot - {folder}", f"Batch renaming - {folder}"))
        win.configure(bg=WINDOW_BG)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{min(int(sw * 0.9), 1400)}x{int(sh * 0.9)}+{max(0, (sw - min(int(sw * 0.9), 1400)) // 2)}+{int(sh * 0.02)}")
        win.protocol("WM_DELETE_WINDOW", self.close)

        top = ttk.Frame(win, style="Card.TFrame", padding=12)
        top.pack(fill="x")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text=tr("FIELDS"), style="Section.TLabel").grid(row=0, column=0, sticky="w")
        row0 = ttk.Frame(top, style="Card.TFrame")
        row0.grid(row=0, column=1, sticky="w", padx=8)
        self.fields_lbl = ttk.Label(row0, style="Muted.TLabel", wraplength=330, justify="left")
        self.fields_lbl.pack(anchor="w")
        bar = ttk.Frame(row0, style="Card.TFrame")
        bar.pack(anchor="w", pady=(4, 0))
        for text, cmd in ((tr("Add field…"), self.add_field), (tr("Edit field…"), self.edit_field),
                          (tr("Remove field…"), self.remove_field)):
            ttk.Button(bar, text=text, command=cmd, style="Small.TButton").pack(side="left", padx=(0, 4))

        ttk.Label(top, text=tr("NAME TEMPLATE"), style="Section.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.template = tk.StringVar(value=pr.get("template", ""))
        ttk.Entry(top, textvariable=self.template, width=40).grid(row=1, column=1, sticky="ew", padx=8, pady=(10, 0))
        self.tokens = ttk.Frame(top, style="Card.TFrame")
        self.tokens.grid(row=2, column=1, sticky="w", padx=8, pady=(4, 0))
        self.preview = tk.StringVar()
        ttk.Label(top, textvariable=self.preview, style="Muted.TLabel", wraplength=560, justify="left").grid(
            row=3, column=1, sticky="w", padx=8)
        ttk.Label(top, text=tr("NAMING RULE (optional)"), style="Section.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 0))
        self.rule = tk.StringVar(value=pr.get("rule", ""))
        e = ttk.Entry(top, textvariable=self.rule)
        e.grid(row=4, column=1, sticky="ew", padx=8, pady=(8, 0))
        Tooltip(e, tr("Regular expression the output names must match, read as PowerShell's -match: "
                   "case-insensitive, found anywhere unless anchored with ^ and $ "
                   "(e.g. ^QSR25_[A-Z0-9]+_US\\d+_\\d+); a name that does not match is flagged. Empty: no rule."))
        self.template.trace_add("write", lambda *_: self.changes())
        self.rule.trace_add("write", lambda *_: (setattr(self, "changed", True), self.rule_feedback()))

        # rule helper: ready-made pieces, the rule as PowerShell code, and a test of a name
        helper = ttk.Labelframe(top, text=tr("  Rule helper  "), style="Card.TLabelframe", padding=8)
        helper.grid(row=0, column=3, rowspan=7, sticky="new", padx=(14, 0))
        top.rowconfigure(6, weight=1)       # the extra height of the helper goes below the left rows
        ttk.Label(helper, text=tr("Tick what the names must respect: the rule is written for you."),
                  style="Muted.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        self.piece_vars = []
        for i, (label, piece, cs) in enumerate(RULE_PIECES):
            v = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(helper, text=tr(label), variable=v, command=self.helper_changed)
            cb.grid(row=1 + i, column=0, columnspan=2, sticky="w")
            Tooltip(cb, f"PowerShell piece: {piece}" + (tr("   (case-sensitive: the rule starts with (?-i))") if cs else ""))
            self.piece_vars.append(v)
        r = 1 + len(RULE_PIECES)
        ttk.Label(helper, text=tr("Starts with")).grid(row=r, column=0, sticky="w")
        self.starts = tk.StringVar()
        ttk.Entry(helper, textvariable=self.starts, width=14).grid(row=r, column=1, sticky="w")
        ttk.Label(helper, text=tr("At most (characters)")).grid(row=r + 1, column=0, sticky="w")
        self.max_len = tk.StringVar()
        ttk.Entry(helper, textvariable=self.max_len, width=6).grid(row=r + 1, column=1, sticky="w")
        for v in (self.starts, self.max_len):
            v.trace_add("write", lambda *_: self.helper_changed())
        ttk.Label(helper, text=tr("In PowerShell:"), style="Section.TLabel").grid(row=r + 2, column=0, sticky="w", pady=(8, 0))
        self.ps_code = tk.StringVar()
        code = tk.Entry(helper, textvariable=self.ps_code, state="readonly", font=(FONT_MONO, 9), width=46,
                        readonlybackground="#F3F1FA", relief="flat")
        code.grid(row=r + 3, column=0, columnspan=2, sticky="ew")
        ttk.Button(helper, text=tr("Copy the PowerShell line"), style="Small.TButton",
                   command=lambda: (self.win.clipboard_clear(), self.win.clipboard_append(self.ps_code.get()))).grid(
            row=r + 4, column=0, sticky="w", pady=(2, 0))
        ttk.Label(helper, text=tr("Test a name")).grid(row=r + 5, column=0, sticky="w", pady=(6, 0))
        self.test_name = tk.StringVar()
        ttk.Entry(helper, textvariable=self.test_name, width=30).grid(row=r + 5, column=1, sticky="w", pady=(6, 0))
        self.test_result = tk.StringVar()
        ttk.Label(helper, textvariable=self.test_result, wraplength=430).grid(row=r + 6, column=0, columnspan=2,
                                                                              sticky="w")
        self.test_name.trace_add("write", lambda *_: self.rule_feedback())
        ttk.Label(helper, text=tr("Also check the photos:"), style="Section.TLabel").grid(
            row=r + 7, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.ext_lower = tk.BooleanVar(value=bool(self.pr.get("photo_ext_lower")))
        cb = ttk.Checkbutton(helper, text=tr("Extension in lowercase (.jpg, not .JPG)"), variable=self.ext_lower,
                             command=self.ext_changed)
        cb.grid(row=r + 8, column=0, columnspan=2, sticky="w")
        Tooltip(cb, tr("Separate control of the names of the original photos (they are never renamed): a photo "
                    "whose extension has capital letters is flagged. In PowerShell: "
                    "$photo.Extension -cmatch '^\\.[a-z0-9]+$'"))
        self.ext_info = tk.StringVar()
        ttk.Label(helper, textvariable=self.ext_info, style="Muted.TLabel").grid(row=r + 9, column=0, columnspan=2,
                                                                                sticky="w")
        top.columnconfigure(3, weight=0)

        foot = ttk.Frame(win, style="Window.TFrame", padding=12)    # packed first at the bottom: always visible
        foot.pack(side="bottom", fill="x")
        ttk.Button(foot, text=tr("Save"), style="Run.TButton", command=self.save).pack(side="left")
        ttk.Button(foot, text=tr("Save and process the photos"), command=lambda: self.save(run=True)).pack(side="left", padx=8)
        b = ttk.Button(foot, text=tr("IPTC metadata…"), command=lambda: IptcWindow(self))
        b.pack(side="left")
        Tooltip(b, tr("Which field goes into which IPTC field (title, keywords, location, copyright…), written "
                   "into the output files and, if wanted, next to the original photos."))
        ttk.Button(foot, text=tr("Close"), command=self.close).pack(side="right")
        self.common_frame = ttk.Labelframe(win, text=tr("  Values for all the photos  "), style="Card.TLabelframe",
                                           padding=8)
        self.common_frame.pack(fill="x", padx=12, pady=(8, 0))

        mid = ttk.Frame(win, style="Window.TFrame", padding=(12, 8, 12, 0))
        mid.pack(fill="both", expand=True)
        bar = ttk.Frame(mid, style="Window.TFrame")
        bar.pack(fill="x", pady=(0, 6))
        ttk.Button(bar, text=tr("Select all"), command=self.select_all).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text=tr("Set for selected…"), command=self.set_selected).pack(side="left")
        ttk.Button(bar, text=tr("Number the selected…"), command=self.number_selected).pack(side="left", padx=6)
        ttk.Button(bar, text=tr("Import CSV / Excel…"), command=self.import_table).pack(side="left")
        ttk.Label(bar, text=tr("Double-click: edit a cell. Square at the corner of a cell: drag it to copy the value "
                            "(Ctrl: count up). Ctrl+A: all rows; Ctrl+D: copy down the first selected row."),
                  style="Muted.TLabel", wraplength=520, justify="left").pack(side="left", padx=12)
        # table and photo preview side by side; the bar between them can be dragged
        pane = tk.PanedWindow(mid, orient="horizontal", sashwidth=8, bg=LAVENDER_LINE, bd=0, sashrelief="flat")
        pane.pack(fill="both", expand=True)
        tablef = ttk.Frame(pane, style="Window.TFrame")
        side = ttk.Frame(pane, style="Card.TFrame", padding=8)
        pane.add(tablef, stretch="always", minsize=420)
        pane.add(side, stretch="never", minsize=220, width=460)
        self.thumb_lbl = tk.Label(side, bg=CARD_BG)
        self.thumb_lbl.pack(fill="both", expand=True)
        self.thumb_lbl.bind("<Configure>", lambda _: self.after_resize())
        self.thumb_lbl.bind("<Double-1>", lambda _: self.open_photo())
        self.thumb_name = tk.StringVar()
        ttk.Label(side, textvariable=self.thumb_name, style="Muted.TLabel").pack(pady=(4, 6))
        ttk.Button(side, text=tr("Open the photo"), command=self.open_photo).pack(fill="x")
        self.thumbs = {}                            # photo -> reduced copy (decoded once)
        self.tree = ttk.Treeview(tablef, show="headings", selectmode="extended")
        sb = ttk.Scrollbar(tablef, orient="vertical", command=self.tree.yview)
        sbx = ttk.Scrollbar(tablef, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=lambda *a: (sb.set(*a), self.place_handle()),
                            xscrollcommand=lambda *a: (sbx.set(*a), self.place_handle()))
        sbx.pack(side="bottom", fill="x")
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.edit_cell)
        self.tree.bind("<ButtonRelease-1>", self.cell_clicked, add="+")
        self.tree.bind("<<TreeviewSelect>>", lambda _: self.show_thumb())
        self.tree.bind("<Configure>", lambda _: self.place_handle())
        self.tree.bind("<Control-a>", lambda _: (self.select_all(), "break")[1])
        self.tree.bind("<Control-d>", lambda _: (self.fill_down(), "break")[1])
        self.active = None                          # (row, key) of the cell with the fill handle
        self.handle = tk.Frame(self.tree, bg=LAVENDER_DARK, cursor="crosshair", width=8, height=8)
        self.handle.bind("<ButtonPress-1>", self.fill_start)
        self.handle.bind("<B1-Motion>", self.fill_move)
        self.handle.bind("<ButtonRelease-1>", self.fill_end)
        self.rebuild()
        self.rule_feedback()
        self.ext_feedback()

    # ------------------------------------------------------------ display
    def fields(self):
        """Fields of the project."""
        return self.pr["fields"]

    def rebuild(self):
        """Fields changed: tokens, common values and columns of the table drawn again."""
        self.fields_lbl.configure(text=", ".join(f["label"] + (" *" if f.get("required") else "")
                                                 for f in self.fields()) + tr("     (* required)"))
        for w in self.tokens.winfo_children():
            w.destroy()
        ttk.Label(self.tokens, text=tr("Insert:"), style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        for i, key in enumerate([f["key"] for f in self.fields()] + ["photo"]):
            ttk.Button(self.tokens, text="{" + key + "}", style="Small.TButton",
                       command=lambda k=key: self.template.set(self.template.get() + ("_" if self.template.get() else "")
                                                                + "{" + k + "}")).grid(
                row=i // 4, column=1 + i % 4, sticky="ew", padx=2, pady=1)
        for w in self.common_frame.winfo_children():
            w.destroy()
        self.common_vars = {}
        for i, f in enumerate(self.fields()):
            ttk.Label(self.common_frame, text=f["label"]).grid(row=0, column=i, sticky="w", padx=4)
            var = tk.StringVar(value=(self.pr.get("common") or {}).get(f["key"], ""))
            w = (ttk.Combobox(self.common_frame, textvariable=var, values=[""] + f["choices"], width=14)
                 if f.get("choices") else ttk.Entry(self.common_frame, textvariable=var, width=16))
            w.grid(row=1, column=i, sticky="w", padx=4)
            var.trace_add("write", lambda *_, k=f["key"], v=var: self.set_common(k, v.get()))
            self.common_vars[f["key"]] = var
        cols = ["photo"] + [f["key"] for f in self.fields()] + ["output"]
        self.tree.configure(columns=cols)
        import tkinter.font as tkfont
        fnt = tkfont.Font(font=(FONT_SERIF, 10))           # the font of the table (Treeview style)
        wid = lambda text: fnt.measure(text) + 26
        self._wid = wid
        self.tree.heading("photo", text=tr("Photo"), anchor="w")
        self.tree.column("photo", width=max([wid(tr("Photo"))] + [wid(n) for n in self.photos[:200]]), minwidth=60,
                         stretch=False)
        for f in self.fields():
            self.tree.heading(f["key"], text=f["label"], anchor="w")
            self.tree.column(f["key"], width=max(wid(f["label"] + " *"), wid("0000000")), minwidth=40, stretch=False)
        self.tree.heading("output", text=tr("Output name"), anchor="w")
        self.tree.column("output", width=wid("QSR25_A5_US7549_187_ceramic_exterior"), minwidth=120, stretch=True)
        self.headings()
        self.fill()

    def fill(self):
        """Fills the table: one row per photo, its values and its output name."""
        sel = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for name in self.photos:
            own = (self.pr["photos"].get(name) or {})
            vals = [own.get(f["key"], "") for f in self.fields()]
            self.tree.insert("", "end", iid=name, values=[name] + vals + [project_output_name(self.pr, name)])
        self.tree.selection_set([i for i in sel if self.tree.exists(i)])
        self.update_preview()
        self.place_handle()

    def update_preview(self):
        """Example of output name, and warning when names are used twice."""
        if not self.photos:
            self.preview.set(tr("No photo in this folder."))
            return
        names = [project_output_name(self.pr, n) for n in self.photos]
        dup = len(names) - len(set(n.lower() for n in names))
        self.preview.set(T("Exemple : ", "Example: ") + f"{self.photos[0]}  ->  {names[0]}_outlined.tif"
                         + (T(f"     ({dup} nom(s) utilisé(s) deux fois : un suffixe _2… sera ajouté)",
                              f"     ({dup} name(s) used twice: a suffix _2… will be added)") if dup else ""))

    def changes(self):
        """The template changed: output names computed again."""
        self.pr["template"] = self.template.get()
        self.changed = True
        for name in self.photos:
            if self.tree.exists(name):
                self.tree.set(name, "output", project_output_name(self.pr, name))
        self.update_preview()

    def set_common(self, key, value):
        """Sets a value common to all the photos."""
        self.pr.setdefault("common", {})
        if value.strip():
            self.pr["common"][key] = value.strip()
        else:
            self.pr["common"].pop(key, None)
        self.headings()
        self.changes()

    def headings(self):
        """Column titles; a value common to all the photos is given in the title (the cells hold the values
        of each photo, which replace it)."""
        common = self.pr.get("common") or {}
        for f in self.fields():
            if f["key"] in self.tree["columns"]:
                text = (f["label"] + (" *" if f.get("required") else "")
                        + (T(" (toutes : ", " (all: ") + f"{common[f['key']]})" if common.get(f["key"]) else ""))
                self.tree.heading(f["key"], text=text)
                if hasattr(self, "_wid"):
                    self.tree.column(f["key"], width=max(self._wid(text), self._wid("0000000")))

    def set_value(self, name, key, value):
        """Sets the value of a field for one photo (table and project)."""
        own = self.pr["photos"].setdefault(name, {})
        if value.strip():
            own[key] = value.strip()
        else:
            own.pop(key, None)
        if not own:
            self.pr["photos"].pop(name, None)
        self.changed = True
        if self.tree.exists(name):
            self.tree.set(name, key, value.strip())
            self.tree.set(name, "output", project_output_name(self.pr, name))
        self.update_preview()

    def ext_changed(self):
        """"Extension in lowercase" ticked or not."""
        self.pr["photo_ext_lower"] = bool(self.ext_lower.get())
        self.changed = True
        self.ext_feedback()

    def ext_feedback(self):
        """Number of photos whose extension has capitals."""
        bad = [n for n in self.photos if os.path.splitext(n)[1] != os.path.splitext(n)[1].lower()]
        if not self.ext_lower.get():
            self.ext_info.set("")
        else:
            self.ext_info.set(T(f"{len(bad)} photographie(s) sur {len(self.photos)} avec des majuscules dans l'extension",
                                f"{len(bad)} photo(s) of {len(self.photos)} with capital letters in the extension")
                              + (T(" (par ex. ", " (e.g. ") + f"{bad[0]})" if bad else ""))

    # ------------------------------------------------------------ rule helper
    def helper_changed(self):
        """Ticked pieces -> rule written in the rule field (it can still be edited by hand)."""
        pieces = [RULE_PIECES[i] for i, v in enumerate(self.piece_vars) if v.get()]
        try:
            n = int(self.max_len.get()) if self.max_len.get().strip() else 0
        except ValueError:
            n = 0
        self.rule.set(build_rule(pieces, self.starts.get().strip(), n))

    def rule_feedback(self):
        """The rule as a PowerShell line, and the result for the name to test (or the first output name)."""
        rule = self.rule.get().strip()
        name = self.test_name.get().strip() or (project_output_name(self.pr, self.photos[0]) if self.photos else "NAME")
        if not rule:
            self.ps_code.set(tr("(no rule)"))
            self.test_result.set("")
            return
        self.ps_code.set("'" + name.replace("'", "''") + "' -match '" + rule.replace("'", "''") + "'")
        try:
            ok = bool(rule_regex(rule).search(name))
            self.test_result.set(f"{name}: " + (tr("✓ matches the rule (True)") if ok else tr("✗ does not match (False)")))
        except re.error as e:
            self.test_result.set(T("✗ règle invalide : ", "✗ invalid rule: ") + str(e))

    # ------------------------------------------------------------ photo, selection, fill handle
    def show_thumb(self):
        """Small view of the photo of the selected row (the first one)."""
        sel = self.tree.selection()
        if not sel:
            return
        name = sel[0]
        self.thumb_name.set(name + (T(f"  (+{len(sel) - 1} sélectionnée(s))", f"  (+{len(sel) - 1} selected)") if len(sel) > 1 else "")
                            + "   - double-click: whole photo")
        if name not in self.thumbs:
            try:
                im = open_photo_image(os.path.join(self.folder, name), small=True)
                im.thumbnail((1400, 1400))
                self.thumbs[name] = im
                while len(self.thumbs) > 12:               # memory: only the last photos seen are kept
                    self.thumbs.pop(next(iter(self.thumbs)))
            except Exception:
                self.thumbs[name] = None
        self.thumb_shown = name
        self.render_thumb()

    def render_thumb(self):
        """The preview fitted to the space it has (it follows the bar between table and preview)."""
        name = getattr(self, "thumb_shown", None)
        im = self.thumbs.get(name) if name else None
        if im is None:
            self.thumb_lbl.configure(image="")
            return
        from PIL import ImageTk
        w, h = max(50, self.thumb_lbl.winfo_width() - 4), max(50, self.thumb_lbl.winfo_height() - 4)
        small = im.copy()
        small.thumbnail((w, h))
        self.thumb_img = ImageTk.PhotoImage(small)
        self.thumb_lbl.configure(image=self.thumb_img)

    def after_resize(self):
        """Preview redrawn a moment after the window is resized."""
        if getattr(self, "_resize_job", None):
            self.win.after_cancel(self._resize_job)
        self._resize_job = self.win.after(80, self.render_thumb)

    def open_photo(self):
        """Opens the selected photo in the Windows viewer."""
        sel = self.tree.selection()
        if sel:
            os.startfile(os.path.join(self.folder, sel[0]))

    def select_all(self):
        """Selects all the rows (Ctrl+A)."""
        self.tree.selection_set(self.tree.get_children())

    def cell_clicked(self, e):
        """Click in the table: the cell becomes the active one (fill handle)."""
        row, col = self.tree.identify_row(e.y), self.tree.identify_column(e.x)
        if row and col and getattr(self, "fill", None) is None:
            key = self.tree["columns"][int(col[1:]) - 1]
            self.active = (row, key) if any(f["key"] == key for f in self.fields()) else None
            self.place_handle()

    def place_handle(self):
        """The small square at the bottom right corner of the active cell (fill handle, as in Excel)."""
        if not self.active or not self.tree.exists(self.active[0]):
            self.handle.place_forget()
            return
        row, key = self.active
        col = "#" + str(list(self.tree["columns"]).index(key) + 1) if key in self.tree["columns"] else None
        box = self.tree.bbox(row, col) if col else ""
        if not box:
            self.handle.place_forget()
            return
        x, y, w, h = box
        self.handle.place(x=x + w - 5, y=y + h - 5, width=8, height=8)
        self.handle.lift()

    def fill_start(self, e):
        """The fill handle is grabbed (Ctrl: numbering)."""
        self.fill = {"rows": [self.active[0]], "ctrl": bool(e.state & 0x4)}

    def fill_move(self, e):
        """Dragging the fill handle: rows covered, table scrolled at its edges."""
        if not getattr(self, "fill", None):
            return
        y = e.y_root - self.tree.winfo_rooty()
        if y > self.tree.winfo_height() - 5:                 # beyond the bottom: scroll
            self.tree.yview_scroll(1, "units")
        elif y < 25:
            self.tree.yview_scroll(-1, "units")
        target = self.tree.identify_row(max(25, min(y, self.tree.winfo_height() - 5)))
        if not target:
            return
        rows = list(self.tree.get_children())
        a, b = rows.index(self.active[0]), rows.index(target)
        self.fill["rows"] = rows[min(a, b):max(a, b) + 1]
        self.tree.selection_set(self.fill["rows"])

    def fill_end(self, e):
        """Handle released: the value copied (or numbered) into the rows covered."""
        f, self.fill = getattr(self, "fill", None), None
        if not f or len(f["rows"]) < 2:
            return
        src, key = self.active
        rows = f["rows"] if f["rows"][0] == src else list(reversed(f["rows"]))
        value = self.tree.set(src, key)
        m = re.fullmatch(r"(.*?)(\d+)", value) if f["ctrl"] else None
        for i, r in enumerate(rows[1:], 1):
            if m:                                             # Ctrl: series 187, 188, 189…
                step = 1 if rows is f["rows"] else -1
                self.set_value(r, key, f"{m.group(1)}{int(m.group(2)) + i * step:0{len(m.group(2))}d}")
            else:
                self.set_value(r, key, value)
        self.update_preview()
        self.place_handle()

    def fill_down(self):
        """Ctrl+D: the values of the first selected row copied to the other selected rows (the active
        column only when a cell is active, else all the fields)."""
        rows = list(self.tree.selection())
        if len(rows) < 2:
            return
        order = list(self.tree.get_children())
        rows.sort(key=order.index)
        keys = [self.active[1]] if self.active else [f["key"] for f in self.fields()]
        for key in keys:
            value = self.tree.set(rows[0], key)
            for r in rows[1:]:
                self.set_value(r, key, value)
        self.update_preview()

    # ------------------------------------------------------------ editing
    def edit_cell(self, e):
        """Double-click: edits the cell in place (entry or list of choices)."""
        row, col = self.tree.identify_row(e.y), self.tree.identify_column(e.x)
        if not row or not col:
            return
        key = self.tree["columns"][int(col[1:]) - 1]
        field = next((f for f in self.fields() if f["key"] == key), None)
        if field is None:
            return
        x, y, w, h = self.tree.bbox(row, col)
        var = tk.StringVar(value=self.tree.set(row, key))
        ed = (ttk.Combobox(self.tree, textvariable=var, values=[""] + field["choices"])
              if field.get("choices") else ttk.Entry(self.tree, textvariable=var))
        ed.place(x=x, y=y, width=max(w, 120), height=h)
        ed.focus_set()

        def commit(_=None):
            if ed.winfo_exists():
                self.set_value(row, key, var.get())
                ed.destroy()
                self.active = (row, key)
                self.place_handle()
        ed.bind("<Return>", commit)
        ed.bind("<FocusOut>", commit)
        ed.bind("<Escape>", lambda _: ed.destroy())

    def _ask_field(self, title, with_value=True, with_start=False):
        """Small dialog: a field, and a value (or a start number and a step)."""
        dlg = tk.Toplevel(self.win)
        dlg.title(title)
        dlg.configure(bg=CARD_BG)
        dlg.transient(self.win)
        frm = ttk.Frame(dlg, style="Card.TFrame", padding=14)
        frm.pack()
        labels = [f["label"] for f in self.fields()]
        fvar = tk.StringVar(value=labels[0] if labels else "")
        ttk.Label(frm, text=tr("Field")).grid(row=0, column=0, sticky="w")
        cb = ttk.Combobox(frm, textvariable=fvar, values=labels, state="readonly", width=24)
        cb.grid(row=0, column=1, pady=2)
        v1, v2 = tk.StringVar(value="1" if with_start else ""), tk.StringVar(value="1")
        val_w = ttk.Combobox(frm, textvariable=v1, width=24)
        if with_value or with_start:
            ttk.Label(frm, text=tr("Start") if with_start else tr("Value")).grid(row=1, column=0, sticky="w")
            val_w.grid(row=1, column=1, pady=2)
        cb.bind("<<ComboboxSelected>>", lambda _: val_w.configure(values=[""] + next(
            (f.get("choices") or [] for f in self.fields() if f["label"] == fvar.get()), [])))
        if with_start:
            ttk.Label(frm, text=tr("Step")).grid(row=2, column=0, sticky="w")
            ttk.Entry(frm, textvariable=v2, width=8).grid(row=2, column=1, sticky="w", pady=2)
        out = {}

        def ok():
            out.update(field=next((f["key"] for f in self.fields() if f["label"] == fvar.get()), None),
                       value=v1.get(), step=v2.get())
            dlg.destroy()
        row = ttk.Frame(frm, style="Card.TFrame")
        row.grid(row=3, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(row, text=tr("OK"), style="Run.TButton", command=ok).pack(side="left")
        ttk.Button(row, text=tr("Cancel"), command=dlg.destroy).pack(side="left", padx=8)
        dlg.grab_set()
        self.win.wait_window(dlg)
        return out if out.get("field") else None

    def set_selected(self):
        """Same value for the selected photos."""
        rows = self.tree.selection()
        if not rows:
            messagebox.showinfo("Gerbil", tr("Select the rows first (Ctrl / Shift + click)."), parent=self.win)
            return
        a = self._ask_field(T(f"Appliquer à {len(rows)} photographie(s)", f"Set for {len(rows)} photo(s)"))
        if a:
            for r in rows:
                self.set_value(r, a["field"], a["value"])
            self.update_preview()

    def number_selected(self):
        """Numbers the selected photos (start, step, zeros)."""
        rows = self.tree.selection()
        if not rows:
            messagebox.showinfo("Gerbil", tr("Select the rows first (Ctrl / Shift + click)."), parent=self.win)
            return
        a = self._ask_field(T(f"Numéroter {len(rows)} photographie(s)", f"Number {len(rows)} photo(s)"), with_start=True)
        if not a:
            return
        m = re.fullmatch(r"(.*?)(\d+)", a["value"].strip())
        try:
            step = int(a["step"])
        except ValueError:
            step = 1
        prefix, start, width = (m.group(1), int(m.group(2)), len(m.group(2))) if m else (a["value"], 1, 1)
        for i, r in enumerate(rows):
            self.set_value(r, a["field"], f"{prefix}{start + i * step:0{width}d}")
        self.update_preview()

    def add_field(self):
        """Adds a field."""
        d = FieldDialog(self.win)
        if d.result:
            if any(f["key"] == d.result["key"] for f in self.fields()):
                messagebox.showwarning("Gerbil", tr("This key is already used."), parent=self.win)
                return
            self.fields().append(d.result)
            self.changed = True
            self.rebuild()

    def _pick_field(self, title):
        """Asks which field to act on."""
        a = self._ask_field(title, with_value=False)
        return next((f for f in self.fields() if a and f["key"] == a["field"]), None)

    def edit_field(self):
        """Edits a field (its values follow a key change)."""
        f = self._pick_field(tr("Field to edit"))
        if f:
            d = FieldDialog(self.win, f)
            if d.result:
                old = f["key"]
                f.clear()
                f.update(d.result)
                if d.result["key"] != old:            # values follow the renamed key
                    for vals in [self.pr.get("common", {})] + list(self.pr["photos"].values()):
                        if old in vals:
                            vals[d.result["key"]] = vals.pop(old)
                self.changed = True
                self.rebuild()

    def remove_field(self):
        """Removes a field and its values."""
        f = self._pick_field(tr("Field to remove"))
        if f and messagebox.askyesno("Gerbil", T(f"Supprimer le champ « {f['label']} » et ses valeurs ?",
                                                f"Remove the field '{f['label']}' and its values?"), parent=self.win):
            self.fields().remove(f)
            for vals in [self.pr.get("common", {})] + list(self.pr["photos"].values()):
                vals.pop(f["key"], None)
            self.changed = True
            self.rebuild()

    def import_table(self):
        """Imports values from a CSV or Excel inventory: matched with the photos
        by name, columns matched with the fields."""
        path = filedialog.askopenfilename(title=tr("Inventory (CSV or Excel)"), parent=self.win,
                                          filetypes=[(tr("CSV or Excel"), "*.csv *.txt *.xlsx *.xlsm"), (tr("All files"), "*.*")])
        if not path:
            return
        try:
            rows = read_table(path)
        except Exception as e:
            messagebox.showerror("Gerbil", T(f"Impossible de lire le fichier :\n{e}", f"Could not read the file:\n{e}"), parent=self.win)
            return
        if len(rows) < 2:
            messagebox.showwarning("Gerbil", tr("The file holds no rows."), parent=self.win)
            return
        header, data = [h.strip() for h in rows[0]], rows[1:]
        names = {os.path.splitext(n)[0].lower(): n for n in self.photos}
        names.update({n.lower(): n for n in self.photos})
        # column of the photo names: the one whose values match most photos
        scores = [sum(1 for r in data if i < len(r) and r[i].strip().lower() in names) for i in range(len(header))]
        if not scores or max(scores) == 0:
            messagebox.showwarning("Gerbil", tr("No column of this file holds the names of the photos of the folder."),
                                   parent=self.win)
            return
        pcol = scores.index(max(scores))
        mapping, ignored = {}, []
        for i, h in enumerate(header):
            if i == pcol:
                continue
            f = next((f for f in self.fields() if h.lower() in (f["key"].lower(), f["label"].lower())), None)
            if f:
                mapping[i] = f["key"]
            elif h:
                ignored.append(h)
        n = 0
        for r in data:
            name = names.get(r[pcol].strip().lower()) if pcol < len(r) else None
            if not name:
                continue
            for i, key in mapping.items():
                if i < len(r) and r[i].strip():
                    self.set_value(name, key, r[i])
            n += 1
        self.fill()
        used = ", ".join(header[i] for i in mapping) or T("aucune", "none")
        messagebox.showinfo("Gerbil", T(f"{n} photographie(s) remplie(s) d'après « {header[pcol]} ».\n"
                                        f"Colonnes utilisées : {used}.",
                                        f"{n} photo(s) filled from '{header[pcol]}'.\nColumns used: {used}.")
                            + (T("\nColonnes ignorées (aucun champ de ce nom) : ",
                                 "\nColumns ignored (no field of that name): ") + ", ".join(ignored) + "."
                               if ignored else ""),
                            parent=self.win)

    # ------------------------------------------------------------ saving
    def save(self, run=False):
        """Checks the rule and saves gerbil_project.json (then processes, if asked)."""
        self.pr["template"], self.pr["rule"] = self.template.get().strip(), self.rule.get().strip()
        if self.pr["rule"]:
            try:
                rule_regex(self.pr["rule"])
            except re.error as e:
                messagebox.showwarning("Gerbil", T(f"La règle n'est pas une expression régulière valide :\n{e}",
                                                   f"The rule is not a valid regular expression:\n{e}"), parent=self.win)
                return False
        try:
            save_project_file(self.folder, self.pr)
        except OSError as e:
            messagebox.showerror("Gerbil", T(f"Impossible d'enregistrer le renommage en lot :\n{e}", f"Could not save the batch renaming:\n{e}"), parent=self.win)
            return False
        self.changed = False
        if run:
            self.win.destroy()
            self.app.run([self.folder])
        return True

    def close(self):
        """Closes, offering to save the changes."""
        if self.changed:
            ans = messagebox.askyesnocancel("Gerbil", tr("Save the changes of the batch renaming?"), parent=self.win)
            if ans is None or (ans and not self.save()):
                return
        self.win.destroy()


REVIEW_DIR = "gerbil_review"                # in the result folder, written by gerbil.py (write_review)
EDITS_DIR = "gerbil_edits"                  # next to the photos, read by gerbil.py (edits_entry)
EDITS_FILE = "gerbil_edits.json"


class ReviewWindow:
    """Review and correction of the cut-outs, photo by photo (doubtful ones first): the photo with the
    outline of the cut-out (green) and of the scale (magenta); erase / add brushes, removal of a whole
    piece by a click, undo; orientation of the object (a line along its rim, or quarter turns); access to
    the manual scale. The corrections are saved next to the photos (EDITS_DIR), so that a later run keeps
    them; the corrected photos are then processed again."""

    TOOLS = (("click", "One click on the object (more precise)"),
             ("erase", "Erase (brush)"), ("add", "Add (brush)"), ("lasso_erase", "Erase (lasso)"),
             ("lasso_add", "Add (lasso)"), ("piece", "Remove a piece (click)"), ("orient", "Orient (line along the rim)"))

    def __init__(self, app, items):
        """The review window: list of photos, view, tools, orientation, information,
        buttons; keyboard and mouse bindings."""
        import numpy as np
        import cv2
        from PIL import Image, ImageOps, ImageTk
        self.np, self.cv2, self.Image, self.ImageOps, self.ImageTk = np, cv2, Image, ImageOps, ImageTk
        self.app, self.items = app, items          # items: review data (dicts, with "json" = their file)
        self.index = 0
        self.queue, self.running = [], []          # photos to export again / being exported
        self.win = win = tk.Toplevel(app.root)
        win.configure(bg=WINDOW_BG)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"{int(sw * 0.9)}x{int(sh * 0.85)}+{int(sw * 0.05)}+{int(sh * 0.04)}")
        win.protocol("WM_DELETE_WINDOW", self.close)

        left = ttk.Frame(win, style="Card.TFrame", padding=8)
        left.pack(side="left", fill="y")
        ttk.Label(left, text=tr("PHOTOS"), style="Section.TLabel").pack(anchor="w")
        self.listbox = tk.Listbox(left, width=34, activestyle="none", font=(FONT_SERIF, 9),
                                  selectbackground=LAVENDER, highlightthickness=0, relief="flat")
        self.listbox.pack(fill="y", expand=True, pady=(4, 0))
        for it in items:
            self.listbox.insert("end", self.list_text(it))
        self.listbox.bind("<<ListboxSelect>>", lambda _: self.goto(self.listbox.curselection()[0])
                          if self.listbox.curselection() else None)

        side = ttk.Frame(win, style="Card.TFrame", padding=12)
        side.pack(side="right", fill="y")
        # actions packed first at the bottom of the panel: always visible, whatever the screen height
        ttk.Label(side, style="Muted.TLabel", wraplength=260, justify="left", text=(
            tr("Left button: tool. Mouse wheel: zoom. Move the view: scroll bars, right or middle button, Space + drag, "
            "arrow keys. R: whole photo. "
            "Ctrl+Z: undo."))).pack(side="bottom", anchor="w", pady=(8, 0))
        ttk.Button(side, text=tr("Close"), command=self.close).pack(side="bottom", fill="x", pady=(6, 0))
        ttk.Button(side, text=tr("Next without change"), command=lambda: self.goto(self.index + 1)).pack(
            side="bottom", fill="x", pady=(6, 0))
        ttk.Button(side, text=tr("Accept and next"), style="Run.TButton", command=self.accept).pack(
            side="bottom", fill="x", pady=(10, 0))
        self.title = tk.StringVar()
        ttk.Label(side, textvariable=self.title, style="Section.TLabel", wraplength=260).pack(anchor="w")
        self.doubts = tk.StringVar()
        ttk.Label(side, textvariable=self.doubts, style="Muted.TLabel", wraplength=260, justify="left").pack(
            anchor="w", pady=(2, 10))
        ttk.Label(side, text=tr("TOOL"), style="Section.TLabel").pack(anchor="w")
        self.tool = tk.StringVar(value="erase")
        for key, text in self.TOOLS:
            text = tr(text)
            ttk.Radiobutton(side, text=text, value=key, variable=self.tool, command=self.tool_changed).pack(anchor="w")
        self.click_hint = tk.StringVar()
        ttk.Label(side, textvariable=self.click_hint, style="Muted.TLabel", wraplength=260, justify="left").pack(
            anchor="w")
        self.click_state = {"index": None, "ready": False, "used": False, "busy": False}
        ttk.Label(side, text=tr("Brush size")).pack(anchor="w", pady=(8, 0))
        self.brush = tk.IntVar(value=20)
        ttk.Scale(side, from_=3, to=120, variable=self.brush, orient="horizontal").pack(fill="x")
        row = ttk.Frame(side, style="Card.TFrame")
        row.pack(fill="x", pady=(8, 0))
        ttk.Button(row, text=tr("Undo"), command=self.undo).pack(side="left")
        ttk.Button(row, text=tr("Reset photo"), command=self.reset).pack(side="left", padx=6)
        ttk.Label(side, text=tr("ORIENTATION"), style="Section.TLabel").pack(anchor="w", pady=(14, 0))
        row = ttk.Frame(side, style="Card.TFrame")
        row.pack(fill="x", pady=(4, 0))
        ttk.Button(row, text=T("Gauche 90°", "Left 90°"), command=lambda: self.turn(90)).pack(side="left")
        ttk.Button(row, text=T("Droite 90°", "Right 90°"), command=lambda: self.turn(-90)).pack(side="left", padx=6)
        ttk.Button(row, text="0°", command=lambda: self.turn(None)).pack(side="left")
        self.angle_txt = tk.StringVar()
        ttk.Label(side, textvariable=self.angle_txt, style="Muted.TLabel").pack(anchor="w", pady=(4, 0))
        self.thumb_lbl = tk.Label(side, bg=CARD_BG)
        self.thumb_lbl.pack(pady=6)
        ttk.Button(side, text=tr("Fix the scale…"), command=self.fix_scale).pack(fill="x", pady=(6, 0))
        self.info = ttk.Labelframe(side, text=tr("  Information  "), style="Card.TLabelframe", padding=6)
        self.info.pack(fill="x", pady=(10, 0))
        self.info_vars = {}

        view = ttk.Frame(win, style="Window.TFrame")
        view.pack(side="left", fill="both", expand=True)
        view.rowconfigure(0, weight=1)
        view.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(view, bg="#2B2738", highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="nsew")
        # scroll bars: move the zoomed view (also middle button, Space + drag, arrow keys)
        self.hbar = ttk.Scrollbar(view, orient="horizontal", command=lambda *a: self.scroll_view(0, *a))
        self.vbar = ttk.Scrollbar(view, orient="vertical", command=lambda *a: self.scroll_view(1, *a))
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        c = self.canvas
        c.bind("<Configure>", lambda _: self.fit() if self.need_fit else self.redraw())
        c.bind("<ButtonPress-1>", self.press)
        c.bind("<B1-Motion>", self.drag)
        c.bind("<ButtonRelease-1>", self.release)
        c.bind("<ButtonPress-3>", lambda e: setattr(self, "pan", (e.x, e.y, self.ox, self.oy)))
        c.bind("<B3-Motion>", self.pan_move)
        c.bind("<ButtonPress-2>", lambda e: setattr(self, "pan", (e.x, e.y, self.ox, self.oy)))
        c.bind("<B2-Motion>", self.pan_move)
        self.space = False
        win.bind("<KeyPress-space>", lambda _: setattr(self, "space", not self.typing()))
        win.bind("<KeyRelease-space>", lambda _: setattr(self, "space", False))
        for key, dx, dy in (("Left", -1, 0), ("Right", 1, 0), ("Up", 0, -1), ("Down", 0, 1)):
            win.bind(f"<KeyPress-{key}>", lambda _, dx=dx, dy=dy: None if self.typing() else self.nudge(dx, dy))
        c.bind("<MouseWheel>", self.wheel)
        c.bind("<Motion>", self.hover)
        win.bind("<Key-r>", lambda _: self.fit())
        win.bind("<Control-z>", lambda _: self.undo())
        self.goto(0)

    # ------------------------------------------------------------ photo
    def goto(self, i):
        """Shows photo i: its cut-out (or the corrections saved before), its angle, its
        information; resets the undo history."""
        if i >= len(self.items):
            self.close()
            return
        self.index = i
        it = self.items[i]
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(i)
        self.listbox.see(i)
        np, Image = self.np, self.Image
        self.photo = open_photo_image(it["photo"])
        self.W, self.H = self.photo.size
        k = min(1.0, 2000 / max(self.W, self.H))
        self.preview = self.photo.resize((round(self.W * k), round(self.H * k)), Image.Resampling.BILINEAR)
        self.k_preview = k
        mask_file = os.path.join(os.path.dirname(it["json"]), os.path.splitext(os.path.basename(it["photo"]))[0] + "_mask.png")
        try:
            with Image.open(mask_file) as im:
                self.mask = (np.asarray(im.convert("L")) > 127).astype(np.uint8) * 255
        except OSError:
            self.mask = np.zeros((self.H, self.W), np.uint8)
        if self.mask.shape != (self.H, self.W):
            self.mask = np.zeros((self.H, self.W), np.uint8)
        saved = self.saved_entry(it["photo"])             # corrections saved before: shown, not the computed cut-out
        if saved.get("mask"):
            try:
                with Image.open(self.saved_mask_file(it["photo"])) as im:
                    m = (np.asarray(im.convert("L")) > 127).astype(np.uint8) * 255
                if m.shape == (self.H, self.W):
                    self.mask = m
                    it["edited"] = True
            except OSError:
                pass
        if "angle" in saved:
            it["angle"] = saved["angle"]
        self.mask0 = self.mask.copy()
        self.history = []
        if hasattr(self, "click_state"):
            self.click_state.update(used=False, ready=False)
            if self.tool.get() == "click":
                self.win.after(10, self.prepare_click)
        self._base = None                          # cached photo of the view
        self.lasso = None
        self.angle = float(it.get("angle") or 0.0)
        self.angle0 = self.angle
        self.line = None
        self.stroke = None
        self.pan = None
        name = os.path.basename(it["photo"])
        self.win.title(T("Vérification - ", "Review - ") + f"{name}  ({i + 1} / {len(self.items)})")
        self.title.set(f"{name}  ({i + 1} / {len(self.items)})")
        doubts = it.get("to_verify") or []
        self.doubts.set((tr("To verify: ") + "; ".join(doubt_text(x) for x in doubts)) if doubts else (tr("Status: ") + it.get("status", "")))
        self.fit()
        self.update_thumb()
        self.show_info()

    def show_info(self):
        """Fields of the project of the photo, with its own values (the values common to all photos are
        given as a hint)."""
        for w in self.info.winfo_children():
            w.destroy()
        self.info_vars = {}
        photo = self.items[self.index]["photo"]
        pr = load_project_file(os.path.dirname(photo))
        self.info_pr = pr
        if pr is None:
            ttk.Label(self.info, text=tr("gerbil_project.json cannot be read."), style="Muted.TLabel").pack(anchor="w")
            return
        own = (pr.get("photos") or {}).get(os.path.basename(photo)) or {}
        common = pr.get("common") or {}
        for i, f in enumerate(pr["fields"]):
            hint = T("  (toutes : ", "  (all: ") + f"{common[f['key']]})" if common.get(f["key"]) else ""
            ttk.Label(self.info, text=f["label"] + (" *" if f.get("required") else "") + hint,
                      style="Muted.TLabel").grid(row=i, column=0, sticky="w", padx=(0, 6))
            var = tk.StringVar(value=own.get(f["key"], ""))
            w = (ttk.Combobox(self.info, textvariable=var, values=[""] + f["choices"], width=14)
                 if f.get("choices") else ttk.Entry(self.info, textvariable=var, width=16))
            w.grid(row=i, column=1, sticky="w", pady=1)
            self.info_vars[f["key"]] = var
        self.info_own0 = {k: v.get().strip() for k, v in self.info_vars.items()}

    def save_info(self):
        """Saves the information typed for the photo shown in its project; True when changed."""
        if not self.info_vars or self.info_pr is None:
            return False
        now = {k: v.get().strip() for k, v in self.info_vars.items()}
        if now == self.info_own0:
            return False
        photo = self.items[self.index]["photo"]
        folder = os.path.dirname(photo)
        pr = load_project_file(folder)                     # read again: the project window may have saved it
        if pr is None:
            return False
        own = {k: v for k, v in ((pr.get("photos") or {}).get(os.path.basename(photo)) or {}).items()
               if k not in now}
        own.update({k: v for k, v in now.items() if v})
        if own:
            pr.setdefault("photos", {})[os.path.basename(photo)] = own
        else:
            pr.get("photos", {}).pop(os.path.basename(photo), None)
        save_project_file(folder, pr)
        self.info_own0 = now
        return True

    # ------------------------------------------------------------ view
    def fit(self):
        """Whole photo in the view. Done again once the window has its real size (at the opening the
        canvas is still 1 x 1 pixel: the first photo would stay invisible)."""
        c = self.canvas
        cw, ch = max(1, c.winfo_width()), max(1, c.winfo_height())
        self.need_fit = cw < 50 or ch < 50
        self.zoom = min(cw / self.W, ch / self.H)
        self.ox, self.oy = (self.W - cw / self.zoom) / 2, (self.H - ch / self.zoom) / 2
        self.redraw()

    def to_screen(self, x, y):
        """Photo pixel -> window position."""
        return (x - self.ox) * self.zoom, (y - self.oy) * self.zoom

    def to_image(self, sx, sy):
        """Window position -> photo pixel."""
        return sx / self.zoom + self.ox, sy / self.zoom + self.oy

    def view_base(self):
        """The photo as shown for the current view (cached: only rebuilt when the view changes)."""
        np, Image = self.np, self.Image
        c = self.canvas
        cw, ch = c.winfo_width(), c.winfo_height()
        key = (self.index, round(self.ox, 3), round(self.oy, 3), round(self.zoom, 6), cw, ch)
        if getattr(self, "_base", None) and self._base["key"] == key:
            return self._base
        x0, y0 = max(0, int(self.ox)), max(0, int(self.oy))
        x1 = min(self.W, int(math.ceil(self.ox + cw / self.zoom)))
        y1 = min(self.H, int(math.ceil(self.oy + ch / self.zoom)))
        if x1 <= x0 or y1 <= y0:
            self._base = {"key": key, "empty": True}
            return self._base
        src, k = (self.preview, self.k_preview) if self.zoom <= self.k_preview else (self.photo, 1.0)
        box = (int(x0 * k), int(y0 * k), max(int(x0 * k) + 1, int(round(x1 * k))),
               max(int(y0 * k) + 1, int(round(y1 * k))))
        sx0, sy0 = self.to_screen(box[0] / k, box[1] / k)
        sx1, sy1 = self.to_screen(box[2] / k, box[3] / k)
        size = (max(1, round(sx1 - sx0)), max(1, round(sy1 - sy0)))
        rgb = np.asarray(src.crop(box).resize(size, Image.Resampling.NEAREST if self.zoom > 2
                                              else Image.Resampling.BILINEAR))
        self._base = {"key": key, "empty": False, "rgb": rgb, "dim": (rgb * 0.45).astype(np.uint8),
                      "pos": (round(sx0), round(sy0)), "size": size,
                      "mbox": (int(box[0] / k), int(box[1] / k), int(box[2] / k), int(box[3] / k))}
        return self._base

    def redraw(self, fast=False):
        """Photo (cached) + cut-out (background dimmed, green outline) + scale outline + line / lasso."""
        if not hasattr(self, "zoom"):
            return
        self._pending = False
        np, cv2, Image = self.np, self.cv2, self.Image
        c = self.canvas
        b = self.view_base()
        self.update_bars()
        c.delete("overlay")
        if b["empty"]:
            c.delete("photo")
            self.img_item = None
            return
        x0, y0, x1, y1 = b["mbox"]
        m = self.mask[y0:y1, x0:x1]
        interp = cv2.INTER_NEAREST if (fast or self.zoom > 1) else cv2.INTER_AREA
        m = cv2.resize(m, b["size"], interpolation=interp) > 127
        part = np.where(m[..., None], b["rgb"], b["dim"])
        edge = m ^ (cv2.erode(m.view(np.uint8), np.ones((3, 3), np.uint8)) > 0)
        part[edge] = (0, 220, 0)
        self.tkimg = self.ImageTk.PhotoImage(Image.fromarray(part))
        if getattr(self, "img_item", None) and c.find_withtag("photo"):
            c.itemconfigure(self.img_item, image=self.tkimg)
            c.coords(self.img_item, *b["pos"])
        else:
            c.delete("photo")
            self.img_item = c.create_image(*b["pos"], image=self.tkimg, anchor="nw", tags="photo")
        it = self.items[self.index]
        if it.get("scale"):
            pts = [v for p in it["scale"] for v in self.to_screen(*p)]
            c.create_polygon(*pts, outline="#FF00FF", fill="", width=2, tags="overlay")
        if self.line:
            (ax, ay), (bx, by) = self.line
            c.create_line(*self.to_screen(ax, ay), *self.to_screen(bx, by), fill="#FFB000", width=3, tags="overlay")
        if getattr(self, "lasso", None) and len(self.lasso) > 1:
            pts = [v for p in self.lasso for v in self.to_screen(*p)]
            c.create_line(*pts, fill="#FFB000", width=2, tags="overlay")

    def schedule_redraw(self):
        """At most one redraw every 30 ms while painting (the mask itself is updated at once)."""
        if not getattr(self, "_pending", False):
            self._pending = True
            self.win.after(30, lambda: self.redraw(fast=True))

    def wheel(self, e):
        """Wheel: zoom on the point under the mouse."""
        x, y = self.to_image(e.x, e.y)
        self.zoom = min(8.0, max(0.02, self.zoom * (1.25 if e.delta > 0 else 0.8)))
        self.ox, self.oy = x - e.x / self.zoom, y - e.y / self.zoom
        self.redraw()

    def pan_move(self, e):
        """Moves the view while a button is held."""
        if self.pan:
            x0, y0, ox, oy = self.pan
            self.ox, self.oy = ox - (e.x - x0) / self.zoom, oy - (e.y - y0) / self.zoom
            self.redraw(fast=True)

    def view_span(self, axis):
        """Visible part of the photo along an axis: (start, length) in photo pixels."""
        c = self.canvas
        return ((self.ox, c.winfo_width() / self.zoom) if axis == 0 else (self.oy, c.winfo_height() / self.zoom))

    def scroll_view(self, axis, *args):
        """Scroll bar commands: "moveto f" or "scroll n units|pages"."""
        size = self.W if axis == 0 else self.H
        start, span = self.view_span(axis)
        if args[0] == "moveto":
            start = float(args[1]) * size
        elif args[0] == "scroll":
            step = span * (0.9 if args[2] == "pages" else 0.1)
            start += int(args[1]) * step
        lo, hi = min(0.0, size - span), max(0.0, size - span)       # never beyond the photo
        start = min(hi, max(lo, start))
        if axis == 0:
            self.ox = start
        else:
            self.oy = start
        self.redraw()

    def nudge(self, dx, dy):
        """Arrow keys: moves the view."""
        if dx:
            self.scroll_view(0, "scroll", dx, "units")
        if dy:
            self.scroll_view(1, "scroll", dy, "units")

    def update_bars(self):
        """Scroll bars set to the visible part of the photo."""
        for axis, bar, size in ((0, self.hbar, self.W), (1, self.vbar, self.H)):
            start, span = self.view_span(axis)
            bar.set(max(0.0, start / size), min(1.0, (start + span) / size))

    def hover(self, e):
        """Circle of the brush under the mouse."""
        self.canvas.delete("cursor")
        if self.tool.get() in ("erase", "add"):
            r = self.brush.get()
            self.canvas.create_oval(e.x - r, e.y - r, e.x + r, e.y + r, outline="white", tags="cursor")

    # ------------------------------------------------------------ editing
    # ------------------------------------------------------------ one click
    def tool_changed(self):
        """Tool chosen: the one-click model is prepared when it is chosen."""
        if self.tool.get() == "click":
            self.prepare_click()
        else:
            self.click_hint.set("")
        self.redraw()

    def prepare_click(self):
        """Loads the model (downloaded once, 45 MB) and encodes the photo shown, in the background."""
        st = self.click_state
        if st["busy"] or (st["index"] == self.index and st["ready"]):
            self.show_click_hint()
            return
        st.update(index=self.index, ready=False, busy=True)
        self.click_hint.set(tr("Preparing the one-click cut-out…"))
        rgb, index = self.np.asarray(self.photo), self.index

        def work():
            try:
                app = self.app
                if getattr(app, "click_model", None) is None:
                    import gerbil as engine
                    app.click_model = engine.ClickCutout(progress=lambda f: self.win.after(
                        0, self.click_hint.set, T("Téléchargement du modèle « un clic » (une fois) : ", "Downloading the one-click model (once): ") + f"{f:.0%}"))
                app.click_model.set_image(rgb)
                ok = None
            except Exception as e:
                ok = f"{type(e).__name__}: {e}"
            self.win.after(0, self.click_prepared, index, ok)
        threading.Thread(target=work, daemon=True).start()

    def click_prepared(self, index, error):
        """The photo is ready for one-click (or the error is shown)."""
        st = self.click_state
        st["busy"] = False
        if error:
            self.click_hint.set(tr("The one-click cut-out is not available: ") + error)
            return
        if index != self.index:                         # another photo was shown meanwhile
            st["index"] = None
            if self.tool.get() == "click":
                self.prepare_click()
            return
        st["ready"] = True
        self.show_click_hint()

    def show_click_hint(self):
        """How the one-click tool is used."""
        self.click_hint.set(tr("Click each object to keep: the computed cut-out is replaced by the objects "
                            "clicked. Shift + click: remove an object. Ctrl+Z: undo."))

    def click_object(self, x, y, keep=True):
        """One click: the object under the click (Segment Anything, edge of the
        computed cut-out where it agrees) is added (or removed with Shift)."""
        st = self.click_state
        if not (st["ready"] and st["index"] == self.index):
            self.prepare_click()
            return
        if not (0 <= x < self.W and 0 <= y < self.H):
            return
        import gerbil as engine
        sam = self.app.click_model.mask([(x, y, True)])
        computed = self.mask0 > 0 if not st["used"] else self.mask > 0
        obj = engine.click_refine(sam, self.mask0 > 0, max(6, round(max(self.W, self.H) / 400)))
        before = self.mask.copy()
        if keep:
            if not st["used"]:                          # first click: the objects clicked replace the cut-out
                self.mask[:] = 0
                st["used"] = True
            self.mask[obj] = 255
        else:
            self.mask[obj | (sam & computed)] = 0
        self._save_patch(0, 0, self.W, self.H, before)
        self.redraw()
        self.update_thumb()

    def _save_patch(self, x0, y0, x1, y1, before=None):
        """Keeps the part of the mask about to change, for Undo (30 steps)."""
        x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(self.W, int(x1)), min(self.H, int(y1))
        if x1 > x0 and y1 > y0:
            src = self.mask if before is None else before
            self.history.append(("mask", (x0, y0), src[y0:y1, x0:x1].copy()))
            del self.history[:-30]

    def typing(self):
        """A text field of the panel has the keyboard: Space and the arrows are for it."""
        w = self.win.focus_get()
        return isinstance(w, (tk.Entry, ttk.Entry, ttk.Combobox, tk.Text))

    def press(self, e):
        """Mouse pressed: starts the brush, the lasso, the line, or acts at once (piece,
        one click); Space held: moves the view."""
        if self.space:                                  # Space + drag: move the view
            self.pan = (e.x, e.y, self.ox, self.oy)
            return
        x, y = self.to_image(e.x, e.y)
        tool = self.tool.get()
        if tool in ("erase", "add"):
            self.stroke = {"before": self.mask.copy(), "pts": [(x, y)], "box": [x, y, x, y]}
            self._paint(x, y, x, y)
        elif tool == "click":
            self.click_object(x, y, keep=not (e.state & 0x0001))      # Shift: remove that object
        elif tool == "piece":
            xi, yi = int(x), int(y)
            if 0 <= xi < self.W and 0 <= yi < self.H and self.mask[yi, xi]:
                before = self.mask.copy()
                _, _, _, (bx, by, bw, bh) = self.cv2.floodFill(self.mask, None, (xi, yi), 0, flags=8)
                self._save_patch(bx, by, bx + bw, by + bh, before)
                self.redraw()
        elif tool in ("lasso_erase", "lasso_add"):
            self.lasso = [(x, y)]
        elif tool == "orient":
            self.line = [(x, y), (x, y)]

    def drag(self, e):
        """Mouse moved with the button held: paints, extends the lasso or the line."""
        if self.space:
            self.pan_move(e)
            return
        x, y = self.to_image(e.x, e.y)
        if self.stroke:
            px, py = self.stroke["pts"][-1]
            self.stroke["pts"].append((x, y))
            b = self.stroke["box"]
            self.stroke["box"] = [min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)]
            self._paint(px, py, x, y)
        elif getattr(self, "lasso", None):
            sx, sy = self.to_screen(*self.lasso[-1])
            self.lasso.append((x, y))
            self.canvas.create_line(sx, sy, e.x, e.y, fill="#FFB000", width=2, tags="overlay")
        elif self.line:
            self.line[1] = (x, y)
            self.canvas.delete("overlay")
            self.canvas.create_line(*self.to_screen(*self.line[0]), e.x, e.y, fill="#FFB000", width=3, tags="overlay")
        self.hover(e)

    def _paint(self, ax, ay, bx, by):
        """Paints (or erases) a stroke of the brush in the mask."""
        r = max(1, int(round(self.brush.get() / self.zoom)))
        v = 0 if self.tool.get() == "erase" else 255
        self.cv2.line(self.mask, (int(round(ax)), int(round(ay))), (int(round(bx)), int(round(by))), v, 2 * r)
        self.cv2.circle(self.mask, (int(round(bx)), int(round(by))), r, v, -1)
        self.schedule_redraw()

    def release(self, e):
        """Button released: ends the stroke, fills the lasso, or turns the object along
        the line drawn."""
        np = self.np
        if self.space:
            return
        if self.stroke:
            r = int(self.brush.get() / self.zoom) + 2
            x0, y0, x1, y1 = self.stroke["box"]
            self._save_patch(x0 - r, y0 - r, x1 + r + 1, y1 + r + 1, self.stroke["before"])
            self.stroke = None
            self.redraw()
        elif getattr(self, "lasso", None):
            pts = self.lasso
            self.lasso = None
            if len(pts) >= 3:
                a = np.array(pts)
                self._save_patch(a[:, 0].min() - 1, a[:, 1].min() - 1, a[:, 0].max() + 2, a[:, 1].max() + 2)
                v = 0 if self.tool.get() == "lasso_erase" else 255
                self.cv2.fillPoly(self.mask, [np.round(a).astype(np.int32)], v)
            self.redraw()
        elif self.line:
            (ax, ay), (bx, by) = self.line
            if math.hypot(bx - ax, by - ay) * self.zoom > 10:
                self.history.append(("angle", self.angle))
                self.angle = self.rim_angle(ax, ay, bx, by)
                self.update_thumb()
            self.line = None
            self.redraw()

    def rim_angle(self, ax, ay, bx, by):
        """Rotation (degrees, counterclockwise) that makes the line horizontal with the object below it."""
        np = self.np
        theta = math.degrees(math.atan2(by - ay, bx - ax))
        ys, xs = np.nonzero(self.mask[::8, ::8])
        cx, cy = (xs.mean() * 8, ys.mean() * 8) if len(xs) else ((ax + bx) / 2, (ay + by) / 2 + 1)
        vx, vy = cx - (ax + bx) / 2, cy - (ay + by) / 2
        for phi in (theta, theta + 180):
            a = math.radians(phi)
            if -math.sin(a) * vx + math.cos(a) * vy > 0:      # below the line once turned
                return round(phi % 360, 2)
        return round(theta % 360, 2)

    def turn(self, step):
        """Quarter turn of the object (or back to 0)."""
        self.history.append(("angle", self.angle))
        self.angle = 0.0 if step is None else (self.angle + step) % 360
        self.update_thumb()

    def undo(self):
        """Undoes the last change of the mask or of the angle."""
        if not self.history:
            return
        kind, *data = self.history.pop()
        if kind == "mask":
            (x0, y0), patch = data
            self.mask[y0:y0 + patch.shape[0], x0:x0 + patch.shape[1]] = patch
            if self.click_state["used"] and self.np.array_equal(self.mask, self.mask0):
                self.click_state["used"] = False          # back to the computed cut-out
            self.redraw()
        else:
            self.angle = data[0]
            self.update_thumb()

    def reset(self):
        """Undoes all the unsaved changes of this photo; if corrections were saved for it before, offers to
        remove them too (the computed cut-out comes back when the photo is processed again)."""
        self.history.append(("mask", (0, 0), self.mask.copy()))
        self.history.append(("angle", self.angle))
        self.mask, self.angle = self.mask0.copy(), self.angle0
        it = self.items[self.index]
        if (it.get("edited") or self.angle0) and messagebox.askyesno(
                "Gerbil", tr("Remove the corrections saved before for this photo?\n\n"
                          "The computed cut-out comes back when the photo is processed again."), parent=self.win):
            try:
                self.remove_saved(it["photo"])
                self.export(it["photo"])
                self.angle = self.angle0 = 0.0
            except OSError as e:
                messagebox.showerror("Gerbil", T(f"Impossible de supprimer les corrections :\n{e}", f"Could not remove the corrections:\n{e}"), parent=self.win)
        self.redraw()
        self.update_thumb()

    def remove_saved(self, photo):
        """Removes the corrections saved for a photo."""
        folder = os.path.join(os.path.dirname(photo), EDITS_DIR)
        name = os.path.basename(photo)
        mask_file = os.path.join(folder, os.path.splitext(name)[0] + "_mask.png")
        if os.path.exists(mask_file):
            os.remove(mask_file)
        jf = os.path.join(folder, EDITS_FILE)
        try:
            with open(jf, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            return
        if data.pop(name, None) is not None:
            with open(jf, "w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=1)

    def update_thumb(self):
        """The object as it will be exported (turned), small."""
        np = self.np
        ys, xs = np.nonzero(self.mask[::4, ::4])
        self.angle_txt.set(T(f"Objet tourné de {self.angle:g}°", f"Object turned by {self.angle:g}°") if self.angle else tr("Not turned"))
        if not len(xs):
            self.thumb_lbl.configure(image="")
            return
        x0, y0, x1, y1 = xs.min() * 4, ys.min() * 4, xs.max() * 4 + 4, ys.max() * 4 + 4
        crop = self.photo.crop((x0, y0, x1, y1))
        alpha = self.Image.fromarray(self.mask[y0:y1, x0:x1])
        rgba = crop.copy()
        rgba.putalpha(alpha)
        rgba.thumbnail((200, 140))
        if self.angle:
            rgba = rgba.rotate(self.angle, expand=True, resample=self.Image.Resampling.BICUBIC)
            rgba.thumbnail((200, 140))
        bg = self.Image.new("RGB", rgba.size, "white")
        bg.paste(rgba, mask=rgba.split()[3])
        self.thumb = self.ImageTk.PhotoImage(bg)
        self.thumb_lbl.configure(image=self.thumb)

    # ------------------------------------------------------------ saving
    def list_text(self, it):
        """Text of a photo in the list: status mark, name, export state."""
        mark = {"ok": "  ", "to verify": "! ", "failed": "x "}.get(it.get("status"), "? ")
        state = {"queued": "  (export waiting)", "running": "  (exporting…)", "done": "  ✓ exported"}
        return mark + os.path.basename(it["photo"]) + state.get(it.get("export"), "")

    def mark(self, photo, state):
        """Changes the export state shown for a photo."""
        for i, it in enumerate(self.items):
            if it["photo"] == photo:
                it["export"] = state
                if not getattr(self, "closed", False):
                    self.listbox.delete(i)
                    self.listbox.insert(i, self.list_text(it))
                    if i == self.index:
                        self.listbox.selection_set(i)

    @staticmethod
    def saved_mask_file(photo):
        """Path of the corrected mask of a photo (gerbil_edits)."""
        return os.path.join(os.path.dirname(photo), EDITS_DIR, os.path.splitext(os.path.basename(photo))[0] + "_mask.png")

    @staticmethod
    def saved_entry(photo):
        """Corrections saved for a photo (mask corrected?, angle)."""
        try:
            with open(os.path.join(os.path.dirname(photo), EDITS_DIR, EDITS_FILE), encoding="utf-8") as fh:
                return dict(json.load(fh).get(os.path.basename(photo)) or {})
        except (OSError, ValueError, AttributeError):
            return {}

    def export(self, photo):
        """The photo is processed again in the background as soon as its corrections are saved: the
        results and the previews are up to date without going through all the photos."""
        self.queue.append(photo)
        self.mark(photo, "queued")
        self.pump()

    def pump(self):
        """Starts the waiting exports once the main window is free (one run at a time, all those waiting)."""
        app = self.app
        if self.running and (app.proc is None or app.proc.poll() is not None) and getattr(app, "kind", "") != "pip":
            for ph in self.running:
                self.mark(ph, "done")
            self.running = []
        if self.queue and not self.running and app.proc is None:
            self.running, self.queue = sorted(set(self.queue)), []
            for ph in self.running:
                self.mark(ph, "running")
            app.run(self.running, quiet=True)
        if self.queue or self.running:
            app.root.after(700, self.pump)

    def save_current(self):
        """Saves the corrections of the photo shown (EDITS_DIR next to the photo); True when changed."""
        np = self.np
        it = self.items[self.index]
        photo = it["photo"]
        changed_mask = not np.array_equal(self.mask, self.mask0)
        changed_angle = abs(self.angle - self.angle0) > 1e-6
        if not (changed_mask or changed_angle):
            return False
        folder = os.path.join(os.path.dirname(photo), EDITS_DIR)
        os.makedirs(folder, exist_ok=True)
        jf = os.path.join(folder, EDITS_FILE)
        try:
            with open(jf, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            data = {}
        name = os.path.basename(photo)
        mask_file = os.path.join(folder, os.path.splitext(name)[0] + "_mask.png")
        entry = dict(data.get(name) or {})
        if changed_mask:
            self.Image.fromarray(self.mask).save(mask_file, compress_level=1)
            entry["mask"] = True
        entry["angle"] = round(self.angle % 360, 2)
        if not entry.get("mask") and not entry["angle"]:
            data.pop(name, None)
        else:
            data[name] = entry
        tmp = jf + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1)
        os.replace(tmp, jf)
        self.mask0, self.angle0 = self.mask.copy(), self.angle
        return True

    def accept(self):
        """Saves the corrections of the photo, exports it again, shows the next one."""
        try:
            changed = self.save_current()
            changed = self.save_info() or changed
            if changed:
                self.export(self.items[self.index]["photo"])
        except OSError as e:
            messagebox.showerror("Gerbil", T(f"Impossible d'enregistrer les corrections :\n{e}", f"Could not save the corrections:\n{e}"), parent=self.win)
            return
        self.goto(self.index + 1)

    def fix_scale(self):
        """Opens the manual scale of the photo."""
        photo = self.items[self.index]["photo"]
        try:
            ScaleWindow(self.app, photo, on_saved=lambda: self.export(photo))
        except (ImportError, OSError) as e:
            messagebox.showerror("Gerbil", T(f"Impossible d'ouvrir la fenêtre de l'échelle :\n{e}", f"Could not open the scale window:\n{e}"), parent=self.win)

    def close(self):
        """Closes, offering to keep the corrections of the photo shown."""
        if getattr(self, "closed", False):
            return
        self.closed = True
        np = self.np
        info_changed = bool(self.info_vars) and {k: v.get().strip() for k, v in self.info_vars.items()} != self.info_own0
        if hasattr(self, "mask") and (not np.array_equal(self.mask, self.mask0) or abs(self.angle - self.angle0) > 1e-6
                                      or info_changed):
            if messagebox.askyesno("Gerbil", tr("Keep the corrections of the photo shown?"), parent=self.win):
                try:
                    changed = self.save_current()
                    changed = self.save_info() or changed
                    if changed:
                        self.export(self.items[self.index]["photo"])
                except OSError as e:
                    messagebox.showerror("Gerbil", T(f"Impossible d'enregistrer les corrections :\n{e}", f"Could not save the corrections:\n{e}"), parent=self.win)
        self.win.destroy()                         # (the waiting exports go on: pump runs on the main window)


class PlatesWindow:
    """Plates of a results folder (gerbil_plates): objects at a chosen scale on pages, captions, graphic
    scale bar in the manner of QGIS; live preview of the pages; written as SVG (Illustrator, Inkscape).
    The settings are remembered (house style of the scale bar)."""

    def __init__(self, app, folder):
        """The plates window: three tabs of settings (plate, scale bar, scales and
        drawings), live preview with zoom, buttons."""
        import gerbil_plates as gp
        self.gp, self.app, self.folder = gp, app, folder
        self.st = gp.PlateSettings.from_dict(app.s.get("plates") or {})
        self.items = gp.collect(folder, True)
        self.thumbs = {}                            # item path -> reduced image (preview)
        self.pages, self.page_no, self.job = [], 0, None
        self.win = win = tk.Toplevel(app.root)
        win.title(T(f"Planches - {folder}", f"Plates - {folder}"))
        win.configure(bg=WINDOW_BG)
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        w, h = min(int(sw * 0.9), 1500), int(sh * 0.88)
        win.geometry(f"{w}x{h}+{(sw - w) // 2}+{int(sh * 0.02)}")
        fields = gp.report_fields(self.items)
        self.vars = {}

        foot = ttk.Frame(win, style="Window.TFrame", padding=12)          # packed first: always visible
        foot.pack(side="bottom", fill="x")
        self.write_btn = ttk.Button(foot, text=tr("Write the plates (SVG)"), style="Run.TButton", command=self.write)
        self.write_btn.pack(side="left")
        self.open_btn = ttk.Button(foot, text=tr("Open the plates folder"), command=self.open_folder, state="disabled")
        self.open_btn.pack(side="left", padx=8)
        ttk.Button(foot, text=tr("Close"), command=self.close).pack(side="right")
        self.msg = tk.StringVar()
        ttk.Label(foot, textvariable=self.msg, style="Footer.TLabel").pack(side="left", padx=12)

        body = ttk.Frame(win, style="Window.TFrame", padding=(12, 12, 12, 0))
        body.pack(fill="both", expand=True)
        side = ttk.Frame(body, style="Window.TFrame")
        side.pack(side="left", fill="y")
        self.nb = nb = ttk.Notebook(side)
        nb.pack(fill="y", expand=True)
        plate = ttk.Frame(nb, style="Card.TFrame", padding=12)
        barf = ttk.Frame(nb, style="Card.TFrame", padding=12)
        nb.add(plate, text=tr("  Plate  "))
        nb.add(barf, text=tr("  Scale bar  "))
        drawf = ttk.Frame(nb, style="Card.TFrame", padding=12)
        nb.add(drawf, text=tr("  Scales & drawings  "))

        r = 0
        def row(parent, label, widget, tip=None):
            nonlocal r
            ttk.Label(parent, text=tr(label)).grid(row=r, column=0, sticky="w", pady=3, padx=(0, 8))
            widget.grid(row=r, column=1, sticky="w", pady=3)
            if tip:
                Tooltip(widget, tr(tip))
            r += 1
            return widget

        def var(key, value, kind=tk.StringVar):
            v = kind(value=value)
            v.trace_add("write", lambda *_: self.changed())
            self.vars[key] = v
            return v

        def combo(parent, key, value, values, width=12, state="readonly"):
            return ttk.Combobox(parent, textvariable=var(key, value), values=values, width=width, state=state)

        def entry(parent, key, value, width=8):
            return ttk.Entry(parent, textvariable=var(key, value), width=width)

        def check(parent, key, value, text):
            return ttk.Checkbutton(parent, text=tr(text), variable=var(key, bool(value), tk.BooleanVar))

        st, b = self.st, self.st.bar
        doubtful = sum(it.doubtful for it in self.items)
        ttk.Label(plate, text=T(f"{len(self.items) - doubtful} objet(s) à taille réelle", f"{len(self.items) - doubtful} object(s) with a real size")
                  + (T(f" (+{doubtful} à vérifier)", f" (+{doubtful} to be verified)") if doubtful else ""), style="Muted.TLabel").grid(
            row=r, column=0, columnspan=2, sticky="w", pady=(0, 6))
        r += 1
        row(plate, tr("Plate title"), entry(plate, "title", st.title, 30),
            tr("Optional, at the top of each plate; {page}, {pages}, {group} and {scale} (1:2) are replaced, "
            "e.g. \"QSR25 - US 1209 - Plate {page} - {scale}\". Empty: no title."))
        tf = ttk.Frame(plate, style="Card.TFrame")
        entry(tf, "title_pt", gp.fmt(st.title_pt), 5).pack(side="left")
        ttk.Label(tf, text=tr(" pt   ")).pack(side="left")
        combo(tf, "title_align", st.title_align, ["left", "centre", "right"], 7).pack(side="left")
        row(plate, tr("Title size, place"), tf)
        row(plate, tr("File names"), entry(plate, "file_name", st.file_name, 30),
            tr("Name of the SVG files: {page} (01, 02…), {pages}, {group}, {scale} (1-2), e.g. \"QSR25_US1209_pl{page}\". "
            "Without {page}, the number is added."))
        self.names_lbl = tk.StringVar()
        ttk.Label(plate, textvariable=self.names_lbl, style="Muted.TLabel", wraplength=300).grid(
            row=r, column=1, sticky="w")
        r += 1
        row(plate, tr("Scale  1 :"), combo(plate, "ratio", gp.fmt(st.ratio), ["1", "1.5", "2", "3", "4", "5", "10"], 6,
                                       "normal"), "1:2 = objects drawn at half their real size.")
        row(plate, "", check(plate, "fit_large", st.fit_large, tr("Reduce the objects too large for the page")),
            tr("An object that does not fit at this scale goes to 1:2, 1:3… on plates of their own, each with its "
            "scale bar (one scale per plate)."))
        row(plate, "", ttk.Button(plate, text=tr("Scale per object…"), style="Small.TButton", command=self.object_scales),
            tr("Choose a scale for some objects (e.g. a large vessel at 1:3): they go on plates of their own."))
        row(plate, "Page", combo(plate, "page", st.page, list(gp.PAGES) + ["custom"], 8))
        row(plate, "", check(plate, "landscape", st.landscape, "Landscape"))
        size = ttk.Frame(plate, style="Card.TFrame")
        entry(size, "width_mm", gp.fmt(st.width_mm), 6).pack(side="left")
        ttk.Label(size, text=tr(" x ")).pack(side="left")
        entry(size, "height_mm", gp.fmt(st.height_mm), 6).pack(side="left")
        ttk.Label(size, text=tr(" mm")).pack(side="left")
        row(plate, tr("Custom size"), size, tr("Page size when the page is 'custom'."))
        row(plate, tr("Margins (mm)"), entry(plate, "margin_mm", gp.fmt(st.margin_mm)))
        row(plate, tr("Space between (mm)"), entry(plate, "gap_mm", gp.fmt(st.gap_mm)))
        row(plate, tr("Order by"), combo(plate, "order", st.order, fields))
        row(plate, tr("Group by"), combo(plate, "group", st.group or "(none)", ["(none)"] + fields[1:]),
            tr("Each value (US, material…) starts a new row, or a new page."))
        row(plate, "", check(plate, "group_new_page", st.group_new_page, tr("A new page for each group")))
        row(plate, "Caption", entry(plate, "caption", st.caption, 26),
            tr("Text under each object: {name} (output name) or a column of the report, e.g. ")
            + ", ".join("{" + f + "}" for f in fields[1:5]) + "; empty: no caption.")
        row(plate, tr("Caption font"), combo(plate, "caption_font", st.caption_font, list(gp.FONTS), 16))
        row(plate, tr("Caption size (pt)"), entry(plate, "caption_pt", gp.fmt(st.caption_pt)))
        row(plate, tr("Images (dpi)"), combo(plate, "dpi", str(st.dpi), ["300", "600", "1200"], 6),
            tr("Resolution of the embedded images on the paper (600: print quality; never enlarged)."))
        var("object_ratios", json.dumps(st.object_ratios or {}))
        row(plate, "", check(plate, "include_doubtful", st.include_doubtful,
                             tr("Also the photos to be verified (_to_be_verified)")))
        row(plate, "", check(plate, "measurements", st.measurements, tr("Measurements as guides (hidden layer)")),
            tr("Width and height of each object as dimension lines, on a 'Measurements' layer hidden in the SVG: "
            "show it in Illustrator or Inkscape to place drawings. Layout guides, not data."))
        self.show_measures = tk.BooleanVar(value=False)
        self.show_measures.trace_add("write", lambda *_: self.changed())
        row(plate, "", ttk.Checkbutton(plate, text=tr("Show the measurements in the preview"),
                                       variable=self.show_measures))

        r = 0
        self.bar_canvas = tk.Canvas(barf, width=360, height=70, bg="white", highlightthickness=1,
                                    highlightbackground=LAVENDER_LINE)
        self.bar_canvas.grid(row=r, column=0, columnspan=2, pady=(0, 8))
        r += 1
        row(barf, "Style", combo(barf, "bar.style", b.style, list(gp.BAR_STYLES), 16))
        row(barf, tr("Bar length (real cm)"), combo(barf, "bar.length_cm", gp.fmt(b.length_cm) if b.length_cm else "auto",
                                       ["auto", "1", "2", "5", "10", "20", "50"], 6, "normal"),
            tr("Length the bar stands for (e.g. 5 = a 5 cm bar, drawn 2.5 cm long at 1:2); auto: 1, 2, 5, 10, 20 "
            "or 50 cm, at most a third of the page width."))
        row(barf, "Segments", combo(barf, "bar.segments", str(b.segments) if b.segments else "auto",
                                    ["auto", "1", "2", "4", "5", "10"], 6, "normal"))
        row(barf, tr("First segment cut in"), combo(barf, "bar.subdivisions", str(b.subdivisions) if b.subdivisions > 1
                                                else "none", ["none", "2", "4", "5", "10"], 6),
            "e.g. 10: the first centimetre divided into millimetres.")
        row(barf, tr("Bar height (mm)"), entry(barf, "bar.height_mm", gp.fmt(b.height_mm)),
            tr("Thickness of the bar on the paper; its length on the paper follows the scale of each plate."))
        row(barf, tr("Line width (mm)"), entry(barf, "bar.line_mm", gp.fmt(b.line_mm)))
        colours = ttk.Frame(barf, style="Card.TFrame")
        for key, text in (("bar.fill", "Fill"), ("bar.fill2", tr("Second fill")), ("bar.line", "Line"),
                          ("bar.font_color", "Text")):
            self.colour_button(colours, key, getattr(b, key[4:]), text)
        row(barf, "Colours", colours)
        row(barf, "Numbers", combo(barf, "bar.labels", b.labels, ["ends", "all", "none"], 8),
            "ends: 0 and the end; all: every segment.")
        row(barf, tr("Numbers placed"), combo(barf, "bar.label_position", b.label_position, ["below", "above"], 8))
        row(barf, "Unit", combo(barf, "bar.unit", b.unit, ["cm", "mm", ""], 6, "normal"),
            tr("Written after the last number; mm: the numbers are given in millimetres."))
        row(barf, "Font", combo(barf, "bar.font", b.font, list(gp.FONTS), 16))
        row(barf, tr("Size (pt)"), entry(barf, "bar.font_pt", gp.fmt(b.font_pt)))
        row(barf, "", check(barf, "bar.bold", b.bold, "Bold"))
        row(barf, "", check(barf, "bar.show_ratio", b.show_ratio, tr("Write the scale (1:2) after the bar")))
        row(barf, tr("On the page"), combo(barf, "bar.position", b.position,
                                       ["bottom right", "bottom centre", "bottom left"], 12))

        r = 0
        ttk.Label(drawf, text=tr("SCALES"), style="Section.TLabel").grid(row=r, column=0, columnspan=2, sticky="w")
        r += 1
        row(drawf, "", check(drawf, "by_material", st.by_material, tr("Scale by material")),
            "Each object at the reduction of its material (publication conventions, DMS Bruxelles 2009): "
            "ceramics and glass 1/3, iron 2/3, stone 1/3… The scale per object still prevails.")
        row(drawf, tr("Material column"), combo(drawf, "material_field", st.material_field, fields, 16, "normal"))
        rules = tk.Text(drawf, width=34, height=4, wrap="word", font=(FONT_SERIF, 9), relief="flat",
                        highlightthickness=1, highlightbackground=LAVENDER_LINE)
        rules.insert("1.0", st.material_ratios)
        rules_var = var("material_ratios", st.material_ratios)
        rules.bind("<KeyRelease>", lambda _: rules_var.set(rules.get("1.0", "end").strip()))
        row(drawf, "Reductions", rules, "word=reduction, separated by ';' - the word is looked for in the "
                                         "material (\"céramique commune\" contains \"céramique\").")
        row(drawf, "", check(drawf, "mix_scales", st.mix_scales, tr("Several scales on one plate")),
            tr("Objects at different scales on the same plate: the scale is written in their caption, one "
            "bar per scale. Unticked: one scale per plate (the usual way)."))
        ttk.Label(drawf, text=tr("DRAWINGS"), style="Section.TLabel").grid(row=r, column=0, columnspan=2, sticky="w",
                                                                      pady=(14, 0))
        r += 1
        dfr = ttk.Frame(drawf, style="Card.TFrame")
        entry(dfr, "drawings_folder", st.drawings_folder, 26).pack(side="left")
        ttk.Button(dfr, text="…", width=3, command=self.pick_drawings).pack(side="left", padx=(4, 0))
        row(drawf, tr("Folder of the drawings"), dfr, tr("Drawings of the objects (.svg; .ai, .pdf, .eps through "
                                                  "Inkscape), placed beside their photo, kept as vectors."))
        row(drawf, tr("Drawing names"), entry(drawf, "drawings_match", st.drawings_match, 26),
            "{name}: a drawing named like the output name of the photo. Or the fields of its name, e.g. "
            "{site}_{number}: matched with the object's (leading zeros ignored).")
        row(drawf, tr("Drawings at  1 :"), combo(drawf, "drawings_ratio", gp.fmt(st.drawings_ratio),
                                             ["1", "2", "3", "5"], 6, "normal"),
            tr("Scale of the drawings on their own paper (usually 1:1)."))
        row(drawf, tr("Drawing placed"), combo(drawf, "drawings_side", st.drawings_side, ["left", "right"], 8))
        self.draw_lbl = tk.StringVar()
        ttk.Label(drawf, textvariable=self.draw_lbl, style="Muted.TLabel", wraplength=300).grid(
            row=r, column=0, columnspan=2, sticky="w", pady=(6, 0))
        if not gp.inkscape():
            ttk.Label(drawf, style="Muted.TLabel", wraplength=300, text=(
                tr("Inkscape is not installed: only .svg drawings can be used, and they show as boxes in the "
                "preview (they are written as vectors all the same)."))).grid(row=r + 1, column=0, columnspan=2,
                                                                             sticky="w")

        view = ttk.Frame(body, style="Window.TFrame")
        view.pack(side="left", fill="both", expand=True, padx=(12, 0))
        nav = ttk.Frame(view, style="Window.TFrame")
        nav.pack(fill="x")
        ttk.Button(nav, text="◀", width=3, command=lambda: self.turn(-1)).pack(side="left")
        self.page_lbl = tk.StringVar()
        ttk.Label(nav, textvariable=self.page_lbl, style="Status.TLabel").pack(side="left", padx=8)
        ttk.Button(nav, text="▶", width=3, command=lambda: self.turn(1)).pack(side="left")
        self.warn = tk.StringVar()
        ttk.Label(nav, textvariable=self.warn, style="Footer.TLabel").pack(side="left", padx=12)
        ttk.Label(nav, text=tr("Wheel: zoom · middle button: move · right-click an object: its scale"),
                  style="Footer.TLabel").pack(side="right")
        cv = ttk.Frame(view, style="Window.TFrame")
        cv.pack(fill="both", expand=True, pady=(6, 0))
        cv.rowconfigure(0, weight=1)
        cv.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(cv, bg="#E6E2F2", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        xs = ttk.Scrollbar(cv, orient="horizontal", command=self.canvas.xview)
        ys = ttk.Scrollbar(cv, orient="vertical", command=self.canvas.yview)
        xs.grid(row=1, column=0, sticky="ew")
        ys.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)
        self.zoom, self.view = 1.0, None
        self.canvas.bind("<Configure>", lambda _: self.changed())
        self.canvas.bind("<MouseWheel>", self.wheel)
        self.canvas.bind("<ButtonPress-2>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B2-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.canvas.bind("<ButtonPress-3>", self.object_menu)
        win.protocol("WM_DELETE_WINDOW", self.close)
        self.changed()

    def object_scales(self):
        """Small window: each object with its size and its scale (plate scale, or one chosen for it)."""
        gp = self.gp
        top = tk.Toplevel(self.win)
        top.title(tr("Scale per object"))
        top.configure(bg=WINDOW_BG)
        top.transient(self.win)
        ttk.Label(top, text=tr("Select objects, choose a scale, then Set. 'plate' = the scale of the plates "
                            "(reduced automatically if too large)."), style="Footer.TLabel",
                  wraplength=460).pack(anchor="w", padx=10, pady=(10, 4))
        tree = ttk.Treeview(top, columns=("size", "scale"), show="tree headings", height=16, selectmode="extended")
        tree.heading("#0", text=tr("Object"), anchor="w")
        tree.heading("size", text=tr("Size (cm)"), anchor="w")
        tree.heading("scale", text=tr("Scale"), anchor="w")
        tree.column("#0", width=230)
        tree.column("size", width=110)
        tree.column("scale", width=125)
        sb = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        bar = ttk.Frame(top, style="Window.TFrame", padding=10)
        bar.pack(side="bottom", fill="x")
        sb.pack(side="right", fill="y", padx=(0, 10))
        tree.pack(fill="both", expand=True, padx=(10, 0))
        chosen = dict(self.st.object_ratios or {})

        def fill():
            tree.delete(*tree.get_children())
            st = self.settings()
            st.object_ratios = {}                       # the scale each object would get without a choice
            for it in self.items:
                r = chosen.get(it.name)
                shown = f"1:{gp.fmt(r)}" if r else f"plate (1:{gp.fmt(gp.object_ratio(it, st))})"
                tree.insert("", "end", iid=it.name, text=it.name,
                            values=(f"{it.width_cm:.1f} x {it.height_cm:.1f}", shown))
        scale = tk.StringVar(value="2")
        ttk.Label(bar, text=tr("Scale  1 :")).pack(side="left")
        ttk.Combobox(bar, textvariable=scale, values=["plate"] + [gp.fmt(r) for r in gp.RATIOS], width=7).pack(
            side="left", padx=(4, 8))

        def set_selected():
            for name in tree.selection():
                v = scale.get().strip().replace(",", ".")
                if v == "plate":
                    chosen.pop(name, None)
                else:
                    try:
                        chosen[name] = float(v)
                    except ValueError:
                        return
            self.vars["object_ratios"].set(json.dumps(chosen))
            fill()
        ttk.Button(bar, text=tr("Set for selected"), command=set_selected).pack(side="left")
        ttk.Button(bar, text=tr("Close"), command=top.destroy).pack(side="right")
        fill()

    def wheel(self, e):
        """Zoom on the point under the mouse (1 = whole page, up to 8)."""
        if not self.view:
            return
        k, x0, y0 = self.view
        mx = (self.canvas.canvasx(e.x) - x0) / k                 # point of the page (mm)
        my = (self.canvas.canvasy(e.y) - y0) / k
        self.zoom = min(8.0, max(1.0, self.zoom * (1.25 if e.delta > 0 else 0.8)))
        self.refresh()
        k, x0, y0 = self.view
        sr = [float(v) for v in str(self.canvas.cget("scrollregion")).split()]
        if len(sr) == 4 and sr[2] > 0 and sr[3] > 0:          # the same point stays under the mouse
            self.canvas.xview_moveto(max(0.0, (x0 + mx * k - e.x) / sr[2]))
            self.canvas.yview_moveto(max(0.0, (y0 + my * k - e.y) / sr[3]))

    def object_menu(self, e):
        """Right-click on an object of the preview: a menu of scales for it (kept in the plate settings)."""
        if not self.view or not self.pages:
            return
        k, x0, y0 = self.view
        mx, my = (self.canvas.canvasx(e.x) - x0) / k, (self.canvas.canvasy(e.y) - y0) / k
        hit = None
        for p in self.pages[self.page_no][1]:
            bx0, by0, bx1, by1 = p.box or (p.x, p.y, p.x + p.w, p.y + p.h)
            if bx0 <= mx <= bx1 and by0 <= my <= by1:
                hit = p
                break
        if hit is None:
            return
        gp, name = self.gp, hit.item.name
        chosen = dict(self.st.object_ratios or {})
        menu = tk.Menu(self.win, tearoff=False)
        menu.add_command(label=f"{name}  (" + T("actuellement", "now") + f" 1:{gp.fmt(hit.ratio)})", state="disabled")
        menu.add_separator()

        def choose(r):
            if r is None:
                chosen.pop(name, None)
            else:
                chosen[name] = r
            self.vars["object_ratios"].set(json.dumps(chosen))
        menu.add_command(label=tr("Scale of the plates (automatic)"), command=lambda: choose(None))
        for r in gp.RATIOS[:9]:
            menu.add_command(label=f"1:{gp.fmt(r)}", command=lambda r=r: choose(float(r)))
        try:
            menu.tk_popup(e.x_root, e.y_root)
        finally:
            menu.grab_release()

    def pick_drawings(self):
        """Chooses the folder of the drawings."""
        d = filedialog.askdirectory(parent=self.win, title=tr("Folder of the drawings"),
                                    initialdir=self.vars["drawings_folder"].get() or self.folder)
        if d:
            self.vars["drawings_folder"].set(os.path.normpath(d))

    def colour_button(self, parent, key, value, text):
        """A colour swatch that opens the colour chooser."""
        from tkinter import colorchooser
        v = tk.StringVar(value=value)
        v.trace_add("write", lambda *_: self.changed())
        self.vars[key] = v
        f = ttk.Frame(parent, style="Card.TFrame")
        f.pack(side="left", padx=(0, 6))
        sw = tk.Label(f, bg=value, width=3, relief="solid", bd=1, cursor="hand2")
        sw.pack()
        ttk.Label(f, text=text, style="Muted.TLabel").pack()

        def pick(_=None):
            c = colorchooser.askcolor(v.get(), parent=self.win, title=text)[1]
            if c:
                v.set(c.upper())
                sw.configure(bg=c)
        sw.bind("<Button-1>", pick)

    def settings(self):
        """PlateSettings from the window (invalid numbers keep their previous value)."""
        gp, st = self.gp, self.gp.PlateSettings.from_dict(self.st.to_dict())

        def number(text, old, integer=False, auto=0):
            t = str(text).strip().replace(",", ".")
            if t in ("auto", "none", ""):
                return auto
            try:
                v = float(t)
                return int(v) if integer else v
            except ValueError:
                return old
        for key, v in self.vars.items():
            obj, name = (st.bar, key[4:]) if key.startswith("bar.") else (st, key)
            old = getattr(obj, name)
            val = v.get()
            if isinstance(old, bool):
                val = bool(val)
            elif isinstance(old, int):
                val = number(val, old, True)
            elif isinstance(old, float):
                val = number(val, old)
            elif name == "group" and val == "(none)":
                val = ""
            elif name == "object_ratios":
                try:
                    val = {k: float(v) for k, v in json.loads(val).items()}
                except (ValueError, AttributeError):
                    val = old
            setattr(obj, name, val)
        if st.ratio <= 0:
            st.ratio = 1.0
        return st

    def changed(self):
        """A setting changed: preview drawn again a moment later."""
        if self.job:
            self.win.after_cancel(self.job)
        self.job = self.win.after(250, self.refresh)

    def thumb(self, item, w_mm, h_mm):
        """Reduced image of an object for the preview (cached)."""
        im = self.thumbs.get(item.path)
        if im is None:
            from PIL import Image
            with Image.open(item.path) as src:
                im = src.convert("RGBA")
                if item.bbox:
                    im = im.crop(item.bbox)
                im.thumbnail((1600, 1600))                  # (sharp enough when zooming in)
            self.thumbs[item.path] = im
        return im

    def refresh(self):
        """Lays out the plates with the current settings and draws the page shown."""
        self.job = None
        gp = self.gp
        self.st = st = self.settings()
        items = [it for it in self.items if st.include_doubtful or not it.doubtful]
        self.pages, warnings = gp.layout(items, st) if items else ([], [])
        self.page_no = min(self.page_no, max(0, len(self.pages) - 1))
        self.warn.set(("⚠ " + warnings[0] + (f" (+{len(warnings) - 1})" if len(warnings) > 1 else ""))
                      if warnings else "")
        cw, ch = max(50, self.canvas.winfo_width()), max(50, self.canvas.winfo_height())
        self.canvas.delete("all")
        from PIL import ImageTk
        if self.pages:
            W, H = st.page_size()
            k = min((cw - 20) / W, (ch - 20) / H) * self.zoom
            dr = gp.page_drawing(st, self.pages[self.page_no], self.page_no + 1, len(self.pages), images=self.thumb)
            img = gp.render(dr, k, show_hidden=self.show_measures.get())
            self.page_img = ImageTk.PhotoImage(img)
            x0, y0 = max(10, (cw - img.width) // 2), max(10, (ch - img.height) // 2)
            self.canvas.create_image(x0, y0, image=self.page_img, anchor="nw")
            self.canvas.configure(scrollregion=(0, 0, max(cw, img.width + 20), max(ch, img.height + 20)))
            self.view = (k, x0, y0)
            n_obj = sum(len(p[1]) for p in self.pages)
            self.page_lbl.set(T(f"Planche {self.page_no + 1} / {len(self.pages)}, {n_obj} objet(s) au 1:{gp.fmt(st.ratio)}",
                                f"Plate {self.page_no + 1} / {len(self.pages)}, {n_obj} object(s) at 1:{gp.fmt(st.ratio)}"))
        else:
            self.page_lbl.set(tr("No object with a real size in this folder"))
        if st.drawings_folder:
            n = sum(1 for it in items if it.drawing)
            self.draw_lbl.set(T(f"{n} objet(s) avec leur dessin, sur {len(items)}.", f"{n} object(s) with their drawing, out of {len(items)}."))
        else:
            self.draw_lbl.set("")
        names = gp.plate_file_names(st, self.pages) if self.pages else []
        self.names_lbl.set(("→ " + names[0] + (f" … {names[-1]}" if len(names) > 1 else "")) if names else "")
        # the bar alone, larger
        bw, bh = gp.bar_size(st.bar, st.ratio, 0.3 * (st.page_size()[0] - 2 * st.margin_mm))
        dr = gp.Drawing(bw + 6, bh + 6)
        gp.draw_bar(dr, st.bar, st.ratio, 3, 3, 0.3 * (st.page_size()[0] - 2 * st.margin_mm))
        k = min(340 / dr.width, 60 / dr.height, 12)
        self.bar_img = ImageTk.PhotoImage(gp.render(dr, k))
        self.bar_canvas.delete("all")
        self.bar_canvas.create_image(180, 35, image=self.bar_img)
        self.app.s["plates"] = st.to_dict()

    def turn(self, step):
        """Previous / next plate."""
        if self.pages:
            self.page_no = (self.page_no + step) % len(self.pages)
            self.refresh()

    def write(self):
        """Writes the SVG plates in a thread."""
        st = self.settings()
        self.write_btn.state(["disabled"])
        self.msg.set(tr("Writing the plates…"))
        out = os.path.join(self.folder, "plates")

        def work():
            try:
                files, warnings = self.gp.write_plates(
                    self.folder, st, out, lambda i, n: self.win.after(0, self.msg.set, T(f"Planche {i} / {n}…", f"Plate {i} / {n}…")))
                text = T(f"{len(files)} planche(s) écrite(s) dans {out}", f"{len(files)} plate(s) written in {out}") + (
                    T(f"  ({len(warnings)} avertissement(s))", f"  ({len(warnings)} warning(s))") if warnings else "")
            except Exception as e:
                text = T("Les planches n'ont pas pu être écrites : ", "The plates could not be written: ") + f"{type(e).__name__}: {e}"
            self.win.after(0, self.written, text)
        threading.Thread(target=work, daemon=True).start()

    def written(self, text):
        """Plates written: message, settings saved."""
        self.msg.set(text)
        self.write_btn.state(["!disabled"])
        self.open_btn.state(["!disabled"])
        self.app.save_settings()

    def open_folder(self):
        """Opens the folder of the plates."""
        d = os.path.join(self.folder, "plates")
        if os.path.isdir(d):
            os.startfile(d)

    def close(self):
        """Closes, saving the plate settings (house style)."""
        self.app.s["plates"] = self.settings().to_dict()
        self.app.save_settings()
        self.win.destroy()


PROFILES_DIR = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "Gerbil", "profiles")
PROFILE_FILE = "gerbil_profile.json"           # a profile placed next to the photos is used by the engine
PROFILE_SETTINGS = ("background", "compression", "psd", "original_layer", "original_copy", "control", "layout",
                    "margin_cm", "gap_cm", "scale", "scale_cm", "default_ppi", "remove_putty", "ai", "ai_model")


def profile_names():
    """Names of the site profiles of the library."""
    try:
        return sorted(os.path.splitext(f)[0] for f in os.listdir(PROFILES_DIR) if f.lower().endswith(".json"))
    except OSError:
        return []


def profile_path(name):
    """File of a profile of the library."""
    return os.path.join(PROFILES_DIR, name + ".json")


def safe_name(name):
    """A name usable as a Windows file name."""
    return "".join("_" if c in '<>:"/\\|?*' else c for c in name).strip(" .")


class ProfileWindow:
    """Site profile: what is known of the photos of a site or a campaign (background, learned scales,
    options), chosen once in the main window instead of setting everything again. Saved in PROFILES_DIR;
    "Put next to the photos…" copies it as gerbil_profile.json into a folder of photos, where the
    engine uses it by itself (and the team can share it)."""

    def __init__(self, app, name=None):
        """The site profile window: name, background, learned scales, options."""
        self.app = app
        self.pr = {"name": name or "", "background": "auto", "learned_first": False, "scales": [], "settings": {}}
        if name:
            try:
                with open(profile_path(name), encoding="utf-8") as fh:
                    self.pr.update(json.load(fh))
            except (OSError, ValueError):
                pass
        self.win = win = tk.Toplevel(app.root)
        win.title(tr("Site profile"))
        win.configure(bg=WINDOW_BG)
        win.transient(app.root)
        card = ttk.Frame(win, style="Card.TFrame", padding=14)
        card.pack(fill="both", expand=True, padx=10, pady=10)
        card.columnconfigure(1, weight=1)
        r = 0
        ttk.Label(card, text=tr("Name")).grid(row=r, column=0, sticky="w", pady=3)
        self.name = tk.StringVar(value=self.pr["name"])
        ttk.Entry(card, textvariable=self.name, width=34).grid(row=r, column=1, sticky="w", pady=3)
        r += 1
        ttk.Label(card, text=tr("Background of the photos")).grid(row=r, column=0, sticky="w", pady=3)
        self.bg_names = {"auto": tr("found by Gerbil"), "light": tr("light (white, grey…)"),
                         "dark": tr("dark (velvet, felt…)")}
        self.bg = tk.StringVar(value=self.bg_names.get(self.pr.get("background"), self.bg_names["auto"]))
        cb = ttk.Combobox(card, textvariable=self.bg, state="readonly", width=24, values=list(self.bg_names.values()))
        cb.grid(row=r, column=1, sticky="w", pady=3)
        Tooltip(cb, tr("Dark: paper labels are discarded, the edge of the objects is placed for a dark background."))
        r += 1
        ttk.Label(card, text=tr("LEARNED SCALES"), style="Section.TLabel").grid(row=r, column=0, columnspan=2,
                                                                           sticky="w", pady=(12, 2))
        r += 1
        ttk.Label(card, style="Muted.TLabel", wraplength=430, justify="left", text=(
            tr("Show Gerbil one photo of each scale used on the site (each physical copy: two prints of "
            "the same model may differ by 1 %). It is then found on the photos where the usual "
            "reading fails."))).grid(row=r, column=0, columnspan=2, sticky="w")
        r += 1
        self.lb = tk.Listbox(card, height=5, activestyle="none", font=(FONT_SERIF, 9), relief="flat",
                             highlightthickness=1, highlightbackground=LAVENDER_LINE, selectbackground=LAVENDER)
        self.lb.grid(row=r, column=0, columnspan=2, sticky="ew", pady=4)
        r += 1
        bar = ttk.Frame(card, style="Card.TFrame")
        bar.grid(row=r, column=0, columnspan=2, sticky="w")
        ttk.Button(bar, text=tr("Learn a scale from a photo…"), command=self.learn).pack(side="left")
        ttk.Button(bar, text=tr("Remove"), style="Small.TButton", command=self.remove_scale).pack(side="left", padx=6)
        r += 1
        self.first = tk.BooleanVar(value=bool(self.pr.get("learned_first")))
        ck = ttk.Checkbutton(card, text=tr("Look for the learned scales first"), variable=self.first)
        ck.grid(row=r, column=0, columnspan=2, sticky="w", pady=(4, 0))
        Tooltip(ck, tr("For a scale the usual reading gets wrong. Otherwise the learned scales are a second "
                    "chance (a learned 10 cm scale is also found inside a 20 cm one of the same make)."))
        r += 1
        ttk.Label(card, text=tr("OPTIONS"), style="Section.TLabel").grid(row=r, column=0, columnspan=2,
                                                                    sticky="w", pady=(12, 2))
        r += 1
        self.opts_lbl = tk.StringVar()
        ttk.Label(card, textvariable=self.opts_lbl, style="Muted.TLabel", wraplength=430, justify="left").grid(
            row=r, column=0, columnspan=2, sticky="w")
        r += 1
        ttk.Button(card, text=tr("Keep the options of the main window"), command=self.take_options).grid(
            row=r, column=0, columnspan=2, sticky="w", pady=(4, 0))
        foot = ttk.Frame(win, style="Window.TFrame", padding=(10, 0, 10, 10))
        foot.pack(fill="x")
        ttk.Button(foot, text=tr("Save"), style="Run.TButton", command=self.save).pack(side="left")
        ttk.Button(foot, text=tr("Put next to the photos…"), command=self.export).pack(side="left", padx=8)
        ttk.Button(foot, text=tr("Close"), command=win.destroy).pack(side="right")
        self.fill()

    def fill(self):
        """List of the learned scales and summary of the options kept."""
        self.lb.delete(0, "end")
        for m in self.pr["scales"]:
            self.lb.insert("end", f"{m.get('name', '')}   ({m.get('cm', 0):g} cm)")
        st = self.pr.get("settings") or {}
        self.opts_lbl.set((tr("Options kept: ") + ", ".join(f"{k}={v}" for k, v in st.items())) if st else
                          tr("No options kept: the main window keeps its own."))

    def learn(self):
        """Chooses a photo showing the scale and opens the scale window in learning mode."""
        path = filedialog.askopenfilename(parent=self.win, title=tr("A photo showing the scale"),
                                          initialdir=self.app.s["last_dir"] or None,
                                          filetypes=[("Photos", " ".join("*" + e for e in sorted(EXTENSIONS))),
                                                     (tr("All files"), "*.*")])
        if path:
            ScaleWindow(self.app, path, learn=lambda entry: self.learned(path, entry))

    def learned(self, path, entry):
        """Learns the scale from the two points given (engine.learn_scale)."""
        try:
            import gerbil as engine
            model = engine.learn_scale(engine.load_photo(path).rgb, entry,
                                       f"{entry['cm']:g} cm ({os.path.basename(path)})")
        except Exception as e:
            messagebox.showerror("Gerbil", T(f"L'échelle n'a pas pu être apprise :\n{e}", f"The scale could not be learned:\n{e}"), parent=self.win)
            return
        self.pr["scales"].append(model)
        self.fill()

    def remove_scale(self):
        """Removes a learned scale."""
        sel = self.lb.curselection()
        if sel:
            del self.pr["scales"][sel[0]]
            self.fill()

    def take_options(self):
        """Keeps the options of the main window in the profile."""
        self.app._collect()
        self.pr["settings"] = {k: self.app.s[k] for k in PROFILE_SETTINGS}
        self.fill()

    def data(self):
        """The profile as saved."""
        pr = dict(self.pr, name=self.name.get().strip(), learned_first=self.first.get(),
                  background={v: k for k, v in self.bg_names.items()}.get(self.bg.get(), "auto"))
        return pr

    def save(self):
        """Saves the profile in the library and chooses it."""
        pr = self.data()
        if not safe_name(pr["name"]):
            messagebox.showwarning("Gerbil", tr("Give the profile a name."), parent=self.win)
            return
        os.makedirs(PROFILES_DIR, exist_ok=True)
        with open(profile_path(safe_name(pr["name"])), "w", encoding="utf-8") as fh:
            json.dump(pr, fh, ensure_ascii=False)
        self.app.profiles_changed(safe_name(pr["name"]))
        self.win.destroy()

    def export(self):
        """Writes the profile as gerbil_profile.json in a folder of photos."""
        folder = filedialog.askdirectory(parent=self.win, title=tr("Folder of photos that use this profile"),
                                         initialdir=self.app.s["last_dir"] or None)
        if folder:
            with open(os.path.join(folder, PROFILE_FILE), "w", encoding="utf-8") as fh:
                json.dump(self.data(), fh, ensure_ascii=False)
            messagebox.showinfo("Gerbil", T(f"Profil enregistré en {PROFILE_FILE} dans\n{folder}\n\n"
                                            "Les photographies de ce dossier l'utilisent, quel que soit le profil choisi.",
                                            f"Profile saved as {PROFILE_FILE} in\n{folder}\n\n"
                                            "The photos of this folder use it, whatever the profile chosen."),
                                parent=self.win)


class IptcWindow:
    """IPTC fields of the batch renaming: for each IPTC Core field, a text where {field} is replaced by
    the value of the photo and {name} by the output name (a text without braces: the same for all, e.g.
    the copyright). Written into the PSD / TIFF, the copy of the original and, if ticked, a .xmp file
    next to each original photo."""

    def __init__(self, project):
        """The IPTC window: one text per IPTC field, sidecar option, example."""
        import gerbil as engine
        self.engine, self.project = engine, project
        pr = project.pr
        self.win = win = tk.Toplevel(project.win)
        win.title(tr("IPTC metadata"))
        win.configure(bg=WINDOW_BG)
        win.transient(project.win)
        card = ttk.Frame(win, style="Card.TFrame", padding=14)
        card.pack(fill="both", expand=True, padx=10, pady=10)
        keys = ", ".join("{" + f["key"] + "}" for f in project.fields())
        ttk.Label(card, style="Muted.TLabel", wraplength=560, justify="left", text=(
            tr("For each field: {name} (output name) or the fields of the photo ") + keys + tr("; a text without "
            "braces is the same for every photo. Keywords and Creator: several values separated by commas. "
            "Empty: not written."))).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        mapping = pr.get("iptc") if isinstance(pr.get("iptc"), dict) else dict(engine.DEFAULT_IPTC)
        self.vars = {}
        for r, (key, (prop, _, label)) in enumerate(engine.IPTC_TARGETS.items(), 1):
            ttk.Label(card, text=label).grid(row=r, column=0, sticky="w", pady=2)
            v = tk.StringVar(value=mapping.get(key, ""))
            v.trace_add("write", lambda *_: self.preview())
            ttk.Entry(card, textvariable=v, width=46).grid(row=r, column=1, sticky="w", padx=8, pady=2)
            ttk.Label(card, text=prop, style="Muted.TLabel").grid(row=r, column=2, sticky="w")
            self.vars[key] = v
        r = len(engine.IPTC_TARGETS) + 1
        self.sidecar = tk.BooleanVar(value=bool(pr.get("xmp_sidecar")))
        ttk.Checkbutton(card, text=tr("Also write a .xmp file next to each original photo (Bridge, Lightroom, "
                                   "darktable; a .xmp of another program is never replaced)"),
                        variable=self.sidecar).grid(row=r, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.example = tk.StringVar()
        ttk.Label(card, textvariable=self.example, style="Muted.TLabel", wraplength=560, justify="left").grid(
            row=r + 1, column=0, columnspan=3, sticky="w", pady=(8, 0))
        foot = ttk.Frame(win, style="Window.TFrame", padding=(10, 0, 10, 10))
        foot.pack(fill="x")
        ttk.Button(foot, text=tr("OK"), style="Run.TButton", command=self.ok).pack(side="left")
        ttk.Button(foot, text=tr("Default model"), command=self.default).pack(side="left", padx=8)
        ttk.Button(foot, text=tr("Cancel"), command=win.destroy).pack(side="right")
        self.preview()

    def mapping(self):
        """The IPTC fields filled in."""
        return {k: v.get().strip() for k, v in self.vars.items() if v.get().strip()}

    def preview(self):
        """Example of the IPTC values of the selected photo."""
        pj = self.project
        sel = pj.tree.selection() or pj.tree.get_children()
        if not sel:
            return
        name = sel[0]
        vals = project_values(pj.pr, name)
        out = self.engine.iptc_values(dict(pj.pr, iptc=self.mapping()), vals, project_output_name(pj.pr, name))
        labels = {k: lab for k, (_, _, lab) in self.engine.IPTC_TARGETS.items()}
        self.example.set(T(f"Exemple ({name}) :  ", f"Example ({name}):  ") + "   /   ".join(
            f"{labels[k]}: {', '.join(v) if isinstance(v, list) else v}" for k, v in out.items()))

    def default(self):
        """Default model."""
        for k, v in self.vars.items():
            v.set(self.engine.DEFAULT_IPTC.get(k, ""))

    def ok(self):
        """Keeps the IPTC settings in the project."""
        self.project.pr["iptc"] = self.mapping()
        self.project.pr["xmp_sidecar"] = self.sidecar.get()
        self.project.changed = True
        self.win.destroy()


class InventoryWindow:
    """Inventory of documentation folders as CSV (gerbil_tools.inventory), with the PowerShell line that
    does the same, shown for learning."""

    def __init__(self, app):
        """The inventory window: folders, kinds of files, fields of the names,
        PowerShell line."""
        import gerbil_tools as tools
        self.tools, self.app = tools, app
        self.win = win = tk.Toplevel(app.root)
        win.title(tr("Inventory (CSV)"))
        win.configure(bg=WINDOW_BG)
        win.transient(app.root)
        card = ttk.Frame(win, style="Card.TFrame", padding=14)
        card.pack(fill="both", expand=True, padx=10, pady=10)
        card.columnconfigure(1, weight=1)
        folders = [p for p in app.tree.get_children() if os.path.isdir(p)] if hasattr(app, "tree") else []
        ttk.Label(card, text=tr("Folders")).grid(row=0, column=0, sticky="nw", pady=2)
        self.folders = tk.Listbox(card, height=4, width=60, relief="flat", highlightthickness=1,
                                  highlightbackground=LAVENDER_LINE)
        self.folders.grid(row=0, column=1, sticky="ew", padx=8)
        for f in folders:
            self.folders.insert("end", f)
        fb = ttk.Frame(card, style="Card.TFrame")
        fb.grid(row=1, column=1, sticky="w", padx=8, pady=(2, 8))
        ttk.Button(fb, text=tr("Add folder…"), style="Small.TButton", command=self.add).pack(side="left")
        ttk.Button(fb, text=tr("Remove"), style="Small.TButton",
                   command=lambda: [self.folders.delete(i) for i in reversed(self.folders.curselection())] and
                   self.update_line()).pack(side="left", padx=4)
        self.kinds = {}
        kf = ttk.Frame(card, style="Card.TFrame")
        ttk.Label(card, text=tr("Files")).grid(row=2, column=0, sticky="w")
        kf.grid(row=2, column=1, sticky="w", padx=8)
        for k, label in (("photos", "photos"), ("drawings", "drawings (.ai, .svg, .pdf, .eps)"), ("3d", "3D models")):
            self.kinds[k] = tk.BooleanVar(value=True)
            ttk.Checkbutton(kf, text=tr(label), variable=self.kinds[k], command=self.update_line).pack(side="left",
                                                                                                    padx=(0, 10))
        ttk.Label(card, text=tr("Fields of the names")).grid(row=3, column=0, sticky="w", pady=(8, 0))
        template = ""
        for f in folders:
            pr = load_project_file(f)
            if pr and pr.get("template"):
                template = pr["template"]
                break
        self.template = tk.StringVar(value=template)
        self.template.trace_add("write", lambda *_: self.update_line())
        e = ttk.Entry(card, textvariable=self.template, width=50)
        e.grid(row=3, column=1, sticky="w", padx=8, pady=(8, 0))
        Tooltip(e, tr("How the names are made, e.g. {site}_{sector}_US{us}_{number}_{material}: each {field} "
                   "becomes a column. Gerbil's suffixes (_outlined, _to_be_verified…) are left out."))
        self.sub = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text=tr("Sub-folders too"), variable=self.sub, command=self.update_line).grid(
            row=4, column=1, sticky="w", padx=8, pady=(6, 0))
        self.img = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text=tr("Image information (size in px, resolution, date taken, camera)"),
                        variable=self.img).grid(row=5, column=1, sticky="w", padx=8)
        ttk.Label(card, text=tr("POWERSHELL"), style="Section.TLabel").grid(row=6, column=0, columnspan=2, sticky="w",
                                                                       pady=(12, 2))
        ttk.Label(card, style="Muted.TLabel", wraplength=560, justify="left", text=(
            tr("The same inventory with Windows only (without the image information): paste this line into "
            "PowerShell."))).grid(row=7, column=0, columnspan=2, sticky="w")
        self.line = tk.Text(card, height=6, width=80, wrap="char", font=(FONT_MONO, 9), relief="flat",
                            highlightthickness=1, highlightbackground=LAVENDER_LINE)
        self.line.grid(row=8, column=0, columnspan=2, sticky="ew", pady=4)
        ttk.Button(card, text=tr("Copy the line"), style="Small.TButton",
                   command=lambda: (win.clipboard_clear(), win.clipboard_append(self.line.get("1.0", "end").strip()))
                   ).grid(row=9, column=0, sticky="w")
        foot = ttk.Frame(win, style="Window.TFrame", padding=(10, 0, 10, 10))
        foot.pack(fill="x")
        ttk.Button(foot, text=tr("Write the inventory…"), style="Run.TButton", command=self.write).pack(side="left")
        self.msg = tk.StringVar()
        ttk.Label(foot, textvariable=self.msg, style="Footer.TLabel").pack(side="left", padx=10)
        ttk.Button(foot, text=tr("Close"), command=win.destroy).pack(side="right")
        self.update_line()

    def add(self):
        """Adds a folder."""
        d = filedialog.askdirectory(parent=self.win, initialdir=self.app.s["last_dir"] or None)
        if d:
            self.folders.insert("end", os.path.normpath(d))
            self.update_line()

    def chosen(self):
        """Folders and kinds of files chosen."""
        return list(self.folders.get(0, "end")), [k for k, v in self.kinds.items() if v.get()]

    def out_path(self):
        """Default path of the CSV."""
        folders, _ = self.chosen()
        return os.path.join(folders[0], "inventory.csv") if folders else "inventory.csv"

    def update_line(self):
        """PowerShell line updated."""
        folders, kinds = self.chosen()
        self.line.delete("1.0", "end")
        if folders and kinds:
            self.line.insert("1.0", self.tools.powershell_line(folders, self.out_path(), kinds, self.template.get(),
                                                               self.sub.get()))

    def write(self):
        """Writes the inventory and opens it."""
        folders, kinds = self.chosen()
        if not folders or not kinds:
            self.msg.set(tr("Add a folder and tick a kind of file."))
            return
        out = filedialog.asksaveasfilename(parent=self.win, title=tr("Inventory"), defaultextension=".csv",
                                           initialdir=folders[0], initialfile="inventory.csv",
                                           filetypes=[("CSV", "*.csv")])
        if not out:
            return
        try:
            n, cols = self.tools.inventory(folders, out, kinds, self.template.get(), self.img.get(), self.sub.get())
        except (OSError, re.error) as e:
            self.msg.set(T("Non écrit : ", "Not written: ") + str(e))
            return
        self.msg.set(T(f"{n} fichier(s), {len(cols)} colonnes : ", f"{n} file(s), {len(cols)} columns: ") + os.path.basename(out))
        os.startfile(out)


class ThumbnailsWindow:
    """Thumbnails in batch (gerbil_tools.thumbnails) for databases."""

    def __init__(self, app):
        """The thumbnails window: folder, size, format."""
        import gerbil_tools as tools
        self.tools, self.app = tools, app
        self.win = win = tk.Toplevel(app.root)
        win.title(tr("Thumbnails"))
        win.configure(bg=WINDOW_BG)
        win.transient(app.root)
        card = ttk.Frame(win, style="Card.TFrame", padding=14)
        card.pack(fill="both", expand=True, padx=10, pady=10)
        folders = [d for d in getattr(app, "results", []) if os.path.isdir(d)]
        self.folder = tk.StringVar(value=folders[0] if folders else "")
        ttk.Label(card, text=tr("Folder")).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(card, textvariable=self.folder, width=50).grid(row=0, column=1, sticky="w", padx=8)
        ttk.Button(card, text=tr("Browse…"), style="Small.TButton", command=self.browse).grid(row=0, column=2)
        self.only = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text=tr("Only the outlined objects (_outlined.tif), their transparent margin cut off"),
                        variable=self.only).grid(row=1, column=1, columnspan=2, sticky="w", padx=8, pady=3)
        ttk.Label(card, text=tr("Size (px, longest side)")).grid(row=2, column=0, sticky="w", pady=3)
        self.size = tk.StringVar(value="512")
        ttk.Combobox(card, textvariable=self.size, values=["128", "256", "512", "1024"], width=7).grid(
            row=2, column=1, sticky="w", padx=8)
        ttk.Label(card, text=tr("Format")).grid(row=3, column=0, sticky="w", pady=3)
        self.fmt = tk.StringVar(value="png")
        ff = ttk.Frame(card, style="Card.TFrame")
        ff.grid(row=3, column=1, sticky="w", padx=8)
        ttk.Radiobutton(ff, text=tr("PNG (transparent)"), value="png", variable=self.fmt).pack(side="left")
        ttk.Radiobutton(ff, text=tr("JPEG (white background, lighter)"), value="jpg", variable=self.fmt).pack(
            side="left", padx=10)
        ttk.Label(card, text=tr("Written in a 'thumbnails' folder inside the chosen folder, as NAME_thumb.png / .jpg."),
                  style="Muted.TLabel").grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))
        foot = ttk.Frame(win, style="Window.TFrame", padding=(10, 0, 10, 10))
        foot.pack(fill="x")
        ttk.Button(foot, text=tr("Make the thumbnails"), style="Run.TButton", command=self.run).pack(side="left")
        self.msg = tk.StringVar()
        ttk.Label(foot, textvariable=self.msg, style="Footer.TLabel").pack(side="left", padx=10)
        ttk.Button(foot, text=tr("Close"), command=win.destroy).pack(side="right")

    def browse(self):
        """Chooses the folder."""
        d = filedialog.askdirectory(parent=self.win, initialdir=self.folder.get() or self.app.s["last_dir"] or None)
        if d:
            self.folder.set(os.path.normpath(d))

    def run(self):
        """Makes the thumbnails in a thread."""
        folder = self.folder.get().strip()
        try:
            size = max(16, int(self.size.get()))
        except ValueError:
            self.msg.set(tr("The size is a number of pixels."))
            return
        if not os.path.isdir(folder):
            self.msg.set(tr("Choose a folder."))
            return
        self.msg.set(tr("Working…"))

        def work():
            files = self.tools.thumbnails([folder], None, size, self.fmt.get(), self.only.get(),
                                          progress=lambda i, n: self.win.after(0, self.msg.set, f"{i} / {n}…"))
            self.win.after(0, self.done, folder, len(files))
        threading.Thread(target=work, daemon=True).start()

    def done(self, folder, n):
        """Thumbnails made: message, folder opened."""
        self.msg.set(f"{n} thumbnail(s) written.")
        if n:
            os.startfile(os.path.join(folder, "thumbnails"))


class Mire(tk.Canvas):
    """Progress bar drawn as an archaeological scale: two rows of squares, inked as the photos are done.
    Answers like a ttk.Progressbar: configure(maximum=, value=, mode=), ["mode"], start(), stop()."""
    SQUARES = 20

    def __init__(self, parent, bg):
        """An empty scale (the canvas takes the width it is given)."""
        self.k = parent.winfo_fpixels("1i") / 96.0
        super().__init__(parent, height=int(14 * self.k), bg=bg, highlightthickness=0)
        self._state = {"maximum": 1, "value": 0, "mode": "determinate"}
        self._job, self._phase = None, 0
        self.bind("<Configure>", lambda _: self._draw())

    def configure(self, cnf=None, **kw):
        """maximum, value and mode are the bar's own; the rest goes to the canvas."""
        for k in ("maximum", "value", "mode"):
            if k in kw:
                self._state[k] = kw.pop(k)
        if cnf or kw:
            super().configure(cnf, **kw)
        self._draw()

    config = configure

    def __getitem__(self, key):
        return self._state[key] if key in self._state else super().__getitem__(key)

    def start(self, interval=15):
        """Moving scale while the length of the work is unknown (installation)."""
        self.stop()
        self._state["mode"] = "indeterminate"

        def tick():
            self._phase = (self._phase + 1) % self.SQUARES
            self._draw()
            self._job = self.after(max(60, interval * 6), tick)
        tick()

    def stop(self):
        """Stops the moving scale."""
        if self._job:
            self.after_cancel(self._job)
            self._job = None

    def _draw(self):
        """The squares: inked (violet / white) up to the value, light (white / lilac) beyond."""
        self.delete("all")
        w = self.winfo_width()
        if w < 40:
            return
        n, top, h = self.SQUARES, int(2 * self.k), max(4, int(5 * self.k))
        sq = (w - 2) / n
        st = self._state
        done = round(n * min(1.0, float(st["value"]) / max(float(st["maximum"]), 1e-9)))
        for row in (0, 1):
            for i in range(n):
                ink = (i % 2 == 0) == (row == 0)
                on = (abs(i - self._phase) <= 2) if st["mode"] == "indeterminate" else i < done
                colour = (VIOLET if ink else "#FFFFFF") if on else ("#FFFFFF" if ink else LILAS)
                x0 = 1 + i * sq
                self.create_rectangle(x0, top + row * h, x0 + sq, top + (row + 1) * h, fill=colour, width=0)
        self.create_rectangle(1, top, w - 1, top + 2 * h, outline=VIOLET, width=1)


class App:
    """The main window: a column of five steps (source photographs, naming and metadata, processing,
    review, publication) and the page of the step chosen; it starts the engine and opens the other
    windows (batch renaming, scale, review, plates, profiles, tools)."""
    def __init__(self, root, paths=(), selftest=None):
        """The main window: settings, fonts, styles, widgets, checks of the packages."""
        global LANG
        self.root = root
        self.selftest = selftest
        # self-test: default settings, results in the given folder, the user's settings untouched
        self.s = load_settings() if not selftest else dict(
            DEFAULTS, output_mode="other", output_dir=selftest, psd=False, open=False)
        LANG = self.s.get("lang") or system_lang()
        self.proc = None
        self.lines = queue.Queue()
        self.results = []
        self.counts = {}
        self.total = 0
        self.rows = []                      # results of the last run: (photo, status, scale, todo, path)
        self.index, self.no_scale = {}, []
        self.page = 0
        root.title("Gerbil")
        root.configure(bg=PAPER)
        load_fonts(root)
        self.k = root.winfo_fpixels("1i") / 96.0           # screen scaling: pixel sizes follow it
        self._icon()
        self._style()
        self._build()
        self.add_paths(paths)
        self.kind = "script"
        self.check_packages()
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        scale = root.winfo_fpixels("1i") / 96.0
        w, h = min(int(1280 * scale), int(sw * 0.95)), min(int(800 * scale), int(sh * 0.9))
        root.geometry(f"{w}x{h}+{max(0, (sw - w) // 2)}+{max(0, (sh - h) // 3)}")
        root.minsize(min(int(1020 * scale), w), min(int(640 * scale), h))
        root.protocol("WM_DELETE_WINDOW", self.close)
        if selftest:
            root.iconify()                                  # stays in the taskbar
            root.after(500, self.run)

    # ---------------------------------------------------------------- look
    def _icon(self):
        """The gerbil with its camera: window icon, and picture of the column of steps."""
        self.gerbil = None
        try:
            self.root.iconbitmap(default=os.path.join(ICONS, "gerbil.ico"))
            scale = self.root.winfo_fpixels("1i") / 96.0
            size = 64 if scale < 1.25 else 96 if scale < 1.75 else 128
            self.gerbil = tk.PhotoImage(file=os.path.join(ICONS, f"gerbil_{size}.png"))
        except (tk.TclError, OSError):
            img = tk.PhotoImage(width=32, height=32)            # icons folder missing: colour stripes
            for x0, colour in ((0, VIOLET), (11, TEAL), (22, TERRA)):
                img.put(colour, to=(x0, 0, x0 + 10, 32))
            self.root.iconphoto(True, img)
            self._icon_img = img

    def _style(self):
        """Colours and fonts of the widgets (ttk styles), shared by every window."""
        st = ttk.Style(self.root)
        st.theme_use("clam")
        st.configure(".", background=CARD_BG, foreground=TEXT, font=(FONT_SERIF, 10), bordercolor=LINE,
                     lightcolor=CARD_BG, darkcolor=CARD_BG, focuscolor=LILAS)
        st.configure("Window.TFrame", background=WINDOW_BG)
        st.configure("Card.TFrame", background=CARD_BG)
        st.configure("Card.TLabelframe", background=CARD_BG, bordercolor=LINE, relief="solid")
        st.configure("Card.TLabelframe.Label", background=CARD_BG, foreground=VIOLET, font=(FONT_DISPLAY, 14, "bold"))
        st.configure("Section.TLabel", background=CARD_BG, foreground=MUTED, font=(FONT_MONO, 9, "bold"))
        st.configure("Muted.TLabel", background=CARD_BG, foreground=MUTED, font=(FONT_SERIF, 9))
        st.configure("Status.TLabel", background=CARD_BG, foreground=VIOLET, font=(FONT_MONO, 10, "bold"))
        st.configure("Footer.TLabel", background=WINDOW_BG, foreground=MUTED, font=(FONT_SERIF, 9))
        for name, bg, hover, fg, border in (("TButton", "#FFFFFF", LILAS_PALE, VIOLET, VIOLET),
                                            ("Run.TButton", VIOLET, VIOLET_2, "#FFFFFF", VIOLET),
                                            ("Cancel.TButton", "#FFFFFF", "#FBEFE9", TERRA, TERRA),
                                            ("Teal.TButton", "#FFFFFF", "#E6F0EF", TEAL, TEAL)):
            st.configure(name, background=bg, foreground=fg, borderwidth=1, padding=(12, 5),
                         bordercolor=border, lightcolor=bg, darkcolor=bg, font=(FONT_SERIF, 10, "bold"))
            st.map(name, background=[("disabled", "#F1F0F3"), ("pressed", hover), ("active", hover)],
                   foreground=[("disabled", "#A9A5B4")], bordercolor=[("disabled", LINE)],
                   lightcolor=[("active", hover)], darkcolor=[("active", hover)])
        st.configure("Run.TButton", font=(FONT_SERIF, 11, "bold"), padding=(24, 7))
        st.configure("Small.TButton", font=(FONT_SERIF, 9), padding=(6, 1))
        st.configure("Cancel.TButton", padding=(14, 7))
        st.configure("Teal.TButton", padding=(14, 7))
        st.configure("Link.TButton", background=CARD_BG, foreground=VIOLET_2, borderwidth=0, padding=(0, 2),
                     bordercolor=CARD_BG, lightcolor=CARD_BG, darkcolor=CARD_BG, font=(FONT_SERIF, 10, "bold"))
        st.map("Link.TButton", background=[("active", CARD_BG)], foreground=[("active", VIOLET)])
        for w in ("TCheckbutton", "TRadiobutton"):
            st.configure(w, background=CARD_BG, foreground=TEXT, indicatorbackground="white",
                         indicatorforeground=VIOLET_2, upperbordercolor=VIOLET, lowerbordercolor=VIOLET,
                         indicatormargin=(0, 0, 6, 0))
            st.map(w, background=[("active", CARD_BG)],
                   indicatorbackground=[("selected", LILAS_PALE), ("disabled", "#F2F1F5")],
                   foreground=[("disabled", "#A9A5B4")])
        st.configure("TCombobox", fieldbackground="white", background=LILAS_PALE, arrowcolor=VIOLET,
                     bordercolor=LINE, padding=3)
        st.map("TCombobox", fieldbackground=[("readonly", "white"), ("disabled", "#F2F1F5")],
               foreground=[("disabled", "#A9A5B4")])
        self.root.option_add("*TCombobox*Listbox.font", (FONT_SERIF, 10))
        st.configure("TSpinbox", fieldbackground="white", background=LILAS_PALE, arrowcolor=VIOLET,
                     bordercolor=LINE, padding=3)
        st.configure("TEntry", fieldbackground="white", bordercolor=LINE, padding=4)
        st.map("TEntry", fieldbackground=[("disabled", "#F2F1F5")])
        st.configure("Treeview", background="white", fieldbackground="white",
                     rowheight=int(27 * self.root.winfo_fpixels("1i") / 96.0),
                     bordercolor=LINE, font=(FONT_SERIF, 10))
        st.configure("Treeview.Heading", background="white", foreground=MUTED, font=(FONT_MONO, 9, "bold"),
                     relief="flat", padding=(6, 5), bordercolor=VIOLET)
        st.map("Treeview", background=[("selected", LILAS)], foreground=[("selected", VIOLET)])
        st.configure("Lav.Horizontal.TProgressbar", troughcolor=LILAS_PALE, background=VIOLET_2,
                     bordercolor=LILAS_PALE, lightcolor=VIOLET_2, darkcolor=VIOLET_2, thickness=10)

    # ---------------------------------------------------------------- layout
    def _build(self):
        """The column of steps on the left, the page of the step on the squared paper."""
        root = self.root
        self.rail = tk.Frame(root, bg=VIOLET, width=int(290 * self.k))
        self.rail.pack(side="left", fill="y")
        self.rail.pack_propagate(False)
        self._rail()
        right = tk.Frame(root, bg=PAPER)
        right.pack(side="left", fill="both", expand=True)

        # banner shown while required Python packages are missing
        self.banner_anchor = tk.Frame(right, bg=PAPER, height=0)
        self.banner_anchor.pack(fill="x")
        self.banner = tk.Frame(right, bg="#FBEFE9")
        self.banner_text = tk.Label(self.banner, bg="#FBEFE9", fg="#3D2017", font=(FONT_SERIF, 10),
                                    justify="left", anchor="w")
        self.banner_text.pack(side="left", padx=18, pady=10, fill="x", expand=True)
        self.install_btn = ttk.Button(self.banner, text=T("Installer maintenant", "Install now"),
                                      style="Cancel.TButton", command=self.install_required)
        self.install_btn.pack(side="right", padx=18, pady=8)

        self.canvas = tk.Canvas(right, bg=PAPER, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _: self._layout())
        self.status = tk.StringVar(value=T("Ajoutez des dossiers ou des photographies.", "Add folders or photos."))
        self.pages = []
        self._page_sources()
        self._page_naming()
        self._page_processing()
        self._page_review()
        self._page_publication()
        for r in self.rows:
            self._add_row(*r)
        self.show_page(self.page)

    def _rail(self):
        """The column of steps: the gerbil, the name, the five steps, the credits and the languages."""
        rail = self.rail
        brand = tk.Frame(rail, bg=VIOLET)
        brand.pack(fill="x", padx=18, pady=(20, 14))
        if self.gerbil is not None:
            tk.Label(brand, image=self.gerbil, bg=VIOLET).pack(side="left")
        names = tk.Frame(brand, bg=VIOLET)
        names.pack(side="left", padx=(12, 0))
        tk.Label(names, text="GERBIL", bg=VIOLET, fg="#EDE8F7", font=(FONT_DISPLAY, 24, "bold")).pack(anchor="w")
        tk.Label(names, text=T("Gestionnaire de photographies\narchéologiques", "Archaeological\nphotography manager"),
                 bg=VIOLET, fg="#D9D2EC", font=(FONT_DISPLAY, 11, "bold"), justify="left").pack(anchor="w")
        tk.Frame(rail, bg="#4A3A72", height=1).pack(fill="x")
        self.step_widgets, self.step_sub = [], []
        for i, (fr, en) in enumerate(STEPS):
            row = tk.Frame(rail, bg=VIOLET, cursor="hand2")
            row.pack(fill="x", pady=(10 if i == 0 else 0, 0))
            stripe = tk.Canvas(row, width=max(4, int(4 * self.k)), height=1, bg=VIOLET, highlightthickness=0)
            stripe.pack(side="left", fill="y")
            n = tk.Label(row, text=f"0{i + 1}", bg=VIOLET, fg=LILAS_2, font=(FONT_MONO, 11, "bold"))
            n.pack(side="left", anchor="n", padx=(14, 10), pady=(10, 0))
            texts = tk.Frame(row, bg=VIOLET)
            texts.pack(side="left", fill="x", expand=True, pady=8)
            head = tk.Frame(texts, bg=VIOLET)
            head.pack(anchor="w")
            title = tk.Label(head, text=T(fr, en), bg=VIOLET, fg="#EDE8F7", font=(FONT_SERIF, 11, "bold"))
            title.pack(side="left")
            badge = tk.Label(head, text="", bg=TERRA, fg="white", font=(FONT_MONO, 8, "bold"), padx=5)
            sub = tk.StringVar(value="")
            subl = tk.Label(texts, textvariable=sub, bg=VIOLET, fg="#C9C1DE", font=(FONT_SERIF, 9),
                            justify="left", wraplength=int(200 * self.k), anchor="w")
            subl.pack(anchor="w")
            parts = (row, stripe, n, texts, head, title, subl)
            for w in parts:
                w.bind("<Button-1>", lambda _, k=i: self.show_page(k))
            self.step_widgets.append({"parts": parts, "stripe": stripe, "n": n, "title": title, "sub": subl,
                                      "badge": badge})
            self.step_sub.append(sub)
        foot = tk.Frame(rail, bg=VIOLET)
        foot.pack(side="bottom", fill="x", padx=18, pady=14)
        langs = tk.Frame(foot, bg=VIOLET)
        langs.pack(anchor="w", pady=(0, 8))
        for code in ("fr", "en"):
            b = tk.Label(langs, text=code.upper(), bg=VIOLET, cursor="hand2",
                         fg="#FFFFFF" if LANG == code else "#9C92BD", font=(FONT_MONO, 10, "bold"))
            b.pack(side="left", padx=(0, 10))
            b.bind("<Button-1>", lambda _, c=code: self.set_lang(c))
        h = tk.Label(langs, text=T("Aide", "Help"), bg=VIOLET, fg="#D9D2EC", cursor="hand2", font=(FONT_SERIF, 10, "underline"))
        h.pack(side="left", padx=(6, 0))
        h.bind("<Button-1>", lambda _: self.help())
        tk.Label(foot, text=T("version", "version") + f" {VERSION}, " + T("licence GPL v3", "GPL v3 licence"),
                 bg=VIOLET, fg="#B9B0D3", font=(FONT_SERIF, 9)).pack(anchor="w")
        tk.Label(foot, text="© 2026 Eloïs Charbonnel", bg=VIOLET, fg="#B9B0D3", font=(FONT_SERIF, 9)).pack(anchor="w")
        tk.Label(foot, text="ITINERA", bg=VIOLET, fg="#EDE8F7", font=(FONT_DISPLAY, 12, "bold")).pack(anchor="w")

    def show_page(self, i):
        """Shows the page of step i and marks the step in the column."""
        self.page = i
        for k, w in enumerate(self.step_widgets):
            on = k == i
            bg = PAPER if on else VIOLET
            for part in w["parts"]:
                part.configure(bg=bg)
            w["title"].configure(fg=VIOLET if on else "#EDE8F7")
            w["n"].configure(fg=VIOLET if on else LILAS_2)
            w["sub"].configure(fg=MUTED if on else "#C9C1DE")
            s = w["stripe"]
            s.delete("all")
            if on:
                s.update_idletasks()
                u = max(7, int(7 * self.k))
                for y in range(0, max(60, s.winfo_height()), 2 * u):
                    s.create_rectangle(0, y, int(s["width"]), y + u, fill=VIOLET_2, width=0)
        for k, p in enumerate(self.pages):
            for item in p["items"]:
                self.canvas.itemconfigure(item, state="normal" if k == i else "hidden")
        if i == 1:
            self._naming_summary()
        self._layout()

    def _card(self):
        """A white card with a thin border, on the squared paper."""
        return tk.Frame(self.canvas, bg=CARD_BG, highlightthickness=1, highlightbackground=LINE, padx=16, pady=14)

    def _section(self, parent, text, top=0):
        """A small heading in typewriter capitals."""
        lbl = tk.Label(parent, text=text.upper(), bg=CARD_BG, fg=MUTED, font=(FONT_MONO, 9, "bold"), anchor="w")
        lbl.pack(fill="x", pady=(top, 4))
        return lbl

    def _text(self, parent, text, wrap=310, muted=True, top=0):
        lbl = tk.Label(parent, text=text, bg=CARD_BG, fg=MUTED if muted else TEXT, font=(FONT_SERIF, 10),
                       justify="left", anchor="w", wraplength=int(wrap * self.k))
        lbl.pack(fill="x", pady=(top, 0))
        return lbl

    def _page(self, kicker, title, desc, left=None, right=None, actions=(), hint=None):
        """A page: its heading drawn on the paper, its cards and its action buttons."""
        c = self.canvas
        p = {"left": left, "right": right, "actions": list(actions), "items": []}
        p["kicker"] = c.create_text(0, 0, text=kicker.upper(), anchor="nw", fill=TEAL, font=(FONT_MONO, 9, "bold"))
        p["title"] = c.create_text(0, 0, text=title, anchor="nw", fill=VIOLET, font=(FONT_DISPLAY, 24, "bold"))
        p["desc"] = c.create_text(0, 0, text=desc, anchor="nw", fill=MUTED, font=(FONT_SERIF, 10))
        p["items"] += [p["kicker"], p["title"], p["desc"]]
        for key in ("left", "right"):
            if p[key] is not None:
                p[key + "_win"] = c.create_window(0, 0, window=p[key], anchor="nw")
                p["items"].append(p[key + "_win"])
        p["action_wins"] = [c.create_window(0, 0, window=w, anchor="nw") for w in p["actions"]]
        p["items"] += p["action_wins"]
        p["hint"] = c.create_text(0, 0, text="", anchor="e", fill=MUTED, font=(FONT_SERIF, 10, "italic"))
        p["items"].append(p["hint"])
        p["hint_var"] = hint
        if hint is not None:
            hint.trace_add("write", lambda *_: c.itemconfigure(p["hint"], text=hint.get()))
            c.itemconfigure(p["hint"], text=hint.get())
        self.pages.append(p)
        return p

    def _layout(self):
        """Squared paper and the page shown, fitted to the size of the window."""
        c = self.canvas
        W, H = c.winfo_width(), c.winfo_height()
        if W < 50 or not self.pages:
            return
        c.delete("grid")
        for x in range(0, W, 10):
            c.create_line(x, 0, x, H, fill=GRID_2 if x % 50 == 0 else GRID, tags="grid")
        for y in range(0, H, 10):
            c.create_line(0, y, W, y, fill=GRID_2 if y % 50 == 0 else GRID, tags="grid")
        c.tag_lower("grid")
        p = self.pages[self.page]
        k = self.k
        m = int(28 * k)
        c.coords(p["kicker"], m, int(20 * k))
        c.coords(p["title"], m, (c.bbox(p["kicker"]) or (0, 0, 0, 40))[3] + int(4 * k))
        c.coords(p["desc"], m, (c.bbox(p["title"]) or (0, 0, 0, 80))[3] + int(2 * k))
        c.itemconfigure(p["desc"], width=W - 2 * m)
        top = (c.bbox(p["desc"]) or (0, 0, 0, 104))[3] + int(16 * k)
        x = m
        bh = max([w.winfo_reqheight() for w in p["actions"]] or [0])
        ya = H - int(18 * k) - bh
        for w, win in zip(p["actions"], p["action_wins"]):
            c.coords(win, x, ya + (bh - w.winfo_reqheight()) // 2)
            x += w.winfo_reqwidth() + int(10 * k)
        c.coords(p["hint"], W - m, ya + bh // 2)
        bottom = ya - int(14 * k) if p["actions"] else H - int(18 * k)
        rw = int(370 * k) if p["right"] is not None else 0
        if p["left"] is not None:
            c.coords(p["left_win"], m, top)
            c.itemconfigure(p["left_win"], width=W - 2 * m - (rw + int(18 * k) if rw else 0), height=bottom - top)
        if p["right"] is not None:
            c.coords(p["right_win"], W - m - rw, top)
            c.itemconfigure(p["right_win"], width=rw, height=bottom - top)

    # ---------------------------------------------------------------- pages
    def _page_sources(self):
        """01: folders and photos to process, and the site profile."""
        left = self._card()
        bar = tk.Frame(left, bg=CARD_BG)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Button(bar, text=T("Ajouter un dossier…", "Add folder…"), command=self.add_folder).pack(side="left")
        ttk.Button(bar, text=T("Ajouter des photographies…", "Add photos…"), command=self.add_files).pack(side="left", padx=8)
        ttk.Button(bar, text=T("Vider", "Clear"), command=self.clear).pack(side="right")
        ttk.Button(bar, text=T("Retirer", "Remove"), command=self.remove).pack(side="right", padx=8)
        tf = tk.Frame(left, bg=CARD_BG)
        tf.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(tf, columns=("name", "photos", "where"), show="headings", selectmode="extended")
        for col, title, width, anchor, stretch in (("name", T("DOSSIER OU PHOTOGRAPHIE", "FOLDER OR PHOTO"), 240, "w", True),
                                                   ("photos", T("NOMBRE", "COUNT"), 80, "center", False),
                                                   ("where", T("EMPLACEMENT", "LOCATION"), 260, "w", True)):
            self.tree.heading(col, text=title, anchor=anchor)
            self.tree.column(col, width=int(width * self.k), minwidth=60, anchor=anchor, stretch=stretch)
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<Delete>", lambda _: self.remove())
        self.total_lbl = tk.Label(left, text="", bg=CARD_BG, fg=MUTED, font=(FONT_SERIF, 10), anchor="w")
        self.total_lbl.pack(fill="x", pady=(8, 0))

        right = self._card()
        self._section(right, T("Profil de site", "Site profile"))
        prow = tk.Frame(right, bg=CARD_BG)
        prow.pack(fill="x")
        none = T("(aucun)", "(none)")
        self.profile = tk.StringVar(value=self.s.get("profile") if self.s.get("profile") in profile_names() else none)
        self.profile_cb = ttk.Combobox(prow, textvariable=self.profile, state="readonly", width=24,
                                       values=[none] + profile_names())
        self.profile_cb.pack(side="left")
        self.profile_cb.bind("<<ComboboxSelected>>", lambda _: self.apply_profile())
        tools = tk.Frame(right, bg=CARD_BG)
        tools.pack(fill="x", pady=(6, 0))
        ttk.Button(tools, text=T("Modifier…", "Edit…"), style="Small.TButton",
                   command=lambda: ProfileWindow(self, None if self.profile.get() == none else self.profile.get())
                   ).pack(side="left")
        ttk.Button(tools, text=T("Nouveau…", "New…"), style="Small.TButton",
                   command=lambda: ProfileWindow(self)).pack(side="left", padx=6)
        self._text(right, T("Ce que l'on sait des photographies d'un site : le fond, les échelles apprises, "
                            "les réglages. Un fichier gerbil_profile.json posé à côté des photographies "
                            "s'applique à elles dans tous les cas.",
                            "What is known of the photos of a site: background, learned scales, settings. "
                            "A gerbil_profile.json placed next to the photos applies to them in any case."), top=10)
        self._section(right, T("Astuce", "Tip"), top=18)
        self._text(right, T("On peut aussi déposer des dossiers sur l'icône de Gerbil pour les ajouter.",
                            "Folders can also be dropped on the Gerbil icon to add them."))
        nxt = ttk.Button(self.canvas, text=T("Continuer", "Continue"), style="Run.TButton",
                         command=lambda: self.show_page(1))
        self.sources_hint = tk.StringVar(value="")
        self._page(T("Étape 01", "Step 01"), T("Photographies sources", "Source photographs"),
                   T("Les dossiers ou les photographies à traiter : JPEG, TIFF, PNG ou RAW, avec une échelle "
                     "dans le plan de l'objet. Les photographies ne sont jamais modifiées.",
                     "The folders or photos to process: JPEG, TIFF, PNG or RAW, with a scale in the plane of "
                     "the object. The photos are never changed."),
                   left, right, [nxt], self.sources_hint)

    def _page_naming(self):
        """02: names of the output files and information of the photos (batch renaming)."""
        left = self._card()
        self._section(left, T("Projet du dossier", "Project of the folder"))
        self.naming_var = tk.StringVar(value="")
        summary = tk.Label(left, textvariable=self.naming_var, bg=CARD_BG, fg=TEXT, font=(FONT_SERIF, 11),
                           justify="left", anchor="nw", wraplength=int(600 * self.k))
        summary.pack(fill="x")
        left.bind("<Configure>", lambda e: summary.configure(wraplength=max(200, e.width - int(40 * self.k))))
        self.naming_example = tk.StringVar(value="")
        tk.Label(left, textvariable=self.naming_example, bg=CARD_BG, fg=VIOLET, font=(FONT_MONO, 11),
                 justify="left", anchor="w").pack(fill="x", pady=(10, 0))
        b = tk.Frame(left, bg=CARD_BG)
        b.pack(fill="x", pady=(16, 0))
        ttk.Button(b, text=T("Ouvrir le renommage en lot…", "Open the batch renaming…"), style="Run.TButton",
                   command=self.project).pack(side="left")
        ttk.Button(b, text=T("Actualiser", "Refresh"), command=self._naming_summary).pack(side="left", padx=10)

        right = self._card()
        self._section(right, T("À quoi ça sert", "What it is for"))
        self._text(right, T("Des champs (site, US, numéro, matière…) et un modèle de nom, par exemple "
                            "{site}_US{us}_{number} : les fichiers produits prennent ce nom, et les informations "
                            "sont écrites dans les fichiers (XMP, IPTC) et dans le rapport.",
                            "Fields (site, US, number, material…) and a name template, e.g. {site}_US{us}_{number}: "
                            "the output files take this name, and the information is written into the files "
                            "(XMP, IPTC) and the report."))
        self._section(right, T("Bon à savoir", "Good to know"), top=16)
        self._text(right, T("Les photographies originales ne sont jamais renommées. Tout est enregistré dans "
                            "gerbil_project.json, à côté des photographies.",
                            "The original photos are never renamed. Everything is saved in gerbil_project.json, "
                            "next to the photos."))
        nxt = ttk.Button(self.canvas, text=T("Continuer", "Continue"), style="Run.TButton",
                         command=lambda: self.show_page(2))
        self._page(T("Étape 02", "Step 02"), T("Nommage et métadonnées", "Naming and metadata"),
                   T("Facultatif : nommer les fichiers produits d'après l'inventaire, et y inscrire les "
                     "informations des objets.",
                     "Optional: name the output files after the inventory, and write the information of "
                     "the objects into them."),
                   left, right, [nxt], tk.StringVar(value=T("Étape facultative", "Optional step")))

    def _page_processing(self):
        """03: settings, Run, progress on the scale bar, table of the results."""
        left = self._card()
        prog = tk.Frame(left, bg=CARD_BG)
        prog.pack(fill="x", pady=(0, 10))
        self.bar = Mire(prog, CARD_BG)
        self.bar.pack(side="left", fill="x", expand=True)
        tk.Label(prog, textvariable=self.status, bg=CARD_BG, fg=VIOLET, font=(FONT_MONO, 10, "bold")).pack(
            side="left", padx=(14, 0))
        tf = tk.Frame(left, bg=CARD_BG)
        tf.pack(fill="both", expand=True)
        self.table = ttk.Treeview(tf, columns=("photo", "state", "scale", "todo"), show="headings", selectmode="browse")
        for col, title, width, stretch in (("photo", T("PHOTOGRAPHIE", "PHOTO"), 300, True),
                                           ("state", T("ÉTAT", "STATE"), 115, False),
                                           ("scale", T("ÉCHELLE", "SCALE"), 125, False),
                                           ("todo", T("À FAIRE", "TO DO"), 280, True)):
            self.table.heading(col, text=title, anchor="w")
            self.table.column(col, width=int(width * self.k), minwidth=60, anchor="w", stretch=stretch)
        for tag, colour in (("ok", TEAL), ("verify", TERRA), ("failed", RED)):
            self.table.tag_configure(tag, foreground=colour)
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=sb.set)
        self.table.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.table.bind("<Double-1>", self._row_open)
        foot = tk.Frame(left, bg=CARD_BG)
        foot.pack(fill="x", pady=(8, 0))
        self.log_btn = ttk.Button(foot, text=T("▸ Détails techniques", "▸ Technical details"), style="Link.TButton",
                                  command=self._toggle_log)
        self.log_btn.pack(side="left")
        tk.Label(foot, text=T("Double-clic sur une ligne : la corriger.", "Double-click a row to fix it."),
                 bg=CARD_BG, fg=MUTED, font=(FONT_SERIF, 9, "italic")).pack(side="right")
        self.logf = tk.Frame(left, bg=CARD_BG)
        self.log = tk.Text(self.logf, height=8, bg=PAPER, fg=TEXT, relief="flat", wrap="word",
                           font=(FONT_MONO, 9), highlightthickness=1, highlightbackground=LINE,
                           padx=8, pady=6, state="disabled")
        lsb = ttk.Scrollbar(self.logf, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=lsb.set)
        self.log.pack(side="left", fill="both", expand=True)
        lsb.pack(side="right", fill="y")
        for tag, colour in (("ok", TEAL), ("verify", TERRA), ("failed", RED), ("info", VIOLET_2), ("cmd", MUTED)):
            self.log.tag_configure(tag, foreground=colour)

        right = self._card()
        self._options(right)
        self.run_btn = ttk.Button(self.canvas, text=T("Lancer", "Run"), style="Run.TButton", command=self.run)
        self.cancel_btn = ttk.Button(self.canvas, text=T("Arrêter", "Stop"), style="Cancel.TButton",
                                     command=self.cancel, state="disabled")
        self.open_btn = ttk.Button(self.canvas, text=T("Ouvrir les résultats", "Open results"), style="Teal.TButton",
                                   command=self.open_results, state="disabled")
        self.next_hint = tk.StringVar(value="")
        self._page(T("Étape 03", "Step 03"), T("Détourer et mettre à l'échelle", "Outline and scale"),
                   T("Gerbil trouve l'échelle de chaque photographie, détoure l'objet et écrit les fichiers à "
                     "leur taille réelle (1:1).",
                     "Gerbil finds the scale of each photo, outlines the object and writes the files at their "
                     "real size (1:1)."),
                   left, right, [self.run_btn, self.cancel_btn, self.open_btn], self.next_hint)

    def _page_review(self):
        """04: the photos to look at, grouped by problem, and the review window."""
        left = self._card()
        self._section(left, T("Photographies à revoir", "Photos to look at"))
        tf = tk.Frame(left, bg=CARD_BG)
        tf.pack(fill="both", expand=True)
        self.todo_tree = ttk.Treeview(tf, columns=("photo", "problem"), show="headings", selectmode="extended")
        for col, title, width in (("photo", T("PHOTOGRAPHIE", "PHOTO"), 280), ("problem", T("PROBLÈME", "PROBLEM"), 360)):
            self.todo_tree.heading(col, text=title, anchor="w")
            self.todo_tree.column(col, width=int(width * self.k), anchor="w", stretch=True)
        self.todo_tree.tag_configure("verify", foreground=TERRA)
        self.todo_tree.tag_configure("failed", foreground=RED)
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.todo_tree.yview)
        self.todo_tree.configure(yscrollcommand=sb.set)
        self.todo_tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.todo_tree.bind("<Double-1>", self._row_open)
        b = tk.Frame(left, bg=CARD_BG)
        b.pack(fill="x", pady=(10, 0))
        ttk.Button(b, text=T("Régler l'échelle à la main…", "Set the scale by hand…"),
                   command=self._scale_for_selection).pack(side="left")

        right = self._card()
        self._section(right, T("Les couleurs", "The colours"))
        for colour, fr, en in ((TEAL, "ok : rien à faire", "ok: nothing to do"),
                               (TERRA, "à vérifier : un doute, les fichiers portent _to_be_verified",
                                "to verify: a doubt, the files carry _to_be_verified"),
                               (RED, "échec : aucun objet trouvé", "failed: no object found")):
            r = tk.Frame(right, bg=CARD_BG)
            r.pack(fill="x", pady=2)
            tk.Label(r, text="●", bg=CARD_BG, fg=colour, font=(FONT_SERIF, 11)).pack(side="left", anchor="n")
            tk.Label(r, text=T(fr, en), bg=CARD_BG, fg=TEXT, font=(FONT_SERIF, 10), justify="left",
                     wraplength=int(300 * self.k), anchor="w").pack(side="left", padx=(6, 0), fill="x")
        self._section(right, T("Bon à savoir", "Good to know"), top=16)
        self._text(right, T("Les corrections sont enregistrées à côté des photographies (dossier gerbil_edits) : "
                            "les traitements suivants les gardent. Une photographie corrigée est retraitée "
                            "aussitôt.",
                            "The corrections are saved next to the photos (gerbil_edits folder): later runs keep "
                            "them. A corrected photo is processed again at once."))
        go = ttk.Button(self.canvas, text=T("Vérifier", "Review"), style="Run.TButton", command=self.review)
        self.review_hint = tk.StringVar(value="")
        self._page(T("Étape 04", "Step 04"), T("Vérification", "Review"),
                   T("Les photographies douteuses d'abord : corriger le détourage, l'orientation ou l'échelle.",
                     "Doubtful photos first: fix the cut-out, the orientation or the scale."),
                   left, right, [go], self.review_hint)

    def _page_publication(self):
        """05: plates, inventory, thumbnails."""
        left = self._card()
        tiles = tk.Frame(left, bg=CARD_BG)
        tiles.pack(fill="both", expand=True)
        for k, (fr, en, dfr, den, cmd) in enumerate((
                ("Planches", "Plates", "Les objets mis en page à une échelle choisie (1:1, 1:2…), avec légendes, "
                 "barre d'échelle et dessins, en SVG pour Illustrator ou Inkscape.",
                 "The objects laid out at a chosen scale (1:1, 1:2…), with captions, scale bar and drawings, "
                 "as SVG for Illustrator or Inkscape.", self.plates),
                ("Inventaire", "Inventory", "Un tableau CSV des fichiers d'un dossier (photographies, dessins, "
                 "modèles 3D) et des informations lues dans leurs noms.",
                 "A CSV table of the files of a folder (photos, drawings, 3D models) and of the information "
                 "read from their names.", lambda: InventoryWindow(self)),
                ("Vignettes", "Thumbnails", "Des copies réduites pour les bases de données, fond transparent ou "
                 "blanc.", "Reduced copies for databases, transparent or white background.",
                 lambda: ThumbnailsWindow(self)))):
            t = tk.Frame(tiles, bg=CARD_BG, highlightthickness=1, highlightbackground=LINE, padx=14, pady=12)
            t.grid(row=0, column=k, sticky="new", padx=(0 if k == 0 else 12, 0))
            tiles.columnconfigure(k, weight=1, uniform="tiles")
            tk.Label(t, text=f"0{k + 1}", bg=CARD_BG, fg=TEAL, font=(FONT_MONO, 10, "bold")).pack(anchor="w")
            tk.Label(t, text=T(fr, en), bg=CARD_BG, fg=VIOLET, font=(FONT_DISPLAY, 18, "bold")).pack(anchor="w")
            tk.Label(t, text=T(dfr, den), bg=CARD_BG, fg=MUTED, font=(FONT_SERIF, 10), justify="left",
                     wraplength=int(230 * self.k), anchor="w").pack(fill="x", pady=(4, 12))
            ttk.Button(t, text=T("Ouvrir…", "Open…"), command=cmd).pack(anchor="w")
        opn = ttk.Button(self.canvas, text=T("Ouvrir les résultats", "Open results"), style="Teal.TButton",
                         command=self.open_results)
        self._page(T("Étape 05", "Step 05"), T("Publication", "Publication"),
                   T("Ce que l'on fait des objets détourés : planches, inventaire, vignettes.",
                     "What to do with the outlined objects: plates, inventory, thumbnails."),
                   left, None, [opn], None)

    # ---------------------------------------------------------------- settings
    def _options(self, card):
        """The essential settings, where the results go, and the settings changed from the defaults; the
        others in the 'Advanced settings' window."""
        self.v, self.w = {}, {}
        for key in OPTION_KEYS:
            v = self.s[key]
            if isinstance(DEFAULTS[key], bool):
                self.v[key] = tk.BooleanVar(value=v)
            elif key in ("margin_cm", "gap_cm"):
                self.v[key] = tk.StringVar(value="%.1f" % float(v))
            elif key in ("default_ppi", "jobs"):
                self.v[key] = tk.StringVar(value="%.0f" % float(v))
            else:
                self.v[key] = tk.StringVar(value=str(v))
            self.v[key].trace_add("write", lambda *_: self._changed())
        self.ai_ok = has_ai()
        if not self.ai_ok:
            self.v["ai"].set(False)
        self._section(card, T("Réglages", "Settings"))
        grid = tk.Frame(card, bg=CARD_BG)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        self._option_widgets(grid, ESSENTIAL_OPTIONS)
        ttk.Button(card, text=T("▸ Réglages avancés…", "▸ Advanced settings…"), style="Link.TButton",
                   command=self.advanced).pack(anchor="w", pady=(8, 0))
        self._section(card, T("Résultats", "Results"), top=14)
        self.out_mode = tk.StringVar(value=self.s["output_mode"])
        ttk.Radiobutton(card, text=T("À côté des photographies (outlined_result)",
                                     "Next to the photos (outlined_result)"),
                        value="next", variable=self.out_mode, command=self._sync).pack(anchor="w")
        row = tk.Frame(card, bg=CARD_BG)
        row.pack(fill="x", pady=(4, 0))
        ttk.Radiobutton(row, text=T("Ici :", "Here:"), value="other", variable=self.out_mode,
                        command=self._sync).pack(side="left")
        self.out_dir = tk.StringVar(value=self.s["output_dir"])
        self.out_entry = ttk.Entry(row, textvariable=self.out_dir, font=(FONT_MONO, 9))
        self.out_entry.pack(side="left", fill="x", expand=True, padx=6)
        self.out_btn = ttk.Button(row, text="…", style="Small.TButton", command=self.pick_output)
        self.out_btn.pack(side="left")
        self._section(card, T("Modifié par rapport au défaut", "Changed from the defaults"), top=14)
        self.changed_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self.changed_var, bg=CARD_BG, fg=TERRA, font=(FONT_SERIF, 10), justify="left",
                 anchor="w", wraplength=int(330 * self.k)).pack(fill="x")
        ttk.Button(card, text=T("Revenir aux valeurs par défaut", "Back to the defaults"), style="Small.TButton",
                   command=self.reset_options).pack(anchor="w", pady=(6, 0))
        self._sync()

    def _option_widgets(self, parent, keys):
        """Check boxes, lists and number fields of the given settings, in two columns of a grid."""
        r = parent.grid_size()[1]
        for key in keys:
            kind, label, extra = OPTION_SPECS[key]
            text = T(*label)
            if key == "ai" and not self.ai_ok:
                text += T("  (à installer)", "  (to install)")
            if kind == "check":
                w = ttk.Checkbutton(parent, text=text, variable=self.v[key],
                                    command=self._ai_ticked if key == "ai" else self._sync)
                w.grid(row=r, column=0, columnspan=2, sticky="w", pady=2)
                tips = [w]
            else:
                lbl = tk.Label(parent, text=text, bg=CARD_BG, fg=TEXT, font=(FONT_SERIF, 10), anchor="w")
                lbl.grid(row=r, column=0, sticky="w", pady=2, padx=(0, 10))
                if kind == "choice":
                    w = ttk.Combobox(parent, textvariable=self.v[key], values=extra, state="readonly", width=12)
                    w.bind("<<ComboboxSelected>>", lambda _: self._sync())
                else:
                    lo, hi, step = extra
                    hi = max(1, os.cpu_count() or 1) if key == "jobs" else hi
                    w = ttk.Spinbox(parent, textvariable=self.v[key], from_=lo, to=hi, increment=step, width=8,
                                    format="%.0f" if step >= 1 else "%.1f")
                w.grid(row=r, column=1, sticky="w", pady=2)
                tips = [lbl, w]
            for x in tips:
                Tooltip(x, help_text(key))
            self.w[key] = w
            r += 1

    def advanced(self):
        """The window of the other settings (files, run, scale and layout, cleaning, AI)."""
        if getattr(self, "adv_win", None) is not None and self.adv_win.winfo_exists():
            self.adv_win.lift()
            return
        win = self.adv_win = tk.Toplevel(self.root)
        win.title(T("Réglages avancés", "Advanced settings"))
        win.configure(bg=CARD_BG)
        win.transient(self.root)
        body = tk.Frame(win, bg=CARD_BG, padx=22, pady=18)
        body.pack(fill="both", expand=True)
        cols = [tk.Frame(body, bg=CARD_BG), tk.Frame(body, bg=CARD_BG)]
        for k, c in enumerate(cols):
            c.grid(row=0, column=k, sticky="nw", padx=(0, 30) if k == 0 else 0)
            c.columnconfigure(1, weight=1)
        for col, sections in ((0, ADVANCED_OPTIONS[:2]), (1, ADVANCED_OPTIONS[2:])):
            for (fr, en), keys in sections:
                tk.Label(cols[col], text=T(fr, en).upper(), bg=CARD_BG, fg=MUTED, font=(FONT_MONO, 9, "bold"),
                         anchor="w").grid(row=cols[col].grid_size()[1], column=0, columnspan=2, sticky="w",
                                          pady=(12, 4))
                self._option_widgets(cols[col], keys)
        ttk.Button(win, text=T("Fermer", "Close"), style="Run.TButton", command=win.destroy).pack(
            anchor="e", padx=22, pady=(0, 18))
        self._sync()

    def _changed(self):
        """The settings that differ from the defaults, listed under the settings."""
        if not hasattr(self, "changed_var"):
            return
        out = []
        for key in OPTION_KEYS:
            try:
                same = option_value(key, self.v[key].get()) == option_value(key, DEFAULTS[key])
            except (ValueError, tk.TclError):
                same = False
            if not same:
                kind, label, _ = OPTION_SPECS[key]
                val = self.v[key].get()
                out.append(T(*label) + ("" if kind == "check" else f" : {val}" if LANG == "fr" else f": {val}")
                           + (T(" (non)", " (off)") if kind == "check" and not val else ""))
        self.changed_var.set(", ".join(out) if out else T("Rien : réglages par défaut.", "Nothing: default settings."))

    def reset_options(self):
        """All the settings back to their default values (the results folder and the profile kept)."""
        for key in OPTION_KEYS:
            v = DEFAULTS[key]
            self.v[key].set(v if isinstance(v, bool) else ("%.1f" % v if key in ("margin_cm", "gap_cm") else str(v)))
        if not self.ai_ok:
            self.v["ai"].set(False)
        self._sync()

    def set_lang(self, code):
        """Interface in French or English: the window is built again in that language."""
        global LANG
        if code == LANG:
            return
        try:
            self._collect()
        except ValueError:
            pass
        paths = list(self.tree.get_children())
        self.s["lang"] = LANG = code
        self.save_settings()
        if getattr(self, "adv_win", None) is not None and self.adv_win.winfo_exists():
            self.adv_win.destroy()
        for w in self.root.winfo_children():
            if not isinstance(w, tk.Toplevel):
                w.destroy()
        self._build()
        self.add_paths(paths)
        self.check_packages()
        self._refresh_steps()

    def apply_profile(self):
        """The options kept in the chosen profile are set in the window."""
        name = self.profile.get()
        self.s["profile"] = "" if name == T("(aucun)", "(none)") else name
        if not self.s["profile"]:
            return
        try:
            with open(profile_path(name), encoding="utf-8") as fh:
                st = json.load(fh).get("settings") or {}
        except (OSError, ValueError):
            return
        for k, v in st.items():
            if k in self.v:
                self.v[k].set(v)
        self._sync()

    def profiles_changed(self, name):
        """List of profiles updated, the profile saved chosen."""
        self.profile_cb.configure(values=[T("(aucun)", "(none)")] + profile_names())
        self.profile.set(name)
        self.apply_profile()

    def _ai_ticked(self):
        """AI ticked: offers to install onnxruntime when missing."""
        if self.v["ai"].get() and not self.ai_ok:
            self.v["ai"].set(False)
            if FROZEN:
                messagebox.showinfo("Gerbil", T("Cette version a été construite sans le second avis de l'IA.",
                                                "This version was built without the AI second opinion."))
            elif self.proc is None and messagebox.askyesno(
                    "Gerbil", T("Le second avis de l'IA a besoin du paquet onnxruntime (environ 60 Mo, "
                                "téléchargé depuis internet).\n\nL'installer maintenant ?",
                                "The AI second opinion needs the onnxruntime package (about 60 MB, "
                                "downloaded from the internet).\n\nInstall it now?")):
                self._start(pip_command([AI_PACKAGE]), "pip-ai")
        self._sync()

    def check_packages(self):
        """Banner and Run button according to the required packages."""
        missing = missing_packages()
        if missing:
            self.banner_text.configure(
                text=T("Des paquets Python nécessaires au traitement manquent sur cet ordinateur :  ",
                       "Some Python packages needed to process the photos are missing on this computer:  ")
                     + ", ".join(missing) + T(".\nCliquez sur « Installer maintenant » (connexion internet, "
                                              "environ 2 minutes).",
                                              ".\nClick 'Install now' (internet connection needed, about 2 minutes)."))
            self.banner.pack(fill="x", after=self.banner_anchor)
            self.run_btn.state(["disabled"])
            self.status.set(T("Installez d'abord les paquets manquants.", "Install the missing packages first."))
        else:
            self.banner.pack_forget()
            if self.proc is None:
                self.run_btn.state(["!disabled"])
        return not missing

    def install_required(self):
        """Installs the missing packages (pip, in the background)."""
        if self.proc is None:
            self._start(pip_command(missing_packages()), "pip")

    def _sync(self):
        """Enables the options that depend on another one; lists the settings changed."""
        on = lambda key: self.v[key].get()
        live = lambda key: key in self.w and self.w[key].winfo_exists()
        if live("original_layer"):
            self.w["original_layer"].state(["!disabled"] if on("psd") else ["disabled"])
        if live("scale_cm"):
            self.w["scale_cm"].state(["!disabled", "readonly"] if on("scale") else ["disabled"])
        for key in ("ai_model", "ai_device"):
            if live(key):
                self.w[key].state(["!disabled", "readonly"] if on("ai") else ["disabled"])
        other = self.out_mode.get() == "other"
        self.out_entry.state(["!disabled"] if other else ["disabled"])
        self.out_btn.state(["!disabled"] if other else ["disabled"])
        self._changed()

    # ---------------------------------------------------------------- steps
    def _refresh_steps(self):
        """What the column of steps says of each step."""
        n = sum(int(self.tree.set(i, "photos")) for i in self.tree.get_children())
        nf = sum(1 for i in self.tree.get_children() if os.path.isdir(i))
        if n:
            self.step_sub[0].set(T(f"{nf} dossier(s), {n} photographie(s)", f"{nf} folder(s), {n} photo(s)"))
        else:
            self.step_sub[0].set(T("aucune pour l'instant", "none yet"))
        if not self.step_sub[1].get():
            self.step_sub[1].set(T("facultatif", "optional"))
        if self.proc is not None and self.kind == "script":
            self.step_sub[2].set(self.status.get())
        elif self.rows:
            self.step_sub[2].set(self._summary())
        else:
            self.step_sub[2].set(T("pas encore lancé", "not run yet"))
        bad = sum(1 for r in self.rows if r[1] != "ok")
        badge = self.step_widgets[3]["badge"]
        if bad:
            badge.configure(text=str(bad))
            badge.pack(side="left", padx=(8, 0))
            self.step_sub[3].set(T("photographies à revoir", "photos to look at"))
        else:
            badge.pack_forget()
            self.step_sub[3].set(T("rien à revoir", "nothing to look at") if self.rows else T("après le traitement",
                                                                                          "after the processing"))
        self.step_sub[4].set(T("planches, inventaire, vignettes", "plates, inventory, thumbnails"))
        self.review_hint.set(T(f"{bad} photographie(s) à revoir", f"{bad} photo(s) to look at") if bad else "")
        self.next_hint.set(T(f"Ensuite : vérification de {bad} photographie(s)", f"Next: review of {bad} photo(s)")
                           if bad and self.proc is None else "")

    def _naming_summary(self):
        """What the project of the first folder says: template, fields, photos with missing information."""
        folders = [i if os.path.isdir(i) else os.path.dirname(i) for i in self.tree.get_children()]
        if not folders:
            self.naming_var.set(T("Ajoutez d'abord un dossier de photographies (étape 01).",
                                  "Add a folder of photos first (step 01)."))
            self.naming_example.set("")
            self.step_sub[1].set(T("facultatif", "optional"))
            return
        folder = folders[0]
        pr = load_project_file(folder)
        if pr is None:
            self.naming_var.set(T("Le fichier gerbil_project.json de ce dossier est illisible.",
                                  "The gerbil_project.json of this folder cannot be read."))
            return
        photos = sorted(f for f in os.listdir(folder) if os.path.splitext(f)[1].lower() in EXTENSIONS)
        template = (pr.get("template") or "").strip()
        exists = os.path.exists(os.path.join(folder, PROJECT_FILE))
        required = [f["key"] for f in pr["fields"] if f.get("required")]
        missing = sum(1 for p in photos if any(not project_values(pr, p).get(k) for k in required))
        name = os.path.basename(folder)
        if not exists:
            text = T(f"Le dossier « {name} » n'a pas encore de projet : les fichiers produits garderont le nom "
                     "des photographies.", f"The folder '{name}' has no project yet: the output files will keep "
                     "the names of the photos.")
            self.step_sub[1].set(T("facultatif", "optional"))
        else:
            fields = ", ".join(f.get("label") or f["key"] for f in pr["fields"])
            text = T(f"Dossier « {name} » : {len(photos)} photographie(s).\nChamps : {fields}.\n"
                     f"Modèle de nom : {template or '(aucun)'}.\n",
                     f"Folder '{name}': {len(photos)} photo(s).\nFields: {fields}.\n"
                     f"Name template: {template or '(none)'}.\n")
            text += (T(f"{missing} photographie(s) sans toutes leurs informations obligatoires.",
                       f"{missing} photo(s) without all their required information.") if missing
                     else T("Toutes les informations obligatoires sont remplies.", "All the required information is filled in."))
            self.step_sub[1].set((template or T("sans modèle", "no template"))
                                 + (T(f", {missing} incomplète(s)", f", {missing} incomplete") if missing else ""))
        self.naming_var.set(text)
        self.naming_example.set((T("Exemple : ", "Example: ") + photos[0] + "  →  "
                                 + project_output_name(pr, photos[0]) + "_outlined.tif") if photos else "")

    # ---------------------------------------------------------------- photos
    def add_paths(self, paths):
        """Adds folders / photos to the list (with their number of photos)."""
        known = set(self.tree.get_children())
        for p in paths:
            p = os.path.normpath(os.path.abspath(p))
            if p in known:
                continue
            name, where = os.path.basename(p) or p, os.path.dirname(p)
            if os.path.isdir(p):
                self.tree.insert("", "end", iid=p, values=("\U0001F4C1 " + name, count_photos(p), where))
            elif os.path.isfile(p) and os.path.splitext(p)[1].lower() in EXTENSIONS:
                self.tree.insert("", "end", iid=p, values=(name, 1, where))
            else:
                continue
            known.add(p)
            self.s["last_dir"] = p if os.path.isdir(p) else os.path.dirname(p)
        n = sum(int(self.tree.set(i, "photos")) for i in self.tree.get_children())
        self.total_lbl.configure(text=T(f"{n} photographie(s) à traiter.", f"{n} photo(s) to process.") if n
                                 else T("Aucune photographie pour l'instant.", "No photo yet."))
        self.sources_hint.set(T(f"{n} photographie(s)", f"{n} photo(s)") if n else "")
        self._refresh_steps()

    def add_folder(self):
        """Adds a folder of photos."""
        d = filedialog.askdirectory(title=T("Dossier de photographies", "Folder of photos"),
                                    initialdir=self.s["last_dir"] or None)
        if d:
            self.add_paths([d])

    def add_files(self):
        """Adds photos."""
        fs = filedialog.askopenfilenames(title=T("Photographies", "Photos"), initialdir=self.s["last_dir"] or None,
                                         filetypes=[(T("Photographies", "Photos"),
                                                     " ".join("*" + e for e in sorted(EXTENSIONS))),
                                                    (T("Tous les fichiers", "All files"), "*.*")])
        if fs:
            self.add_paths(fs)

    def project(self):
        """Project of the folder selected in the list (or of the folder of the photo selected)."""
        sel = self.tree.selection()
        folders = [i if os.path.isdir(i) else os.path.dirname(i) for i in sel]
        if not folders:
            folders = [i if os.path.isdir(i) else os.path.dirname(i) for i in self.tree.get_children()]
        folders = list(dict.fromkeys(folders))
        if len(folders) != 1:
            d = filedialog.askdirectory(title=T("Dossier de photographies à renommer", "Folder of photos to rename"),
                                        initialdir=self.s["last_dir"] or None)
            if not d:
                return
            folders = [os.path.normpath(d)]
        try:
            ProjectWindow(self, folders[0])
        except (ValueError, OSError) as e:
            messagebox.showerror("Gerbil", T("Impossible d'ouvrir le renommage en lot :\n", "Could not open the batch "
                                             "renaming:\n") + str(e))

    def set_scale(self):
        """Manual scale of one photo: the photo selected in the list, otherwise one to choose."""
        sel = [i for i in self.tree.selection() if os.path.isfile(i)]
        if len(sel) > 1:                                  # several photos selected: one after the other
            self.scale_series(sel)
            return
        path = sel[0] if len(sel) == 1 else filedialog.askopenfilename(
            title=T("Photographie dont régler l'échelle", "Photo whose scale to set"),
            initialdir=(self.tree.selection() or [self.s["last_dir"]])[0] or None,
            filetypes=[(T("Photographies", "Photos"), " ".join("*" + e for e in sorted(EXTENSIONS))),
                       (T("Tous les fichiers", "All files"), "*.*")])
        if path:
            self._open_scale(os.path.normpath(path))

    def _open_scale(self, path):
        try:
            ScaleWindow(self, path)
        except ImportError:
            messagebox.showwarning("Gerbil", T("Cette fenêtre a besoin du paquet Pillow : installez d'abord les "
                                               "paquets manquants.", "This window needs the Pillow package: install "
                                               "the missing packages first."))
        except OSError as e:
            messagebox.showerror("Gerbil", T("Impossible d'ouvrir la photographie :\n", "Could not open the photo:\n")
                                 + str(e))

    def scale_series(self, paths):
        """Manual scales of several photos, one window after the other; the photos whose scale was saved
        can then be processed again in one run."""
        self.next_scale({"todo": list(paths), "saved": [], "total": len(paths), "cm": None, "width_cm": None})

    def next_scale(self, seq):
        """Series of manual scales: opens the next photo."""
        while seq["todo"]:
            path = seq["todo"].pop(0)
            try:
                ScaleWindow(self, path, seq)
                return
            except ImportError:
                messagebox.showwarning("Gerbil", T("Cette fenêtre a besoin du paquet Pillow : installez d'abord "
                                                   "les paquets manquants.", "This window needs the Pillow package: "
                                                   "install the missing packages first."))
                return
            except OSError as e:
                self._log(f"Could not open {path}: {e}\n", "verify")
        if seq["saved"] and messagebox.askyesno(
                "Gerbil", T(f"Échelle réglée pour {len(seq['saved'])} photographie(s).\n\nLes retraiter maintenant ?",
                            f"Scale set for {len(seq['saved'])} photo(s).\n\nProcess them again now?")):
            self.run(seq["saved"])

    def _scale_for_selection(self):
        """Manual scale of the photos selected in the list to look at (else of those whose scale is missing)."""
        paths = [self._path_of(self.todo_tree.set(i, "photo")) for i in self.todo_tree.selection()]
        paths = [p for p in paths if p] or list(self.no_scale)
        if paths:
            self.scale_series(paths)
        else:
            self.set_scale()

    def _path_of(self, name):
        return next((r[4] for r in self.rows if r[0] == name and r[4]), self.index.get(name))

    def _row_open(self, event):
        """Double-click on a result: the scale window when the scale is the problem, else the review."""
        tree = event.widget
        item = tree.identify_row(event.y)
        if not item:
            return
        name = tree.set(item, "photo")
        row = next((r for r in self.rows if r[0] == name), None)
        if row and row[1] != "ok" and row[5] and row[4]:
            self._open_scale(row[4])
        else:
            self.review()

    def remove(self):
        """Removes the selected rows of the list."""
        for i in self.tree.selection():
            self.tree.delete(i)
        self.add_paths([])

    def clear(self):
        """Empties the list."""
        self.tree.delete(*self.tree.get_children())
        self.add_paths([])

    def pick_output(self):
        """Chooses the results folder (not a folder of photos)."""
        d = filedialog.askdirectory(title=T("Dossier des résultats", "Result folder"), initialdir=self.out_dir.get() or None)
        if d:
            d = os.path.normpath(d)
            photos = {os.path.normcase(os.path.normpath(p)) for p in self.tree.get_children() if os.path.isdir(p)}
            if os.path.normcase(d) in photos:
                messagebox.showwarning("Gerbil", T("C'est un dossier de photographies : les résultats seraient mêlés "
                                                   "aux photographies. Choisissez un autre dossier (ou gardez le "
                                                   "dossier outlined_result à côté des photographies).",
                                                   "This is a folder of photos: the results would be mixed with the "
                                                   "photos. Choose another folder (or keep 'outlined_result next to "
                                                   "the photos')."))
                return
            self.out_dir.set(d)

    # ---------------------------------------------------------------- run
    def _collect(self):
        """Reads the options; returns the command-line arguments (only what differs from the defaults)."""
        s = self.s
        for k, var in self.v.items():
            s[k] = var.get()
        for k in ("margin_cm", "gap_cm", "default_ppi", "jobs"):
            try:
                s[k] = float(str(s[k]).replace(",", "."))
            except ValueError:
                raise ValueError(T(f"valeur invalide pour « {k} » : {s[k]}", f"invalid value for '{k}': {s[k]}"))
            if s[k] == int(s[k]):
                s[k] = int(s[k])
        s["output_mode"], s["output_dir"] = self.out_mode.get(), self.out_dir.get().strip()
        a = []
        if s["output_mode"] == "other":
            if not s["output_dir"]:
                raise ValueError(T("choisissez le dossier des résultats, ou gardez les résultats à côté des "
                                   "photographies", "choose the result folder, or keep the results next to the photos"))
            a += ["-o", s["output_dir"]]
        if s["background"] != "transparent":
            a += ["--background", s["background"]]
        if s["compression"] != "lzw":
            a += ["--compression", s["compression"]]
        if not s["psd"]:
            a.append("--no-psd")
        elif not s["original_layer"]:
            a.append("--no-original-layer")
        if not s["original_copy"]:
            a.append("--no-original-copy")
        if not s["control"]:
            a.append("--no-control")
        if not s["scale"]:
            a.append("--no-scale")
        elif s["scale_cm"] != "auto":
            a += ["--scale-cm", s["scale_cm"]]
        if s["default_ppi"] != 300:
            a += ["--default-ppi", f"{s['default_ppi']:g}"]
        if s["layout"] != "recompose":
            a += ["--layout", s["layout"]]
        if s["margin_cm"] != 0.5:
            a += ["--margin-cm", f"{s['margin_cm']:g}"]
        if s["gap_cm"] != 0.5:
            a += ["--gap-cm", f"{s['gap_cm']:g}"]
        if s["remove_putty"]:
            a.append("--remove-putty")
        if s["ai"]:
            a.append("--ai")
            if s["ai_model"] != "isnet":
                a += ["--ai-model", s["ai_model"]]
            if s["ai_device"] != "auto":
                a += ["--ai-device", s["ai_device"]]
        if s.get("profile") and os.path.isfile(profile_path(s["profile"])):
            a += ["--profile", profile_path(s["profile"])]
        a += ["-j", str(max(1, int(s["jobs"])))]
        if s["open"]:
            a.append("--open")
        return a

    def save_settings(self):
        """Saves the settings of the interface."""
        if self.selftest:
            return
        try:
            with open(SETTINGS, "w", encoding="utf-8") as fh:
                json.dump({k: self.s[k] for k in DEFAULTS}, fh, indent=1)
        except OSError:
            pass

    def run(self, inputs=None, quiet=False):
        """Processes the photos of the list (or the given ones: a photo whose scale was just set, photos
        corrected in the review window). quiet: no question at the end (exports of the review window)."""
        self.quiet = quiet
        inputs = list(inputs or self.tree.get_children())
        if not inputs:
            messagebox.showinfo("Gerbil", T("Ajoutez au moins un dossier ou une photographie (étape 01).",
                                            "Add at least one folder or photo (step 01)."))
            return
        try:
            args = self._collect()
        except ValueError as e:
            messagebox.showwarning("Gerbil", str(e)[:1].upper() + str(e)[1:] + ".")
            return
        self.save_settings()
        if not self.check_packages():
            return
        if not quiet:
            self.show_page(2)
        self._clear_log()
        self._log(("gerbil_cli.exe " if FROZEN else "py gerbil.py ")
                  + " ".join(f'"{x}"' if " " in x else x for x in inputs + args)
                  + "\n", "cmd")
        self.results, self.counts, self.total = [], {}, 0
        self.no_scale = []                                  # photos whose scale is missing or doubtful
        self.index = {}                                     # photo name -> path, to find them again
        if not quiet:
            self.rows = []
            self.table.delete(*self.table.get_children())
            self.todo_tree.delete(*self.todo_tree.get_children())
        for p in inputs:
            files = [os.path.join(p, f) for f in sorted(os.listdir(p))] if os.path.isdir(p) else [p]
            for f in files:
                if os.path.splitext(f)[1].lower() in EXTENSIONS:
                    self.index.setdefault(os.path.basename(f), f)
        self.bar.configure(value=0, maximum=1, mode="determinate")
        engine = [ENGINE] if FROZEN else [python_exe(), "-u", SCRIPT]
        self._start(engine + inputs + args + ["-v"], "script")

    def _start(self, cmd, kind):
        """Runs the script ("script") or pip ("pip": required packages, "pip-ai": onnxruntime)."""
        self.kind = kind
        if kind != "script":
            self._log(T("Installation : ", "Installing: ") + " ".join(cmd[cmd.index("install") + 2:])
                      + T("  (connexion internet nécessaire)\n", "  (internet connection needed)\n"), "info")
            self.bar.start(15)
        self.status.set(T("Démarrage…", "Starting…") if kind == "script"
                        else T("Installation des paquets Python…", "Installing the Python packages…"))
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        try:
            self.proc = subprocess.Popen(cmd, cwd=HERE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                         stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
                                         creationflags=NO_WINDOW)
        except OSError as e:
            messagebox.showerror("Gerbil", T("Impossible de démarrer :\n", "Could not start:\n") + str(e))
            self._stop_bar()
            return
        self.run_btn.state(["disabled"])
        self.install_btn.state(["disabled"])
        self.cancel_btn.state(["!disabled"])
        self.open_btn.state(["disabled"])
        threading.Thread(target=self._reader, args=(self.proc,), daemon=True).start()
        self.root.after(100, self._poll)

    def _stop_bar(self):
        """Stops the moving progress bar."""
        if str(self.bar["mode"]) == "indeterminate":
            self.bar.stop()
            self.bar.configure(mode="determinate", value=0)

    def _reader(self, proc):
        """Thread reading the output of the engine line by line (into a queue)."""
        for line in proc.stdout:
            self.lines.put(line.rstrip("\n"))
        proc.wait()
        self.lines.put(None)

    def _poll(self):
        """Every 100 ms: handles the lines received; end of the process detected."""
        done = False
        try:
            while True:
                line = self.lines.get_nowait()
                if line is None:
                    done = True
                    break
                self._handle(line)
        except queue.Empty:
            pass
        if done:
            self._finished()
        else:
            self.root.after(100, self._poll)

    def _add_row(self, name, status, scale, todo, path, scale_problem):
        """One photo in the table of the results (and in the list to look at when it is not ok)."""
        tag = {"ok": "ok", "to verify": "verify"}.get(status, "failed")
        state = {"ok": "● ok", "to verify": T("● à vérifier", "● to verify")}.get(status, T("● échec", "● failed"))
        self.table.insert("", "end", values=(name, state, scale, todo), tags=(tag,))
        if status != "ok":
            self.todo_tree.insert("", "end", values=(name, todo), tags=(tag,))

    def _handle(self, line):
        """One line of the engine: progress, table of the results, log, results folder."""
        if self.kind != "script":                          # pip output
            if line.strip():
                self._log(line + "\n", "cmd" if not line.startswith(("ERROR", "error")) else "failed")
            return
        m = re.match(r"^(\d+) photo\(s\) -> ", line)
        if m:
            self.total = int(m.group(1))
            self.bar.configure(maximum=max(1, self.total))
            self.status.set(f"0 / {self.total}")
            self._log(line + "\n", "info")
            self._refresh_steps()
            return
        m = re.match(r"^\[(\d+)/(\d+)\] (.+?): (ok|to verify|failed|error) \((.*?)\)(.*)$", line)
        if m:
            i, n, name, status = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
            self.counts[status] = self.counts.get(status, 0) + 1
            scale_problem = any(k in line for k in SCALE_PROBLEMS)
            if scale_problem and name in self.index:
                self.no_scale.append(self.index[name])
            scale = scale_text(m.group(5))
            parts = [p.strip() for p in m.group(6).split(" | ") if p.strip()]
            todo = doubt_text(parts[0].split(" ; ")[0]) if parts else ""
            row = (name, status, scale, todo, self.index.get(name), scale_problem)
            self.rows = [r for r in self.rows if r[0] != name] + [row]
            for tree in (self.table, self.todo_tree):
                for it in tree.get_children():
                    if tree.set(it, "photo") == name:
                        tree.delete(it)
            self._add_row(*row)
            self.table.see(self.table.get_children()[-1])
            self.bar.configure(maximum=n, value=i)
            self.status.set(f"{i} / {n}")
            self._log(line + "\n", {"ok": "ok", "to verify": "verify"}.get(status, "failed"))
            self._refresh_steps()
            return
        if line.startswith("Results: "):
            self.results.append(line[9:].strip())
        if line.startswith(("To check:", "  - ")):           # end-of-run summary
            self._log(line + "\n", "verify")
            return
        if line.startswith("Nothing to check."):
            self._log(line + "\n", "ok")
            return
        tag = "info" if line.startswith(("Done in", "Results:", "AI second opinion", "Downloading")) else None
        if line.startswith(("Traceback", "Warning", "Not found", "--ai needs", "AI model not available",
                            "Missing Python package")):
            tag = "verify"
        self._log(line + "\n", tag)

    def _summary(self):
        """"12 ok, 3 à vérifier, 1 échec"."""
        c = self.counts if self.counts else {}
        if not c and self.rows:
            for r in self.rows:
                c[r[1]] = c.get(r[1], 0) + 1
        parts = [f"{c.get('ok', 0)} ok", T(f"{c.get('to verify', 0)} à vérifier", f"{c.get('to verify', 0)} to verify")]
        bad = c.get("failed", 0) + c.get("error", 0)
        if bad:
            parts.append(T(f"{bad} échec(s)", f"{bad} failed"))
        return ", ".join(parts)

    def _finished(self):
        """End of a run: status, offers (manual scales), self-test file."""
        code = self.proc.returncode if self.proc else None
        cancelled = getattr(self, "_cancelled", False)
        self.proc, self._cancelled = None, False
        self.run_btn.state(["!disabled"])
        self.install_btn.state(["!disabled"])
        self.cancel_btn.state(["disabled"])
        self._stop_bar()
        if self.kind == "pip":
            ok = code == 0 and imports_ok(REQUIRED)
            self._log(T("Paquets installés : les photographies peuvent être traitées.\n",
                        "Packages installed: the photos can be processed.\n") if ok else
                      T("L'installation n'a pas réussi (connexion internet ? proxy ?). Voir les lignes ci-dessus.\n",
                        "The installation did not succeed (internet connection? proxy?). See the lines above.\n"),
                      "ok" if ok else "failed")
            if self.check_packages():
                self.status.set(T("Prêt.", "Ready."))
            return
        if self.kind == "pip-ai":
            self.ai_ok = code == 0 and imports_ok(["onnxruntime"])
            self._log(T("Second avis de l'IA installé (son modèle est téléchargé à la première utilisation).\n",
                        "AI second opinion installed (its model is downloaded at its first use).\n") if self.ai_ok else
                      T("L'installation de l'IA n'a pas réussi ; tout le reste fonctionne sans elle.\n",
                        "The AI installation did not succeed; everything else works without it.\n"),
                      "ok" if self.ai_ok else "failed")
            if self.ai_ok:
                if "ai" in self.w and self.w["ai"].winfo_exists():
                    self.w["ai"].configure(text=T(*OPTION_SPECS["ai"][1]))
                self.v["ai"].set(True)
                self._sync()
            self.check_packages()
            self.status.set(T("IA prête.", "AI ready.") if self.ai_ok else T("IA non installée.", "AI not installed."))
            return
        if self.results:
            self.open_btn.state(["!disabled"])
        if cancelled:
            self.status.set(T("Arrêté : ", "Stopped: ") + self._summary())
        elif code == 0 and self.total:
            self.status.set(self._summary())
            self.bar.configure(value=self.bar["maximum"])
        else:
            self.status.set(T("Arrêté : voir les détails techniques.", "Stopped: see the technical details."))
            if not self.logf.winfo_ismapped():
                self._toggle_log()
        self._refresh_steps()
        if not cancelled and not self.selftest and not getattr(self, "quiet", False) and getattr(self, "no_scale", None):
            todo, self.no_scale = self.no_scale, []         # offered once
            n = len(todo)
            if messagebox.askyesno("Gerbil", T(f"L'échelle manque ou est douteuse sur {n} photographie(s).\n\n"
                                               "La régler à la main maintenant, une photographie après l'autre ?",
                                               f"The scale is missing or doubtful on {n} photo(s).\n\n"
                                               "Set it by hand now, one photo after the other?")):
                self.scale_series(todo)
        if self.selftest:
            with open(os.path.join(self.selftest, "selftest.txt"), "w", encoding="utf-8") as fh:
                fh.write(f"exit code: {code}\nstatus: {self.status.get()}\n\n" + self.log.get("1.0", "end"))
            self.root.destroy()

    def cancel(self):
        """Stops the processing (the whole process tree)."""
        if self.proc and self.proc.poll() is None:
            self._cancelled = True
            # the whole process tree (the script runs the photos in worker processes)
            subprocess.run(["taskkill", "/PID", str(self.proc.pid), "/T", "/F"], capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self._log(T("Arrêté.\n", "Cancelled.\n"), "verify")

    def review(self):
        """Review window over the result folders of the last run (or a result folder to choose)."""
        folders = [d for d in self.results if os.path.isdir(os.path.join(d, REVIEW_DIR))]
        if not folders:
            d = filedialog.askdirectory(title=T("Dossier de résultats à vérifier (outlined_result)",
                                                "Result folder to review (outlined_result)"),
                                        initialdir=self.s["last_dir"] or None)
            if not d:
                return
            if not os.path.isdir(os.path.join(d, REVIEW_DIR)):
                messagebox.showinfo("Gerbil", T("Pas de données de vérification dans ce dossier : retraitez d'abord "
                                                "les photographies avec cette version de Gerbil.",
                                                "No review data in this folder: process the photos again "
                                                "with this version of Gerbil first."))
                return
            folders = [d]
        items = []
        for d in folders:
            rd = os.path.join(d, REVIEW_DIR)
            for f in sorted(os.listdir(rd)):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(rd, f), encoding="utf-8") as fh:
                            it = json.load(fh)
                    except (OSError, ValueError):
                        continue
                    if os.path.exists(it.get("photo", "")):
                        it["json"] = os.path.join(rd, f)
                        items.append(it)
        if not items:
            messagebox.showinfo("Gerbil", T("Rien à vérifier : les photographies de ces résultats sont introuvables.",
                                            "Nothing to review: the photos of these results cannot be found."))
            return
        rank = {"failed": 0, "error": 0, "to verify": 1}
        items.sort(key=lambda it: (rank.get(it.get("status"), 2), os.path.basename(it["photo"]).lower()))
        try:
            ReviewWindow(self, items)
        except ImportError:
            messagebox.showwarning("Gerbil", T("La vérification a besoin de numpy, OpenCV et Pillow : installez "
                                               "d'abord les paquets manquants.", "The review window needs numpy, "
                                               "OpenCV and Pillow: install the missing packages first."))

    def plates(self):
        """Plates window over a results folder (the last one processed, or one to choose)."""
        folders = [d for d in self.results if os.path.isdir(d)]
        d = folders[0] if len(folders) == 1 else filedialog.askdirectory(
            title=T("Dossier de résultats (outlined_result) à mettre en planches",
                    "Results folder (outlined_result) to lay out on plates"),
            initialdir=(folders[0] if folders else self.s["last_dir"]) or None)
        if not d:
            return
        try:
            PlatesWindow(self, os.path.normpath(d))
        except ImportError:
            messagebox.showwarning("Gerbil", T("Les planches ont besoin de Pillow : installez d'abord les paquets "
                                               "manquants.", "The plates need Pillow: install the missing "
                                               "packages first."))

    def open_results(self):
        """Opens the results folders."""
        for d in self.results:
            if os.path.isdir(d):
                os.startfile(d)

    def help(self):
        """Opens the guide of the interface language (else the README)."""
        guide = os.path.join(HERE, "docs", "Gerbil_guide_FR.odt" if LANG == "fr" else "Gerbil_guide_EN.odt")
        for path in (guide, README):
            if os.path.exists(path):
                os.startfile(path)
                return

    def close(self):
        """Closes (stops a run first, if wanted) and saves the settings."""
        if self.proc and self.proc.poll() is None:
            if not messagebox.askyesno("Gerbil", T("Un traitement est en cours. L'arrêter et quitter ?",
                                                   "A processing is running. Stop it and quit?")):
                return
            self.cancel()
        try:
            self._collect()
        except ValueError:
            pass
        self.save_settings()
        self.root.destroy()

    # ---------------------------------------------------------------- log
    def _toggle_log(self):
        """Shows or hides the technical details (the lines of the engine)."""
        if self.logf.winfo_ismapped():
            self.logf.pack_forget()
            self.log_btn.configure(text=T("▸ Détails techniques", "▸ Technical details"))
        else:
            self.logf.pack(fill="both", expand=False, pady=(8, 0))
            self.log_btn.configure(text=T("▾ Détails techniques", "▾ Technical details"))

    def _log(self, text, tag=None):
        """Adds a text to the technical details, in a colour."""
        self.log.configure(state="normal")
        self.log.insert("end", text, tag or ())
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        """Empties the technical details."""
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")


def main():
    """Entry of the interface: --install / --check for Install.bat, --selftest, or the window."""
    if "--install" in sys.argv[1:]:
        sys.exit(console_install())
    if "--check" in sys.argv[1:]:
        missing = missing_packages()
        if missing:
            print("Missing Python packages:", ", ".join(missing))
        sys.exit(1 if missing else 0)
    try:                                              # sharp text on high-resolution screens
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    args, selftest = sys.argv[1:], None
    if "--selftest" in args:                          # Gerbil.exe --selftest OUT_DIR photo... : runs, writes
        i = args.index("--selftest")                  # OUT_DIR\selftest.txt and quits (checks a build)
        selftest = os.path.abspath(args[i + 1])
        os.makedirs(selftest, exist_ok=True)
        args = args[:i] + args[i + 2:]
    root = tk.Tk()
    App(root, args, selftest)
    root.mainloop()


if __name__ == "__main__":
    main()
