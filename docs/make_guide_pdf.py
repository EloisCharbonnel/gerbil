"""Writes the guides to Gerbil as PDF, in French and English:

- docs/Gerbil_guide_FR.pdf, docs/Gerbil_guide_EN.pdf: the user guide (USER blocks of docs/fr/guide_fr.py and
  docs/guide_en.py), with the screenshots of docs/guide_images (made by docs/make_guide_shots.py);
- docs/Gerbil_code_guide_FR.pdf, docs/Gerbil_code_guide_EN.pdf: the guide to the code (CODE blocks), then
  the reference made from the code itself, as CODE_GUIDE.md: every function and class with its explanation
  (French: docs/fr/reference_fr*.py, English: its docstring) and its line.

Each guide is written as one HTML page (the fonts of Gerbil, the green of its interface, grey squared paper)
and printed to PDF by Microsoft Edge or Google Chrome, without a window: clickable contents and cross
references, PDF bookmarks. When pypdfium2 can be imported (or is found in the folder given by the variable
GERBIL_PDFIUM), the contents also get their page numbers (a first print gives the pages).

Run again after a change: py -3 docs/make_guide_pdf.py [fr] [en] [user] [code] [--html]"""
import ast
import datetime
import glob
import html
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

DOCS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DOCS)
sys.path.insert(0, DOCS)
import make_code_guide as mcg           # noqa: E402  (files, sections, entries, docstring paragraphs)

IMAGES = os.path.join(DOCS, "guide_images")
FONTS = os.path.join(ROOT, "fonts")

# the green of the interface (gerbil_gui.pyw, theme green light)
INK, INK_2, TINT, TINT_2, TINT_PALE = "#1E4230", "#3B7656", "#D2E7D8", "#B6D6BE", "#EEF6F0"
SAGE, TEAL, TERRA, TERRA_PALE = "#ABD6B4", "#215353", "#B5582F", "#FBEFE9"
TEXT, MUTED, PAPER, GRID, LINE = "#1F1D24", "#5E5A66", "#F3F3F4", "#E3E6E3", "#CFD9D2"


def load_module(path):
    spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def version():
    src = open(os.path.join(ROOT, "gerbil.py"), encoding="utf-8").read()
    return re.search(r'^VERSION = "([^"]+)"', src, re.M).group(1)


def slug(text):
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-") or "s"


def file_url(path):
    return "file:///" + os.path.abspath(path).replace("\\", "/")


# ----------------------------------------------------------------------------------------------------------
# Inline text: **bold**, *italic*, `code`, [[anchor]] or [[anchor|text]] (link), {{Ctrl+Z}} (keys),
# <https://…> (web link); \* is a plain asterisk
# ----------------------------------------------------------------------------------------------------------

TOKEN = re.compile(r"`([^`]+)`|\*\*(.+?)\*\*|\*(.+?)\*|\[\[([^\]|]+)(?:\|([^\]]+))?\]\]|\{\{([^}]+)\}\}"
                   r"|<(https?://[^>\s]+)>")


def french(s):
    """French typography: no-break space before : ; ! ? and inside « »."""
    s = re.sub(r" ([:;!?»])", " \\1", s)
    return s.replace("« ", "« ")


