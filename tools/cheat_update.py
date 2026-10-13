#!/usr/bin/env python3
"""
cheat_update.py: change the cheat sheet of an EXISTING notes .docx in place (keeps the user's hand
edits; no rebuild): add Variables lists after equation groups, design figures, new entries and
extra lines inside an entry.

  python3 cheat_update.py NOTES.docx spec.yaml OUT.docx

Run cheat_dump.py first to see each entry's equation ordinals (EQ0, EQ1, ...). Headings in the spec
match by prefix. spec.yaml:

  vars:                         # after equation EQk of the entry (the last EQ of a group)
    "Passive LRC block":
      3: [["|p|", "pole magnitude"], ["θ", "pole angle from the positive real axis"]]
  figs:                         # inserted right under the entry's "Use when:" line
    "Passive LRC block": figs/lrc.png
  extra:                        # extra items after EQk (and after any Variables there)
    "Gain and phase margin":
      1: [["eq", "GM = \\frac{1}{|AB|}"], ["p", [["Shortcut: ", true], ["text", false]]]]
  new:                          # new entries, inserted before the entry whose heading starts with `before`
    - before: "Common traps"
      heading: "Effects of negative feedback (summary)"
      usewhen: '"what does negative feedback do"'
      fig: figs/compare.png     # optional
      items: [["eq", "D = 1 + A_{dc}B"], ["vars", [["D", "amount of feedback"]]], ["p", [["Gain: ", true], ["÷D", false]]]]

Symbols in vars and p text: X_{sub} / X_s gives a subscript, X^{sup} a superscript.
Text size and column width are read from the document. Equations go through pandoc (OMML).
"""
import sys, os, re, copy, subprocess, shutil, zipfile, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml
from lxml import etree
from PIL import Image
from cheat_common import ptext, region, kind, entries, NS, W, M

src, specp, out = sys.argv[1:4]
spec = yaml.safe_load(open(specp, encoding='utf-8')) or {}
w = lambda t: '{%s}%s' % (W, t)
W14 = 'http://schemas.microsoft.com/office/word/2010/wordml'
DECL = ('xmlns:w="%s" xmlns:m="%s" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"') % (W, M)
X = lambda s: etree.fromstring('<root %s>%s</root>' % (DECL, s))[0]
esc = lambda s: s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

work = tempfile.mkdtemp(prefix='cheatupd_')
with zipfile.ZipFile(src) as z:
    names = z.namelist(); z.extractall(work)
docp = os.path.join(work, 'word/document.xml')
tree = etree.parse(docp); body = tree.getroot().find('w:body', NS)
kids, s0, e0 = region(body)
ents = entries(kids, s0, e0)

# ---- text size and column width from the document
from collections import Counter
_sz = Counter(int(r.get(w('val'))) for i in range(s0 + 1, e0) if kind(kids[i]) == 'T'
              for r in kids[i].findall('.//w:r/w:rPr/w:sz', NS))
SZ = _sz.most_common(1)[0][0] if _sz else 16   # body text size of the cheat sheet (half-points)
VSZ = SZ - 2 if SZ >= 16 else SZ - 1
COLW = 2.3
for sp in [k.find('.//w:sectPr', NS) for k in kids[s0:]] + [body.find('w:sectPr', NS)]:
    if sp is None: continue
    c = sp.find('w:cols', NS)
    if c is not None and c.get(w('num')) and int(c.get(w('num'))) > 1:
        n = int(c.get(w('num'))); space = int(c.get(w('space')) or 0)
        pg = sp.find('w:pgSz', NS); mar = sp.find('w:pgMar', NS)
        avail = int(pg.get(w('w'))) - int(mar.get(w('left'))) - int(mar.get(w('right')))
        COLW = ((avail - (n - 1) * space) / n - 60) / 1440.0
        break

def rpr(sz, b=False, color=None, vert=None):
    x = '<w:rPr>' + ('<w:b/><w:bCs/>' if b else '')
    if color: x += '<w:color w:val="%s"/>' % color
    x += '<w:sz w:val="%d"/><w:szCs w:val="%d"/>' % (sz, sz)
    if vert: x += '<w:vertAlign w:val="%s"/>' % vert
    return x + '</w:rPr>'

