"""Shared helpers for reading the cheat-sheet section of a notes .docx (used by cheat_dump.py and cheat_update.py)."""
from lxml import etree

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
M = 'http://schemas.openxmlformats.org/officeDocument/2006/math'
NS = {'w': W, 'm': M}


def ptext(p):
    return ''.join(e.text or '' for e in p.iter() if e.tag in ('{%s}t' % W, '{%s}t' % M))


def region(body):
    """(children, start, end): body children from the 'Cheat sheet, copy-ready' heading to 'Open questions' (or the end)."""
    kids = list(body)
    s = e = None
    for i, k in enumerate(kids):
        if k.tag == '{%s}p' % W:
            t = ptext(k).strip()
            if s is None and i > 20 and t.startswith('Cheat sheet, copy-ready'):
                s = i
            elif s is not None and t == 'Open questions':
                e = i
                break
    if s is None:
        raise SystemExit('no "Cheat sheet, copy-ready" heading found')
    return kids, s, (e if e is not None else len(kids) - 1)


def kind(k):
    """H entry heading (D9E2F3 shading), U Use when, EQ display equation, IMG, TBL, SECT, T text."""
    if k.tag == '{%s}tbl' % W:
        return 'TBL'
    if k.find('.//m:oMathPara', NS) is not None:
        return 'EQ'
    if k.find('.//w:drawing', NS) is not None:
        return 'IMG'
    shd = k.find('w:pPr/w:shd', NS)
    if shd is not None and shd.get('{%s}fill' % W) == 'D9E2F3':
        return 'H'
    if ptext(k).startswith('Use when'):
        return 'U'
    if k.find('.//w:sectPr', NS) is not None:
        return 'SECT'
    return 'T'


def entries(kids, s, e):
    """[(heading_text, heading_index, [child indices of the entry body])]"""
    out = []
    for i in range(s, e):
        if kind(kids[i]) == 'H':
            out.append([ptext(kids[i]).strip(), i, []])
        elif out:
            out[-1][2].append(i)
    return out


def load(docx_path):
    import zipfile
    with zipfile.ZipFile(docx_path) as z:
        root = etree.fromstring(z.read('word/document.xml'))
    return root
