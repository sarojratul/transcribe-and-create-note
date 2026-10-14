#!/usr/bin/env python3
"""
cheat_figures.py: library of ready-made figures for cheat sheets and notes, any course. Figures
live in tools/figsets/<subject>.py (one module per subject area: analog_circuits, dc_machines,
magnetic_circuits, ac_power), drawn
2.3 in wide with 4.5-6 pt labels and general symbols only (no example values). The builder scales
them to the column.

  python3 cheat_figures.py --list                     # catalogue, grouped by subject
  python3 cheat_figures.py --list analog_circuits     # one subject
  python3 cheat_figures.py OUTDIR lrc sk butter       # write OUTDIR/<name>.png
  python3 cheat_figures.py OUTDIR lrc --plot-only     # drop the drawn circuit/diagram panel, keep the plot
                                                      # (pair it with a slide crop: slide_crop.py pair)
  python3 cheat_figures.py OUTDIR --all

Use in notes.md: "!fig OUTDIR/<name>.png". First choice for a figure is the lecture's own slide
(slide_crop.py); this library fills gaps. New figure: add it to the right figsets module (or a new
module for a new subject) with @reg and a DESC line, check the PNG, commit it so later runs reuse it.
A figure function may set fig.cs_tight = True (hand-placed axes): it is then saved cropped to its
content at true size instead of tight_layout.
Needs: matplotlib, schemdraw, scipy, numpy, pillow.
"""
import os, sys, glob, argparse, importlib
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figlib
from figlib import plt, REG, DESC, DOMAIN

for f in sorted(glob.glob(os.path.join(HERE, 'figsets', '*.py'))):
    if not os.path.basename(f).startswith('_'):
        importlib.import_module('figsets.' + os.path.basename(f)[:-3])


def plot_only_bbox(fig):
    """Bounding box (inches) of the plot panels only: panels drawn with axis('off') (circuits,
    block diagrams) are left out, so the saved PNG keeps the full layout of the plot."""
    from matplotlib.transforms import Bbox
    keep = [ax for ax in fig.axes if ax.axison]
    if not keep or len(keep) == len(fig.axes):
        return 'tight'
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bb = Bbox.union([ax.get_tightbbox(r) for ax in keep]).transformed(fig.dpi_scale_trans.inverted())
    return bb.padded(0.03)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('out', nargs='?'); ap.add_argument('names', nargs='*')
    ap.add_argument('--list', nargs='?', const='', metavar='SUBJECT')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--plot-only', action='store_true')
    a = ap.parse_args()
    if a.list is not None or not a.out:
        subj = a.list or None
        for d in sorted(set(DOMAIN.values())):
            if subj and d != subj: continue
            print('[%s]' % d)
            for n in REG:
                if DOMAIN[n] == d: print('  %-12s %s' % (n, DESC.get(n, '')))
        return
    os.makedirs(a.out, exist_ok=True)
    names = list(REG) if a.all else a.names
    bad = [n for n in names if n not in REG]
    if bad: sys.exit('unknown figure(s): %s (see --list)' % ', '.join(bad))
    for n in names:
        f = REG[n]()
        tight = getattr(f, 'cs_tight', False)   # figure laid out by hand (fig.add_axes, fig.text): crop to content
        if not tight:
            f.tight_layout(pad=0.15, w_pad=0.4)
        path = os.path.join(a.out, n + ('_plot' if a.plot_only else '') + '.png')
        f.savefig(path, dpi=400, facecolor='white',
                  bbox_inches=plot_only_bbox(f) if a.plot_only else ('tight' if tight else None),
                  pad_inches=0.02)
        plt.close(f)
        print('wrote', path)


if __name__ == '__main__':
    main()
