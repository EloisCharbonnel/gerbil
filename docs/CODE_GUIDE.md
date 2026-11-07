# Gerbil — guide to the code

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

- [gerbil.py](#gerbil-py) — The engine and the command line: everything that processes a photo.
- [gerbil_gui.pyw](#gerbil-gui-pyw) — The interface (windows) - it runs the engine as a separate program.
- [gerbil_plates.py](#gerbil-plates-py) — The plates: objects laid out at a chosen scale, written as SVG.
- [gerbil_tools.py](#gerbil-tools-py) — Inventory (CSV) and thumbnails.
- [packaging/gerbil_setup.pyw](#packaging-gerbil-setup-pyw) — The installer (Gerbil_Setup.exe).
- [tests/synthetic.py](#tests-synthetic-py) — Synthetic photos for the automatic tests.
- [tests/test_gerbil.py](#tests-test-gerbil-py) — The automatic tests.


### gerbil.py

The engine and the command line: everything that processes a photo. (3919 lines.)

Gerbil - archaeological photo toolkit (formerly SherdCut): outlining of finds photographed with a scale, at their real size (1:1). © 2026 Eloïs CHARBONNEL Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE. This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to redistribute it under the conditions of the licence.

For each photo NAME.JPG, in an "outlined_result" folder next to the photos:

      * NAME.JPG                        copy of the original photo;
      * NAME.psd                        layers "Original photo" (hidden), "Scale", "Ceramic"
                                        (editable layer masks in Photoshop);
      * NAME_outlined.tif               outlined ceramic;
      * NAME_outlined_scale.tif         ceramic + scale;
      * to_control/NAME_to_control.jpg  control preview;
      * outlined_report.csv             one row per photo.
When something is doubtful, the output files get the "_to_be_verified" suffix.

The scale (1 cm squares, or a ruler graduated in millimetres; 5 or 10 cm) gives the real resolution of each photo. It is stored in the files: dropped into Illustrator, they show at 1:1.

Optional (--ai, needs onnxruntime): an AI second opinion (IS-Net or BiRefNet) that may only remove background kept by the colour rule (perforations, gaps between sherds, halos), never add anything.

Usage:

      py gerbil.py FOLDER_OR_PHOTOS [...] [options]
      py gerbil.py --help
      (or the interface: Gerbil.bat / gerbil_gui.pyw)


#### Image and metadata loading

- **`Photo`** — class, line 78  
  A photo as the engine uses it: path, RGB pixels (upright), ICC profile, EXIF, shooting
  
  information (camera, lens, date) kept for the report and the metadata.

- **`_txt(v)`** — function, line 88  
  EXIF value as clean text: bytes decoded (Latin-1), trailing zeros and spaces removed.

- **`_rational(v)`** — function, line 97  
  EXIF number written as an XMP fraction ("1/125"), as XMP expects.

- **`_xmp_date(v)`** — function, line 106  
  EXIF date "2025:12:01 21:03:55" turned into the XMP form "2025-12-01T21:03:55".

- **`develop_raw(path, half)`** — function, line 114  
  RAW photo developed by LibRaw (rawpy): white balance of the camera, sRGB, 8 bits, turned upright (the interface develops it the same way, so that the coordinates match).

- **`load_photo(path)`** — function, line 125  
  Opens a photo as the engine needs it: RGB pixels (8 bits, turned upright by the EXIF orientation; RAW files developed by develop_raw), EXIF, ICC colour profile, and the shooting information kept for the report and the XMP. Returns a Photo.

- **`srgb_profile()`** — function, line 174  
  Standard sRGB colour profile (ICC), embedded when the photo has none.

- **`output_exif(exif, dpi)`** — function, line 179  
  Copy of the shooting metadata, updated for the outlined file.


#### Background model and "object / background" map

- **`to_lab(rgb)`** — function, line 203  
  RGB image -> CIELAB (L* 0-100, a* and b* around 0): colour differences in Lab match what the eye sees, which makes "different from the background" measurable.

- **`distance(lab, ref, l_weight)`** — function, line 212  
  Colour distance of every pixel to the background model (Lab), lightness weighted by l_weight (shadows change the lightness more than the colour).

- **`poly_terms(x, y, deg)`** — function, line 221  
  Terms x^i * y^j of a 2D polynomial of degree deg: the background model is such a polynomial fitted on the background, so that a lighting gradient is followed.

- **`BackgroundModel`** — class, line 227  
  Background colour (Lab) modelled by a polynomial in x, y (lighting gradient).

  - **`__init__(self, lab)`** — method, line 230  
    Fits the background colour of the photo: a polynomial surface per Lab channel, fitted by least squares on the pixels that look like background (iterated, the object and the scale left out); decides whether the background is dark.

  - **`evaluate(self, x0, y0, w, h, W, H, step)`** — method, line 260  
    Background colour over the area [x0, x0+w[ x [y0, y0+h[ of a W x H image.

- **`hysteresis(d, low, high)`** — function, line 270  
  Hysteresis threshold: keeps the regions above `low` that contain at least one pixel
  
  above `high` (a faint edge is kept when it belongs to a clear object).

- **`fill_holes(m, d, min_true_hole_area, keep_open)`** — function, line 285  
  Fills the holes of the mask (gloss reflections, light concretions), except true openings: holes large enough whose mean colour is the background colour (handle, perforation).

- **`cast_shadows(obj, lab, model)`** — function, line 313  
  Light background: the cast shadows kept by the colour rule (darker than the background by a
  
  shadow, of its colour, smooth, along the outline, fading into the background). Returns their mask, or None.

- **`disk(r)`** — function, line 350  
  Disc-shaped structuring element of radius r for the morphology (erosion, dilation...).


#### Scale detection and measurement (squares)

- **`scale_ink_classes(rgb, white)`** — function, line 360  
  Black and vivid red pixels (coloured squares of an archaeological scale).

- **`straighten(img, center, theta, size, interp)`** — function, line 370  
  Extracts a crop of size=(w, h) centred on `center`, rotated so that the direction `theta` (radians, image frame) becomes horizontal.

- **`apply_affine(M, pts)`** — function, line 383  
  Applies the 2 x 3 affine matrix M to points (N x 2): rotation / scale / translation.

- **`_runs(state)`** — function, line 389  
  Runs of equal values in a 1D array: [[value, start, end], ...] (reading the squares).

- **`_merge_runs(R)`** — function, line 397  
  Joins consecutive runs of the same value.

- **`_clean_runs(R, min_len)`** — function, line 408  
  Removes the shortest inner runs (noise, digits) until all are at least min_len long.

- **`_crossing(p, x, direction)`** — function, line 422  
  Sub-pixel position where the profile p crosses 0.5 near x (direction +1: rising to the right).

- **`analyze_pattern(crop, valid)`** — function, line 436  
  Analyses a crop where the scale is horizontal and centred. Returns the position of the printed face, the number of squares and their length. `valid`: pixels of the crop that come from inside the photo (None: all of them). Beyond the photo edge the straightening copies the edge pixels: nothing is read there, and a square cut by the edge is counted but left out of the measurement (n = complete squares, n_cut = cut ones).

- **`_inside(shape, M, crop_shape)`** — function, line 538  
  Pixels of a straightened crop that come from inside the photo; None when they all do.

- **`_fit_comb(xs, step, min_n, tol)`** — function, line 551  
  Fits a regular sequence x_k = a0 + step * k to the positions xs (common phase by circular mean, then least squares rejecting the residuals above tol x step). Returns (a0, step, k, res) for the kept positions, or None.

- **`analyze_comb(crop, valid)`** — function, line 576  
  Second reading of a checkerboard (crop where the scale is horizontal and centred), used only when analyze_pattern fails. Robust to digits printed inside the squares ("5", "10", "cm") and to any number of squares: the boundaries between squares are where the signed profile
  
          q(x) = ink(top row) - ink(bottom row)      (two rows), or 2 ink(row) - 1 (single row)
  changes sign between two plateaus (|q| > 0.3). A digit only lowers |q| inside its square: the sign, hence the boundaries, do not change. The boundaries are fitted by a regular comb x_k = a0 + square x k (as the ruler ticks), so that the square length is measured over the whole scale; the end squares (no sign change against the card or the background) are added when their sign continues the alternation. Same result fields as analyze_pattern.

- **`Scale`** — class, line 760  
  A scale found (or given): px/cm, number of squares, length, angle, outline in the photo (poly), enlarged zone (holder, putty), straightened crop and its matrix M, reading details (pattern), note, doubts and kind (checkerboard, ruler, manual, learned).

- **`_rect_axis(rect)`** — function, line 782  
  Angle of the long side of a rotated rectangle (radians, -pi/2..pi/2), and its long and short sides.

- **`_single_row_groups(ink)`** — function, line 796  
  Single-row scale: its black squares do not touch. Looks for solid blobs of the same size, aligned and evenly spaced. Returns lists of points.

- **`_card_side(crop, res)`** — function, line 839  
  Single-row scale ending with a white square: side where the card continues (-1 left, +1 right, 0 undecided). Each end is compared with the white of the inner white squares of the scale.

- **`_scale_on_dark(rgb, small, f, forced_cm)`** — function, line 874  
  Dark background (black velvet): the black squares merge with the background. The scale is looked for from its light squares: for each large, elongated group of light areas, everything outside the rectangle around it (and beyond the photo edge) is painted white, so that the scale looks as it does on a light background; then the usual detection runs (without the ruler).

- **`_glyph_vector(g)`** — function, line 966  
  Sign cropped to its box, scaled into GLYPH_SIZE x GLYPH_SIZE, centred, zero mean, unit norm.

- **`_glyph_templates_get()`** — function, line 982  
  Templates of GLYPH_CHARS drawn with the fonts of Windows (empty list when none is found).

- **`digits_upside_down(crop, res)`** — function, line 1004  
  Is the scale of this straightened crop upside down, judging from the signs printed in its squares ("5", "10", "cm")? Each sign (dark ink in a light square, light ink in a dark or red one) is compared with templates of digits and of "c", "m" drawn with common fonts, as it is and turned over (180 degrees): the side that looks more like a printed character gets the vote of the sign, when the difference exceeds GLYPH_MARGIN. Returns True / False, or None when undecided (no clear sign, no font). Used on the final crop, once the red row is on top: on 1,265 scales of known orientation, no error (2 % undecided at a margin of 0.05, 0.08 is used).

- **`manual_scale_entry(path)`** — function, line 1052  
  Scale given by hand for this photo (interface: "Set scale…"), or None. The file MANUAL_SCALES, in the folder of the photo, maps a photo name to {"p1": [x, y], "p2": [x, y], "cm": length between the two points, "width_cm": width of the scale}; coordinates in pixels of the upright photo.

- **`manual_scale(rgb, entry)`** — function, line 1074  
  Scale from two points of known distance: px/cm = distance / length. The scale layer is a band of the given width around the segment, straightened like a detected scale; centimetre marks every cm.


#### Site profiles and learned scales

- **`find_profile(path, given)`** — function, line 1115  
  Profile of a photo: the file given (--profile), else PROFILE_FILE in the folder of the photo.

- **`load_profile(file)`** — function, line 1126  
  {"name", "background": "auto"|"light"|"dark", "learned_first": bool, "scales": [model...]}; models ready for matching (cached per process). A model: {"name", "cm", "width_cm", "px_cm", "image": PNG in base64}. learned_first: the learned scales are looked for before the usual detection (by default only when it fails or is doubtful: a learned 10 cm scale is also found inside a 20 cm one of the same make).

- **`learn_scale(rgb, entry, name)`** — function, line 1153  
  Model of a scale from two points of known distance on a photo (entry as manual_scale): the band of the scale between the two points, straightened, kept LEARN_LEN pixels long, and its px/cm.

- **`detect_learned_scale(rgb, models)`** — function, line 1167  
  Looks for the learned scales on the photo. Coarse: points matched between each model and the photo (SIFT), one position, size and angle agreed by RANSAC; fine: the model correlated with the photo (ECC, affine) refines the length to better than 0.1 % when it is the same physical scale. The best model (correlation) gives two points at its ends: the scale is then built as a manual one.

- **`detect_scale(rgb, small, f, forced_cm, dark, min_ratio, ruler, comb)`** — function, line 1224  
  comb: also try the second reading (analyze_comb) when the usual one finds nothing;
  
  "only": the second reading alone.


#### Graduated ruler (millimetre ticks on a light card)

- **`_thin_ticks(grey)`** — function, line 1384  
  Thin, elongated dark strokes (graduations): list of (cx, cy, theta, length).

- **`_tick_combs(ticks, long_ticks)`** — function, line 1404  
  Groups parallel strokes lying side by side and evenly spaced (graduations). long_ticks: grid cell sized on the longest strokes instead of the 95th percentile of all of them (long graduations among many short strokes of a sherd surface: neighbours further apart).

- **`_peaks(profile, step)`** — function, line 1485  
  Local maxima of a profile, at least 0.55 step apart, sub-pixel position.

- **`analyze_ruler(crop, step_estimate, robust)`** — function, line 1503  
  Straightened crop: horizontal ruler, vertical graduations.
  
  Returns the measurement (millimetre step, centimetre ticks) or None. robust (second pass): the band of the ticks is measured against the 90th percentile of the row densities instead of their maximum, and short dips are crossed (thick ticks hanging from the card edge: the top rows, darker, and a light line under the edge, would make the band a few rows).

- **`ruler_outline(crop, res)`** — function, line 1605  
  Edges of the ruler card (straightened crop, graduations at the top).

- **`detect_ruler(rgb, robust)`** — function, line 1666  
  Ruler graduated in millimetres: measures the millimetre step over the whole length.
  
  Returns a Scale, or None when no ruler is found. robust: second pass (thick, long ticks: _tick_combs(long_ticks) and analyze_ruler(robust)), used when the first one finds nothing.


#### Ceramic outlining

- **`poly_mask(shape, poly, aa)`** — function, line 1741  
  Mask of a polygon (sub-pixel coordinates), anti-aliased or not.

- **`discard_labels(keep, lab, stats, f, scale, dark)`** — function, line 1749  
  Discards what is not ceramic (modifies `keep`):
  
        * what lies entirely on the other side of the scale from the main object
          (labels, notes placed under the ruler);
        * elements that are nowhere thicker than ~1.7 mm (felt-pen writing, printed lines
          of a bag, threads) or that are very long and narrow (lines);
        * small isolated elements, far from the object (thick letter on a label or a bag), except on a
          dark background (a dark letter does not stand out there: what does is a small sherd).
  Returns the outlines (image frame) of the small isolated elements discarded.

- **`translucent_supports(obj, d_small, dl_small, db_small, cm_small)`** — function, line 1802  
  Plexiglass (translucent) supports: regions whose colour stays close to the background colour (distance < SUPPORT_T, whereas the ceramic differs clearly), at least 0.015 cm² in area, which stick out of the object (at least half of their perimeter on the background or an opening). A reflection of the background on a black gloss also has the background colour, but it runs along the ceramic, it is clearly darker and of the same hue; a support is as light as the background, or whiter than it (lavender background). Returns their mask (low resolution) or None.

- **`colour_chart(lab, m, sector_px)`** — function, line 1838  
  Colour chart (Pantone colorimeter, ColorChecker...): its saturated pixels (chroma > CHART_CHROMA) cover at least CHART_HUES hue sectors of 30° (each one at least `sector_px` pixels, i.e. CHART_SECTOR), among the warm hues (red, orange, yellow, magenta), the greens and the blues alike. A ceramic, even glazed or painted, stays within a few neighbouring hues (2 sectors at most over 1763 photos, against 5 to 9 for the charts). Returns None (not a chart), "alone" (regular, convex outline: the chart only) or "attached" (irregular outline: the chart touches something else, e.g. the ceramic).

- **`chart_disc(lab, m)`** — function, line 1859  
  Circle of a round colour chart (Pantone colorimeter) inside the mask m, fitted on its printed inks whose hue is foreign to ceramics (pinks, yellows, greens, blues: chroma > 40, hue outside 30-90°). Algebraic circle fit (x² + y² + Dx + Ey + F = 0, least squares), refitted on the points of the coloured ring; the inks must surround the centre (at least 20 of 36 sectors of 10°: under a warm light the yellow turns orange and joins the excluded hues) and the disc must be filled by the mask. Returns (cx, cy, r) in the frame of m, or None.

- **`remove_charts(obj, lab_small, bg_small, f, cm_small)`** — function, line 1890  
  Removes the colour charts from the analysis mask `obj` (in place): a chart alone is discarded whole; a round chart touching the ceramic is cut out along its circle, together with its cast shadow (the chart is a thick disc). Shadow = pixels of the object having the colour of the background darkened (a* and b* of the background scaled by the lightness ratio, distance < SHADOW_T), within 1.6 radius, connected to the edge of the disc. Returns the outlines to show (image frame), the circles cut out (polygons, image frame, also applied at full resolution) and whether a chart touching the ceramic could not be separated.

- **`label_card(lab_small, m, origin)`** — function, line 1965  
  Paper label on a dark background: white (L* >= LABEL_L), uncoloured (chroma <= LABEL_C) - or bluish (paper with optical brighteners: b* < 0, chroma <= LABEL_BLUE_C), or very bright (L* >= LABEL_BRIGHT_L, chroma <= LABEL_BRIGHT_C: pale yellow note) - and rectangular (it fills at least LABEL_FILL of its minimum-area rectangle). A pale sherd is warm (b* > 0), darker, or not that rectangular. Very rectangular (LABEL_SQUARE_FILL) and light (L* >= LABEL_SQUARE_L): a label of any colour (sticky note) - a broken sherd never fills its rectangle that much.

- **`straight_outline(m, origin, size)`** — function, line 1988  
  Share of the outline of a piece (away from the photo border) made of long straight sides parallel or perpendicular to its main direction: near 1 for a scale bar, a ruler, a label or a chart (even L-shaped), lower for a broken sherd, a coin or a tool. The outline is closed first, so that the ticks of a ruler or the squares of a scale make a straight side. Returns (that share, how much of its minimum-area rectangle the closed outline fills).

- **`printed_element(lab_small, m, origin, size)`** — function, line 2019  
  A scale bar, ruler, label or colour card, recognised without measuring it (no scale found): straight-sided, and the content of a print (see PRINT_*).

- **`split_labels(obj, lab_small, f)`** — function, line 2042  
  Dark background: a paper label touching an object by a narrow join (a corner, a point) forms
  
  one blob with it, neither label-coloured nor rectangular. Each blob that is not a label as a whole is cut at its narrow joins (opening, disc of 2 % of its size); a part that is a label is removed from the mask. Returns the mask and the outlines of the labels removed (photo coordinates).

- **`edge_at_half_contrast(m, d, depth)`** — function, line 2073  
  Dark background: the edge of a light object is a ramp several pixels wide (blur, shadow at its
  
  foot), and the threshold LOW_T keeps it almost down to the dark background (dark outline). In the outer band of the mask (depth pixels), the pixels whose distance to the background is under half that of the object nearby are removed, peeled from the outside only: the edge goes to the middle of the ramp. Dark areas inside the object (decoration) are not reached; where the object is hardly different from the background, LOW_T stays the threshold.

- **`outline_ceramic(photo, small, f, background, scale, ai)`** — function, line 2097  
  The cut-out of the object(s): first mask on the reduced photo (colour distance to the background, hysteresis, holes filled), sorting of the pieces (scale zone, labels, supports, colour charts, isolated elements), refinement at full resolution, edge softened. Returns the alpha mask and what was discarded (see PSEUDOCODE §10).

- **`find_putty(rgb, cer, px_cm)`** — function, line 2320  
  Looks for a visible support (mounting putty) attached to the ceramic.
  
  A part of the outline is a candidate only if:
  
        * it separates from the rest at two concavities of the outline (straight cut between them);
        * it is clearly smoother than the ceramic (texture < 50 %);
        * its colour differs (Delta E > 6), it is less saturated (chroma < 80 %) and lighter.
  The pixels stay in the PSD layer: only the layer mask changes. Returns (cer without the putty, removed polygons in image coordinates, area in cm²).


#### AI second opinion (optional, --ai): neural segmentation of the object

- **`ai_model_path(model)`** — function, line 2440  
  Model file, in the 'models' folder next to the script; downloaded the first time (checked with its MD5 sum).

- **`ai_providers(device, model)`** — function, line 2466  
  Graphics card when onnxruntime offers one (CUDA, or DirectML on Windows), else the processor. BiRefNet (1 GB) is too large for DirectML on an 8 GB card: it fails, or crawls in shared memory; it only uses CUDA.

- **`_ai_open(model, providers, jobs)`** — function, line 2477  
  Opens an ONNX model with onnxruntime (graphics card or processor), threads shared by the photos processed in parallel.

- **`ai_mask(rgb, opts)`** — function, line 2490  
  Object probability (0-255, AI_SIZE x AI_SIZE) for the whole photo, as in rembg: photo resized to 1024 x 1024 (Lanczos), values divided by their maximum, centred and scaled (mean, standard deviation of the network), network, sigmoid (BiRefNet), stretched to 0-1. On a failure of the graphics card (lack of memory), the processor takes over.


#### One-click cut-out (review window): Segment Anything, MobileSAM version

- **`click_model_path(part, progress)`** — function, line 2531  
  File of the one-click model, in the 'models' folder; downloaded the first time (SHA-256 checked).

- **`ClickCutout`** — class, line 2554  
  Cut-out of the object the archaeologist clicks on. Segment Anything is told WHICH object to cut out (a click on it; a click with "remove" on what must not be kept): it no longer has to guess what is a sherd and what is a label, a shadow or the background, hence a more reliable result than the automatic way on difficult photos. Its own edge is coarse (it sees the photo at 1024 px): where the computed cut-out agrees with it, the edge of the computed cut-out is kept.

  - **`__init__(self, progress)`** — method, line 2561  
    Loads the two parts of MobileSAM (image encoder, mask decoder); downloads them the first time.

  - **`set_image(self, rgb)`** — method, line 2572  
    Encodes the photo once (about a second); the clicks are then instant.

  - **`mask(self, points, out_size)`** — method, line 2580  
    Mask (bool) of the object for points [(x, y, keep)] in photo pixels; out_size (h, w) of the mask, by default the photo's.

- **`click_refine(sam, computed, band)`** — function, line 2599  
  Edge of the clicked object: the computed cut-out where it agrees with Segment Anything (within
  
  `band` pixels of its edge), Segment Anything elsewhere (object missed by the computed cut-out).


#### Layers and compositing

- **`Layer`** — class, line 2622  
  One layer of the output files: name, position on the canvas, pixels, mask (or None),
  
  visible or hidden.

- **`extract(rgb, x0, y0, x1, y1)`** — function, line 2633  
  Crop, filled with white where the area goes beyond the image.

- **`composite(layers, W, H)`** — function, line 2643  
  Merges the visible layers (non-premultiplied rgb + alpha) over a transparent background.

- **`decontaminate_edge(rgb, mask, band)`** — function, line 2667  
  Dark background: the pixels of the edge (the half-transparent ones and the last `band` pixels
  
  inside) mix the colour of the object with the dark background: a thin dark line around the sherd, whatever the cut-out. Their colour is replaced by the colour of the object just inside (normalised Gaussian average of the inner pixels), where it is lighter - the outline (mask) is not changed.

- **`layout(photo, cer, scale, opts)`** — function, line 2697  
  Builds the layers of the output files: the object with its mask, the scale (straightened under the object, or where it was photographed), the whole photo (hidden layer); sizes of the canvas with the margins. Returns the layers of the PSD and those of the TIFF alone.


#### PSD writing (layers, layer masks, resolution, ICC profile, EXIF)

- **`_packbits_block(a)`** — function, line 2782  
  PackBits compression (the RLE of Photoshop) of a block of rows, vectorised with numpy.

- **`packbits(a, block)`** — function, line 2822  
  PackBits compression of a whole channel, block by block; returns the row lengths and data.

- **`rle_channel(a)`** — function, line 2833  
  A channel as Photoshop stores it: compression flag 1 (RLE), row lengths, data.

- **`_pascal(b, multiple)`** — function, line 2839  
  Pascal string (length byte + text), padded, as in the PSD format.

- **`_resource(rid, data)`** — function, line 2845  
  PSD image resource block ("8BIM", id, data padded to an even length).

- **`_unicode(s)`** — function, line 2851  
  Unicode string of the PSD format (length + UTF-16 big-endian).

- **`_xml(s)`** — function, line 2856  
  Escapes &, < and > for XML.

- **`iptc_values(pr, values, name)`** — function, line 2886  
  IPTC fields of a photo: the mapping of the project (else DEFAULT_IPTC) filled with its values.

- **`_iptc_prop(prop, kind, value)`** — function, line 2906  
  One XMP property as RDF: plain text, one-language alternative (Alt) or list (Bag/Seq).

- **`make_xmp(description, fields, meta, title, iptc, packet)`** — function, line 2916  
  XMP packet: description of the scale + shooting information of the original photo + information of
  
  the project (title = output name; each field as gerbil:Name, and all of them as keywords) + the IPTC fields of the project (iptc_values), which take precedence. packet=False: no xpacket wrapper (sidecar .xmp file).

- **`embed_xmp_jpeg(path, xmp)`** — function, line 2966  
  Puts the XMP packet into a JPEG file without touching the image: the APP1 XMP segment is replaced or added after the EXIF / JFIF segments. False when the file is not a plain JPEG.

- **`write_sidecar(photo_path, xmp, folder)`** — function, line 2993  
  NAME.xmp beside a photo (Bridge, Lightroom, darktable read it, above all for RAW files). A sidecar written by another program (Lightroom: develop settings) is never replaced. Returns the path or None.

- **`write_psd(path, W, H, layers, comp_rgb, comp_a, dpi, icc, exif, xmp)`** — function, line 3009  
  Writes the layered Photoshop file byte by byte: header, resolution in cm, ICC profile, EXIF and XMP, layers with their masks (PackBits), flattened image. See PSEUDOCODE §13.


#### TIFF writing

- **`write_tiff(path, rgb, a, dpi, icc, xmp, fields, description, background, compression)`** — function, line 3094  
  Writes a TIFF (transparent or on white, LZW / ZIP / none) at the 1:1 resolution, with the ICC profile, the XMP and the main text tags.


#### Control preview

- **`font(size)`** — function, line 3124  
  A TrueType font for the texts of the control preview (Arial, Segoe UI, DejaVu...).

- **`control_image(path, photo, cer, scale, text_lines)`** — function, line 3134  
  The control preview (to_control): reduced photo, outline of the cut-out in green, scale in magenta with its marks, what was discarded in red, removed by the AI in cyan, and the main information written on top.


#### Processing of one photo

- **`output_paths(folder, base, doubtful)`** — function, line 3219  
  Paths of the files of a photo (PSD, TIFF, preview), with _to_be_verified when doubtful.

- **`remove_stale(folder, base, written)`** — function, line 3230  
  After a new run, deletes the obsolete variant (with / without "_to_be_verified") of the files that have just been rewritten.

- **`copy_original(path, folder)`** — function, line 3241  
  Copy of the original photo in the result folder; returns its path (None: same file).


#### Project: fields, naming template, naming rule, values of the photos (gerbil_project.json)

- **`load_project(folder)`** — function, line 3270  
  Project of a folder of photos, or None. Keys: fields (key, label, required, choices), template (e.g. "{site}_{us}_{number}"; empty: the names of the photos are kept), rule (regular expression the output names must match; empty: none), common (values of all the photos), photos (name -> values).

- **`photo_values(project, name)`** — function, line 3293  
  Values of a photo: those common to the project, completed / replaced by its own.

- **`project_name(project, name)`** — function, line 3301  
  Output name (without extension) built from the template, or None (template empty or giving nothing). Forbidden characters and spaces become "_"; the separators left by empty fields are merged ("{site}_{us}_{number}" without US: "QSR25_12").

- **`rule_regex(rule)`** — function, line 3315  
  The naming rule as PowerShell's -match reads it: .NET regular expression, case-insensitive, found anywhere in the name unless anchored with ^ and $. .NET named groups (?<name>...) are accepted, and (?-i) at the start makes the rule case-sensitive (as in PowerShell).

- **`project_checks(project, name, out_name)`** — function, line 3325  
  Reasons for doubt about the information of a photo: required fields empty, name off the rule.

- **`plan_names(tasks)`** — function, line 3346  
  Output name and information of every photo, decided before the processing: two photos of the same result folder cannot get the same name (a suffix _2, _3... is added, with a doubt).


#### Review window: data written for it, corrections read back

- **`edits_entry(path)`** — function, line 3382  
  Corrections made by hand for this photo: (mask or None, angle in degrees). The mask (full photo, 0 / 255) replaces the computed cut-out; the angle turns the object (counterclockwise).

- **`cutout_from_mask(mask, cer)`** — function, line 3405  
  Cut-out from a mask corrected by hand (photo size): same softened edge as outline_ceramic (Gaussian blur 0.8 px of the 0 / 255 mask). The other fields of `cer` are kept (or emptied).

- **`write_review(out_dir, path, shape, cer, scale, status, doubts, angle, output)`** — function, line 3429  
  Mask (photo size) and scale outline of the photo, for the review window of the interface.

- **`rotated_ceramic(rgb, cer, border, angle)`** — function, line 3449  
  The object turned by `angle` degrees (counterclockwise, as decided in the review window): pixels (bicubic) and layer mask (bilinear) resampled once. Returns rgb, mask (with `border` around the object), and the width and height of the turned object.

- **`process_photo(path, opts, out_dir, plan)`** — function, line 3475  
  plan: output name, doubts and information of the photo decided by plan_names (project).

- **`_init_worker()`** — function, line 3651  
  Each worker process limits OpenCV to 2 threads (photos are already processed in parallel).

- **`list_photos(inputs)`** — function, line 3660  
  Photos of the folders / files given. Gerbil's own results (NAME_outlined.tif, _to_control.jpg…) lying among the photos (result folder = photo folder) are left out: never processed again.

- **`_HelpFormatter`** — class, line 3682  
  Shows the default value only when it is meaningful.

  - **`_get_help_string(self, action)`** — method, line 3685  
    Help of an option: its default value shown only when it means
    
    something.

- **`main(argv)`** — function, line 3693  
  Command line: reads the options, lists the photos, plans their output names (batch
  
  renaming), processes them in parallel (process_photo), writes the report and prints the summary of the problems.

- **`previous_output(path, out_dir)`** — function, line 3810  
  Output name the photo had at its previous run (review data), or None.

- **`remove_renamed(tasks, plan, previous)`** — function, line 3820  
  Files of a photo written under a former output name (the project name changed): removed, unless another photo now uses that name.

- **`write_report(report, rows)`** — function, line 3834  
  CSV report (Excel: ";" separator, decimal comma). Rows already present for other photos are kept: the script can be run again on a few photos. The fields of the project come after the usual columns.

- **`print_summary(rows)`** — function, line 3861  
  What needs checking, grouped by problem, with the photos concerned (a photo may appear under several problems).

- **`print_row(row, i, n)`** — function, line 3885  
  One line of progress for a photo: [i/n] name: status (scale, time) | doubts and notes.

- **`_own_console()`** — function, line 3894  
  True when the program has a visible console to itself: .exe double-clicked, or folders dropped on it (not when the interface runs it, with its output redirected).


### gerbil_gui.pyw

The interface (windows) - it runs the engine as a separate program. (4059 lines.)

Gerbil - archaeological photo toolkit (formerly SherdCut): graphical interface of gerbil.py © 2026 Eloïs CHARBONNEL Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE. This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to redistribute it under the conditions of the licence.

Choose the photos (folders or files) and the options, then "Run": the script runs in the background and each processed photo shows up in the log. Double-click this file to open it; folders or photos dropped on it are added to the list.

Missing Python packages (numpy, OpenCV, Pillow, rawpy) are detected and can be installed from the window. Console use (Install.bat):  py -3 gerbil_gui.pyw --install   (or --check: exit code 1 if missing)

- **`open_photo_image(path, small)`** — function, line 46  
  The photo upright, as the engine sees it (RAW: developed by rawpy the same way; small: half size, for previews). Returns a PIL image in RGB.

- **`python_exe()`** — function, line 108  
  Console Python of the running installation (the GUI itself may run under pythonw).

- **`missing_packages()`** — function, line 114  
  Python packages still to install (none in the .exe version, where all is inside).

- **`has_ai()`** — function, line 122  
  True when onnxruntime (the AI engine) is available.

- **`pip_command(packages)`** — function, line 130  
  Command that installs packages with pip, for the Python found.

- **`imports_ok(modules)`** — function, line 135  
  Checked in a new process: a package just installed in the user folder is seen there.

- **`console_install()`** — function, line 142  
  Install.bat: installs what is missing, in the Python running this file.

- **`count_photos(folder)`** — function, line 176  
  Number of photos (known extensions) in a folder.

- **`load_settings()`** — function, line 184  
  Settings of the interface (~/.gerbil.json, or the files of older names), with the defaults for what is missing.

- **`Tooltip`** — class, line 198  
  Help text shown when the mouse rests on a widget. It goes away when the mouse leaves the widget (checked every 250 ms: a drop-down list or a window opened meanwhile can swallow the "leave" event), on a click, and after 8 s at most; one bubble at a time.

  - **`__init__(self, widget, text)`** — method, line 205  
    Ties the bubble to the widget: shown when the mouse rests on it, hidden on leave,
    
    click, focus lost or destruction.

  - **`_schedule(self, _)`** — method, line 215  
    The mouse enters: the bubble is shown after 450 ms.

  - **`_pointer_inside(self)`** — method, line 220  
    True when the mouse pointer is over the widget (or one of its children).

  - **`_show(self)`** — method, line 233  
    Shows the bubble under the widget, if the mouse is still there; one bubble at a time.

  - **`_watch(self)`** — method, line 251  
    Every 250 ms: hides the bubble when the mouse has left, or after 8 s.

  - **`_hide(self, _)`** — method, line 259  
    Hides the bubble and cancels what was planned.

- **`ScaleWindow`** — class, line 285  
  Manual scale of one photo: two points of known distance, clicked on the photo (upright as the
  
  engine sees it). Saved in MANUAL_SCALES next to the photo; the engine then uses it instead of looking for the scale.

  - **`__init__(self, app, path, seq, on_saved, learn)`** — method, line 292  
    seq: series of photos corrected one after the other (see App.scale_series), or None.
    
    on_saved: called after saving instead of offering to process the photo (review window).
    
    learn: called with the two points instead of saving a manual scale (site profile: learn a scale).

  - **`fit(self)`** — method, line 370  
    Whole photo in the window.

  - **`to_screen(self, x, y)`** — method, line 378  
    Photo pixel -> window position (zoom and offset of the view).

  - **`to_image(self, sx, sy)`** — method, line 382  
    Window position -> photo pixel.

  - **`redraw(self)`** — method, line 386  
    Draws the visible part of the photo, the two points, the line between them and the band of the scale.

  - **`values(self)`** — method, line 427  
    (px/cm, width cm) from the two points and the entries; px/cm None when not computable.

  - **`update_readout(self)`** — method, line 438  
    Text under the fields: distance in pixels, px/cm and ppi.

  - **`press(self, e)`** — method, line 448  
    Click: grabs a point near the click, or places a new point.

  - **`move(self, e)`** — method, line 461  
    Drag: moves the grabbed point.

  - **`pan_move(self, e)`** — method, line 468  
    Right button held: moves the view.

  - **`wheel(self, e)`** — method, line 475  
    Wheel: zoom on the point under the mouse.

  - **`_load(self)`** — method, line 482  
    Manual scales of the folder (gerbil_scales.json).

  - **`_write(self, data)`** — method, line 491  
    Writes the manual scales (aside, then swapped); the file of the old name goes.

  - **`save(self)`** — method, line 500  
    Saves the scale of the photo (or gives it to the profile when learning), then next photo of the series or offer to process it again.

  - **`skip(self)`** — method, line 537  
    Series: leaves this photo without a scale and goes to the next one.

  - **`close(self)`** — method, line 542  
    Close (single photo) or Stop (series: the photos already set may then be processed).

  - **`remove(self)`** — method, line 549  
    Removes the manual scale of the photo (the detection is used again).

- **`load_project_file(folder)`** — function, line 580  
  Project of a folder (dict), a new one if there is none; None if the file cannot be read.

- **`save_project_file(folder, pr)`** — function, line 598  
  Writes gerbil_project.json (written aside, then swapped: never half-written).

- **`project_values(pr, name)`** — function, line 607  
  Values of a photo: the common ones, replaced by its own.

- **`project_output_name(pr, name)`** — function, line 614  
  Output name of a photo (as gerbil.py: project_name), or its own name without a template.

- **`rule_regex(rule)`** — function, line 627  
  The naming rule as PowerShell's -match reads it: .NET regular expression, case-insensitive, found anywhere in the name unless anchored with ^ and $. .NET named groups (?<name>...) are accepted, and (?-i) at the start makes the rule case-sensitive (as in PowerShell).

- **`ps_escape(text)`** — function, line 647  
  Text taken literally in a .NET / PowerShell regular expression (as [regex]::Escape).

- **`build_rule(pieces, starts, max_len)`** — function, line 652  
  PowerShell rule made of look-aheads (each one tests the whole name), e.g. (?-i)^(?!.*[a-z])(?=QSR25)(?=.{1,40}$): case-sensitive when a piece needs it.

- **`read_table(path)`** — function, line 666  
  Rows (lists of strings) of a CSV file or of the first sheet of an Excel .xlsx file.

- **`FieldDialog`** — class, line 720  
  Adds or edits a field of the project: label, key (name used in the template), required, choices.

  - **`__init__(self, parent, field)`** — method, line 723  
    Small window to create or edit a field: label, key, required, choices.

  - **`ok(self)`** — method, line 753  
    Checks and returns the field (key made of letters, digits and _).

- **`ProjectWindow`** — class, line 768  
  Project of a folder of photos (gerbil_project.json next to them): fields, name template, naming rule, values common to all the photos, and a table with one row per photo (double-click a cell to edit it; several rows selected: "Set for selected", "Number the selected"); import of a CSV / Excel inventory. The output files of the photos take the names built from the template (the photos keep theirs).

  - **`__init__(self, app, folder)`** — method, line 774  
    The batch renaming window: fields, template, naming rule with its helper,
    
    common values, table of the photos with preview, buttons.

  - **`fields(self)`** — method, line 939  
    Fields of the project.

  - **`rebuild(self)`** — method, line 943  
    Fields changed: tokens, common values and columns of the table drawn again.

  - **`fill(self)`** — method, line 983  
    Fills the table: one row per photo, its values and its output name.

  - **`update_preview(self)`** — method, line 995  
    Example of output name, and warning when names are used twice.

  - **`changes(self)`** — method, line 1005  
    The template changed: output names computed again.

  - **`set_common(self, key, value)`** — method, line 1014  
    Sets a value common to all the photos.

  - **`headings(self)`** — method, line 1024  
    Column titles; a value common to all the photos is given in the title (the cells hold the values of each photo, which replace it).

  - **`set_value(self, name, key, value)`** — method, line 1036  
    Sets the value of a field for one photo (table and project).

  - **`ext_changed(self)`** — method, line 1051  
    "Extension in lowercase" ticked or not.

  - **`ext_feedback(self)`** — method, line 1057  
    Number of photos whose extension has capitals.

  - **`helper_changed(self)`** — method, line 1067  
    Ticked pieces -> rule written in the rule field (it can still be edited by hand).

  - **`rule_feedback(self)`** — method, line 1076  
    The rule as a PowerShell line, and the result for the name to test (or the first output name).

  - **`show_thumb(self)`** — method, line 1092  
    Small view of the photo of the selected row (the first one).

  - **`render_thumb(self)`** — method, line 1112  
    The preview fitted to the space it has (it follows the bar between table and preview).

  - **`after_resize(self)`** — method, line 1126  
    Preview redrawn a moment after the window is resized.

  - **`open_photo(self)`** — method, line 1132  
    Opens the selected photo in the Windows viewer.

  - **`select_all(self)`** — method, line 1138  
    Selects all the rows (Ctrl+A).

  - **`cell_clicked(self, e)`** — method, line 1142  
    Click in the table: the cell becomes the active one (fill handle).

  - **`place_handle(self)`** — method, line 1150  
    The small square at the bottom right corner of the active cell (fill handle, as in Excel).

  - **`fill_start(self, e)`** — method, line 1165  
    The fill handle is grabbed (Ctrl: numbering).

  - **`fill_move(self, e)`** — method, line 1169  
    Dragging the fill handle: rows covered, table scrolled at its edges.

  - **`fill_end(self, e)`** — method, line 1186  
    Handle released: the value copied (or numbered) into the rows covered.

  - **`fill_down(self)`** — method, line 1204  
    Ctrl+D: the values of the first selected row copied to the other selected rows (the active column only when a cell is active, else all the fields).

  - **`edit_cell(self, e)`** — method, line 1220  
    Double-click: edits the cell in place (entry or list of choices).

  - **`_ask_field(self, title, with_value, with_start)`** — method, line 1246  
    Small dialog: a field, and a value (or a start number and a step).

  - **`set_selected(self)`** — method, line 1283  
    Same value for the selected photos.

  - **`number_selected(self)`** — method, line 1295  
    Numbers the selected photos (start, step, zeros).

  - **`add_field(self)`** — method, line 1314  
    Adds a field.

  - **`_pick_field(self, title)`** — method, line 1325  
    Asks which field to act on.

  - **`edit_field(self)`** — method, line 1330  
    Edits a field (its values follow a key change).

  - **`remove_field(self)`** — method, line 1346  
    Removes a field and its values.

  - **`import_table(self)`** — method, line 1356  
    Imports values from a CSV or Excel inventory: matched with the photos by name, columns matched with the fields.

  - **`save(self, run)`** — method, line 1406  
    Checks the rule and saves gerbil_project.json (then processes, if asked).

  - **`close(self)`** — method, line 1426  
    Closes, offering to save the changes.

- **`ReviewWindow`** — class, line 1440  
  Review and correction of the cut-outs, photo by photo (doubtful ones first): the photo with the outline of the cut-out (green) and of the scale (magenta); erase / add brushes, removal of a whole piece by a click, undo; orientation of the object (a line along its rim, or quarter turns); access to the manual scale. The corrections are saved next to the photos (EDITS_DIR), so that a later run keeps them; the corrected photos are then processed again.

  - **`__init__(self, app, items)`** — method, line 1451  
    The review window: list of photos, view, tools, orientation, information,
    
    buttons; keyboard and mouse bindings.

  - **`goto(self, i)`** — method, line 1557  
    Shows photo i: its cut-out (or the corrections saved before), its angle, its
    
    information; resets the undo history.

  - **`show_info(self)`** — method, line 1616  
    Fields of the project of the photo, with its own values (the values common to all photos are given as a hint).

  - **`save_info(self)`** — method, line 1641  
    Saves the information typed for the photo shown in its project; True when changed.

  - **`fit(self)`** — method, line 1665  
    Whole photo in the view. Done again once the window has its real size (at the opening the canvas is still 1 x 1 pixel: the first photo would stay invisible).

  - **`to_screen(self, x, y)`** — method, line 1675  
    Photo pixel -> window position.

  - **`to_image(self, sx, sy)`** — method, line 1679  
    Window position -> photo pixel.

  - **`view_base(self)`** — method, line 1683  
    The photo as shown for the current view (cached: only rebuilt when the view changes).

  - **`redraw(self, fast)`** — method, line 1710  
    Photo (cached) + cut-out (background dimmed, green outline) + scale outline + line / lasso.

  - **`schedule_redraw(self)`** — method, line 1749  
    At most one redraw every 30 ms while painting (the mask itself is updated at once).

  - **`wheel(self, e)`** — method, line 1755  
    Wheel: zoom on the point under the mouse.

  - **`pan_move(self, e)`** — method, line 1762  
    Moves the view while a button is held.

  - **`view_span(self, axis)`** — method, line 1769  
    Visible part of the photo along an axis: (start, length) in photo pixels.

  - **`scroll_view(self, axis, *args)`** — method, line 1774  
    Scroll bar commands: "moveto f" or "scroll n units|pages".

  - **`nudge(self, dx, dy)`** — method, line 1791  
    Arrow keys: moves the view.

  - **`update_bars(self)`** — method, line 1798  
    Scroll bars set to the visible part of the photo.

  - **`hover(self, e)`** — method, line 1804  
    Circle of the brush under the mouse.

  - **`tool_changed(self)`** — method, line 1813  
    Tool chosen: the one-click model is prepared when it is chosen.

  - **`prepare_click(self)`** — method, line 1821  
    Loads the model (downloaded once, 45 MB) and encodes the photo shown, in the background.

  - **`click_prepared(self, index, error)`** — method, line 1845  
    The photo is ready for one-click (or the error is shown).

  - **`show_click_hint(self)`** — method, line 1860  
    How the one-click tool is used.

  - **`click_object(self, x, y, keep)`** — method, line 1865  
    One click: the object under the click (Segment Anything, edge of the
    
    computed cut-out where it agrees) is added (or removed with Shift).

  - **`_save_patch(self, x0, y0, x1, y1, before)`** — method, line 1890  
    Keeps the part of the mask about to change, for Undo (30 steps).

  - **`typing(self)`** — method, line 1898  
    A text field of the panel has the keyboard: Space and the arrows are for it.

  - **`press(self, e)`** — method, line 1903  
    Mouse pressed: starts the brush, the lasso, the line, or acts at once (piece,
    
    one click); Space held: moves the view.

  - **`drag(self, e)`** — method, line 1928  
    Mouse moved with the button held: paints, extends the lasso or the line.

  - **`_paint(self, ax, ay, bx, by)`** — method, line 1950  
    Paints (or erases) a stroke of the brush in the mask.

  - **`release(self, e)`** — method, line 1958  
    Button released: ends the stroke, fills the lasso, or turns the object along
    
    the line drawn.

  - **`rim_angle(self, ax, ay, bx, by)`** — method, line 1988  
    Rotation (degrees, counterclockwise) that makes the line horizontal with the object below it.

  - **`turn(self, step)`** — method, line 2001  
    Quarter turn of the object (or back to 0).

  - **`undo(self)`** — method, line 2007  
    Undoes the last change of the mask or of the angle.

  - **`reset(self)`** — method, line 2022  
    Undoes all the unsaved changes of this photo; if corrections were saved for it before, offers to remove them too (the computed cut-out comes back when the photo is processed again).

  - **`remove_saved(self, photo)`** — method, line 2041  
    Removes the corrections saved for a photo.

  - **`update_thumb(self)`** — method, line 2058  
    The object as it will be exported (turned), small.

  - **`list_text(self, it)`** — method, line 2081  
    Text of a photo in the list: status mark, name, export state.

  - **`mark(self, photo, state)`** — method, line 2087  
    Changes the export state shown for a photo.

  - **`saved_mask_file(photo)`** — method, line 2099  
    Path of the corrected mask of a photo (gerbil_edits).

  - **`saved_entry(photo)`** — method, line 2104  
    Corrections saved for a photo (mask corrected?, angle).

  - **`export(self, photo)`** — method, line 2112  
    The photo is processed again in the background as soon as its corrections are saved: the results and the previews are up to date without going through all the photos.

  - **`pump(self)`** — method, line 2119  
    Starts the waiting exports once the main window is free (one run at a time, all those waiting).

  - **`save_current(self)`** — method, line 2134  
    Saves the corrections of the photo shown (EDITS_DIR next to the photo); True when changed.

  - **`accept(self)`** — method, line 2169  
    Saves the corrections of the photo, exports it again, shows the next one.

  - **`fix_scale(self)`** — method, line 2181  
    Opens the manual scale of the photo.

  - **`close(self)`** — method, line 2189  
    Closes, offering to keep the corrections of the photo shown.

- **`PlatesWindow`** — class, line 2209  
  Plates of a results folder (gerbil_plates): objects at a chosen scale on pages, captions, graphic scale bar in the manner of QGIS; live preview of the pages; written as SVG (Illustrator, Inkscape). The settings are remembered (house style of the scale bar).

  - **`__init__(self, app, folder)`** — method, line 2214  
    The plates window: three tabs of settings (plate, scale bar, scales and
    
    drawings), live preview with zoom, buttons.

  - **`object_scales(self)`** — method, line 2448  
    Small window: each object with its size and its scale (plate scale, or one chosen for it).

  - **`wheel(self, e)`** — method, line 2503  
    Zoom on the point under the mouse (1 = whole page, up to 8).

  - **`object_menu(self, e)`** — method, line 2518  
    Right-click on an object of the preview: a menu of scales for it (kept in the plate settings).

  - **`pick_drawings(self)`** — method, line 2552  
    Chooses the folder of the drawings.

  - **`colour_button(self, parent, key, value, text)`** — method, line 2559  
    A colour swatch that opens the colour chooser.

  - **`settings(self)`** — method, line 2578  
    PlateSettings from the window (invalid numbers keep their previous value).

  - **`changed(self)`** — method, line 2613  
    A setting changed: preview drawn again a moment later.

  - **`thumb(self, item, w_mm, h_mm)`** — method, line 2619  
    Reduced image of an object for the preview (cached).

  - **`refresh(self)`** — method, line 2632  
    Lays out the plates with the current settings and draws the page shown.

  - **`turn(self, step)`** — method, line 2676  
    Previous / next plate.

  - **`write(self)`** — method, line 2682  
    Writes the SVG plates in a thread.

  - **`written(self, text)`** — method, line 2699  
    Plates written: message, settings saved.

  - **`open_folder(self)`** — method, line 2706  
    Opens the folder of the plates.

  - **`close(self)`** — method, line 2712  
    Closes, saving the plate settings (house style).

- **`profile_names()`** — function, line 2725  
  Names of the site profiles of the library.

- **`profile_path(name)`** — function, line 2733  
  File of a profile of the library.

- **`safe_name(name)`** — function, line 2738  
  A name usable as a Windows file name.

- **`ProfileWindow`** — class, line 2743  
  Site profile: what is known of the photos of a site or a campaign (background, learned scales,
  
  options), chosen once in the main window instead of setting everything again. Saved in PROFILES_DIR; "Put next to the photos…" copies it as gerbil_profile.json into a folder of photos, where the engine uses it by itself (and the team can share it).

  - **`__init__(self, app, name)`** — method, line 2749  
    The site profile window: name, background, learned scales, options.

  - **`fill(self)`** — method, line 2818  
    List of the learned scales and summary of the options kept.

  - **`learn(self)`** — method, line 2827  
    Chooses a photo showing the scale and opens the scale window in learning mode.

  - **`learned(self, path, entry)`** — method, line 2836  
    Learns the scale from the two points given (engine.learn_scale).

  - **`remove_scale(self)`** — method, line 2848  
    Removes a learned scale.

  - **`take_options(self)`** — method, line 2855  
    Keeps the options of the main window in the profile.

  - **`data(self)`** — method, line 2861  
    The profile as saved.

  - **`save(self)`** — method, line 2867  
    Saves the profile in the library and chooses it.

  - **`export(self)`** — method, line 2879  
    Writes the profile as gerbil_profile.json in a folder of photos.

- **`IptcWindow`** — class, line 2891  
  IPTC fields of the batch renaming: for each IPTC Core field, a text where {field} is replaced by the value of the photo and {name} by the output name (a text without braces: the same for all, e.g. the copyright). Written into the PSD / TIFF, the copy of the original and, if ticked, a .xmp file next to each original photo.

  - **`__init__(self, project)`** — method, line 2897  
    The IPTC window: one text per IPTC field, sidecar option, example.

  - **`mapping(self)`** — method, line 2937  
    The IPTC fields filled in.

  - **`preview(self)`** — method, line 2941  
    Example of the IPTC values of the selected photo.

  - **`default(self)`** — method, line 2954  
    Default model.

  - **`ok(self)`** — method, line 2959  
    Keeps the IPTC settings in the project.

- **`InventoryWindow`** — class, line 2967  
  Inventory of documentation folders as CSV (gerbil_tools.inventory), with the PowerShell line that does the same, shown for learning.

  - **`__init__(self, app)`** — method, line 2971  
    The inventory window: folders, kinds of files, fields of the names,
    
    PowerShell line.

  - **`add(self)`** — method, line 3041  
    Adds a folder.

  - **`chosen(self)`** — method, line 3048  
    Folders and kinds of files chosen.

  - **`out_path(self)`** — method, line 3052  
    Default path of the CSV.

  - **`update_line(self)`** — method, line 3057  
    PowerShell line updated.

  - **`write(self)`** — method, line 3065  
    Writes the inventory and opens it.

- **`ThumbnailsWindow`** — class, line 3085  
  Thumbnails in batch (gerbil_tools.thumbnails) for databases.

  - **`__init__(self, app)`** — method, line 3088  
    The thumbnails window: folder, size, format.

  - **`browse(self)`** — method, line 3126  
    Chooses the folder.

  - **`run(self)`** — method, line 3132  
    Makes the thumbnails in a thread.

  - **`done(self, folder, n)`** — method, line 3151  
    Thumbnails made: message, folder opened.

- **`App`** — class, line 3158  
  The main window: list of photos, options, Run, log; it starts the engine and opens the
  
  other windows (batch renaming, scale, review, plates, profiles, tools).

  - **`__init__(self, root, paths, selftest)`** — method, line 3161  
    The main window: settings, styles, widgets, checks of the packages.

  - **`_icon(self)`** — method, line 3194  
    The purple gerbil: window icon, and picture of the header (size following the screen scaling).

  - **`_style(self)`** — method, line 3209  
    Colours and fonts of the widgets (ttk styles).

  - **`_build(self)`** — method, line 3261  
    Builds the main window: header, photos, options, Run, log.

  - **`_photos_card(self, parent)`** — method, line 3347  
    Card of the photos: buttons, list, results folder, site profile.

  - **`apply_profile(self)`** — method, line 3412  
    The options kept in the chosen profile are set in the window.

  - **`profiles_changed(self, name)`** — method, line 3428  
    List of profiles updated, the profile saved chosen.

  - **`_options_card(self, parent)`** — method, line 3434  
    Card of the options (files, run, scale and layout, cleaning, AI).

  - **`_ai_ticked(self)`** — method, line 3519  
    AI ticked: offers to install onnxruntime when missing.

  - **`check_packages(self)`** — method, line 3531  
    Banner and Run button according to the required packages.

  - **`install_required(self)`** — method, line 3547  
    Installs the missing packages (pip, in the background).

  - **`_sync(self)`** — method, line 3552  
    Enables the options that depend on another one.

  - **`add_paths(self, paths)`** — method, line 3565  
    Adds folders / photos to the list (with their number of photos).

  - **`add_folder(self)`** — method, line 3584  
    Adds a folder of photos.

  - **`add_files(self)`** — method, line 3590  
    Adds photos.

  - **`project(self)`** — method, line 3598  
    Project of the folder selected in the list (or of the folder of the photo selected).

  - **`set_scale(self)`** — method, line 3615  
    Manual scale of one photo: the photo selected in the list, otherwise one to choose.

  - **`scale_series(self, paths)`** — method, line 3634  
    Manual scales of several photos, one window after the other; the photos whose scale was saved can then be processed again in one run.

  - **`next_scale(self, seq)`** — method, line 3639  
    Series of manual scales: opens the next photo.

  - **`remove(self)`** — method, line 3656  
    Removes the selected rows of the list.

  - **`clear(self)`** — method, line 3662  
    Empties the list.

  - **`pick_output(self)`** — method, line 3667  
    Chooses the results folder (not a folder of photos).

  - **`_collect(self)`** — method, line 3681  
    Reads the options; returns the command-line arguments (only what differs from the defaults).

  - **`save_settings(self)`** — method, line 3738  
    Saves the settings of the interface.

  - **`run(self, inputs, quiet)`** — method, line 3748  
    Processes the photos of the list (or the given ones: a photo whose scale was just set, photos corrected in the review window). quiet: no question at the end (exports of the review window).

  - **`_start(self, cmd, kind)`** — method, line 3780  
    Runs the script ("script") or pip ("pip": required packages, "pip-ai": onnxruntime).

  - **`_stop_bar(self)`** — method, line 3805  
    Stops the moving progress bar.

  - **`_reader(self, proc)`** — method, line 3811  
    Thread reading the output of the engine line by line (into a queue).

  - **`_poll(self)`** — method, line 3818  
    Every 100 ms: handles the lines received; end of the process detected.

  - **`_handle(self, line)`** — method, line 3835  
    One line of the engine: progress, coloured log, results folder, photos to set by hand.

  - **`_summary(self)`** — method, line 3874  
    "12 ok, 3 to verify, 1 failed".

  - **`_finished(self)`** — method, line 3883  
    End of a run: status, offers (manual scales), self-test file.

  - **`cancel(self)`** — method, line 3933  
    Stops the processing (the whole process tree).

  - **`review(self)`** — method, line 3942  
    Review window over the result folders of the last run (or a result folder to choose).

  - **`plates(self)`** — method, line 3979  
    Plates window over a results folder (the last one processed, or one to choose).

  - **`open_results(self)`** — method, line 3993  
    Opens the results folders.

  - **`help(self)`** — method, line 3999  
    Opens the README.

  - **`close(self)`** — method, line 4004  
    Closes (stops a run first, if wanted) and saves the settings.

  - **`_log(self, text, tag)`** — method, line 4018  
    Adds a text to the log, in a colour.

  - **`_clear_log(self)`** — method, line 4025  
    Empties the log.

- **`main()`** — function, line 4032  
  Entry of the interface: --install / --check for Install.bat, --selftest, or the window.


### gerbil_plates.py

The plates: objects laid out at a chosen scale, written as SVG. (1050 lines.)

Gerbil - plates: the outlined objects of a results folder laid out on pages at a chosen scale (1:1, 1:2, 1:3...), written as SVG files that open in Illustrator or Inkscape. © 2026 Eloïs CHARBONNEL Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE. This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to redistribute it under the conditions of the licence.

Each object keeps its true size at the plate scale (read from the resolution of its _outlined.tif, which is 1:1). The objects are placed in rows, in the chosen order, with a caption under each one (its name, or the fields of the batch renaming) and a graphic scale bar on every page. The images are embedded: an SVG file can be sent alone.

The page is first described as a list of shapes in millimetres (Drawing), then written as SVG or drawn with Pillow for the preview of the interface: both always show the same thing.

Usage:  py -3 gerbil_plates.py RESULTS_FOLDER [--ratio 2] [--page A4] [--landscape] [-o FOLDER]


#### Objects of a results folder

- **`ScaleBar`** — class, line 57  
  Graphic scale bar, in the manner of the QGIS print layouts. Lengths in real centimetres, sizes on the paper in millimetres, text sizes in points.

- **`PlateSettings`** — class, line 81  
  All the settings of the plates (page, scale, captions, title, drawings, options) and the scale bar; saved as JSON (interface settings, plates_settings.json).

  - **`from_dict(d)`** — method, line 120  
    Settings rebuilt from a dictionary (saved settings); unknown keys ignored, so that older files still load.

  - **`to_dict(self)`** — method, line 130  
    Settings as a dictionary (to save them as JSON).

  - **`page_size(self)`** — method, line 134  
    Width and height of the page in mm, turned for landscape.

- **`Item`** — class, line 145  
  An outlined object of a results folder: output name, TIFF file, real size (cm), row of the report, doubtful or not, box of the object in the TIFF, drawing found for it.

- **`natural_key(text)`** — function, line 158  
  Sort key where numbers count as numbers: "2" before "10".

- **`read_report(folder)`** — function, line 163  
  Rows of outlined_report.csv by output name (fields of the photos).

- **`collect(folder, include_doubtful)`** — function, line 173  
  The outlined objects of a results folder, with their real size (from the TIFF resolution).

- **`field_value(item, key)`** — function, line 200  
  Value of a column of the report for the object: its exact name, else the same letters and digits (case, spaces and underscores aside), else a field of the batch renaming ending so ("number" for "Object number").

- **`caption_text(template, item)`** — function, line 221  
  Caption of an object: the template with {field} replaced by its values.

- **`report_fields(items)`** — function, line 228  
  Fields usable for the order, the groups and the captions.


#### Drawing: shapes in millimetres, written as SVG or drawn with Pillow

- **`Drawing`** — class, line 242  
  A page described as shapes in millimetres, by layer: written as SVG (write_svg) or drawn with Pillow for the preview (render), so that both always show the same thing.

  - **`__init__(self, width, height)`** — method, line 245  
    An empty page of width x height mm.

  - **`add(self, layer, *shape)`** — method, line 251  
    Adds a shape (a tuple: kind, coordinates in mm, style) to a layer.

- **`pil_font(family, size_px, bold)`** — function, line 259  
  A Pillow font of the family at a size in pixels (cached), for the preview and to measure texts.

- **`text_width_mm(text, family, pt, bold)`** — function, line 276  
  Width of a text on the paper (measured with the font at 100 px per mm).

- **`svg_escape(s)`** — function, line 284  
  Escapes a text for SVG / XML.

- **`num(v)`** — function, line 289  
  A number written short for SVG (3 decimals at most, no trailing zeros).

- **`write_svg(drawing, path, layer_names)`** — function, line 294  
  Writes a Drawing as an SVG file in millimetres, one Inkscape / Illustrator layer per layer of the drawing, hidden layers hidden.

- **`svg_shape(s)`** — function, line 318  
  One shape of the drawing as SVG: rectangle, polygon / line, text, vertical text,
  
  image (PNG embedded in base64) or drawing (nested SVG).

- **`render(drawing, px_per_mm, hidden, show_hidden)`** — function, line 373  
  The page as a Pillow image (preview); the hidden layers only with show_hidden.


#### Scale bar

- **`bar_geometry(bar, ratio, max_mm)`** — function, line 437  
  Length (real cm) and segments of the bar: given, or chosen so that it stays under max_mm.

- **`fmt(v)`** — function, line 451  
  A number written without useless decimals (3, 1.5).

- **`draw_bar(dr, bar, ratio, x0, y0, max_mm, layer)`** — function, line 456  
  Draws the bar with its top-left corner at (x0, y0) (labels included). Returns (width, height).

- **`bar_size(bar, ratio, max_mm)`** — function, line 542  
  Width and height of a scale bar, measured by drawing it on an empty page.


#### Drawings (vector: SVG, or .ai / .pdf / .eps converted by Inkscape)

- **`inkscape()`** — function, line 558  
  Inkscape command line, if installed (converts .ai / .pdf / .eps and renders the previews).

- **`_cached(path, ext)`** — function, line 567  
  Path of a file in the cache of drawings, named from the source path, size and date (a changed drawing is converted again).

- **`drawing_svg(path)`** — function, line 576  
  SVG of a drawing: the file itself, or its conversion by Inkscape (cached). None if impossible.

- **`drawing_png(svg, px_per_mm)`** — function, line 590  
  Raster of a drawing for the preview (Inkscape, cached), or None.

- **`_length_mm(value)`** — function, line 603  
  An SVG length ("12.5mm", "300pt", "800") in mm (pixels at 96 per inch).

- **`svg_root(text)`** — function, line 611  
  (start tag of the root <svg>, inner content) of an SVG document.

- **`svg_size_mm(svg)`** — function, line 618  
  Width and height of the drawing on its paper (mm), from the root width / height (else viewBox at 96 px per inch).

- **`norm(text)`** — function, line 633  
  A value compared without case, spaces, punctuation or leading zeros ("0187" = "187").

- **`attach_drawings(items, s)`** — function, line 638  
  Each object gets the drawing of the same object found in s.drawings_folder: a drawing whose name (Gerbil's suffixes left out) is the output name (template "{name}"), or whose fields, read with the template (e.g. {site}_{number}), are those of the object (leading zeros ignored).


#### Layout

- **`Placed`** — class, line 680  
  An object placed on a plate: its photo (x, y, w, h in mm), caption, scale, drawing box
  
  and the box of photo + drawing.

- **`sort_items(items, s)`** — function, line 694  
  Objects sorted by group, then by the order field, then by name.

- **`page_room(s)`** — function, line 703  
  Width and height (mm) an object and its caption may take on a page of these settings.

- **`parse_ratio(text)`** — function, line 713  
  '1/3', '1:3', '3' -> 3 (plate scale 1:3); '2/3' -> 1.5.

- **`material_ratio(item, s)`** — function, line 725  
  Scale given by the material of the object (s.material_ratios: 'word=1/3; …', the word found in the material), or None.

- **`object_mm(item, r, s)`** — function, line 740  
  Size on the paper of an object at 1:r (photo, and its drawing beside it): (width, height, photo width, photo height, drawing width, drawing height) in mm.

- **`object_ratio(item, s)`** — function, line 750  
  Scale of an object: the one chosen for it, else the one of its material (by_material), else the
  
  plate scale - and, when it does not fit on the page (fit_large), the first usual scale at which it does.

- **`layout(items, s)`** — function, line 767  
  Pages of placed objects, one scale per page: the objects at the plate scale first, then those reduced (too large, or a scale chosen for them), each scale on its own pages with its own bar. Returns (pages, warnings); a page is (group, [Placed], ratio).

- **`layout_one(items, s, ratio_of, bars)`** — function, line 791  
  Pages of placed objects at one scale (or at the scale ratio_of gives each, the scale then written in the captions; `bars` scale bars stacked at the bottom): rows filled from left to right, centred, the images of a row aligned on their bottom edge, the drawing beside the photo, captions under them. Returns (pages, warnings); a page is (group, [Placed]).

- **`load_image(item, w_mm, h_mm, dpi)`** — function, line 880  
  The object image at `dpi` on the paper (never enlarged).

- **`page_drawing(s, page, number, total, images, dpi)`** — function, line 890  
  Drawing of one page. images: True (files read at the plate dpi), False (grey boxes) or a function (item, w_mm, h_mm) -> image (the interface gives its cached thumbnails).

- **`draw_measures(dr, p, color, font, pt, off, tick, lw)`** — function, line 936  
  Width and height of the object (real cm, as it lies on the plate) as dimension lines, above and on the left of it, on the hidden "Measurements" layer: layout guides, not data.

- **`plate_text(template, number, total, group, pad, scale)`** — function, line 952  
  Title or file name of a plate: {page}, {pages}, {group} and {scale} replaced (page on 2 digits
  
  and scale written 1-2 for files, 1:2 in a title).

- **`plate_file_names(s, pages)`** — function, line 964  
  File names of the plates (without folder): from the template, the characters not allowed in a Windows file name replaced by "_"; the page number added when the template has none.

- **`write_plates(folder, s, out_dir, progress)`** — function, line 988  
  Writes plate_01.svg, plate_02.svg... Returns (list of files, warnings).

- **`main(argv)`** — function, line 1011  
  Command line of the plates: options or a settings file, then write_plates.


### gerbil_tools.py

Inventory (CSV) and thumbnails. (220 lines.)

Gerbil - tools: inventory of a documentation folder as CSV (photos, drawings, 3D models) and thumbnails in batch for databases. © 2026 Eloïs CHARBONNEL Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE. This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to redistribute it under the conditions of the licence.

Inventory: one row per file, the columns chosen (file, folder, kind, size, date, the fields read from

the name with a template such as {site}_{us}_{number}, image size, resolution, date taken, camera). The PowerShell line that does the same (without the image information) is given too, for learning.

Thumbnails: a reduced copy of each image (PNG, transparency kept, or JPEG on white), the transparent

margin of the outlined objects cut off.

Usage:

      py -3 gerbil_tools.py inventory FOLDER [-o inventory.csv] [--template "{site}_{us}_{number}"]
      py -3 gerbil_tools.py thumbnails FOLDER [--size 512] [--format png|jpg] [--only-outlined]

- **`kind_of(name)`** — function, line 42  
  Kind of a file from its extension: photos, drawings, 3d or None.

- **`template_regex(template)`** — function, line 48  
  {site}_{us}_{number} -> ^(?<site>.+?)_(?<us>.+?)_(?<number>.+?)$ (fields, literal text kept). Returns (Python pattern, PowerShell / .NET pattern, field names).

- **`list_files(folders, kinds, recursive)`** — function, line 63  
  Files of the chosen kinds in the folders (sub-folders if wanted, Gerbil's work folders left out).

- **`image_info(path)`** — function, line 77  
  Size, resolution, date taken and camera of an image (empty when it cannot be read).

- **`inventory(folders, out_csv, kinds, template, image_columns, recursive, progress)`** — function, line 94  
  Writes the inventory; returns (number of rows, columns).

- **`ps_quote(s)`** — function, line 123  
  A text between single quotes for PowerShell (quotes doubled).

- **`powershell_line(folders, out_csv, kinds, template, recursive)`** — function, line 128  
  The same inventory in PowerShell (file columns and fields of the name; no image information).

- **`thumbnails(folders, out_dir, size, fmt, only_outlined, trim, recursive, progress)`** — function, line 144  
  Writes NAME_thumb.png / .jpg (longest side `size`) in out_dir (default: a "thumbnails" folder in each source folder). Returns the list of files written.

- **`main(argv)`** — function, line 188  
  Command line: "inventory" or "thumbnails".


### packaging/gerbil_setup.pyw

The installer (Gerbil_Setup.exe). (330 lines.)

Gerbil - installer (Gerbil_Setup.exe, built by build_exe.bat). © 2026 Eloïs CHARBONNEL Licence: GNU General Public License v3 or later (SPDX: GPL-3.0-or-later), see LICENSE. This program comes with ABSOLUTELY NO WARRANTY; it is free software, and you are welcome to redistribute it under the conditions of the licence.

One file to send: it holds the whole .exe version (Gerbil.zip) and installs it for the current user,

without administrator rights:

      - in %LOCALAPPDATA%\Programs\Gerbil (or another folder chosen in the window);
      - shortcuts in the Start menu and, if wanted, on the desktop;
      - an entry in Windows "Installed apps" (and Uninstall.bat in the folder) to remove it.
Installing again over an earlier version updates it; the AI models already downloaded ("models" folder) are kept. Photos and results are never touched.

Test without building: py -3 gerbil_setup.pyw --zip dist\Gerbil.zip

- **`version()`** — function, line 83  
  Version of Gerbil, read from version.txt (built in) or gerbil.py.

- **`payload()`** — function, line 95  
  The Gerbil.zip to install (inside the setup, or given with --zip for tests).

- **`running()`** — function, line 102  
  Gerbil programs open at the moment.

- **`members(zf)`** — function, line 112  
  Files of the archive, without the top 'Gerbil' folder: [(info, relative path)].

- **`check_folder(folder)`** — function, line 125  
  None if the folder can receive Gerbil, otherwise the reason. A folder that already holds other things than Gerbil is refused: the update removes the previous program files.

- **`install(folder, zip_path, desktop, progress)`** — function, line 138  
  Installs: removes the files of the previous version (not the AI models),
  
  extracts the archive with a progress, writes Uninstall.bat and the list of files, creates the shortcuts and the Windows uninstall entry.

- **`register(folder, size)`** — function, line 178  
  Entry in Windows "Installed apps" (current user only).

- **`Setup`** — class, line 193  
  (small helper: see the code)

  - **`__init__(self, root)`** — method, line 194  
    The setup window: folder, desktop shortcut, Install button, progress.

  - **`browse(self)`** — method, line 260  
    Chooses the folder; a parent folder gets a "Gerbil" folder inside.

  - **`start(self)`** — method, line 268  
    Checks the folder and that Gerbil is closed, then installs in a thread (the window stays responsive).

  - **`finished(self, folder, error)`** — method, line 294  
    End of the installation: error shown, or "Open Gerbil" offered.

  - **`launch(self, folder)`** — method, line 309  
    Starts the installed Gerbil (in a clean environment) and closes.

- **`main()`** — function, line 316  
  Starts the setup window (sharp on high-resolution screens).


### tests/synthetic.py

Synthetic photos for the automatic tests. (68 lines.)

Synthetic photos for the tests: a sherd and a printed checkerboard scale (1 cm squares, two rows),

on a light background or on dark felt (with a paper label). Nothing real: the repository holds no photo.

- **`sherd_polygon(cx, cy, r, seed, n)`** — function, line 8  
  (small helper: see the code)

- **`scale_image(px_cm, n_cm)`** — function, line 15  
  A checkerboard scale: two rows of 1 cm x 0.5 cm squares, black and white, on a white card.

- **`photo(px_cm, dark, label, size, seed, shadow)`** — function, line 37  
  (rgb image, sherd mask, px_cm) - the sherd in the upper middle, the scale below it; with shadow, the sherd casts a soft shadow down and to the right (light from the upper left).


### tests/test_gerbil.py

The automatic tests. (151 lines.)

Automatic checks of Gerbil on synthetic photos (tests/synthetic.py): scale, cut-out, labels on a dark background, learned scales, IPTC metadata, plates, inventory. Run: py -3 -m pytest tests

- **`save(path, rgb)`** — function, line 23  
  (small helper: see the code)

- **`run(folder, *args)`** — function, line 27  
  (small helper: see the code)

- **`number(text)`** — function, line 35  
  (small helper: see the code)

- **`light(tmp_path_factory)`** — function, line 40  
  (small helper: see the code)

- **`test_scale_read_exactly(light)`** — function, line 48  
  (small helper: see the code)

- **`test_cutout_matches_the_sherd(light)`** — function, line 56  
  (small helper: see the code)

- **`test_dark_background_label_discarded(tmp_path)`** — function, line 66  
  (small helper: see the code)

- **`test_no_scale_still_discards_the_scale(tmp_path)`** — function, line 76  
  (small helper: see the code)

- **`test_cast_shadow_removed(tmp_path)`** — function, line 86  
  (small helper: see the code)

- **`test_learned_scale(tmp_path)`** — function, line 96  
  (small helper: see the code)

- **`test_iptc_and_lossless_jpeg(tmp_path)`** — function, line 111  
  (small helper: see the code)

- **`test_plates_svg(light, tmp_path)`** — function, line 127  
  (small helper: see the code)

- **`test_inventory_and_powershell(tmp_path)`** — function, line 138  
  (small helper: see the code)
