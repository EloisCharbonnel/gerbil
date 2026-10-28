# Gerbil — references

Sources that guide Gerbil's choices: archaeological drawing and plates, graphic documentation, archiving
of 2D and 3D data. Kept in mind for the roadmap (`docs/ROADMAP.md`).

## Archaeological drawing and plates (documents shared by Eloïs Charbonnel)

Folder: `Proton Drive\charbonnelelois\My files\09_Dessin-et-mobilier\` (PDF files, not copied here).

| File | Content | Notes for Gerbil |
|---|---|---|
| Arcelin & Rigoir, s.d. — *Normalisation du dessin en céramologie* | Drawing conventions for pottery | Scanned (no text layer) |
| Bruxelles, DMS 2009 — *Normalisation des dessins d'objets archéologiques* | Drawing and plate conventions | **Publication reductions: ceramics, glass 1/3; iron 2/3 or 1/3; stone, architecture 1/3 or 1/6.** Several reductions may share a plate if the caption states them; scale written in the plate caption |
| Collado 2021 — *Initiation au DAO Illustrator* | Computer-aided drawing with Illustrator | Drawings are mostly `.ai` files |
| David 2021 — *Dessin de l'industrie osseuse* | Drawing bone industry | |
| Feugère, Foy & Vallauri 1982 — *Normalisation du dessin non céramologique* | Conventions for non-ceramic finds | Scanned |
| Jean 2008 — *Le dessin archéologique* | Archaeological drawing, scales | **"The graphic scale must always be present"**; computing reduction rates; graphic scales follow the reduction |
| Jean 2010 — *Didacticiel infographie céramique* | Illustrator workflow for pottery | Pottery presented at 1/3; reduction to a third (33.33 %) when mounting plates; requests on files to mount plates |
| Laurent 1986 — *Dessin et archéologie* | Drawing and archaeology | |
| Prodhomme, s.d. — ch. 4 *Le dessin de l'objet* | Drawing finds | Scanned |
| Prodhomme, s.d. — *Préparation des publications archéologiques* | Preparing publications, plates | Scanned (190 p.) |
| SA 2011 — *Normalisation du dessin du mobilier non céramique* | Conventions for non-ceramic finds | Scanned |
| Thébaud 2020 — *Cours céramique antique L3* (2 files) | Course on Roman pottery | Mostly figures |

## Graphic documentation in archaeology

- Sylvie Eusèbe (Inrap, image, drawing and computer graphics) — *La représentation scientifique des
  vestiges archéologiques*: conventions of scientific representation; "details" such as the graphic
  scale or the north arrow matter. https://www.prehistoire.org/offres/gestion/actus_515_36665-911/la-representation-scientifique-des-vestiges-archeologiques-par-sylvie-eusebe.html
- Inrap — *La photogrammétrie, une alliée de l'archéologie préventive* (interview with S. Eusèbe):
  restitution is part of the chaîne opératoire. https://www.inrap.fr/entretien-la-photogrammetrie-une-alliee-de-l-archeologie-preventive-15050
- Inrap — *Archéologie, imagerie numérique et 3D* (seminar Inrap / Inria / IRISA).
  https://www.inrap.fr/archeologie-imagerie-numerique-et-3d-13628

## 3D data

- Consortium 3D for Humanities (Huma-Num; now CST3D HN) — life cycle of 3D data, from creation to
  archiving. *Life cycle of 3D data for cultural heritage*: https://hal.archives-ouvertes.fr/hal-01926434
- *Toward FAIR Data Practices with the French National 3D Data Repository* (2023): new metadata schema,
  aligned on the Europeana Data Model. https://hal-u-bordeaux-montaigne.archives-ouvertes.fr/hal-04115905v1
- Conservatoire National des Données 3D (CND3D): publication and curation of 3D models; **PLY and DAE**
  for archiving at the CINES; documentation of deposits with the **aLTAG3D** software.
  https://recherche.data.gouv.fr/en/repositories/conservatoire-national-des-donnees-3d-cnd3d-1

## Archiving formats

- CINES — selection of file formats for long-term preservation, and the FACILE validation tool.
  https://www.cines.fr/preservation/expertises/file-format/selection/
- HEG Genève (ArchiLab) — comparison of recommended formats: TIFF for digitised images, PNG for web
  content, SVG (without JavaScript) for vector images.
  https://www.hesge.ch/heg/sites/default/files/archilab/formats-fichiers-recommandes.pdf

## Metadata

- IPTC Photo Metadata Standard (IPTC Core and Extension), written as XMP. Model used by E. Charbonnel
  for the Shelby collection (to be offered as the default mapping of the batch renaming fields):

| IPTC Core field | Content |
|---|---|
| Title | title of the document |
| Creator | author |
| Description | description |
| Keywords | keywords |
| Date Created | date of the document |
| Domain (top geographic level) | geographic unit (Kuwait, Failaka…) |
| Country | zone or sector |
| State / Province | building |
| City | structure, wall |
| Sublocation | US / locus |
| Job Identifier | language (ENG, FRE, ARA) |
| Instructions | physical location (at the MoM) |
| Copyright Notice | copyright, constant value |

## Segmentation models

- MobileSAM (Zhang et al. 2023, *Faster Segment Anything*), MIT licence: https://github.com/ChaoningZhang/MobileSAM
- ONNX export used by Gerbil (Acly): https://huggingface.co/Acly/MobileSAM
- Segment Anything (Meta AI): https://github.com/facebookresearch/segment-anything

