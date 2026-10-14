#!/usr/bin/env python3
"""
cs4_post.py: post-processor for the 4-column exam cheat sheet (cheatsheet-generator skill), any course.

  pandoc sheet.md -f markdown -o raw.docx
  python3 cs4_post.py raw.docx OUT.docx

Turns pandoc output into the house style: US Letter landscape, 0.25 in margins, 4 columns with a
separator, Calibri, native bold Cambria Math equations (blue = provided formula list, dark green after a
`NEWX ` marker = added), red [units] (custom-style "Unit"), purple subscripts, orange superscripts,
navy-on-blue Topic bars, legend styles (LegBlue, LegGreen, LegRed, LegSub, LegSup, LegTopic).
Sizes: items under a `Formulas` label 7 pt, under `Variables and constants` 5.5 pt, everything else 6 pt
(the labels must be spelled exactly so). Tight list indents fit two-digit numbers. Needs lxml.
Also used to build fragments for cs4_edit.py (append / addblock).
"""

import os, sys, shutil, subprocess, copy
from lxml import etree

SRC = sys.argv[1]
OUT = sys.argv[2]
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
w = lambda t: '{%s}%s' % (W, t)
m = lambda t: '{%s}%s' % (M, t)
SZ = '12'          # half-points -> 6 pt (headers, labels, unit conversions, legend)
SZ_FORM = '14'     # Formulas section: 7 pt
SZ_VAR = '11'      # Variables and constants section: 5.5 pt
BLUE = '0000FF'
RED = 'FF0000'
GREEN = '006400'   # formulas not in the provided source list
SUBC = '9A00FF'    # bright purple subscripts
SUPC = 'B34700'    # burnt orange superscripts

work = SRC + '_x'
shutil.rmtree(work, ignore_errors=True)
os.makedirs(work)
subprocess.run(['unzip', '-oq', SRC, '-d', work], check=True)

def load(p):
    return etree.parse(os.path.join(work, p))

def save(t, p):
    t.write(os.path.join(work, p), xml_declaration=True, encoding='UTF-8', standalone=True)

def el(tag, **attrs):
    e = etree.Element(tag)
    for k, v in attrs.items():
        e.set(w(k) if not k.startswith('{') else k, v)
    return e

AFTER_SZ = ['highlight','u','effect','bdr','shd','fitText','vertAlign','rtl','cs','em','lang','eastAsianLayout','specVanish','oMath']
def add_sz(rp):
    for t in ('sz','szCs'):
        for o in rp.findall(w(t)):
            rp.remove(o)
    anchor = None
    for k in rp:
        if etree.QName(k).localname in AFTER_SZ:
            anchor = k; break
    for t in ('sz','szCs'):
        e = el(w(t), val=SZ)
        if anchor is not None: anchor.addprevious(e)
        else: rp.append(e)

PPR_ORDER = ['pStyle','keepNext','keepLines','pageBreakBefore','framePr','widowControl','numPr','suppressLineNumbers','pBdr','shd','tabs','suppressAutoHyphens','kinsoku','wordWrap','overflowPunct','topLinePunct','autoSpaceDE','autoSpaceDN','bidi','adjustRightInd','snapToGrid','spacing','ind','contextualSpacing','mirrorIndents','suppressOverlap','jc','textDirection','textAlignment','textboxTightWrap','outlineLvl','divId','cnfStyle','rPr','sectPr','pPrChange']
STYLE_ORDER = ['name','aliases','basedOn','next','link','autoRedefine','hidden','uiPriority','semiHidden','unhideWhenUsed','qFormat','locked','personal','personalCompose','personalReply','rsid','pPr','rPr','tblPr','trPr','tcPr','tblStylePr']
RPR_ORDER = ['rStyle','rFonts','b','bCs','i','iCs','caps','smallCaps','strike','dstrike','outline','shadow','emboss','imprint','noProof','snapToGrid','vanish','webHidden','color','spacing','w','kern','position','sz','szCs','highlight','u','effect','bdr','shd','fitText','vertAlign','rtl','cs','em','lang','eastAsianLayout','specVanish','oMath']
def sort_children(node, order):
    kids = list(node)
    kids.sort(key=lambda e: order.index(etree.QName(e).localname) if etree.QName(e).localname in order else len(order))
    for k in list(node): node.remove(k)
    for k in kids: node.append(k)
def clean_rpr(r):
    r.text = None
    for k in r: k.tail = None
    sort_children(r, RPR_ORDER)
DPR_ORDER = ['begChr','sepChr','endChr','grow','shp','ctrlPr']

