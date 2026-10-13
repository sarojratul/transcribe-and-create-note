#!/usr/bin/env python3
"""
cheat_dump.py: list the cheat-sheet entries of a notes .docx, one line per paragraph,
with the equation ordinals that cheat_update.py specs refer to.

  python3 cheat_dump.py NOTES.docx            # all entries
  python3 cheat_dump.py NOTES.docx "Sallen"   # entries whose heading starts with "Sallen"

Output: "## <heading>" then "  EQ0 ...", "  U ...", "  T ...", "  IMG", "  TBL ...".
Also prints the text size (half-points) and column count of the cheat-sheet section.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cheat_common import load, region, entries, kind, ptext, NS, W

root = load(sys.argv[1])
body = root.find('w:body', NS)
kids, s, e = region(body)
want = sys.argv[2] if len(sys.argv) > 2 else None
from collections import Counter
c = Counter(r.get('{%s}val' % W) for i in range(s + 1, e) if kind(kids[i]) == 'T'
            for r in kids[i].findall('.//w:r/w:rPr/w:sz', NS))
sz = c.most_common(1)[0][0] if c else None
cols = [c.get('{%s}num' % W) for c in body.iter('{%s}cols' % W) if c.get('{%s}num' % W)]
print('text size (half-points): %s; column counts in document: %s' % (sz, cols))
for head, hi, idx in entries(kids, s, e):
    if want and not head.startswith(want):
        continue
    print('## ' + head)
    n = 0
    for i in idx:
        k = kind(kids[i])
        t = ptext(kids[i]).strip().replace('\n', ' ')[:90]
        if k == 'EQ':
            print('  EQ%d %s' % (n, t))
            n += 1
        else:
            print('  %s %s' % (k, t))
