# Gerbil — Archaeological photo toolkit

**Outlining of archaeological finds photographed with a scale, at their real size (1:1).** Formerly *SherdCut*.
© 2026 Eloïs CHARBONNEL

**[⬇ Download Gerbil for Windows](https://github.com/EloisCharbonnel/gerbil/releases/latest)**: the installer
(`Gerbil_Setup.exe`, no Python needed) and the user guide in French and English (PDF).

Gerbil processes photos of sherds taken on a plain, light background with an archaeological scale
(1 cm squares or a millimetre ruler, 5 or 10 cm long), in JPEG, TIFF, PNG or RAW (see "RAW photos"). For each photo it writes a layered Photoshop file
and transparent TIFF files whose resolution is the real one: dropped into Illustrator, the sherd shows at
1:1 scale.

## Quick start

- **Computer without Python**: double-click **`Gerbil_Setup.exe`** (one file), then open Gerbil from the
  Start menu (see "The .exe version" below).
- **Computer with the scripts** (`gerbil.py`, …): double-click **`Install.bat`** once, then
  **`Gerbil.bat`** to open the interface (see "Installation on another computer").

In the interface: *Add folder…*, then **Run**. The results go into an `outlined_result` folder next to the
photos.

## What comes out

For a folder of photos, Gerbil creates an **`outlined_result`** folder next to them. All the files of a
photo keep its original name, so they follow one another in the Explorer:

```
outlined_result/
  NAME.JPG                      copy of the original photo
  NAME.psd                      layers: Original photo (hidden), Scale, Ceramic
  NAME_outlined.tif             outlined ceramic, transparent background
  NAME_outlined_scale.tif       ceramic + scale, transparent background
  outlined_report.csv           one row per photo (opens in Excel)
  to_control/
    NAME_to_control.jpg         control preview
```

- **PSD**: the scale and the ceramic are cut out with a *layer mask*. Correct it with the brush
  (white = show, black = hide) without losing anything. The hidden **Original photo** layer holds the
  **whole photo**, aligned on the sherd: the scale stays where it was photographed, even when it is moved
  under the sherd. What lies beyond the document stays in the file: move the layer, or use
  *Image > Reveal All*, to see it.
- **`to_control` preview**: green outline = cut-out; magenta frame = scale; orange lines = centimetres
  found; red area = possible mounting putty; at the top, the measurement and any points to check.
- **When something is doubtful**, all the files written for the photo get the **`_to_be_verified`** suffix
  (e.g. `NAME_outlined_to_be_verified.tif`). Type `to_be_verified` in the Explorer search box to find them.
  There is a doubt when:
  - the scale is not found;
  - it is not 5, 10 or 20 cm long, or its squares / graduations are irregular or partly hidden;
  - an area looks like mounting putty (red area);
  - a colour chart touches the ceramic;
  - the ceramic touches the edge of the photo.
- The copy of the original photo always keeps its exact name.

At the end of a run, a summary lists what needs checking, grouped by problem (scale not found, scale
doubtful, no object kept, object cut by the photo edge, mounting putty, colour chart touching the object),
with the photos concerned.

Running Gerbil again on a folder replaces the files of each photo processed again, and the
`_to_be_verified` suffix disappears if the doubt is lifted. The report keeps the rows of the other photos.

Report statuses: `ok`, `to verify` (`_to_be_verified` files), `failed` (no ceramic found), `error`.
Columns: `file` (name of the photo), `output_name` (name of the output files), `status`, `to_verify`
(reasons for the doubt), `scale_found`, `scale_type`,
`squares`, `scale_length_cm`, `px_per_cm`, `ppi_1_1`, `ceramic_width_cm`, `ceramic_height_cm`, `pieces`,
`camera`, `lens`, `focal_mm`, `date_taken`, `notes`, `duration_s`. An older report with French column names
is taken over and converted at the next run in the same folder.

`docs\PSEUDOCODE.txt` describes the whole processing step by step (pseudocode, libraries, methods);
`docs\CODE_GUIDE.md` explains the Python code itself, file by file and function by function.
`docs\Gerbil_guide_FR.odt` (French) and `docs\Gerbil_guide_EN.odt` gather everything in one illustrated
document: using Gerbil, the processing explained in plain words, reading the code (real functions explained
line by line) and the reference of every function (`py -3 docs/make_guide_odt.py` writes them again).
`docs\ROADMAP.md` lists what is planned next, and `docs\REFERENCES.md` the sources behind
the choices (drawing conventions, graphic documentation, archiving of 2D and 3D data).

## Batch renaming: names and information of the photos

A folder of photos can be renamed in batch (button *Batch renaming…* of the interface, on the folder of the
photos — choosing an `outlined_result` folder opens the folder of its photos; saved in
`gerbil_project.json` next to the photos, so it travels with them):

- **Fields**: by default *Site*, *Sector*, *US*, *Object number* (site and number required), *Material*
  (ceramic, metal, bone, glass, lithic, other) and *View* (exterior, interior, profile, top, bottom).
  Fields can be added, edited (label, key, required, list of choices) or removed.
- **Name template**, e.g. `{site}_{sector}_US{us}_{number}_{material}`: the **output files** (PSD, TIFF,
  previews) take the name built from it, e.g. `QSR25_A5_US7549_187_metal_outlined.tif`. **The original
  photos are never renamed** (the report keeps their name in `file`, the new one in `output_name`).
  `{photo}` gives the name of the photo. (Other way of working: rename the original photos yourself
  *before* processing them, e.g. with PowerShell; without a template, the output files simply take the
  names of the photos. Do it before the first run: the corrections, manual scales and batch-renaming
  values are attached to the names of the photos.) Spaces and forbidden characters become `_`; the separators left by
  an empty field are merged. Two photos giving the same name get a suffix (`_2`, `_3`…) and are flagged.
  Without a template, the names of the photos are kept. When a name changes, the files written under the
  former name are removed.
- **Naming rule** (optional): a regular expression the output names must match, read **as PowerShell's
  `-match`**: case-insensitive, found anywhere in the name unless anchored with `^` and `$`, .NET named
  groups `(?<name>…)` accepted, `(?-i)` at the start makes it case-sensitive (a rule written for PowerShell
  can be pasted as it is). A name that does not match is flagged ("name does not match the naming rule").
  The rule tests the output name, without extension (Gerbil always writes its extensions in lowercase).
  **Rule helper**: tick ready-made conditions (capital letters only, lowercase only, only letters / digits /
  `_`, also `-`, no double separator, ends with a number, starts with…, at most N characters): the rule is
  written for you, shown as a PowerShell line (`'NAME' -match '…'`, to learn or to reuse), and a name can be
  tested (✓ True / ✗ False). *Also check the photos: extension in lowercase* flags the original photos
  whose extension has capital letters (`.JPG`); they are not renamed, only reported.
- **Values**: those common to all the photos (e.g. the site), and a table with one row per photo: double-
  click a cell to edit it; **drag the small square at the corner of a cell** over the rows below to copy its
  value (with Ctrl: a series 187, 188, 189…), as in Excel; *Select all* (Ctrl+A) then *Set for selected…*
  (e.g. the same site for every photo), *Number the selected…*, Ctrl+D (copies the first selected row down);
  a preview shows the photo of the selected row (drag the bar between the table and the preview to enlarge
  it; double-click it or *Open the photo* to see it whole); or *Import CSV /
  Excel…*: an inventory whose first row holds the column names; the
  column of the photo names is found by itself (with or without extension), the other columns fill the
  fields of the same label or key (the others are reported as ignored).
- The information can also be typed in the **review window**, next to the photo.
- A photo whose required fields are empty is flagged ("missing information: …").
- The information is written in the report (one column per field, after the usual ones) and **inside the
  PSD and TIFF files** (XMP: title = output name, keywords = values, and one `gerbil:` property per field).

## IPTC metadata (`IPTC metadata…` in *Batch renaming*)

The fields of the batch renaming also fill the standard **IPTC** fields (read by Bridge, Lightroom,
Photoshop, darktable, the Windows Explorer…). For each IPTC Core field (Title, Headline, Description,
Keywords, Creator, Date Created, Country Code, Country, State / Province, City, Sublocation, Job
Identifier, Instructions, Credit Line, Source, Copyright Notice) a text where `{field}` is replaced by
the value of the photo and `{name}` by the output name; a text without braces is the same for every
photo (copyright, creator). Default model: Title = `{name}`, Keywords = all the fields, Country Code =
`{site}`, Country = `{sector}`, Sublocation = `{us}`. The example of the selected photo is shown.

They are written into the PSD and TIFF files, into the **copy of the original** in `outlined_result`
(JPEG: added without recompressing the image; RAW and others: a `NAME.xmp` file beside the copy) and,
if ticked, into a **`NAME.xmp` file next to each original photo** (the photos themselves are never
changed; a `.xmp` written by another program, Lightroom for instance, is never replaced).

## Inventory and thumbnails (`Tools` menu)

- **Inventory (CSV)…**: one row per file of the chosen folders (photos, drawings `.ai` `.svg` `.pdf`
  `.eps`, 3D models), with its folder, kind, size, date, the **fields read from its name** (template
  such as `{site}_{sector}_US{us}_{number}_{material}`, taken from the batch renaming; Gerbil's suffixes
  `_outlined`, `_to_be_verified`… go into a column *variant*) and, for the images, their size in pixels,
  resolution, date taken and camera. The window shows the **PowerShell line** that makes the same
  inventory with Windows alone (without the image information), to copy and learn from. Opens in Excel
  (`;` separator, UTF-8).
- **Thumbnails…**: reduced copies for databases, longest side 128 to 1024 px, PNG (transparent) or
  JPEG (white background), the transparent margin of the outlined objects cut off; in a `thumbnails`
  folder.

Command line: `py -3 gerbil_tools.py inventory FOLDER --template "{site}_{us}_{number}" --powershell`,
`py -3 gerbil_tools.py thumbnails FOLDER --size 512 --format png --only-outlined`.

## Site profiles and learned scales

A **site profile** gathers what is known of the photos of a site or a campaign, chosen once under
*SITE PROFILE* in the main window (*New…*, *Edit…*) instead of setting everything again:

- the **background** of the photos: found by Gerbil, light, or dark (velvet, felt: paper labels
  discarded, edge of the objects placed for a dark background);
- **learned scales**: *Learn a scale from a photo…*, then click the two ends of the scale (its 0 and its
  last mark) and give the width of its printed band. Gerbil keeps its image and finds it again on the
  other photos (matched points, then a fine alignment of the image: same measurement as the usual
  reading within 0.05 % on the same physical scale). Learn **each copy** of the scale used: two prints of
  the same model may differ by 1 %. By default a learned scale is a second chance, used when the usual
  reading fails or is doubtful (a learned 10 cm scale is also found inside a 20 cm one of the same
  make); *Look for the learned scales first* for a scale the usual reading gets wrong;
- the **options** of the main window (*Keep the options of the main window*), set again when the
  profile is chosen.

Profiles are kept in `%APPDATA%\Gerbil\profiles`. *Put next to the photos…* writes the profile as
`gerbil_profile.json` in a folder of photos: the engine then uses it for these photos whatever the
profile chosen (to share with the team). Command line: `--profile FILE`.

## Plates (`Plates…`, or `gerbil_plates.py`)

**Plates…** (main window) lays out the outlined objects of a results folder on pages at a chosen scale
(1:1, 1:2, 1:3…) and writes them as **SVG files** in `plates\` that open in Illustrator or Inkscape at
their true size: 1 cm of the object = 1 cm / scale on the paper.

- **Plate title** (optional) at the top of each plate, left, centred or right, with `{page}`, `{pages}`
  and `{group}` replaced (e.g. `QSR25 - US 1209 - Plate {page}`).
- **File names** of the SVG files from a template: `plate_{page}` by default (`plate_01.svg`…), e.g.
  `QSR25_US1209_pl{page}` or `{group}`; the number is added when `{page}` is missing; the names that will
  be written are shown under the field.

- Each object keeps its real size, read from the 1:1 resolution of its `_outlined.tif` (photos without a
  scale are left out; those *to be verified* only when ticked).
- Objects are placed in **rows**, in the chosen order (name or a column of the report: US, material…),
  centred, the images of a row aligned on their bottom edge, with a **caption** under each one (`{name}`,
  or the fields of the batch renaming: `{site}_{us}_{number}`…). *Group by* starts a new row (or a new
  page) at each value. Page A4, A3, A5, Letter or custom, portrait or landscape, margins, spacing.
- The images are **embedded** (PNG, at 600 dpi on the paper by default, never enlarged), cropped to the
  object (the transparent margin of the TIFF is left out): an SVG file can be sent alone. Layers:
  *Objects*, *Captions*, *Title*, *Scale bar*.
- **Measurements as guides** (option): width and height of each object (as it lies on the plate, in real
  cm) as dimension lines, on a *Measurements (guides)* layer **hidden** in the SVG; show it in Illustrator
  or Inkscape to place drawings or sections. They are layout guides, not data, and are not written in the
  report. *Show the measurements in the preview* displays them in the window.
- A **graphic scale bar** on every page, set as in QGIS: style (single box, double box, line with ticks
  up / down / middle, stepped line, hollow), length (auto: 1, 2, 5, 10, 20 or 50 cm) and segments, first
  segment cut in millimetres or halves, height, line width, two fill colours, line and text colours,
  numbers at the ends or at every segment, above or below, unit (cm, or mm: numbers in millimetres),
  font, size, bold, the scale "1:2" written after it, position on the page. It is remembered as your
  house style.
- **One scale per plate.** With *Reduce the objects too large for the page* (ticked by default), an object
  that does not fit at the chosen scale goes to 1:1.5, 1:2, 1:3… on plates of its own, each with its scale
  bar. *Scale per object…* sets a scale by hand for some objects (a large vessel at 1:3). `{scale}` in the
  title gives "1:2", in the file names "1-2".
- **Scale by material** (tab *Scales & drawings*): each object at the reduction of its material, read in
  the column *Material* of the report: by default ceramics and glass 1/3, iron 2/3, stone 1/3 (DMS
  Bruxelles 2009), as editable rules `word=reduction; …` (the word is looked for in the material).
- **Several scales on one plate** (option): the objects keep their own scale on the same plate, the scale
  is written in their caption ("(1:3)") and the plate gets one named bar per scale. Unticked (default):
  one scale per plate.
- **Drawings beside the photos**: give the folder of the drawings (`.svg`, or `.ai` `.pdf` `.eps`
  converted by Inkscape when it is installed). A drawing named like the output name of the photo
  (`{name}`), or whose name gives the same fields (`{site}_{number}`, leading zeros ignored), is placed
  on the left (or right) of its photo, at the same scale, **kept as vectors** (editable in Illustrator;
  layer *Drawings*). Drawings at 1:1 by default, or give their scale.
- In the preview, the **mouse wheel zooms** on the point under the mouse, the middle button or the scroll
  bars move the view, and a **right-click on an object** gives a menu of scales for it (1:1, 1:1.5, 1:2,
  1:3…; "scale of the plates" goes back to the automatic one).
- The preview shows the pages as they will be written (◀ ▶ to turn them); a warning appears when an
  object is larger than the page at that scale.

The settings of a run are saved next to the plates (`plates_settings.json`). Command line:
`py -3 gerbil_plates.py outlined_result --ratio 2 --page A4 --caption "{name}" --title "Plate {page}"
--name "QSR25_pl{page}" [--measurements]`, or
`--settings plates_settings.json` to write again with the same settings.

## Scale and 1:1 size in Illustrator

Gerbil recognises two kinds of scale and derives from them the real resolution of **each** photo, without
relying on the EXIF data: the camera body, the lens or the distance do not matter.

- **Square scale** (black / white / red checkerboard, or single black / white row), 5, 10 or 20 cm: Gerbil
  counts the 1 cm squares and measures their length. When digits are printed inside the squares ("5",
  "10", "cm" in white on red), a second reading finds the boundaries between the squares and fits a regular
  spacing over the whole scale (note "squares read by their boundaries (second reading)" in the report).
  This second reading never turns the scale over: it keeps its orientation in the photo.
- **Graduated ruler** (light card, millimetre ticks, "0 cm 1 2 3 4 5"): Gerbil finds the ~50 millimetre
  ticks and measures their spacing, which gives a precision of about 0.1 %. It also finds the centimetre
  ticks to read the length (5 or 10 cm). Rulers with thick ticks hanging from the edge of the card are
  read by a second pass. A slightly bent ruler, or one partly hidden by a support, can
  still be read.

The report gives the type of scale found for each photo (`scale_type` column: `checkerboard` = square scale,
`ruler` = graduated ruler).

This resolution is stored in the PSD and TIFF files (ppi = px/cm × 2.54), and Illustrator sizes a placed
image from it. **A simple drag and drop into Illustrator therefore puts the sherd at 1:1 scale.** To check,
the scale of `NAME_outlined_scale.tif` measures exactly 5 cm (or 10 cm) with Illustrator's ruler. For a
plate at 1:2, scale it down by 50 % afterwards.

By default, the scale is straightened and centred under the ceramic. It is never enlarged or reduced.
It is turned upright from the digits printed in its squares ("5", "10", "cm"), compared with common
fonts; when they are unclear, the red row goes on top.
A square scale cut by the edge of the photo is still found: it is measured on its complete squares (the
measurement stays precise), the cut square still counts in its length, and the report notes "scale cut by
the photo edge". A square scale is cut flush with its printed face (without its edge or the white border of the card);
a graduated ruler keeps its card.

## Mounting putty

Gerbil spots an area that looks like a putty support: stuck to the sherd, clearly smoother, lighter and
less coloured than it. By default it **flags it without removing it**: the photo goes `_to_be_verified` and
the area shows in red on the preview. Remove it afterwards in Photoshop by painting black on the mask of
the "Ceramic" layer. Why not remove it straight away? A light, smooth vessel base (for example with an
inventory number written on it) looks too much like it. The `--remove-putty` option removes the area
automatically; its pixels then stay in the PSD (paint white to bring them back). A blue putty (Blu-Tack
type), or putty hidden behind the object, avoids the problem.

## Plexiglass supports

Translucent supports (plexiglass stand, plate or wedge, behind or under the sherd) are removed
automatically: their colour stays close to the background colour, whereas the ceramic clearly differs.
They are outlined in blue on the preview. Reflections of the background on a black gloss, of a similar
colour, are left alone: they are darker and run along the ceramic instead of sticking out.

**Opaque** white or cream supports (putty, foam) lodged in a hollow or behind a handle are not recognised:
their colour and texture look too much like a light ceramic. Remove them in Photoshop by painting black on
the mask of the "Ceramic" layer.

## Cast shadows

Soft shadows are left out by the colour rule itself (the lightness counts for half in the distance to the
background). A darker cast shadow (lamp from the side, museum photos) is recognised on a light background
and removed: darker than the background by a shadow but of its colour, smooth, lying along the outline of
the object and fading into the background (its outer edge is soft, the edge of an object is sharp). It is
outlined in blue on the preview (note "cast shadow removed"). Its darkest part, against the object (tinted
by the light the object reflects), is followed up to the sharp edge of the object. A dark, smooth part of
the object itself
(black gloss, obsidian, grey flint) does not fade into the background and stays. On 191 open photos of finds,
22 shadows were removed, none on the objects. On a dark background a shadow does not show: nothing changes.

## Labels, bags

What lies on the other side of the scale from the object (labels under the ruler) is discarded. Thin
strokes and lines (handwriting, printed lines of a bag) are discarded too, as well as small isolated
elements, more than 8 mm from the object and smaller than 8 % of its area (felt-pen letter on a bag).
These last ones are outlined in red on the preview, for checking.

An object lying close to the scale, or against its card (coin, small bronze), is kept when it reaches at
least 8 mm from the squares and clearly differs from the background (note "object(s) lying close to the
scale kept"); a support or the edge of the card, near the squares or of the background colour, stays out.

When no scale is measured (scale not found, a scale of an unknown kind, or `--no-scale`), the scale is
still kept out of the cut-out, as well as rulers, labels and colour cards: they are recognised by their
outline, made of long straight sides at right angles (even an L-shaped scale bar, or a ruler whose ticks
make a comb), and by the content of a print (black and white, uncoloured, or a full rectangle). They are
outlined in red on the preview (note "scale, label or card discarded"). On 191 open photos of finds from
many museums and the Portable Antiquities Scheme, no object was discarded this way (a pin, a black blade
or a long bone tool stays an object), and the photos where the object seemed cut by the photo edge
(because the scale bar touching it was kept) went from 79 to 18. When a scale is found, nothing changes.

On a dark background (black velvet, dark felt), a paper label is discarded wherever it lies, outlined in
red on the preview (note "paper label discarded"): bright and rectangular, white, bluish white (paper with
optical brighteners) or pale yellow (sticky note), even slightly bent, with writing or a punched hole;
any light, very rectangular element (it fills 95 % of its rectangle: a broken sherd never does), whatever
its colour. A label touching an object by a corner is cut from it (a label joined to a sherd by a wide
shadow is not: erase it in *Review…*); a label stuck against the scale is told apart from
the light squares of the scale. When the only object of a photo looks like a label (a small, pale, square
sherd), it is kept and the photo is flagged *to be verified*. On a dark background, small sherds lying
apart from the others are kept (the rule for isolated felt-pen letters applies to light backgrounds only).

On a dark background the edge of a light object is a ramp several pixels wide (slight blur, shadow at its
foot): the cut-out follows the middle of that ramp, and the colours of the last pixels of the edge are
replaced by those of the sherd just inside (the outline itself does not move), so that no dark line
remains around the sherds, also on cut-outs corrected by hand.

## Colour charts

A colour chart (Pantone colorimeter, ColorChecker…) placed next to the sherd is recognised by its palette:
its very saturated printed colours cover at least 5 hue sectors out of 12 (reds, yellows, greens and blues
together), whereas a ceramic, even glazed or painted, stays within a few neighbouring hues (2 sectors at
most over the 1,763 photos tested, against 5 to 9 for the charts). A chart separate from the sherd is
discarded and outlined in red on the preview (note "colour chart discarded"). A round chart (Pantone
colorimeter) touching the sherd is cut out along its circle, together with its cast shadow. If this circle
cannot be found (rectangular chart stuck to the sherd), the chart is kept and the photo goes
`_to_be_verified` ("colour chart touching the ceramic").

## Openings and perforations

Holes through which the background shows (opening between the attachments of a handle, perforation)
stay transparent. The other holes of the cut-out (gloss reflections, light concretions) are filled.

## AI second opinion (`--ai` option)

Without the option, nothing changes. With `--ai`, a neural cut-out network gives a second opinion (the
IS-Net/DIS or BiRefNet models, the same as the rembg library). It can **only remove** background that the
script kept, never add anything. An area is removed only when the four conditions are met: the script keeps
it, the AI sees background there, its colour stays close to the background, and it covers at least
0.02 cm². This opens shadowed perforations, gaps between two sherds, background halos along a blurred edge
or small background patches between two close sherds. Labels, supports, scale and colour charts keep their
usual treatment. The areas removed by the AI are outlined in **cyan** on the preview, with a note in the
report ("AI (...) removed background: ...").

- `--ai`: IS-Net model, fast (less than 1 s per photo on the graphics card).
- `--ai --ai-model birefnet`: BiRefNet, more precise on perforations (colanders), but much slower (on the
  processor: it is too large for the graphics card through DirectML).
- `--ai-device cpu`: force the processor.

To turn it on with `Gerbil_drop.bat`: `set OPTIONS=--open --ai`.

It needs the onnxruntime package (once per computer: see "Installation"; included in the .exe version) and
the model, in the `models` folder next to the script (or next to the .exe). If missing, the model is
downloaded automatically at its first use (180 MB for IS-Net, 970 MB for BiRefNet; internet needed once).
The `models` folder can also be copied from one computer to another.

## The interface (`Gerbil.bat` or `Gerbil.exe`)

Double-clicking **`Gerbil.bat`** (or `gerbil_gui.pyw`, or `Gerbil.exe` in the .exe version) opens a
window in French or English (FR / EN at the bottom of the column; it follows Windows the first time). A
column on the left gives the five steps of the work, each with its page; the steps can be visited in any
order:

1. **Source photographs**: folders or photos to process, and the site profile.
2. **Naming and metadata** (optional): a summary of the batch renaming of the folder, and the button that
   opens it.
3. **Processing**: the essential settings (the others in *Advanced settings…*, and the settings changed
   from the defaults listed, with *Back to the defaults*), where the results go, *Run*. The progress is a
   scale bar whose squares fill in; a table gives each photo, its state (ok, to verify, failed), its scale
   and what to do in a few words; double-click a row to fix it. The lines of the engine are in *Technical
   details*.
4. **Review**: the photos to look at with their problem, the review window and the manual scale.
5. **Publication**: plates, inventory (CSV), thumbnails.

The sections below describe each window in detail, with the English names of their buttons (all the windows also exist in French; their texts are in `gerbil_lang_fr.py`):

- **Photos**: *Add folder…* / *Add photos…* add folders or photos (the number of photos of each folder is
  shown); *Remove* (or the Delete key) and *Clear* empty the list.
- **Set scale…**: when the scale of a photo is not found or wrongly read, give it by hand. Select the photo
  in the list (or choose it), click the two ends of a known length on the scale (for example 0 and 5 cm,
  along its middle), give that length and the width of the scale, then *Save*: the photo can be processed
  again straight away. Mouse wheel: zoom; right button: move the view; points can be dragged. The scale
  is saved in `gerbil_scales.json` **in the folder of the photos** (not in `outlined_result`; keep this
  file with the photos; a `sherdcut_scales.json` written before the renaming is still read, and replaced
  by `gerbil_scales.json` at the next change); it prevails over the automatic search at every run (report: `scale_type` =
  `manual`). *Remove the manual scale* goes back to the automatic search. Width of the scale: 1 cm by
  default.
- **Review…**: review the cut-outs photo by photo, the doubtful and failed ones first. The photo shows
  with the outline of the cut-out (green, background dimmed) and of the scale (magenta). Tools:
  **One click on the object (more precise)**: click each object to keep and Segment Anything (the
  MobileSAM version, offline, downloaded once: 45 MB in `models`) cuts it out; the computed cut-out is
  replaced by the objects clicked, Shift + click removes one. It is more reliable on difficult photos
  because the program is told *which* object to cut out instead of guessing what is a sherd, a label,
  a shadow or the background (a label stuck to the sherd by its shadow, for instance); the edge of the
  computed cut-out is kept where it agrees. About a second to prepare each photo, then instant clicks.
  *Erase* / *Add* with the brush (size slider) or with the **lasso** (draw around an area),
  *Remove a piece* (one click removes a whole piece: shadow, background patch), *Undo* (Ctrl+Z),
  *Reset photo*. Mouse wheel: zoom; move the zoomed view with the **scroll bars**, the right or middle
  button, Space + drag or the arrow keys; R: whole photo. **Orientation**: draw a line along the rim of the
  object (it becomes horizontal, the object below it), or turn it by quarter turns; a thumbnail shows the
  object as it will be exported; *Fix the scale…* opens the manual scale. *Accept and next* saves the
  corrections of the photo and **exports it again at once**, in the background (the list shows
  "exporting…", then "✓ exported"): no need to go through all the photos. Reopened later, the window shows
  the corrections already saved, not the computed cut-out. The corrections are
  saved **next to the photos**, in a `gerbil_edits` folder (keep it with them): every later run keeps
  them. A turned object is resampled once, at the export; the scale stays straight under it, and the
  original photo stays untouched (not turned) in the hidden layer of the PSD. The review uses the data
  written in `outlined_result\gerbil_review` at each run (about 300 KB per photo).
- **Series of photos without a scale**: at the end of a run, Gerbil offers to set by hand the scales it
  did not find, one photo after the other (*Save and next*, *Skip this photo*, *Stop*; the length and
  width typed are kept from one photo to the next); the corrected photos are then processed again in one
  run. Selecting several photos in the list before *Set scale…* does the same for them. Folders or photos dropped on
  `Gerbil.bat` / `Gerbil.exe` are added straight away.
- **Results**: in an `outlined_result` folder next to the photos (default), or in a chosen folder.
- **Options**: the same as on the command line, grouped (files, scale and layout, cleaning, AI, run).
  Resting the mouse on an option shows its explanation.
- **Run** starts the processing; the bar and the log show each photo (green: ok, terracotta: to verify,
  red: failed). **Cancel** stops it cleanly. **Open results** opens the result folder.
- The settings are remembered from one time to the next (`.gerbil.json` file in the user's folder;
  the settings of the previous names, `.sherdcut.json` and `.detourage_ceramique_gui.json`, are taken
  over). The log starts with
  the equivalent command line.
- **Help** opens this document.

For a desktop shortcut: right-click `Gerbil.bat` (or `Gerbil.exe`) > *Show more options* > *Send to* >
*Desktop (create shortcut)*.

## Drag and drop (`Gerbil_drop.bat`)

1. In the Explorer, **drag the folder of photos onto `Gerbil_drop.bat`** and drop it. Several folders can
   be dropped at once (each one gets its `outlined_result`), or a few photos.
2. A black window shows the progress photo by photo. Count 3 to 4 s per photo.
3. At the end, the `outlined_result` folder opens. Press a key to close the window.
4. Look through `to_control`, then fix the `_to_be_verified` files in Photoshop.

Tips:
- **Desktop shortcut**: right-click `Gerbil_drop.bat` > *Show more options* > *Send to* > *Desktop (create
  shortcut)*. Then drop the folders on the shortcut.
- **"Send to" menu**: copy this shortcut into the folder that opens when typing `shell:sendto` in the
  Explorer address bar. Then: right-click a folder > *Send to* > *Gerbil_drop*.
- **Change the settings**: right-click `Gerbil_drop.bat` > *Edit*, then complete the line
  `set OPTIONS=--open` (for example `set OPTIONS=--open --background white`). Several copies of the .bat can
  be kept with different settings.
- Double-clicking `Gerbil_drop.bat` without dropping anything shows the list of options.

## Command line (`gerbil.py`, or `gerbil_cli.exe`)

Right-click in the folder of the script > *Open in Terminal*, then:

```
py gerbil.py "D:\Photos\Lot 12"
py gerbil.py "D:\Photos\Lot 12" --background white
py gerbil.py "D:\Photos\Lot 12" -o "D:\Output\Lot 12"
py gerbil.py "D:\Photos\Lot 12\DDN_xxx.JPG" "D:\Photos\Lot 12\DDN_yyy.JPG"
py gerbil.py --help
```

In the .exe version, `gerbil_cli.exe` takes the same arguments (`gerbil_cli.exe "D:\Photos\Lot 12"`).

### Options

| Option | Effect |
|---|---|
| `--background white` | TIFF on a white background instead of transparent |
| `--remove-putty` | remove the mounting putty found automatically (otherwise: only flagged) |
| `--layout original` | leave the scale where it is on the photo instead of centring it |
| `--scale-cm 10` | force the scale length if the count of squares does not suit |
| `--margin-cm 0.5`, `--gap-cm 0.5` | margin around the object, gap between ceramic and scale |
| `--no-original-layer` | PSD 2 to 4 times lighter (no hidden photo layer) |
| `--no-original-copy` | do not copy the original photo into `outlined_result` |
| `--no-psd` | no PSD (TIFF only) |
| `--no-control` | no `to_control` previews |
| `--compression zip` | slightly smaller TIFF files (LZW by default, the most compatible) |
| `--default-ppi 300` | resolution used when there is no scale |
| `--no-scale` | do not look for a scale |
| `--ai` | AI second opinion, which can only remove background (see above) |
| `--ai-model birefnet` | with `--ai`: BiRefNet model instead of IS-Net (more precise, much slower) |
| `--ai-device cpu` | with `--ai`: processor instead of the graphics card |
| `-o FOLDER` | write everything into this folder |
| `--open` | open the result folder at the end |
| `-j 4` | number of photos processed in parallel |
| `-v` | show the details of errors |

## Limits

- The measurement is right only if the scale is **in the plane of the object** (at the same height).
- The background must be plain and different from the ceramic: light (the intended situation) or black
  velvet. On velvet, the scale was found on 41 of 42 photos of a 2025 sample (5, 10 and 20 cm
  checkerboards), but less often on small old photos (448 px: 12 of the 14 that show a scale, plus one of
  doubtful length; the last one, squares of 13 px in three rows, needs the manual scale).
- A very light object on a white background (white paste, flint cortex, chalk spindle whorl) cannot be
  told from the background by its colour or its grain where it is almost white: parts of it may be lost.
  Photograph such objects on a darker background (grey or black), or use *One click on the object* in
  *Review…*, which is told which object to cut out.
- When the ceramic fills almost the whole frame (close-up of a vessel base), the background is taken from
  the edges of the photo.
- Scale forms tested: black/white/red checkerboard (one or two rows, digits inside the squares allowed),
  single black/white row, ruler graduated in millimetres.
  Another form will most often be flagged `_to_be_verified`.

## JPEG or TIFF?

TIFF (LZW or ZIP) is lossless: it adds no degradation to the original JPEG. On the contrary, each new save
as JPEG compresses the image again and adds artefacts, especially on the sharp edges of the cut-out. TIFF
also keeps the transparency and the 1:1 resolution.

## RAW photos

RAW files straight from the camera are read as well: DNG, CR2, CR3 (Canon), NEF, NRW (Nikon), ARW
(Sony), ORF (Olympus), RW2 (Panasonic), RAF (Fujifilm), PEF (Pentax), SRW (Samsung), 3FR, IIQ. They are
developed by LibRaw (the `rawpy` package) with the white balance of the camera, in sRGB, 8 bits, turned
upright; the camera, lens and date are read from them for the report. The windows (*Set scale…*,
*Review…*, *Batch renaming…*) show them developed the same way. The original copy in `outlined_result` is
the RAW file itself; the TIFF and PSD files hold the developed image. For a precise colour rendering,
develop them yourself (Lightroom, darktable…) and give Gerbil the TIFF files.

## The .exe version (computers without Python)

**`Gerbil_Setup.exe`** (about 100 MB) is the one file to send: double-click it, keep or change the folder
(by default `%LOCALAPPDATA%\Programs\Gerbil`, no administrator rights needed), tick the desktop shortcut
or not, then *Install*. Gerbil goes in the Start menu and in Windows *Settings > Apps > Installed apps*,
from where it is removed (or with `Uninstall.bat` in its folder; photos and results are never touched).
Running a newer `Gerbil_Setup.exe` updates the installed version and keeps the AI models already
downloaded. The setup is not signed either: "Windows protected your PC" > *More info* > *Run anyway*.

Without the installer, the `Gerbil` folder (or `Gerbil.zip`) works as it is, neither Python nor packages
needed, on Windows 10 or 11 (64-bit):

- **`Gerbil.exe`**: the interface (purple gerbil icon).
- **`gerbil_cli.exe`**: the processing engine, used by the interface. Folders can also be dropped on it,
  or on `Gerbil_drop.bat` (which keeps the `set OPTIONS=` line for the settings).
- The AI second opinion is included; its model is downloaded at its first use into a `models` folder next
  to the .exe files (or copy this `models` folder from another computer).

To distribute it: copy `dist\Gerbil.zip` to the other computer, right-click > *Extract All*, then
double-click `Gerbil.exe` (desktop shortcut: right-click > *Send to* > *Desktop*). The .exe files are not
signed: at the first launch, Windows may show "Windows protected your PC"; click *More info*, then
*Run anyway*.

**The .exe files need their `_internal` folder** (about 40 items, with `python314.dll` and
`base_library.zip`), next to them and from the same build. Always send the whole `Gerbil.zip` and
extract it entirely; never copy the .exe files alone. Typical messages when it is missing or incomplete:
"Failed to load Python DLL ... python314.dll" (no `_internal` folder) or "Failed to start embedded python
interpreter: Failed to import encodings module" (`_internal` incomplete, from another build, or partly
removed by an antivirus). Fix: delete the folder and extract `Gerbil.zip` again.

**Rebuild the .exe version** after a change of the scripts: double-click **`build_exe.bat`** (on a computer
with Python; about 5 minutes the first time). It prepares its own environment in `build\`, compiles with
PyInstaller (recipes `gerbil.spec` and `packaging\gerbil_setup.spec`) and produces `dist\Gerbil\`,
`dist\Gerbil.zip` and the installer `dist\Gerbil_Setup.exe`, which holds the zip. Close
`Gerbil.exe` first (the .bat checks it): the new version is built aside and replaces `dist\Gerbil` only
once it is complete. For everyday use, better work with a copy extracted from the zip somewhere else than in
`dist`. The icon is in `icons\` (`draw_gerbil.py` redraws it). The `build\` folder (about 400 MB) can be
deleted: it is recreated at the next build.

To check a built version without touching your own settings:
`Gerbil.exe --selftest FOLDER photo1.jpg photo2.jpg` processes the photos into FOLDER, writes
`selftest.txt` there ("exit code: 0" when all is well) and closes.

## Results folder

Keep the results apart from the photos (the default: an `outlined_result` folder next to them). If the
results are written in the folder of the photos, Gerbil's own files (`_outlined.tif`, `_to_control.jpg`…)
are recognised and never processed again as photos; the interface warns when a folder of photos is
chosen as the results folder.

## Folder layout

```
gerbil.py, gerbil_gui.pyw, gerbil_plates.py   the program (engine, interface, plates)
gerbil_tools.py                              inventory (CSV) and thumbnails
Gerbil.bat, Gerbil_drop.bat, Install.bat     launchers of the Python version
build_exe.bat, gerbil.spec, packaging\       building the .exe version and the installer
requirements.txt                             Python packages
icons\                                       icon (draw_gerbil.py redraws it)
fonts\                                       fonts of the interface (SIL Open Font License)
docs\                                        PSEUDOCODE.txt, ROADMAP.md, REFERENCES.md, guides (.odt)
tests\                                       automatic checks on synthetic photos (py -3 -m pytest tests)
models\, build\, dist\                       downloaded or built: not in the repository
```

Photos are never put in the repository (their owners' rights): the reference photos used to check every
change stay on the developer's computer.

## Licence and source code

Gerbil is free software under the **GNU General Public License v3 or later** (`LICENSE`): you may use,
study, share and modify it; modified versions you distribute stay under the same licence. Source code:
https://github.com/EloisCharbonnel/gerbil. Contributing: `CONTRIBUTING.md`.

## Installation on another computer (Python version)

1. **Copy the whole folder**: `gerbil.py`, `gerbil_gui.pyw`, `gerbil_plates.py`, `gerbil_tools.py`, the `.bat` files, `requirements.txt`,
   `README.md`, the `icons` and `fonts` folders (and the `models` folder only for the AI option: otherwise it is
   downloaded at its first use).
2. **Double-click `Install.bat`** (once per computer, internet connection needed):
   - if Python is not installed, it offers to install it with winget, the installer built into Windows
     (otherwise: install it from https://www.python.org/downloads/), then run `Install.bat` again;
   - it then installs what is missing among numpy, OpenCV, Pillow and rawpy (about 2 minutes);
   - finally it offers the AI option (onnxruntime, about 60 MB), which is optional.
3. Open the interface with **`Gerbil.bat`** (or use `Gerbil_drop.bat`).

It also works without `Install.bat`: the interface shows the missing packages in a banner with an
**Install now** button, and `Gerbil_drop.bat` installs them at its first launch. Ticking "AI second
opinion" likewise offers to install onnxruntime when it is missing.

The launchers find Python through the `py` command (python.org installation) or, failing that, `python`
(Microsoft Store Python). The interface uses tkinter, which comes with Python for Windows ("tcl/tk and
IDLE" option, ticked by default).

By hand, on the command line:

```
py -3 -m pip install -r requirements.txt
py -3 -m pip install onnxruntime-directml
```

(the second line only for the AI option; `onnxruntime-directml` uses the graphics card on Windows, plain
`onnxruntime` uses only the processor.)
