#!/usr/bin/env python3
"""
build_notes.py: AES lecture notes builder (slide left 2/3, notes right 1/3).

  python3 build_notes.py scan  DECK.pdf|DECK.pptx  -o slides/
      Redacts purple (#9933FF-ish) notetaker notes, renders + crops every page
      to slides/cN.png, and writes slides/map.txt (text, emphasis spans,
      annotations, purple notes per page).

  python3 build_notes.py build NOTES.md --slides slides/ -o OUT.docx [--render DIR]
      Builds the Word notes from the markup in NOTES.md (see FORMAT.md).
      "!fig path.png" places an image at column width (cheat-sheet design
      figures from tools/cheat_figures.py, or a figure beside a slide).
      Auto-splits long pages into "(continued)" pages, converts LaTeX to native
      Word equations, generates title page, contents, Open questions, runs the
      content checks, and (with --render) renders pages to PNG contact sheets.

Requires: python3, pymupdf, pillow, lxml, pyyaml, pandoc; soffice for .pptx and --render.
"""
import argparse, io, os, re, shutil, subprocess, sys, tempfile, zipfile, glob, math
from xml.sax.saxutils import escape as _esc

# ----------------------------------------------------------------- constants
NOTE_SZ = 30            # half-points (15pt)
DEF_SZ = 26             # symbol-definition lines, nested tables (13pt)
H2_SZ, H3_SZ, H1_SZ = 36, 32, 40
CHEAT_SZ, CHEAT_H_SZ = 16, 18
CODE_SZ = 24
NAVY, AMBER_TXT, AMBER_FILL, AMBER_BAR = "1F3864", "7F5F00", "FFF2CC", "BF8F00"
GREY, DGREY, RED = "808080", "595959", "FF0000"
PAGE_W, LEFT_W, RIGHT_W = 14400, 9600, 4800
RIGHT_TEXT_PT = (RIGHT_W - 140 - 100) / 20.0       # 228pt
WIDE_TEXT_PT = (PAGE_W - 200) / 20.0
CHEAT_COL_W = 3400
PURPLE = (153, 51, 255)
EMU_IN = 914400

FONT_DIRS = ["/usr/share/fonts/truetype/crosextra", "/usr/share/fonts/truetype/liberation",
             "/usr/share/fonts/truetype/dejavu", "/usr/share/fonts"]


def esc(s):
    return _esc(s, {'"': "&quot;"})


def die(msg):
    sys.exit("ERROR: " + msg)


# =================================================================== SCAN
def is_purple(rgb):
    r, g, b = rgb
    return (abs(r - PURPLE[0]) < 40 and abs(g - PURPLE[1]) < 50 and abs(b - PURPLE[2]) < 40) or \
           (b > 180 and r > 110 and g < 110 and r < 210)


def to_pdf(deck, workdir):
    if deck.lower().endswith(".pdf"):
        return deck
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", workdir, deck],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
    out = os.path.join(workdir, os.path.splitext(os.path.basename(deck))[0] + ".pdf")
    if not os.path.exists(out):
        die("could not convert %s to PDF" % deck)
    return out


