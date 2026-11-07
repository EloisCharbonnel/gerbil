"""Writes the guide to Gerbil as OpenDocument text (LibreOffice, Word): docs/Gerbil_guide_FR.odt and
docs/Gerbil_guide_EN.odt. Parts I to III are the texts of docs/fr/guide_fr.py and docs/guide_en.py; part IV
is made from the code itself, as CODE_GUIDE.md: every function and class with its explanation (French:
docs/fr/reference_fr*.py, English: its docstring) and its line. The figures are made once from the synthetic
photos of the tests (docs/guide_images). The ODT is written directly, a zip of XML files, without any
office library. Run again after a change: py -3 docs/make_guide_odt.py [fr] [en]"""
import ast
import datetime
import glob
import importlib.util
import os
import re
import shutil
import sys
import tempfile
import zipfile

DOCS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DOCS)
sys.path.insert(0, DOCS)
import make_code_guide as mcg           # noqa: E402  (files, sections, entries, docstring paragraphs)

FIG_DIR = os.path.join(DOCS, "guide_images")
TEXT_WIDTH_CM = 16.6                    # A4 minus the side margins
PURPLE, PURPLE2, LILAC = "#4B1F78", "#6A3BA0", "#8E5CC4"
PALE, PALER, LINE, INK, GREY = "#F1EAF9", "#FAF7FD", "#D9CCE8", "#2B2233", "#6E6478"
WARM, WARM_PALE = "#B5582F", "#FBEFE9"

NS = ('xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
      'xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0" '
      'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" '
      'xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" '
      'xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0" '
      'xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0" '
      'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" '
      'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" '
      'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0" office:version="1.2"')


def load_module(path):
    spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------------------------------------------------
# Figures (synthetic photos of the tests, processed by the engine)
# ----------------------------------------------------------------------------------------------------------

