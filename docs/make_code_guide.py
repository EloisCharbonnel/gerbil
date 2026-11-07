"""Writes docs/CODE_GUIDE.md: a guide to the Python code of Gerbil. Part 1 (below, INTRO) explains how the
code is organised and the Python notions it uses; part 2 is made from the code itself: for every file,
its sections (the "# ----" banners) and, in each, every function and class with its explanation (its
docstring) and its line. Run again after a change: py -3 docs/make_code_guide.py"""
import ast
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = [
    ("gerbil.py", "The engine and the command line: everything that processes a photo."),
    ("gerbil_gui.pyw", "The interface (windows) - it runs the engine as a separate program."),
    ("gerbil_plates.py", "The plates: objects laid out at a chosen scale, written as SVG."),
    ("gerbil_tools.py", "Inventory (CSV) and thumbnails."),
    ("packaging/gerbil_setup.pyw", "The installer (Gerbil_Setup.exe)."),
    ("tests/synthetic.py", "Synthetic photos for the automatic tests."),
    ("tests/test_gerbil.py", "The automatic tests."),
]

INTRO = r"""# Gerbil — guide to the code

This guide explains **what the Python code of Gerbil says, what it does and how**, so that it can be read,
explained and changed. Part 1 gives the keys to read it; part 2 lists every function and class, file by
file and section by section, with its explanation and its line in the file. The processing itself (the
methods, the thresholds, the mathematics) is described step by step in `PSEUDOCODE.txt`; this guide
follows the code.

*This file is written by `docs/make_code_guide.py` from the code: run it again after a change.*

## Part 1 — How to read the code

### The files and how they talk to each other

```
gerbil_gui.pyw  (windows)  --runs-->  gerbil.py / gerbil_cli.exe  (engine, one photo after the other)
       |                                   |
       |  reads its printed lines          +--> outlined_result/ : PSD, TIFF, previews, report, review data
       |  ("[3/12] NAME: ok ...")          |
       +--> gerbil_plates.py (plates)      +--> reads gerbil_project.json, gerbil_scales.json,
       +--> gerbil_tools.py  (inventory)        gerbil_edits/, gerbil_profile.json next to the photos
```

- The **engine** (`gerbil.py`) can be used alone, from the command line: `py -3 gerbil.py FOLDER`. It knows
  nothing about the windows.
- The **interface** (`gerbil_gui.pyw`) does not process photos itself: it builds the command line from
  the options, starts the engine as a separate program (`subprocess`), reads the lines it prints to show
  the progress, and opens the windows (review, plates…). Some windows also use functions of the engine
  directly (`import gerbil`), for instance to read a photo or learn a scale.
- Everything the user decides is saved **next to the photos** in small JSON files (names, manual scales,
  corrections, profile), so that a later run, or a colleague, finds them again.

### The path of one photo (gerbil.py, `process_photo`)

1. `load_photo` — reads the file (JPEG, TIFF, PNG, RAW through `develop_raw`), turns it upright, keeps the
   EXIF and the colour profile.
2. A reduced copy (1500 px) is made for the analysis; `BackgroundModel` models the background colour.
3. **The scale**: a manual scale if one was given (`manual_scale`), else `detect_scale` (checkerboards,
   rulers through `detect_ruler`, dark backgrounds through `_scale_on_dark`), else a learned scale of the
   site profile (`detect_learned_scale`). The result is a `Scale`: px/cm, outline, straightened image.
4. **The cut-out**: `outline_ceramic` (colour distance to the background, pieces sorted, labels and
   supports discarded, refined at full resolution), or the mask corrected by hand (`cutout_from_mask`).
5. `find_putty` flags (or removes) mounting putty.
6. `layout` builds the layers; `write_psd` and `write_tiff` write the files at the 1:1 resolution with
   their metadata (`make_xmp`: EXIF, IPTC); `control_image` the preview; `write_review` the data of the
   review window.
7. The row of the report is returned; `main` writes `outlined_report.csv` and the summary.

### Python notions used

- **Modules and `import`**: each file is a module; `import gerbil as g` gives access to its functions
  (`g.load_photo`). `from PIL import Image` takes one name from a library.
- **Functions** (`def name(arguments):`) take values and return a result (`return`). Their first string,
  between `\"\"\"`, is their *docstring*: the explanation shown in part 2.
- **Classes** (`class Name:`) group data and the functions that work on them (*methods*, whose first
  argument `self` is the object itself). Each window is a class (`ReviewWindow`, `PlatesWindow`…): its
  `__init__` builds the window, its methods react to the user.
- **`@dataclass`**: a class that is mostly a record of named values (`Scale`, `PlateSettings`, `Item`),
  written without boilerplate.
- **Dictionaries** `{"key": value}` hold settings, report rows, JSON files; **lists** `[a, b]` ordered
  values; **tuples** `(x, y)` fixed groups (coordinates, colours).
- **numpy arrays** hold images: `rgb[y, x]` is a pixel, `rgb.shape` is `(height, width, 3)`, values 0–255
  (`uint8`). Operations apply to all pixels at once (`rgb * 0.5`), without loops — that is what makes the
  processing fast. A **mask** is an array of `True` / `False` (or 0 / 255): `rgb[mask]` are the pixels
  of the object.
- **OpenCV** (`cv2`): image processing — resizing (`cv2.resize`), blurs, colour conversions (Lab),
  morphology (`cv2.erode` shrinks a mask, `cv2.dilate` grows it, `MORPH_OPEN` removes thin parts,
  `MORPH_CLOSE` fills thin gaps), connected components (separate pieces of a mask), contours.
- **Pillow** (`PIL`): reading and writing image files, drawing texts, ICC profiles.
- **Coordinates**: `x` to the right, `y` downwards, in pixels of the photo; on the plates, in millimetres
  of the page. Affine matrices `M` (2 × 3) turn coordinates of a straightened crop into coordinates of the
  photo (`apply_affine`).
- **Exceptions**: `try: … except OSError:` catches an error (a file that cannot be read) instead of
  stopping the program.
- **f-strings**: `f"{px_cm:.2f} px/cm"` writes values inside a text.
- **Parallel work**: the engine processes several photos at once in separate processes
  (`ProcessPoolExecutor`); the interface keeps responsive by doing long work in **threads**
  (`threading.Thread`) and by checking regularly with `after(ms, function)`.
- **tkinter** (the windows): widgets (`ttk.Button`, `tk.Canvas`…) are placed with `pack` or `grid`;
  `command=` and `bind("<Event>", function)` tie a click or a key to a method; variables
  (`tk.StringVar`) hold the value of a field; `mainloop()` waits for the events.

### Conventions

- Names and messages in English; constants in capitals at the top of their section (`LOW_T`,
  `LABEL_FILL`…), with a comment saying what they are.
- Comments explain *why* when it is not obvious; the docstrings say *what* and, briefly, *how*.
- Every change must leave the results already right identical (see `CONTRIBUTING.md`).

## Part 2 — Reference, file by file
"""