def cmd_scan(a):
    import pymupdf as fitz
    from PIL import Image, ImageOps
    os.makedirs(a.out, exist_ok=True)
    pdf = to_pdf(a.deck, a.out)
    doc = fitz.open(pdf)
    lines = ["DECK %s: %d pages" % (os.path.basename(a.deck), doc.page_count)]
    for pno, page in enumerate(doc, 1):
        lines.append("\n=== PAGE %d ===" % pno)
        words = page.get_text("words")
        txt = page.get_text("text").strip()
        lines.append("TEXT: " + (re.sub(r"\s+", " ", txt)[:1500] or "(no text layer: read this slide from the sheet image)"))
        purple, emph = [], []
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for s in line["spans"]:
                    t = s["text"].strip()
                    if not t:
                        continue
                    rgb = fitz.sRGB_to_rgb(s["color"])
                    if is_purple(rgb):
                        purple.append((fitz.Rect(s["bbox"]), t))
                    elif (s["flags"] & 16) or "Bold" in s["font"] or s["color"] != 0:
                        emph.append("%s%s %s" % ("B " if ((s["flags"] & 16) or "Bold" in s["font"]) else "",
                                                 "#%02X%02X%02X" % rgb, t))
        if emph:
            lines.append("EMPHASIS: " + " | ".join(emph)[:1200])
        for an in page.annots() or []:
            hit = " ".join(w[4] for w in words if fitz.Rect(w[:4]).intersects(an.rect))
            lines.append("ANNOT %s: %s %s" % (an.type[1], an.info.get("content", ""), hit[:200]))
        if purple:
            lines.append("PURPLE NOTE (to notetaker, removed from image): " + " ".join(t for _, t in purple))
            for r, _ in purple:
                page.add_redact_annot(r + (-2, -2, 2, 2), fill=(1, 1, 1))
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                                  graphics=fitz.PDF_REDACT_LINE_ART_NONE)
        raw = os.path.join(a.out, "raw%d.png" % pno)
        page.get_pixmap(dpi=a.dpi).save(raw)
        im = Image.open(raw).convert("RGB")
        bb = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 25 else 0).getbbox() or (0, 0, im.width, im.height)
        pad = 25
        bb = (max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad))
        im.crop(bb).save(os.path.join(a.out, "c%d.png" % pno), optimize=True)
        os.remove(raw)
    with open(os.path.join(a.out, "map.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    # contact sheets of the cropped slides, 3x3, for one Read per 9 slides
    sheets = contact_sheets(sorted(glob.glob(os.path.join(a.out, "c*.png")),
                                   key=lambda p: int(re.findall(r"c(\d+)\.png", p)[0])),
                            os.path.join(a.out, "slides_sheet"), cols=3, rows=3, cell=(700, 420), label=True)
    print("Rendered %d slides to %s; map: %s/map.txt; sheets: %s" % (doc.page_count, a.out, a.out, ", ".join(sheets)))
    print("Look at the sheets for ink; zoom into a single cN.png only where detail matters.")


def contact_sheets(files, prefix, cols=4, rows=3, cell=(550, 425), label=False):
    from PIL import Image, ImageDraw
    out = []
    per = cols * rows
    for k in range(0, len(files), per):
        g = Image.new("RGB", (cell[0] * cols, cell[1] * rows), "white")
        d = ImageDraw.Draw(g)
        for j, f in enumerate(files[k:k + per]):
            im = Image.open(f).convert("RGB")
            im.thumbnail((cell[0] - 10, cell[1] - (30 if label else 10)))
            x, y = (j % cols) * cell[0] + 5, (j // cols) * cell[1] + 5
            g.paste(im, (x, y))
            if label:
                d.text((x, y + im.height + 2), os.path.basename(f), fill=(200, 0, 0))
            d.rectangle([x - 5, y - 5, x - 5 + cell[0] - 1, y - 5 + cell[1] - 1], outline=(220, 220, 220))
        p = "%s%d.png" % (prefix, k // per + 1)
        g.save(p)
        out.append(p)
    return out


# =================================================================== MEASURE
_fonts = {}


def font(bold=False, italic=False, size=15, mono=False):
    from PIL import ImageFont
    key = (bold, italic, size, mono)
    if key in _fonts:
        return _fonts[key]
    if mono:
        names = ["LiberationMono-Bold.ttf" if bold else "LiberationMono-Regular.ttf", "DejaVuSansMono.ttf"]
    else:
        nm = "Carlito-" + ("BoldItalic" if bold and italic else "Bold" if bold else "Italic" if italic else "Regular")
        names = [nm + ".ttf", "DejaVuSans.ttf"]
    f = None
    for n in names:
        for d in FONT_DIRS:
            for p in glob.glob(os.path.join(d, "**", n), recursive=True):
                f = ImageFont.truetype(p, size * 10)  # measure at 10x for precision
                break
            if f:
                break
        if f:
            break
    if f is None:
        f = ImageFont.load_default()
    _fonts[key] = f
    return f


def text_w(s, size_pt, bold=False, italic=False, mono=False):
    return font(bold, italic, int(size_pt), mono).getlength(s) / 10.0 * (size_pt / int(size_pt))


def latex_plain(l):
    """crude width-equivalent string for a LaTeX expression"""
    s = re.sub(r"\\(left|right|big|Big|bigg|Bigg)\b", "", l)
    s = re.sub(r"\\[,;:!]|\\quad|\\qquad", " ", s)
    s = re.sub(r"\\(text|mathrm|mathbf|mathit|operatorname)\s*\{([^{}]*)\}", r"\2", s)
    for _ in range(6):
        s2 = re.sub(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}",
                    lambda m: m.group(1) if len(m.group(1)) >= len(m.group(2)) else m.group(2), s)
        if s2 == s:
            break
        s = s2
    s = re.sub(r"\\sqrt\s*", "v", s)
    s = re.sub(r"\\[a-zA-Z]+", "x", s)
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"[\^_](\w)", r"\1", s)
    s = s.replace("^", "").replace("_", "")
    return s


def latex_w(l, size_pt):
    s = latex_plain(l)
    ops = len(re.findall(r"[=<>+\-]|\\(le|ge|approx|cdot|times|pm|neq|to|Rightarrow)", l))
    return len(s) * 0.52 * size_pt + ops * 0.35 * size_pt


def frac_depth(l):
    depth = best = 0
    i = 0
    stack = []
    # count nesting of \frac by brace tracking
    tokens = re.finditer(r"\\[dt]?frac|\{|\}", l)
    pending = 0
    for t in tokens:
        v = t.group(0)
        if v.endswith("frac"):
            pending += 2
            depth_here = len([x for x in stack if x]) + 1
            best = max(best, depth_here)
        elif v == "{":
            if pending:
                stack.append(True)
                pending -= 1
            else:
                stack.append(False)
        else:
            if stack:
                stack.pop()
    return best


def eq_height(l, size_pt, display):
    d = frac_depth(l)
    h = size_pt * (1.35 + 1.15 * d)
    if re.search(r"\\(sum|int|prod|lim)", l):
        h += size_pt * 0.8
    if re.search(r"\\begin\{[bpv]?matrix\}|\\begin\{cases\}", l):
        rows = l.count(r"\\") + 1
        h = max(h, rows * size_pt * 1.5)
    if display:
        h += size_pt * 0.5
    return h


def runs_lines(runs, width, size_pt):
    """estimate wrapped line count + extra height from inline fractions"""
    words = []
    for r in runs:
        if r["math"] is not None:
            words.append((latex_w(r["math"], size_pt), r["math"]))
        else:
            for wd in re.split(r"(\s+)", r["text"]):
                if wd and not wd.isspace():
                    words.append((text_w(wd, size_pt, r["b"], r["i"], r.get("mono", False)), None))
                elif wd:
                    words.append((-1, None))
    space = text_w(" ", size_pt)
    lines, cur, tall_lines, cur_tall = 1, 0.0, 0, 0
    for w, m in words:
        if w < 0:
            cur += space
            continue
        if cur > 0 and cur + w > width:
            lines += 1
            tall_lines += cur_tall
            cur, cur_tall = 0.0, 0
        cur += w
        if m is not None and frac_depth(m) > 0:
            cur_tall = max(cur_tall, frac_depth(m))
        while cur > width:   # very long word/equation
            lines += 1
            cur -= width
    tall_lines += cur_tall
    return lines, tall_lines


LINE = 1.22


def para_h(runs, width, size_pt, before=0, after=0):
    n, tall = runs_lines(runs, width, size_pt)
    return n * LINE * size_pt + tall * 0.75 * size_pt + before + after


# =================================================================== INLINE
def parse_inline(s):
    """-> list of runs {text, b, i, math}"""
    runs, b, i = [], False, False
    pos = 0
    pat = re.compile(r"(?<!\\)\$(.+?)(?<!\\)\$|\*\*|\*|`([^`]+)`")
    for m in pat.finditer(s):
        if m.start() > pos:
            runs.append(dict(text=s[pos:m.start()].replace("\\$", "$"), b=b, i=i, math=None))
        tok = m.group(0)
        if tok == "**":
            b = not b
        elif tok == "*":
            i = not i
        elif tok.startswith("`"):
            runs.append(dict(text=m.group(2), b=b, i=i, math=None, mono=True))
        else:
            runs.append(dict(text="", b=b, i=i, math=m.group(1)))
        pos = m.end()
    if pos < len(s):
        runs.append(dict(text=s[pos:].replace("\\$", "$"), b=b, i=i, math=None))
    return [r for r in runs if r["text"] or r["math"] is not None]


# =================================================================== XML EMIT
class Doc:
    def __init__(self):
        self.eqs = []           # (latex, sz, display, bold, color)
        self.images = []        # (rid, path)
        self.nums = []          # (numId, abstractId, start)
        self.next_num = 10
        self.docpr = 1
        self.markers = []       # (page label, text runs source)

    def eq(self, latex, sz, display=False, bold=False, color=None):
        self.eqs.append((latex, sz, display, bold, color))
        return "@@EQ%d@@" % (len(self.eqs) - 1)

    def new_num(self, abstract, start=1):
        nid = self.next_num
        self.next_num += 1
        self.nums.append((nid, abstract, start))
        return nid


def rpr(sz, b=False, i=False, color=None, mono=False, extra=""):
    x = "<w:rPr>"
    if mono:
        x += '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
    x += "<w:b/><w:bCs/>" if b else '<w:b w:val="0"/><w:bCs w:val="0"/>'
    x += "<w:i/><w:iCs/>" if i else '<w:i w:val="0"/><w:iCs w:val="0"/>'
    if color:
        x += '<w:color w:val="%s"/>' % color
    x += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz) + extra + "</w:rPr>"
    return x


def runs_xml(doc, runs, sz, force_b=None, force_i=None, color=None):
    out = []
    for r in runs:
        b = r["b"] if force_b is None else (force_b or r["b"])
        i = r["i"] if force_i is None else (force_i or r["i"])
        if r["math"] is not None:
            out.append('<w:r><w:t>%s</w:t></w:r>' % doc.eq(r["math"], sz, False, b and color == RED, color if color == RED else None))
        else:
            out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (
                rpr(CODE_SZ if r.get("mono") else sz, b, i, color, r.get("mono", False)), esc(r["text"])))
    return "".join(out)


def p(content, spacing=(0, 60), ind=None, jc=None, style=None, extra_ppr="", keep_next=False, page_break=False):
    x = "<w:p><w:pPr>"
    if style:
        x += '<w:pStyle w:val="%s"/>' % style
    if keep_next:
        x += "<w:keepNext/>"
    if page_break:
        x += "<w:pageBreakBefore/>"
    x += extra_ppr
    x += '<w:spacing w:before="%d" w:after="%d"/>' % spacing
    if ind:
        x += ind
    if jc:
        x += '<w:jc w:val="%s"/>' % jc
    x += "</w:pPr>" + content + "</w:p>"
    return x