def rich(text, sz, b=False, color=None):
    out = []
    for m in re.finditer(r'([_^])(\{[^}]*\}|[A-Za-z0-9\u0080-￿′+\-−]+)|([^_^]+|[_^])', text):
        if m.group(1):
            t = m.group(2); t = t[1:-1] if t.startswith('{') else t
            out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(sz, b, color, 'subscript' if m.group(1) == '_' else 'superscript'), esc(t)))
        else:
            out.append('<w:r>%s<w:t xml:space="preserve">%s</w:t></w:r>' % (rpr(sz, b, color), esc(m.group(3))))
    return ''.join(out)

def para(inner, after=30, before=0, ind=None, jc=None, keep=False, line=228):
    p = '<w:p><w:pPr>' + ('<w:keepNext/>' if keep else '')
    p += '<w:spacing w:before="%d" w:after="%d" w:line="%d" w:lineRule="auto"/>' % (before, after, line)
    if ind: p += ind
    if jc: p += '<w:jc w:val="%s"/>' % jc
    return X(p + '</w:pPr>' + inner + '</w:p>')

def vars_block(items):
    g = '404040'
    els = [para('<w:r>%s<w:t>Variables</w:t></w:r>' % rpr(VSZ, True, g), after=0, before=10, keep=True)]
    for k, (sym, desc) in enumerate(items):
        inner = ('<w:r>%s<w:t xml:space="preserve">• </w:t></w:r>' % rpr(VSZ, False, g) + rich(str(sym), VSZ, True, g) +
                 '<w:r>%s<w:t xml:space="preserve">: </w:t></w:r>' % rpr(VSZ, False, g) + rich(str(desc), VSZ, False, g))
        els.append(para(inner, after=30 if k == len(items) - 1 else 0, ind='<w:ind w:left="160" w:hanging="100"/>'))
    return els

EQS = []
def items_xml(items):
    els = []
    for k, v in items:
        if k == 'eq': EQS.append(v); els.append(('EQ', len(EQS) - 1))
        elif k == 'p': els.append(para(''.join(rich(t, SZ, b) for t, b in v)))
        elif k == 'vars': els += vars_block(v)
        else: raise SystemExit('unknown item kind %r' % k)
    return els

def build_eqs():
    if not EQS: return []
    t = tempfile.mkdtemp()
    open(t + '/e.md', 'w', encoding='utf-8').write('\n\n'.join('$$%s$$' % l for l in EQS))
    subprocess.run(['pandoc', t + '/e.md', '-o', t + '/e.docx'], check=True)
    with zipfile.ZipFile(t + '/e.docx') as z: x = etree.fromstring(z.read('word/document.xml'))
    shutil.rmtree(t); res = []
    for omp in x.iter('{%s}oMathPara' % M):
        for r in omp.iter('{%s}r' % M):
            for o in r.findall(w('rPr')): r.remove(o)
            wr = X('<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/><w:sz w:val="%d"/><w:szCs w:val="%d"/></w:rPr>' % (SZ, SZ))
            mr = r.find('{%s}rPr' % M)
            (mr.addnext(wr) if mr is not None else r.insert(0, wr))
        p = para('', before=20, after=40, jc='center', line=240); p.append(omp); res.append(p)
    return res

# ---- images
rels_p = os.path.join(work, 'word/_rels/document.xml.rels'); rels = etree.parse(rels_p)
ct_p = os.path.join(work, '[Content_Types].xml'); ct = etree.parse(ct_p)
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
if not any((d.get('Extension') or '').lower() == 'png' for d in ct.getroot()):
    ct.getroot().insert(0, etree.Element('{%s}Default' % CT, Extension='png', ContentType='image/png'))
