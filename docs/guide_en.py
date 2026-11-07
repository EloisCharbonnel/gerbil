"""Text of the guide in English (parts I to III). Part IV, the reference of the functions, is made from the
code by docs/make_guide_odt.py, with the docstrings. Same blocks as docs/fr/guide_fr.py:
("h1"|"h2"|"h3", title), ("p", text), ("ul"|"ol", [items]), ("code", text), ("tip"|"warn"|"note", text),
("table", [header row, rows...]), ("figure", image, caption), ("defs", [(term, definition)...]),
("annotated", file, function, [explanation of each line]), ("pagebreak",).
In the texts: **bold**, *italic*, `code`."""

TITLE = "Gerbil"
SUBTITLE = "Guide for archaeologists and to the code"
TAGLINE = "Outline, measure, publish: using Gerbil and understanding what it does, function by function"
FOOTER = "Gerbil — Guide for archaeologists and to the code"
LABELS = {
    "contents": "Contents", "foreword": "Foreword", "line": "line", "lines": "lines", "function": "function",
    "class": "class", "method": "method", "untranslated": "", "helper": "(small helper: see the code)",
    "tip": "Tip", "warn": "Warning", "note": "Good to know", "code_col": "Code", "expl_col": "What the line does",
    "part4": "Part IV — Reference of the functions, file by file",
    "part4_intro": "Every file of the program, its sections (the \"# ----\" banners of the code) and, in each, all "
        "its functions and classes, with their explanation and their line number in the file. The name in purple "
        "is the one to look for in the code (Ctrl+F); in brackets, what the function receives.",
    "generated": "This part is written automatically from the code (docs/make_guide_odt.py): it always follows the "
        "version of the program.",
    "version": "Version", "licence": "Free software under the GNU GPL v3 or later",
    "date": "Guide made on",
}
FILE_ROLES = {}                         # the roles of docs/make_code_guide.py
SECTION_TITLES = {}                     # the banners of the code, as they are

FOREWORD = [
    ("p", "Gerbil outlines archaeological finds photographed with a scale and gives them back **at their real "
          "size**: dropped into Illustrator, they show at 1:1, without any computation or scaling by hand. It also "
          "prepares the plates, the file names, the metadata and the inventories."),
    ("p", "This guide is for those who **use** Gerbil as well as for those who want to **understand** what it "
          "does, to explain it in a report, check it or change it. It can be read in any order:"),
    ("ul", ["**Part I — Using Gerbil**: from the installation to the plates, step by step.",
            "**Part II — Understanding the processing**: every step explained in plain words, with the thresholds "
            "and the measured precision; enough to write a methodology.",
            "**Part III — Reading the code**: how the program is organised, the useful Python notions, and real "
            "functions explained line by line.",
            "**Part IV — Reference**: every function and class of the program (more than 400), with its line "
            "number."]),
]

