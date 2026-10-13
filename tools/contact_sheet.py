#!/usr/bin/env python3
"""
contact_sheet.py: stack PNGs into one labelled image, to check figures in a single Read.

  python3 contact_sheet.py OUT.png figs/lrc.png figs/sk.png ...      (or a folder: figs/)
"""
import sys, os, glob
from PIL import Image, ImageDraw

out, *paths = sys.argv[1:]
files = []
for p in paths:
    files += sorted(glob.glob(os.path.join(p, '*.png'))) if os.path.isdir(p) else [p]
W = 920
rows = []
for f in files:
    im = Image.open(f).convert('RGB')
    r = im.resize((W, int(im.height * W / im.width)))
    c = Image.new('RGB', (W, r.height + 18), 'white')
    c.paste(r, (0, 18))
    ImageDraw.Draw(c).text((4, 2), os.path.basename(f), fill='red')
    rows.append(c)
sheet = Image.new('RGB', (W, sum(r.height for r in rows)), 'white')
y = 0
for r in rows:
    sheet.paste(r, (0, y)); y += r.height
sheet.save(out)
print('wrote %s (%d images, %dx%d); keep under about 8 images per sheet so labels stay readable' % (out, len(rows), W, y))
