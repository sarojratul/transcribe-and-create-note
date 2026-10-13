#!/usr/bin/env python3
"""
slide_crop.py: cut a figure (circuit, block diagram, plot, flowchart, table, photo) out of a slide
image from `build_notes.py scan` (slides/cN.png), for the cheat sheet or a notes page. Any course.

  1. Find coordinates in one look (labelled grid, fractions 0-1 of width and height):
       python3 slide_crop.py grid slides/c12.png -o grid12.png
  2. Crop, optionally blanking example values and writing symbols in their place:
       python3 slide_crop.py crop slides/c12.png --box 0.05 0.30 0.55 0.85 -o figs/s12_circuit.png \
           --blank 0.40 0.52 0.48 0.58 --label 0.40 0.52 "R_2"
     --box/--blank/--label coordinates are slide fractions (x0 y0 x1 y1, origin top-left).
     White margins are trimmed. --blank is repeatable (white fill); --label writes text at the
     top-left corner of a blanked spot, sized to its height (use plain text or Unicode symbols;
     "_x" makes a subscript-looking smaller suffix).
  3. Put two pieces side by side (e.g. a circuit from one slide and a plot from another):
       python3 slide_crop.py pair figs/a.png figs/b.png -o figs/entry.png [--ratio 1.2]

Then reference the PNG with "!fig figs/<name>.png" in notes.md (the builder scales it to the
column), or pass it to cheat_update.py. Check every crop by looking at it: no cut-off labels,
no neighbouring slide text, no example values left on a cheat-sheet figure.
"""
import argparse, sys
from PIL import Image, ImageDraw, ImageFont, ImageOps


def font(px):
    for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(f, max(8, int(px)))
        except OSError:
            pass
    return ImageFont.load_default()


def frac_box(im, b):
    x0, y0, x1, y1 = b
    return (int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height))


def trim(im, pad=12):
    g = ImageOps.invert(im.convert("L")).point(lambda v: 255 if v > 20 else 0)
    bb = g.getbbox()
    if not bb:
        return im
    return im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))


def cmd_grid(a):
    im = Image.open(a.slide).convert("RGB")
    d = ImageDraw.Draw(im)
    f = font(im.height / 45)
    for k in range(1, a.n):
        x = im.width * k / a.n
        y = im.height * k / a.n
        d.line([(x, 0), (x, im.height)], fill=(255, 0, 0), width=2)
        d.line([(0, y), (im.width, y)], fill=(255, 0, 0), width=2)
        d.text((x + 3, 3), "%.1f" % (k / a.n), fill=(255, 0, 0), font=f)
        d.text((3, y + 3), "%.1f" % (k / a.n), fill=(255, 0, 0), font=f)
    if im.width > 1600:
        im = im.resize((1600, int(im.height * 1600 / im.width)))
    im.save(a.out)
    print("wrote", a.out)


def cmd_crop(a):
    im = Image.open(a.slide).convert("RGB")
    d = ImageDraw.Draw(im)
    blanks = [frac_box(im, b) for b in (a.blank or [])]
    for b in blanks:
        d.rectangle(b, fill="white")
    for x, y, text in (a.label or []):
        x, y = float(x), float(y)
        px = (int(x * im.width), int(y * im.height))
        h = next((b[3] - b[1] for b in blanks if b[0] <= px[0] <= b[2] and b[1] <= px[1] <= b[3]), im.height / 30)
        main, _, sub = text.partition("_")
        f = font(h * 0.8)
        d.text(px, main, fill="black", font=f)
        if sub:
            w = d.textlength(main, font=f)
            d.text((px[0] + w, px[1] + h * 0.35), sub, fill="black", font=font(h * 0.55))
    out = im.crop(frac_box(im, a.box))
    if not a.no_trim:
        out = trim(out)
    out.save(a.out)
    print("wrote %s (%dx%d px)" % (a.out, out.width, out.height))


def cmd_pair(a):
    A, B = Image.open(a.left).convert("RGB"), Image.open(a.right).convert("RGB")
    h = max(A.height, B.height)
    A = A.resize((int(A.width * h / A.height), h))
    B = B.resize((int(B.width * h / B.height), h))
    if a.ratio:   # target width ratio left:right
        tw = int(B.width * a.ratio)
        A = A.resize((tw, int(A.height * tw / A.width)))
        h = max(A.height, B.height)
    gap = int(h * 0.04)
    out = Image.new("RGB", (A.width + B.width + gap, h), "white")
    out.paste(A, (0, (h - A.height) // 2))
    out.paste(B, (A.width + gap, (h - B.height) // 2))
    out.save(a.out)
    print("wrote %s (%dx%d px)" % (a.out, out.width, out.height))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grid"); g.add_argument("slide"); g.add_argument("-o", "--out", required=True); g.add_argument("--n", type=int, default=10)
    c = sub.add_parser("crop"); c.add_argument("slide"); c.add_argument("-o", "--out", required=True)
    c.add_argument("--box", type=float, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    c.add_argument("--blank", type=float, nargs=4, action="append", metavar=("X0", "Y0", "X1", "Y1"))
    c.add_argument("--label", nargs=3, action="append", metavar=("X", "Y", "TEXT"))
    c.add_argument("--no-trim", action="store_true")
    p = sub.add_parser("pair"); p.add_argument("left"); p.add_argument("right"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--ratio", type=float, help="width of left piece relative to right (default: equal heights)")
    a = ap.parse_args()
    {"grid": cmd_grid, "crop": cmd_crop, "pair": cmd_pair}[a.cmd](a)


if __name__ == "__main__":
    main()
