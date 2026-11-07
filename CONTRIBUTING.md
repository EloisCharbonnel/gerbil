# Contributing to Gerbil

Gerbil is a free tool (GPL-3.0-or-later) for archaeologists who process photos of finds: cut-out at true
size, scales, naming and metadata, plates. Contributions are welcome: bug reports, photos that fail,
ideas, translations, code.

## Reporting a problem

Open an issue with: what you did, what you expected, what happened, the version (window title or
`py -3 gerbil.py --version`), and if you can the line of `outlined_report.csv` and the control preview
(`to_control`). **Never attach photos you have no right to share**: describe them, or share a photo whose
owner agrees.

## Principles (see `docs/ROADMAP.md`)

- The human eye decides: Gerbil prepares files, every result stays editable, every doubt is flagged.
- Zero setting by default; options for those who want them.
- Measurements are layout aids, never scientific data.
- **No regression**: a change must leave the results already right pixel-identical. Run the tests
  (`py -3 -m pytest tests`) and, if you have reference photos, compare the TIFF files before / after.
- Offline: nothing needs an internet connection (except downloading an AI model once).

## Code

- `gerbil.py`: engine and command line (scale, cut-out, PSD / TIFF, report, metadata).
- `gerbil_gui.pyw`: interface (tkinter); `gerbil_plates.py`: plates (SVG); `gerbil_tools.py`: inventory and
  thumbnails; `packaging/`: installer; `docs/PSEUDOCODE.txt` explains every step of the processing and
  `docs/CODE_GUIDE.md` the code itself (regenerate it with `py -3 docs/make_code_guide.py`: every function
  needs a docstring saying what it does).
- Python 3.10 or later; packages in `requirements.txt`. Code, messages and documents in English
  (interface translations welcome); comments explain *why*, in the style of the surrounding code.
- Tests: `tests/`, on synthetic photos made by `tests/synthetic.py` (the repository holds no real photo).
  Add a test with every fix or feature.

## Translations

The interface texts are being made translatable (French and English first). Other languages welcome.