PARTS = [
    # =========================================================================================== PART I
    ("h1", "Part I — Using Gerbil"),

    ("h2", "1. What Gerbil does"),
    ("p", "Gerbil is given a folder of photos of finds (sherds, metal, lithics, bone, glass…) lying on a plain "
          "background with a scale. For each photo, it:"),
    ("ol", ["**finds the scale** (black / white / red checkerboard, single row or millimetre ruler) and measures "
            "it: how many pixels make one centimetre on *this* photo;",
            "**outlines the object**: separates it from the background, discards the labels, the supports, the "
            "colour charts and the scale itself;",
            "**writes the files**: a layered PSD and transparent TIFF files whose resolution is the real one, so "
            "that the object shows at its real size in Illustrator, Photoshop or InDesign;",
            "**flags its doubts**: everything that deserves a look gets the `_to_be_verified` suffix."]),
    ("p", "The measurement comes from the scale of each photo, not from the EXIF data: the camera, the lens and "
          "the distance do not matter. A photo taken closer simply gives more pixels per centimetre."),
    ("figure", "fig_photo", "A photo to process (synthetic photo: an invented sherd and a 10 cm checkerboard "
                            "scale)."),

    ("h2", "2. Installing Gerbil"),
    ("h3", "On a computer without Python (the simplest)"),
    ("ol", ["Double-click **Gerbil_Setup.exe** (one file, about 100 MB).",
            "Keep the folder offered (no administrator rights needed), tick the desktop shortcut if wanted, then "
            "*Install*.",
            "Open Gerbil from the Start menu."]),
    ("warn", "The programs are not signed: at the first launch, Windows may show \"Windows protected your PC\". "
             "Click *More info*, then *Run anyway*."),
    ("p", "To update, run a newer Gerbil_Setup.exe: the AI models already downloaded are kept. To uninstall: "
          "*Settings > Apps > Installed apps*. Photos and results are never touched."),
    ("h3", "With the Python scripts"),
    ("p", "Copy the whole folder of the program, double-click **Install.bat** once (it installs Python if needed, "
          "then numpy, OpenCV, Pillow and rawpy), then open the interface with **Gerbil.bat**."),

    ("h2", "3. Taking the photos"),
    ("ul", ["**The scale in the plane of the object**: at the height of the face photographed. A scale lying on "
            "the table under a thick object gives a wrong measurement (the object is closer to the lens).",
            "**A plain background**, different from the object: light (the intended situation) or dark (black "
            "velvet, felt). A slight lighting gradient does no harm.",
            "**A known scale**: black / white / red checkerboard of 5, 10 or 20 cm (one or two rows, digits "
            "printed in the squares allowed), single black and white row, or ruler graduated in millimetres. "
            "Another scale can be *learned* (see the site profiles).",
            "**The whole object in the frame**, not touching the edge of the photo.",
            "**Formats**: JPEG, TIFF, PNG or RAW (DNG, CR2, CR3, NEF, ARW, ORF, RW2, RAF…)."]),
    ("tip", "Mounting putty: a blue putty (Blu-Tack type), or putty hidden behind the object, is never mistaken "
            "for a light sherd."),

    ("h2", "4. A first run, step by step"),
    ("p", "The window of Gerbil follows the work: a column on the left gives the five steps, each with its page. "
          "The steps can be visited in any order. The interface is in French and English (FR / EN at the bottom "
          "of the column)."),
    ("ol", ["**01 Source photographs**: *Add folder…* and choose the folder of the photos (their number is "
            "shown). Several can be added, or folders dropped on the Gerbil icon.",
            "**02 Naming and metadata** (optional): the summary of the batch renaming of the folder, and the button "
            "that opens it.",
            "**03 Processing**: keep the default settings for a first try (resting the mouse on a setting shows its "
            "explanation), then *Run*. The scale bar fills in; the table gives each photo, its state (green: ok, "
            "terracotta: to verify, red: failed), its scale and what to do, in a few words.",
            "**04 Review**: the photos to look at with their problem; *Review* opens the correction window. A "
            "double-click on a row opens straight what needs fixing.",
            "**05 Publication**: plates, inventory, thumbnails. *Open results* opens the `outlined_result` folder, "
            "created next to the photos."]),
    ("p", "Count 3 to 4 seconds per photo; several photos are processed at the same time."),

    ("h2", "5. What comes out"),
    ("p", "All the files of a photo keep its name, so that they follow one another in the Explorer:"),
    ("table", [["File", "Content"],
               ["`NAME.JPG`", "Copy of the original photo (with the IPTC metadata added, without recompression)."],
               ["`NAME.psd`", "Layered Photoshop file: *Original photo* (hidden, the whole photo), *Scale*, "
                              "*Ceramic*, with layer masks editable with the brush (white = show, black = hide)."],
               ["`NAME_outlined.tif`", "The object alone, transparent background, at the 1:1 resolution."],
               ["`NAME_outlined_scale.tif`", "The object and its straightened scale under it, transparent."],
               ["`to_control/NAME_to_control.jpg`", "The control preview."],
               ["`outlined_report.csv`", "The report: one row per photo, opens in Excel."]]),
    ("figure", "fig_control", "The control preview: outline of the cut-out in green, scale in magenta, centimetres "
                              "found in orange, and the measurement written at the top."),
    ("p", "Colours of the control preview:"),
    ("table", [["Colour", "Meaning"],
               ["Green", "Outline of the cut-out."],
               ["Magenta", "Frame of the scale found."],
               ["Orange", "Centimetres read on the scale."],
               ["Red", "What was discarded (label, chart, small isolated element), or possible mounting putty."],
               ["Blue", "Plexiglass support removed."],
               ["Cyan", "Background removed by the AI second opinion."]]),
    ("h3", "The _to_be_verified suffix"),
    ("p", "When something is doubtful, all the files written for the photo get this suffix (e.g. "
          "`NAME_outlined_to_be_verified.tif`): type `to_be_verified` in the search box of the Explorer to find "
          "them. There is a doubt when:"),
    ("ul", ["the scale is not found;",
            "it is not 5, 10 or 20 cm long, or its squares / graduations are irregular or partly hidden;",
            "an area looks like mounting putty;",
            "a colour chart touches the object;",
            "the object touches the edge of the photo;",
            "a required piece of information is missing, or the name does not follow the naming rule."]),
    ("p", "Processing a folder again replaces the files of the photos processed again; the suffix goes when the "
          "doubt is lifted. The copy of the original photo always keeps its exact name."),

    ("h2", "6. The report outlined_report.csv"),
    ("p", "One row per photo, \";\" separator and decimal comma (Excel). Statuses: `ok`, `to verify`, `failed` (no "
          "object found), `error`. Main columns:"),
    ("table", [["Column", "Content"],
               ["`file`, `output_name`", "Name of the photo, name of the output files (batch renaming)."],
               ["`status`, `to_verify`", "Status, and the reasons for the doubt."],
               ["`scale_found`, `scale_type`", "Scale found? Its kind: `checkerboard`, `ruler`, `manual` (given "
                                               "by hand), `learned`."],
               ["`squares`, `scale_length_cm`", "Number of squares, length of the scale."],
               ["`px_per_cm`, `ppi_1_1`", "The measurement: pixels per centimetre, and the 1:1 resolution it "
                                          "gives."],
               ["`ceramic_width_cm`, `ceramic_height_cm`", "Size of the outlined object, in cm."],
               ["`pieces`", "Number of pieces outlined."],
               ["`camera`, `lens`, `focal_mm`, `date_taken`", "Shooting information (EXIF)."],
               ["`notes`, `duration_s`", "Remarks of the processing, duration."]]),
    ("p", "The fields of the batch renaming (site, US, number…) are added as columns after these."),

    ("h2", "7. Review and correct"),
    ("p", "The review window shows the photos one by one, **doubtful and failed ones first**, with the outline of "
          "the cut-out (green, background dimmed) and of the scale (magenta)."),
    ("table", [["Tool", "Use"],
               ["*One click on the object (more precise)*", "Click each object to keep: Segment Anything cuts it out "
                    "(Shift + click removes one). More reliable on difficult photos, because the program is **told "
                    "which object to cut out** instead of guessing what is a sherd, a label, a shadow or the "
                    "background."],
               ["*Erase* / *Add*", "Brush (adjustable size) or lasso (draw around an area) to remove or add."],
               ["*Remove a piece*", "One click removes a whole piece (shadow, background patch)."],
               ["*Undo* (Ctrl+Z), *Reset photo*", "Undo the last action, or all those of the photo."],
               ["Orientation", "Draw a line along the rim: it becomes horizontal, the object below it. Or turn by "
                               "quarter turns."],
               ["*Fix the scale…*", "Opens the manual scale of the photo."],
               ["*Accept and next*", "Saves the corrections and **exports the photo again at once**, in the "
                                     "background (\"exporting…\", then \"✓ exported\")."]]),
    ("p", "Navigation: mouse wheel to zoom, scroll bars, right or middle button, Space + drag or the arrow keys to "
          "move the view; R to see the whole photo again."),
    ("note", "The corrections are saved **next to the photos**, in a `gerbil_edits` folder: every later run keeps "
             "them. Reopened later, the window shows the corrections already made. Keep this folder with the "
             "photos."),

    ("h2", "8. Giving the scale by hand"),
    ("p", "When the scale of a photo is not found or wrongly read: select the photo, *Set the scale by hand…*, click the two "
          "ends of a known length (for example 0 and 5 cm, along the middle of the scale), give that length and "
          "the width of the scale, then *Save*. The photo can be processed again at once."),
    ("p", "The scale is kept in `gerbil_scales.json`, in the folder of the photos; it prevails over the automatic "
          "search at every run (report: `scale_type` = `manual`). At the end of a run, Gerbil offers to set in a row "
          "all the scales it did not find (*Save and next*, *Skip this photo*, *Stop*)."),

    ("h2", "9. Batch renaming and information of the photos"),
    ("p", "*Open the batch renaming…* gives a folder of photos **fields** (by default *Site*, *Sector*, *US*, *Object "
          "number*, *Material*, *View*), a **name template** and a **naming rule**. Everything is saved in "
          "`gerbil_project.json`, next to the photos."),
    ("ul", ["**Name template**, e.g. `{site}_{sector}_US{us}_{number}_{material}`: the output files take this name "
            "(`QSR25_A5_US7549_187_metal_outlined.tif`). **The original photos are never renamed.**",
            "**Values**: those common to all the photos (the site), and a table with one row per photo. As in "
            "Excel: double-click to edit, **fill handle** at the corner of a cell to copy down (with Ctrl: a series "
            "187, 188, 189…), Ctrl+D, *Set for selected…*, *Number the selected…*.",
            "**Import CSV / Excel**: an inventory whose first row holds the column names; the column of the photo "
            "names is found by itself.",
            "**Naming rule** (optional): a regular expression read as PowerShell's `-match`. The helper writes it "
            "from tick boxes (capitals only, ends with a number…) and shows the equivalent PowerShell line, to "
            "learn from."]),
    ("p", "The information goes into the report (one column per field) and **into the PSD and TIFF files** (XMP: "
          "title = output name, keywords = values)."),

    ("h2", "10. IPTC metadata"),
    ("p", "In *Batch renaming*, *IPTC metadata…* fills the standard IPTC fields (read by Bridge, Lightroom, "
          "darktable, the Windows Explorer): for each field (title, description, keywords, creator, copyright, "
          "place…), a text where `{field}` is replaced by the value of the photo and `{name}` by the output name. "
          "A text without braces is the same for every photo (copyright, creator)."),
    ("p", "They are written into the PSD and TIFF files, into the copy of the original (JPEG: without recompressing "
          "the image) and, if ticked, into a `NAME.xmp` file next to each original photo. The photos themselves "
          "are never changed, and a `.xmp` written by another program is never replaced."),

    ("h2", "11. Site profiles and learned scales"),
    ("p", "A **site profile** gathers what is known of the photos of a site or a campaign, chosen once under *SITE "
          "PROFILE* (*New…*, *Edit…*):"),
    ("ul", ["the **background**: found by Gerbil, light, or dark (velvet, felt);",
            "**learned scales**: *Learn a scale from a photo…*, click the two ends of the scale and give the width "
            "of its printed band. Gerbil keeps its image and finds it again on the other photos. Learn **each "
            "copy** used: two prints of the same model may differ by 1 %;",
            "the **options** of the main window (*Keep the options of the main window*)."]),
    ("p", "By default a learned scale is a second chance, used when the usual reading fails or is doubtful; *Look "
          "for the learned scales first* uses it first. *Put next to the photos…* copies the profile as "
          "`gerbil_profile.json` into a folder of photos: it then applies to these photos, for the whole team."),

    ("h2", "12. Plates"),
    ("p", "*Plates* lays out the outlined objects of a results folder at a chosen scale (1:1, 1:2, 1:3…) and "
          "writes them as **SVG** files (`plates` folder), which open in Illustrator or Inkscape at their true size: "
          "1 cm of the object = 1 cm ÷ scale on the paper."),
    ("ul", ["Objects in **rows**, in the chosen order (name, US, material…), with a **caption** under each one "
            "(`{name}`, or `{site}_{us}_{number}`…). *Group by* starts a row or a page at each value.",
            "Graphic **scale bar** set as in QGIS (style, length, segments, colours, font), remembered as your "
            "house style.",
            "**One scale per plate**; an object too large goes to 1:1.5, 1:2, 1:3… on plates of its own. *Scale "
            "per object…*, or a right-click on an object of the preview, chooses its scale.",
            "**Scale by material**: ceramics and glass at 1/3, iron at 2/3, stone at 1/3 by default (editable rules "
            "`word=reduction`).",
            "**Drawings beside the photos**: a folder of drawings (`.svg`, or `.ai` `.pdf` `.eps` converted by "
            "Inkscape); a drawing named like the object is placed beside its photo, at the same scale, **as "
            "vectors** (editable in Illustrator).",
            "**Title** and **file names** from templates (`{page}`, `{pages}`, `{group}`, `{scale}`).",
            "Optional **measurements** on a hidden layer: layout guides, not data."]),
    ("p", "The preview shows the pages as they will be written; the wheel zooms, ◀ ▶ turns the pages."),

    ("h2", "13. Inventory and thumbnails"),
    ("ul", ["*Inventory*: one row per file of the chosen folders (photos, drawings, 3D models), with "
            "folder, kind, size, date, **the fields read from the name** (same template as the batch renaming), "
            "and for the images their size, resolution, date taken and camera. The window shows the **PowerShell "
            "line** that makes the same inventory with Windows alone, to copy and learn from.",
            "*Thumbnails*: reduced copies for databases (128 to 1,024 px), transparent PNG or JPEG on white, "
            "transparent margin cut off."]),

    ("h2", "14. The options"),
    ("p", "The same options exist in the interface and on the command line (`py gerbil.py FOLDER --option`, or "
          "`gerbil_cli.exe FOLDER --option` in the .exe version):"),
    ("table", [["Option", "Effect"],
               ["`--background white`", "TIFF on a white background instead of transparent."],
               ["`--remove-putty`", "Removes the putty found (otherwise only flagged)."],
               ["`--layout original`", "Leaves the scale where it is on the photo, instead of centring it under the "
                                       "object."],
               ["`--scale-cm 10`", "Forces the length of the scale."],
               ["`--margin-cm 0.5`, `--gap-cm 0.5`", "Margin around the object, gap between object and scale."],
               ["`--no-original-layer`", "PSD 2 to 4 times lighter (no layer of the whole photo)."],
               ["`--no-original-copy`", "Does not copy the original photo into the results."],
               ["`--no-psd`, `--no-control`", "No PSD; no control previews."],
               ["`--compression zip`", "Slightly smaller TIFF files (LZW by default, the most compatible)."],
               ["`--default-ppi 300`", "Resolution used when there is no scale."],
               ["`--no-scale`", "Does not look for a scale."],
               ["`--ai`, `--ai-model birefnet`, `--ai-device cpu`", "AI second opinion (it can only remove "
                    "background); more precise but slower model; force the processor."],
               ["`--profile FILE`", "Site profile to use."],
               ["`-o FOLDER`, `--open`, `-j 4`, `-v`", "Output folder; open the results at the end; photos in "
                    "parallel; details of the errors."]]),

    ("h2", "15. The files Gerbil writes next to the photos"),
    ("p", "What is decided is saved **next to the photos**, in small files, so that a later run or a colleague "
          "finds it again. To archive with the photos:"),
    ("table", [["File", "Content"],
               ["`gerbil_project.json`", "Batch renaming: fields, template, rule, values, IPTC settings."],
               ["`gerbil_scales.json`", "Scales given by hand."],
               ["`gerbil_edits/`", "Corrections of the review window (corrected masks, angles)."],
               ["`gerbil_profile.json`", "Site profile put in the folder."],
               ["`NAME.xmp`", "IPTC metadata next to the photo, if asked."]]),

    ("h2", "16. Limits"),
    ("ul", ["The measurement is right only if the scale is **in the plane of the object**.",
            "The background must be plain and different from the object. An opaque white or cream support lodged "
            "in a hollow is not recognised: erase it in *Review* or in Photoshop.",
            "A very light object on a white background (white paste, flint cortex, chalk spindle whorl) cannot be "
            "told from the background by its colour or its grain where it is almost white: parts may be lost. "
            "Photograph such objects on a darker background (grey or black), or use *One click on the object* in "
            "*Review*, which is told which object to cut out.",
            "Another form of scale will most often be flagged to verify: learn it in a site profile, or give it by "
            "hand.",
            "For a precise colour rendering of RAW files, develop them yourself (Lightroom, darktable) and give "
            "Gerbil the TIFF files."]),

    # =========================================================================================== PART II
    ("pagebreak",),
    ("h1", "Part II — Understanding the processing"),
    ("p", "This part explains what Gerbil does, step by step, without programming. The thresholds given are those "
          "of the code; `docs/PSEUDOCODE.txt` details them all."),

    ("h2", "1. The path of a photo"),
    ("ol", ["**Reading**: the photo is opened and turned upright (EXIF orientation); a RAW file is developed.",
            "**Reduced copy** of 1,500 px for the analysis: faster, and enough to find things; the fine "
            "measurements are made again at full resolution.",
            "**Background model**: the colour of the background at every point of the photo.",
            "**Scale**: manual if one was given, else looked for (checkerboard, ruler, dark background), else a "
            "learned scale of the site profile.",
            "**Cut-out**: what differs from the background, sorted, refined at full resolution.",
            "**Mounting putty** looked for along the outline.",
            "**Files**: layers, PSD, TIFF at the 1:1 resolution, metadata, preview, row of the report."]),

    ("h2", "2. Seeing colours as the eye does: CIELAB"),
    ("p", "A photo is made of red, green and blue pixels (RGB). But in RGB, two colours that look \"equally "
          "different\" may have very different gaps in numbers. Gerbil therefore works in **CIELAB**: **L\\*** is "
          "the lightness (0 = black, 100 = white), **a\\*** goes from green to red, **b\\*** from blue to yellow. In "
          "this space, a distance between two colours roughly matches what is perceived, which makes it possible "
          "to say in numbers that a pixel is \"different from the background\"."),
    ("p", "The distance of a pixel to the background is computed as:"),
    ("code", "d = sqrt( (0.5 × ΔL*)² + Δa*² + Δb*² )"),
    ("p", "Lightness counts only for half: a **soft shadow** mostly changes the lightness of the background, not its "
          "colour; it thus stays out of the object. The **chroma** C\\* = sqrt(a\\*² + b\\*²) says whether a "
          "colour is vivid or grey; the **hue** h is its angle (red, yellow, green, blue)."),

    ("h2", "3. The background model"),
    ("p", "The background is never perfectly even: the lighting makes a gradient. Gerbil therefore does not take "
          "one background colour, but a **surface** that follows this gradient: for each of the L\\*, a\\* and b\\* "
          "channels, a polynomial of degree 2 in x and y (a slightly curved \"sheet\"), fitted by **least squares** "
          "on the background pixels."),
    ("ol", ["Start: the median colour of the photo (the background is the largest part). When the object fills the "
            "frame, the median of a 3 % band along the edges is taken instead.",
            "The pixels close to this colour (distance < 12) are the first background.",
            "Four times: the sheet is fitted on these pixels, then only those very close to it (distance < 6) are "
            "kept as background. The object and the scale, too different, are left out of the fit."]),
    ("p", "When the median lightness of the background is under 35, the background is **dark** (velvet, felt): "
          "several rules then change (labels, edges, scale)."),

    ("h2", "4. Finding the object"),
    ("ul", ["**Distance to the background** of each pixel, with the background sheet.",
            "**Hysteresis threshold** (thresholds 8 and 18): the regions more different than 8 that contain at "
            "least one pixel more different than 18 are kept. A faint edge is thus kept when it belongs to a clear "
            "object, but an isolated faint patch is not (the principle of Canny's edge detector, applied to "
            "regions).",
            "**Mathematical morphology**: an *opening* (shrink, then grow back) erases dust and thin threads; a "
            "*closing* (grow, then shrink back) fills small gaps.",
            "**Holes**: a hole whose mean colour is that of the background and of at least 0.02 cm² is a true "
            "opening (handle, perforation) and stays transparent; the others (gloss reflection, light concretion) "
            "are filled."]),

    ("h2", "5. Sorting"),
    ("p", "Not everything that differs from the background is the object. The pieces found are sorted:"),
    ("table", [["Element", "How it is recognised"],
               ["The scale", "Its zone (enlarged for its support or its putty) is removed; an object lying close to "
                             "it is kept when it reaches at least 8 mm from it and clearly differs from the "
                             "background."],
               ["Scale, ruler, label without a measured scale", "When the scale is not measured (not found, "
                    "of another kind, or `--no-scale`), it stays out of the cut-out: its outline is made of long "
                    "straight sides at right angles (even an L-shaped bar, or a ruler whose ticks make a comb), "
                    "and its content is that of a print (black and white, uncoloured, or a full rectangle). On 191 "
                    "open photos, no object discarded this way: a pin, a black blade or a long bone tool stay "
                    "objects."],
               ["Cast shadow (light background)", "Darker than the background but of its colour, smooth, along the "
                    "outline, and it fades into the background: its outer edge is soft (penumbra), the edge of an "
                    "object is sharp. A dark, smooth part of the object (black gloss, obsidian, grey flint) does "
                    "not touch the background that way and stays. Blue outline in the preview."],
               ["Plexiglass support", "Colour almost that of the background (distance < 15), sticks out of the "
                                      "object, as light as or whiter than the background. A reflection on a black "
                                      "gloss, darker and along the object, is left alone."],
               ["Colour chart", "Many vivid hues: at least 5 hue sectors out of 12, with a warm one, a green and a "
                                "blue. A ceramic, even painted, covers 2 at most (1,763 photos tested); the charts 5 "
                                "to 9."],
               ["Labels, writing", "What lies on the other side of the scale; what is everywhere thinner than 1.7 mm "
                                   "(writing, thread, line of a bag); small isolated elements more than 8 mm from "
                                   "the object (on a light background)."],
               ["Paper label (dark background)", "Light and rectangular (it fills 85 % of its rectangle): white, "
                    "bluish white (optical brighteners of the paper) or pale yellow; or very rectangular (95 %) and "
                    "light, whatever its colour — a broken sherd never fills its rectangle that much."]]),
    ("p", "A label touching a sherd by a corner is cut at the narrow join. When the only object of a photo looks "
          "like a label (small, pale, square sherd), it is kept and the photo is flagged."),
    ("figure", "fig_dark", "On dark felt: the paper label is recognised and discarded (red outline), the sherd is "
                           "kept (green outline)."),

    ("h2", "6. Refining and softening the edge"),
    ("p", "The first cut-out is made on the reduced copy; it is made again **at full resolution** in a band around "
          "its outline. One part is \"sure\" (well inside and different from the background), another "
          "\"allowed\" (near the outline): the final edge is looked for in the band, pixel by pixel. The mask is "
          "then softened (Gaussian blur of 0.8 px): a sharp edge without staircase, like a cut-out made by hand."),
    ("p", "On a dark background the edge of a light object is a ramp several pixels wide (slight blur, shadow). The "
          "edge is placed **in the middle of this ramp**, then the colour of the last pixels of the edge is "
          "replaced by that of the object just inside, without moving the outline: no dark line remains."),

    ("h2", "7. Reading a checkerboard scale"),
    ("ol", ["**Spot** the ink: black and vivid red pixels, joined into elongated groups (a scale is at least 2.5 "
            "times longer than wide).",
            "**Straighten**: a crop is extracted and turned so that the scale is horizontal.",
            "**Read the squares**: column by column, which row is inked (top, bottom, both, none); the runs of "
            "similar columns are the squares. Runs too short (digits, arrows) are absorbed by their neighbours.",
            "**Second reading** when digits are printed in the squares (\"5\", \"10\", \"cm\"): the **boundaries** "
            "between squares are looked for (where the ink goes from one row to the other), and a regular \"comb\" "
            "is fitted on them over the whole length.",
            "**Measure at full resolution**: px/cm = length of the squares ÷ number of squares (one square = 1 cm), "
            "at the sub-pixel (where the profile crosses half the contrast).",
            "**Turn upright**: the printed signs (\"5\", \"10\", \"cm\") are compared with templates of digits drawn "
            "with 12 common fonts, upright and turned over. On 1,265 scales of known orientation: no error."]),
    ("p", "Checks: usual length (5, 10 or 20 cm), regular squares (gap < 15 %). A scale cut by the edge of the "
          "photo is measured on its complete squares. On a dark background the black squares merge with the "
          "background: the scale is looked for from its light squares, then everything around it is painted white "
          "to read it as on a light background."),

    ("h2", "8. Reading a millimetre ruler"),
    ("p", "The graduations are thin, parallel dark strokes. Gerbil spots them (\"black-hat\" filter, which brings out "
          "small dark details), groups them into regular rows, then fits a regular sequence x = start + step × k on "
          "the fifty or so graduations. Measuring one step over ~50 intervals gives a precision of about **0.1 %**. "
          "The centimetre graduations, longer, give the length (5 or 10 cm)."),

    ("h2", "9. Learned scales"),
    ("p", "For a scale of another form, its two ends are shown once: Gerbil keeps its straightened image. On "
          "another photo, it looks for it in two steps:"),
    ("ul", ["**Roughly**: characteristic points (SIFT method: corners, details recognisable even turned or at "
            "another size) are matched between the learned image and the photo; a common position, size and angle "
            "are found by **RANSAC** (many small groups of points are tried, and the explanation most points agree "
            "with is kept).",
            "**Finely**: the learned image is aligned on the photo by correlation (ECC method), which measures the "
            "length within 0.1 % when it is the same physical scale (0.05 % measured)."]),

    ("h2", "10. Mounting putty"),
    ("p", "Gerbil looks along the outline for two hollows (concavities) that cut off a part of the object. This "
          "part is possible putty when it is at once **smoother** (half the texture), **of another colour**, **less "
          "coloured** and **lighter** than the rest. By default it is only flagged (red area): a light, smooth "
          "vessel base looks too much like it to be removed without a check."),

    ("h2", "11. The AI second opinion (option)"),
    ("p", "With `--ai`, a neural cut-out network (IS-Net or BiRefNet) gives its opinion. It can **only remove** "
          "background, never add: an area is removed only when the cut-out keeps it, the AI sees background there, "
          "its colour stays close to the background and it covers at least 0.02 cm². This opens shadowed "
          "perforations, gaps between two sherds, halos along a blurred edge. When the AI is wrong, it is by "
          "keeping too much (label, support): its errors therefore have no effect."),

    ("h2", "12. The one-click cut-out"),
    ("p", "In the review window, the one-click tool uses **Segment Anything** (MobileSAM version, offline, 45 MB): "
          "click the object, it cuts it out. It is more reliable on difficult photos because it is **told which "
          "object** to cut out: it no longer has to guess what is a sherd, a label, a shadow or the background. Its "
          "edge being less precise, Gerbil keeps the edge of its own cut-out where both agree."),

    ("h2", "13. From the measurement to 1:1"),
    ("p", "An image file carries a **resolution**: the number of pixels per inch (ppi). Illustrator uses it to give "
          "a placed image its size. Gerbil therefore writes into each file the resolution measured on the scale:"),
    ("code", "ppi = px/cm × 2.54        (1 inch = 2.54 cm)\nexample: 100 px/cm → 254 ppi: a sherd 600 px wide is 6 cm wide"),
    ("p", "Dropped into Illustrator, the object therefore has its real size. The scale of `NAME_outlined_scale.tif` "
          "measures exactly 5 or 10 cm with Illustrator's ruler: the simplest check. The image is never enlarged or "
          "reduced; only its resolution tag changes."),
    ("p", "The **PSD** is written byte by byte: the *Ceramic* layer holds the original pixels and a **layer mask** "
          "(nothing is erased: a stroke of white brush brings back what was hidden); *Scale* holds the straightened "
          "scale; *Original photo*, hidden, the whole photo aligned on the object. The **TIFF** files are lossless "
          "(LZW), with transparency; a JPEG would compress the image again at every save."),

    ("h2", "14. Metadata"),
    ("ul", ["**EXIF**: the camera information (body, lens, focal length, date, aperture, speed, ISO), copied and "
            "updated.",
            "**XMP**: a packet of structured text written into the files: the measurement of the scale, the output "
            "name, the fields of the batch renaming.",
            "**IPTC Core**: the standard fields of photo libraries (title, keywords, creator, copyright, place), "
            "written into the XMP from the model of the project. In a JPEG, the XMP segment is added without "
            "touching the image data (checked pixel for pixel by the tests)."]),

    ("h2", "15. Plates: from the real object to the paper"),
    ("p", "Each object has its real size, read from the resolution of its TIFF. At the scale 1:r, its size on the "
          "paper is: real size ÷ r. Example: a 6 cm sherd at 1:2 is 3 cm on the plate. The page is first "
          "described as a list of shapes **in millimetres** (rectangles, texts, images, drawings); this same "
          "description is written as SVG and drawn for the preview, which therefore shows exactly what will be "
          "written."),

    ("h2", "16. For a methodology"),
    ("p", "An example of paragraph, to adapt:"),
    ("note", "\"The finds were photographed on a plain background with a scale in the plane of the face "
             "photographed. The photographs were outlined and scaled with Gerbil 2.0 (Charbonnel 2026, free "
             "software, GPL v3). The scale of each photograph is detected and measured automatically "
             "(checkerboard: length of the squares fitted at the sub-pixel; ruler: millimetre step fitted over all "
             "the graduations, precision about 0.1 %), then the real resolution is written into the files, which "
             "gives back the finds at 1:1. The cut-out relies on the colour distance (CIELAB) to a polynomial model "
             "of the background, with a hysteresis threshold; the doubtful cases were flagged by the software and "
             "checked one by one.\""),

    # =========================================================================================== PART III
    ("pagebreak",),
    ("h1", "Part III — Reading the code"),

    ("h2", "1. The files"),
    ("table", [["File", "Role"],
               ["`gerbil.py`", "The engine: everything that processes a photo, and the command line. It knows "
                               "nothing about the windows."],
               ["`gerbil_gui.pyw`", "The interface: the windows. It starts the engine as a separate program and "
                                    "reads what it prints."],
               ["`gerbil_plates.py`", "The SVG plates."],
               ["`gerbil_tools.py`", "The CSV inventory and the thumbnails."],
               ["`packaging/gerbil_setup.pyw`", "The installer."],
               ["`tests/`", "The automatic tests, on synthetic photos."],
               ["`docs/`", "Pseudocode, roadmap, sources, this guide."]]),

    ("h2", "2. How they talk to each other"),
    ("code", "gerbil_gui.pyw  (windows)  --runs-->  gerbil.py / gerbil_cli.exe  (engine, one photo after the other)\n"
             "       |                                   |\n"
             "       |  reads its printed lines          +--> outlined_result/ : PSD, TIFF, previews, report\n"
             "       |  (\"[3/12] NAME: ok ...\")          |\n"
             "       +--> gerbil_plates.py (plates)      +--> reads gerbil_project.json, gerbil_scales.json,\n"
             "       +--> gerbil_tools.py  (inventory)        gerbil_edits/, gerbil_profile.json"),
    ("p", "The interface does not process the photos itself: it builds the command line from the options, starts "
          "the engine (`subprocess`), and reads the lines it prints to show the progress. Some windows also call "
          "functions of the engine directly (`import gerbil`), for instance to read a photo or learn a scale."),

    ("h2", "3. The path of a photo in the code"),
    ("p", "The function `process_photo` of `gerbil.py` calls, in order:"),
    ("ol", ["`load_photo`: reads the file (RAW through `develop_raw`), turns it upright, keeps EXIF and colour "
            "profile.",
            "`BackgroundModel`: the background model, on the reduced copy.",
            "`manual_scale`, else `detect_scale` (which calls `analyze_pattern`, `analyze_comb`, `detect_ruler`, "
            "`_scale_on_dark`…), else `detect_learned_scale`. The result is a `Scale` object.",
            "`outline_ceramic` (or `cutout_from_mask` for a mask corrected by hand).",
            "`find_putty`.",
            "`layout`, then `write_psd`, `write_tiff` (with `make_xmp`), `control_image`, `write_review`.",
            "The row of the report is returned; `main` writes `outlined_report.csv` and the summary."]),

    ("h2", "4. Useful Python notions"),
    ("defs", [("Module, import", "Each file is a module. `import gerbil as g` gives access to its functions "
                                 "(`g.load_photo`); `from PIL import Image` takes one name from a library."),
              ("Function", "`def name(arguments):` takes values and returns a result (`return`). The body of the "
                           "function is the indented block under the `def` line."),
              ("Docstring", "The first string of a function, between triple quotes: its explanation. Part IV shows "
                            "it."),
              ("Class, method, self", "`class Name:` groups data and the functions that work on them (its "
                    "*methods*). The first argument of a method, `self`, is the object itself. Each window is a "
                    "class (`ReviewWindow`, `PlatesWindow`): its `__init__` builds it, its methods react to the "
                    "user."),
              ("@dataclass", "A class that is mostly a record of named values (`Scale`, `PlateSettings`), written "
                             "without repetitions."),
              ("Dictionary, list, tuple", "`{\"key\": value}`: settings, report rows, JSON files. `[a, b]`: ordered "
                    "values, changeable. `(x, y)`: fixed group (coordinates, colours)."),
              ("numpy array", "An image is an array: `rgb[y, x]` is a pixel, `rgb.shape` is (height, width, 3), "
                    "values 0 to 255. An operation applies to all pixels at once (`rgb * 0.5`), without a loop: "
                    "that is what makes the processing fast."),
              ("Mask", "An array of true / false the size of the image: `rgb[mask]` gives the pixels of the "
                       "object."),
              ("OpenCV (cv2)", "Image processing: resizing, blurring, converting to Lab, morphology (`cv2.erode` "
                    "shrinks a mask, `cv2.dilate` grows it), connected components (the separate pieces of a mask), "
                    "contours."),
              ("Pillow (PIL)", "Reading and writing image files, drawing texts, colour profiles."),
              ("Coordinates", "x to the right, y downwards, in pixels of the photo; in millimetres of the page for "
                    "the plates. An affine matrix `M` (2 × 3) goes from a straightened crop to the photo."),
              ("Exceptions", "`try: … except OSError:` catches an error (a file that cannot be read) instead of "
                             "stopping the program."),
              ("f-string", "`f\"{px_cm:.2f} px/cm\"` writes values inside a text (here with 2 decimals)."),
              ("Parallel work", "The engine processes several photos at once in separate processes "
                    "(`ProcessPoolExecutor`). The interface stays responsive by doing long work in threads "
                    "(`threading.Thread`) and checking regularly with `after(ms, function)`."),
              ("tkinter", "The windows: widgets (`ttk.Button`, `tk.Canvas`) placed with `pack` or `grid`; "
                          "`command=` and `bind(\"<Event>\", function)` tie a click or a key to a method; "
                          "`mainloop()` waits for the events.")]),

    ("h2", "5. A small lexicon to read a line"),
    ("table", [["Written", "Read as"],
               ["`a = b`", "a receives the value of b (not an equality)."],
               ["`a == b`, `a != b`", "is a equal to b? different from b? (true or false)"],
               ["`a += 1`, `a *= 2`", "a grows by 1; a is multiplied by 2."],
               ["`x ** 2`", "x squared."],
               ["`if … :`, `elif … :`, `else:`", "if…, else if…, otherwise."],
               ["`for x in items:`", "for each element of the list."],
               ["`and`, `or`, `not`", "and, or, not."],
               ["`# text`", "a comment: ignored by Python, written for the reader."],
               ["`lab[..., 0]`", "in an image array, channel 0 (L\\*) of all the pixels."],
               ["`rgb[y0:y1, x0:x1]`", "a rectangle of the image (from y0 to y1 excluded, from x0 to x1 excluded)."],
               ["`np.`, `cv2.`", "a function of numpy, of OpenCV."],
               ["`self.name`", "a piece of data of the object (the window, the scale…)."],
               ["`None`", "\"nothing\": no value (scale not found, for instance)."]]),

    ("h2", "6. Real functions, line by line"),
    ("p", "The extracts below are read from the code when this guide is made: they are exactly the lines of the "
          "program."),
    ("h3", "to_lab: going to CIELAB colours"),
    ("annotated", "gerbil.py", "to_lab", [
        "Defines the function `to_lab`, which receives `rgb`, an image in red-green-blue.",
        "The docstring: what the function does and why (see Part II, § 2).",
        "OpenCV converts the image to Lab; `.astype(np.float32)` turns it into decimal numbers, to compute "
        "without rounding. OpenCV stores each channel from 0 to 255.",
        "Channel 0 (L\\*) is brought from 0–255 to the usual 0–100 scale.",
        "Channels 1 and 2 (a\\* and b\\*) are centred on 0 (OpenCV shifts them by 128).",
        "Returns the image in Lab."]),
    ("h3", "distance: how different a pixel is from the background"),
    ("annotated", "gerbil.py", "distance", [
        "Receives the image in Lab, the reference colour (the background model) and the weight of lightness, by "
        "default `L_WEIGHT` (0.5).",
        "The docstring.",
        "Gap in lightness (L\\*) of each pixel to the background, multiplied by the weight: a shadow counts less.",
        "Gap in a\\* (green–red).",
        "Gap in b\\* (blue–yellow).",
        "The distance: square root of the sum of the squares (Pythagoras in the space of colours), for all pixels "
        "at once."]),
    ("h3", "hysteresis: keeping the clear regions and their faint edges"),
    ("annotated", "gerbil.py", "hysteresis", [
        "Receives the map of distances `d` and the two thresholds (8 and 18 for the cut-out).",
        "The docstring.",
        "`weak`: the pixels above the low threshold (1 = yes, 0 = no).",
        "OpenCV numbers the connected regions of `weak` (`n` regions; `lab` gives the number of each pixel). This "
        "`lab` has nothing to do with Lab colours: it is a \"label\".",
        "A list of `n` answers \"keep?\", all set to no to start with.",
        "The numbers of the regions that contain at least one pixel above the high threshold are set to yes.",
        "Region 0, the background, is never kept.",
        "Each pixel takes the answer of its region: this is the mask."]),
    ("h3", "parse_ratio: reading a scale written \"1/3\""),
    ("annotated", "gerbil_plates.py", "parse_ratio", [
        "Receives a text, for instance \"1/3\", \"1:3\" or \"3\".",
        "The docstring gives examples: \"2/3\" gives 1.5 (reduction to two thirds).",
        "The text is cleaned (spaces removed); a decimal comma becomes a point, as Python wants.",
        "Try what follows; on an error, go to `except`.",
        "If the text holds \"/\" or \":\"…",
        "… cut it in two at this sign: `a` before, `b` after.",
        "… and return b ÷ a (1/3 → 3, 2/3 → 1.5).",
        "Otherwise the text is a number alone: return it.",
        "If the reading fails (not a number) or divides by zero…",
        "… return `None`: the interface then keeps the previous value."]),
    ("h3", "Tooltip.__init__: tying a help bubble to a button"),
    ("annotated", "gerbil_gui.pyw", "Tooltip.__init__", [
        "The method that builds a help bubble: `self` is the bubble, `widget` the element (button, box), `text` the "
        "explanation.",
        "The docstring.",
        "Keeps the element and the text; the bubble itself (`tip`) and the planned task (`job`) do not exist yet.",
        "When the mouse **enters** the element: plan the display (`_schedule`, in 450 ms). `add=\"+\"` adds this "
        "binding without removing those already there.",
        "When the mouse **leaves**: hide the bubble.",
        "On a **click**: hide it.",
        "When the element loses the **focus**: hide it.",
        "When the element is **destroyed** (window closed): hide it."]),

    ("h2", "7. Changing the code without breaking anything"),
    ("ul", ["Names and messages in English; constants in capitals at the top of their section (`LOW_T`, "
            "`LABEL_FILL`…), with a comment saying what they are.",
            "Comments say *why* when it is not obvious; the docstrings say *what* and, briefly, *how*.",
            "**A change must leave the results already right identical, to the pixel**: it is checked on the "
            "reference sets of photos before being adopted (see `CONTRIBUTING.md`).",
            "The automatic tests run with `py -3 -m pytest tests`; they make their own synthetic photos (the "
            "repository holds no real photo).",
            "After a change of the code, run `py -3 docs/make_guide_odt.py` again: this guide is updated."]),

    ("h2", "8. Glossary"),
    ("defs", [("Affine (transformation)", "Rotation, change of size and shift combined; used to straighten a "
                                          "scale."),
              ("Alpha, layer mask", "The transparency of each pixel: 0 = transparent, 255 = opaque. In the PSD, the "
                                    "mask hides without erasing."),
              ("Connected component", "A piece of a mask in one block."),
              ("ECC", "Method of fine alignment of two images by correlation."),
              ("Hysteresis", "Threshold with two levels: keep what is above the low one when it touches what is "
                             "above the high one."),
              ("Least squares", "Fitting a curve or a surface so that the sum of the squared gaps is the smallest."),
              ("Morphology (opening, closing)", "Operations on the shape of a mask: the opening erases what is "
                    "thinner than a given disc, the closing fills narrower gaps."),
              ("ONNX, onnxruntime", "Format of neural networks, and the program that runs them."),
              ("px/cm, ppi", "Pixels per centimetre (measured on the scale); pixels per inch (= px/cm × 2.54), "
                             "written into the files."),
              ("RANSAC", "Robust method: try many small explanations and keep the one most of the data confirm."),
              ("SIFT", "Characteristic points of an image, recognisable even turned or enlarged."),
              ("Sub-pixel", "Position measured more finely than the pixel, by interpolating the lightness "
                            "profile."),
              ("SVG", "Vector drawing format (XML) read by Illustrator and Inkscape."),
              ("XMP, IPTC, EXIF", "Metadata written into the files: XMP is the format, IPTC the set of fields of photo "
                                  "libraries, EXIF the camera information.")]),
]
