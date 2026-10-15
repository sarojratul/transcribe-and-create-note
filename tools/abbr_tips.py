"""abbr_tips.py: add hover tips (ScreenTips) to abbreviations in a notes .docx built by build_notes.py.

usage: python3 abbr_tips.py IN.docx DICT.json OUT.docx [--dry]
DICT.json maps whole-word keys to tips ("Full name: purpose in this document.").
Skips: headings, title page and contents (everything before the Contents heading), Open questions,
red marker runs, equations (OMML), runs already inside a hyperlink. Keeps each run's rPr unchanged.
"""
import sys, re, json, copy, zipfile, shutil, collections
from lxml import etree
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
ns = {"w": W}
q = lambda t: "{%s}%s" % (W, t)

def ptext(p):
    return "".join(t.text or "" for t in p.iter(q("t")))

def main():
    src, dj, out = sys.argv[1:4]
    dry = "--dry" in sys.argv
    D = json.load(open(dj))
    keys = sorted(D, key=len, reverse=True)
    pat = re.compile("(?<![A-Za-z0-9_])(%s)(?![A-Za-z0-9_])" % "|".join(re.escape(k) for k in keys))
    zin = zipfile.ZipFile(src)
    root = etree.fromstring(zin.read("word/document.xml"))
    body = root.find(q("body"))
    paras = list(body.iter(q("p")))
    before = [ptext(p) for p in paras]
    start, end = 0, len(paras)
    for i, p in enumerate(paras):
        st = p.find("w:pPr/w:pStyle", ns)
        if st is not None and st.get(q("val")) == "Heading1":
            t = ptext(p).strip()
            if t == "Contents" and start == 0:
                start = i + 1
            if t == "Open questions":
                end = i
    counts = collections.Counter()
    for p in paras[start:end]:
        st = p.find("w:pPr/w:pStyle", ns)
        if st is not None and st.get(q("val")) in ("Heading1", "Heading2", "Heading3"):
            continue
        shd = p.find("w:pPr/w:shd", ns)
        if shd is not None and (shd.get(q("fill")) or "").upper() == "D9E2F3":
            continue                               # cheat sheet topic bars
        if any("TOC" in (x.text or "") for x in p.iter(q("instrText"))):
            continue
        for r in [c for c in p if c.tag == q("r")]:
            kids = [c for c in r if c.tag != q("rPr")]
            if len(kids) != 1 or kids[0].tag != q("t"):
                continue
            col = r.find("w:rPr/w:color", ns)
            if col is not None and (col.get(q("val")) or "").upper() == "FF0000":
                continue                           # red markers
            text = kids[0].text or ""
            ms = []
            for m in pat.finditer(text):
                ms.append((m.start(), m.end(), m.group(1)))
            if not ms:
                continue
            ms.sort()
            for _, _, k in ms:
                counts[k] += 1
            if dry:
                continue
            pieces, pos = [], 0
            rpr = r.find(q("rPr"))
            def mk(s, tip=None):
                nr = etree.Element(q("r"))
                if rpr is not None:
                    nr.append(copy.deepcopy(rpr))
                t = etree.SubElement(nr, q("t"))
                t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                t.text = s
                if tip is None:
                    return nr
                h = etree.Element(q("hyperlink"))
                h.set(q("anchor"), "_abbr"); h.set(q("tooltip"), tip); h.set(q("history"), "0")
                h.append(nr)
                return h
            for a, b, k in ms:
                if a > pos:
                    pieces.append(mk(text[pos:a]))
                pieces.append(mk(text[a:b], D[k]))
                pos = b
            if pos < len(text):
                pieces.append(mk(text[pos:]))
            parent = r.getparent(); idx = parent.index(r)
            parent.remove(r)
            for j, pc in enumerate(pieces):
                parent.insert(idx + j, pc)
    print("total tips:", sum(counts.values()), "distinct:", len(counts))
    print(dict(sorted(counts.items())))
    print("keys never matched:", sorted(set(D) - set(counts)))
    if dry:
        return
    after = [ptext(p) for p in body.iter(q("p"))]
    bad=[(i,a[:60],b[:60]) for i,(a,b) in enumerate(zip(before,after)) if a!=b]
    print(len(before),len(after),bad[:3])
    assert before == after, "paragraph text changed"
    zout = zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED)
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename == "word/document.xml":
            data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
        zout.writestr(it, data)
    zout.close()
    print("wrote", out, "paragraphs", len(after))

main()