def sections(src):
    """(line, title) of the section banners: a line of dashes, a title line, a line of dashes."""
    lines = src.split("\n")
    out = []
    for i in range(len(lines) - 2):
        if re.match(r"^# -{20,}", lines[i]) and lines[i + 1].startswith("# ") and re.match(r"^# -{20,}", lines[i + 2]):
            out.append((i + 2, lines[i + 1][2:].strip()))
    return out


def signature(node):
    args = [a.arg for a in node.args.args]
    if node.args.vararg:
        args.append("*" + node.args.vararg.arg)
    if node.args.kwarg:
        args.append("**" + node.args.kwarg.arg)
    return f"{node.name}({', '.join(args)})"


def entries(tree):
    """(line, kind, name, signature, docstring, depth) of the classes, functions and methods."""
    out = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out.append((node.lineno, "class", node.name, node.name, ast.get_docstring(node) or "", 0))
            for sub in node.body:
                if isinstance(sub, ast.FunctionDef):
                    out.append((sub.lineno, "method", f"{node.name}.{sub.name}", signature(sub),
                                ast.get_docstring(sub) or "", 1))
        elif isinstance(node, ast.FunctionDef):
            out.append((node.lineno, "function", node.name, signature(node), ast.get_docstring(node) or "", 0))
    return out


def para(text):
    """A docstring as Markdown: lines joined into paragraphs, lists and indented blocks kept."""
    blocks, cur = [], []
    for line in text.split("\n"):
        if not line.strip():
            if cur:
                blocks.append(" ".join(cur))
                cur = []
        elif line.startswith((" ", "*", "-")) or re.match(r"^\w[\w ]{0,30}:\s", line) and cur == []:
            if cur:
                blocks.append(" ".join(cur))
                cur = []
            blocks.append("    " + line.rstrip() if line.startswith(" ") else line.rstrip())
        else:
            cur.append(line.strip())
    if cur:
        blocks.append(" ".join(cur))
    return "\n".join(b if b.startswith("    ") else b + "\n" for b in blocks).strip()


def main():
    out = [INTRO]
    toc = []
    for f, role in FILES:
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        n_lines = src.count("\n") + 1
        anchor = re.sub(r"[^a-z0-9]+", "-", f.lower()).strip("-")
        toc.append(f"- [{f}](#{anchor}) — {role}")
        out.append(f"\n### {f}\n\n{role} ({n_lines} lines.)\n")
        head = ast.get_docstring(tree)
        if head:
            out.append(para(head) + "\n")
        secs = sections(src) or [(1, "")]
        items = entries(tree)
        bounds = [s[0] for s in secs] + [n_lines + 1]
        for k, (line0, title) in enumerate(secs):
            inside = [e for e in items if bounds[k] <= e[0] < bounds[k + 1]]
            if k == 0:
                inside = [e for e in items if e[0] < bounds[1]]
            if not inside:
                continue
            if title:
                out.append(f"\n#### {title}\n")
            for line, kind, name, sig, doc, depth in inside:
                ind = "  " * depth
                text = para(doc) if doc else "(small helper: see the code)"
                text = text.replace("\n", "\n" + ind + "  ")
                out.append(f"{ind}- **`{sig}`** — {kind}, line {line}  \n{ind}  {text}\n")
    content = "\n".join(out)
    content = content.replace("## Part 2 — Reference, file by file\n",
                              "## Part 2 — Reference, file by file\n\n" + "\n".join(toc) + "\n", 1)
    with open(os.path.join(ROOT, "docs", "CODE_GUIDE.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(content)
    print("docs/CODE_GUIDE.md:", content.count("\n- **") + content.count("\n  - **"), "entries,",
          len(content) // 1024, "KB")


if __name__ == "__main__":
    main()
