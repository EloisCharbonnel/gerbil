"""Text of the guides in English, read by docs/make_guide_pdf.py:

- USER: the user guide (docs/Gerbil_guide_EN.pdf);
- CODE: the guide to the code (docs/Gerbil_code_guide_EN.pdf), followed by the reference of the functions made
  from the code, with their docstrings.

Same blocks as docs/fr/guide_fr.py: ("part", number, title, lead, anchor), ("h2"|"h3", title[, anchor]),
("p", text), ("lead", text), ("ul"|"ol", [items]), ("code", text), ("tip"|"warn"|"note"|"key", text),
("quote", text), ("table", [header, rows…][, widths]), ("figure", image, caption), ("shot", screenshot,
caption[, "half"]), ("defs", [(term, definition)…]), ("flow", [(no., title, text, anchor)…]), ("cards",
[(question, answer, anchor)…]), ("annotated", file, function, [explanation of each line]), ("pagebreak",).
In the texts: **bold**, *italic*, `code`, [[anchor]] or [[anchor|text]] (cross reference), {{Ctrl+Z}} (keys),
<https://…> (link). The anchors are the same as in the French guide."""

LABELS = {
    "contents": "Contents", "part": "PART", "in_part": "In this part", "line": "line", "lines": "lines",
    "function": "function", "class": "class", "method": "method", "untranslated": "",
    "helper": "(small helper: see the code)",
    "tip": "Tip", "warn": "Warning", "note": "Good to know", "key": "The essentials",
    "code_col": "Code", "expl_col": "What the line does",
    "ref_title": "Reference of the functions",
    "ref_intro": "Every file of the program, its sections (the \"# ----\" banners of the code) and, in each, all "
        "its functions and classes, with their explanation and their line number. The name in bold is the one to "
        "look for in the code (Ctrl+F); in brackets, what the function receives.",
    "generated": "This part is written automatically from the code (docs/make_guide_pdf.py): it always follows "
        "the version of the program.",
    "version": "Version", "licence": "Free software, GNU GPL v3 or later",
    "date": "Guide made on",
}

USER_META = {
    "subtitle": "User guide",
    "tagline": "From photographs of finds and of the field to published plates and archives: the whole way, step "
               "by step, with its possibilities, its methods and its sources.",
    "footer": "Gerbil {version}, user guide",
}
CODE_META = {
    "subtitle": "Guide to the code",
    "tagline": "How the program is organised, the Python notions to read it, functions explained line by line, "
               "and the reference of every function.",
    "footer": "Gerbil {version}, guide to the code",
    "ref_number": "5",
}

FILE_ROLES = {}                         # the roles of docs/make_code_guide.py
SECTION_TITLES = {}                     # the banners of the code, as they are

# =============================================================================================================
# USER GUIDE
# =============================================================================================================