# ---------------------------------------------------------------- blocks
class Block:
    """A unit of right-column content. kind + data; height measured per width."""
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)
        self.glue_prev = kind in ("display", "defs")
        self.glue_next = kind in ("h3",)

    def height(self, width, cheat=False):
        k = self.kind
        sz = (CHEAT_SZ if cheat else NOTE_SZ) / 2.0
        if k == "para":
            return para_h(self.runs, width, sz, 0, 3)
        if k == "bullet":
            ind = 14 if self.level == 0 else 27
            return para_h(self.runs, width - ind, sz, 0, 2)
        if k == "num":
            return para_h(self.runs, width - 17, sz, 0, 2)
        if k == "h3":
            return para_h(self.runs, width, H3_SZ / 2.0, 6, 3)
        if k == "display":
            w = latex_w(self.latex, sz)
            rows = max(1, math.ceil(w / width))
            return eq_height(self.latex, sz, True) * rows + 3
        if k == "defs":
            return para_h(self.runs, width - 6, DEF_SZ / 2.0, 0, 3)
        if k == "flag":
            return para_h(self.runs, width - 25, sz, 3, 5) + 4
        if k in ("watch", "red", "onslide"):
            return para_h(self.runs, width - 20, sz, 3, 4)
        if k == "code":
            return len(self.lines) * 1.18 * CODE_SZ / 2.0 + 6
        if k == "fig":
            wpx, hpx = fig_size(self.path)
            return width * hpx / wpx + 6
        if k == "table":
            cw = col_widths(self.rows, width * 20)
            h = 0
            for r in self.rows:
                h += max(para_h(parse_inline(c), w / 20.0 - 6, DEF_SZ / 2.0) for c, w in zip(r, cw)) + 4
            return h + 6
        return 20


