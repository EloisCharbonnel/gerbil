# Gerbil — Archaeological photo toolkit: roadmap

Gerbil aims to become a free, open-source tool for archaeologists who process 2D photos: outlining,
true 1:1 scale, naming and plates. **First scope: finds** (ceramics, metal, bone, glass, lithics…)
photographed with a scale. Sites, sections and orthophotos come later.

**Order decided (2026-10-21):** phase A, then phase B (both done), review window and plates (done).
**Order proposed (2026-10-24):** C (end), G profiles, H metadata and inventory, I one-click cut-out,
then F open source; J 3D and K archiving after; the database of graphic documentation at the very end.
Sources behind these choices: `docs/REFERENCES.md`.

## Principles

- **The human eye decides.** Gerbil prepares the files; it never replaces the drawing or the
  specialist's judgement. Every result stays editable (PSD layer masks), and every doubt is flagged
  (`_to_be_verified`).
- **Zero setting by default.** Dropping a folder must be enough; options are there for those who want them.
- **Measurements are layout aids, not data.** Sizes computed by Gerbil help to place the objects on a
  plate; they are not scientific measurements and are never presented as such.
- **No regression.** Every change is checked against reference photo sets: results already right must
  stay pixel-identical.
- **Offline.** Nothing needs an internet connection, a phone or a paid service (except downloading
  the optional AI model once).

## Done

| Version | Content |
|---|---|
| 1.5 | Outlining on a light background, checkerboard and ruler scales, PSD + TIFF at 1:1, putty, plexiglass supports, colour charts discarded, AI second opinion, interface and .exe |
| 1.6 | Checkerboard cut by the photo edge |
| 1.7 | Second checkerboard reading (digits inside the squares, 5/10/20 cm), black velvet backgrounds, paper labels discarded on velvet, objects lying close to the scale kept, rulers with thick ticks |

Measured on a 2025 sample from Qusur (42 photos, velvet and light backgrounds): 10 → 37 photos ready
without retouching. On 1,764 reference photos: no scale already found changed; photos without a
scale went from 67 to 12.

## Phase A — Finish the scale (short term)

1. ~~Release v1.7~~ (no official release before the end of the current ideas: Gerbil 2.0 is in development;
   the first public release will come with the GitHub repository).
2. ~~Rulers read as 3 or 4 cm when the first or last centimetre tick is missed~~ (done: the crop of the
   ruler is lengthened when its ticks reach its ends; on 1,764 reference photos, rulers of a doubtful
   length went from 48 to 16).
3. ~~Manual scale when detection fails~~ (done: "Set scale…" in the interface, two points of known
   distance, saved in `gerbil_scales.json` next to the photos).
4. ~~RAW files~~ (done: DNG, CR2, CR3, NEF, ARW, ORF, RW2, RAF… developed by LibRaw with the camera white
   balance, in the engine and in every window).
5. ~~Remaining cases of old low-resolution photos~~ (done as far as useful: a label with writing stuck to
   the scale no longer hides it, 448-px Qusur 2008 photos 11 → 12 of 14; enlarging the photo before the
   search found nothing more; the last one, 13-px squares in three rows, goes to the manual scale).
6. ~~Orientation of the scale~~ (done: turned upright from the digits printed in its squares, the red
   row deciding only when they are unclear).
7. ~~An installer~~ (done: `Gerbil_Setup.exe`, one file, installs for the user without administrator
   rights, Start menu and desktop shortcuts, entry in Windows "Installed apps", updates keep the AI
   models).

## Review and correction window

**Done (2026-10-21)**, lasso included, except moving the outline of the scale (the scale is fixed by two
points). Instead of retouching the bad outlines in Photoshop and running the export again:

1. A **review window** in the interface, photo by photo (doubtful ones first): the photo with the
   outline of the cut-out (green) and of the scale (magenta), as in the `to_control` previews.
2. **Erase / add brushes** on the cut-out (with a size slider and undo), plus quick tools: click on a
   piece to remove it entirely (shadow, background patch between two objects), lasso.
3. Correct the scale in the same window: move its outline, or click two points and give their distance
   (the manual scale of phase A).
4. **Orient the object** as the archaeologist decides (never automatic): for instance draw a line along
   the rim of a sherd, which becomes horizontal and goes on top, or turn it with a handle or by 90°
   steps. The scale stays straight under it; the rotation is applied once, at the export (one
   resampling only), and the original photo stays untouched in the hidden layer of the PSD.