os.makedirs(os.path.join(work, 'word/media'), exist_ok=True)
nid = [max([int(x) for x in re.findall(rb'docPr id="(\d+)"', open(docp, 'rb').read())] + [0]) + 1000]
def img_para(png):
    if not os.path.exists(png): raise SystemExit('figure not found: %s' % png)
    n = nid[0]; nid[0] += 1
    name = 'csfig%d.png' % n; shutil.copy(png, os.path.join(work, 'word/media', name)); rid = 'rIdCSF%d' % n
    etree.SubElement(rels.getroot(), '{http://schemas.openxmlformats.org/package/2006/relationships}Relationship',
                     Id=rid, Type='http://schemas.openxmlformats.org/officeDocument/2006/relationships/image', Target='media/' + name)
    wpx, hpx = Image.open(png).size; cx = int(COLW * 914400); cy = int(cx * hpx / wpx)
    d = ('<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="%d" cy="%d"/>'
         '<wp:docPr id="%d" name="%s" descr="Cheat sheet figure"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
         '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic><pic:nvPicPr>'
         '<pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
         '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="%d" cy="%d"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
         '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>') % (cx, cy, n, name, n, name, rid, cx, cy)
    return para(d, before=20, after=40, jc='center', line=240)

def strip_ids(el):
    for e in el.iter():
        for a in list(e.attrib):
            if a.startswith('{%s}' % W14) or 'rsid' in a: del e.attrib[a]
    return el

def find(prefix):
    for ent in ents:
        if ent[0].startswith(prefix): return ent
    raise SystemExit('no entry heading starts with %r (run cheat_dump.py)' % prefix)

def eq_at(ent, k):
    eqs = [i for i in ent[2] if kind(kids[i]) == 'EQ']
    if k >= len(eqs): raise SystemExit('%r has only %d equations (EQ%d asked)' % (ent[0], len(eqs), k))
    return kids[eqs[k]]

plan = []
anchors = {}
for head, m in (spec.get('vars') or {}).items():
    ent = find(head)
    for k, items in m.items():
        anchors[(head, int(k))] = vars_block(items)
for head, m in (spec.get('extra') or {}).items():
    for k, items in m.items():
        anchors.setdefault((head, int(k)), []).extend(items_xml(items))
for (head, k), els in anchors.items():
    plan.append((eq_at(find(head), k), els))
for head, png in (spec.get('figs') or {}).items():
    ent = find(head)
    u = next((kids[i] for i in ent[2][:1] if kind(kids[i]) == 'U'), kids[ent[1]])
    plan.append((u, [img_para(png)]))
H_TPL = kids[ents[0][1]]
U_TPL = next(kids[i] for _, hi, idx in ents for i in idx[:1] if kind(kids[i]) == 'U')
for ne in spec.get('new') or []:
    h = strip_ids(copy.deepcopy(H_TPL)); rs = h.findall(w('r'))
    for r in rs[1:]: h.remove(r)
    for t in rs[0].findall(w('t'))[1:]: rs[0].remove(t)
    rs[0].find(w('t')).text = ne['heading']
    u = strip_ids(copy.deepcopy(U_TPL)); rs = u.findall(w('r'))
    for r in rs[2:]: u.remove(r)
    t = rs[1].find(w('t')); t.text = ne['usewhen']; t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    els = [h, u] + ([img_para(ne['fig'])] if ne.get('fig') else []) + items_xml(ne.get('items') or [])
    plan.append((kids[find(ne['before'])[1]].getprevious(), els))

eqs = build_eqs()
for anchor, els in plan:
    last = anchor
    for el in els:
        if isinstance(el, tuple): el = eqs[el[1]]
        last.addnext(el); last = el
for f, t in ((docp, tree), (rels_p, rels), (ct_p, ct)):
    t.write(f, xml_declaration=True, encoding='UTF-8', standalone=True)
tmpout = out + '.tmp'
with zipfile.ZipFile(tmpout, 'w', zipfile.ZIP_DEFLATED) as z:
    for n in names: z.write(os.path.join(work, n), n)
    for d, _, fs in os.walk(work):
        for f in fs:
            rel = os.path.relpath(os.path.join(d, f), work).replace(os.sep, '/')
            if rel not in names: z.write(os.path.join(d, f), rel)
os.replace(tmpout, out); shutil.rmtree(work)
print('wrote %s: %d Variables/extra anchors, %d figures, %d new entries, %d equations (text %d half-points, column %.2f in)'
      % (out, len(anchors), len(spec.get('figs') or {}), len(spec.get('new') or []), len(EQS), SZ, COLW))
