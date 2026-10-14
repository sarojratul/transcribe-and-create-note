"""
AC and three-phase power basics figure set (any course): power triangle and star vs delta with line and
phase relations. 2.45 in wide, 5-6 pt labels. Add figures with @reg + DESC.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from figlib import *
from matplotlib.patches import Arc

NAVY = '#1F3864'; GRN = '#006400'; ORG = '#B34700'; WW = 2.45


@reg
def ac_3ph():
    f = plt.figure(figsize=(WW, 1.25))
    ax = f.add_axes([0, 0, 0.3, 1]); ax.set_aspect('equal'); ax.axis('off')
    ax.plot([0, 2, 2, 0], [0, 0, 1.2, 0], 'k', lw=0.8); ax.text(1, -0.18, '$P$ [W]', ha='center', va='top', fontsize=5.5)
    ax.text(2.08, 0.6, '$Q$\n[var]', va='center', fontsize=5.5); ax.text(0.8, 0.75, '$S$ [VA]', ha='right', fontsize=5.5)
    ax.add_patch(Arc((0, 0), 0.9, 0.9, theta1=0, theta2=31, lw=0.6)); ax.text(0.5, 0.1, r'$\phi$', fontsize=5.5)
    ax.text(0, 1.55, 'Power triangle\n(lagging, inductive)', fontsize=5.5); ax.text(0, -0.75, r'pf $=\cos\phi=P/S$', fontsize=5.5, color=GRN)
    ax.set_xlim(-0.1, 2.6); ax.set_ylim(-1.0, 2.0)
    pts = [(np.cos(np.radians(a)), np.sin(np.radians(a))) for a in (90, 210, 330)]
    ax = f.add_axes([0.32, 0, 0.34, 1]); ax.set_aspect('equal'); ax.axis('off')
    for x, y in pts: ax.plot([0, x], [0, y], color=ORG, lw=1.1); ax.plot(x, y, 'ko', ms=1.5)
    ax.plot(0, 0, 'ko', ms=1.5); ax.text(-0.25, -0.05, 'n', fontsize=5)
    ax.annotate('', xy=(pts[1][0], pts[1][1] - 0.12), xytext=(pts[2][0], pts[2][1] - 0.12), arrowprops=dict(arrowstyle='<->', lw=0.5, color=NAVY)); ax.text(0, -0.85, '$V_L$', ha='center', fontsize=5.5, color=NAVY)
    ax.text(0.12, 0.45, '$V_{ph}$', fontsize=5.5, color=ORG); ax.text(-1.1, 1.25, 'Star (Y)', fontsize=6)
    ax.text(-1.15, -1.15, r'$V_L=\sqrt{3}V_{ph}$' + '\n' + '$I_L=I_{ph}$', fontsize=5.5, color=GRN, va='top'); ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.9, 1.5)
    ax = f.add_axes([0.66, 0, 0.34, 1]); ax.set_aspect('equal'); ax.axis('off')
    for i in range(3): ax.plot([pts[i][0], pts[(i + 1) % 3][0]], [pts[i][1], pts[(i + 1) % 3][1]], color=ORG, lw=1.1); ax.plot(*pts[i], 'ko', ms=1.5)
    ax.annotate('', xy=(pts[1][0], pts[1][1] - 0.15), xytext=(pts[2][0], pts[2][1] - 0.15), arrowprops=dict(arrowstyle='<->', lw=0.5, color=NAVY)); ax.text(0, -0.9, '$V_L=V_{ph}$', ha='center', fontsize=5.5, color=NAVY)
    ax.text(-1.1, 1.25, 'Delta (Δ)', fontsize=6); ax.text(-1.15, -1.15, '$V_L=V_{ph}$\n' + r'$I_L=\sqrt{3}I_{ph}$', fontsize=5.5, color=GRN, va='top'); ax.set_xlim(-1.3, 1.3); ax.set_ylim(-1.9, 1.5)
    f.cs_tight = True
    return f


DESC = {'ac_3ph': 'Power triangle (P, Q, S, phi, pf) + star and delta with V_L/V_ph and I_L/I_ph relations'}
register_desc(DESC)
