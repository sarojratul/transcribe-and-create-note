"""
Analog circuits and filters figure set (op-amps, feedback, stability, passive/active filter blocks,
standard filter responses, spec masks). Add figures with @reg and a DESC entry; see figlib.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from figlib import *

DESC = {'rc_lp': 'First-order RC low-pass: circuit + Bode magnitude/phase (omega0, -3 dB, -20 dB/dec, -45 deg)', 'rc_hp': 'First-order RC high-pass: circuit + Bode', 'rlc2': 'Series R, shunt L||C (band-pass RLC): circuit + pole locus as R increases', 'dcerr': 'Inverting amp with compensating R at + input (bias current) + transfer curve shifted by V_OS', 'seriesshunt': 'Non-inverting amp (series-shunt feedback, B = R1/(R1+R2)) + A/B feedback block diagram', 'sp_fb': 'Non-inverting amp + single pole moving from -w0 to -w0(1+Adc B)', 'gbp': '|A| and |G| log-log: Adc, Gdc, w0, w0prime, wu = GBP', 'twopole': 'Two-pole amp with feedback: pole locus (meet, split vertically) + |G| peaking for Q', 'polemove': 'Three equal poles root locus vs B (crossing jw at B_crit)', 'stab': 'Feedback block diagram G = A/(1+AB) + three-pole root locus', 'equal': 'n equal poles: |A| and angle A, w_c where angle = -pi, Adc cos^n(pi/n)', 'dompole': 'Dominant-pole compensation: |A| with wD, wp (angle -pi), 1/Bmax line', 'margins': 'Bode |A| and angle A with 1/B line, PM at |AB| = 1, GM at w180', 'spec': 'Filter |H| regions: passband ripple, transition, stopband, 1/sqrt2', 'butter': 'Butterworth: poles on circle (kept/dropped) + |H| for increasing n', 'cheb': 'Chebyshev: poles on ellipse + |H| with passband ripple alpha', 'invcheb': 'Inverse Chebyshev: poles + jw-axis zeros + |H| with stopband ripple', 'compare': 'Butterworth/Chebyshev/inverse Chebyshev/elliptic/Bessel |H| + group delay, same n', 'cascade': 'Block cascade H1 -> H2 -> ... -> Hk (poles grouped into blocks)', 'realization': 'Cascade of n/2 second-order sections', 'zmult': 'Op-amp impedance (capacitance) multiplier circuit + R_eq/C_eq equivalent', 'rc1': 'Passive RC one-pole block: circuit + single pole at -w0', 'lrc': 'Passive LRC block (series L, shunt R||C): circuit + conjugate pair at |p|, theta', 'sk': 'Sallen-Key low-pass with gain K (R0, (K-1)R0): circuit + pole locus vs K (K=1 to K=3)', 'act1': 'First-order active RC (inverting, R2||C feedback): circuit + Bode', 'integ': 'Inverting integrator circuit + biquad block diagram (summer + two integrators)', 'lpspec': 'Low-pass spec mask: Gp, Ap, As, fc, fs', 'types3': 'Butterworth vs Chebyshev I vs elliptic in dB, same order', 'sos': 'Second-order sections: type 1 |H| for Q values + type 2 notch at wz', 'topo': 'Sallen-Key (unity gain) and MFB low-pass circuits, stacked'}


import schemdraw.dsp as dsp
from scipy import signal
VIN = '$V_\\mathrm{in}$'
VOUT = '$V_\\mathrm{out}$'

def term_l(d, lab=VIN):
    d += elm.Dot(open=True).label(lab, 'left')

def term_r(d, lab=VOUT):
    d += elm.Dot(open=True).label(lab, 'right')

def two_port_passive(d, series, shunts, lens=None):
    """series: element factory for the series arm; shunts: list of factories for shunt branches."""
    start = d.here
    term_l(d)
    d += series()
    top_nodes = []
    for k, sh in enumerate(shunts):
        if k > 0:
            d += elm.Line().right(1.2)
        d += elm.Dot()
        d.push()
        d += sh().down()
        d += elm.Dot()
        d.pop()
    d += elm.Line().right(1.0)
    term_r(d)
    endx = d.here[0]
    d += elm.Gap().down().label(VOUT if False else '', 'right')
    d += elm.Dot(open=True)
    d += elm.Line().left().tox(start[0])
    d += elm.Dot(open=True)

def bode_lp1(ax, hp=False, lab='$\\omega_0$', ylab='$|H|$ dB'):
    w = np.logspace(-2, 2, 300)
    H = 1j * w / (1 + 1j * w) if hp else 1 / (1 + 1j * w)
    m = 20 * np.log10(abs(H))
    ph = np.angle(H, deg=True)
    ax.plot(w, m, 'k')
    bode_axes(ax, ylabel=ylab)
    ax.set_ylim(-45, 6)
    ax.axvline(1, color='0.5', lw=0.5, ls=':')
    vlabel(ax, 1, lab)
    ax.plot([1], [-3], 'k.', ms=3)
    ax.text(1.35, -1.5 if not hp else -9, '$-3$ dB', fontsize=5)
    if not hp:
        ax.text(7, -12, '$-20$ dB/dec', fontsize=5)
    else:
        ax.text(0.011, -33, '$+20$ dB/dec', fontsize=5)
    a2 = ax.twinx()
    a2.plot(w, ph, 'k--', lw=0.7)
    a2.set_yticks([])
    a2.set_ylim(-105, 105)
    for s in ['top', 'right']:
        a2.spines[s].set_visible(False)
    if not hp:
        a2.text(0.011, -60, '$\\angle H$ (dashed):' + '\n' + '$0\\to-90°$, $-45°$ at $\\omega_0$', fontsize=4.6)
    else:
        a2.text(4, 15, '$\\angle H$ (dashed):' + '\n' + '$90°\\to0$, $+45°$ at $\\omega_0$', fontsize=4.6)

@reg
def rc_lp():
    f, (a, b) = fig(2, 1.0, [1, 1.15])
    circuit(a, lambda d: two_port_passive(d, lambda: elm.Resistor().right().label('R'), [lambda: elm.Capacitor().label('C', loc='bottom')]))
    bode_lp1(b)
    return f

@reg
def rc_hp():
    f, (a, b) = fig(2, 1.0, [1, 1.15])
    circuit(a, lambda d: two_port_passive(d, lambda: elm.Capacitor().right().label('C'), [lambda: elm.Resistor().label('R', loc='bottom')]))
    bode_lp1(b, hp=True)
    return f

@reg
def rlc2():
    f, (a, b) = fig(2, 1.1, [1.15, 1])
    circuit(a, lambda d: two_port_passive(d, lambda: elm.Resistor().right().label('R'), [lambda: elm.Inductor2().label('L', loc='bottom'), lambda: elm.Capacitor().label('C', loc='bottom')]))
    splane(b, 1.25, xl=(-1.45, 0.5))
    r = 0.75
    c = np.linspace(np.pi, np.pi * 0.54, 50)
    b.plot(r * np.cos(c), r * np.sin(c), 'k', lw=0.9)
    b.plot(r * np.cos(c), -r * np.sin(c), 'k', lw=0.9)
    b.annotate('', xy=(r * np.cos(c[-1]), r * np.sin(c[-1])), xytext=(r * np.cos(c[-6]), r * np.sin(c[-6])), arrowprops=dict(arrowstyle='->', lw=0.7))
    b.plot([-0.1, -1.35], [0, 0], 'k', lw=2.2, alpha=0.25)
    b.annotate('', xy=(-0.6, 0.0), xytext=(-0.12, 0.0), arrowprops=dict(arrowstyle='->', lw=0.7))
    b.annotate('', xy=(-0.9, 0.0), xytext=(-1.3, 0.0), arrowprops=dict(arrowstyle='->', lw=0.7))
    pole(b, -0.1, 0)
    pole(b, -1.32, 0)
    b.plot([-r], [0], 'k.', ms=3.5)
    b.text(-1.3, -0.12, '$-\\frac{1}{RC}$', ha='center', va='top', fontsize=4.6)
    b.text(-0.12, -0.12, '$-\\frac{R}{L}$', ha='center', va='top', fontsize=4.6)
    b.text(-r - 0.08, 0.18, '$-\\frac{1}{2RC}$', ha='right', va='bottom', fontsize=4.6)
    b.text(0.06, 0.9, '$\\frac{j}{\\sqrt{LC}}$', fontsize=5)
    b.text(-1.4, 0.95, '$R\\uparrow$', fontsize=6)
    b.text(-1.4, -1.15, 'circle: ' + '$|p|=1/\\sqrt{LC}$', fontsize=4.5)
    return f

@reg
def dcerr():
    f, (a, b) = fig(2, 1.1, [1.3, 1])
    circuit(a, lambda d: inv_amp(d, plusR=True))
    a.text(0.62, 0.02, '$I_B$ into each input', transform=a.transAxes, fontsize=4.6, ha='center')
    x = np.linspace(-1, 1, 200)
    vos = 0.25
    b.plot(x, np.clip(-4 * (x - vos), -1, 1), 'k')
    b.plot(x, np.clip(-4 * x, -1, 1), color='0.6', lw=0.6, ls='--')
    b.axhline(0, color='k', lw=0.5)
    b.axvline(0, color='k', lw=0.5)
    b.set_xticks([])
    b.set_yticks([])
    [s.set_visible(False) for s in b.spines.values()]
    b.text(vos + 0.03, 0.1, '$V_{OS}$', fontsize=5)
    b.text(1.0, -0.1, VIN, ha='right', va='top', fontsize=5)
    b.text(0.04, 1.08, VOUT, fontsize=5)
    b.text(-1, 1.08, 'rail', fontsize=5)
    b.text(0.6, -0.92, 'rail', fontsize=5)
    b.text(-1, -0.5, 'grey dashed:\nno offset', fontsize=4.5, color='0.4')
    b.set_ylim(-1.15, 1.25)
    return f

def noninv2(d, R1='$R_1$', R2='$R_2$'):
    OPAMP(d)
    n = (-0.5, 0.62)
    xo = 3.9
    W_(d, (0, 0.62), n)
    DOT(d, n)
    R_(d, n, (-2.4, 0.62), R1)
    GND(d, (-2.4, 0.62))
    W_(d, n, (-0.5, 1.9))
    R_(d, (-0.5, 1.9), (xo, 1.9), R2)
    W_(d, (xo, 1.9), (xo, 0))
    W_(d, (3.42, 0), (xo, 0))
    DOT(d, (xo, 0))
    W_(d, (xo, 0), (xo + 0.5, 0))
    TR(d, (xo + 0.5, 0), VOUT)
    W_(d, (0, -0.62), (-2.4, -0.62))
    TL(d, (-2.4, -0.62), VIN)

def blockdiag(ax, A='A', B='B'):

    def c(d):
        d += dsp.Arrow().right(0.8).label('$x$', 'left')
        d += (sm := dsp.SumSigma())
        d += dsp.Arrow().right(0.8).at(sm.E)
        d += (bx := dsp.Box(w=1.2, h=0.9).label(A).anchor('W'))
        d += dsp.Line().right(0.7).at(bx.E)
        d += dsp.Dot()
        d.push()
        d += dsp.Arrow().right(0.7).label('$y$', 'right')
        d.pop()
        d += dsp.Line().down(1.4)
        d += dsp.Arrow().left(0.9)
        d += (fb := dsp.Box(w=1.2, h=0.9).label(B).anchor('E'))
        d += dsp.Line().left().at(fb.W).tox(sm.S)
        d += dsp.Arrow().up().toy(sm.S).label('−', 'left', ofst=0.05)
    circuit(ax, c)

@reg
def seriesshunt():
    f, (a, b) = fig(2, 1.05, [1.25, 1])
    circuit(a, lambda d: noninv2(d))
    blockdiag(b, 'A', 'B')
    a.text(0.5, -0.02, '$B=\\frac{R_1}{R_1+R_2}$', transform=a.transAxes, ha='center', va='top', fontsize=5)
    b.text(0.5, -0.02, '$G=\\frac{A}{1+AB}$', transform=b.transAxes, ha='center', va='top', fontsize=5)
    return f

@reg
def sp_fb():
    f, (a, b) = fig(2, 1.05, [1.25, 1])
    circuit(a, lambda d: noninv2(d))
    a.text(0.5, -0.02, '$B=\\frac{R_1}{R_1+R_2}$', transform=a.transAxes, ha='center', va='top', fontsize=5)
    splane(b, 1.2, xl=(-1.3, 0.35), yl=(-0.6, 0.6))
    pole(b, -0.15, 0)
    pole(b, -1.05, 0)
    b.annotate('', xy=(-0.95, 0.12), xytext=(-0.22, 0.12), arrowprops=dict(arrowstyle='->', lw=0.7))
    b.text(-0.15, -0.08, '$-\\omega_0$', ha='center', va='top', fontsize=5)
    b.text(-1.05, -0.08, "$-\\omega_0'$", ha='center', va='top', fontsize=5)
    b.text(-0.6, 0.18, '$\\times(1+A_{dc}B)$', ha='center', va='bottom', fontsize=5)
    return f

@reg
def gbp():
    f, (b,) = fig(1, 0.95)
    w = np.logspace(-1, 4, 300)
    A = 1000.0 / np.sqrt(1 + w ** 2)
    G = 10 / np.sqrt(1 + (w / 100) ** 2)
    b.loglog(w, A, 'k')
    b.loglog(w, G, 'k--')
    bode_axes(b, ylabel='$|A|,\\ |G|$ (log)')
    b.set_ylim(0.3, 3000)
    b.text(0.12, 1300, '$A_{dc}$', fontsize=5)
    b.text(0.12, 13, '$G_{dc}$', fontsize=5)
    b.axvline(1, color='0.6', lw=0.5, ls=':')
    b.axvline(100, color='0.6', lw=0.5, ls=':')
    vlabel(b, 1, '$\\omega_0$')
    vlabel(b, 100, "$\\omega_0'$")
    b.axhline(1, color='0.6', lw=0.5)
    b.plot([1000.0], [1], 'k.', ms=3)
    b.text(1200.0, 1.4, '$\\omega_u\\approx$ GBP', fontsize=5)
    b.text(20, 200, '$|A|$', fontsize=5)
    b.text(3, 4, '$|G|$ (dashed)', fontsize=5)
    b.text(300, 60, '$-20$ dB/dec', fontsize=5)
    return f

@reg
def twopole():
    f, (a, b) = fig(2, 1.0, [1, 1.2])
    splane(a, 1.2, xl=(-1.35, 0.3), yl=(-1.1, 1.1))
    w1, w2 = (0.25, 1.1)
    m = -(w1 + w2) / 2
    pole(a, -w1, 0)
    pole(a, -w2, 0)
    a.annotate('', xy=(m + 0.04, 0), xytext=(-w1, 0), arrowprops=dict(arrowstyle='->', lw=0.7))
    a.annotate('', xy=(m - 0.04, 0), xytext=(-w2, 0), arrowprops=dict(arrowstyle='->', lw=0.7))
    a.plot([m, m], [0, 0.95], 'k', lw=0.9)
    a.plot([m, m], [0, -0.95], 'k', lw=0.9)
    a.annotate('', xy=(m, 1.0), xytext=(m, 0.7), arrowprops=dict(arrowstyle='->', lw=0.7))
    a.annotate('', xy=(m, -1.0), xytext=(m, -0.7), arrowprops=dict(arrowstyle='->', lw=0.7))
    a.text(-w1, -0.1, '$-\\omega_1$', fontsize=4.6, ha='center', va='top')
    a.text(-w2, -0.1, '$-\\omega_2$', fontsize=4.6, ha='center', va='top')
    a.text(m + 0.06, -0.55, '$-\\frac{\\omega_1+\\omega_2}{2}$', ha='left', fontsize=4.6)
    a.text(m + 0.06, 0.7, '$B\\uparrow$', fontsize=5.5)
    w = np.logspace(-1.3, 1, 300)
    for Q, ls in [(0.5, '-'), (0.707, '--'), (2, ':')]:
        H = 1 / (1 - w ** 2 + 1j * w / Q)
        b.plot(w, 20 * np.log10(abs(H)), 'k', ls=ls, lw=0.8)
    bode_axes(b, ylabel='$|G|$ dB')
    b.set_ylim(-34, 12)
    b.text(1.15, 7, '$Q>1/\\sqrt{2}$: peak', fontsize=5)
    b.text(0.055, -31, 'Q = 1/2 (solid),\n' + '$1/\\sqrt{2}$ (dashed), 2 (dotted)', fontsize=4.5)
    b.axvline(1, color='0.6', lw=0.5, ls=':')
    vlabel(b, 1, "$\\omega_0'$")
    return f

def locus3(ax, labB=True):
    splane(ax, 1.3, xl=(-1.6, 0.7), yl=(-1.25, 1.25))
    pole(ax, -0.5, 0)
    ax.text(-0.75, -0.12, '$-\\omega_0$ (×3)', ha='center', va='top', fontsize=4.6)
    t = np.linspace(0, 1.25, 60)
    for sgn in (1, -1):
        ax.plot(-0.5 + t * 0.5, sgn * t * 0.866, 'k', lw=0.9)
        ax.annotate('', xy=(-0.5 + 1.15 * 0.5, sgn * 1.15 * 0.866), xytext=(-0.5 + 0.9 * 0.5, sgn * 0.9 * 0.866), arrowprops=dict(arrowstyle='->', lw=0.7))
        ax.plot([0], [sgn * 0.866], 'ko', ms=2.5)
    ax.plot([-0.5, -1.55], [0, 0], 'k', lw=0.9)
    ax.annotate('', xy=(-1.5, 0), xytext=(-1.2, 0), arrowprops=dict(arrowstyle='->', lw=0.7))
    ax.text(0.07, 0.6, '$B_{crit}$', fontsize=5)
    if labB:
        ax.text(-1.5, 0.9, '$B\\uparrow$', fontsize=5.5)
    ax.text(0.25, -0.45, 'RHP:\nunstable', fontsize=4.5)

@reg
def polemove():
    f, (b,) = fig(1, 1.0)
    locus3(b)
    return f

@reg
def stab():
    f, (a, b) = fig(2, 1.0, [1.2, 1])
    blockdiag(a, 'A(s)', 'B')
    locus3(b)
    a.text(0.5, -0.02, '$G=\\frac{A}{1+AB}$', transform=a.transAxes, ha='center', va='top', fontsize=5.5)
    return f

@reg
def equal():
    f, (b,) = fig(1, 1.0)
    w = np.logspace(-1.3, 1.3, 300)
    n = 3
    ph = -n * np.degrees(np.arctan(w))
    m = 20 * np.log10(1 / (1 + w ** 2) ** (n / 2))
    b.plot(w, m, 'k')
    bode_axes(b, ylabel='$|A|$ dB')
    b.set_ylim(-75, 10)
    a2 = b.twinx()
    a2.plot(w, ph, 'k--', lw=0.7)
    a2.set_yticks([])
    a2.set_ylim(-290, 20)
    a2.axhline(-180, color='0.6', lw=0.5)
    for s in ['top', 'right']:
        a2.spines[s].set_visible(False)
    wc = np.sqrt(3)
    b.axvline(wc, color='0.6', lw=0.5, ls=':')
    vlabel(b, wc, '$\\omega_c=\\omega_0\\tan(\\pi/n)$')
    a2.text(0.06, -175, '$\\angle A=-\\pi$', fontsize=5)
    a2.text(0.25, -120, '$\\angle A$ (dashed)', fontsize=5)
    b.text(0.06, -12, '$A_{dc}$', fontsize=5)
    b.plot([wc], [20 * np.log10(1 / (1 + 3) ** 1.5)], 'k.', ms=3)
    b.text(wc * 1.15, -14, '$|A|=A_{dc}\\cos^n(\\pi/n)$', fontsize=5)
    return f

@reg
def dompole():
    f, (b,) = fig(1, 1.0)
    w = np.logspace(-3, 1.4, 400)
    wD = 0.002
    wp = 1
    A = 1000.0 / ((1 + 1j * w / wD) * (1 + 1j * w / wp) ** 2)
    b.loglog(w, abs(A), 'k')
    bode_axes(b, ylabel='$|A|$ (log)')
    b.set_ylim(0.004, 5000)
    b.axhline(1, color='0.6', lw=0.5)
    b.text(0.0012, 1.5, '$1/B_{max}$ line ($=1$ for a follower)', fontsize=4.6)
    b.axvline(wD, color='0.6', lw=0.5, ls=':')
    b.axvline(wp, color='0.6', lw=0.5, ls=':')
    vlabel(b, wD, '$\\omega_D$')
    vlabel(b, wp, '$\\omega_p$: $\\angle A=-\\pi$')
    b.text(0.003, 15, '$-20$ dB/dec, $\\angle A\\approx-\\pi/2$', fontsize=4.6)
    b.text(0.0012, 1500, '$A_{dc}$', fontsize=5)
    b.text(0.0012, 0.012, 'need $|A|B_{max}<1$ at $\\omega_p$', fontsize=4.6)
    return f

@reg
def margins():
    f, (b,) = fig(1, 1.2)
    w = np.logspace(-1, 2.5, 400)
    A = 1000.0 / ((1 + 1j * w / 0.1) * (1 + 1j * w / 20) * (1 + 1j * w / 60))
    m = 20 * np.log10(abs(A))
    ph = np.degrees(np.unwrap(np.angle(A)))
    b.plot(w, m, 'k')
    bode_axes(b, ylabel='$|A|$ dB')
    B = 0.05
    L = 20 * np.log10(1 / B)
    b.axhline(L, color='0.35', lw=0.6, ls='-.')
    b.text(0.11, L + 6, '$1/B$ line: $|AB|=1$ where $|A|=1/B$', fontsize=4.6)
    i1 = np.argmin(abs(m - L))
    w1 = w[i1]
    i180 = np.argmin(abs(ph + 180))
    w180 = w[i180]
    b.axvline(w1, color='0.6', lw=0.5, ls=':')
    b.axvline(w180, color='0.6', lw=0.5, ls=':')
    b.annotate('', xy=(w180, L), xytext=(w180, m[i180]), arrowprops=dict(arrowstyle='<->', lw=0.6))
    b.text(w180 * 1.1, (L + m[i180]) / 2 - 2, 'GM', fontsize=5)
    vlabel(b, w1, '$\\omega_1$')
    vlabel(b, w180, '$\\omega_{180}$')
    b.set_ylim(-70, 75)
    a2 = b.twinx()
    a2.plot(w, ph, 'k--', lw=0.7)
    a2.set_yticks([])
    a2.set_ylim(-330, 60)
    for s in ['top', 'right']:
        a2.spines[s].set_visible(False)
    a2.axhline(-180, color='0.6', lw=0.5)
    a2.text(0.11, -200, '$-180°$', fontsize=5)
    a2.annotate('', xy=(w1, -180), xytext=(w1, ph[i1]), arrowprops=dict(arrowstyle='<->', lw=0.6))
    a2.text(w1 * 0.85, (ph[i1] - 180) / 2 - 5, 'PM', fontsize=5, ha='right')
    a2.text(0.11, -130, '$\\angle A$ (dashed)', fontsize=5)
    return f

def magplot(ax, ylab='$|H|$'):
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel('$\\omega/\\omega_0$', labelpad=1)
    ax.set_ylabel(ylab, labelpad=1)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)

def resp(b, a, w):
    return abs(signal.freqs(b, a, worN=w)[1])

@reg
def spec():
    f, (b,) = fig(1, 1.0)
    w = np.linspace(0, 3, 400)
    bb, aa = signal.cheby1(5, 1, 1, analog=True)
    H = resp(bb, aa, w)
    b.plot(w, H, 'k')
    magplot(b)
    b.axhspan(10 ** (-1 / 20), 1, xmin=0, xmax=1 / 3.1, color='0.85')
    b.axhspan(0, 0.1, xmin=1.6 / 3.1, xmax=1, color='0.85')
    b.set_xlim(0, 3.1)
    b.set_ylim(0, 1.15)
    b.text(0.05, 1.03, 'passband (ripple)', fontsize=5)
    b.text(1.05, 0.5, 'transition', fontsize=5)
    b.text(1.7, 0.13, 'stopband, max $|H|$', fontsize=5)
    b.axvline(1, color='0.5', lw=0.5, ls=':')
    b.axhline(1 / np.sqrt(2), color='0.6', lw=0.4, ls=':')
    b.text(2.0, 0.73, '$1/\\sqrt{2}$ ($-3$ dB)', fontsize=5)
    return f

def circle_poles(ax, n, ell=1.0):
    k = np.arange(1, n + 1)
    th = np.pi / 2 + (2 * k - 1) * np.pi / (2 * n)
    x = np.cos(th) * ell
    y = np.sin(th)
    t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(np.cos(t) * ell, np.sin(t), color='0.6', lw=0.5, ls='--')
    for xi, yi in zip(x, y):
        pole(ax, xi, yi, 3.5)
    for xi, yi in zip(-x, y):
        ax.plot([xi], [yi], 'x', color='0.65', ms=3, mew=0.7)
    return (x, y)

@reg
def butter():
    f, (a, b) = fig(2, 1.05, [1, 1.3])
    splane(a, 1.3, xl=(-1.3, 1.3))
    circle_poles(a, 4)
    a.text(0.55, 0.95, '$\\omega_0$', fontsize=5)
    a.plot([0, 0.707], [0, 0.707], color='0.4', lw=0.5)
    a.text(0.15, -1.3, 'grey: dropped', fontsize=4.3, color='0.4')
    w = np.linspace(0, 2.5, 300)
    for n, ls in [(2, ':'), (4, '--'), (8, '-')]:
        b.plot(w, 1 / np.sqrt(1 + w ** (2 * n)), 'k', ls=ls, lw=0.8)
    magplot(b)
    b.text(1.45, 0.55, '$n\\uparrow$: steeper', fontsize=5)
    b.text(0.05, 1.04, 'maximally flat', fontsize=5)
    b.axvline(1, color='0.6', lw=0.5, ls=':')
    b.plot([1], [0.707], 'k.', ms=3)
    b.text(0.55, 0.62, '$1/\\sqrt{2}$', fontsize=5)
    b.set_ylim(0, 1.15)
    return f

@reg
def cheb():
    f, (a, b) = fig(2, 1.05, [1, 1.3])
    splane(a, 1.3, xl=(-1.3, 1.3))
    circle_poles(a, 4, ell=0.4)
    a.text(0.5, 0.6, 'ellipse', fontsize=5)
    w = np.linspace(0, 2, 400)
    bb, aa = signal.cheby1(4, 1, 1, analog=True)
    H = resp(bb, aa, w)
    b.plot(w, H, 'k')
    magplot(b)
    b.set_ylim(0, 1.15)
    b.axhline(1, color='0.6', lw=0.4, ls=':')
    b.axhline(10 ** (-1 / 20), color='0.6', lw=0.4, ls=':')
    b.annotate('', xy=(1.25, 1.0), xytext=(1.25, 10 ** (-1 / 20)), arrowprops=dict(arrowstyle='<->', lw=0.5))
    b.text(1.3, 0.98, 'ripple $\\alpha$ dB', fontsize=4.8)
    b.text(1.15, 0.45, 'sharp cut-off', fontsize=5)
    b.axvline(1, color='0.6', lw=0.5, ls=':')
    return f

@reg
def invcheb():
    f, (a, b) = fig(2, 1.05, [1, 1.3])
    z, p, k = signal.cheb2ap(4, 30)
    lim = max(abs(z.imag)) * 1.15
    splane(a, lim, xl=(-lim * 0.9, lim * 0.55))
    for pp in p:
        pole(a, pp.real, pp.imag, 3.5)
    for zz in z:
        zero(a, zz.real, zz.imag, 3)
    a.text(0.12 * lim, 0.45 * lim, 'zeros on\n' + '$j\\omega$ axis', fontsize=4.6)
    w = np.linspace(0, 4, 600)
    bb, aa = signal.cheby2(4, 30, 1, analog=True)
    H = resp(bb, aa, w)
    b.plot(w, H, 'k')
    magplot(b)
    b.set_ylim(0, 1.12)
    b.text(0.05, 1.02, 'no passband ripple', fontsize=5)
    b.text(1.4, 0.15, 'stopband ripple', fontsize=5)
    b.annotate('weak attenuation', xy=(2.6, 0.03), xytext=(1.9, 0.5), fontsize=4.8, arrowprops=dict(arrowstyle='->', lw=0.5))
    return f

@reg
def compare():
    f, (a, b) = fig(2, 1.15, [1, 1])
    w = np.linspace(0.001, 2.5, 600)
    n = 4
    sets = [('Butterworth', signal.butter(n, 1, analog=True), '-'), ('Chebyshev', signal.cheby1(n, 1, 1, analog=True), '--'), ('Inverse Cheb.', signal.cheby2(n, 30, 1.6, analog=True), '-.'), ('Elliptic', signal.ellip(n, 1, 30, 1, analog=True), ':'), ('Bessel', signal.bessel(n, 1, analog=True, norm='mag'), None)]
    for nm, (bb, aa), ls in sets:
        H = signal.freqs(bb, aa, worN=w)[1]
        if nm == 'Bessel':
            a.plot(w, abs(H), color='0.55', ls='-', lw=1.0, label=nm)
        else:
            a.plot(w, abs(H), 'k', ls=ls, lw=0.75, label=nm)
        gd = -np.gradient(np.unwrap(np.angle(H)), w)
        if nm == 'Bessel':
            b.plot(w, gd / gd[0], color='0.55', lw=1.0)
        elif nm in ('Butterworth', 'Chebyshev'):
            b.plot(w, gd / gd[0], 'k', ls=ls, lw=0.75)
    magplot(a)
    a.set_ylim(0, 1.15)
    a.legend(loc='upper right', fontsize=4.0, handlelength=2.0, borderaxespad=0.1, labelspacing=0.15)
    a.set_title('same order n', fontsize=5, pad=1)
    magplot(b, 'group delay (norm.)')
    b.set_ylim(0, 3.2)
    b.set_title('delay: Bessel flattest', fontsize=5, pad=1)
    return f

def cascade_block(ax, labs=('$H_1$', '$H_2$', '$H_k$')):
    y = 0
    bw, bh = (0.9, 0.6)
    xs = [1.2, 2.6, 4.6]
    barrow(ax, [(0.2, y), (xs[0] - bw / 2, y)])
    ax.text(0.15, y, VIN, ha='right', va='center', fontsize=5.5)
    for x, l in zip(xs, labs):
        bbox_(ax, x, y, bw, bh, l)
    barrow(ax, [(xs[0] + bw / 2, y), (xs[1] - bw / 2, y)])
    ax.plot([xs[1] + bw / 2, xs[1] + bw / 2 + 0.3], [y, y], 'k', lw=0.8)
    ax.text((xs[1] + xs[2]) / 2, y, '...', ha='center', va='center', fontsize=6)
    barrow(ax, [(xs[2] - bw / 2 - 0.3, y), (xs[2] - bw / 2, y)])
    barrow(ax, [(xs[2] + bw / 2, y), (xs[2] + bw / 2 + 0.6, y)])
    ax.text(xs[2] + bw / 2 + 0.65, y, VOUT, ha='left', va='center', fontsize=5.5)
    ax.set_xlim(-0.5, 6.4)
    ax.set_ylim(-1.2, 0.45)
    ax.set_aspect('equal')
    ax.axis('off')

@reg
def cascade():
    f, (a,) = fig(1, 0.5)
    cascade_block(a)
    a.text(0.5, 0.02, 'pair → two-pole block; real pole → one-pole block;\nactive blocks do not load each other', transform=a.transAxes, ha='center', va='bottom', fontsize=4.6)
    return f

@reg
def realization():
    f, (a,) = fig(1, 0.5)
    cascade_block(a, ('$H_1$', '$H_2$', '$H_{n/2}$'))
    a.text(0.5, 0.02, 'each block: one second-order section (one pole pair)', transform=a.transAxes, ha='center', va='bottom', fontsize=4.6)
    return f

@reg
def zmult():
    f, (a, b) = fig(2, 1.05, [1.5, 0.75])

    def c(d):
        OPAMP(d)
        P = (-0.5, -0.62)
        X = (-2.9, -0.62)
        N = (-0.5, 0.62)
        xo = 3.9
        W_(d, (0, -0.62), P)
        DOT(d, P)
        C_(d, P, (-0.5, -2.0), 'C', 'bottom')
        GND(d, (-0.5, -2.0))
        R_(d, X, P, '$R_2$', 'bottom')
        DOT(d, X)
        W_(d, X, (-3.5, -0.62))
        TL(d, (-3.5, -0.62), VIN)
        W_(d, X, (-2.9, 0.62))
        R_(d, (-2.9, 0.62), N, '$R_1$')
        W_(d, (0, 0.62), N)
        DOT(d, N)
        W_(d, N, (-0.5, 1.7))
        W_(d, (-0.5, 1.7), (xo, 1.7))
        W_(d, (xo, 1.7), (xo, 0))
        W_(d, (3.42, 0), (xo, 0))
        DOT(d, (xo, 0))
        d += elm.Label().at((xo + 0.15, 0.3)).label('$V_\\mathrm{out}=V_-$', 'right')
    circuit(a, c)

    def c2(d):
        TL(d, (0, 0), '$Z_\\mathrm{in}$')
        R_(d, (0, 0), (2, 0), '$R_{eq}$')
        C_(d, (2, 0), (2, -1.6), '$C_{eq}$', 'bottom')
        GND(d, (2, -1.6))
    circuit(b, c2)
    b.text(0.5, 0.0, 'equivalent', transform=b.transAxes, ha='center', va='bottom', fontsize=4.8)
    return f

def spl_single(ax):
    splane(ax, 1.2, xl=(-1.3, 0.4), yl=(-0.7, 0.7))
    pole(ax, -0.8, 0)
    ax.text(-0.8, -0.1, '$p=-\\omega_0$', ha='center', va='top', fontsize=5)

@reg
def rc1():
    f, (a, b) = fig(2, 0.85, [1.2, 1])
    circuit(a, lambda d: two_port_passive(d, lambda: elm.Resistor().right().label('R'), [lambda: elm.Capacitor().label('C', loc='bottom')]))
    spl_single(b)
    return f

@reg
def lrc():
    f, (a, b) = fig(2, 1.05, [1.35, 1])
    circuit(a, lambda d: two_port_passive(d, lambda: elm.Inductor2().right().label('L'), [lambda: elm.Resistor().label('R', loc='bottom'), lambda: elm.Capacitor().label('C', loc='bottom')]))
    splane(b)
    th = np.deg2rad(135)
    r = 1
    pole(b, r * np.cos(th), r * np.sin(th))
    pole(b, r * np.cos(th), -r * np.sin(th))
    b.plot([0, r * np.cos(th)], [0, r * np.sin(th)], 'k--', lw=0.7)
    t = np.linspace(0, th, 50)
    b.plot(0.35 * np.cos(t), 0.35 * np.sin(t), 'k', lw=0.7)
    b.text(0.3, 0.38, '$\\theta$')
    b.text(-0.62, 0.22, '$\\omega_0=|p|$', ha='center', fontsize=5)
    b.text(-0.7, -0.95, 'conjugate at $-\\theta$', fontsize=4.6, ha='center')
    return f

@reg
def sk():
    f, (a, b) = fig(2, 1.2, [1.6, 0.85])
    circuit(a, lambda d: sk_circ(d, True))
    splane(b, 1.2, xl=(-1.25, 0.5))
    t = np.linspace(np.pi, np.pi / 2, 60)
    b.plot(np.cos(t), np.sin(t), 'k', lw=0.9)
    b.plot(np.cos(t), -np.sin(t), 'k', lw=0.9)
    pole(b, -1, 0)
    b.text(-1, -0.1, '$K=1$', ha='center', va='top', fontsize=4.6)
    b.plot([0], [1], 'ko', ms=2.5)
    b.plot([0], [-1], 'ko', ms=2.5)
    b.text(0.07, 0.85, '$K=3$', fontsize=4.6, va='center')
    th = np.deg2rad(135)
    pole(b, np.cos(th), np.sin(th))
    pole(b, np.cos(th), -np.sin(th))
    b.annotate('', xy=(np.cos(np.deg2rad(100)), np.sin(np.deg2rad(100))), xytext=(np.cos(np.deg2rad(112)), np.sin(np.deg2rad(112))), arrowprops=dict(arrowstyle='->', lw=0.7))
    b.text(-1.2, 1.0, '$K\\uparrow$', fontsize=5.5)
    b.text(-0.5, 0.2, '$\\omega_0$', fontsize=5)
    b.plot([0, np.cos(th)], [0, np.sin(th)], 'k--', lw=0.5)
    b.text(-1.2, -1.15, 'radius $\\omega_0=1/RC$', fontsize=4.4)
    return f

@reg
def act1():
    f, (a, b) = fig(2, 1.1, [1.3, 1])
    circuit(a, lambda d: inv_amp(d, fb='RC'))
    w = np.logspace(-2, 2, 300)
    H = 1 / (1 + 1j * w)
    b.plot(w, 20 * np.log10(abs(H)), 'k')
    bode_axes(b)
    b.text(0.012, 2, '$|K|=R_2/R_1$ (inverted)', fontsize=5)
    b.axvline(1, color='0.6', lw=0.5, ls=':')
    vlabel(b, 1, '$\\omega_0=1/R_2C$')
    b.set_ylim(-40, 8)
    b.text(6, -14, '$-20$ dB/dec', fontsize=5)
    return f

@reg
def integ():
    f, (a, b) = fig(2, 1.1, [0.9, 1.4])
    circuit(a, lambda d: inv_amp(d, fb='C', R1='R'))
    y = 0
    bsum(b, 1.0, y)
    barrow(b, [(0.1, y), (0.72, y)])
    b.text(0.05, y + 0.08, '$KV_\\mathrm{in}$', ha='left', va='bottom', fontsize=4.8)
    bbox_(b, 2.3, y, 0.9, 0.6, '$-\\frac{\\omega_0}{s}$', 5)
    bbox_(b, 3.9, y, 0.9, 0.6, '$-\\frac{\\omega_0}{s}$', 5)
    barrow(b, [(1.28, y), (1.85, y)])
    b.text(1.55, y + 0.08, '$V_A$', ha='center', va='bottom', fontsize=4.8)
    barrow(b, [(2.75, y), (3.45, y)])
    b.text(3.25, y + 0.08, '$V_B$', ha='center', va='bottom', fontsize=4.8)
    bdot(b, (3.05, y))
    barrow(b, [(4.35, y), (5.1, y)])
    bdot(b, (4.7, y))
    b.text(5.12, y, VOUT, ha='left', va='center', fontsize=4.8)
    barrow(b, [(3.05, y), (3.05, 0.85), (1.0, 0.85), (1.0, 0.28)])
    b.text(2.0, 0.9, '$\\times 1/Q$', ha='center', va='bottom', fontsize=4.8)
    barrow(b, [(4.7, y), (4.7, -0.85), (1.0, -0.85), (1.0, -0.28)])
    b.text(0.85, -0.45, '−', fontsize=6, ha='right')
    b.text(2.9, -1.2, 'biquad: summer + two integrators', ha='center', va='top', fontsize=4.8)
    b.set_xlim(0, 6.2)
    b.set_ylim(-1.5, 1.3)
    b.set_aspect('equal')
    b.axis('off')
    return f

@reg
def lpspec():
    f, (b,) = fig(1, 1.05)
    w = np.logspace(-1, 1, 400)
    bb, aa = signal.cheby1(5, 1, 1, analog=True)
    H = 20 * np.log10(resp(bb, aa, w))
    b.plot(w, H, 'k')
    bode_axes(b, '$f$ (log)', '$G$ dB')
    b.set_ylim(-60, 10)
    fc, fs = (1, 1.6)
    Ap, As = (3, 40)
    b.fill_between([0.1, fc], [-Ap, -Ap], [-60, -60], color='0.85', lw=0)
    b.fill_between([0.1, fc], [0.3, 0.3], [10, 10], color='0.85', lw=0)
    b.fill_between([fs, 10], [-As, -As], [10, 10], color='0.85', lw=0)
    b.text(0.11, 2, '$G_p$', fontsize=5)
    b.text(0.3, -10, '$A_p$ (max ripple below $G_p$)', fontsize=4.6)
    b.annotate('', xy=(2.3, 0), xytext=(2.3, -As), arrowprops=dict(arrowstyle='<->', lw=0.4))
    b.text(2.45, -25, '$A_s$ (min)', fontsize=5)
    b.axhline(0, color='0.5', lw=0.4, ls=':')
    vlabel(b, fc, '$f_c$')
    vlabel(b, fs, '$f_s$')
    b.text(0.12, -50, 'grey = forbidden', fontsize=4.6, color='0.35')
    return f

@reg
def types3():
    f, (b,) = fig(1, 1.05)
    w = np.logspace(-1, 1, 500)
    n = 4
    for nm, (bb, aa), ls in [('Butterworth', signal.butter(n, 1, analog=True), '-'), ('Chebyshev I', signal.cheby1(n, 1, 1, analog=True), '--'), ('Elliptic', signal.ellip(n, 1, 40, 1, analog=True), ':')]:
        b.plot(w, 20 * np.log10(resp(bb, aa, w) + 1e-09), 'k', ls=ls, lw=0.8, label=nm)
    bode_axes(b, '$f$ (log)', '$G$ dB')
    b.set_ylim(-80, 5)
    b.legend(loc='lower left', fontsize=4.6)
    b.text(1.4, -75, 'elliptic notches (zeros on $j\\omega$)', fontsize=4.5)
    b.set_title('same order n', fontsize=5, pad=1)
    return f

@reg
def sos():
    f, (a, b) = fig(2, 1.0, [1, 1])
    w = np.logspace(-1, 1, 400)
    for Q, ls in [(0.5, '-'), (1, '--'), (3, ':')]:
        a.plot(w, 20 * np.log10(abs(1 / (1 - w ** 2 + 1j * w / Q))), 'k', ls=ls, lw=0.8)
    bode_axes(a)
    a.set_ylim(-40, 15)
    a.text(0.12, 3, '$K$', fontsize=5)
    a.text(1.3, 10, '$Q\\uparrow$', fontsize=5)
    a.axvline(1, color='0.6', lw=0.5, ls=':')
    vlabel(a, 1, '$\\omega_0$')
    a.set_title('type 1', fontsize=5, pad=1)
    wz = 2
    H = (wz ** 2 - w ** 2) / (1 - w ** 2 + 1j * w / 0.8)
    b.plot(w, 20 * np.log10(abs(H) / wz ** 2 + 1e-06), 'k', lw=0.8)
    bode_axes(b)
    b.set_ylim(-50, 10)
    b.axvline(wz, color='0.6', lw=0.5, ls=':')
    vlabel(b, wz, '$\\omega_z$')
    b.set_title('type 2 (notch)', fontsize=5, pad=1)
    b.text(0.12, -30, '$H(0)=K\\omega_z^2/\\omega_0^2$', fontsize=4.6)
    return f

@reg
def topo():
    f, axs = plt.subplots(2, 1, figsize=(W, 2.1))
    a, b = axs
    circuit(a, lambda d: sk_circ(d, False))
    a.set_title('Sallen-Key (unity gain)', fontsize=5, pad=5)

    def c2(d):
        OPAMP(d)
        xo = 4.4
        A = (-3.4, 0.62)
        B = (-0.5, 0.62)
        TL(d, (-5.8, 0.62), VIN)
        R_(d, (-5.8, 0.62), A, '$R_1$')
        DOT(d, A)
        R_(d, A, B, '$R_3$')
        DOT(d, B)
        W_(d, B, (0, 0.62))
        C_(d, A, (-3.4, -1.0), '$C_1$', 'bottom')
        GND(d, (-3.4, -1.0))
        W_(d, B, (-0.5, 1.9))
        C_(d, (-0.5, 1.9), (xo, 1.9), '$C_2$')
        DOT(d, (xo, 1.9))
        W_(d, A, (-3.4, 3.2))
        R_(d, (-3.4, 3.2), (xo, 3.2), '$R_2$')
        W_(d, (xo, 3.2), (xo, 0))
        W_(d, (3.42, 0), (xo, 0))
        DOT(d, (xo, 0))
        W_(d, (xo, 0), (xo + 0.5, 0))
        TR(d, (xo + 0.5, 0), VOUT)
        W_(d, (0, -0.62), (-0.4, -0.62))
        GND(d, (-0.4, -0.62))
    circuit(b, c2)
    b.set_title('MFB (multiple feedback)', fontsize=5, pad=5)
    return f

def inv_amp(d, fb='R', R1='$R_1$', R2='$R_2$', plusR=False):
    OPAMP(d)
    n = (-0.5, 0.62)
    xo = 3.9
    W_(d, (0, 0.62), n)
    DOT(d, n)
    R_(d, (-2.6, 0.62), n, R1)
    TL(d, (-2.6, 0.62), VIN)
    W_(d, (3.42, 0), (xo, 0))
    DOT(d, (xo, 0))
    W_(d, (xo, 0), (xo + 0.5, 0))
    TR(d, (xo + 0.5, 0), VOUT)
    if fb == 'R':
        W_(d, n, (-0.5, 1.9))
        R_(d, (-0.5, 1.9), (xo, 1.9), R2)
        W_(d, (xo, 1.9), (xo, 0))
    elif fb == 'C':
        W_(d, n, (-0.5, 1.9))
        C_(d, (-0.5, 1.9), (xo, 1.9), 'C')
        W_(d, (xo, 1.9), (xo, 0))
    else:
        W_(d, n, (-0.5, 2.9))
        DOT(d, (-0.5, 1.7))
        R_(d, (-0.5, 1.7), (xo, 1.7), R2)
        C_(d, (-0.5, 2.9), (xo, 2.9), 'C')
        W_(d, (xo, 2.9), (xo, 0))
        DOT(d, (xo, 1.7))
    if plusR:
        W_(d, (0, -0.62), (-0.5, -0.62))
        R_(d, (-0.5, -0.62), (-0.5, -2.3), 'R', 'bottom')
        GND(d, (-0.5, -2.3))
    else:
        W_(d, (0, -0.62), (-0.4, -0.62))
        GND(d, (-0.4, -0.62))

def sk_circ(d, gainK=True):
    OPAMP(d)
    xo = 4.3
    A = (-3.4, -0.62)
    B = (-0.5, -0.62)
    N = (-0.5, 0.62)
    TL(d, (-5.6, -0.62), VIN)
    R_(d, (-5.6, -0.62), A, '$R_1$', 'bottom')
    DOT(d, A)
    R_(d, A, B, '$R_2$', 'bottom')
    DOT(d, B)
    W_(d, B, (0, -0.62))
    C_(d, B, (-0.5, -2.1), '$C_2$', 'bottom')
    GND(d, (-0.5, -2.1))
    W_(d, A, (-3.4, 3.3))
    C_(d, (-3.4, 3.3), (xo, 3.3), '$C_1$')
    W_(d, (xo, 3.3), (xo, 0))
    W_(d, (3.42, 0), (xo, 0))
    DOT(d, (xo, 0))
    W_(d, (xo, 0), (xo + 0.5, 0))
    TR(d, (xo + 0.5, 0), VOUT)
    W_(d, (0, 0.62), N)
    W_(d, N, (-0.5, 1.8))
    DOT(d, (xo, 1.8))
    if gainK:
        DOT(d, N)
        R_(d, (-0.5, 1.8), (xo, 1.8), '$(K-1)R_0$')
        R_(d, N, (-2.5, 0.62), '$R_0$', 'top')
        GND(d, (-2.5, 0.62))
    else:
        W_(d, (-0.5, 1.8), (xo, 1.8))

register_desc(DESC)
