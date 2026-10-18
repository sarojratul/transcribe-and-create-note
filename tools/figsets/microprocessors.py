"""
Microprocessor / assembly language figure set (CME 331 and any ARM Cortex-M course): number wheel
for n-bit unsigned and two's complement arithmetic with the C and V wrap points, and the stack
layout after a multi-register PUSH (lowest register at the lowest address). 2.3-2.45 in wide,
5-6 pt labels, symbols only. Add figures with @reg + DESC.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from figlib import *
from matplotlib.patches import Arc, FancyArrowPatch

NAVY = '#1F3864'; BLUE = '#1F4FBF'; RED = '#C00000'; GRN = '#006400'; WW = 2.45

DESC = {
    'number_wheel4': '4-bit number wheel: bit patterns, unsigned 0-15, signed -8..7; C wraps at 1111/0000, V wraps at 0111/1000; add = clockwise',
    'stack_push3': 'Stack after PUSH {Ra,Rb,Rc} (a<b<c): SP drops by 12, Ra at lowest address (SP), Rc at SP+8; POP refills in the same order',
}
register_desc(DESC)


@reg
def number_wheel4():
    f = plt.figure(figsize=(WW, 2.05))
    ax = f.add_axes([0, 0, 0.62, 1]); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(plt.Circle((0, 0), 1.0, fill=False, lw=0.8))
    for k in range(16):
        a = np.radians(90 - k * 22.5)
        c, s = np.cos(a), np.sin(a)
        ax.plot([0.95 * c, 1.05 * c], [0.95 * s, 1.05 * s], 'k', lw=0.5)
        ax.text(1.27 * c, 1.27 * s, format(k, '04b'), ha='center', va='center', fontsize=5)
        ax.text(0.80 * c, 0.80 * s, str(k), ha='center', va='center', fontsize=5.3)
        sv = k if k < 8 else k - 16
        ax.text(0.55 * c, 0.55 * s, str(sv), ha='center', va='center', fontsize=5, color=BLUE)
    # C wrap point between 15 and 0 (top), V wrap point between 7 and 8 (bottom)
    a = np.radians(90 + 11.25)
    ax.plot([0.35 * np.cos(a), 1.5 * np.cos(a)], [0.35 * np.sin(a), 1.5 * np.sin(a)], color=RED, lw=1.1)
    ax.text(1.55 * np.cos(a) - 0.05, 1.55 * np.sin(a) + 0.02, 'C', color=RED, fontsize=6, ha='right', weight='bold')
    a = np.radians(90 - 7.5 * 22.5)
    ax.plot([0.35 * np.cos(a), 1.5 * np.cos(a)], [0.35 * np.sin(a), 1.5 * np.sin(a)], color=GRN, lw=1.1)
    ax.text(1.55 * np.cos(a) + 0.05, 1.55 * np.sin(a) - 0.05, 'V', color=GRN, fontsize=6, ha='left', va='top', weight='bold')
    ax.add_patch(FancyArrowPatch((1.62 * np.cos(np.radians(72)), 1.62 * np.sin(np.radians(72))),
                                 (1.62 * np.cos(np.radians(38)), 1.62 * np.sin(np.radians(38))),
                                 connectionstyle='arc3,rad=-0.3', arrowstyle='->', mutation_scale=6, lw=0.6))
    ax.text(1.05, 1.62, '+ (add)', fontsize=5)
    ax.set_xlim(-1.75, 1.75); ax.set_ylim(-1.75, 1.85)
    tx = f.add_axes([0.62, 0, 0.38, 1]); tx.axis('off')
    lines = [('outer: bit pattern', 'k'), ('middle: unsigned', 'k'), ('inner: signed', BLUE),
             ('', 'k'), ('add $b$: $b$ steps', 'k'), ('clockwise', 'k'), ('subtract $b$: add', 'k'),
             ('$2^n-b$ (= $b$ steps', 'k'), ('counterclockwise)', 'k'), ('', 'k'),
             ('crossing C line:', RED), ('unsigned wrap', RED), ('crossing V line:', GRN), ('signed wrap', GRN)]
    for i, (t, col) in enumerate(lines):
        tx.text(0.02, 0.95 - i * 0.068, t, fontsize=5, color=col, va='top')
    return f


@reg
def stack_push3():
    f = plt.figure(figsize=(WW, 1.45))
    def column(ax, x, vals, sp_row, title):
        rows = 5
        for r in range(rows):
            y = rows - 1 - r
            ax.add_patch(plt.Rectangle((x, y * 0.3), 0.7, 0.3, fill=(r == rows - 1), fc='#DDDDDD', ec='k', lw=0.6))
            if vals[r]:
                ax.text(x + 0.35, y * 0.3 + 0.15, vals[r], ha='center', va='center', fontsize=5.3)
        ysp = (rows - 1 - sp_row) * 0.3 + 0.15
        ax.annotate('', xy=(x, ysp), xytext=(x - 0.32, ysp), arrowprops=dict(arrowstyle='->', lw=0.6))
        ax.text(x - 0.34, ysp, 'SP', fontsize=5, ha='right', va='center')
        ax.text(x + 0.35, 1.62, title, ha='center', fontsize=5.3)
    ax = f.add_axes([0, 0, 1, 1]); ax.axis('off')
    column(ax, 0.55, ['', '', '', '', 'old'], 4, 'before')
    column(ax, 1.95, ['', 'Ra', 'Rb', 'Rc', 'old'], 1, 'after PUSH {Ra,Rb,Rc}')
    ax.text(2.72, 1.05, 'SP', fontsize=5, va='center'); ax.text(2.72, 0.75, 'SP+4', fontsize=5, va='center')
    ax.text(2.72, 0.45, 'SP+8', fontsize=5, va='center')
    ax.annotate('', xy=(3.45, 1.5), xytext=(3.45, 0.0), arrowprops=dict(arrowstyle='<->', lw=0.5))
    ax.text(3.52, 1.45, 'low address', fontsize=5, va='top'); ax.text(3.52, 0.05, 'high address', fontsize=5, va='bottom')
    ax.text(3.52, 0.75, 'stack grows\nup the page\n(toward low)', fontsize=4.8, va='center')
    ax.text(0.0, -0.18, 'a < b < c; SP drops 4 bytes per register', fontsize=4.8)
    ax.text(0.0, -0.36, 'POP {Rx,Ry,Rz} (x < y < z): Rx gets the word at SP', fontsize=4.8)
    ax.set_xlim(0, 4.6); ax.set_ylim(-0.48, 1.8)
    return f