def set_child(parent, tag, **attrs):
    for old in parent.findall(tag):
        parent.remove(old)
    e = el(tag, **attrs)
    parent.append(e)
    return e

# ---------- styles ----------
st = load('word/styles.xml')
root = st.getroot()
dd = root.find(w('docDefaults'))
rpr = dd.find(w('rPrDefault')).find(w('rPr'))
for o in rpr.findall(w('rFonts')):
    rpr.remove(o)
rpr.insert(0, el(w('rFonts'), ascii='Calibri', hAnsi='Calibri', cs='Calibri', eastAsia='Calibri'))
add_sz(rpr)
ppd = dd.find(w('pPrDefault'))
if ppd is None:
    ppd = etree.SubElement(dd, w('pPrDefault'))
ppr = ppd.find(w('pPr'))
if ppr is None:
    ppr = etree.SubElement(ppd, w('pPr'))
set_child(ppr, w('spacing'), before='0', after='0', line='228', lineRule='auto')

for s in root.findall(w('style')):
    sid = s.get(w('styleId'))
    for r in s.findall(w('rPr')):
        for t in ('sz', 'szCs'):
            for o in r.findall(w(t)):
                o.set(w('val'), SZ)
    if s.get(w('type')) == 'paragraph':
        p = s.find(w('pPr'))
        if p is None:
            p = etree.Element(w('pPr'))
            r = s.find(w('rPr'))
            (r.addprevious(p) if r is not None else s.append(p))
        for o in p.findall(w('spacing')):
            p.remove(o)
        if sid == 'Topic':
            p.append(el(w('keepNext')))
            bdr = el(w('pBdr')); p.append(bdr)
            bdr.append(el(w('bottom'), val='single', sz='4', space='1', color='1F3864'))
            p.append(el(w('shd'), val='clear', color='auto', fill='D9E2F3'))
            p.append(el(w('spacing'), before='60', after='20'))
        else:
            p.append(el(w('spacing'), before='0', after='0', line='228', lineRule='auto'))
    if sid in ('Topic', 'Unit'):
        r = s.find(w('rPr'))
        if r is None:
            r = etree.SubElement(s, w('rPr'))
        if sid == 'Topic':
            r.append(el(w('b'))); r.append(el(w('bCs')))
            r.append(el(w('color'), val='1F3864'))
        else:
            r.append(el(w('color'), val=RED))
        r.append(el(w('sz'), val=SZ)); r.append(el(w('szCs'), val=SZ))

# legend character styles
LEG = {'LegBlue': (BLUE, True), 'LegGreen': (GREEN, True), 'LegRed': (RED, False),
       'LegSub': (SUBC, True), 'LegSup': (SUPC, True), 'LegTopic': ('1F3864', True)}
for s in root.findall(w('style')):
    sid = s.get(w('styleId'))
    if sid in LEG:
        col, bold = LEG[sid]
        r = s.find(w('rPr'))
        if r is None:
            r = etree.SubElement(s, w('rPr'))
        if bold:
            r.append(el(w('b'))); r.append(el(w('bCs')))
        r.append(el(w('color'), val=col))
        if sid == 'LegTopic':
            r.append(el(w('shd'), val='clear', color='auto', fill='D9E2F3'))

for r_ in root.iter(w('rPr')):
    clean_rpr(r_)
for tc in root.iter(w('tcPr')):
    sort_children(tc, ['cnfStyle','tcW','gridSpan','hMerge','vMerge','tcBorders','shd','noWrap','tcMar','textDirection','tcFitText','vAlign','hideMark'])
for s_ in root.findall(w('style')):
    sort_children(s_, STYLE_ORDER)
    for pp in s_.findall(w('pPr')): sort_children(pp, PPR_ORDER)
save(st, 'word/styles.xml')

# ---------- numbering: tight indents, room for two-digit numbers ----------
nb = load('word/numbering.xml')
for lvl in nb.getroot().iter(w('lvl')):
    ilvl = int(lvl.get(w('ilvl')))
    ppr = lvl.find(w('pPr'))
    if ppr is None:
        ppr = etree.Element(w('pPr'))
        rp0 = lvl.find(w('rPr'))
        (rp0.addprevious(ppr) if rp0 is not None else lvl.append(ppr))
    for o in ppr.findall(w('ind')) + ppr.findall(w('tabs')):
        ppr.remove(o)
    nf = lvl.find(w('numFmt'))
    hang = 170 if (nf is not None and nf.get(w('val')) == 'bullet') else 270   # room for '10.' at 7 pt
    ppr.append(el(w('ind'), left=str(hang + 170 * ilvl), hanging=str(hang)))
    rp = lvl.find(w('rPr'))
    if rp is not None:
        for t in ('sz', 'szCs'):
            for o in rp.findall(w(t)):
                o.set(w('val'), SZ)