5. **Accept**: only this photo is exported again (PSD, TIFF, preview, report row), from the corrected
   mask; the correction is saved so that a later run does not undo it.

## Phase B — Naming and metadata

**Done (2026-10-21/22)**: project file `gerbil_project.json` next to the photos, *Batch renaming…* window (fields,
template with preview, rule read like PowerShell -match with a rule helper (ready-made conditions, the
PowerShell line, a test of a name), common values, table per photo with photo
thumbnail, Excel-like fill handle, Ctrl+A / Ctrl+D, numbering, CSV / Excel import), fields in
the review window, output names, XMP, report columns, doubts in the summary. Choices of the user: only
the output files are renamed; the settings travel with the photos.

1. A **context panel** in the interface: site code, sector, stratigraphic unit (US), object number…
   (the list of fields is editable per project).
2. **Material** check boxes: ceramic, metal, bone, glass, lithic, other (editable list).
3. A **naming template** built from these fields, e.g. `{site}_{US}_{material}_{number}`, with a preview
   of the new names before anything is renamed. The original photo always keeps its name.
4. The same information written **inside** the files (XMP metadata), so that it follows the image.
5. **Naming rules set by each project** (the hard-coded `DDN_…` rule has been removed): a pattern the
   names must follow, checked and reported without blocking.
6. Import of an inventory (CSV / Excel) to fill the fields.

## Phase C — Plates

1. ~~Plates in SVG at a chosen scale~~ (done: `Plates…` window and `gerbil_plates.py`; objects in rows at
   their true size, captions from the names or the fields of phase B, embedded images, live preview).
2. ~~Page size, margins, grouping~~ (done: A4, A3, A5, Letter, custom, landscape; order and group by any
   column of the report, a new row or a new page per group).
3. ~~Optional measurements as layout guides~~ (done: width and height of each object as dimension lines
   on a hidden "Measurements (guides)" layer of the SVG; never in the report).