USER = [
    # ------------------------------------------------------------------------------------------------ 1
    ("part", "1", "Welcome", "Gerbil is the archaeologist's photo toolkit: it outlines finds at their real "
     "size, names and documents the photographs, converts them for the archive and lays out the plates. This "
     "guide goes all the way round, from the shot to the deposit.", "bienvenue"),

    ("h2", "I want to…", "je-veux"),
    ("cards", [
        ("Outline finds at their real size", "step 03, then review", "etape-03"),
        ("Name my files from the inventory", "batch renaming, CSV import", "etape-02"),
        ("Archive my RAW photos as DNG with their metadata", "step 04", "etape-04"),
        ("Make plates at 1/3", "plates at scale", "planches"),
        ("Show burials at the same scale", "free plates", "planches-libres"),
        ("Prepare a deposit to an archive", "final review", "etape-05"),
        ("Fix a cut-out", "review window", "verifier"),
        ("Give the scale by hand", "two clicks and a length", "echelle-main"),
        ("Share the settings with the team", "site profile", "profils"),
        ("Write the methodology of the report", "a paragraph to adapt", "methodologie"),
        ("Find a shortcut", "keyboard and mouse", "raccourcis"),
        ("Understand a message", "troubleshooting", "depannage"),
    ]),

    ("h2", "This guide", "ce-guide"),
    ("p", "It is for those who **use** Gerbil, in the finds room as in the field, and for those who want to "
          "**understand** what it does to explain it in a report. The code itself has its own guide, the *Guide "
          "to the code*."),
    ("ul", ["[[apercu|Gerbil at a glance]]: what the program does, the way from A to Z, the window.",
            "[[prise-de-vue|Taking good photos]]: what happens before Gerbil.",
            "[[etapes|The six steps]]: every page of the window, in detail, with screenshots.",
            "[[workflows|Workflows]]: complete recipes, from finds to deposit.",
            "[[comprendre|Understanding the processing]]: the methods, in plain words, for a methodology.",
            "[[inspirations|Inspirations and sources]]: where Gerbil's choices come from.",
            "[[annexes|Appendices]]: shortcuts, options, files, troubleshooting, glossary, libraries."]),
    ("h3", "Conventions"),
    ("table", [["Written", "Means"],
               ["*Run*", "a button, box or menu of Gerbil (in italics, with its name on screen)."],
               ["{{Ctrl+Z}}", "a key or a combination of keys."],
               ["`outlined_result`", "a file or folder name, an option, text to type."],
               ["[[raccourcis|Shortcuts]]", "a cross reference: a click goes to the page. The bookmarks of the PDF "
                                            "also give the whole outline."]], [0.3, 0.7]),
    ("note", "The interface is in English and French; this guide gives the English names of the buttons. The "
             "screenshots show version 2.3 on a real test set: 13 sherds photographed with a Nikon D850, with a "
             "10 cm checkerboard scale and a label."),

    # ------------------------------------------------------------------------------------------------ 2
    ("part", "2", "Gerbil at a glance", "What the program does, the way of a series of photos from A to Z, and "
     "the window that follows it step by step.", "apercu"),

    ("h2", "What Gerbil does", "ce-que-fait-gerbil"),
    ("p", "Gerbil is given photos of finds (pottery, metal, lithics, bone, glass…) laid on a plain background "
          "**with a scale**, or photos of the field. It:"),
    ("ol", ["**finds and measures the scale** of each photo (checkerboard, single row, millimetre ruler, or a "
            "scale it has learned): how many pixels make a centimetre on *this* photo;",
            "**outlines the object**, leaving out labels, supports, colour charts and the scale itself;",
            "**writes files at 1:1**: a layered PSD and transparent TIFFs whose resolution is the real one, so that "
            "the object shows at its real size in Illustrator, Photoshop or InDesign;",
            "**names and documents** the files from the batch renaming (site, context, number…) and writes the "
            "IPTC metadata read by Bridge, Lightroom or Windows Explorer;",
            "**converts RAW photos to archival DNG**, with their metadata, their new names and a JPG;",
            "**lays out plates** at scale (1:1, 1:2, 1:3…), free plates of the field, contact sheets, the inventory "
            "and thumbnails;",
            "**checks a folder before a deposit**: formats, names, duplicates, checksums;",
            "**says when it is unsure** instead of keeping quiet: whatever deserves a look gets the suffix "
            "`_to_be_verified`."]),
    ("p", "The measurement comes from the scale of each photo, not from the camera data: the lens and the distance "
          "do not matter. The original photos are **never changed**."),
    ("figure", "fig_control", "The control preview of a photo: outline of the cut-out in green, label left out "
                              "in red, scale found in magenta, centimetres read in orange, measurement written at "
                              "the top."),

    ("h2", "The way from A to Z", "parcours"),
    ("p", "Gerbil's window follows the work in six steps. Only the first is needed; the others are done as "
          "needed, and in any order. A click on a card goes to its page."),
    ("flow", [
        ("01", "Source photographs", "The folders or photos to process, and the site profile.", "etape-01"),
        ("02", "Naming and metadata", "The names of the files written, the information of each photo; then "
                                      "checking it.", "etape-02"),
        ("03", "Outline and scale", "The objects at 1:1 as PSD and TIFF; then the review of doubtful cases.",
         "etape-03"),
        ("04", "Convert", "RAW photos to archival DNG, with a JPG and, if wanted, a 16-bit TIFF.", "etape-04"),
        ("05", "Final review", "Every file written, and the check before a deposit.", "etape-05"),
        ("06", "Publication", "Plates at scale, free plates, contact sheets, inventory, thumbnails.", "etape-06"),
    ]),
    ("table", [["", "You do", "You get"],
               ["**Before**", "[[prise-de-vue|Photograph]] with a scale in the plane of the object, on a plain "
                              "background.", "Photos that Gerbil can measure."],
               ["**01**", "Add the folder, choose the site profile.", "The list of photos."],
               ["**02**", "Fill in the batch renaming, or import the inventory.", "Right file names and metadata."],
               ["**03**", "*Run*, then *Review* the flagged photos.", "`outlined_result`: PSD, TIFF at 1:1, CSV "
                                                                      "report."],
               ["**04**", "*Convert* the RAW photos.", "`<date>\\DNG`, `<date>\\JPG`, `<date>\\TIFF`."],
               ["**05**", "Look over the files; check before a deposit.", "`deposit_check`: inventory, checksums."],
               ["**06**", "Make the plates, the inventory, the thumbnails.", "SVG, TIFF, JPEG, PDF, CSV."]],
     [0.12, 0.5, 0.38]),
    ("tip", "A team that only converts (the protocol of a field mission) goes from 02 to 04: its site profile marks "
            "step 03 as optional and *Continue* goes straight to the conversion."),

    ("h2", "The window", "la-fenetre"),
    ("shot", "sources", "Gerbil's window, here at step 01: the column of steps on the left, the page of the step "
                        "on the right, on squared paper."),
    ("ul", ["**The column of steps**: a click opens a step. Under each title, a summary kept up to date (\"6 "
            "photo(s)\", \"4 ok, 2 to verify\"); an orange badge counts what is left to look at. Two steps have a "
            "second page, indented: *Check the metadata* and *See the results*.",
            "**The page**: a title, a sentence that says what the step is for, then its cards. Leaving the mouse "
            "on a setting shows its explanation.",
            "**Continue** (light green, at the bottom) goes to the next useful step.",
            "**At the bottom of the column**: the language (*FR*, *EN*), *Help* (this guide), the theme (*GREEN*, "
            "*VIOLET*, *LIGHT*, *DARK*), the version."]),

    ("h2", "Language and themes", "themes"),
    ("p", "The interface is in English and French; the first time, it follows the language of Windows. It comes "
          "in green (by default) or violet, light or dark: a click on *GREEN*, *VIOLET*, *LIGHT* or *DARK* changes "
          "the window at once, and the choice is kept. Windows already open take the new colours when opened "
          "again. The files written (plates, PDF) stay on white, whatever the theme."),
    ("shot", "dark", "The dark green theme, at step 03."),

    ("h2", "Install, update, uninstall", "installer"),
    ("h3", "On a computer without Python (the simplest)"),
    ("ol", ["Double-click **Gerbil_Setup.exe** (a single file, about 100 MB).",
            "Keep the folder offered (no administrator rights needed), tick the desktop shortcut if wanted, then "
            "*Install*.",
            "Open Gerbil from the Start menu."]),
    ("warn", "The programs are not signed: the first time, Windows may show \"Windows protected your PC\". Click "
             "*More info*, then *Run anyway*."),
    ("p", "**Update**: run a newer Gerbil_Setup.exe; the BiRefNet models already downloaded are kept. **Uninstall**: "
          "*Settings > Apps > Installed apps*. Photos and results are never touched."),
    ("h3", "With the Python scripts"),
    ("p", "Copy the folder of the program, double-click **Install.bat** once (it installs Python if needed, then "
          "numpy, OpenCV, Pillow and rawpy), then open the interface with **Gerbil.bat**. **Gerbil_drop.bat** "
          "processes the folders dropped on it."),
    ("h3", "What is needed alongside"),
    ("ul", ["**Adobe DNG Converter** (free, from Adobe) for step 04 only; Gerbil finds it once installed.",
            "**ExifTool** ships with Gerbil (metadata of the DNG files).",
            "**Inkscape** (free), to place `.ai`, `.pdf` or `.eps` drawings on the plates.",
            "The **models of machine learning** (BiRefNet, one-click cut-out) are downloaded once, the first time "
            "they are used; "
            "then everything runs on the computer."]),

    # ------------------------------------------------------------------------------------------------ 3
    ("part", "3", "Taking good photos", "Gerbil measures what it sees: the quality of the result is decided "
     "when the photo is taken. A few simple rules are enough.", "prise-de-vue"),

    ("h2", "The five rules", "cinq-regles"),
    ("ol", ["**The scale in the plane of the object**, at the height of the photographed face. Laid on the table "
            "under a thick object, it gives a wrong measurement (the object is closer to the lens).",
            "**A plain background** that differs from the object: light (paper, card) or dark (black velvet, "
            "felt). A slight lighting gradient does not matter.",
            "**A known scale**: a black and white (or red) checkerboard of 5, 10 or 20 cm, one or two rows, "
            "printed digits accepted; a single row; a ruler graduated in millimetres. Any other scale can be "
            "[[profils|learned]].",
            "**The whole object in the frame**, not touching the edge of the photo.",
            "**The camera parallel to the table**: from the front, not at an angle."]),
    ("figure", "fig_photo", "A photo to process: the sherd, its label and a 10 cm checkerboard scale, on a light "
                            "background."),
    ("h2", "Formats", "formats"),
    ("p", "JPEG, TIFF, PNG or RAW (DNG, CR2, CR3, NEF, ARW, ORF, RW2, RAF…). A RAW photo is developed by Gerbil; "
          "for very precise colours, develop it yourself (Lightroom, darktable) and give the TIFFs to Gerbil."),
    ("h2", "Small tips", "conseils"),
    ("ul", ["**Mounting putty**: a blue putty, or putty hidden behind the object, is not mistaken for a light object.",
            "**Very light objects** (white fabric, chalk, cortex): on a grey or black background; BiRefNet, the "
            "default cut-out, mostly sees them.",
            "**A colour chart** in the frame lets you balance the whites afterwards ([[couleurs|Colour setting]]).",
            "**A label** may stay on the photo: Gerbil leaves it out. Placing it on the other side of the scale "
            "helps.",
            "**Several objects** on one photo are outlined together, each at scale."]),

    # ------------------------------------------------------------------------------------------------ 4
    ("part", "4", "The six steps", "Every page of the window in detail: what is done there, what is set there, "
     "what comes out.", "etapes"),

    ("h2", "01 Source photographs", "etape-01"),
    ("p", "The list of folders and photos to process, and the site profile."),
    ("ul", ["*Add folder…* (sub-folders included) or *Add photos…*; the number of photos is shown.",
            "**Paste a path** in the *or paste a path* field, then *Add* or {{Enter}}.",
            "**Drop folders** on Gerbil's icon to add them at start.",
            "*Remove* (or {{Delete}}) takes the chosen row out, *Clear* the whole list. The files are never "
            "touched."]),
    ("p", "On the right, **the site profile** and **what it holds**: its work (cut-out or conversion), its fields "
          "(required ones have a star), its name template, its keyword lists, its settings, its learned scales."),

    ("h2", "Site profiles and learned scales", "profils"),
    ("p", "A **site profile** gathers what is known of the photos of a site or season, chosen once and for all "
          "(*New…*, *Edit…*, *Import…*):"),
    ("ul", ["the **background**: found by Gerbil, light, or dark;",
            "the **renaming**: fields, meaning of each field and its IPTC field, checks (a context in digits "
            "only…), name template, keyword lists to tick;",
            "the **settings** of the window (*Keep the options of the main window*) and the **work** of the team "
            "(cut-out, or conversion only);",
            "the **learned scales**: *Learn a scale from a photo…*, click both ends of the scale and give the width "
            "of its printed band; Gerbil then finds it on the other photos."]),
    ("p", "By default, a learned scale is a second chance, used when the usual reading fails; *Look for the learned "
          "scales first* uses it first. *Put next to the photos…* copies the profile as `gerbil_profile.json` into "
          "a folder: it then applies to those photos, for the whole team. *Import…* adds a profile received (a "
          "`.json` file) to the library."),
    ("shot", "profile", "The window of a site profile: background, learned scales, settings kept.", "third"),
    ("tip", "Learn **each copy** of a scale in use: two prints of the same model may differ by 1%."),

    ("h2", "02 Naming and metadata", "etape-02"),
    ("p", "The page sums up the batch renaming of the folder; *Open the batch renaming…* opens the window that "
          "gives each photo its information and the name of its files. Only the photos of step 01 are shown in it "
          "(a box shows the whole folder)."),
    ("shot", "project", "The batch renaming window: fields, name template and values on the left, one row per photo "
                        "with its output name; on the right, the photo chosen, in large, to recognise it. Incomplete "
                        "rows are in orange."),
    ("h3", "Fields, name template, rule"),
    ("ul", ["**Fields**: by default *Site*, *Sector*, *US*, *Object number*, *Material*, *View*; else those of the "
            "profile. *Add field…*, *Edit field…* (name, meaning, IPTC field, required).",
            "**Name template**, for instance `{site}_US{us}_{number}_{material}`: the files written take this name "
            "(`EX24_US1043_1_pottery_outlined.tif`). The *Insert* buttons add a field. `{building|first}` keeps, of "
            "several values (`B27 ; B20`), the one with the smallest number. **The original photos are never "
            "renamed.**",
            "**Naming rule** (optional): a regular expression, read as PowerShell's `-match`. The helper (*▸ Rule helper*, folded by default) writes it "
            "from tick boxes (uppercase only, ends with a number…) and shows the equivalent PowerShell line, to "
            "learn. *Test a name* tries it.",
            "**Names without accents** (box of the helper): \"céramique\" becomes \"ceramique\" in the files "
            "written. Tick it before a deposit: most archives refuse accents, and *Check the metadata* flags a name "
            "that has some."]),
    ("h3", "Filling in the values as in Excel"),
    ("ul", ["**Values for all the photos**: the site, the season, the author.",
            "**The table**: double-click to edit a cell ({{Enter}} accepts, {{Esc}} cancels); the **handle** at the "
            "corner of a cell copies down (with {{Ctrl}}: a series 187, 188, 189…); {{Ctrl+D}} copies the first "
            "row chosen; {{Ctrl+A}} chooses all.",
            "*Set for selected…*, *Number the selected…*; in *Keywords…*, a field finds a keyword.",
            "*Import CSV / Excel…*: an inventory whose first row holds the column names; the column of photo names "
            "is found by itself.",
            "*Keywords…*: the lists of the profile, to tick for the rows chosen."]),
    ("p", "*Save* keeps the renaming (in memory for a conversion, in `gerbil_project.json` for a cut-out); *Save and "
          "process the photos* starts the step of the profile at once."),

    ("h2", "Check the metadata", "relire"),
    ("p", "The second page of step 02 checks, before any processing, each photo of step 01: its output name and "
          "what to note. A double-click opens the batch renaming on that photo."),
    ("shot", "meta", "Check the metadata: in orange, required information is missing."),
    ("table", [["Remark", "Meaning", "The photo is"],
               ["*Missing information: Site, Context*", "a required field of the profile is empty", "to verify"],
               ["*Value not written as expected: Context 1043a*", "the value does not follow the check of its field",
                "to verify"],
               ["*Not mentioned: Material*", "an optional field is empty: only mentioned", "ok"]],
     [0.4, 0.4, 0.2]),

    ("h2", "IPTC metadata", "iptc"),
    ("p", "*IPTC metadata…* (in the batch renaming) fills in the standard fields of photo libraries: title, "
          "description, keywords, creator, copyright, location… For each, a text where `{field}` is replaced by the "
          "value of the photo and `{name}` by the output name; a text without braces is the same for all (copyright, "
          "creator). They are written into the PSD, TIFF, DNG and JPG files written, into the copy of the original "
          "(without recompressing the image) and, if ticked, into a `NAME.xmp` file next to each original. A `.xmp` "
          "written by another program is never replaced."),

    ("h2", "03 Outline and scale", "etape-03"),
    ("p", "The heart of Gerbil: the scale of each photo, the cut-out of the object, the files at 1:1. Keep the "
          "default settings for a first try, then *Run*."),
    ("shot", "cutout", "Step 03 after a run: the progress chart, one row per photo (green: ok, orange: to verify, "
                       "red: failed), the settings on the right."),
    ("table", [["Setting", "Choices"],
               ["*Cut-out*", "*BiRefNet* (default): an algorithm of machine learning points out the objects, the "
                             "surest ([[ia|see]]); *BiRefNet, lighter*: faster; *by the colour*: rules written by "
                             "hand, fast, exact on a really plain background."],
               ["*Colour*", "*unchanged*; white *balance*; *exposure*: balance and the same lightness for the whole "
                            "series ([[couleurs|see]])."],
               ["*White reference*", "*colour chart*, *scale* or *background*."],
               ["*Photoshop file (.psd)*", "a layered PSD besides the TIFFs."],
               ["*TIFF background*", "transparent or white."],
               ["*Look for the scale*", "untick for photos without a scale."],
               ["*Advanced settings…*", "margins, layout of the scale, putty, compression, second opinion (machine learning), photos "
                                        "in parallel…"],
               ["*Results*", "*next to the photos* (`outlined_result` folder) or in a folder chosen."]], [0.3, 0.7]),
    ("p", "*Changed from the defaults* recalls what was changed; *Back to the defaults* undoes it all. Count 20 to "
          "30 seconds per photo with BiRefNet, 3 to 4 seconds by the colour."),

    ("h2", "What comes out", "ce-qui-sort"),
    ("p", "All the files of a photo keep its name (or the name of the batch renaming), to follow them in Explorer:"),
    ("table", [["File", "Content"],
               ["`NAME.JPG`", "Copy of the original photo, with its IPTC metadata (no recompression)."],
               ["`NAME.psd`", "Layered Photoshop: *Original photo* (hidden), *Scale*, *Object*, with layer masks "
                              "that can be painted (white: show, black: hide)."],
               ["`NAME_outlined.tif`", "The object alone, transparent background, at the 1:1 resolution."],
               ["`NAME_outlined_scale.tif`", "The object and its straightened scale below."],
               ["`to_control/NAME_to_control.jpg`", "The control preview."],
               ["`outlined_report.csv`", "The report: one row per photo ([[rapport|columns]])."]], [0.38, 0.62]),
    ("table", [["Colour of the preview", "Meaning"],
               ["Green", "outline of the cut-out"], ["Magenta", "frame of the scale found"],
               ["Orange", "centimetres read on the scale"],
               ["Red", "what was left out (label, chart, small isolated piece) or possible putty"],
               ["Blue", "plexiglas support or cast shadow removed"],
               ["Cyan", "background removed by the second opinion"]], [0.3, 0.7]),
    ("h3", "The _to_be_verified suffix"),
    ("p", "When something is doubtful, all the files of the photo get this suffix (`NAME_outlined_to_be_verified.tif`): "
          "type `to_be_verified` in Explorer's search to find them. There is a doubt when the scale is not found or "
          "irregular, when an area looks like putty, a chart touches the object, the object touches the edge, "
          "required information is missing or the name does not follow the rule. The suffix goes away at the next "
          "run once the doubt is cleared."),

    ("h2", "See the results and fix them", "verifier"),
    ("p", "The second page of step 03 lists the photos to look at with their problem. *Review* opens the correction "
          "window; a double-click on a row opens straight what needs fixing (the scale, the renaming or the "
          "cut-out)."),
    ("shot", "review", "The review window: doubtful photos first, the outline of the cut-out in green and of the "
                       "scale in magenta, the tools on the right."),
    ("table", [["Tool", "Use"],
               ["*One click on the object (more precise)*", "click each object to keep: Segment Anything outlines it "
                    "({{Shift}} + click removes one). The surest on difficult photos, because you **show** the "
                    "object instead of letting it guess."],
               ["*Erase* / *Add*", "with a brush (adjustable size) or a lasso."],
               ["*Remove a piece*", "a click removes a whole piece (shadow, stain of the background)."],
               ["*Orient*", "draw a line along the rim: it becomes horizontal, the object below; or turn by quarter "
                            "turns."],
               ["*Undo*, *Reset photo*", "the last action ({{Ctrl+Z}}), or all of them."],
               ["*Fix the scale…*", "opens the manual scale of the photo."],
               ["*Information*", "the fields of the renaming, editable here."],
               ["*Accept and next*", "saves and **exports the photo again at once**, in the background."]],
     [0.34, 0.66]),
    ("p", "*Redo with BiRefNet…* cuts out again, with [[ia|BiRefNet]], the photos to verify (or those chosen in "
          "the list), when the cut-out by the colour had been chosen: often all that is needed for a cast shadow, "
          "the edge of the table or a white object on white. The setting of the window does not change."),
    ("p", "Moving around: mouse wheel to zoom; right or middle button, {{Space}} + drag or the arrow keys to move "
          "the view; {{R}} to see the whole photo again."),
    ("note", "The corrections are kept **next to the photos**, in `gerbil_edits`: later runs keep them. Keep this "
             "folder with the photos."),

    ("h2", "Give the scale by hand", "echelle-main"),
    ("p", "When the scale is not found or misread: *Set the scale by hand…*, click both ends of a known length (0 "
          "and 5 cm, in the middle of the scale), give this length and the width of the scale, then *Save*. The "
          "scale is kept in `gerbil_scales.json` and wins over the automatic search (report: `scale_type = manual`). "
          "At the end of a run, Gerbil offers to set in a row all the scales it did not find (*Save and next*, "
          "*Skip this photo*, *Stop*)."),
    ("shot", "scale", "The scale by hand: two clicks on a known length, then that length and the width of the "
                      "scale.", "half"),

    ("h2", "04 Convert: RAW to DNG", "etape-04"),
    ("p", "To archive RAW photos as DNG with their metadata (the \"Convert RAW to DNG\" protocol of the MAFKF / QSR "
          "mission, brought into Gerbil). Each RAW photo of step 01 is converted by **Adobe DNG Converter** with "
          "the settings of the protocol (DNG 1.7, original RAW embedded, medium preview), under the **name of the "
          "batch renaming**."),
    ("shot", "convert", "Step 04: the conversion on the left, the extra exports on the right."),
    ("ul", ["Sorted by date taken: `<date>\\DNG`, `<date>\\JPG` and, if ticked, `<date>\\TIFF` (16-bit, full "
            "size).",
            "**JPG**: the preview of the DNG (~1024 px, by default), developed at full size, or none. Metadata "
            "embedded in each file.",
            "The **XMP** next to the RAW (Lightroom, Bridge) is embedded in the DNG; the fields filled in Gerbil "
            "win and the **keywords are added**.",
            "**Nothing is written next to the photos**: each DNG keeps its original RAW and the values given; "
            "opened later, the batch renaming of a converted folder is **read back from its DNG files**.",
            "**Running again only redoes what changed**: a DNG already made is renamed (with its JPG and TIFF) if "
            "its name changed, and its metadata written again if the values changed.",
            "Empty optional fields are only mentioned; only the required fields of the profile make a photo to "
            "verify."]),

    ("h2", "05 Final review and deposit", "etape-05"),
    ("p", "Every file written for the photos of step 01, each with what it is (TIFF 1:1, PSD, preview, copy of the "
          "original, plate, thumbnail, DNG, JPG, TIFF); a double-click opens one, *Open results* shows the folders "
          "in Explorer."),
    ("shot", "final", "The final review: every file written, and the check before a deposit."),
    ("p", "*Check before a deposit…* checks a folder before it goes to an archive, **without copying, moving or "
          "changing anything**. For each file: its **format** (from the list of accepted extensions, to adapt to "
          "the archive), its **name** (letters without accents, digits, `_`, `-`, `.`, and the naming rule of the "
          "project), an **empty** file, a **path** too long (over 240 characters), the **same content present "
          "twice**. The `deposit_check` folder receives the inventory (`deposit_inventory.csv`, with the SHA-256 "
          "checksum of each file), `checksums.sha256` (to check the deposit after its transfer) and a readable "
          "report (`deposit_report.txt`)."),
    ("shot", "deposit_done", "The check before a deposit: the folder, the formats accepted, and the summary.",
     "half"),
    ("warn", "This check does not replace the deposit protocol of the archive."),

    ("h2", "06 Publication", "etape-06"),
    ("p", "The outputs for the report and the publication, each in its window."),
    ("shot", "publication", "Step 06: plates, free plates, contact sheets, inventory, thumbnails."),

    ("h2", "Plates at scale", "planches"),
    ("p", "*Plates* lays out the outlined objects of a results folder at a chosen scale (1:1, 1:2, 1:3…) and writes "
          "them as **SVG**, which open in Illustrator or Inkscape at their real size: 1 cm of the object is 1 cm ÷ "
          "scale on paper. *Files written* also gives each page as **TIFF** or **JPEG** (300 to 1200 ppi) and all "
          "the plates in one **PDF**."),
    ("shot", "plates", "The plates window: the settings in three tabs, the exact preview of the page on the right.",
     "half"),
    ("ul", ["Objects in **rows**, in the order chosen (name, context, material…), with a **caption** (`{name}`, or "
            "`{site}_{us}_{number}`…); *Group by* starts a row or a page at each value.",
            "**Scale bar** set as in QGIS (style, length, segments, colours, font), kept as house style.",
            "**One scale per plate**; an object too large goes to 1:1.5, 1:2, 1:3… on its own plates. *Scale per "
            "object…*, or a click on an object of the preview, chooses its scale.",
            "**Scale per material**: pottery and glass at 1/3, iron at 2/3, stone at 1/3 by default (rules "
            "`word=reduction` that can be changed), after the conventions of archaeological drawing.",
            "**Drawings next to the photos**: a folder of drawings (`.svg`, or `.ai` `.pdf` `.eps` converted by "
            "Inkscape); a drawing named like the object is placed next to its photo, at the same scale, as vectors.",
            "**Title** and **file names** from templates (`{page}`, `{pages}`, `{group}`, `{scale}`); optional "
            "**dimensions** on a hidden layer.",
            "**List of figures**: `figures.csv`, written next to the plates (number, file, title, caption, scale, "
            "credit), pastes into the report as a table."]),
    ("p", "In the preview, the mouse wheel zooms, ◀ ▶ turn the pages."),

    ("h2", "Free plates: field photos and orthophotos", "planches-libres"),
    ("p", "*Free plates* lays out **whole photos** (burials, structures, orthophotos), each brought to the scale of "
          "the plate (1:10, 1:20, 1:50…): a typological plate thus shows the burials at the same scale, sorted by "
          "type."),
    ("ul", ["*Scale of the photos…* lists the photos with their real size; a double-click opens a photo: click both "
            "ends of a known length (ranging pole, target, length of the pit measured in the field) and give it in "
            "centimetres.",
            "A photo **already outlined in step 03** keeps the scale measured then: nothing to do (the list says "
            "where each scale comes from).",
            "An **orthophoto** with its georeferencing file (`.jgw`, `.tfw`) needs nothing.",
            "**A click on a photo of the preview**: choose its scale (1:5 to 1:100) or measure it.",
            "**Captions, order and groups** come from the batch renaming of the folder (add *Burial*, *Type*, "
            "*Phase*…), then *Group by: Type*.",
            "Pages A4 to A2, portrait or landscape; scale bar in cm or m; SVG, TIFF, JPEG or PDF."]),
    ("warn", "The scale holds in the plane of the two points clicked: a photo taken at an angle is not an "
             "orthophoto."),

    ("h2", "Contact sheets, inventory, thumbnails", "planches-contact"),
    ("ul", ["**Contact sheets**: all the photos of a folder on pages, with their name, so many per row; *Group by* a "
            "field (context, sector) starts a page at each value. The photos are not at scale there.",
            "**Inventory**: one row per file of the folders chosen (photos, drawings, 3D models), with folder, type, "
            "size, date, **the fields read in the name** (same template as the renaming), and for images their "
            "size, resolution, date taken and camera. The window shows the **PowerShell line** that makes the same "
            "inventory with Windows alone.",
            "**Thumbnails**: reduced copies for databases (128 to 1,024 px), transparent PNG or JPEG on white, "
            "transparent margin cut off."]),
    ("shot", "contact_done", "Contact sheets: folder, page, number per row, caption, groups.", "half"),
    ("shot", "inventory_done", "The inventory, with the PowerShell line that does the same with Windows alone.",
     "half"),
    ("shot", "thumbnails_done", "Thumbnails: size, format, outlined objects only.", "half"),

    # ------------------------------------------------------------------------------------------------ 5
    ("part", "5", "Workflows", "Complete recipes, from the box of finds to the report, from the field to the "
     "archive. Each points to the pages it needs.", "workflows"),

    ("h2", "Finds: from the sherd to the published plate", "wf-mobilier"),
    ("ol", ["**Photograph** each object with its scale, on a plain background ([[cinq-regles|the five rules]]).",
            "**01**: add the folder of the box; choose the site profile.",
            "**02**: *Import CSV / Excel…* the finds inventory, or fill in the table (context, number, material); "
            "check the output name; *Check the metadata*.",
            "**03**: *Run*. Then *See the results*: *Review* the flagged photos, one click on the object if needed; "
            "set by hand the scales not found.",
            "**06**: *Plates*, at 1/3 for pottery, *Group by* context; tick *PDF*; add the folder of drawings.",
            "**Report**: paste `figures.csv` and the [[methodologie|methodology paragraph]]."]),
    ("key", "The simplest check of the measurement: drop `NAME_outlined_scale.tif` into Illustrator; the scale must "
            "measure exactly 5 or 10 cm with the ruler."),

    ("h2", "Field: archive the RAW photos as DNG", "wf-terrain"),
    ("ol", ["**Import the profile** of the mission (*Import…*, step 01): fields, checks, name template, keywords, "
            "\"conversion\" work.",
            "**01**: add the folder of the day.",
            "**02**: batch renaming: *Creator* and *Area* for all photos, then building, structure, unit, context "
            "row by row; *Keywords…*; *Check the metadata* until nothing is orange.",
            "**04**: *Convert*, with the preview JPG (and the TIFF if asked for).",
            "**05**: look over the files; *Check before a deposit…* before copying to the server.",
            "**The next day**: a corrected renaming converts again in a few seconds; only the DNG files that changed "
            "are renamed or rewritten."]),

    ("h2", "Burials and structures at the same scale", "wf-sepultures"),
    ("ol", ["Photograph each burial from above (vertical photo, or an orthophoto from photogrammetry) with a ranging "
            "pole or a target.",
            "**02**: in the batch renaming, add the fields *Burial*, *Type*, *Phase*.",
            "**06**: *Free plates*; *Scale of the photos…*: measure the pole of each.",
            "Plate scale 1:20, *Group by: Type*, caption `{burial}`; write SVG and PDF."]),

    ("h2", "Prepare a deposit", "wf-versement"),
    ("ol", ["Gather the folder to deposit (photos, DNG, plates, inventory).",
            "**05**: *Check before a deposit…*; adapt the list of accepted formats to the archive's (TIFF, PNG, SVG, "
            "PDF/A, CSV…).",
            "Read `deposit_report.txt`: rename the files with refused names, remove duplicates, shorten the paths; "
            "start again until the report is clean.",
            "Attach `deposit_inventory.csv` and `checksums.sha256` to the transfer slip; after the transfer, the "
            "archive can check each file."]),

    ("h2", "Working as a team", "wf-equipe"),
    ("ul", ["**One profile for the whole site**: prepare it once, send it (`.json` file); each imports it. Or *put "
            "it next to the photos* of a shared folder.",
            "**Decisions travel with the photos**: `gerbil_project.json`, `gerbil_scales.json`, `gerbil_edits` "
            "([[fichiers-voisins|see]]); for the conversion, everything is in the DNG files.",
            "**Same settings, same results**: a run started again elsewhere gives the same files."]),

    ("h2", "Large batches and the command line", "wf-ligne"),
    ("p", "The engine runs without a window, with the same options ([[options|list]]):"),
    ("code", "py gerbil.py \"D:\\Dig\\Box 12\" --no-psd -j 6 --open\n"
             "gerbil_cli.exe \"D:\\Dig\\Box 12\" --cutout ai\n"
             "py gerbil.py --dng \"D:\\Field\\2026-02-14\" --jpg preview --tiff"),
    ("p", "Dropping folders on **Gerbil_drop.bat** processes them with the default settings. `--refresh-names` "
          "applies a changed renaming to the results already made, without processing again."),

    ("h2", "Process again without losing anything", "wf-retraiter"),
    ("p", "Processing a folder again replaces the files of the photos processed again and **keeps** the scales "
          "given by hand, the corrections of the review and the renaming. The `_to_be_verified` suffix goes away "
          "if the doubt is cleared; the copy of the original always keeps its name. For a change of name only, "
          "`--refresh-names` (or *Save* in the batch renaming, which offers to apply it) is enough."),

    # ------------------------------------------------------------------------------------------------ 6
    ("part", "6", "Understanding the processing", "What Gerbil does, step by step, without programming: enough to "
     "explain it, check it and write a methodology. The thresholds are those of the code; docs/PSEUDOCODE.txt gives "
     "them all.", "comprendre"),

    ("h2", "The way of a photo", "chemin"),
    ("ol", ["**Reading**: the photo is opened and turned upright (EXIF orientation); a RAW photo is developed.",
            "**Reduced copy** at 1,500 px for the analysis; the fine measurements are made again at full resolution.",
            "**Background model**: the colour of the background at every point.",
            "**Scale**: manual if one was given, else searched (checkerboard, ruler, dark background), else a learned "
            "scale.",
            "**Cut-out**: what differs from the background, sorted, refined at full resolution.",
            "**Putty** searched along the outline; **colours** corrected if asked for.",
            "**Files**: layers, PSD, TIFF at 1:1, metadata, preview, report row."]),

    ("h2", "Seeing colours as the eye does: CIELAB", "cielab"),
    ("p", "A photo is made of red, green and blue pixels. But in RGB, two colours that look \"equally different\" "
          "may have very different gaps in numbers. Gerbil therefore works in **CIELAB**: **L\\*** is the "
          "lightness (0 black, 100 white), **a\\*** goes from green to red, **b\\*** from blue to yellow. A distance "
          "there roughly matches what we perceive:"),
    ("code", "d = sqrt( (0.5 × ΔL*)² + Δa*² + Δb*² )"),
    ("p", "Lightness counts for half only: a **soft shadow** mostly changes the lightness of the background, not its "
          "colour, and so stays out of the object."),

    ("h2", "The background model", "modele-fond"),
    ("note", "This section and the next two describe the **cut-out by the colour**, made of rules written by hand. "
             "With [[ia|BiRefNet]], the default cut-out, an algorithm of machine learning points out the objects; "
             "the sorting of the pieces and the drawing of the edge stay as described here."),
    ("p", "The background is never even: the lighting makes a gradient. Gerbil therefore fits a **surface** that "
          "follows it: for L\\*, a\\* and b\\*, a polynomial of degree 2 in x and y, fitted by **least squares** "
          "on the background pixels. It starts from the median colour (the background is the largest part), keeps "
          "the close pixels (distance < 12), then four times fits and keeps only the very close ones (< 6). If the "
          "median lightness of the background is under 35, the background is **dark** (velvet, felt) and several "
          "rules change."),

    ("h2", "Finding the object", "trouver-objet"),
    ("ul", ["**Hysteresis thresholding** (thresholds 8 and 18): the regions more different than 8 that hold at "
            "least one pixel more different than 18 are kept. A pale edge is kept if it belongs to a sharp object, "
            "an isolated pale stain is not (the principle of Canny's edge detector, applied to regions).",
            "**Morphology**: an *opening* removes dust and thin threads, a *closing* fills small gaps.",
            "**Holes**: a hole of the background colour and at least 0.02 cm² stays transparent (handle, "
            "perforation); the others (glare, light concretion) are filled."]),

    ("h2", "Sorting", "tri"),
    ("p", "Not everything that differs from the background is the object. The pieces found are sorted:"),
    ("table", [["Element", "How it is recognised"],
               ["The scale", "its area is removed; an object laid close by is kept if it is 8 mm away and clearly "
                             "differs from the background."],
               ["Unmeasured scale, label", "long straight sides at right angles and printed content (black and "
                                           "white, little colour); on 191 free photos, no object left out this way."],
               ["Cast shadow", "darker than the background but of its colour, smooth, with a blurred outer edge "
                               "(penumbra); the edge of an object is sharp."],
               ["Plexiglas support", "almost the colour of the background, sticks out of the object, as light or "
                                     "whiter."],
               ["Colour chart", "at least 5 sectors of vivid hue out of 12; a painted pot covers 2 at most (1,763 "
                                "photos tested)."],
               ["Labels, writing", "on the other side of the scale; everywhere thinner than 1.7 mm; small isolated "
                                   "pieces more than 8 mm from the object."],
               ["Paper label on a dark background", "light and rectangular (85% of its rectangle); a broken sherd never "
                                                    "fills its rectangle that much."]], [0.3, 0.7]),
    ("figure", "fig_dark", "On dark felt (synthetic photo): the paper label is left out (red outline), the "
                           "object kept (green outline)."),

    ("h2", "Refining the edge", "bord"),
    ("p", "The first cut-out, made on the reduced copy, is made again **at full resolution** in a band around the "
          "outline, then softened (0.8 px blur): a sharp edge without steps, like a cut-out by hand. On a dark "
          "background, the edge is placed in the middle of the gradient and its last pixels take the colour of the "
          "object: no dark fringe."),

    ("h2", "Reading a checkerboard scale", "damier"),
    ("ol", ["**Spot** the ink: black or red pixels, in elongated groups (2.5 times longer than wide).",
            "**Straighten** a thumbnail of the scale to horizontal.",
            "**Read the squares**, column by column: which row is inked; runs of similar columns are the squares.",
            "**Second reading** if digits are printed in the squares: a regular \"comb\" is fitted on the boundaries "
            "between squares.",
            "**Measure at full resolution**, to the sub-pixel: px/cm = length of the squares ÷ number of squares.",
            "**Turn it the right way up**: the printed signs (\"5\", \"10\", \"cm\") are compared with digits drawn "
            "in 12 fonts; on 1,265 scales of known orientation, no error."]),
    ("p", "Checks: usual length (5, 10 or 20 cm), regular squares (gap < 15%). A scale cut by the edge is measured "
          "on its complete squares."),

    ("h2", "Reading a millimetre ruler", "reglet"),
    ("p", "The ticks are thin, parallel dark lines: Gerbil spots them (\"black-hat\" filter), groups them in regular "
          "rows and fits a series x = start + step × k on the fifty or so ticks. Measuring a step over ~50 intervals "
          "gives a precision of about **0.1%**."),

    ("h2", "Learned scales", "apprises"),
    ("p", "Both ends of a scale of another kind are shown once; Gerbil keeps its image. On another photo, it looks "
          "for it **roughly** with keypoints (SIFT) matched and filtered by **RANSAC**, then **finely** by "
          "correlation (ECC), which measures the length to better than 0.1% (0.05% measured) when it is the same "
          "physical scale."),

    ("h2", "Mounting putty", "pate"),
    ("p", "Gerbil looks along the outline for two hollows that cut off a part of the object. That part is possible "
          "putty if it is at once smoother, of another colour, less colourful and lighter than the rest. By default "
          "it is only flagged (red area); `--remove-putty` removes it."),

    ("h2", "BiRefNet: the cut-out by machine learning", "ia"),
    ("p", "The cut-out by the colour follows rules written by hand: fast and exact on a really plain background, it "
          "is fooled by a cast shadow, the edge of the table or a white object on white. **BiRefNet**, the default "
          "cut-out, is an algorithm of **machine learning**: a neural network whose 220 million or so settings were "
          "written by nobody but learned by showing it hundreds of thousands of images already outlined. It points "
          "out the objects; Gerbil then sorts the pieces as usual (scale, label, chart, support) and always draws "
          "the edge from the photo, at full resolution."),
    ("ul", ["Everything runs on the computer: no photo is sent over the internet.",
            "*BiRefNet* (970 MB, downloaded once): about 20 s more per photo; *BiRefNet, lighter* (224 MB): faster, "
            "a little less sure on difficult cases. From the command line: `--cutout ai` and `--cutout ai-lite`.",
            "On a real set of 13 sherds, the cut-out by the colour left 5 to verify or badly outlined (shadows, "
            "table edge, white sherd); BiRefNet got them all right.",
            "**Second opinion** (*Advanced settings*): IS-Net or BiRefNet may only **remove** background "
            "(perforations, gaps, halos), never add: its mistakes therefore have no effect.",
            "**One click on the object** (review): **Segment Anything**, MobileSAM version (45 MB); it is told which "
            "object to outline, Gerbil keeps its own edge where both agree."]),

    ("h2", "Colours: balance and exposure", "couleurs"),
    ("p", "By default, the colours are kept. *Colour: balance* removes the cast of the light by making a white of "
          "the photo neutral; *exposure* also brings this white to the same lightness on every photo (85% "
          "luminance), for an even series. The correction comes **after** the cut-out, which stays the same; the "
          "copy of the original is never changed."),
    ("ul", ["*colour chart* (default): the white patch of a chart (SpyderCheckr, ColorChecker, Farbkarte) or the "
            "white centre of an Archaeo Colorimeter; without a chart, no correction.",
            "*scale*: when it is really white (some are cream).",
            "*background*: on white paper only."]),
    ("note", "These are corrections of the light, not a calibration: reading the Munsell code is still done on the "
             "object."),

    ("h2", "From the measurement to 1:1", "un-pour-un"),
    ("p", "An image file holds a **resolution** (pixels per inch) that Illustrator uses to size a placed image. "
          "Gerbil writes the measured resolution there:"),
    ("code", "ppi = px/cm × 2.54        (1 inch = 2.54 cm)\n"
             "example: 100 px/cm → 254 ppi: an object 600 px wide measures 6 cm"),
    ("p", "The image is never enlarged or reduced: only the resolution tag changes. The **PSD** is written byte by "
          "byte (layer masks: nothing is erased); the **TIFFs** are lossless (LZW), with transparency."),

    ("h2", "Metadata", "metadonnees"),
    ("ul", ["**EXIF**: the camera information (body, lens, focal length, date, aperture, ISO), copied.",
            "**XMP**: a structured text packet inside the file: the measurement of the scale, the output name, the "
            "fields of the renaming.",
            "**IPTC Core**: the fields of photo libraries (title, keywords, creator, copyright, location), written in "
            "the XMP. In a JPEG, the XMP is added without touching the image (checked pixel by pixel)."]),

    ("h2", "The conversion to DNG", "conversion"),
    ("p", "For each RAW photo: the date taken sorts the file; Adobe DNG Converter writes the DNG under the name of "
          "the renaming; **ExifTool** embeds the neighbouring XMP, then Gerbil's IPTC fields, and keeps in it the "
          "original RAW and the values given (`gerbil` XMP namespace). This is what lets everything be read back "
          "from the DNG files, and only what changed be redone, without any file next to the photos."),

    ("h2", "Plates: from the real to the paper", "planches-papier"),
    ("p", "Each object has its real size, read in the resolution of its TIFF; at scale 1:r, its size on paper is "
          "real size ÷ r (6 cm at 1:2 make 3 cm). The page is described as a list of shapes **in millimetres**; "
          "this same description is written as SVG and drawn for the preview, which thus shows exactly what will "
          "be written."),

    ("h2", "Precision and limits", "limites"),
    ("ul", ["The measurement is only right if the scale is **in the plane of the object**.",
            "The background must be plain and differ from the object; an opaque white support in a hollow is not "
            "recognised (erase it in *Review*).",
            "A very light object on white may lose parts with the cut-out by the colour: darker background, "
            "BiRefNet, or one click on the object.",
            "Another kind of scale is most often flagged: learn it, or give it by hand.",
            "On 1,764 reference photos, no scale already found changed from one version to the next: every change "
            "of the program is checked to the pixel on these sets."]),

    ("h2", "For a methodology", "methodologie"),
    ("p", "A paragraph to adapt for the report:"),
    ("quote", "\"The finds were photographed on a plain background with a scale in the plane of the photographed "
              "face. The photographs were outlined and scaled with Gerbil 2.3 (Charbonnel 2026, free software, GPL "
              "v3). The scale of each photograph is detected and measured automatically (checkerboard: length of the "
              "squares fitted to the sub-pixel; ruler: millimetre step fitted over all the ticks, precision about "
              "0.1%), then the real resolution is written into the files, which gives the objects back at 1:1. The "
              "cut-out relies on the colour distance (CIELAB) to a polynomial model of the background, with "
              "hysteresis thresholding; doubtful cases were flagged by the software and checked one by one.\""),

    # ------------------------------------------------------------------------------------------------ 7
    ("part", "7", "Inspirations and sources", "The practices, conventions, methods and programs whose ideas Gerbil "
     "takes up.", "inspirations"),

    ("h2", "Where Gerbil comes from", "origine"),
    ("p", "Gerbil was born from a gesture repeated thousands of times in the finds room: outlining an object in "
          "Photoshop, then scaling it again by hand for the plate. It grew with the needs of a team: file names "
          "and metadata, then the \"Convert RAW to DNG\" protocol of the MAFKF / QSR mission (Failaka, Kuwait), "
          "written by Eloïs Charbonnel and brought as it is into step 04, then plates, the field and the deposit."),
    ("p", "Three principles guide it: **never change the originals**, **say when unsure** rather than be wrong in "
          "silence, and **keep identical to the pixel** the results already right from one version to the next."),

    ("h2", "Archaeological drawing and plates", "normes-dessin"),
    ("ul", ["Conventions for drawing archaeological objects (Brussels, DMS 2009): publication reductions, pottery "
            "and glass at 1/3, iron at 2/3 or 1/3, stone at 1/3 or 1/6: the **scales per material** of the plates.",
            "M. Jean, *Le dessin archéologique* (2008): \"the graphic scale must always be present\": the **scale "
            "bar** of every plate.",
            "M. Jean, *Didacticiel infographie céramique* (2010): pottery presented at 1/3 and plates mounted in "
            "Illustrator.",
            "Arcelin and Rigoir, Feugère, Foy and Vallauri (1982), SA (2011), Prodhomme: conventions for drawing "
            "pottery and other finds, preparing publications.",
            "S. Eusèbe (Inrap), *La représentation scientifique des vestiges archéologiques*: \"details\" such as "
            "the graphic scale matter."]),

    ("h2", "Image processing methods", "methodes"),
    ("table", [["Method", "In Gerbil", "Reference"],
               ["CIELAB", "colour distance to the background", "CIE, L\\*a\\*b\\* space (1976)"],
               ["Hysteresis", "keep the pale edges of a sharp object", "J. Canny, *A Computational Approach to Edge "
                                                                      "Detection*, 1986"],
               ["Least squares", "polynomial model of the background, comb of the ruler", "Legendre, Gauss"],
               ["SIFT", "find a learned scale again", "D. Lowe, *Distinctive Image Features from Scale-Invariant "
                                                      "Keypoints*, 2004"],
               ["RANSAC", "keep the matches that agree", "M. Fischler and R. Bolles, 1981"],
               ["ECC", "fine alignment of a learned scale", "G. Evangelidis and E. Psarakis, 2008"],
               ["IS-Net", "second opinion", "X. Qin et al., *Highly Accurate Dichotomous Image Segmentation*, "
                                               "2022"],
               ["BiRefNet", "default cut-out, second opinion", "P. Zheng et al., *Bilateral Reference for High-Resolution "
                                                         "Dichotomous Image Segmentation*, 2024"],
               ["Segment Anything", "one click on the object", "A. Kirillov et al., 2023; MobileSAM: C. Zhang et al., "
                                                               "*Faster Segment Anything*, 2023"]],
     [0.2, 0.36, 0.44]),

    ("h2", "Programs that inspired the interface", "logiciels-inspiration"),
    ("ul", ["**Excel**: the handle that copies a cell down, series, {{Ctrl+D}}.",
            "**QGIS**: the scale bar (style, segments, units) of the plates.",
            "**PowerShell**: the naming rule read as `-match`, and the inventory line to copy, to learn.",
            "**Bridge and Lightroom**: the IPTC fields and the neighbouring XMP, embedded as they are.",
            "**Photoshop**: the PSD with layers and layer masks, to take the cut-out up again with a brush.",
            "**The draughtsman's graph paper**: the grid of the window and of this guide, and the checkered progress "
            "chart."]),

    ("h2", "Formats, metadata and archiving", "formats-archivage"),
    ("ul", ["**IPTC Photo Metadata Standard** (IPTC Core), written as **XMP** (ISO 16684-1).",
            "**DNG** (Adobe Digital Negative), an open archival format for RAW photos.",
            "**CINES**: selection of formats for long-term preservation and the FACILE validation tool "
            "(<https://www.cines.fr/preservation/expertises/file-format/selection/>).",
            "**HEG Geneva (ArchiLab)**: TIFF for digitised images, PNG for the web, SVG for vectors.",
            "**Consortium 3D (Huma-Num)** and **CND3D**: life cycle and archiving of 3D data, leads for the future."]),

    # ------------------------------------------------------------------------------------------------ 8
    ("part", "8", "Appendices", "Everything one looks up once used to the program.", "annexes"),

    ("h2", "Keyboard and mouse shortcuts", "raccourcis"),
    ("table", [["Where", "Key or gesture", "Effect"],
               ["Step 01", "{{Enter}} in the path field", "adds the folder pasted"],
               ["Step 01", "{{Delete}}", "removes the chosen row"],
               ["Step 01", "drop folders on the icon", "adds them at start"],
               ["Tables of the steps", "double-click a row", "opens what needs fixing"],
               ["Batch renaming", "double-click a cell", "edit it; {{Enter}} accepts, {{Esc}} cancels"],
               ["Batch renaming", "drag the handle of a cell", "copies down; with {{Ctrl}}: a series"],
               ["Batch renaming", "{{Ctrl+D}}", "copies the first row chosen to the others"],
               ["Batch renaming", "{{Ctrl+A}}", "chooses all rows"],
               ["Batch renaming", "{{Ctrl}} / {{Shift}} + click", "choose several rows"],
               ["Review", "mouse wheel", "zoom"],
               ["Review", "right or middle button, {{Space}} + drag, arrows", "move the view"],
               ["Review", "{{R}}", "whole photo"],
               ["Review", "{{Ctrl+Z}}", "undo the last action"],
               ["Review", "{{Shift}} + click (one-click tool)", "remove an object"],
               ["Scale by hand", "drag a point", "adjust it; wheel: zoom; {{R}}: see all"],
               ["Plates", "mouse wheel, ◀ ▶", "zoom, pages"],
               ["Plates", "click an object", "choose its scale"],
               ["Everywhere", "mouse on a setting", "its explanation"]], [0.22, 0.38, 0.4]),

    ("h2", "Command line options", "options"),
    ("p", "`py gerbil.py FOLDER --option` (scripts) or `gerbil_cli.exe FOLDER --option` (.exe version):"),
    ("table", [["Option", "Effect"],
               ["`-o FOLDER`", "output folder (default `outlined_result` next to the photos)"],
               ["`--cutout colour|ai|ai-lite`", "cut-out by the colour, by BiRefNet or BiRefNet lighter (the "
                                                "command line keeps the colour by default)"],
               ["`--colour none|balance|exposure`, `--white chart|scale|background`", "colours and white reference"],
               ["`--background white`", "TIFF on white"],
               ["`--remove-putty`", "removes the putty found"],
               ["`--layout original`", "leaves the scale where it is"],
               ["`--scale-cm 10`, `--no-scale`", "forces the length of the scale; no scale"],
               ["`--margin-cm`, `--gap-cm`", "margin around the object, gap object / scale (0.5 cm)"],
               ["`--no-psd`, `--no-original-layer`, `--no-original-copy`, `--no-control`", "fewer files"],
               ["`--compression lzw|zip|none`", "TIFF compression"],
               ["`--default-ppi 300`", "resolution without a scale"],
               ["`--ai`, `--ai-model isnet|birefnet|birefnet-lite`, `--ai-device cpu`", "second opinion (machine learning)"],
               ["`--profile FILE`", "site profile"],
               ["`--refresh-names`", "applies a changed renaming without processing again"],
               ["`-j 4`, `--open`, `-v`", "photos in parallel; open at the end; error details"],
               ["`--dng FOLDER`, `--jpg preview|full|none`, `--tiff`", "RAW to DNG conversion (step 04)"]],
     [0.5, 0.5]),

    ("h2", "The outlined_report.csv report", "rapport"),
    ("p", "One row per photo, \";\" separator and decimal comma (French Excel). States: `ok`, `to verify`, `failed`, "
          "`error`. The fields of the renaming are added as columns."),
    ("table", [["Column", "Content"],
               ["`file`, `output_name`", "name of the photo, name of the files written"],
               ["`status`, `to_verify`", "state, and reasons for the doubt"],
               ["`scale_found`, `scale_type`", "`checkerboard`, `ruler`, `manual`, `learned`"],
               ["`squares`, `scale_length_cm`", "number of squares, length of the scale"],
               ["`px_per_cm`, `ppi_1_1`", "the measurement, and the 1:1 resolution"],
               ["`object_width_cm`, `object_height_cm`", "size of the outlined object"],
               ["`pieces`", "number of pieces outlined"],
               ["`camera`, `lens`, `focal_mm`, `date_taken`", "shooting data (EXIF)"],
               ["`notes`, `duration_s`", "remarks, duration"]], [0.42, 0.58]),

    ("h2", "Files written next to the photos", "fichiers-voisins"),
    ("p", "What is decided for a **cut-out** is kept next to the photos, so that a later run or a colleague finds it; "
          "archive them together. The **conversion** writes nothing next to them: everything is in the DNG files."),
    ("table", [["File", "Content"],
               ["`gerbil_project.json`", "batch renaming: fields, template, rule, values, IPTC"],
               ["`gerbil_scales.json`", "scales given by hand"],
               ["`gerbil_edits/`", "corrections of the review (masks, angles)"],
               ["`gerbil_profile.json`", "site profile placed in the folder"],
               ["`NAME.xmp`", "IPTC metadata next to the original, if asked for"]], [0.35, 0.65]),

    ("h2", "Troubleshooting", "depannage"),
    ("table", [["What you see", "What to do"],
               ["\"Windows protected your PC\"", "*More info*, then *Run anyway* (unsigned program)."],
               ["An orange \"missing packages\" banner", "*Install now* (scripts version): numpy, OpenCV, Pillow, "
                                                         "rawpy."],
               ["\"Scale not found\"", "check it is whole and sharp; [[echelle-main|give it by hand]] or "
                                       "[[profils|learn it]]."],
               ["Parts of a light object are missing", "*Cut-out: BiRefNet*, darker background, or one click on the object "
                                                       "in *Review*."],
               ["The shadow is kept with the object", "*Cut-out: BiRefNet*, or *Remove a piece*."],
               ["\"Missing information\"", "fill in the required fields of the batch renaming ([[relire|check]])."],
               ["Two photos have the same output name", "Gerbil adds a suffix; complete the template (number, view)."],
               ["Step 04 asks for Adobe DNG Converter", "install it (free, from Adobe), then run again."],
               ["The cut-out is slow", "*BiRefNet, lighter*, or *by the colour* for a really plain background."],
               ["The measurement seems a few % off", "was the scale in the plane of the object? Check with "
                                                     "`NAME_outlined_scale.tif` in Illustrator."]], [0.42, 0.58]),

    ("h2", "Glossary", "lexique"),
    ("defs", [("1:1, scale 1:r", "1:1: real size. At scale 1:3, the object is three times smaller on paper."),
              ("Batch renaming", "The names and information of all the photos of a folder, at once."),
              ("Checkerboard", "A scale of alternating 1 cm squares, black and white (or red)."),
              ("CIELAB", "A colour space close to perception: lightness L\\*, axes a\\* and b\\*."),
              ("Colour chart", "A card of reference colours (SpyderCheckr, ColorChecker) photographed with the "
                               "object."),
              ("Contact sheet", "All the photos of a folder, small, on pages, to find one's way."),
              ("Cut-out", "Separating the object from its background; the background becomes transparent."),
              ("Deposit", "Handing a set of files over to an archive."),
              ("DNG", "Digital Negative: Adobe's open format to archive RAW photos, with their metadata."),
              ("EXIF", "Information written by the camera: body, lens, date, settings."),
              ("Hysteresis", "Thresholding with two thresholds: keep what passes the low one if it touches what passes "
                             "the high one."),
              ("IPTC", "The standard set of fields of photo libraries (title, creator, location, keywords…)."),
              ("Layer mask", "In a PSD, what hides part of a layer without erasing it."),
              ("Metadata", "Information written into a file, besides the image."),
              ("Naming rule", "What every name must follow, written as a regular expression."),
              ("Orthophoto", "A straightened image, without perspective, at a constant scale, often georeferenced."),
              ("Plate", "A page of figures of a publication, at a given scale."),
              ("PSD", "Layered Photoshop file."),
              ("px/cm, ppi", "Pixels per centimetre (measured on the scale); pixels per inch (= px/cm × 2.54), "
                             "written into the files."),
              ("RAW", "The raw file of the camera (CR2, CR3, NEF, ARW…), before development."),
              ("Ruler", "A rule graduated in millimetres."),
              ("SHA-256", "A fingerprint of a file: if a single byte changes, it changes; used to check a transfer."),
              ("Site profile", "What Gerbil knows of a site: background, scales, fields, name template, settings."),
              ("SVG", "A vector drawing format, opened by Illustrator and Inkscape."),
              ("Thumbnail", "A small copy of an image, for a database."),
              ("TIFF", "A lossless image format, with transparency: the format of the outlined objects."),
              ("White balance", "A correction that makes a white neutral, to remove the cast of the light."),
              ("XMP", "The format of the metadata written into files (or into a neighbouring .xmp file).")]),

    ("h2", "Libraries and programs", "bibliotheques"),
    ("p", "Gerbil relies on free software; many thanks to their authors."),
    ("table", [["Name", "Role in Gerbil", "Licence"],
               ["Python", "the language of the program", "PSF"],
               ["numpy", "images as arrays of numbers, computations", "BSD"],
               ["OpenCV", "image processing: colours, morphology, contours, SIFT, ECC", "Apache 2.0"],
               ["Pillow", "reading and writing images, drawing the plates", "MIT-CMU"],
               ["rawpy, LibRaw", "developing RAW photos", "MIT; LGPL 2.1 or CDDL"],
               ["onnxruntime", "running the networks of machine learning on the computer", "MIT"],
               ["BiRefNet, IS-Net", "cut-out networks (ONNX exports by rembg)", "MIT; Apache 2.0"],
               ["MobileSAM", "one click on the object (ONNX export by Acly)", "MIT"],
               ["Tk (tkinter)", "the windows", "Tcl/Tk BSD licence"],
               ["ExifTool", "writing the metadata of the DNG files (shipped)", "Perl licence"],
               ["Adobe DNG Converter", "converting RAW photos to DNG (to install)", "free, proprietary"],
               ["Inkscape", "converting .ai, .pdf, .eps drawings (optional)", "GPL"],
               ["PyInstaller", "building Gerbil.exe", "GPL with exception"],
               ["Source Serif 4, Cormorant Garamond, Courier Prime", "the fonts of the interface and of the guides",
                "SIL OFL"]], [0.3, 0.48, 0.22]),

    ("h2", "Citing Gerbil, licence", "citer"),
    ("p", "Charbonnel E. 2026. *Gerbil: the archaeologist's photo toolkit*, version 2.3. Free software, GNU GPL v3 "
          "or later. <https://github.com/EloisCharbonnel/gerbil>"),
    ("p", "Gerbil comes without any warranty. It may be used, studied, changed and shared under the terms of the "
          "licence (`LICENSE` file)."),
]