for ns in nb.getroot().iter(w('nsid')):
    v = ns.get(w('val'))
    ns.set(w('val'), (v.upper().rjust(8, '0'))[-8:])
save(nb, 'word/numbering.xml')

# ---------- document ----------
doc = load('word/document.xml')
body = doc.getroot().find(w('body'))

def math_wrpr(color=BLUE):
    r = etree.Element(w('rPr'))
    r.append(el(w('rFonts'), ascii='Cambria Math', hAnsi='Cambria Math', cs='Cambria Math'))
    r.append(el(w('b'))); r.append(el(w('bCs')))
    r.append(el(w('color'), val=color))
    r.append(el(w('sz'), val=SZ)); r.append(el(w('szCs'), val=SZ))
    return r

for mr in body.iter(m('r')):
    mrpr = mr.find(m('rPr'))
    if mrpr is None:
        mrpr = etree.Element(m('rPr')); mr.insert(0, mrpr)
    for o in mr.findall(w('rPr')):
        mr.remove(o)
    if mrpr.find(m('nor')) is not None:      # \text{}: nor excludes sty
        for o in mrpr.findall(m('sty')): mrpr.remove(o)
        mrpr.addnext(math_wrpr()); continue
    sty = mrpr.find(m('sty'))
    if sty is None:
        sty = etree.SubElement(mrpr, m('sty')); sty.set(m('val'), 'bi')
    else:
        sty.set(m('val'), 'b' if sty.get(m('val')) == 'p' else 'bi')
    sort_children(mrpr, ['lit', 'nor', 'scr', 'sty', 'brk', 'aln'])
    mrpr.addnext(math_wrpr())

# control properties (fraction bars, delimiters, radicals, scripts)
PR = {'f': 'fPr', 'd': 'dPr', 'rad': 'radPr', 'sSub': 'sSubPr', 'sSup': 'sSupPr',
      'sSubSup': 'sSubSupPr', 'nary': 'naryPr', 'acc': 'accPr', 'bar': 'barPr',
      'func': 'funcPr', 'limLow': 'limLowPr', 'limUpp': 'limUppPr'}
for loc, prname in PR.items():
    for node in list(body.iter(m(loc))):
        pr = node.find(m(prname))
        if pr is None:
            pr = etree.Element(m(prname)); node.insert(0, pr)
        for o in pr.findall(m('ctrlPr')):
            pr.remove(o)
        etree.SubElement(pr, m('ctrlPr')).append(math_wrpr())

# NEWX markers -> dark green math for the rest of that paragraph
new_math = set()
for p_ in body.iter(w('p')):
    flag = False
    for node in list(p_.iter()):
        if node.tag == w('t') and node.text and 'NEWX' in node.text:
            flag = True
            node.text = node.text.replace('NEWX ', '').replace('NEWX', '')
            run = node.getparent()
            if not node.text.strip():
                nxt = run.getnext()
                if nxt is not None and nxt.tag == w('r'):
                    t2 = nxt.find(w('t'))
                    if t2 is not None and t2.text == ' ':
                        nxt.getparent().remove(nxt)
                if not node.text:
                    run.getparent().remove(run)
        elif node.tag == m('oMath') and flag:
            new_math.add(node)

def script_color(node):
    a = node.getparent()
    while a is not None and a.tag != m('oMath'):
        if a.tag == m('sub'): return SUBC
        if a.tag == m('sup'): return SUPC
        a = a.getparent()
    return None

def math_root(node):
    a = node
    while a is not None and a.tag != m('oMath'):
        a = a.getparent()
    return a

def recolor(rpr, col):
    c = rpr.find(w('color'))
    if c is None:
        c = el(w('color'), val=col); rpr.append(c)
    c.set(w('val'), col)

for node in list(body.iter(m('r'))) + list(body.iter(m('ctrlPr'))):
    rp = node.find(w('rPr'))
    if rp is None: continue
    base = GREEN if math_root(node) in new_math else BLUE
    recolor(rp, script_color(node) or base)

# Unicode super/subscripts in plain text (incl. units) get their own runs + colour
SUPCH = set('⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺ⁿ')
SUBCH = set('₀₁₂₃₄₅₆₇₈₉₊₋')
def kind(ch):
    return 'sup' if ch in SUPCH else ('sub' if ch in SUBCH else None)
