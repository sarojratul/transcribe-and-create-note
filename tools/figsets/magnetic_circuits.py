"""
Magnetic circuits and electromagnetic-law figure set (any machines/EM course): C-core with air gap and
its reluctance equivalent, ring/toroid mean path with the geometry formulas, Fleming's right- and
left-hand rules. 2.45 in wide, 5-6.5 pt labels, symbols only. Add figures with @reg + DESC.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from figlib import *
from matplotlib.patches import Rectangle, Wedge, Arc, FancyArrowPatch

NAVY = '#1F3864'; GRN = '#006400'; ORG = '#B34700'; WW = 2.45


def arr(ax, p1, p2, c=NAVY, lw=0.9, ms=6):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle='-|>', mutation_scale=ms, color=c, lw=lw, shrinkA=0, shrinkB=0))


@reg
def mag_core():
    f = plt.figure(figsize=(WW, 2.0))
    ax = f.add_axes([0, 0.45, 0.5, 0.5]); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((0, 0), 4, 3, fc='#BFBFBF', ec='k', lw=0.6)); ax.add_patch(Rectangle((0.8, 0.8), 2.4, 1.4, fc='white', ec='k', lw=0.6))
    ax.add_patch(Rectangle((3.2, 1.3), 0.8, 0.4, fc='white', ec='white', lw=0)); ax.plot([3.2, 4], [1.3, 1.3], 'k', lw=0.6); ax.plot([3.2, 4], [1.7, 1.7], 'k', lw=0.6)
    for y in np.linspace(1.0, 2.0, 6): ax.plot([-0.15, 0.95], [y - 0.08, y + 0.08], color=ORG, lw=1.0)
    ax.plot([-0.15, -0.6], [0.92, 0.7], color=ORG, lw=0.8); ax.plot([-0.15, -0.6], [1.92, 2.3], color=ORG, lw=0.8)
    arr(ax, (-0.9, 2.3), (-0.6, 2.3)); ax.text(-1.0, 2.45, '$I$', color=NAVY, ha='center'); ax.text(-0.75, 1.5, '$N$', ha='center')
    ax.plot([0.4, 3.6, 3.6, 0.4, 0.4], [0.4, 0.4, 2.6, 2.6, 0.4], '--', color=NAVY, lw=0.6)
    arr(ax, (1.6, 2.6), (2.4, 2.6)); ax.text(2.0, 2.72, r'$\Phi$', color=NAVY, ha='center')
    ax.text(4.15, 1.5, '$g$', va='center'); ax.text(2.0, 0.53, '$l_c$ (mean path)', ha='center', fontsize=5, color=NAVY)
    ax.text(2.0, -0.35, '$A_c$ = core area', ha='center', fontsize=5)
    ax.set_xlim(-1.3, 4.6); ax.set_ylim(-0.6, 3.0); ax.set_title('Core with air gap', fontsize=6.5, pad=2)
    ax2 = f.add_axes([0.52, 0.5, 0.46, 0.4])
    def eq(d):
        s = d.add(elm.SourceV().up().label(r'$\mathcal{F}=NI$', loc='top'))
        r1 = d.add(elm.Resistor().right().label(r'$\mathcal{R}_{iron}$'))
        r2 = d.add(elm.Resistor().down().label(r'$\mathcal{R}_{gap}$', loc='bot'))
        l = d.add(elm.Line().left())
        d.add(elm.LoopCurrent([r1, r2, l, s], pad=0.5, color=NAVY).label(r'$\Phi$', color=NAVY))
    circuit(ax2, eq, unit=1.6); ax2.set_title('Equivalent (like KVL)', fontsize=6.5, pad=2)
    ax3 = f.add_axes([0.02, 0.0, 0.46, 0.44]); ax3.set_aspect('equal'); ax3.axis('off')
    ax3.add_patch(Wedge((0, 0), 1.5, 8, 352, width=0.5, fc='#BFBFBF', ec='k', lw=0.6))
    ax3.add_patch(Arc((0, 0), 2.5, 2.5, theta1=8, theta2=352, ls='--', color=NAVY, lw=0.6))
    ax3.annotate('', xy=(-1.5, -1.75), xytext=(1.5, -1.75), arrowprops=dict(arrowstyle='<->', lw=0.5)); ax3.text(0, -2.05, '$D_{out}$', ha='center', fontsize=5.5)
    ax3.annotate('', xy=(-1.0, 0), xytext=(1.0, 0), arrowprops=dict(arrowstyle='<->', lw=0.5)); ax3.text(0, 0.12, '$D_{in}$', ha='center', fontsize=5.5)
    ax3.text(1.65, 0, 'gap', fontsize=5, va='center'); ax3.set_xlim(-2, 2.3); ax3.set_ylim(-2.3, 1.8); ax3.set_title('Ring / toroid', fontsize=6.5, pad=1)
    ax4 = f.add_axes([0.5, 0.0, 0.5, 0.44]); ax4.axis('off'); ax4.set_xlim(0, 1); ax4.set_ylim(-0.1, 1)
    ax4.text(0, 0.85, r'$l_{mean}=\pi\,\frac{D_{in}+D_{out}}{2}$', fontsize=6.5, color=GRN)
    ax4.text(0, 0.62, r'$A=\pi\left(\frac{D_{out}-D_{in}}{4}\right)^2$ (circular', fontsize=5.5, color=GRN)
    ax4.text(0.05, 0.47, 'cross-section, d = ($D_{out}$ − $D_{in}$)/2)', fontsize=5.2, color=GRN)
    ax4.text(0, 0.3, r'$l_{iron}=l_{mean}-g$ (if g given)', fontsize=5.5, color=GRN)
    ax4.text(0, -0.02, 'Same Φ in every series part;\nsame B where A is the same', fontsize=5.2)
    f.cs_tight = True
    return f


@reg
def mag_fleming():
    f, axs = plt.subplots(1, 2, figsize=(WW, 1.05))
    for ax, (t, labs) in zip(axs, [('Right hand: generator', ['Thumb: motion $v$', 'First:\nfield $B$', 'Middle: induced $e$, $I$']),
                                   ('Left hand: motor', ['Thumb: force $F$', 'First:\nfield $B$', 'Middle: current $I$'])]):
        ax.set_aspect('equal'); ax.axis('off')
        arr(ax, (0, 0), (0, 1)); arr(ax, (0, 0), (1, 0), c=GRN); arr(ax, (0, 0), (-0.6, -0.6), c=ORG)
        ax.text(0.05, 1.03, labs[0], fontsize=5.2, color=NAVY); ax.text(1.03, 0.03, labs[1], fontsize=5.2, color=GRN, va='bottom')
        ax.text(-0.62, -0.72, labs[2], fontsize=5.2, color=ORG, va='top'); ax.set_xlim(-1.1, 1.6); ax.set_ylim(-1.0, 1.25); ax.set_title(t, fontsize=6.3, pad=1)
    f.text(0.5, -0.02, '$e=Blv\\,\\sin\\theta$ (generator)      $F=BIl\\,\\sin\\theta$ (motor)', ha='center', fontsize=5.5, color=GRN)
    f.cs_tight = True
    return f


DESC = {'mag_core': 'C-core with coil, air gap g, mean path l_c + reluctance equivalent (F = NI, R_iron, R_gap, Phi) + toroid mean-length/area formulas',
        'mag_fleming': "Fleming's right-hand (generator) and left-hand (motor) rules as labelled axes, e = Blv sin, F = BIl sin"}
register_desc(DESC)