# =============================================================================================================
# GUIDE TO THE CODE
# =============================================================================================================

CODE = [
    ("part", "1", "The program as a whole", "The files, how they talk to each other, and the way of a photo in the "
     "code. The processing itself (methods, thresholds) is described in the user guide and in docs/PSEUDOCODE.txt.",
     "programme"),

    ("h2", "The files", "fichiers"),
    ("table", [["File", "Role"],
               ["`gerbil.py`", "the engine: everything that processes a photo, and the command line; it knows nothing "
                               "of the windows"],
               ["`gerbil_gui.pyw`", "the interface: the windows; it runs the engine as a separate program"],
               ["`gerbil_dng.py`", "the RAW to DNG conversion (Adobe DNG Converter, ExifTool)"],
               ["`gerbil_plates.py`", "the SVG plates"],
               ["`gerbil_tools.py`", "the CSV inventory and the thumbnails"],
               ["`gerbil_lang_fr.py`", "the French texts of the interface"],
               ["`packaging/gerbil_setup.pyw`", "the installer"],
               ["`tests/`", "the automatic tests, on synthetic photos"],
               ["`docs/`", "pseudo-code, roadmap, sources, guides and their generators"]], [0.35, 0.65]),

    ("h2", "How they talk to each other", "dialogue"),
    ("code", "gerbil_gui.pyw  (windows)  --runs-->  gerbil.py / gerbil_cli.exe  (engine, one photo after the other)\n"
             "       |                                  |\n"
             "       |  reads the printed lines         +--> outlined_result/ : PSD, TIFF, previews, report\n"
             "       |  (\"[3/12] NAME: ok ...\")         |\n"
             "       |                                  +--> reads gerbil_project.json, gerbil_scales.json,\n"
             "       |                                       gerbil_edits/, gerbil_profile.json\n"
             "       +--> gerbil.py --dng  -->  gerbil_dng.py  -->  Adobe DNG Converter, ExifTool\n"
             "       +--> gerbil_plates.py (plates)    gerbil_tools.py (inventory, thumbnails)"),
    ("p", "The interface does not process photos itself: it builds the command line from the settings, starts the "
          "engine (`subprocess`) and reads the lines it prints to show the progress. A few windows call functions of "
          "the engine directly (`import gerbil`), to read a photo or learn a scale. The batch renamings kept in "
          "memory are given to the engine through a temporary file named in the `GERBIL_PROJECTS` variable."),

    ("h2", "The way of a photo in the code", "chemin-code"),
    ("p", "The `process_photo` function of `gerbil.py` calls, in order:"),
    ("ol", ["`load_photo`: reads the file (RAW through `develop_raw`), turns it upright, keeps EXIF and colour "
            "profile.",
            "`BackgroundModel`: the background model, on the reduced copy.",
            "`manual_scale`, else `detect_scale` (`analyze_pattern`, `analyze_comb`, `detect_ruler`, "
            "`_scale_on_dark`…), else `detect_learned_scale`: a `Scale` object.",
            "`outline_object` (or `cutout_from_mask` for a mask fixed by hand), then `find_putty`.",
            "`layout`, then `write_psd`, `write_tiff` (with `make_xmp`), `control_image`, `write_review`.",
            "The report row is returned; `main` writes `outlined_report.csv` and the summary."]),
    ("h2", "The way of a conversion", "chemin-dng"),
    ("ol", ["`gerbil.py --dng` hands over to `gerbil_dng.main`, which opens ExifTool once (`-stay_open`) with the "
            "`gerbil` XMP namespace.",
            "`convert` groups the RAW photos by folder; `convert_folder` reads the renaming (`gerbil.load_project`) "
            "and the DNG files already made (`previous_outputs`).",
            "For each RAW photo: the date taken, the name, Adobe DNG Converter, the neighbouring XMP, the IPTC "
            "fields, the JPG (and the TIFF through `develop_to`), a report row."]),

    ("part", "2", "Python notions", "Enough to read any line of the program.", "python"),
    ("h2", "Useful notions", "notions"),
    ("defs", [("Module, import", "Each file is a module. `import gerbil as g` gives access to its functions "
                                 "(`g.load_photo`); `from PIL import Image` takes a single name."),
              ("Function", "`def name(arguments):` receives values and returns a result (`return`); the body is the "
                           "indented block under the `def` line."),
              ("Docstring", "The first string of a function, in triple quotes: its explanation. The reference shows "
                            "it."),
              ("Class, method, self", "`class Name:` gathers data and the functions that work on it (its methods); "
                    "`self` is the object itself. Each window is a class: its `__init__` builds it, its methods "
                    "answer the user."),
              ("@dataclass", "A class that is mostly a record of named values (`Scale`, `PlateSettings`)."),
              ("Dictionary, list, tuple", "`{\"key\": value}`: settings, report rows, JSON; `[a, b]`: ordered values; "
                    "`(x, y)`: a fixed group."),
              ("numpy array", "An image is an array: `rgb[y, x]` is a pixel, `rgb.shape` is (height, width, 3). An "
                              "operation applies to all pixels at once, without a loop."),
              ("Mask", "An array of true / false the size of the image: `rgb[mask]` gives the pixels of the object."),
              ("OpenCV (cv2)", "Image processing: resize, blur, Lab, morphology (`cv2.erode`, `cv2.dilate`), "
                               "connected components, contours."),
              ("Exceptions", "`try: … except OSError:` catches an error instead of stopping the program."),
              ("f-string", "`f\"{px_cm:.2f} px/cm\"` writes values into a text."),
              ("Parallel work", "The engine processes several photos at once (`ProcessPoolExecutor`); the interface "
                                "stays responsive with threads (`threading.Thread`) and `after(ms, function)`."),
              ("tkinter", "The windows: widgets (`ttk.Button`, `tk.Canvas`) placed with `pack` or `grid`; `command=` "
                          "and `bind(\"<Event>\", function)` link a click to a method."),
              ("Themes", "The colours are named by their role (`INK`, `TINT`, `RAIL`, `CARD_BG`…) and chosen by "
                         "`use_theme()` before the windows are built.")]),
    ("h2", "A small glossary to read a line", "lexique-ligne"),
    ("table", [["Written", "Read as"],
               ["`a = b`", "a receives the value of b (not an equality)"],
               ["`a == b`, `a != b`", "is a equal to b? different?"],
               ["`a += 1`", "a increases by 1"],
               ["`x ** 2`", "x squared"],
               ["`if … :`, `elif … :`, `else:`", "if…, else if…, else"],
               ["`for x in items:`", "for each element of the list"],
               ["`# text`", "a comment, for the reader"],
               ["`lab[..., 0]`", "channel 0 (L\\*) of all the pixels"],
               ["`rgb[y0:y1, x0:x1]`", "a rectangle of the image"],
               ["`self.name`", "a piece of data of the object (the window, the scale…)"],
               ["`None`", "\"nothing\": no value"]], [0.35, 0.65]),

    ("part", "3", "Real functions, line by line", "These extracts are read from the code when the guide is made: "
     "they are exactly the lines of the program.", "lignes"),
    ("h2", "to_lab: going to CIELAB", "to-lab"),
    ("annotated", "gerbil.py", "to_lab", [
        "Defines the function `to_lab`, which receives `rgb`, an image in red-green-blue.",
        "The docstring: what the function does and why.",
        "OpenCV converts the image to Lab; `.astype(np.float32)` goes to decimal numbers. OpenCV stores each channel "
        "from 0 to 255.",
        "Channel 0 (L\\*) is brought back to the usual 0–100 scale.",
        "Channels 1 and 2 (a\\* and b\\*) are centred on 0.",
        "Returns the image in Lab."]),
    ("h2", "distance: how much a pixel differs from the background", "distance"),
    ("annotated", "gerbil.py", "distance", [
        "Receives the image in Lab, the reference colour (the background model) and the weight of lightness (0.5).",
        "The docstring.",
        "Lightness gap of each pixel to the background, times the weight: a shadow counts less.",
        "Gap on a\\* (green–red).",
        "Gap on b\\* (blue–yellow).",
        "The distance: square root of the sum of squares, for all pixels at once."]),
    ("h2", "hysteresis: keep sharp regions and their pale edges", "hysteresis"),
    ("annotated", "gerbil.py", "hysteresis", [
        "Receives the distance map `d` and both thresholds (8 and 18).",
        "The docstring.",
        "`weak`: the pixels above the low threshold.",
        "OpenCV numbers the connected regions of `weak`; `lab` gives the number of each pixel (a \"label\", nothing "
        "to do with Lab colours).",
        "A list of `n` answers \"keep?\", all no.",
        "The regions that hold a pixel above the high threshold turn to yes.",
        "Region 0, the background, is never kept.",
        "Each pixel takes the answer of its region: the mask."]),
    ("h2", "parse_ratio: reading a scale written \"1/3\"", "parse-ratio"),
    ("annotated", "gerbil_plates.py", "parse_ratio", [
        "Receives a text: \"1/3\", \"1:3\" or \"3\".",
        "The docstring: \"2/3\" gives 1.5 (reduction to two thirds).",
        "The text is cleaned; a decimal comma becomes a point.",
        "Try what follows; on an error, go to `except`.",
        "If the text holds \"/\" or \":\"…",
        "… cut it in two: `a` before, `b` after…",
        "… and return b ÷ a (1/3 → 3).",
        "Else, return the number alone.",
        "If reading fails or divides by zero…",
        "… return `None`: the interface keeps the old value."]),
    ("h2", "Tooltip.__init__: a help bubble on a button", "tooltip"),
    ("annotated", "gerbil_gui.pyw", "Tooltip.__init__", [
        "The method that builds a help bubble: `widget` is the element, `text` the explanation.",
        "The docstring.",
        "Keeps the element and the text; the bubble and the planned task do not exist yet.",
        "When the mouse **enters**: plan the display (450 ms); `add=\"+\"` keeps the other bindings.",
        "When the mouse **leaves**: hide the bubble.",
        "On a **click**: hide it.",
        "When the element loses the **focus**: hide it.",
        "When the element is **destroyed**: hide it."]),

    ("part", "4", "Changing the code without breaking anything", "The house rules, the tests, and how to make the "
     "guides again.", "modifier"),
    ("h2", "The rules", "regles"),
    ("ul", ["Names and messages in English; constants in capitals at the top of their section, with a comment.",
            "Comments say *why*; docstrings say *what* and, briefly, *how*.",
            "**A change must leave identical, to the pixel, the results already right**: it is checked on the "
            "reference sets before being adopted (`CONTRIBUTING.md`).",
            "The names of the files written do not change without a reason: other tools read them.",
            "The `.bat` files keep Windows line endings (CRLF)."]),
    ("h2", "Tests and guides", "tests-guides"),
    ("code", "py -3 -m pytest tests                    the automatic tests (synthetic photos)\n"
             "py -3 docs/make_code_guide.py            docs/CODE_GUIDE.md\n"
             "py -3 docs/make_guide_shots.py           the screenshots of the interface (needs a screen)\n"
             "py -3 docs/make_guide_pdf.py             the four PDF guides (Edge or Chrome)"),
    ("p", "A new function shows in the French reference with its English explanation, flagged \"à traduire\": add "
          "it to `docs/fr/reference_fr_more.py`."),
]