for r in list(body.iter(w('r'))):
    t = r.find(w('t'))
    if t is None or not t.text or not any(kind(c) for c in t.text): continue
    segs = []
    for ch in t.text:
        k = kind(ch)
        if segs and segs[-1][0] == k: segs[-1][1] += ch
        else: segs.append([k, ch])
    parent = r.getparent(); idx = parent.index(r)
    for i, (k, txt) in enumerate(segs):
        nr = copy.deepcopy(r)
        nt = nr.find(w('t')); nt.text = txt
        nt.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
        if k:
            rp = nr.find(w('rPr'))
            if rp is None:
                rp = etree.Element(w('rPr')); nr.insert(0, rp)
            recolor(rp, SUPC if k == 'sup' else SUBC)
        parent.insert(idx + i, nr)
    parent.remove(r)

# collapse double spaces between adjacent text runs
for r in list(body.iter(w('r'))):
    t = r.find(w('t')); prev = r.getprevious()
    if t is None or t.text is None or prev is None or prev.tag != w('r'): continue
    pt = prev.find(w('t'))
    if pt is not None and pt.text and pt.text.endswith(' ') and t.text.startswith(' '):
        t.text = t.text.lstrip(' ')
        if not t.text:
            r.getparent().remove(r)

# explicit 6 pt on every text run (sections resized below)
for r in body.iter(w('r')):
    rp = r.find(w('rPr'))
    if rp is None:
        rp = etree.Element(w('rPr')); r.insert(0, rp)
    add_sz(rp)

# Section sizes: Formulas items 7 pt, Variables and constants 5.5 pt (incl. list markers)
state = None
for p_ in body.findall(w('p')):
    txt = ''.join(t.text or '' for t in p_.iter(w('t'))).strip()
    ps = p_.find(w('pPr')); st_ = ps.find(w('pStyle')) if ps is not None else None
    if txt == 'Formulas':
        state = 'f'; continue
    if txt == 'Variables and constants':
        state = 'v'; continue
    if txt == 'Unit conversions' or (st_ is not None and st_.get(w('val')) == 'Topic'):
        state = None; continue
    if state is None:
        continue
    size = SZ_FORM if state == 'f' else SZ_VAR
    for e_ in p_.iter(w('sz'), w('szCs')):
        e_.set(w('val'), size)
    if ps is None:
        ps = etree.Element(w('pPr')); p_.insert(0, ps)
    mrk = ps.find(w('rPr'))
    if mrk is None:
        mrk = etree.SubElement(ps, w('rPr'))
    for o in mrk.findall(w('sz')) + mrk.findall(w('szCs')):
        mrk.remove(o)
    mrk.append(el(w('sz'), val=size)); mrk.append(el(w('szCs'), val=size))

# section: Letter landscape, 0.25 in margins, 4 columns with separator
sp = body.find(w('sectPr'))
for k in list(sp):
    sp.remove(k)
sp.append(el(w('pgSz'), w='15840', h='12240', orient='landscape'))
sp.append(el(w('pgMar'), top='360', right='360', bottom='360', left='360', header='0', footer='0', gutter='0'))
sp.append(el(w('cols'), num='4', space='200', sep='1'))
for d_ in body.iter(m('dPr')):
    sort_children(d_, DPR_ORDER)
for pp in body.iter(w('pPr')):
    sort_children(pp, PPR_ORDER)
for r_ in body.iter(w('rPr')):
    clean_rpr(r_)
save(doc, 'word/document.xml')

# settings: small default tab stop, fix pandoc schema order
stt = load('word/settings.xml')
dts = stt.getroot().find(w('defaultTabStop'))
if dts is not None:
    dts.set(w('val'), '72')   # overflowing list numbers jump only a hair, never to mid-column
for e_ in stt.getroot().findall(w('embedSystemFonts')):
    stt.getroot().remove(e_)
sort_children(stt.getroot(), ['zoom','proofState','stylePaneFormatFilter','doNotTrackMoves','defaultTabStop','drawingGridHorizontalSpacing','drawingGridVerticalSpacing','displayHorizontalDrawingGridEvery','displayVerticalDrawingGridEvery','characterSpacingControl','savePreviewPicture','footnotePr','endnotePr','compat','docVars','rsids','mathPr','themeFontLang','clrSchemeMapping','decimalSymbol','listSeparator'])
save(stt, 'word/settings.xml')

if os.path.exists(OUT):
    os.remove(OUT)
subprocess.run('cd "%s" && zip -Xqr "%s" .' % (work, os.path.abspath(OUT)), shell=True, check=True)
print('wrote', OUT)