def col_widths(rows, total):
    n = max(len(r) for r in rows)
    lens = [max(8, len(rows[0][j]) + 2 if j < len(rows[0]) else 0,
                max((len(latex_plain(r[j])) if j < len(r) else 0) for r in rows[1:]) if len(rows) > 1 else 0)
            for j in range(n)]
    lens = [min(l, 60) for l in lens]
    s = sum(lens)
    w = [int(total * l / s) for l in lens]
    floor = min(1100, total // (n + 1))
    for j in range(n):
        if w[j] < floor:
            k = max(range(n), key=lambda t: w[t])
            w[k] -= floor - w[j]
            w[j] = floor
    w[-1] += total - sum(w)
    return w


def block_xml(doc, b, width_tw, cheat=False, num_ids=None):
    sz = CHEAT_SZ if cheat else NOTE_SZ
    k = b.kind
    if k == "para":
        if cheat:
            m = re.match(r"^(Use when:)\s*(.*)$", b.raw)
            if m:
                return p('<w:r>%s<w:t xml:space="preserve">Use when: </w:t></w:r>' % rpr(sz, True, True, "806000") +
                         runs_xml(doc, parse_inline(m.group(2)), sz, None, True, "806000"), (0, 20))
        return p(runs_xml(doc, b.runs, sz), (0, 20 if cheat else 60))
    if k == "bullet":
        nid = num_ids["cheat_bullet" if cheat else "bullet"]
        return p(runs_xml(doc, b.runs, sz), (0, 10 if cheat else 40), style="ListParagraph",
                 extra_ppr='<w:numPr><w:ilvl w:val="%d"/><w:numId w:val="%d"/></w:numPr>' % (b.level, nid))
    if k == "num":
        return p(runs_xml(doc, b.runs, sz), (0, 10 if cheat else 40), style="ListParagraph",
                 extra_ppr='<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr>' % b.num_id)
    if k == "h3":
        if cheat:
            return p(runs_xml(doc, b.runs, CHEAT_H_SZ, True, None, NAVY), (60, 20), keep_next=True,
                     extra_ppr='<w:pBdr><w:bottom w:val="single" w:sz="4" w:space="1" w:color="8EAADB"/></w:pBdr>'
                               '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>')
        return p(runs_xml(doc, b.runs, H3_SZ, True, None, NAVY), (120, 60), style="Heading3", keep_next=True)
    if k == "display":
        red = getattr(b, "red", False)
        return p('<w:r><w:t>%s</w:t></w:r>' % doc.eq(b.latex, sz, True, red, RED if red else None), (0, 60 if not cheat else 20))
    if k == "defs":
        return p(runs_xml(doc, b.runs, CHEAT_SZ if cheat else DEF_SZ, None, None, "404040"), (0, 60),
                 ind='<w:ind w:left="120"/>')
    if k == "flag":
        lab, rest = b.label, b.runs
        return p('<w:r>%s<w:t xml:space="preserve">\u26a0 %s: </w:t></w:r>' % (rpr(sz, True, False, AMBER_TXT), esc(lab)) +
                 runs_xml(doc, rest, sz, True, None, AMBER_TXT), (60, 100), ind='<w:ind w:left="140"/>',
                 extra_ppr='<w:pBdr><w:left w:val="single" w:color="%s" w:sz="36" w:space="6"/></w:pBdr>'
                           '<w:shd w:fill="%s" w:color="auto" w:val="clear"/>' % (AMBER_BAR, AMBER_FILL))
    if k == "watch":
        return p('<w:r>%s<w:t xml:space="preserve">Watch out. </w:t></w:r>' % rpr(sz, True) + runs_xml(doc, b.runs, sz),
                 (60, 80), ind='<w:ind w:left="140"/>',
                 extra_ppr='<w:pBdr><w:left w:val="single" w:color="808080" w:sz="24" w:space="6"/></w:pBdr>')
    if k == "red":
        return p(runs_xml(doc, b.runs, sz, True, None, RED), (60, 80))
    if k == "onslide":
        return p('<w:r>%s<w:t xml:space="preserve">On the slide: </w:t></w:r>' % rpr(sz, True, True, DGREY) +
                 runs_xml(doc, b.runs, sz, None, True, DGREY), (60, 60))
    if k == "code":
        return "".join(p('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(CHEAT_SZ if cheat else CODE_SZ, mono=True), esc(l) or " "),
                         (0, 0), extra_ppr='<w:keepNext/>' if j < len(b.lines) - 1 else "")
                       for j, l in enumerate(b.lines)) + p("", (0, 60))
    if k == "table":
        return table_xml(doc, b.rows, width_tw, CHEAT_SZ if cheat else DEF_SZ)
    if k == "fig":
        w_in = (width_tw - 60) / 1440.0
        return p(image_xml(doc, fig_path(b.path), max_w_in=w_in, max_h_in=4.0), (20, 40), jc="center")
    return ""


NOTES_DIR = "."


def fig_path(path):
    """!fig paths: absolute, relative to the working directory, or relative to notes.md."""
    for cand in (path, os.path.join(NOTES_DIR, path)):
        if os.path.exists(cand):
            return cand
    die("!fig image not found: %s" % path)


def fig_size(path):
    from PIL import Image
    return Image.open(fig_path(path)).size


def table_xml(doc, rows, width_tw, sz):
    cw = col_widths(rows, width_tw)
    n = len(cw)
    bd = '<w:top w:val="single" w:sz="4" w:color="BFBFBF"/><w:left w:val="single" w:sz="4" w:color="BFBFBF"/>' \
         '<w:bottom w:val="single" w:sz="4" w:color="BFBFBF"/><w:right w:val="single" w:sz="4" w:color="BFBFBF"/>' \
         '<w:insideH w:val="single" w:sz="4" w:color="BFBFBF"/><w:insideV w:val="single" w:sz="4" w:color="BFBFBF"/>'
    x = '<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="%d"/><w:tblBorders>%s</w:tblBorders><w:tblLayout w:type="fixed"/>' \
        '<w:tblCellMar><w:top w:w="30" w:type="dxa"/><w:left w:w="60" w:type="dxa"/><w:bottom w:w="30" w:type="dxa"/><w:right w:w="60" w:type="dxa"/></w:tblCellMar>' \
        '</w:tblPr><w:tblGrid>%s</w:tblGrid>' % (width_tw, bd, "".join('<w:gridCol w:w="%d"/>' % w for w in cw))
    for ri, r in enumerate(rows):
        x += "<w:tr>" + ('<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' if ri == 0 else '<w:trPr><w:cantSplit/></w:trPr>')
        for j in range(n):
            c = r[j] if j < len(r) else ""
            shd = '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>' if ri == 0 else ""
            x += '<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="%d"/>%s</w:tcPr>%s</w:tc>' % (
                cw[j], shd, p(runs_xml(doc, parse_inline(c), sz, True if ri == 0 else None), (0, 0)))
        x += "</w:tr>"
    return x + "</w:tbl>" + p("", (0, 40))


# =================================================================== PARSE
def parse_front(text):
    import yaml
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        die("NOTES.md must start with a --- front matter block")
    meta = yaml.safe_load(m.group(1)) or {}
    return meta, text[m.end():]


def split_cells(row):
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    cells, cur, inmath = [], "", False
    for ch in row:
        if ch == "$":
            inmath = not inmath
        if ch == "|" and not inmath:
            cells.append(cur.strip())
            cur = ""
        else:
            cur += ch
    cells.append(cur.strip())
    return cells


def parse_blocks(lines, ctx):
    """lines -> list of Block / ('break',)"""
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if not s:
            i += 1
            continue
        if s == "---":
            out.append(Block("break"))
            i += 1
            continue
        if s.startswith("```"):
            j = i + 1
            code = []
            while j < len(lines) and not lines[j].strip().startswith("```"):
                code.append(lines[j].rstrip("\n"))
                j += 1
            for l in code:
                if len(l) > (34 if not ctx.get("wide") else 110):
                    ctx["warn"].append("%s: chart line over 34 chars (may wrap): %r" % (ctx["where"], l))
            out.append(Block("code", lines=code))
            i = j + 1
            continue
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_cells(lines[i].strip())
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if len(rows[0]) > 3 and not ctx.get("wide") and not ctx.get("cheat"):
                ctx["warn"].append("%s: table with >3 columns belongs on a '## Wide:' page" % ctx["where"])
            out.append(Block("table", rows=rows))
            continue
        if s.startswith("$$"):
            latex = s.strip("$").strip()
            out.append(Block("display", latex=latex))
            i += 1
            continue
        if s.startswith("### "):
            out.append(Block("h3", runs=parse_inline(s[4:]), raw=s[4:]))
        elif re.match(r"^!!\s*", s):
            body = re.sub(r"^!!\s*", "", s)
            m = re.match(r"^([A-Z0-9 ]+?):\s*(.*)$", body)
            if not m:
                ctx["warn"].append("%s: flag needs 'LABEL: text': %s" % (ctx["where"], s[:60]))
                m = re.match(r"^()(.*)$", body)
            out.append(Block("flag", label=m.group(1) or "IMPORTANT", runs=parse_inline(m.group(2)), raw=body))
        elif s.startswith("!watch "):
            out.append(Block("watch", runs=parse_inline(s[7:]), raw=s[7:]))
        elif s.startswith("!red "):
            out.append(Block("red", runs=parse_inline(s[5:]), raw=s[5:]))
        elif s.startswith("!slide "):
            out.append(Block("onslide", runs=parse_inline(s[7:]), raw=s[7:]))
        elif s.startswith("!fig "):
            out.append(Block("fig", path=s[5:].strip(), raw=s[5:].strip()))
        elif s.startswith("defs: "):
            out.append(Block("defs", runs=parse_inline(s[6:]), raw=s[6:]))
        elif re.match(r"^(\s*)[-*] ", ln):
            lvl = 1 if len(ln) - len(ln.lstrip()) >= 2 else 0
            out.append(Block("bullet", level=lvl, runs=parse_inline(re.sub(r"^\s*[-*] ", "", ln).strip()), raw=s))
        elif re.match(r"^\d+[.)] ", s):
            n = int(re.match(r"^(\d+)", s).group(1))
            out.append(Block("num", n=n, runs=parse_inline(re.sub(r"^\d+[.)] ", "", s)), raw=s))
        else:
            out.append(Block("para", runs=parse_inline(s), raw=s))
        i += 1
    return out


def parse_body(body, meta, warn):
    pages, back = [], {}
    sections = re.split(r"(?m)^(#{1,2} .*)$", body)
    cur_back = None
    for k in range(1, len(sections), 2):
        head, content = sections[k].strip(), sections[k + 1]
        lines = content.split("\n")
        if head.startswith("# "):
            title = head[2:].strip()
            low = title.lower()
            key = "important" if low.startswith("marked") else "cheat" if low.startswith("cheat") else "extra"
            back.setdefault(key, []).append((title, lines))
            cur_back = key
            continue
        if cur_back == "cheat":           # "## Topic" inside cheat sheet
            back["cheat"].append((head[3:].strip(), lines))
            continue
        h = head[3:].strip()
        pg = dict(head=h, lines=lines)
        m = re.match(r"^Slide (\d+)\s*:\s*(.+)$", h)
        mb = re.match(r'^Box\s+"([^"]+)"\s*:\s*(.+)$', h)
        mw = re.match(r"^Wide\s*:\s*(.+)$", h)
        if m:
            pg.update(kind="slide", slide=int(m.group(1)), title="Slide %s: %s" % (m.group(1), m.group(2).strip()))
        elif mb:
            pg.update(kind="box", box=mb.group(1), title=mb.group(2).strip())
        elif mw:
            pg.update(kind="wide", title=mw.group(1).strip())
        else:
            warn.append("Unrecognised page heading %r (use 'Slide N: ...', 'Box \"label\": ...' or 'Wide: ...')" % h)
            pg.update(kind="box", box=h, title=h)
        ctx = dict(where=h, warn=warn, wide=pg["kind"] == "wide")
        pg["blocks"] = parse_blocks(lines, ctx)
        pages.append(pg)
    return pages, back


# =================================================================== PAGINATE
def paginate(pg, budget, width_pt, warn):
    """split page blocks into chunks that fit the budget (pt)."""
    blocks = pg["blocks"]
    # groups: glue display/defs to previous, h3 to next
    groups, cur = [], []
    for b in blocks:
        if b.kind == "break":
            if cur:
                groups.append(cur)
            groups.append("BREAK")
            cur = []
            continue
        if cur and (b.glue_prev or cur[-1].glue_next):
            cur.append(b)
        else:
            if cur:
                groups.append(cur)
            cur = [b]
    if cur:
        groups.append(cur)
    head_h = para_h(parse_inline(pg["title"]), width_pt, H2_SZ / 2.0, 0, 5) if pg["kind"] != "wide" else 18
    cont_h = 18
    chunks, chunk, used = [], [], head_h
    chunk_used = {}
    for g in groups:
        if g == "BREAK":
            if chunk:
                chunks.append(chunk)
            chunk, used = [], cont_h
            continue
        gh = sum(b.height(width_pt) for b in g)
        if chunk and used + gh > budget:
            chunks.append(chunk)
            chunk, used = [], cont_h
        if not chunk and used + gh > budget:
            warn.append("%s: one block group is ~%dpt tall (budget %d); split it with shorter bullets or '---'"
                        % (pg["title"], used + gh, budget))
        chunk.extend(g)
        used += gh
        chunk_used[id(chunk)] = used
    if chunk or not chunks:
        chunks.append(chunk)
    if os.environ.get("NOTES_DEBUG"):
        for c in chunks:
            print("DEBUG est %4dpt  %s" % (chunk_used.get(id(c), 0), pg["title"][:40]))
    return chunks


# =================================================================== PAGE XML
NOB = '<w:top w:val="none" w:color="FFFFFF" w:sz="0"/><w:left w:val="none" w:color="FFFFFF" w:sz="0"/>' \
      '<w:bottom w:val="none" w:color="FFFFFF" w:sz="0"/><w:right w:val="none" w:color="FFFFFF" w:sz="0"/>'


def image_xml(doc, path, max_w_in=6.4, max_h_in=6.4):
    from PIL import Image
    w, h = Image.open(path).size
    wi = max_w_in
    hi = wi * h / w
    if hi > max_h_in:
        hi = max_h_in
        wi = hi * w / h
    rid = "rIdImg%d" % (len(doc.images) + 1)
    doc.images.append((rid, path))
    cx, cy = int(wi * EMU_IN), int(hi * EMU_IN)
    n = doc.docpr
    doc.docpr += 1
    return ('<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
            '<wp:docPr id="%d" name="Slide %d"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr><pic:cNvPr id="%d" name="slide%d.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>') % (cx, cy, n, n, n, n, rid, cx, cy)


def box_xml(label):
    """dashed grey placeholder ~6.4 x 3.6 in, as a 1-cell table"""
    return ('<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="9216"/><w:jc w:val="center"/><w:tblBorders>'
            '<w:top w:val="dashed" w:sz="8" w:color="A6A6A6"/><w:left w:val="dashed" w:sz="8" w:color="A6A6A6"/>'
            '<w:bottom w:val="dashed" w:sz="8" w:color="A6A6A6"/><w:right w:val="dashed" w:sz="8" w:color="A6A6A6"/>'
            '</w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr><w:tblGrid><w:gridCol w:w="9216"/></w:tblGrid>'
            '<w:tr><w:trPr><w:trHeight w:val="5184" w:hRule="exact"/></w:trPr><w:tc><w:tcPr><w:tcW w:type="dxa" w:w="9216"/>'
            '<w:vAlign w:val="center"/></w:tcPr>%s</w:tc></w:tr></w:tbl>') % p(
        '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(28, False, True, DGREY), esc(label)), (0, 0), jc="center")


def assign_lists(doc, chunk):
    """numbered items: one w:num per contiguous list run within the chunk"""
    last = None                       # last numbered item still "open"
    for b in chunk:
        if b.kind == "num":
            if last is not None and b.n == last.n + 1:
                b.num_id = last.num_id
            else:
                b.num_id = doc.new_num(3, b.n)
            last = b
        elif b.kind not in ("display", "defs", "code"):
            last = None


def page_xml(doc, pg, chunk, idx, nslides, slides_dir, num_ids, first_page):
    cont = idx > 0
    assign_lists(doc, chunk)
    # right column
    if pg["kind"] == "wide":
        right = p('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(26, True, False, GREY), esc(pg["title"])), (0, 80))
        right += "".join(block_xml(doc, b, PAGE_W - 200, num_ids=num_ids) for b in chunk) or p("")
        tbl = ('<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="%d"/><w:tblBorders>%s<w:insideH w:val="none" w:color="FFFFFF" w:sz="0"/>'
               '<w:insideV w:val="none" w:color="FFFFFF" w:sz="0"/></w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>'
               '<w:tblGrid><w:gridCol w:w="%d"/></w:tblGrid><w:tr><w:trPr><w:cantSplit/></w:trPr><w:tc><w:tcPr><w:tcW w:type="dxa" w:w="%d"/>'
               '<w:tcMar><w:top w:type="dxa" w:w="100"/><w:left w:type="dxa" w:w="100"/><w:bottom w:type="dxa" w:w="100"/><w:right w:type="dxa" w:w="100"/></w:tcMar>'
               '</w:tcPr>%s</w:tc></w:tr></w:tbl>') % (PAGE_W, NOB, PAGE_W, PAGE_W, right)
    else:
        if not cont:
            right = p(runs_xml(doc, parse_inline(pg["title"]), H2_SZ, True, None, NAVY), (0, 100), style="Heading2")
        else:
            lab = ("Slide %d (continued)" % pg["slide"]) if pg["kind"] == "slide" else pg["title"] + " (continued)"
            right = p('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(26, True, False, GREY), esc(lab)), (0, 80))
        right += "".join(block_xml(doc, b, RIGHT_W - 240, num_ids=num_ids) for b in chunk)
        if pg["kind"] == "slide":
            img = os.path.join(slides_dir, "c%d.png" % pg["slide"])
            if not os.path.exists(img):
                die("missing slide image %s" % img)
            left = p(image_xml(doc, img), (0, 0), jc="center")
            cap = "Slide %d of %d%s" % (pg["slide"], nslides, " (continued)" if cont else "")
        else:
            left = box_xml(pg["box"])
            cap = pg["box"] + (" (continued)" if cont else "")
        left += p('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(22, False, True, DGREY), esc(cap)), (80, 0), jc="center")
        tbl = ('<w:tbl><w:tblPr><w:tblW w:type="dxa" w:w="%d"/><w:tblBorders>%s<w:insideH w:val="none" w:color="FFFFFF" w:sz="0"/>'
               '<w:insideV w:val="none" w:color="FFFFFF" w:sz="0"/></w:tblBorders><w:tblLayout w:type="fixed"/></w:tblPr>'
               '<w:tblGrid><w:gridCol w:w="%d"/><w:gridCol w:w="%d"/></w:tblGrid>'
               '<w:tr><w:trPr><w:cantSplit/><w:trHeight w:val="9600" w:hRule="atLeast"/></w:trPr>'
               '<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="%d"/><w:tcBorders><w:top w:val="none" w:color="FFFFFF" w:sz="0"/>'
               '<w:left w:val="none" w:color="FFFFFF" w:sz="0"/><w:bottom w:val="none" w:color="FFFFFF" w:sz="0"/>'
               '<w:right w:val="single" w:color="BFBFBF" w:sz="4"/></w:tcBorders>'
               '<w:tcMar><w:top w:type="dxa" w:w="100"/><w:left w:type="dxa" w:w="100"/><w:bottom w:type="dxa" w:w="100"/><w:right w:type="dxa" w:w="100"/></w:tcMar>'
               '<w:vAlign w:val="center"/></w:tcPr>%s</w:tc>'
               '<w:tc><w:tcPr><w:tcW w:type="dxa" w:w="%d"/><w:tcBorders>%s</w:tcBorders>'
               '<w:tcMar><w:top w:type="dxa" w:w="100"/><w:left w:type="dxa" w:w="140"/><w:bottom w:type="dxa" w:w="100"/><w:right w:type="dxa" w:w="100"/></w:tcMar>'
               '<w:vAlign w:val="top"/></w:tcPr>%s</w:tc></w:tr></w:tbl>') % (
            PAGE_W, NOB, LEFT_W, RIGHT_W, LEFT_W, left, RIGHT_W, NOB, right)
    brk = "" if first_page else p('<w:r><w:rPr><w:sz w:val="2"/><w:szCs w:val="2"/></w:rPr><w:t xml:space="preserve"></w:t></w:r>',
                                  (0, 0), page_break=True)
    return brk + tbl


# =================================================================== FRONT / BACK
def heading1(doc, text, page_break=False):
    return p('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(H1_SZ, True, False, NAVY), esc(text)), (0, 160),
             style="Heading1", page_break=page_break, keep_next=True)


def front_xml(doc, meta, num_ids):
    x = p('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(48, True, False, NAVY),
          esc("%s: %s" % (meta.get("course", ""), meta.get("title", "")))), (0, 120))
    x += p('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(34, True),
          esc("Lecture %s notes, %s" % (meta.get("lecture", ""), meta.get("date", "")))), (0, 160))
    x += p('<w:r>%s<w:t xml:space="preserve">Topics: </w:t></w:r>' % rpr(NOTE_SZ, True) +
           runs_xml(doc, parse_inline(str(meta.get("topics", ""))), NOTE_SZ), (0, 160))
    x += p('<w:r>%s<w:t xml:space="preserve">Sources</w:t></w:r>' % rpr(NOTE_SZ, True), (0, 60))
    rows = [["File", "Range used", "Role"]] + [[c.strip() for c in str(s).split("|")] for s in meta.get("sources", [])]
    x += table_xml(doc, rows, PAGE_W, DEF_SZ)
    x += heading1(doc, "How to use these notes")
    howto = [
        "Each page shows a **slide on the left** and the **notes for that slide on the right**, in the order things happened in class.",
        "When a slide's notes run long, the slide repeats on the next page marked **(continued)**.",
        "Group work, videos, presentations and discussions have their own headed blocks where they happened.",
        "Each topic ends with a **Topic wrap-up** beside its last slide: how to recognize the problem, numbered steps, a check, and a worked example.",
    ]
    howto += [str(h) for h in meta.get("howto", [])]
    howto += [
        "Examples are the professor's own unless marked *constructed*.",
        "**Amber boxes** = flagged as important (exam, homework, repeated or stressed).",
        "@@RED@@",
        "The contents page fills in when the file is opened in Word; if it looks blank, press Ctrl+A then F9.",
    ]
    for h in howto:
        if h == "@@RED@@":
            runs = ('<w:r>%s<w:t xml:space="preserve">BOLD RED CAPITALS</w:t></w:r>' % rpr(NOTE_SZ, True, False, RED) +
                    runs_xml(doc, parse_inline(" = something that could not be made out or confirmed, or where what was said "
                                               "differed from the slide, ending with the AI notetaker's best guess where one applies. "
                                               "All of them are also listed under Open questions at the end."), NOTE_SZ))
        else:
            runs = runs_xml(doc, parse_inline(h), NOTE_SZ)
        x += p(runs, (0, 40), style="ListParagraph",
               extra_ppr='<w:numPr><w:ilvl w:val="0"/><w:numId w:val="%d"/></w:numPr>' % num_ids["bullet"])
    # contents
    x += heading1(doc, "Contents", page_break=True)
    x += ('<w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r><w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
          '<w:r><w:fldChar w:fldCharType="separate"/></w:r><w:r>%s<w:t>Press Ctrl+A then F9 to fill in the contents.</w:t></w:r>'
          '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>') % rpr(NOTE_SZ, False, True, GREY)
    return x


def sect(cols=1, last=False, first=False):
    c = '<w:cols w:space="216" w:num="4" w:sep="1"/>' if cols == 4 else '<w:cols w:num="1"/>'
    t = "" if first else '<w:type w:val="nextPage"/>'
    return ('<w:sectPr><w:footerReference w:type="default" r:id="rIdFtr"/>%s<w:pgSz w:w="15840" w:h="12240" w:orient="landscape"/>'
            '<w:pgMar w:top="648" w:right="720" w:bottom="648" w:left="720" w:header="300" w:footer="300" w:gutter="0"/>%s'
            '<w:docGrid w:linePitch="360"/></w:sectPr>') % (t, c)


def sect_para(s):
    return '<w:p><w:pPr><w:spacing w:before="0" w:after="0"/>%s</w:pPr></w:p>' % s


def back_xml(doc, back, markers, num_ids, warn):
    x = ""
    for title, lines in back.get("important", []):
        x += heading1(doc, title, page_break=True)
        ctx = dict(where=title, warn=warn, wide=True)
        for b in parse_blocks(lines, ctx):
            x += table_xml(doc, b.rows, PAGE_W, DEF_SZ) if b.kind == "table" else block_xml(doc, b, PAGE_W, num_ids=num_ids)
    for title, lines in back.get("extra", []):
        x += heading1(doc, title, page_break=True)
        ctx = dict(where=title, warn=warn, wide=True)
        bl = parse_blocks(lines, ctx)
        assign_lists(doc, bl)
        for b in bl:
            x += block_xml(doc, b, PAGE_W, num_ids=num_ids)
    cheat = back.get("cheat", [])
    if cheat:
        x += sect_para(sect(1, first=True))           # end of main section
        x += p('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(28, True, False, NAVY), esc(cheat[0][0])), (0, 80),
               style="Heading1", keep_next=True)
        for topic, lines in cheat:
            ctx = dict(where="cheat sheet", warn=warn, cheat=True)
            blocks = parse_blocks(lines, ctx)
            if topic != cheat[0][0]:
                x += block_xml(doc, Block("h3", runs=parse_inline(topic)), CHEAT_COL_W, cheat=True)
            assign_lists(doc, blocks)
            for b in blocks:
                if b.kind == "para":
                    m = re.match(r"^(Solve:|Trap:|Traps:|Check:)\s*(.*)$", b.raw)
                    if m:
                        b.runs = [dict(text=m.group(1) + " ", b=True, i=False, math=None)] + parse_inline(m.group(2))
                x += block_xml(doc, b, CHEAT_COL_W, cheat=True, num_ids=num_ids)
            cheat_check(topic, lines, warn)
        x += sect_para(sect(4))
    if markers:
        x += heading1(doc, "Open questions", page_break=not cheat)
        for where, raw in markers:
            x += p(runs_xml(doc, parse_inline("%s: %s" % (where.upper(), raw)), NOTE_SZ, True, None, RED), (0, 80))
    final = sect(1, first=not cheat)
    return x, final


def cheat_check(topic, lines, warn):
    txt = topic + "\n" + "\n".join(lines)
    for pat, why in [(r"\bL\d{1,2}\b", "lecture number"), (r"\b[Ll]ecture\b", "'Lecture'"), (r"\b[Ss]lides?\b", "'slide'"),
                     (r"\b\d{1,2}:\d{2}\b", "timestamp")]:
        if re.search(pat, txt):
            warn.append("cheat sheet '%s': contains %s (cheat sheet must be topic-based and general)" % (topic, why))
    if topic.lower().startswith("common traps") is False and topic != "" and "Use when:" not in txt and \
            not topic.lower().startswith("cheat"):
        warn.append("cheat sheet '%s': missing 'Use when:' line" % topic)


# =================================================================== EQUATIONS
def build_equations(doc, workdir):
    from lxml import etree
    if not doc.eqs:
        return []
    md = []
    for latex, sz, display, b, c in doc.eqs:
        md.append(("$$%s$$" if display else "$%s$") % latex)
    mdp = os.path.join(workdir, "eqs.md")
    with open(mdp, "w") as f:
        f.write("\n\n".join(md) + "\n")
    dx = os.path.join(workdir, "eqs.docx")
    subprocess.run(["pandoc", mdp, "-o", dx], check=True)
    xml = zipfile.ZipFile(dx).read("word/document.xml")
    root = etree.fromstring(xml)
    M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    paras = root.findall(".//{%s}body/{%s}p" % (W, W))
    maths = []
    for para in paras:
        found = [e for e in para.iter("{%s}oMath" % M) if e.getparent().tag != "{%s}oMath" % M]
        # outermost oMath elements only
        outer = []
        for e in found:
            anc = e.getparent()
            nested = False
            while anc is not None:
                if anc.tag == "{%s}oMath" % M:
                    nested = True
                    break
                anc = anc.getparent()
            if not nested:
                outer.append(e)
        if len(outer) == 0:
            maths.append(None)       # pandoc failed: falls back
        else:
            maths.append(outer[0])
    if len(maths) != len(doc.eqs):
        die("equation count mismatch (%d vs %d); check for a '$' typo" % (len(maths), len(doc.eqs)))
    order_d = ["begChr", "sepChr", "endChr", "grow", "shp"]
    order_r = ["lit", "nor", "scr", "sty", "brk", "aln"]
    out = []
    for (latex, sz, display, bold, color), mth in zip(doc.eqs, maths):
        if mth is None:
            out.append(None)
            continue
        for dpr in mth.iter("{%s}dPr" % M):
            kids = list(dpr)
            kids.sort(key=lambda e: order_d.index(etree.QName(e).localname) if etree.QName(e).localname in order_d else 99)
            for e in kids:
                dpr.remove(e)
                dpr.append(e)
        for r in mth.iter("{%s}r" % M):
            mr = r.find("{%s}rPr" % M)
            if mr is not None:
                if mr.find("{%s}nor" % M) is not None and mr.find("{%s}sty" % M) is not None:
                    mr.remove(mr.find("{%s}sty" % M))
                kids = list(mr)
                kids.sort(key=lambda e: order_r.index(etree.QName(e).localname) if etree.QName(e).localname in order_r else 99)
                for e in kids:
                    mr.remove(e)
                    mr.append(e)
            for old in r.findall("{%s}rPr" % W):
                r.remove(old)
            wr = etree.SubElement(r, "{%s}rPr" % W)
            f = etree.SubElement(wr, "{%s}rFonts" % W)
            for a in ("ascii", "hAnsi", "cs"):
                f.set("{%s}%s" % (W, a), "Cambria Math")
            if bold:
                etree.SubElement(wr, "{%s}b" % W)
            if color:
                etree.SubElement(wr, "{%s}color" % W).set("{%s}val" % W, color)
            etree.SubElement(wr, "{%s}sz" % W).set("{%s}val" % W, str(sz))
            etree.SubElement(wr, "{%s}szCs" % W).set("{%s}val" % W, str(sz))
            r.remove(wr)
            idx = 1 if mr is not None else 0
            r.insert(idx, wr)
        out.append(etree.tostring(mth, encoding="unicode"))
    return out


def insert_equations(body, doc, omml):
    for i, (latex, sz, display, bold, color) in enumerate(doc.eqs):
        ph = "@@EQ%d@@" % i
        om = omml[i] if i < len(omml) else None
        if om is None:
            rep = '<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(sz - 4, bold, False, color, True), esc(latex))
            print("WARN: equation fell back to monospace: %s" % latex)
        elif display:
            rep = None
        else:
            rep = om
        if display and om is not None:
            # replace whole paragraph run with oMathPara
            body = body.replace('<w:r><w:t>%s</w:t></w:r>' % ph,
                                '<m:oMathPara><m:oMathParaPr><m:jc m:val="center"/></m:oMathParaPr>%s</m:oMathPara>' % om, 1)
        else:
            body = body.replace('<w:r><w:t>%s</w:t></w:r>' % ph, rep, 1)
    if "@@EQ" in body:
        die("leftover equation placeholder")
    return body


# =================================================================== PACKAGE
NS = ('xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" '
      'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture" '
      'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" mc:Ignorable="w14"')

STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/><w:sz w:val="30"/><w:szCs w:val="30"/><w:lang w:val="en-CA"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:color w:val="1F3864"/><w:sz w:val="40"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:color w:val="1F3864"/><w:sz w:val="36"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:color w:val="1F3864"/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Footer"><w:name w:val="footer"/><w:basedOn w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="TOC1"><w:name w:val="toc 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:spacing w:before="60" w:after="20"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TOC2"><w:name w:val="toc 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:pPr><w:ind w:left="240"/></w:pPr><w:rPr><w:sz w:val="22"/></w:rPr></w:style>
<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:rPr><w:color w:val="0563C1"/><w:u w:val="single"/></w:rPr></w:style>
</w:styles>'''


def numbering_xml(doc):
    ab = ('<w:abstractNum w:abstractNumId="2"><w:multiLevelType w:val="hybridMultilevel"/>'
          '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u2022"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="280" w:hanging="220"/></w:pPr></w:lvl>'
          '<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u2013"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="540" w:hanging="200"/></w:pPr></w:lvl></w:abstractNum>'
          '<w:abstractNum w:abstractNumId="3"><w:multiLevelType w:val="hybridMultilevel"/>'
          '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="340" w:hanging="300"/></w:pPr></w:lvl></w:abstractNum>'
          '<w:abstractNum w:abstractNumId="4"><w:multiLevelType w:val="hybridMultilevel"/>'
          '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u2022"/><w:lvlJc w:val="left"/><w:pPr><w:tabs><w:tab w:val="num" w:pos="160"/></w:tabs><w:ind w:left="160" w:hanging="140"/></w:pPr><w:rPr><w:sz w:val="16"/></w:rPr></w:lvl>'
          '<w:lvl w:ilvl="1"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u2013"/><w:lvlJc w:val="left"/><w:pPr><w:tabs><w:tab w:val="num" w:pos="300"/></w:tabs><w:ind w:left="300" w:hanging="140"/></w:pPr><w:rPr><w:sz w:val="16"/></w:rPr></w:lvl></w:abstractNum>')
    nums = '<w:num w:numId="2"><w:abstractNumId w:val="2"/></w:num><w:num w:numId="4"><w:abstractNumId w:val="4"/></w:num>'
    for nid, a, start in doc.nums:
        nums += ('<w:num w:numId="%d"><w:abstractNumId w:val="%d"/><w:lvlOverride w:ilvl="0"><w:startOverride w:val="%d"/>'
                 '</w:lvlOverride></w:num>') % (nid, a, start)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            + ab + nums + "</w:numbering>")


def footer_xml(text):
    r = '<w:rPr><w:color w:val="808080"/><w:sz w:val="16"/><w:szCs w:val="16"/></w:rPr>'
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr %s><w:p><w:pPr><w:pStyle w:val="Footer"/><w:jc w:val="center"/></w:pPr>'
            '<w:r>%s<w:t xml:space="preserve">%s \u00b7 page </w:t></w:r><w:r>%s<w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r>%s<w:instrText xml:space="preserve"> PAGE </w:instrText></w:r><w:r>%s<w:fldChar w:fldCharType="separate"/></w:r>'
            '<w:r>%s<w:t>1</w:t></w:r><w:r>%s<w:fldChar w:fldCharType="end"/></w:r></w:p></w:ftr>') % (NS, r, esc(text), r, r, r, r, r)


def write_package(out, body_xml, final_sect, doc, meta):
    files = {}
    files["word/document.xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document %s><w:body>%s%s</w:body></w:document>'
                                  % (NS, body_xml, final_sect))
    files["word/styles.xml"] = STYLES
    files["word/numbering.xml"] = numbering_xml(doc)
    files["word/settings.xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
                                  'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><w:defaultTabStop w:val="720"/><w:updateFields w:val="true"/>'
                                  '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>'
                                  '<m:mathPr><m:mathFont m:val="Cambria Math"/><m:dispDef/></m:mathPr></w:settings>')
    footer = meta.get("footer") or "%s \u00b7 Lecture %s" % (meta.get("course", ""), meta.get("lecture", ""))
    files["word/footer1.xml"] = footer_xml(footer)
    rels = ['<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>',
            '<Relationship Id="rIdNum" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>',
            '<Relationship Id="rIdSet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>',
            '<Relationship Id="rIdFtr" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>']
    media = {}
    for rid, path in doc.images:
        name = "media/%s.png" % rid
        media["word/" + name] = path
        rels.append('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="%s"/>' % (rid, name))
    files["word/_rels/document.xml.rels"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                             + "".join(rels) + "</Relationships>")
    files["_rels/.rels"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
                            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
    title = "%s Lecture %s notes" % (meta.get("course", ""), meta.get("lecture", ""))
    files["docProps/core.xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                                  'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                                  '<dc:title>%s</dc:title><dc:subject>%s</dc:subject><dc:creator>%s</dc:creator></cp:coreProperties>'
                                  % (esc(title), esc(str(meta.get("topics", ""))[:250]), esc(str(meta.get("author", "")))))
    files["docProps/app.xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
                                 '<Application>Microsoft Office Word</Application></Properties>')
    files["[Content_Types].xml"] = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                                    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                                    '<Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
                                    '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                                    '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                                    '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                                    '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
                                    '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
                                    '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                                    '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>')
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for n in ["[Content_Types].xml", "_rels/.rels"] + [k for k in files if k not in ("[Content_Types].xml", "_rels/.rels")]:
            z.writestr(n, files[n])
        for n, path in media.items():
            z.write(path, n)


# =================================================================== CHECKS
BANNED = [r"\btranscri\w*", r"\brecord(ing|ed)\b", r"\baudio\b", r"\btimestamps?\b", r"\bplayback\b",
          r"speech-to-text", r"\bcaption file\b", r"\bmic\b", r"\bminute \d+", r"\bat minute\b"]


def content_checks(text, pages, nslides, markers, warn):
    errs = []
    for ln_no, ln in enumerate(text.split("\n"), 1):
        if "\u2014" in ln:
            errs.append("line %d: em dash (not allowed): %s" % (ln_no, ln.strip()[:80]))
        for pat in BANNED:
            if re.search(pat, ln, re.I):
                warn.append("line %d: possible recording reference %r: %s" % (ln_no, re.search(pat, ln, re.I).group(0), ln.strip()[:80]))
        if re.search(r"(?<![\d.])\b\d{1,2}:\d{2}\b", re.sub(r"\$[^$]*\$", "", ln)):
            warn.append("line %d: looks like a clock time/timestamp: %s" % (ln_no, ln.strip()[:80]))
    seen = {pg["slide"] for pg in pages if pg["kind"] == "slide"}
    missing = [n for n in range(1, nslides + 1) if n not in seen]
    extra = sorted(n for n in seen if n > nslides or n < 1)
    if extra:
        errs.append("page headings name slides the deck does not have (deck has %d): %s" % (nslides, extra))
    if missing:
        errs.append("slides with no page (add a page, or one saying 'Not covered in lecture'): %s" % missing)
    for where, raw in markers:
        if not re.match(r"^(UNCLEAR IN LECTURE|SLIDE AND LECTURE DISAGREE|SOURCES DISAGREE|NOT LEGIBLE ON SLIDE|NEEDS CONFIRMATION):", raw):
            warn.append("%s: red marker should start with a step 8 label: %s" % (where, raw[:60]))
        if re.match(r"^(UNCLEAR IN LECTURE|NOT LEGIBLE ON SLIDE|NEEDS CONFIRMATION):", raw) and "BEST GUESS" not in raw:
            warn.append("%s: marker lacks AI NOTETAKER'S BEST GUESS: %s" % (where, raw[:60]))
        words = re.findall(r"[A-Za-z]{4,}", re.sub(r"\$[^$]*\$|`[^`]*`", "", raw))
        if any(w != w.upper() for w in words):
            warn.append("%s: marker words should be CAPITALS: %s" % (where, raw[:60]))
    return errs


def render(out, rdir, budget):
    import pymupdf as fitz
    os.makedirs(rdir, exist_ok=True)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", rdir, out],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    pdf = os.path.join(rdir, os.path.splitext(os.path.basename(out))[0] + ".pdf")
    if not os.path.exists(pdf):
        print("WARN: render failed")
        return
    d = fitz.open(pdf)
    files, tall = [], []
    for i, pg in enumerate(d, 1):
        f = os.path.join(rdir, "p%03d.png" % i)
        pg.get_pixmap(dpi=50).save(f)
        files.append(f)
        W = pg.rect.width
        ys = [b[3] for b in pg.get_text("blocks") if b[0] > W * 0.66 and b[3] < pg.rect.height - 30]
        if ys and max(ys) - 32.4 > budget + 15:
            tall.append((i, int(max(ys) - 32.4)))
    sheets = contact_sheets(files, os.path.join(rdir, "sheet"))
    print("Rendered %d pages -> %s" % (d.page_count, ", ".join(sheets)))
    print("(LibreOffice has no Math module here: equations show as gaps; Word draws them taller.)")
    for i, h in tall:
        print("WARN: page %d right column reaches ~%dpt (limit ~%d): split it with '---'" % (i, h, budget))


# =================================================================== BUILD
def cmd_build(a):
    global NOTES_DIR
    NOTES_DIR = os.path.dirname(os.path.abspath(a.notes))
    text = open(a.notes, encoding="utf-8").read()
    meta, body = parse_front(text)
    warn = []
    pages, back = parse_body(body, meta, warn)
    slides_dir = a.slides or meta.get("slides_dir", "slides")
    nslides = len(glob.glob(os.path.join(slides_dir, "c*.png"))) if os.path.isdir(slides_dir) else 0
    if a.nslides:
        nslides = a.nslides
    doc = Doc()
    num_ids = {"bullet": 2, "cheat_bullet": 4}
    markers = []
    for pg in pages:
        where = ("Slide %d" % pg["slide"]) if pg["kind"] == "slide" else pg["title"]
        for b in pg["blocks"]:
            if b.kind == "red":
                markers.append((where, b.raw))
    errs = content_checks(text, pages, nslides, markers, warn)
    if errs:
        for w in warn:
            print("WARN:", w)
        for e in errs:
            print("ERROR:", e)
        if not a.force:
            sys.exit("Fix the errors above (or pass --force).")
    xml = front_xml(doc, meta, num_ids)
    npages = 0
    first = False
    for pg in pages:
        width = WIDE_TEXT_PT if pg["kind"] == "wide" else RIGHT_TEXT_PT
        chunks = paginate(pg, a.budget, width, warn)
        for idx, ch in enumerate(chunks):
            xml += page_xml(doc, pg, ch, idx, nslides, slides_dir, num_ids, first)
            first = False
            npages += 1
    bx, final = back_xml(doc, back, markers, num_ids, warn)
    xml += bx
    work = tempfile.mkdtemp(prefix="notes_")
    omml = build_equations(doc, work)
    xml = insert_equations(xml, doc, omml)
    write_package(a.out, xml, final, doc, meta)
    # validate
    val = None
    for cand in ["/mnt/skills/public/docx/scripts/office/validate.py"] + glob.glob("/root/.claude/skills/**/docx/scripts/office/validate.py", recursive=True):
        if os.path.exists(cand):
            val = cand
            break
    if val:
        r = subprocess.run([sys.executable, val, a.out], capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().split("\n")[-3:]
        print("validate.py:", " | ".join(tail))
    for w in warn:
        print("WARN:", w)
    print("Built %s: %d lecture pages from %d page entries, %d equations, %d slide images, %d problem markers."
          % (a.out, npages, len(pages), len(doc.eqs), len(doc.images), len(markers)))
    if a.render:
        render(a.out, a.render, a.budget)
    shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("deck")
    s.add_argument("-o", "--out", default="slides")
    s.add_argument("--dpi", type=int, default=220)
    b = sub.add_parser("build")
    b.add_argument("notes")
    b.add_argument("--slides", help="folder with cN.png from scan (default: slides_dir in front matter, else ./slides)")
    b.add_argument("-o", "--out", required=True)
    b.add_argument("--budget", type=float, default=460, help="right-column height budget in pt (default 460)")
    b.add_argument("--nslides", type=int, help="override deck slide count M")
    b.add_argument("--render", help="folder for PDF + page contact sheets")
    b.add_argument("--force", action="store_true")
    a = ap.parse_args()
    {"scan": cmd_scan, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    main()
