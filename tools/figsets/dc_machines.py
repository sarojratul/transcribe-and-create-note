"""
DC machines figure set (EE 341 style, usable by any machines course): the five field connections as
generator and motor (labelled parts, nodes a/b, current arrows, KCL/KVL line), plugging, Ward-Leonard,
OCC with critical resistance, external characteristics, power flow, efficiency curve, motor
characteristics, commutation, 2-pole cross-section with GNA/MNA, universal-motor phasor diagram.
Circuits are drawn at true size (0.2175 in per schemdraw unit, labels about 5.2 pt) so every circuit in
the set prints with the same font size; insert them at their PNG size (cs4_edit.py figs does this).
Colours: navy arrows = current, dark green = key relation, black parts. Add figures with @reg + DESC.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from figlib import *
from matplotlib.patches import Rectangle, Circle, Wedge, FancyArrowPatch, Arc, FancyBboxPatch

NAVY = '#1F3864'; GRN = '#006400'; GREY = '#666666'; RED = '#C00000'; ORG = '#B34700'
K = 0.435            # font/line scale: drawn at native schemdraw size, printed at K
S = 0.5 * K          # inches per schemdraw unit (default 0.5 in/unit, scaled)
H = 3.2              # rail height (units)
FSB = 12             # base label size before scaling

DESC = {}


# ---------------------------------------------------------------- circuit helpers (explicit coordinates)
def lab(d, p, t, ha='center', va='center', fs=FSB, color='black'):
    d.add(elm.Label().at(p).label(t, fontsize=fs * K, color=color, halign=ha, valign=va))


def arrow(d, p1, p2, t, lp, ha='left', va='center'):
    d.add(elm.Arrow(color=NAVY, lw=1.8 * K, headwidth=0.2, headlength=0.25).endpoints(p1, p2))
    if t: lab(d, lp, t, ha, va, color=NAVY)


def line(d, p1, p2):
    d.add(elm.Line().endpoints(p1, p2))


def node(d, p, name, below=False):
    d.add(elm.Dot().at(p)); lab(d, (p[0] + 0.18, p[1] + (-0.3 if below else 0.3)), name, 'left', fs=11, color=GREY)


def armature(d, x, gen):
    line(d, (x, 0), (x, 0.2))
    d.add(elm.Motor().endpoints((x, 0.2), (x, 1.6)))
    lab(d, (x + 0.75, 0.9), '$E_g$' if gen else '$E_b$', 'left')
    lab(d, (x + 0.3, 1.72), '+', 'left', fs=11)
    d.add(elm.Resistor().endpoints((x, 1.6), (x, H)))
    lab(d, (x - 0.4, 2.4), '$R_a$', 'right')
    if gen: arrow(d, (x + 0.45, 1.95), (x + 0.45, 2.85), '$I_a$', (x + 0.6, 2.4))
    else:   arrow(d, (x + 0.45, 2.85), (x + 0.45, 1.95), '$I_a$', (x + 0.6, 2.4))


def shunt(d, x):
    d.add(elm.Inductor2(loops=3).endpoints((x, H), (x, 0)))
    lab(d, (x - 0.45, 1.6), '$R_{sh}$', 'right')
    arrow(d, (x + 0.55, 2.05), (x + 0.55, 1.15), '$I_{sh}$', (x + 0.7, 1.6))
    node(d, (x, H), 'a'); node(d, (x, 0), 'b', True)


def series(d, x1, x2, gen, t):
    d.add(elm.Inductor2(loops=3).endpoints((x1, H), (x2, H)))
    xm = (x1 + x2) / 2
    lab(d, (xm, H + 0.5), '$R_{se}$')
    if gen: arrow(d, (xm - 0.45, H - 0.45), (xm + 0.45, H - 0.45), t, (xm, H - 0.8), 'center')
    else:   arrow(d, (xm + 0.45, H - 0.45), (xm - 0.45, H - 0.45), t, (xm, H - 0.8), 'center')


def sfig(build, m=0.35):
    """Draw build(d) on a figure sized from the drawing bbox (true size, S in per unit)."""
    f = plt.figure(figsize=(2, 2))
    ax = f.add_axes([0, 0, 1, 1])
    d = schemdraw.Drawing(show=False)
    d.config(fontsize=FSB * K, lw=1.3 * K)
    build(d)
    d.draw(show=False, canvas=ax)
    bb = d.get_bbox()
    ax.set_xlim(bb.xmin - m, bb.xmax + m); ax.set_ylim(bb.ymin - m, bb.ymax + m)
    ax.set_aspect('equal'); ax.axis('off')
    f.set_size_inches((bb.xmax - bb.xmin + 2 * m) * S, (bb.ymax - bb.ymin + 2 * m) * S)
    f.cs_tight = True
    return f


def machine(kind, gen, title, eq):
    def build(d):
        x0 = 0
        if kind == 'sep':
            x0 = -3.4
            line(d, (x0, 0), (x0, 0.5)); d.add(elm.SourceV().endpoints((x0, 0.5), (x0, H - 0.5))); line(d, (x0, H - 0.5), (x0, H))
            lab(d, (x0 - 0.55, H / 2), '$V_f$', 'right')
            d.add(elm.Inductor2(loops=3).endpoints((-1.6, H), (-1.6, 0)))
            lab(d, (-2.05, 1.6), '$R_f$', 'right')
            arrow(d, (-1.05, 2.05), (-1.05, 1.15), '$I_f$', (-0.9, 1.6))
            line(d, (x0, H), (-1.6, H)); line(d, (x0, 0), (-1.6, 0))
            lab(d, (-2.5, H + 0.35), 'field circuit', fs=10, color=GREY)
        armature(d, 0, gen)
        if kind == 'sep':
            xt = 2.6; line(d, (0, H), (xt, H))
        elif kind == 'shunt':
            shunt(d, 2.4); xt = 4.6; line(d, (0, H), (xt, H))
        elif kind == 'series':
            series(d, 1.0, 3.0, gen, '$I_{se}$'); line(d, (0, H), (1.0, H)); xt = 4.0; line(d, (3.0, H), (xt, H))
        elif kind == 'long':
            series(d, 1.1, 3.1, gen, '$I_{se}=I_a$'); line(d, (0, H), (1.1, H)); shunt(d, 3.9); xt = 6.1; line(d, (3.1, H), (xt, H))
        elif kind == 'short':
            line(d, (0, H), (2.2, H)); shunt(d, 2.2); series(d, 3.0, 5.0, gen, '$I_{se}=I_L$'); line(d, (2.2, H), (3.0, H)); xt = 6.0; line(d, (5.0, H), (xt, H))
        line(d, (0, 0), (xt, 0))
        xl = xt + 1.8
        d.add(elm.Dot(open=True).at((xt, H))); d.add(elm.Dot(open=True).at((xt, 0)))
        lab(d, (xt, H + 0.35), '+'); lab(d, (xt, -0.35), '−')
        line(d, (xt + 0.08, H), (xl, H)); line(d, (xt + 0.08, 0), (xl, 0))
        lab(d, (xt, 1.6), '$V_t$')
        if gen:
            d.add(elm.Resistor().endpoints((xl, H), (xl, 0)))
            lab(d, (xl + 0.45, 1.6), 'Load\n$R_L$', 'left', fs=11)
            arrow(d, (xt + 0.4, H + 0.35), (xt + 1.3, H + 0.35), '$I_L$', (xt + 0.85, H + 0.7), 'center')
        else:
            line(d, (xl, 0), (xl, 0.5)); d.add(elm.SourceV().endpoints((xl, 0.5), (xl, H - 0.5))); line(d, (xl, H - 0.5), (xl, H))
            lab(d, (xl + 0.8, 1.6), 'DC supply\n$V_t$', 'left', fs=11)
            arrow(d, (xt + 1.3, H + 0.35), (xt + 0.4, H + 0.35), '$I_L$', (xt + 0.85, H + 0.7), 'center')
        xc = (x0 + xl) / 2
        lab(d, (xc, H + 1.75), title, fs=13.5)
        lab(d, (xc, H + 1.2), eq, fs=11.5, color=GRN)
    return sfig(build)


GEN = {'sep': ('Separately excited generator', r'$I_a=I_L$ ;  $E_g=V_t+I_aR_a$'),
       'shunt': ('Shunt generator', r'$I_a=I_L+I_{sh}$ ;  $I_{sh}=V_t/R_{sh}$ ;  $E_g=V_t+I_aR_a$'),
       'series': ('Series generator', r'$I_a=I_{se}=I_L$ ;  $E_g=V_t+I_a(R_a+R_{se})$'),
       'long': ('Long-shunt compound generator', r'$I_a=I_{se}=I_L+I_{sh}$ ;  $E_g=V_t+I_a(R_a+R_{se})$'),
       'short': ('Short-shunt compound generator', r'$I_{se}=I_L$, $I_a=I_L+I_{sh}$ ;  $E_g=V_t+I_LR_{se}+I_aR_a$')}
MOT = {'sep': ('Separately excited motor', r'$I_a=I_L$ ;  $E_b=V_t-I_aR_a$'),
       'shunt': ('Shunt motor', r'$I_L=I_a+I_{sh}$ ;  $I_{sh}=V_t/R_{sh}$ ;  $E_b=V_t-I_aR_a$'),
       'series': ('Series motor', r'$I_L=I_a=I_{se}$ ;  $E_b=V_t-I_a(R_a+R_{se})$'),
       'long': ('Long-shunt compound motor', r'$I_{se}=I_a=I_L-I_{sh}$ ;  $E_b=V_t-I_a(R_a+R_{se})$'),
       'short': ('Short-shunt compound motor', r'$I_{se}=I_L$, $I_a=I_L-I_{sh}$ ;  $E_b=V_t-I_LR_{se}-I_aR_a$')}


def _mk(kind, gen):
    tbl = GEN if gen else MOT
    def fn():
        return machine(kind, gen, *tbl[kind])
    fn.__name__ = ('dc_gen_' if gen else 'dc_mot_') + kind
    fn.__module__ = __name__
    return fn


for _k in ('sep', 'shunt', 'series', 'long', 'short'):
    for _g in (True, False):
        _f = _mk(_k, _g); reg(_f); globals()[_f.__name__] = _f
        DESC[_f.__name__] = '%s: parts, nodes a/b, I_a I_L I_sh I_se arrows, V_t, KCL/KVL line' % (GEN if _g else MOT)[_k][0]


@reg
def dc_plug():
    def build(d):
        line(d, (0, 0), (0, 0.2)); d.add(elm.Motor().endpoints((0, 0.2), (0, 1.6)))
        lab(d, (0.75, 0.9), '$E_b$', 'left'); lab(d, (0.3, 1.72), '+', 'left', fs=11)
        d.add(elm.Resistor().endpoints((0, 1.6), (0, H))); lab(d, (-0.4, 2.4), '$R_a$', 'right')
        d.add(elm.Resistor().endpoints((0, H), (2.6, H))); lab(d, (1.3, H + 0.45), '$R_{ext}$ (added)')
        line(d, (2.6, H), (4.4, H)); line(d, (0, 0), (4.4, 0))
        line(d, (4.4, H), (4.4, H - 0.5)); d.add(elm.SourceV().endpoints((4.4, H - 0.5), (4.4, 0.5))); line(d, (4.4, 0.5), (4.4, 0))
        lab(d, (5.0, 1.6), '$V_t$\nreversed', 'left', fs=11)
        arrow(d, (2.4, H - 0.45), (3.4, H - 0.45), "$I_a'$", (2.9, H - 0.8), 'center')
        arrow(d, (0.45, 1.95), (0.45, 2.85), '', (0.6, 2.4))
        lab(d, (2.2, H + 1.75), 'Plugging (reverse armature supply)', fs=13.5)
        lab(d, (2.2, H + 1.2), "$V_R=V_t+E_b$ ;  $I_a'=(V_t+E_b)/(R_a+R_{ext})$", fs=11.5, color=GRN)
        lab(d, (2.2, -0.65), 'Regenerative braking: $E_b>V_t$, $I_a$ reverses', fs=11, color=GRN)
    return sfig(build)


@reg
def dc_wardleonard():
    def build(d):
        d.add(elm.Rect(corner1=(-3.6, 0.9), corner2=(-1.8, 2.3))); lab(d, (-2.7, 1.6), 'AC motor\n(const. N)', fs=10.5)
        g = d.add(elm.Motor().at((0, 2.6)).down()); mm = d.add(elm.Motor().at((4, 2.6)).down())
        d.add(elm.Line().endpoints((-1.8, 1.6), (-0.75, 1.6)).linestyle('--'))
        lab(d, (-0.7, 2.5), 'G'); lab(d, (4.7, 2.5), 'M')
        line(d, g.start, (0, 3.4)); line(d, (0, 3.4), (4, 3.4)); line(d, (4, 3.4), mm.start)
        line(d, g.end, (0, -0.2)); line(d, (0, -0.2), (4, -0.2)); line(d, (4, -0.2), mm.end)
        arrow(d, (1.4, 3.75), (2.6, 3.75), '$I_a$', (2, 4.1), 'center')
        d.add(elm.Line().endpoints((4.75, 1.6), (5.6, 1.6)).linestyle('--')); lab(d, (6.1, 1.6), 'load', fs=11)
        d.add(elm.Dot(open=True).at((-1.6, -1.2))); d.add(elm.Inductor2(loops=3).endpoints((-1.5, -1.2), (0.4, -1.2)))
        d.add(elm.ResistorVar().endpoints((0.4, -1.2), (2.0, -1.2))); d.add(elm.Dot(open=True).at((2.1, -1.2)))
        lab(d, (0.25, -1.85), '$F_1$: gen. field $I_{fg}$ + rheostat (reversible)', fs=10.5)
        d.add(elm.Dot(open=True).at((3.0, -1.2))); d.add(elm.Inductor2(loops=3).endpoints((3.1, -1.2), (5.0, -1.2))); d.add(elm.Dot(open=True).at((5.1, -1.2)))
        lab(d, (4.05, -0.65), '$F_2$: motor field, fixed', fs=10.5)
        lab(d, (1.4, 5.0), 'Ward-Leonard speed control', fs=13.5)
        lab(d, (1.4, 4.55), '$I_{fg}$ sets $E_g$ = motor voltage; reverse $I_{fg}$ to reverse or brake', fs=11, color=GRN)
    return sfig(build)


# ---------------------------------------------------------------- plots and diagrams (matplotlib, 2.45 in)
WW = 2.45


def arr(ax, p1, p2, c=NAVY, lw=0.9, ms=6):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle='-|>', mutation_scale=ms, color=c, lw=lw, shrinkA=0, shrinkB=0))


def _tight(f):
    f.cs_tight = True
    return f


@reg
def dc_occ():
    If = np.array([0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 2.0, 2.4]); E = np.array([6, 24, 43, 61, 79, 93, 103, 110, 115, 120, 122.4])
    f, ax = plt.subplots(figsize=(WW, 1.6))
    ax.plot(If, E, 'k', lw=1.1); ax.plot(If, E * 0.7, 'k--', lw=0.7)
    ax.text(2.42, 124, 'OCC at $N$', fontsize=5, ha='right', va='bottom'); ax.text(2.42, 68, 'OCC at $N_2<N$', fontsize=5, ha='right', va='bottom')
    x = np.linspace(0, 1.3, 5); ax.plot(x, 100 * x, color=NAVY, lw=0.8)
    ax.text(0.35, 150, '$R_c$ = slope of tangent to linear part (from origin)', color=NAVY, fontsize=5, va='center')
    x = np.linspace(0, 2.25, 5); ax.plot(x, 60 * x, color=GRN, lw=0.8); ax.text(2.45, 100, '$R_f<R_c$:\nbuilds up', color=GRN, fontsize=5, ha='right')
    ax.plot(2.0, 120, 'o', mfc='none', mec=GRN, ms=4)
    ax.annotate('operating point: OCC ∩\n$V=R_fI_f$ (no-load $E_0$)', xy=(2.0, 120), xytext=(1.25, 22), fontsize=5, arrowprops=dict(arrowstyle='->', lw=0.5))
    x = np.linspace(0, 0.45, 5); ax.plot(x, 200 * x, color=RED, lw=0.8); ax.text(0.02, 100, '$R_f>R_c$:\nno build-up', color=RED, fontsize=5)
    ax.annotate('$E_r$ residual', xy=(0, 6), xytext=(0.35, -2), fontsize=5, arrowprops=dict(arrowstyle='->', lw=0.5), va='center')
    ax.set_xlabel('$I_f$ [A]', fontsize=5.5, labelpad=1); ax.set_ylabel('$E_0$ [V]', fontsize=5.5, labelpad=1)
    ax.tick_params(labelsize=5, length=2); ax.set_xlim(0, 2.5); ax.set_ylim(-8, 160); ax.grid(alpha=0.25, lw=0.4)
    ax.set_title(r'OCC, critical resistance;  $N_c=N\,R_f/R_c$', fontsize=6, pad=2)
    return _tight(f)


@reg
def dc_extchar():
    f, ax = plt.subplots(figsize=(WW, 1.55)); I = np.linspace(0, 1, 100)
    cv = [(1.0 + 0.18 * I - 0.05 * I**2, GRN, '-'), (1.0 + 0.02 * I - 0.02 * I**2, '#2E75B6', '-'), (1.0 - 0.13 * I - 0.05 * I**2, 'k', '-'),
          (1.0 - 0.15 * I - 0.12 * I**3, 'k', '--'), (1.0 - 0.03 * I - 0.05 * I**2, '#7F6000', '-'), (1.0 - 0.25 * I - 0.35 * I**2, RED, '-'),
          (np.clip(1.35 * I * (1 - 0.45 * I) / 0.6, 0, None) * 0.85, '#7030A0', '-.')]
    for y, c, ls in cv: ax.plot(I, y, color=c, ls=ls, lw=0.9)
    for (x, y, t), c in zip([(1.01, 1.13, 'over'), (1.01, 1.0, 'flat'), (1.01, 0.81, 'sep. exc.'), (1.01, 0.72, 'shunt'), (1.01, 0.92, 'under'), (1.01, 0.40, 'differential'), (0.2, 0.52, 'series')],
                            [GRN, '#2E75B6', 'k', 'k', '#7F6000', RED, '#7030A0']):
        ax.text(x, y, t, fontsize=4.8, color=c, va='center')
    ax.set_xlim(0, 1.35); ax.set_ylim(0, 1.3); ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel('$I_L$', fontsize=5.5, labelpad=1); ax.set_ylabel('$V_t$', fontsize=5.5, labelpad=1)
    ax.set_title('External characteristics ($V_t$ vs $I_L$, constant N)', fontsize=6, pad=2)
    ax.text(0.2, 0.03, 'Internal char. ($E_g$ vs $I_L$) lies above\nexternal by $I_aR_a$ (+ armature reaction).\nCompound: over $V_{FL}>V_{NL}$, flat $V_{FL}=V_{NL}$', fontsize=4.8, va='bottom')
    return _tight(f)


@reg
def dc_flow():
    f, axs = plt.subplots(2, 1, figsize=(WW, 1.45))
    def flow(ax, boxes, losses, t):
        ax.axis('off'); ax.set_xlim(0, 10); ax.set_ylim(-1.6, 1.3); xs = [0.9, 5.0, 9.1]
        for x, b in zip(xs, boxes):
            ax.add_patch(FancyBboxPatch((x - 0.85, 0.1), 1.7, 0.8, boxstyle='round,pad=0.05', fc='#D9E2F3', ec=NAVY, lw=0.5)); ax.text(x, 0.5, b, ha='center', va='center', fontsize=5)
        for i, l in enumerate(losses):
            x0, x1 = xs[i] + 0.9, xs[i + 1] - 0.9; arr(ax, (x0, 0.5), (x1, 0.5), ms=5)
            xm = (x0 + x1) / 2; arr(ax, (xm, 0.5), (xm, -0.25), c=RED, ms=4); ax.text(xm, -0.33, l, ha='center', va='top', fontsize=4.8, color=RED)
        ax.text(0, 1.15, t, fontsize=6)
    cu = 'copper: $I_a^2R_a$, $I_{se}^2R_{se}$,\n$V_tI_{sh}$, brush $V_{br}I_a$'; rot = 'rotational:\ncore + friction, windage'
    flow(axs[0], ['$P_{in}=T\\omega$\n(shaft)', '$P_{dev}=E_gI_a$', '$P_{out}=V_tI_L$'], [rot, cu], 'Generator power flow')
    flow(axs[1], ['$P_{in}=V_tI_L$', '$P_{dev}=E_bI_a$\n$=T_e\\omega$', '$P_{out}=T_{sh}\\omega$\n(shaft)'], [cu, rot], 'Motor power flow')
    return _tight(f)


@reg
def dc_eff():
    f, ax = plt.subplots(figsize=(WW, 1.25)); I = np.linspace(0.5, 25, 200); Pk = 200; Ra = 0.5; V = 230
    ax.plot(I, I**2 * Ra, color=RED, lw=0.9); ax.axhline(Pk, color=NAVY, lw=0.9)
    ax.text(13, 105, r'$P_{var}=I_a^2R_a$', fontsize=5, ha='right', color=RED); ax.text(5, Pk + 12, '$P_{const}$ ($P_k$)', fontsize=5, color=NAVY)
    Im = np.sqrt(Pk / Ra); ax.axvline(Im, color='k', ls=':', lw=0.6)
    ax.set_ylabel('loss [W]', fontsize=5.5, labelpad=1); ax.set_xlabel('$I_a\\approx I_L$ [A]', fontsize=5.5, labelpad=1); ax.set_ylim(0, 330); ax.tick_params(labelsize=5, length=2)
    a2 = ax.twinx(); a2.plot(I, V * I / (V * I + Pk + I**2 * Ra) * 100, color=GRN, lw=1.1)
    a2.set_ylabel('η [%]', fontsize=5.5, color=GRN, labelpad=1); a2.tick_params(labelsize=5, colors=GRN, length=2); a2.set_ylim(40, 100)
    a2.text(24, 95, 'η', color=GRN, fontsize=5.5, ha='right')
    ax.text(Im - 0.4, 20, r'$\eta_{max}$ at $I_a=\sqrt{P_{const}/R_a}$', fontsize=5, ha='right')
    ax.set_title('Max efficiency: variable loss = constant loss', fontsize=6, pad=2)
    return _tight(f)


@reg
def dc_motorchar():
    f, axs = plt.subplots(1, 3, figsize=(WW, 1.05)); I = np.linspace(0.16, 1, 100)
    shT = I; seT = np.where(I < 0.6, I**2 / 1.2, I - 0.3); shN = 1 - 0.08 * I; seN = np.clip(0.25 / I, 0, 1.6)
    for ax, (x1, y1, x2, y2, xl, yl, t) in zip(axs, [(I, shT, I, seT, '$I_a$', '$T$', 'T vs $I_a$'), (I, shN, I, seN, '$I_a$', '$N$', 'N vs $I_a$'), (shT, shN, seT, seN, '$T$', '$N$', 'N vs T')]):
        ax.plot(x1, y1, color=NAVY, lw=1); ax.plot(x2, y2, color=RED, lw=1, ls='--'); ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlabel(xl, fontsize=5.5, labelpad=0); ax.set_ylabel(yl, fontsize=5.5, labelpad=0); ax.set_title(t, fontsize=5.8, pad=1); ax.set_ylim(0, 1.65); ax.set_xlim(0, 1.05)
    axs[0].text(0.05, 1.45, 'shunt', color=NAVY, fontsize=5); axs[0].text(0.05, 1.25, 'series', color=RED, fontsize=5)
    f.text(0.5, -0.06, 'Series: $T\\propto I_a^2$ (unsat.), $N\\propto 1/I_a$, never start at no load (N → ∞)\nShunt: $T\\propto I_a$, N nearly constant', ha='center', va='top', fontsize=5)
    f.tight_layout(pad=0.2, w_pad=0.6)
    return _tight(f)


@reg
def dc_comm():
    f, ax = plt.subplots(figsize=(WW, 0.95)); t = np.linspace(0, 1, 100)
    ax.plot(t, 1 - 2 * t, color=GRN, lw=1, label='linear (ideal)'); ax.plot(t, 1 - 2 * t**2.2, color=RED, lw=0.9, ls='--', label='delayed (under-commutation, sparking)')
    ax.axhline(0, color='k', lw=0.4); ax.set_xticks([0, 1]); ax.set_xticklabels(['0', '$t_c$']); ax.set_yticks([1, -1]); ax.set_yticklabels(['$+I_c$', '$-I_c$'])
    ax.tick_params(labelsize=5, length=2); ax.set_ylim(-1.3, 1.3); ax.legend(fontsize=4.6, frameon=False, loc='lower left'); ax.set_xlabel('time', fontsize=5, labelpad=0)
    ax.set_title(r'Coil current during commutation;  $e_r=L_c\,\frac{2I_c}{t_c}$, $I_c=I_a/A$', fontsize=5.8, pad=2)
    return _tight(f)


@reg
def dc_machine():
    f, ax = plt.subplots(figsize=(WW, 2.0)); ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Circle((0, 0), 3.0, fc='#D9D9D9', ec='k', lw=0.6)); ax.add_patch(Circle((0, 0), 2.5, fc='white', ec='k', lw=0.6))
    for s, nm in ((-1, 'N'), (1, 'S')):
        ax.add_patch(Rectangle((-2.5 if s < 0 else 1.45, -0.45), 1.05, 0.9, fc='#BFBFBF', ec='k', lw=0.5))
        ax.add_patch(Wedge((0, 0), 1.45, 140 if s < 0 else -40, 220 if s < 0 else 40, width=0.25, fc='#BFBFBF', ec='k', lw=0.5))
        for yy in (0.5, -0.85): ax.add_patch(Rectangle((-2.45 if s < 0 else 1.75, yy), 0.5, 0.35, fc=ORG, ec='k', lw=0.4))
        ax.text(s * 1.95, 0, nm, ha='center', va='center', fontsize=7, fontweight='bold')
    ax.add_patch(Rectangle((-0.2, 1.8), 0.4, 0.7, fc='#E0E0E0', ec='k', lw=0.4)); ax.add_patch(Rectangle((-0.2, -2.5), 0.4, 0.7, fc='#E0E0E0', ec='k', lw=0.4))
    ax.add_patch(Circle((0, 0), 1.1, fc='#EDEDED', ec='k', lw=0.6))
    ax.add_patch(Rectangle((-0.12, 1.1), 0.24, 0.25, fc='k')); ax.add_patch(Rectangle((-0.12, -1.35), 0.24, 0.25, fc='k'))
    ax.plot([0, 0], [-2.9, 2.9], color='k', lw=0.5, ls='-.'); ax.text(0.08, 2.75, 'GNA', fontsize=5)
    th = np.radians(-15); ax.plot([-2.6 * np.sin(th), 2.6 * np.sin(th)], [2.6 * np.cos(th), -2.6 * np.cos(th)], color=RED, lw=0.6, ls='--'); ax.text(-1.55, -2.2, 'MNA', fontsize=5, color=RED)
    ax.add_patch(Arc((0, 0), 2.9, 2.9, theta1=40, theta2=75, color=NAVY, lw=0.7))
    arr(ax, (np.cos(np.radians(55)) * 1.45, np.sin(np.radians(55)) * 1.45), (np.cos(np.radians(42)) * 1.45, np.sin(np.radians(42)) * 1.45), ms=5)
    ax.text(0.15, 1.75, 'rotation', fontsize=4.8, color=NAVY)
    arr(ax, (-0.75, 0), (0.75, 0), c=GRN, ms=5); ax.text(-0.1, 0.1, '$F_m$', fontsize=5, color=GRN, ha='right')
    arr(ax, (0, 0), (0, -0.75), c=ORG, ms=5); ax.text(0.05, -0.55, '$F_a$', fontsize=5, color=ORG)
    for t, xy, xt in (('yoke', (-2.15, 2.0), (-3.4, 2.7)), ('field coil', (-2.0, -0.7), (-3.7, -1.9)), ('pole shoe', (-1.35, -0.6), (-3.7, -2.5)),
                      ('interpole', (0.2, 2.2), (2.35, 2.55)), ('brush (on GNA)', (0.12, -1.25), (2.0, -2.95)), ('armature', (0.55, 0.55), (1.65, 1.0))):
        ax.text(xt[0], xt[1], t, fontsize=5); ax.annotate('', xy=xy, xytext=(xt[0] + (0.5 if xt[0] < 0 else 0), xt[1] + 0.1), arrowprops=dict(arrowstyle='-', lw=0.4))
    ax.set_xlim(-3.8, 3.8); ax.set_ylim(-3.2, 3.1)
    ax.set_title('2-pole DC machine; MNA shifts with rotation (gen.),\nagainst rotation (motor) by brush lead $\\theta_d$', fontsize=5.8, pad=1)
    return _tight(f)


@reg
def dc_universal():
    f, ax = plt.subplots(figsize=(WW, 1.15)); ax.set_aspect('equal'); ax.axis('off'); E, IR, IX = 3.0, 0.8, 1.9
    arr(ax, (0, 0), (E, 0), c=GRN); ax.text(E / 2, -0.25, '$E_{ac}$', ha='center', fontsize=5.5, color=GRN)
    arr(ax, (E, 0), (E + IR, 0), c=RED, ms=5); ax.text(E + IR / 2, -0.25, '$IR$', ha='center', fontsize=5.5, color=RED)
    arr(ax, (E + IR, 0), (E + IR, IX), c=ORG, ms=5); ax.text(E + IR + 0.1, IX / 2, '$IX_L$', fontsize=5.5, color=ORG, va='center')
    arr(ax, (0, 0), (E + IR, IX)); ax.text(1.5, 1.05, '$V$', fontsize=6, color=NAVY)
    arr(ax, (0, -0.55), (1.6, -0.55), c='k', ms=5); ax.text(1.7, -0.55, '$I$ (reference)', fontsize=5, va='center')
    ax.add_patch(Arc((0, 0), 1.6, 1.6, theta1=0, theta2=np.degrees(np.arctan(IX / (E + IR))), lw=0.6)); ax.text(0.9, 0.2, r'$\phi$', fontsize=5.5)
    ax.text(4.6, 1.4, r'$V^2=(E_{ac}+IR)^2+(IX_L)^2$' + '\n' + r'$\cos\phi=(E_{ac}+IR)/V$', fontsize=5.3, color=GRN, va='top')
    ax.set_xlim(-0.2, 7.6); ax.set_ylim(-0.8, 2.1); ax.set_title('Universal motor on AC (phasor diagram)', fontsize=6, pad=1)
    return _tight(f)


DESC.update({
    'dc_plug': 'Plugging circuit: reversed V_t, R_ext, I_a\', V_R = V_t + E_b; regenerative braking line',
    'dc_wardleonard': 'Ward-Leonard set: AC motor -> G -> M, generator field + reversing rheostat, fixed motor field',
    'dc_occ': 'OCC with residual E_r, R_c tangent, R_f < R_c and R_f > R_c lines, operating point, OCC at lower speed (N_c)',
    'dc_extchar': 'Generator external characteristics: over/flat/under compound, separately excited, shunt, series, differential',
    'dc_flow': 'Generator and motor power flow with rotational and copper loss taps',
    'dc_eff': 'Losses vs I_a (P_var parabola, P_const line) with efficiency curve, eta_max at sqrt(P_const/R_a)',
    'dc_motorchar': 'Shunt vs series motor: T vs I_a, N vs I_a, N vs T',
    'dc_comm': 'Coil current during commutation: linear vs delayed, e_r = L_c 2I_c/t_c',
    'dc_machine': '2-pole DC machine cross-section: yoke, poles, field coils, interpoles, brushes, GNA vs MNA, F_m, F_a',
    'dc_universal': 'Universal motor on AC phasor diagram: E_ac, IR, IX_L, V, phi',
})
register_desc(DESC)