class Doc:
    """One guide: its HTML body, its headings (contents, bookmarks) and its cross references."""

    def __init__(self, lang, labels):
        self.lang, self.lab = lang, labels
        self.out = []
        self.heads = []                 # (level, number, title, anchor)
        self.titles = {}                # anchor -> title (for [[anchor]] without a text)
        self.links = set()


    # ---- inline
    def text(self, s):
        s = html.escape(s, quote=False)
        return french(s) if self.lang == "fr" else s

    def inline(self, s):
        s = s.replace("\\*", "\x00")
        out, pos = [], 0
        for m in TOKEN.finditer(s):
            out.append(self.text(s[pos:m.start()]))
            code, bold, ital, anchor, label, keys, url = m.groups()
            if code is not None:
                out.append(f"<code>{html.escape(code)}</code>")
            elif bold is not None:
                out.append(f"<strong>{self.inline(bold)}</strong>")
            elif ital is not None:
                out.append(f"<em>{self.inline(ital)}</em>")
            elif anchor is not None:
                self.links.add(anchor)
                body = self.inline(label) if label else f"\x01{anchor}\x02"
                out.append(f'<a class="xref" href="#{anchor}">{body}</a>')
            elif keys is not None:
                out.append("<span class=keys>" + "+".join(f"<kbd>{html.escape(k.strip())}</kbd>"
                                                          for k in keys.split("+")) + "</span>")
            else:
                out.append(f'<a class="web" href="{html.escape(url)}">{html.escape(url)}</a>')
            pos = m.end()
        out.append(self.text(s[pos:]))
        return "".join(out).replace("\x00", "*")

    # ---- blocks
    def heading(self, level, title, anchor=None, number=None):
        anchor = anchor or slug(title)
        base, k = anchor, 2
        while anchor in self.titles:
            anchor, k = f"{base}-{k}", k + 1
        self.titles[anchor] = title
        self.heads.append((level, number, title, anchor))
        num = f'<span class="num">{html.escape(number)}</span>' if number else ""
        self.out.append(f'<h{level} id="{anchor}">{num}<span class="t">{self.inline(title)}</span></h{level}>')
        return anchor

    def part(self, number, title, intro, anchor, sections):
        """A part opens on a new page: its number, its title, a few words and the list of its sections."""
        self.out.append(f'<section class="part"><div class="band"><span class="big">{html.escape(number)}</span>')
        self.heading(1, title, anchor, number)
        if intro:
            self.out.append(f'<p class="lead">{self.inline(intro)}</p>')
        self.out.append("</div>")
        if sections:
            self.out.append(f'<div class="intoc">{self.text(self.lab["in_part"])}</div><ol class="minitoc">' +
                            "".join(f'<li><span class="k">{k:02d}</span><a href="#{a}">{self.inline(t)}</a></li>'
                                    for k, (t, a) in enumerate(sections, 1)) + "</ol>")
        self.out.append("</section>")

    def table(self, rows, widths=None, cls=""):
        cols = "".join(f'<col style="width:{w * 100:.0f}%">' for w in widths) if widths else ""
        head = "".join(f"<th>{self.inline(c)}</th>" for c in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{self.inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
        self.out.append(f'<table class="{cls}"><colgroup>{cols}</colgroup><thead><tr>{head}</tr></thead>'
                        f"<tbody>{body}</tbody></table>")

    def image(self, path, caption, cls="figure"):
        if not os.path.exists(path):
            print("  missing picture:", os.path.relpath(path, ROOT))
            return
        cap = f"<figcaption>{self.inline(caption)}</figcaption>" if caption else ""
        self.out.append(f'<figure class="{cls}"><img src="{file_url(path)}" alt="">{cap}</figure>')

    def annotated(self, file, qualname, notes):
        """The source of a function, one row per line (the docstring as one row), with its explanation."""
        src = open(os.path.join(ROOT, file), encoding="utf-8").read()
        lines = src.split("\n")
        scope, node = ast.parse(src).body, None
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
        rows = []
        for k, (no, ls) in enumerate(groups):
            code = html.escape("\n".join(l[indent:] for l in ls))
            note = self.inline(notes[k]) if k < len(notes) else ""
            rows.append(f'<tr><td class="ln">{no}</td><td class="src"><pre>{code}</pre></td><td>{note}</td></tr>')
        self.out.append(f'<table class="annotated"><colgroup><col style="width:5%"><col style="width:55%">'
                        f'<col style="width:40%"></colgroup><thead><tr><th></th><th>{self.lab["code_col"]}</th>'
                        f'<th>{self.lab["expl_col"]}</th></tr></thead><tbody>{"".join(rows)}</tbody></table>')

    def blocks(self, blocks, sections_of):
        for b in blocks:
            kind = b[0]
            if kind == "part":
                _, number, title, intro, anchor = b
                self.part(number, title, intro, anchor, sections_of.get(anchor, []))
            elif kind in ("h2", "h3"):
                self.heading(int(kind[1]), b[1], b[2] if len(b) > 2 else None)
            elif kind == "p":
                self.out.append(f"<p>{self.inline(b[1])}</p>")
            elif kind == "lead":
                self.out.append(f'<p class="lead">{self.inline(b[1])}</p>')
            elif kind in ("ul", "ol"):
                items = "".join(f"<li>{self.inline(t)}</li>" for t in b[1])
                self.out.append(f"<{kind}>{items}</{kind}>")
            elif kind == "code":
                longest = max(len(line) for line in b[1].splitlines())
                size = f' style="font-size:{8.4 * 92 / longest:.2f}pt;white-space:pre"' if longest > 92 else ""
                self.out.append(f"<pre class=code{size}>{html.escape(b[1])}</pre>")
            elif kind in ("tip", "warn", "note", "key"):
                self.out.append(f'<div class="box {kind}"><span class="label">{self.lab[kind]}</span>'
                                f"{self.inline(b[1])}</div>")
            elif kind == "quote":
                self.out.append(f'<blockquote>{self.inline(b[1])}</blockquote>')
            elif kind == "table":
                self.table(b[1], b[2] if len(b) > 2 else None)
            elif kind == "figure":
                self.image(os.path.join(IMAGES, b[1] + ".jpg"), b[2], "figure small")
            elif kind == "shot":
                cls = "figure shot" + (" " + b[3] if len(b) > 3 else "")
                self.image(os.path.join(IMAGES, f"ui_{self.lang}_{b[1]}.jpg"), b[2], cls)
            elif kind == "defs":
                cls = ' class="two"' if len(b[1]) > 12 else ""
                self.out.append(f"<dl{cls}>" + "".join(f"<dt>{self.inline(t)}</dt><dd>{self.inline(d)}</dd>"
                                                 for t, d in b[1]) + "</dl>")
            elif kind == "flow":
                # the work from A to Z: one card per step, with its number, its result and a link
                cards = "".join(
                    f'<a class="stepcard" href="#{a}"><span class="n">{html.escape(n)}</span>'
                    f'<span class="st">{self.inline(t)}</span><span class="sd">{self.inline(d)}</span></a>'
                    for n, t, d, a in b[1])
                self.out.append(f'<div class="flow">{cards}</div>')
                for *_, a in b[1]:
                    self.links.add(a)
            elif kind == "cards":
                # "I want to…": a question, the answer in a few words, a link
                cards = "".join(f'<a class="want" href="#{a}"><span class="q">{self.inline(q)}</span>'
                                f'<span class="r">{self.inline(r)}</span></a>' for q, r, a in b[1])
                self.out.append(f'<div class="wants">{cards}</div>')
                for *_, a in b[1]:
                    self.links.add(a)
            elif kind == "annotated":
                self.annotated(b[1], b[2], b[3])
            elif kind == "pagebreak":
                self.out.append('<div class="pagebreak"></div>')
            elif kind == "raw":
                self.out.append(b[1])
            else:
                raise ValueError(f"unknown block {kind}")

    def resolve(self):
        body = "".join(self.out)
        missing = sorted(a for a in self.links if a not in self.titles)
        if missing:
            print("  links without a target:", ", ".join(missing))
        return re.sub("\x01([^\x02]+)\x02", lambda m: self.inline(self.titles.get(m.group(1), m.group(1))), body)


def sections_of(blocks):
    """{part anchor: [(title, anchor) of its h2]} — the anchors are made as Doc.heading makes them."""
    out, current, seen = {}, None, set()
    for b in blocks:
        if b[0] in ("part", "h2", "h3"):
            title = b[2] if b[0] == "part" else b[1]
            anchor = b[4] if b[0] == "part" else (b[2] if len(b) > 2 else None)
            anchor = anchor or slug(title)
            base, k = anchor, 2
            while anchor in seen:
                anchor, k = f"{base}-{k}", k + 1
            seen.add(anchor)
            if b[0] == "part":
                current = anchor
                out[current] = []
            elif b[0] == "h2" and current:
                out[current].append((title, anchor))
    return out


# ----------------------------------------------------------------------------------------------------------
# Reference made from the code (code guide)
# ----------------------------------------------------------------------------------------------------------

def reference(d, guide, fr, number):
    lab = d.lab
    files = [(f, role) for f, role in mcg.FILES if os.path.exists(os.path.join(ROOT, f))]
    d.part(number, lab["ref_title"], lab["ref_intro"], "reference",
           [(f, "ref-" + slug(f)) for f, _ in files])
    d.out.append(f'<div class="box note"><span class="label">{lab["note"]}</span>{d.inline(lab["generated"])}</div>')
    for f, role_en in files:
        src = open(os.path.join(ROOT, f), encoding="utf-8").read()
        tree = ast.parse(src)
        n_lines = src.count("\n") + 1
        d.heading(2, f, "ref-" + slug(f))
        d.out.append(f'<p class="filerole">{d.inline(guide.FILE_ROLES.get(f, role_en))} '
                     f'({n_lines} {lab["lines"]})</p>')
        head = describe(d, f, "__module__", ast.get_docstring(tree) or "", fr, module=True)
        if head:
            d.out.append(f"<p>{head}</p>")
        secs = mcg.sections(src) or [(1, "")]
        items = mcg.entries(tree)
        bounds = [s[0] for s in secs] + [n_lines + 1]
        for k, (line0, title) in enumerate(secs):
            inside = [e for e in items if (e[0] < bounds[1] if k == 0 else bounds[k] <= e[0] < bounds[k + 1])]
            if not inside:
                continue
            if title:
                d.out.append(f'<h3 class="refsec">{d.text(guide.SECTION_TITLES.get(title, title))}</h3>')
            for line, kind, name, sig, doc, depth in inside:
                cls = "ref method" if depth else "ref"
                d.out.append(f'<div class="{cls}"><div class="sig"><code>{html.escape(sig)}</code>'
                             f'<span class="meta">{lab[kind]}, {lab["line"]} {line}</span></div>'
                             f'<div class="expl">{describe(d, f, name, doc, fr)}</div></div>')


def describe(d, f, name, doc, fr, module=False):
    """HTML of the explanation of an entry: the French text when there is one, else the docstring (flagged
    as untranslated in the French guide)."""
    if fr is not None and f"{f}:{name}" in fr:
        return d.text(fr[f"{f}:{name}"])
    if not doc:
        return "" if module else d.text(d.lab["helper"])
    text = mcg.para(doc).replace("\n\n", "\n").replace("\n    ", "\n").strip()
    if module:                                                  # the licence lines are on the cover
        text = "\n".join(l for l in text.split("\n") if not re.match(r"(©|Licence|This program|redistribute)", l))
    out = d.text(text).replace("\n", "<br>")
    if fr is not None:
        out += f' <span class="meta">{d.text(d.lab["untranslated"])}</span>'
    return out


# ----------------------------------------------------------------------------------------------------------
# Page: styles, cover, contents
# ----------------------------------------------------------------------------------------------------------

def css(footer):
    def face(family, file, style="normal", weight="100 900"):
        return (f'@font-face{{font-family:"{family}";src:url("{file_url(os.path.join(FONTS, file))}");'
                f"font-style:{style};font-weight:{weight}}}")
    fonts = (face("Gerbil Serif", "SourceSerif4[opsz,wght].ttf") +
             face("Gerbil Serif", "SourceSerif4-Italic[opsz,wght].ttf", "italic") +
             face("Gerbil Display", "CormorantGaramond[wght].ttf") +
             face("Gerbil Mono", "CourierPrime-Regular.ttf", weight="400") +
             face("Gerbil Mono", "CourierPrime-Bold.ttf", weight="700") +
             face("Gerbil Mono", "CourierPrime-Italic.ttf", "italic", "400"))
    footer = footer.replace('"', '\\"')
    return fonts + f"""
:root {{ --ink:{INK}; --ink2:{INK_2}; --tint:{TINT}; --tint2:{TINT_2}; --pale:{TINT_PALE}; --sage:{SAGE};
  --teal:{TEAL}; --terra:{TERRA}; --terrapale:{TERRA_PALE}; --text:{TEXT}; --muted:{MUTED}; --line:{LINE};
  --grid:{GRID}; --paper:{PAPER}; }}
@page {{ size: A4; margin: 20mm 19mm 19mm 19mm;
  @bottom-left {{ content: "{footer}"; font: italic 8.5pt "Gerbil Serif", Georgia, serif; color: {MUTED}; }}
  @bottom-right {{ content: counter(page); font: 700 9pt "Gerbil Mono", monospace; color: {INK}; }} }}
@page cover {{ margin: 0; @bottom-left {{ content: none }} @bottom-right {{ content: none }} }}
@page partpage {{ margin: 0 0 19mm 0; @bottom-left {{ content: none }} @bottom-right {{ content: none }} }}
* {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
html {{ font: 10.2pt/1.5 "Gerbil Serif", Georgia, serif; color: var(--text); }}
body {{ margin: 0; font-variant-numeric: oldstyle-nums proportional-nums; hyphens: auto; }}
p {{ margin: 0 0 2.6mm; text-align: justify; orphans: 3; widows: 3; }}
a {{ color: var(--ink2); text-decoration: none; }}
a.xref {{ border-bottom: 0.6pt dotted var(--ink2); }}
a.web {{ word-break: break-all; }}
strong {{ color: var(--ink); font-weight: 650; }}
code, kbd, pre {{ font-family: "Gerbil Mono", monospace; }}
code {{ font-size: 0.92em; color: var(--ink); background: var(--pale); padding: 0 1.2pt; border-radius: 2pt;
  font-variant-numeric: normal; }}
kbd {{ font-size: 0.82em; font-weight: 700; color: var(--ink); background: #fff; border: 0.7pt solid var(--tint2);
  border-bottom-width: 1.6pt; border-radius: 2.5pt; padding: 0 3pt; white-space: nowrap; }}
.keys {{ white-space: nowrap; }}
h1, h2, h3 {{ font-family: "Gerbil Display", Georgia, serif; color: var(--ink); line-height: 1.1;
  break-after: avoid; page-break-after: avoid; font-variant-numeric: lining-nums; }}
h2 {{ font-size: 21pt; font-weight: 600; margin: 8mm 0 3mm; padding-bottom: 1.6mm;
  border-bottom: 0.8pt solid var(--tint2); }}
h2 .num, h3 .num {{ font-family: "Gerbil Mono"; font-size: 0.55em; color: var(--ink2); margin-right: 3mm;
  vertical-align: 0.25em; }}
h3 {{ font-size: 14.5pt; font-weight: 700; margin: 5mm 0 2mm; color: var(--ink2); }}
h3.refsec {{ font-size: 12.5pt; margin-top: 6mm; }}
ul, ol {{ margin: 0 0 3mm; padding-left: 6.5mm; }}
li {{ margin: 0 0 1.3mm; }}
li::marker {{ color: var(--ink2); font-weight: 700; }}
ol > li::marker {{ font-family: "Gerbil Mono"; }}
pre.code {{ font-size: 8.4pt; line-height: 1.45; color: var(--ink); background: var(--pale);
  border-left: 2.5pt solid var(--ink2); padding: 2.5mm 3.5mm; margin: 1mm 0 3.5mm; white-space: pre-wrap;
  break-inside: avoid; }}
.box {{ margin: 2mm 0 4mm; padding: 2.6mm 3.6mm 2.6mm 4mm; border-left: 3pt solid var(--ink2);
  background: var(--pale); break-inside: avoid; text-align: left; }}
.box .label {{ display: block; font: 700 7.6pt "Gerbil Mono", monospace; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ink2); margin-bottom: 0.8mm; }}
.box.warn {{ border-color: var(--terra); background: var(--terrapale); }}
.box.warn .label {{ color: var(--terra); }}
.box.note {{ border-color: var(--teal); background: #EEF4F4; }}
.box.note .label {{ color: var(--teal); }}
.box.key {{ border: 1pt solid var(--tint2); border-left: 3pt solid var(--ink); background: #fff; }}
.box.key .label {{ color: var(--ink); }}
blockquote {{ margin: 2mm 0 4mm; padding: 3mm 5mm; border-left: 2pt solid var(--sage); font-style: italic;
  background: repeating-linear-gradient(0deg, transparent 0 4.6mm, var(--grid) 4.6mm 4.8mm),
  repeating-linear-gradient(90deg, transparent 0 4.6mm, var(--grid) 4.6mm 4.8mm); }}
table {{ width: 100%; border-collapse: collapse; margin: 1.5mm 0 4.5mm; font-size: 9pt; line-height: 1.38;
  table-layout: fixed; }}
thead {{ display: table-header-group; }}
th {{ font: 700 7.6pt "Gerbil Mono", monospace; letter-spacing: 0.06em; text-transform: uppercase;
  color: #fff; background: var(--ink); text-align: left; padding: 1.8mm 2.2mm; }}
td {{ padding: 1.6mm 2.2mm; border-bottom: 0.5pt solid var(--line); vertical-align: top; }}
tbody tr:nth-child(even) td {{ background: #F7FAF8; }}
tr {{ break-inside: avoid; }}
table.annotated td.ln {{ font: 7pt "Gerbil Mono"; color: var(--muted); text-align: right; }}
table.annotated td.src {{ background: var(--pale) !important; }}
table.annotated pre {{ margin: 0; font-size: 7.6pt; line-height: 1.35; white-space: pre-wrap; color: var(--ink); }}
figure {{ margin: 3mm 0 5mm; break-inside: avoid; text-align: center; }}
figure img {{ max-width: 100%; }}
figure.shot img {{ width: 100%; border: 0.6pt solid var(--line); border-radius: 1.5mm;
  box-shadow: 0 0.8mm 2.4mm rgba(30, 66, 48, 0.16); }}
figure.shot.half img {{ width: 72%; }}
figure.shot.third img {{ width: 46%; }}
figure.small img {{ max-height: 85mm; border: 0.6pt solid var(--line); }}
figcaption {{ font-size: 8.6pt; font-style: italic; color: var(--muted); margin-top: 1.8mm; text-align: center;
  padding: 0 8mm; }}
dl {{ margin: 0 0 4mm; }}
dl.two {{ columns: 2; column-gap: 8mm; }}
dl.two dt {{ break-after: avoid; }}
dl.two dd {{ break-before: avoid; text-align: left; font-size: 9.4pt; }}
dt {{ font-weight: 700; color: var(--ink); margin-top: 2.2mm; break-after: avoid; }}
dd {{ margin: 0.4mm 0 0 6mm; text-align: justify; }}
p.lead {{ font-size: 12pt; line-height: 1.5; color: var(--ink); text-align: left; }}
p.filerole {{ font-style: italic; color: var(--muted); }}
.pagebreak {{ break-after: page; }}

/* the work from A to Z */
.flow {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 3mm; margin: 2mm 0 5mm; }}
.stepcard {{ display: block; border: 0.8pt solid var(--tint2); border-top: 3pt solid var(--ink); background: #fff;
  padding: 2.4mm 3mm 3mm; color: var(--text); break-inside: avoid; }}
.stepcard .n {{ display: block; font: 700 15pt "Gerbil Mono", monospace; color: var(--ink2); }}
.stepcard .st {{ display: block; font: 700 13pt/1.15 "Gerbil Display", serif; color: var(--ink); margin: 0.6mm 0 1.2mm; }}
.stepcard .sd {{ display: block; font-size: 8.6pt; line-height: 1.38; color: var(--muted); }}
.wants {{ display: grid; grid-template-columns: 1fr 1fr; gap: 2.2mm 4mm; margin: 2mm 0 5mm; }}
.want {{ display: block; padding: 2mm 3mm; border-left: 2.5pt solid var(--sage); background: var(--pale);
  color: var(--text); break-inside: avoid; }}
.want .q {{ display: block; font-weight: 700; color: var(--ink); }}
.want .r {{ display: block; font-size: 8.6pt; color: var(--muted); }}

/* parts */
section.part {{ page: partpage; break-before: page; break-after: page; }}
section.part .band {{ position: relative; margin: 0; padding: 34mm 19mm 12mm; min-height: 128mm;
  overflow: hidden; color: #fff; background-color: var(--ink);
  background-image: repeating-linear-gradient(0deg, transparent 0 5mm, rgba(255,255,255,0.07) 5mm 5.25mm),
    repeating-linear-gradient(90deg, transparent 0 5mm, rgba(255,255,255,0.07) 5mm 5.25mm); }}
section.part .big {{ position: absolute; right: 14mm; bottom: -16mm; font: 600 150pt/1 "Gerbil Display", serif;
  color: rgba(171, 214, 180, 0.22); }}
section.part h1 {{ position: relative; margin: 0; color: #fff; font-size: 40pt; font-weight: 600; border: 0; }}
section.part h1 .num {{ display: block; font: 700 11pt "Gerbil Mono", monospace; color: var(--sage);
  letter-spacing: 0.14em; margin-bottom: 5mm; }}
section.part h1 .num::before {{ content: "{{PART}} "; }}
section.part .band p.lead {{ position: relative; max-width: 140mm; font-size: 12.5pt; margin: 9mm 0 0; color: #E6F0E9; }}
.intoc {{ font: 700 8pt "Gerbil Mono", monospace; letter-spacing: 0.12em; color: var(--ink2); margin: 12mm 19mm 2mm;
  text-transform: uppercase; }}
ol.minitoc {{ list-style: none; padding: 0; margin: 0 19mm; columns: 2; column-gap: 10mm; }}
ol.minitoc li {{ break-inside: avoid; display: flex; gap: 3mm; padding: 2mm 0; border-bottom: 0.5pt solid var(--line);
  font-size: 10.8pt; }}
ol.minitoc .k {{ font: 700 8.5pt "Gerbil Mono"; color: var(--ink2); padding-top: 0.8mm; }}
ol.minitoc a {{ color: var(--ink); }}

/* cover */
.cover {{ page: cover; height: 297mm; position: relative; overflow: hidden; color: #fff;
  background-color: var(--ink);
  background-image: repeating-linear-gradient(0deg, transparent 0 5mm, rgba(255,255,255,0.07) 5mm 5.25mm),
    repeating-linear-gradient(90deg, transparent 0 5mm, rgba(255,255,255,0.07) 5mm 5.25mm); }}
.cover .inner {{ position: absolute; left: 24mm; right: 24mm; top: 34mm; }}
.cover img {{ width: 58mm; height: 58mm; }}
.cover .name {{ font: 600 66pt/1 "Gerbil Display", serif; letter-spacing: 0.04em; margin: 10mm 0 2mm; }}
.cover .sub {{ font: 600 23pt/1.15 "Gerbil Display", serif; color: var(--sage); }}
.cover .tag {{ font-size: 12.5pt; line-height: 1.5; margin-top: 9mm; max-width: 140mm; color: #E6F0E9; }}
.cover .ruler {{ position: absolute; left: 24mm; bottom: 46mm; width: 100mm; height: 5mm;
  background: repeating-linear-gradient(90deg, #fff 0 10mm, var(--ink) 10mm 20mm); border: 0.8pt solid #fff; }}
.cover .ruler::after {{ content: "10 cm"; position: absolute; left: 103mm; top: -1mm;
  font: 700 9pt "Gerbil Mono"; color: var(--sage); }}
.cover .foot {{ position: absolute; left: 24mm; right: 24mm; bottom: 18mm; font-size: 9.5pt; color: #D9E8DE;
  display: flex; justify-content: space-between; align-items: flex-end; }}
.cover .foot b {{ font: 600 17pt "Gerbil Display", serif; color: #fff; letter-spacing: 0.08em; }}

/* contents */
.toc {{ break-after: page; }}
.toc h2.toctitle {{ font-size: 30pt; border: 0; margin: 0 0 6mm; }}
.toc .l1 {{ display: flex; align-items: baseline; margin: 4.2mm 0 1.2mm; font: 700 13.5pt "Gerbil Display", serif;
  break-after: avoid; }}
.toc .l1 .n {{ font: 700 9pt "Gerbil Mono"; color: var(--ink2); width: 9mm; }}
.toc .l2 {{ display: flex; align-items: baseline; margin: 0.5mm 0 0.5mm 9mm; font-size: 9.6pt; }}
.toc a {{ color: var(--text); }}
.toc .l1 a {{ color: var(--ink); }}
.toc .dots {{ flex: 1; border-bottom: 0.8pt dotted var(--tint2); margin: 0 2mm; transform: translateY(-1mm); }}
.toc .pg {{ font: 700 8.6pt "Gerbil Mono"; color: var(--ink2); min-width: 7mm; text-align: right; }}

/* reference */
.ref {{ margin: 2.2mm 0 0; break-inside: avoid; }}
.ref.method {{ margin-left: 6mm; }}
.ref .sig code {{ background: none; padding: 0; font-weight: 700; font-size: 8.6pt; }}
.ref .sig .meta {{ margin-left: 2mm; }}
.ref .expl {{ margin-left: 5mm; font-size: 9pt; line-height: 1.42; }}
.meta {{ font-size: 7.8pt; font-style: italic; color: var(--muted); }}
"""


def cover(d, guide, ver):
    icon = os.path.join(IMAGES, "gerbil_512.png")
    lab = d.lab
    today = datetime.date.today().isoformat()
    return (f'<div class="cover"><div class="inner"><img src="{file_url(icon)}" alt="">'
            f'<div class="name">GERBIL</div><div class="sub">{d.inline(guide["subtitle"])}</div>'
            f'<div class="tag">{d.inline(guide["tagline"])}</div></div><div class="ruler"></div>'
            f'<div class="foot"><span>{lab["version"]} {ver}<br>{d.text(lab["licence"])}<br>'
            f'{d.text(lab["date"])} {today}<br>github.com/EloisCharbonnel/gerbil</span>'
            f'<span style="text-align:right">© {today[:4]} Eloïs Charbonnel<br><b>ITINERA</b></span></div></div>')


def contents(d, pages):
    rows = []
    for level, number, title, anchor in d.heads:
        if level > 2 or (level == 2 and anchor.startswith("ref-")):
            continue
        pg = pages.get(anchor, "")
        if level == 1:
            rows.append(f'<div class="l1"><span class="n">{html.escape(number or "")}</span><a href="#{anchor}">'
                        f'{d.inline(title)}</a><span class="dots"></span><span class="pg">{pg}</span></div>')
        else:
            rows.append(f'<div class="l2"><a href="#{anchor}">{d.inline(title)}</a><span class="dots"></span>'
                        f'<span class="pg">{pg}</span></div>')
    return f'<div class="toc"><h2 class="toctitle">{d.text(d.lab["contents"])}</h2>{"".join(rows)}</div>'


# ----------------------------------------------------------------------------------------------------------
# Printing
# ----------------------------------------------------------------------------------------------------------

def browser():
    names = [os.path.join(os.environ.get(v, ""), *p) for v in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")
             for p in (("Microsoft", "Edge", "Application", "msedge.exe"),
                       ("Google", "Chrome", "Application", "chrome.exe"))]
    for path in names + [shutil.which("msedge") or "", shutil.which("chrome") or ""]:
        if path and os.path.exists(path):
            return path
    sys.exit("Microsoft Edge or Google Chrome is needed to print the guides.")


def print_pdf(html_path, pdf_path):
    profile = tempfile.mkdtemp(prefix="gerbil_print_")
    try:
        subprocess.run([browser(), "--headless=new", "--disable-gpu", "--no-first-run", "--no-pdf-header-footer",
                        "--generate-pdf-document-outline", "--run-all-compositor-stages-before-draw",
                        "--virtual-time-budget=20000", f"--user-data-dir={profile}",
                        f"--print-to-pdf={pdf_path}", file_url(html_path)],
                       check=True, capture_output=True, timeout=600)
    finally:
        shutil.rmtree(profile, ignore_errors=True)


def pdfium():
    try:
        import pypdfium2
        return pypdfium2
    except ImportError:
        pass
    extra = os.environ.get("GERBIL_PDFIUM")
    if extra:
        sys.path.append(extra)
        try:
            import pypdfium2
            return pypdfium2
        except ImportError:
            pass
    return None


def page_numbers(pdf_path, heads):
    """{anchor: page} from the bookmarks of a printed guide (they follow the headings, in order)."""
    lib = pdfium()
    if lib is None:
        return {}
    doc = lib.PdfDocument(pdf_path)
    marks = [(re.sub(r"\s+", " ", b.get_title()).strip(), b.get_dest().get_index() + 1)
             for b in doc.get_toc() if b.get_dest() is not None]
    doc.close()
    out, k = {}, 0
    for level, number, title, anchor in heads:
        want = re.sub(r"\s+", " ", re.sub(r"[`*]|\[\[[^|\]]*\|?|\]\]", "", title)).strip()[:25]
        for j in range(k, len(marks)):
            if want and want in marks[j][0]:
                out[anchor], k = marks[j][1], j + 1
                break
    return out


def build(lang, which, keep_html=False):
    if lang == "fr":
        guide = load_module(os.path.join(DOCS, "fr", "guide_fr.py"))
        fr = {**load_module(os.path.join(DOCS, "fr", "reference_fr.py")).FR,
              **load_module(os.path.join(DOCS, "fr", "reference_fr_more.py")).FR}
    else:
        guide = load_module(os.path.join(DOCS, "guide_en.py"))
        fr = None
    meta = guide.USER_META if which == "user" else guide.CODE_META
    blocks = guide.USER if which == "user" else guide.CODE
    ver = version()
    name = f"Gerbil_guide_{lang.upper()}" if which == "user" else f"Gerbil_code_guide_{lang.upper()}"
    pdf = os.path.join(DOCS, name + ".pdf")
    tmp = tempfile.mkdtemp(prefix="gerbil_guide_")
    pages = {}
    try:
        for attempt in (1, 2):
            d = Doc(lang, guide.LABELS)
            d.blocks(blocks, sections_of(blocks))
            if which == "code":
                reference(d, guide, fr, meta["ref_number"])
            body = d.resolve()
            page = (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>'
                    f'{html.escape("Gerbil, " + meta["subtitle"])}</title><style>'
                    f'{css(meta["footer"].format(version=ver)).replace("{PART}", d.lab["part"])}</style></head><body>'
                    f'{cover(d, meta, ver)}{contents(d, pages)}{body}</body></html>')
            html_path = os.path.join(tmp, name + ".html")
            with open(html_path, "w", encoding="utf-8") as fh:
                fh.write(page)
            print_pdf(html_path, pdf)
            found = page_numbers(pdf, d.heads)
            if not found or found == pages:
                break
            pages = found
        if keep_html:
            shutil.copy(html_path, os.path.join(DOCS, name + ".html"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n_pages = ""
    lib = pdfium()
    if lib is not None:
        doc = lib.PdfDocument(pdf)
        n_pages = f", {len(doc)} pages"
        doc.close()
    print(f"{os.path.relpath(pdf, ROOT)}: {len(d.heads)} headings{n_pages}, {os.path.getsize(pdf) // 1024} KB"
          + ("" if pages else " (contents without page numbers: pypdfium2 not found)"))


if __name__ == "__main__":
    args = sys.argv[1:]
    langs = [a for a in args if a in ("fr", "en")] or ["fr", "en"]
    kinds = [a for a in args if a in ("user", "code")] or ["user", "code"]
    for language in langs:
        for kind in kinds:
            build(language, kind, "--html" in args)