def make_figures():
    """fig_photo, fig_control, fig_dark in docs/guide_images: made once (delete them to make them again)."""
    want = {k: os.path.join(FIG_DIR, k + ".jpg") for k in ("fig_photo", "fig_control", "fig_dark")}
    if all(os.path.exists(p) for p in want.values()):
        return want
    sys.path[:0] = [ROOT, os.path.join(ROOT, "tests")]
    import gerbil
    import synthetic
    from PIL import Image
    os.makedirs(FIG_DIR, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for name, kw in (("sherd", {}), ("felt", {"dark": True, "label": True})):
            folder = os.path.join(tmp, name)
            os.makedirs(folder)
            rgb = synthetic.photo(px_cm=100.0, **kw)[0]
            Image.fromarray(rgb).save(os.path.join(folder, name + ".jpg"), quality=95)
            gerbil.main([folder, "-o", os.path.join(tmp, name + "_out"), "-j", "1", "--no-psd"])
            control = glob.glob(os.path.join(tmp, name + "_out", "to_control", name + "*.jpg"))[0]
            shutil.copy(control, want["fig_control" if name == "sherd" else "fig_dark"])
            if name == "sherd":
                im = Image.fromarray(rgb)
                im.thumbnail((1400, 1400))
                im.save(want["fig_photo"], quality=88)
    return want


# ----------------------------------------------------------------------------------------------------------
# Text: inline markup (**bold**, *italic*, `code`) and XML
# ----------------------------------------------------------------------------------------------------------

TOKEN = re.compile(r"`([^`]+)`|\*\*(.+?)\*\*|\*(.+?)\*")
SPAN_STYLES = {("b",): "Tb", ("i",): "Ti", ("c",): "Tc", ("b", "i"): "Tbi", ("b", "c"): "Tbc",
               ("c", "i"): "Tci", ("b", "c", "i"): "Tbci"}


def spans(text, styles=()):
    """[(styles, text)] of a text with **bold**, *italic* and `code` (\\* is a plain asterisk)."""
    out, pos = [], 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            out.append((styles, text[pos:m.start()]))
        if m.group(1) is not None:
            out.append((styles + ("c",), m.group(1)))
        elif m.group(2) is not None:
            out += spans(m.group(2), styles + ("b",))
        else:
            out += spans(m.group(3), styles + ("i",))
        pos = m.end()
    if pos < len(text):
        out.append((styles, text[pos:]))
    return out


def xml_text(s, keep_spaces=False):
    """Text for ODF XML: & < > escaped, runs of spaces and line breaks kept as ODF elements."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    lines = []
    for line in s.split("\n"):
        if keep_spaces:
            lead = len(line) - len(line.lstrip(" "))
            line = (f'<text:s text:c="{lead}"/>' if lead else "") + line[lead:]
        line = re.sub(r" {2,}", lambda m: f' <text:s text:c="{len(m.group()) - 1}"/>', line)
        lines.append(line.replace("\t", "<text:tab/>"))
    return "<text:line-break/>".join(lines)


def nbsp_fr(s):
    """French typography: no-break space before : ; ! ? and inside « »."""
    s = re.sub(r" ([:;!?»])", " \\1", s)
    return s.replace("« ", "« ")


class Writer:
    """Builds the body of the document: paragraphs, lists, tables, figures, headings (kept for the
    table of contents) and the images to embed."""

    def __init__(self, lang, labels, figures):
        self.lang, self.labels, self.figures = lang, labels, figures
        self.body, self.headings, self.images, self.n_tables = [], [], {}, 0

    # inline text
    def inline(self, text, markup=True):
        out = []
        for styles, s in (spans(text.replace("\\*", "\x00")) if markup else [((), text)]):
            s = s.replace("\x00", "*")
            if self.lang == "fr" and "c" not in styles:
                s = nbsp_fr(s)
            x = xml_text(s)
            name = SPAN_STYLES.get(tuple(sorted(styles)))
            out.append(f'<text:span text:style-name="{name}">{x}</text:span>' if name else x)
        return "".join(out)

    def p(self, style, text, markup=True):
        self.body.append(f'<text:p text:style-name="{style}">{self.inline(text, markup)}</text:p>')

    def heading(self, level, title):
        anchor = f"h{len(self.headings) + 1}"
        self.headings.append((level, title, anchor))
        self.body.append(f'<text:h text:style-name="H{level}" text:outline-level="{level}">'
                         f'<text:bookmark text:name="{anchor}"/>{self.inline(title, False)}</text:h>')

    def lst(self, items, numbered):
        rows = "".join(f'<text:list-item><text:p text:style-name="ListPara">{self.inline(t)}</text:p>'
                       f'</text:list-item>' for t in items)
        self.body.append(f'<text:list text:style-name="{"Lnum" if numbered else "Lbul"}" '
                         f'text:continue-numbering="false">{rows}</text:list>')

    def code(self, text):
        self.body.append(f'<text:p text:style-name="Code">{xml_text(text, keep_spaces=True)}</text:p>')

    def callout(self, kind, text):
        label = self.labels[kind]
        self.body.append(f'<text:p text:style-name="Box_{kind}"><text:span text:style-name="Tlabel_{kind}">'
                         f'{xml_text(label)} </text:span>{self.inline(text)}</text:p>')

    def table(self, rows, widths=None, code_first=False):
        """A table: first row = header (repeated on each page), body rows striped."""
        self.n_tables += 1
        name = f"Tab{self.n_tables}"
        n = len(rows[0])
        widths = widths or ([0.36, 0.64] if n == 2 else [1 / n] * n)
        self.auto_styles.append(f'<style:style style:name="{name}" style:family="table"><style:table-properties '
                                f'style:width="{TEXT_WIDTH_CM}cm" table:align="margins" fo:margin-top="0.15cm" '
                                f'fo:margin-bottom="0.3cm"/></style:style>')
        cols = ""
        for k, w in enumerate(widths):
            self.auto_styles.append(f'<style:style style:name="{name}.{k}" style:family="table-column">'
                                    f'<style:table-column-properties style:column-width="{TEXT_WIDTH_CM * w:.2f}cm"/>'
                                    f'</style:style>')
            cols += f'<table:table-column table:style-name="{name}.{k}"/>'

        def row(cells, head, alt):
            out = "<table:table-row>"
            for k, c in enumerate(cells):
                cell_style = "CellHead" if head else ("CellCode" if code_first and k == 0 else
                                                      ("CellAlt" if alt else "CellBody"))
                if head:
                    content = f'<text:p text:style-name="TableHead">{xml_text(c)}</text:p>'
                elif code_first and k == 0:
                    content = c                                 # already XML
                else:
                    content = f'<text:p text:style-name="TableText">{self.inline(c)}</text:p>'
                out += (f'<table:table-cell table:style-name="{cell_style}" office:value-type="string">'
                        f'{content}</table:table-cell>')
            return out + "</table:table-row>"

        body = "".join(row(r, False, i % 2 == 1) for i, r in enumerate(rows[1:]))
        self.body.append(f'<table:table table:name="{name}" table:style-name="{name}">{cols}'
                         f'<table:table-header-rows>{row(rows[0], True, False)}</table:table-header-rows>'
                         f'{body}</table:table>')

    def image(self, path, max_w=14.5, max_h=11.0, style="Figure"):
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
        scale = min(max_w / w, max_h / h)
        name = "Pictures/" + os.path.basename(path)
        self.images[name] = path
        self.body.append(f'<text:p text:style-name="{style}"><draw:frame draw:style-name="FrImg" '
                         f'draw:name="{os.path.basename(path)}" text:anchor-type="as-char" '
                         f'svg:width="{w * scale:.2f}cm" svg:height="{h * scale:.2f}cm" draw:z-index="0">'
                         f'<draw:image xlink:href="{name}" xlink:type="simple" xlink:show="embed" '
                         f'xlink:actuate="onLoad"/></draw:frame></text:p>')

    def figure(self, key, caption):
        path = self.figures.get(key)
        if path and os.path.exists(path):
            self.image(path)
            self.p("Caption", caption)

    def defs(self, items):
        for term, definition in items:
            self.p("DefTerm", term)
            self.p("DefBody", definition)

    def annotated(self, file, qualname, notes):
        """The source of a function, one row per line (the docstring as one row), with its explanation."""
        src = open(os.path.join(ROOT, file), encoding="utf-8").read()
        lines = src.split("\n")
        node = None
        scope = ast.parse(src).body
        for part in qualname.split("."):
            node = next(n for n in scope if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part)
            scope = node.body
        indent = len(lines[node.lineno - 1]) - len(lines[node.lineno - 1].lstrip())
        doc = node.body[0] if (isinstance(node.body[0], ast.Expr) and
                               isinstance(getattr(node.body[0], "value", None), ast.Constant)) else None
        groups, i = [], node.lineno
        while i <= node.end_lineno:
            if doc and i == doc.lineno:
                groups.append((i, lines[i - 1:doc.end_lineno]))
                i = doc.end_lineno + 1
                continue
            if lines[i - 1].strip():
                groups.append((i, [lines[i - 1]]))
            i += 1
        if len(groups) != len(notes):
            print(f"  warning: {file} {qualname}: {len(groups)} lines of code, {len(notes)} explanations")
        rows = [[self.labels["code_col"], self.labels["expl_col"]]]
        for k, (no, ls) in enumerate(groups):
            code = "\n".join(l[indent:] for l in ls)
            cell = (f'<text:p text:style-name="TableCode"><text:span text:style-name="Tlineno">{no}</text:span>'
                    f'<text:s text:c="2"/>{xml_text(code, keep_spaces=True)}</text:p>')
            rows.append([cell, notes[k] if k < len(notes) else ""])
        self.table(rows, [0.6, 0.4], code_first=True)

    def blocks(self, blocks):
        for b in blocks:
            kind = b[0]
            if kind in ("h1", "h2", "h3"):
                self.heading(int(kind[1]), b[1])
            elif kind == "p":
                self.p("Body", b[1])
            elif kind in ("ul", "ol"):
                self.lst(b[1], kind == "ol")
            elif kind == "code":
                self.code(b[1])
            elif kind in ("tip", "warn", "note"):
                self.callout(kind, b[1])
            elif kind == "table":
                self.table(b[1])
            elif kind == "figure":
                self.figure(b[1], b[2])
            elif kind == "defs":
                self.defs(b[1])
            elif kind == "annotated":
                self.annotated(b[1], b[2], b[3])
            elif kind == "pagebreak":
                pass                                            # a part (H1) always starts a new page


# ----------------------------------------------------------------------------------------------------------
# Part IV: reference made from the code
# ----------------------------------------------------------------------------------------------------------

def doc_text(doc):
    """A docstring as one text: its paragraphs joined, list lines kept on their own line."""
    return mcg.para(doc).replace("\n\n", "\n").replace("\n    ", "\n").strip()


def reference(w, guide, fr):
    lab = w.labels
    w.heading(1, lab["part4"])
    w.p("Body", lab["part4_intro"])
    w.callout("note", lab["generated"])
    for f, role_en in mcg.FILES:
        path = os.path.join(ROOT, f)
        if not os.path.exists(path):
            continue
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
        n_lines = src.count("\n") + 1
        w.heading(2, f)
        w.p("FileRole", f"{guide.FILE_ROLES.get(f, role_en)} ({n_lines} {lab['lines']})")
        head = describe(f, "__module__", ast.get_docstring(tree) or "", fr, lab, module=True)
        if head:
            w.body.append(f'<text:p text:style-name="Body">{head}</text:p>')
        secs = mcg.sections(src) or [(1, "")]
        items = mcg.entries(tree)
        bounds = [s[0] for s in secs] + [n_lines + 1]
        for k, (line0, title) in enumerate(secs):
            inside = [e for e in items if (e[0] < bounds[1] if k == 0 else bounds[k] <= e[0] < bounds[k + 1])]
            if not inside:
                continue
            if title:
                w.heading(3, guide.SECTION_TITLES.get(title, title))
            for line, kind, name, sig, doc, depth in inside:
                m = "M" if depth else ""
                w.body.append(f'<text:p text:style-name="RefSig{m}"><text:span text:style-name="Tsig">'
                              f'{xml_text(sig)}</text:span><text:span text:style-name="Tmeta"> {lab[kind]}, '
                              f'{lab["line"]} {line}</text:span></text:p>')
                w.body.append(f'<text:p text:style-name="RefBody{m}">{describe(f, name, doc, fr, lab)}</text:p>')


def describe(f, name, doc, fr, lab, module=False):
    """XML of the explanation of an entry: French text when there is one, else the docstring (flagged as
    untranslated in the French guide)."""
    if fr is not None and f"{f}:{name}" in fr:
        return xml_text(nbsp_fr(fr[f"{f}:{name}"]))
    if not doc:
        return "" if module else xml_text(lab["helper"])
    text = doc_text(doc)
    if module:                                                  # the licence lines are on the title page
        text = "\n".join(l for l in text.split("\n") if not re.match(r"(©|Licence|This program|redistribute)", l))
    out = xml_text(text)
    if fr is not None:
        out += f' <text:span text:style-name="Tmeta">{xml_text(lab["untranslated"])}</text:span>'
    return out


# ----------------------------------------------------------------------------------------------------------
# Styles
# ----------------------------------------------------------------------------------------------------------

def pstyle(name, para="", text="", parent="Standard", extra="", display=None):
    disp = f' style:display-name="{display}"' if display else ""
    return (f'<style:style style:name="{name}"{disp} style:family="paragraph" style:parent-style-name="{parent}"'
            f'{extra}><style:paragraph-properties {para}/><style:text-properties {text}/></style:style>')


def tstyle(name, text):
    return f'<style:style style:name="{name}" style:family="text"><style:text-properties {text}/></style:style>'


def cstyle(name, bg, left=None):
    border = f"0.5pt solid {LINE}"
    return (f'<style:style style:name="{name}" style:family="table-cell"><style:table-cell-properties '
            f'fo:background-color="{bg}" fo:padding-left="0.16cm" fo:padding-right="0.16cm" '
            f'fo:padding-top="0.09cm" fo:padding-bottom="0.09cm" fo:border-left="{left or border}" '
            f'fo:border-right="{border}" fo:border-top="{border}" fo:border-bottom="{border}"/></style:style>')


FONTS = ('<office:font-face-decls>'
         '<style:font-face style:name="Georgia" svg:font-family="Georgia" style:font-family-generic="roman"/>'
         '<style:font-face style:name="Segoe UI" svg:font-family="&apos;Segoe UI&apos;" '
         'style:font-family-generic="swiss"/>'
         '<style:font-face style:name="Segoe UI Semibold" svg:font-family="&apos;Segoe UI Semibold&apos;" '
         'style:font-family-generic="swiss"/>'
         '<style:font-face style:name="Consolas" svg:font-family="Consolas" style:font-family-generic="modern" '
         'style:font-pitch="fixed"/></office:font-face-decls>')

SERIF = 'style:font-name="Georgia"'
SANS = 'style:font-name="Segoe UI"'
MONO = 'style:font-name="Consolas"'


def styles_xml(lang, footer_text):
    language = 'fo:language="fr" fo:country="FR"' if lang == "fr" else 'fo:language="en" fo:country="GB"'
    keep = 'fo:keep-with-next="always"'
    s = [
        f'<style:default-style style:family="paragraph"><style:paragraph-properties style:writing-mode="lr-tb" '
        f'style:tab-stop-distance="1.25cm"/><style:text-properties {SANS} fo:font-size="10.5pt" {language} '
        f'fo:color="{INK}" fo:hyphenate="false"/></style:default-style>',
        pstyle("Standard", "", "", parent="", display="Standard").replace(' style:parent-style-name=""', ""),
        pstyle("Body", 'fo:margin-top="0cm" fo:margin-bottom="0.22cm" fo:line-height="132%"', "",
               display="Gerbil body"),
        pstyle("H1", f'fo:margin-top="0cm" fo:margin-bottom="0.5cm" fo:padding-bottom="0.18cm" '
                     f'fo:border-bottom="2.2pt solid {LILAC}" fo:break-before="page" {keep}',
               f'{SERIF} fo:font-size="24pt" fo:color="{PURPLE}"',
               extra=' style:default-outline-level="1"', display="Gerbil heading 1"),
        pstyle("H2", f'fo:margin-top="0.55cm" fo:margin-bottom="0.22cm" {keep}',
               f'{SERIF} fo:font-size="15.5pt" fo:color="{PURPLE2}"', extra=' style:default-outline-level="2"',
               display="Gerbil heading 2"),
        pstyle("H3", f'fo:margin-top="0.38cm" fo:margin-bottom="0.14cm" {keep}',
               f'style:font-name="Segoe UI Semibold" fo:font-size="11.5pt" fo:color="{LILAC}"',
               extra=' style:default-outline-level="3"', display="Gerbil heading 3"),
        pstyle("ListPara", 'fo:margin-top="0cm" fo:margin-bottom="0.12cm" fo:line-height="128%"', "",
               display="Gerbil list"),
        pstyle("Code", f'fo:margin-top="0.1cm" fo:margin-bottom="0.3cm" fo:margin-left="0.2cm" '
                       f'fo:background-color="{PALE}" fo:padding="0.22cm" fo:border-left="3pt solid {LILAC}" '
                       f'fo:border-right="none" fo:border-top="none" fo:border-bottom="none"',
               f'{MONO} fo:font-size="8.8pt" fo:color="{PURPLE}"', display="Gerbil code"),
        pstyle("Figure", 'fo:text-align="center" fo:margin-top="0.25cm" fo:margin-bottom="0.08cm" '
                         'fo:keep-with-next="always"', "", display="Gerbil figure"),
        pstyle("Caption", 'fo:text-align="center" fo:margin-bottom="0.4cm" fo:margin-left="1cm" '
                          'fo:margin-right="1cm"', f'fo:font-size="9pt" fo:font-style="italic" fo:color="{GREY}"',
               display="Gerbil caption"),
        pstyle("DefTerm", f'fo:margin-top="0.16cm" fo:margin-bottom="0.03cm" {keep}',
               f'fo:font-weight="bold" fo:color="{PURPLE2}"', display="Gerbil term"),
        pstyle("DefBody", 'fo:margin-left="0.7cm" fo:margin-bottom="0.12cm" fo:line-height="128%"', "",
               display="Gerbil definition"),
        pstyle("TableHead", "", 'fo:font-size="9.5pt" fo:font-weight="bold" fo:color="#FFFFFF"',
               display="Gerbil table heading"),
        pstyle("TableText", 'fo:line-height="122%"', 'fo:font-size="9.5pt"', display="Gerbil table text"),
        pstyle("TableCode", 'fo:line-height="118%"', f'{MONO} fo:font-size="8.3pt" fo:color="{PURPLE}"',
               display="Gerbil table code"),
        pstyle("FileRole", 'fo:margin-bottom="0.2cm"', f'fo:font-style="italic" fo:color="{GREY}"',
               display="Gerbil file role"),
        pstyle("RefSig", f'fo:margin-top="0.2cm" fo:margin-bottom="0.02cm" {keep}', "",
               display="Gerbil reference name"),
        pstyle("RefBody", 'fo:margin-left="0.55cm" fo:margin-bottom="0.08cm" fo:line-height="125%"',
               'fo:font-size="9.8pt"', display="Gerbil reference text"),
        pstyle("RefSigM", f'fo:margin-left="0.75cm" fo:margin-top="0.12cm" fo:margin-bottom="0.02cm" {keep}', "",
               display="Gerbil reference method"),
        pstyle("RefBodyM", 'fo:margin-left="1.3cm" fo:margin-bottom="0.06cm" fo:line-height="125%"',
               'fo:font-size="9.6pt"', display="Gerbil reference method text"),
        pstyle("TocTitle", f'fo:margin-bottom="0.3cm" fo:padding-bottom="0.15cm" '
                           f'fo:border-bottom="2.2pt solid {LILAC}"',
               f'{SERIF} fo:font-size="24pt" fo:color="{PURPLE}"', display="Gerbil contents title"),
        pstyle("TOC1", 'fo:margin-top="0.13cm" fo:margin-bottom="0.02cm"',
               f'fo:font-weight="bold" fo:color="{PURPLE}" fo:font-size="11pt"', display="Gerbil contents 1"),
        pstyle("TOC2", 'fo:margin-left="0.6cm" fo:margin-bottom="0cm" fo:line-height="112%"', 'fo:font-size="9.4pt"',
               display="Gerbil contents 2"),
        pstyle("Footer", f'fo:border-top="0.6pt solid {LINE}" fo:padding-top="0.12cm"',
               f'fo:font-size="8.5pt" fo:color="{GREY}"', display="Gerbil footer"),
        pstyle("CoverTitle", 'fo:text-align="center" fo:margin-top="1.2cm" fo:margin-bottom="0.2cm"',
               f'{SERIF} fo:font-size="54pt" fo:color="{PURPLE}"',
               display="Gerbil cover title"),
        pstyle("CoverSub", 'fo:text-align="center" fo:margin-bottom="0.5cm"',
               f'{SERIF} fo:font-size="21pt" fo:color="{PURPLE2}"', display="Gerbil cover subtitle"),
        pstyle("CoverTag", 'fo:text-align="center" fo:margin-left="1.5cm" fo:margin-right="1.5cm" '
                           'fo:margin-bottom="1.2cm"', f'fo:font-size="12pt" fo:font-style="italic" fo:color="{GREY}"',
               display="Gerbil cover tagline"),
        pstyle("PageBreak", 'fo:break-before="page"', "", display="Gerbil page break"),
        pstyle("CoverImg", 'fo:text-align="center" fo:margin-top="1.4cm" fo:margin-bottom="1.4cm"', "",
               display="Gerbil cover picture"),
        pstyle("CoverBand", f'fo:text-align="center" fo:background-color="{PURPLE}" fo:padding="0.35cm" '
                            f'fo:margin-top="1cm"', 'fo:font-size="10.5pt" fo:color="#FFFFFF"',
               display="Gerbil cover band"),
        pstyle("CoverSmall", 'fo:text-align="center" fo:margin-top="0.2cm"', f'fo:font-size="9pt" fo:color="{GREY}"',
               display="Gerbil cover small"),
    ]
    for kind, colour, bg in (("tip", LILAC, PALE), ("note", PURPLE2, PALER), ("warn", WARM, WARM_PALE)):
        s.append(pstyle(f"Box_{kind}", f'fo:margin-top="0.15cm" fo:margin-bottom="0.32cm" fo:margin-left="0.2cm" '
                                       f'fo:background-color="{bg}" fo:padding="0.25cm" '
                                       f'fo:border-left="3.5pt solid {colour}" fo:border-right="none" '
                                       f'fo:border-top="none" fo:border-bottom="none" fo:line-height="128%"', "",
                        display=f"Gerbil box {kind}"))
        s.append(tstyle(f"Tlabel_{kind}", f'fo:font-weight="bold" fo:color="{colour}"'))
    s += [tstyle("Tb", f'fo:font-weight="bold" fo:color="{PURPLE}"'), tstyle("Ti", 'fo:font-style="italic"'),
          tstyle("Tbi", f'fo:font-weight="bold" fo:font-style="italic" fo:color="{PURPLE}"')]
    for name, extra in (("Tc", ""), ("Tbc", ' fo:font-weight="bold"'), ("Tci", ' fo:font-style="italic"'),
                        ("Tbci", ' fo:font-weight="bold" fo:font-style="italic"')):
        s.append(tstyle(name, f'{MONO} fo:font-size="9.2pt" fo:color="{PURPLE}" fo:background-color="{PALE}"{extra}'))
    s += [tstyle("Tsig", f'{MONO} fo:font-size="9.6pt" fo:font-weight="bold" fo:color="{PURPLE}"'),
          tstyle("Tmeta", f'fo:font-size="8.5pt" fo:color="{GREY}" fo:font-style="italic"'),
          tstyle("Tlineno", f'{MONO} fo:font-size="7.5pt" fo:color="{GREY}"'),
          tstyle("Tbullet", f'fo:color="{LILAC}" fo:font-weight="bold"')]
    lists = (
        '<text:list-style style:name="Lbul">' +
        "".join(f'<text:list-level-style-bullet text:level="{lv}" text:style-name="Tbullet" '
                f'text:bullet-char="{"•" if lv == 1 else "–"}"><style:list-level-properties '
                f'text:list-level-position-and-space-mode="label-alignment"><style:list-level-label-alignment '
                f'text:label-followed-by="listtab" text:list-tab-stop-position="{0.35 + 0.6 * lv:.2f}cm" '
                f'fo:text-indent="-0.45cm" fo:margin-left="{0.35 + 0.6 * lv:.2f}cm"/></style:list-level-properties>'
                f'</text:list-level-style-bullet>' for lv in (1, 2)) +
        '</text:list-style><text:list-style style:name="Lnum">' +
        "".join(f'<text:list-level-style-number text:level="{lv}" text:style-name="Tbullet" style:num-format="1" '
                f'style:num-suffix="."><style:list-level-properties '
                f'text:list-level-position-and-space-mode="label-alignment"><style:list-level-label-alignment '
                f'text:label-followed-by="listtab" text:list-tab-stop-position="{0.45 + 0.6 * lv:.2f}cm" '
                f'fo:text-indent="-0.55cm" fo:margin-left="{0.45 + 0.6 * lv:.2f}cm"/></style:list-level-properties>'
                f'</text:list-level-style-number>' for lv in (1, 2)) +
        '</text:list-style>')
    page = ('<style:page-layout style:name="PL"><style:page-layout-properties fo:page-width="21cm" '
            'fo:page-height="29.7cm" style:print-orientation="portrait" fo:margin-top="1.9cm" '
            'fo:margin-bottom="1.4cm" fo:margin-left="2.2cm" fo:margin-right="2.2cm"/>'
            '<style:footer-style><style:header-footer-properties fo:min-height="0.9cm" fo:margin-top="0.4cm"/>'
            '</style:footer-style></style:page-layout>')
    masters = ('<style:master-page style:name="Standard" style:page-layout-name="PL"><style:footer>'
               '<text:p text:style-name="FooterP">' + xml_text(footer_text) +
               '<text:tab/><text:page-number text:select-page="current">1</text:page-number></text:p>'
               '</style:footer></style:master-page>')
    footer_p = (f'<style:style style:name="FooterP" style:family="paragraph" style:parent-style-name="Footer">'
                f'<style:paragraph-properties><style:tab-stops><style:tab-stop style:position="{TEXT_WIDTH_CM}cm" '
                f'style:type="right"/></style:tab-stops></style:paragraph-properties></style:style>')
    frame = ('<style:style style:name="FrImg" style:family="graphic"><style:graphic-properties '
             'style:vertical-pos="top" style:vertical-rel="baseline" fo:border="none" fo:padding="0cm"/>'
             '</style:style>')
    return (f'<?xml version="1.0" encoding="UTF-8"?><office:document-styles {NS}>{FONTS}<office:styles>'
            + "".join(s) + footer_p + lists + frame + '</office:styles><office:automatic-styles>' + page +
            f'</office:automatic-styles><office:master-styles>{masters}</office:master-styles>'
            '</office:document-styles>')


# ----------------------------------------------------------------------------------------------------------
# Document
# ----------------------------------------------------------------------------------------------------------

def build(lang):
    if lang == "fr":
        guide = load_module(os.path.join(DOCS, "fr", "guide_fr.py"))
        fr = {**load_module(os.path.join(DOCS, "fr", "reference_fr.py")).FR,
              **load_module(os.path.join(DOCS, "fr", "reference_fr_more.py")).FR}
    else:
        guide = load_module(os.path.join(DOCS, "guide_en.py"))
        fr = None
    lab = guide.LABELS
    version = re.search(r'^VERSION = "([^"]+)"', open(os.path.join(ROOT, "gerbil.py"), encoding="utf-8").read(),
                        re.M).group(1)
    today = datetime.date.today()
    w = Writer(lang, lab, make_figures())
    w.auto_styles = [cstyle("CellHead", PURPLE), cstyle("CellBody", "#FFFFFF"), cstyle("CellAlt", PALER),
                     cstyle("CellCode", PALE, left=f"2.5pt solid {LILAC}")]     # used by content.xml: kept there

    w.blocks([("h1", lab["foreword"])] + guide.FOREWORD)
    w.blocks(guide.PARTS)
    reference(w, guide, fr)

    # cover and table of contents, written before the body
    cover = Writer(lang, lab, {})
    cover.auto_styles = w.auto_styles
    cover.p("CoverTitle", guide.TITLE)
    cover.p("CoverSub", guide.SUBTITLE)
    cover.p("CoverTag", guide.TAGLINE)
    icon = os.path.join(ROOT, "icons", "gerbil_128.png")
    if os.path.exists(icon):
        cover.image(icon, 4.2, 4.2, "CoverImg")
    cover.p("CoverBand", f"Gerbil {version}  ·  © {today.year} Eloïs CHARBONNEL  ·  {lab['licence']}", False)
    cover.p("CoverSmall", f"{lab['date']} {today.isoformat()}  ·  github.com/EloisCharbonnel/gerbil", False)
    part4 = next(k for k, h in enumerate(w.headings) if h[1] == lab["part4"])  # its files: not in the contents
    toc_entries = "".join(
        f'<text:p text:style-name="TOC{lv}"><text:a xlink:type="simple" xlink:href="#{a}">'
        f'{xml_text(nbsp_fr(t) if lang == "fr" else t)}</text:a></text:p>'
        for k, (lv, t, a) in enumerate(w.headings) if lv == 1 or lv == 2 and k < part4)
    tmpl = "".join(f'<text:table-of-content-entry-template text:outline-level="{lv}" text:style-name="TOC{lv}">'
                   '<text:index-entry-link-start/><text:index-entry-text/><text:index-entry-tab-stop '
                   'style:type="right" style:leader-char="."/><text:index-entry-page-number/>'
                   '<text:index-entry-link-end/></text:table-of-content-entry-template>' for lv in (1, 2))
    toc = (f'<text:table-of-content text:name="Contents" text:protected="false"><text:table-of-content-source '
           f'text:outline-level="2" text:use-index-marks="false"><text:index-title-template '
           f'text:style-name="TocTitle">{xml_text(lab["contents"])}</text:index-title-template>{tmpl}'
           f'</text:table-of-content-source><text:index-body><text:index-title text:name="ContentsTitle">'
           f'<text:p text:style-name="TocTitle">{xml_text(lab["contents"])}</text:p></text:index-title>'
           f'{toc_entries}</text:index-body></text:table-of-content>')

    content = (f'<?xml version="1.0" encoding="UTF-8"?><office:document-content {NS}>{FONTS}'
               f'<office:automatic-styles>{"".join(w.auto_styles)}</office:automatic-styles><office:body>'
               f'<office:text>{"".join(cover.body)}<text:p text:style-name="PageBreak"/>{toc}{"".join(w.body)}'
               f'</office:text></office:body>'
               f'</office:document-content>')
    meta = (f'<?xml version="1.0" encoding="UTF-8"?><office:document-meta {NS}><office:meta>'
            f'<dc:title>{xml_text(guide.TITLE + " — " + guide.SUBTITLE)}</dc:title>'
            f'<dc:creator>Eloïs CHARBONNEL</dc:creator><dc:language>{lang}</dc:language>'
            f'<meta:generator>Gerbil docs/make_guide_odt.py</meta:generator>'
            f'<dc:date>{datetime.datetime.now().replace(microsecond=0).isoformat()}</dc:date>'
            f'</office:meta></office:document-meta>')
    images = {**cover.images, **w.images}
    manifest = ('<?xml version="1.0" encoding="UTF-8"?><manifest:manifest '
                'xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">'
                '<manifest:file-entry manifest:full-path="/" manifest:version="1.2" '
                'manifest:media-type="application/vnd.oasis.opendocument.text"/>' +
                "".join(f'<manifest:file-entry manifest:full-path="{n}" manifest:media-type="text/xml"/>'
                        for n in ("content.xml", "styles.xml", "meta.xml")) +
                "".join(f'<manifest:file-entry manifest:full-path="{n}" manifest:media-type="image/'
                        f'{"png" if n.endswith(".png") else "jpeg"}"/>' for n in images) +
                '</manifest:manifest>')
    out = os.path.join(DOCS, f"Gerbil_guide_{lang.upper()}.odt")
    tmp = out + ".tmp"
    with zipfile.ZipFile(tmp, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/vnd.oasis.opendocument.text")   # first, stored
        for name, data in (("content.xml", content), ("styles.xml", styles_xml(lang, guide.FOOTER)),
                           ("meta.xml", meta), ("META-INF/manifest.xml", manifest)):
            z.writestr(name, data.encode("utf-8"), compress_type=zipfile.ZIP_DEFLATED)
        for name, path in images.items():
            z.write(path, name, compress_type=zipfile.ZIP_STORED)
    os.replace(tmp, out)
    n_ref = sum(1 for b in w.body if 'text:style-name="RefSig' in b)
    print(f"{os.path.relpath(out, ROOT)}: {len(w.headings)} headings, {n_ref} functions and classes, "
          f"{os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    for language in (sys.argv[1:] or ["fr", "en"]):
        build(language)