4. ~~Graphic scale bar on the plates~~ (done, in the manner of QGIS: 7 styles, segments and subdivisions,
   colours, font, numbers at the ends or at every segment, unit, "1:2" written; remembered as a house
   style). Not wanted for now in the PSD / TIFF of each photo (the user's choice, 2026-10-22).
5. ~~One scale per plate, large objects reduced~~ (done 2026-10-24: objects too large for the page go to
   1:1.5, 1:2, 1:3… on plates of their own, each with its bar; scale chosen per object; `{scale}`).
6. ~~**Reductions by material**~~ (done 2026-10-28), from the field "material" of phase B: ceramics and glass 1/3, iron 2/3 or
   1/3, stone and architecture 1/3 or 1/6 (DMS Bruxelles 2009), editable.
7. ~~Option: **several scales on one plate**~~ (done 2026-10-28), the scale written in the caption of each object (allowed by
   the conventions when the caption states it), each group with its own bar.
8. ~~**Drawings beside the photos.**~~ (done 2026-10-28, side by side; the overlay is still to do) The drawings are mostly Illustrator `.ai` files (recent ones hold a
   PDF that Inkscape converts), sometimes `.svg` (open-source users: Inkscape, GIMP, Éveha), almost
   always at 1:1 except large objects (scale given, or read from the drawing's bar). Matched to the
   photos by their names (object number). First side by side on the plate; later, an overlay aligned
   by two or three points clicked on both (rotation and scale only: the photo is never deformed).

## Phase G — Site profiles (fewer clicks)

1. ~~A profile per site / campaign~~ (done 2026-10-24: background, learned scales, options of the main
   window; library in %APPDATA%, `gerbil_profile.json` next to the photos to share). Still to add:
   naming template and plate settings in the profile.
2. ~~Scales "to learn"~~ (done 2026-10-24: two points on one photo; found again by matched points and a
   fine alignment, within 0.05 % on the same physical scale; one model per physical copy).
3. Profiles of other sites and teams gathered in the open-source repository (phase F).

## Phase H — Metadata, inventory, thumbnails

1. ~~**IPTC fields**~~ (done 2026-10-28) filled from the batch renaming fields, with a default mapping (title, creator,
   description, keywords, date, geographic unit, zone / sector, building, structure, US / locus,
   language, physical location, copyright: the model of the Shelby collection, `docs/REFERENCES.md`)
   that each project can change. Written in the output files, and for the original photos in a `.xmp`
   file next to them (the photo itself untouched).
2. ~~**Inventory as CSV**~~ (done 2026-10-28): photos and drawings of a folder, the columns chosen (fields of the name from the
   naming rule, metadata, size, date…), with the PowerShell line that does the same, shown for learning.
3. ~~**Thumbnails in batch**~~ (done 2026-10-28) for databases: PNG or JPEG (GIF has 256 colours only), size chosen, on a
   transparent or white background.

## Phase I — One-click cut-out

1. ~~Two ways~~ (done 2026-10-28, MobileSAM ONNX), side by side in the review window: **automatic** (as now) and **one click / more precise**:
   the archaeologist clicks on the sherd and a segmentation model ("Segment Anything" type, offline)
   draws its outline. It is more precise because the program is told *which* object to cut out: it no
   longer has to guess what is a sherd and what is a label, a shadow or the background.
2. **Learning from the corrections**: every mask corrected in the review window (`gerbil_edits`) is a
   true example; gathered from several sites (with the owners' permission), they can train a small
   cut-out model that improves the automatic way.

## Phase J — 3D data (checks and metadata, no viewer)

1. Integrity of 3D files (PLY, OBJ + MTL + textures, STL, glTF): opens, number of vertices and faces,
   missing textures, size, units.
2. Technical metadata (software, version, number of photos, resolution, texture size) and scientific
   ones (site, US, sector, year…) written in a sidecar file compatible with **aLTAG3D** / the
   Conservatoire National des Données 3D, rather than a new schema.
3. Thumbnails of the models for databases. Viewing stays with existing tools (MeshLab, 3DHOP).

## Phase K — Archiving assistant

1. **Checksums** (SHA-256) and a manifest of a folder, to prove later that nothing changed.
2. Check of the formats against those accepted for long-term archiving (CINES): TIFF, PNG, SVG, PDF/A,
   PLY, DAE…
3. Conversions where open tools exist: `.ai` (PDF-compatible) to SVG or PDF through Inkscape, open 3D
   formats to PLY. Proprietary project files (Metashape…) cannot be converted.

## At the very end — database of graphic documentation

The names (batch renaming) and the metadata already link photos, drawings, objects, US, sectors and
sites: Gerbil could build from them a **relational database of the finds' graphic documentation**
(SQLite: one table per kind — sites, contexts, objects, photos, drawings, 3D models), queried to mount
the plates or to answer "all the drawings of US 1209". Kept for the end: it needs the drawings (C.8),
the metadata (H) and the 3D data (J) first.

## Phase D — Colour charts

1. Detect the chart and calibrate the colours of the photo (optional).
2. Many models exist: one reference file per model (Pantone round colorimeter, X-Rite ColorChecker
   Classic and Passport…), so that users can add their own.
3. Report the calibration quality (ΔE) and leave the photo untouched when the chart is not recognised.

## Phase E — Label reading (assistance only)

1. OCR of the label to **suggest** the fields of phase B; the user always validates.
2. Labels are often handwritten: test the engines (offline only) on real labels and measure their
   accuracy before deciding.

## Phase F — Open-source project

1. GitHub repository, **GPL-3.0** licence, contribution guide.
2. Code split into an engine (library), the command line and the interface, so that others can add
   modules.
3. Interface and documentation in French and English (other languages welcome).
4. A public test photo set (with the owners' permission) and automatic checks on every change.
5. Versions for Mac and Linux.

## Later — beyond finds

- Scale from **orthophotos** (georeferenced images, GeoTIFF / world files) and from photogrammetry
  targets.
- Sections, structures and site photos.

## Ideas set aside

| Idea | Why |
|---|---|
| QR codes on labels | Labels do not last, extra cost, needs extra equipment on site |
| Vector outline export (SVG contour) | Nothing replaces the eye of the person drawing |
| Measurements as scientific data | Only layout aids (see Principles) |

## Open questions

- Which fields for the context panel, and which naming templates are used on other projects?
- Plates: one object per cell or free layout? Captions under each object?
- Which colour chart models are used by the teams interested?
- Order of the phases after B (C, D, E, F): should the GitHub repository open before?
