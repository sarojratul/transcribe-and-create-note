"""
Electromagnetics figure set (EE 301 style, Hayt and Buck notation): coordinate-system point figures with
unit vectors (RCS-CCS and RCS-SCS) and differential volume elements in RCS, CCS and SCS with edge
lengths, face normals and the surface element on each face. 2.45 in wide, 5 to 6 pt labels, symbols
only. Drawn in 2-D with a true orthographic projection (proj3), so labels never shift.

Colours: navy arrows = unit vectors / face normals, burnt orange = lengths and angles,
dark green = differential surface element on that face. Add figures with @reg + DESC.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from figlib import *
from matplotlib.patches import FancyArrowPatch, Polygon

NAVY = '#1F3864'; GRN = '#006400'; ORG = '#B34700'; GREY = '#9A9A9A'; WW = 2.45
FACE = ['#DCE6F2', '#E2EFDA', '#FCE4D6']   # light tints for the three labelled faces


class View:
    """Orthographic view from azimuth az (deg, from +x toward +y) and elevation el (deg)."""
    def __init__(self, az=30, el=20):
        a, e = np.radians(az), np.radians(el)
        self.e1 = np.array([-np.sin(a), np.cos(a), 0.0])
        self.e2 = np.array([-np.sin(e) * np.cos(a), -np.sin(e) * np.sin(a), np.cos(e)])

    def p(self, q):
        q = np.asarray(q, float)
        return np.array([q @ self.e1, q @ self.e2])

    def ps(self, qs):
        return np.array([self.p(q) for q in qs])


def _ax(h):
    f = plt.figure(figsize=(WW, h))
    ax = f.add_axes([0, 0, 1, 1]); ax.set_aspect('equal'); ax.axis('off')
    f.cs_tight = True   # hand-placed axes: cheat_figures.py crops to content at true size
    return f, ax


def arr2(ax, a, b, c=NAVY, lw=0.8, ms=5.5):
    ax.add_patch(FancyArrowPatch(tuple(a), tuple(b), arrowstyle='-|>', mutation_scale=ms, color=c, lw=lw, shrinkA=0, shrinkB=0))


def arr3(ax, V, q0, q1, **kw):
    arr2(ax, V.p(q0), V.p(q1), **kw)


def line3(ax, V, qs, c='k', lw=0.7, ls='-'):
    P = V.ps(qs); ax.plot(P[:, 0], P[:, 1], color=c, lw=lw, ls=ls, solid_capstyle='round')


def face3(ax, V, qs, fc, ec='k', lw=0.6):
    ax.add_patch(Polygon(V.ps(qs), closed=True, fc=fc, ec=ec, lw=lw, joinstyle='round'))


def txt3(ax, V, q, s, c='k', fs=5.5, ha='center', va='center', dx=0.0, dy=0.0):
    x, y = V.p(q); ax.text(x + dx, y + dy, s, color=c, fontsize=fs, ha=ha, va=va)


def axes3(ax, V, L=(1.9, 1.9, 1.9), fs=6):
    for k, (lab, n) in enumerate(zip('xyz', L)):
        e = np.zeros(3); e[k] = n
        arr3(ax, V, (0, 0, 0), e, c='k', lw=0.6, ms=5)
        x, y = V.p(e * 1.07); ax.text(x, y, '$' + lab + '$', fontsize=fs, ha='center', va='center')


def cyl(r, ph, z):
    return np.array([r * np.cos(ph), r * np.sin(ph), z])


def sph(r, th, ph):
    return np.array([r * np.sin(th) * np.cos(ph), r * np.sin(th) * np.sin(ph), r * np.cos(th)])


def fit(ax, V, pts, pad=0.12):
    P = V.ps(pts); ax.set_xlim(P[:, 0].min() - pad, P[:, 0].max() + pad); ax.set_ylim(P[:, 1].min() - pad, P[:, 1].max() + pad)


# ---------------------------------------------------------------- point and unit vectors
@reg
def em_point_ccs():
    """P(x,y,z) = P(rho,phi,z) with the projections and a_rho, a_phi, a_z at P."""
    V = View(30, 20); f, ax = _ax(1.75)
    axes3(ax, V, (1.7, 2.0, 1.55))
    rho, ph, z = 1.25, np.radians(55), 0.95
    P = cyl(rho, ph, z); Pp = cyl(rho, ph, 0)
    line3(ax, V, [(0, 0, 0), Pp], c=ORG, lw=0.9)
    line3(ax, V, [Pp, P], c=ORG, lw=0.9)
    line3(ax, V, [Pp, (Pp[0], 0, 0)], c=GREY, ls='--', lw=0.6)
    line3(ax, V, [Pp, (0, Pp[1], 0)], c=GREY, ls='--', lw=0.6)
    t = np.linspace(0, ph, 30); line3(ax, V, [cyl(0.42, a, 0) for a in t], c=ORG, lw=0.7)
    txt3(ax, V, cyl(0.62, ph / 2, 0), r'$\phi$', c=ORG, fs=6)
    txt3(ax, V, cyl(rho * 0.55, ph, 0), r'$\rho$', c=ORG, fs=6, dx=0.08, dy=0.06)
    txt3(ax, V, (Pp + P) / 2, '$z$', c=ORG, fs=6, dx=0.08)
    txt3(ax, V, (Pp[0] / 2, Pp[1], 0), r'$x=\rho\cos\phi$', fs=5, ha='left', dx=0.06, dy=-0.04)
    txt3(ax, V, (Pp[0], Pp[1] / 2, 0), r'$y=\rho\sin\phi$', fs=5, ha='right', dx=-0.02, dy=-0.12)
    ax.plot(*V.p(P), 'o', color='k', ms=2.2)
    L = 0.55
    arr3(ax, V, P, P + L * cyl(1, ph, 0)); txt3(ax, V, P + 1.18 * L * cyl(1, ph, 0), r'$\mathbf{a}_\rho$', c=NAVY, fs=6)
    aph = np.array([-np.sin(ph), np.cos(ph), 0])
    arr3(ax, V, P, P + L * aph); txt3(ax, V, P + 1.25 * L * aph, r'$\mathbf{a}_\phi$', c=NAVY, fs=6)
    arr3(ax, V, P, P + (0, 0, L)); txt3(ax, V, P + (0, 0, 1.22 * L), r'$\mathbf{a}_z$', c=NAVY, fs=6)
    txt3(ax, V, P, r'$P(x,y,z)=P(\rho,\phi,z)$', fs=5, ha='right', dx=-0.08, dy=0.1)
    fit(ax, V, [(0, 0, 0), (1.85, 0, 0), (0, 2.15, 0), (0, 0, 1.7), P + (0, 0, 0.7), P + 0.7 * aph], pad=0.1)
    return f
register_desc({'em_point_ccs': 'RCS <-> CCS: point P(rho, phi, z) with x = rho cos phi, y = rho sin phi and unit vectors a_rho, a_phi, a_z at P'})


@reg
def em_point_scs():
    """P(r,theta,phi) with rho = r sin theta, z = r cos theta and a_r, a_theta, a_phi at P."""
    V = View(30, 20); f, ax = _ax(1.85)
    axes3(ax, V, (1.6, 1.9, 1.75))
    r, th, ph = 1.6, np.radians(45), np.radians(55)
    P = sph(r, th, ph); Pp = np.array([P[0], P[1], 0]); Z = np.array([0, 0, P[2]])
    line3(ax, V, [(0, 0, 0), P], c=ORG, lw=0.9)
    line3(ax, V, [Z, P], c=GREY, ls='--', lw=0.6)
    line3(ax, V, [P, Pp], c=GREY, ls='--', lw=0.6)
    line3(ax, V, [(0, 0, 0), Pp], c=GREY, ls='--', lw=0.6)
    t = np.linspace(0, th, 30); line3(ax, V, [sph(0.5, a, ph) for a in t], c=ORG, lw=0.7)
    txt3(ax, V, sph(0.68, th / 2, ph), r'$\theta$', c=ORG, fs=6)
    t = np.linspace(0, ph, 30); line3(ax, V, [cyl(0.42, a, 0) for a in t], c=ORG, lw=0.7)
    txt3(ax, V, cyl(0.6, ph / 2, 0), r'$\phi$', c=ORG, fs=6)
    txt3(ax, V, P * 0.55, '$r$', c=ORG, fs=6, dx=0.07, dy=0.03)
    txt3(ax, V, (Z + P) / 2, r'$\rho=r\sin\theta$', fs=5, dx=-0.08, dy=0.09)
    txt3(ax, V, P + (Pp - P) * 0.72, r'$z=r\cos\theta$', fs=5, ha='left', dx=0.04)
    ax.plot(*V.p(P), 'o', color='k', ms=2.2)
    L = 0.55
    ar = sph(1, th, ph); at = np.array([np.cos(th) * np.cos(ph), np.cos(th) * np.sin(ph), -np.sin(th)]); ap = np.array([-np.sin(ph), np.cos(ph), 0])
    arr3(ax, V, P, P + L * ar); txt3(ax, V, P + 1.2 * L * ar, r'$\mathbf{a}_r$', c=NAVY, fs=6)
    arr3(ax, V, P, P + L * at); txt3(ax, V, P + 1.3 * L * at, r'$\mathbf{a}_\theta$', c=NAVY, fs=6, dx=0.06)
    arr3(ax, V, P, P + L * ap); txt3(ax, V, P + 1.25 * L * ap, r'$\mathbf{a}_\phi$', c=NAVY, fs=6)
    txt3(ax, V, P + 1.2 * L * ap, r'$P(r,\theta,\phi)$', fs=5, ha='left', dx=0.03, dy=0.17)
    fit(ax, V, [(0, 0, 0), (1.75, 0, 0), (0, 2.05, 0), (0, 0, 1.9), P + 0.75 * ar, P + 0.75 * ap, P + 0.75 * at], pad=0.1)
    return f
register_desc({'em_point_scs': 'RCS <-> SCS: point P(r, theta, phi) with rho = r sin theta, z = r cos theta and unit vectors a_r, a_theta, a_phi at P'})


# ---------------------------------------------------------------- differential elements
def _normal(ax, V, c, n, lab, dS, L=0.42, side='right'):
    arr3(ax, V, c, c + L * np.asarray(n)); tip = c + 1.12 * L * np.asarray(n)
    x, y = V.p(tip)
    ha = {'right': 'left', 'left': 'right', 'top': 'center'}[side]
    dx = {'right': 0.03, 'left': -0.03, 'top': 0}[side]; dy = 0.09 if side == 'top' else 0
    ax.text(x + dx, y + dy, lab + '  ' + dS if side != 'top' else dS + '  ' + lab, color=NAVY, fontsize=5.5, ha=ha, va='center')


@reg
def em_diff_rcs():
    """Box dx dy dz with the three visible faces, their normals and dS."""
    V = View(30, 22); f, ax = _ax(1.45)
    o = np.array([0.0, 0.0, 0.0]); dx, dy, dz = 0.9, 1.15, 0.85
    X, Y, Z = np.array([dx, 0, 0]), np.array([0, dy, 0]), np.array([0, 0, dz])
    face3(ax, V, [o + X, o + X + Y, o + X + Y + Z, o + X + Z], FACE[0])          # x face (normal a_x)
    face3(ax, V, [o + Y, o + X + Y, o + X + Y + Z, o + Y + Z], FACE[1])          # y face
    face3(ax, V, [o + Z, o + X + Z, o + X + Y + Z, o + Y + Z], FACE[2])          # z face
    txt3(ax, V, o + X + Y / 2, '$dy$', c=ORG, dy=-0.1)
    txt3(ax, V, o + Y + X / 2, '$dx$', c=ORG, dx=0.05, dy=-0.08)
    txt3(ax, V, o + X + Y + Z / 2, '$dz$', c=ORG, dx=0.1)
    cx = o + X + Y / 2 + Z / 2; cy = o + Y + X / 2 + Z / 2; cz = o + Z + X / 2 + Y / 2
    _normal(ax, V, cx, (1, 0, 0), r'$\mathbf{a}_x$', r'$dy\,dz$', side='left')
    _normal(ax, V, cy, (0, 1, 0), r'$\mathbf{a}_y$', r'$dx\,dz$', side='right')
    _normal(ax, V, cz, (0, 0, 1), r'$\mathbf{a}_z$', r'$dx\,dy$', side='top')
    ax.text(0.99, 0.99, r'$dv=dx\,dy\,dz$', transform=ax.transAxes, ha='right', va='top', fontsize=5.5, color=GRN)
    fit(ax, V, [o, o + X + Y + Z, cx + 0.8 * X, cy + 1.2 * Y, cz + 0.65 * np.array([0, 0, 1])], pad=0.38)
    return f
register_desc({'em_diff_rcs': 'RCS differential element: edges dx, dy, dz; faces with normals a_x, a_y, a_z and dS = dy dz, dx dz, dx dy'})


@reg
def em_diff_ccs():
    """Cylindrical element: edges d rho, rho d phi, dz; normals a_rho, a_phi, a_z and dS on each face."""
    V = View(62, 22); f, ax = _ax(1.75)
    axes3(ax, V, (1.45, 1.75, 1.45))
    r0, dr, p0, dp, z0, dz = 1.05, 0.42, np.radians(18), np.radians(28), 0.5, 0.5
    r1, p1, z1 = r0 + dr, p0 + dp, z0 + dz
    t = np.linspace(p0, p1, 24)
    outer = [cyl(r1, a, z0) for a in t] + [cyl(r1, a, z1) for a in t[::-1]]
    top = [cyl(r1, a, z1) for a in t] + [cyl(r0, a, z1) for a in t[::-1]]
    side = [cyl(r0, p1, z0), cyl(r1, p1, z0), cyl(r1, p1, z1), cyl(r0, p1, z1)]
    face3(ax, V, side, FACE[1]); face3(ax, V, outer, FACE[0]); face3(ax, V, top, FACE[2])
    txt3(ax, V, cyl((r0 + r1) / 2, p1, z0), r'$d\rho$', c=ORG, dy=-0.1, dx=0.12)
    txt3(ax, V, cyl(r1, (p0 + p1) / 2, z0), r'$\rho\,d\phi$', c=ORG, dy=-0.1)
    txt3(ax, V, cyl(r1, p0, (z0 + z1) / 2), '$dz$', c=ORG, dx=-0.1)
    pm, zm, rm = (p0 + p1) / 2, (z0 + z1) / 2, (r0 + r1) / 2
    _normal(ax, V, cyl(r1, pm, zm), cyl(1, pm, 0), r'$\mathbf{a}_\rho$', r'$\rho\,d\phi\,dz$', side='left', L=0.55)
    _normal(ax, V, cyl(rm, p1, zm), np.array([-np.sin(p1), np.cos(p1), 0]), r'$\mathbf{a}_\phi$', r'$d\rho\,dz$', side='right')
    _normal(ax, V, cyl(rm, pm, z1), (0, 0, 1), r'$\mathbf{a}_z$', r'$\rho\,d\rho\,d\phi$', side='top')
    ax.text(0.99, 0.99, r'$dv=\rho\,d\rho\,d\phi\,dz$', transform=ax.transAxes, ha='right', va='top', fontsize=5.5, color=GRN)
    fit(ax, V, [(0, 0, 0), (1.6, 0, 0), (0, 1.95, 0), (0, 0, 1.6), cyl(r1 + 0.8, pm, zm)], pad=0.1)
    return f
register_desc({'em_diff_ccs': 'CCS differential element: edges d rho, rho d phi, dz; normals a_rho, a_phi, a_z with dS = rho d phi dz, d rho dz, rho d rho d phi'})


@reg
def em_diff_scs():
    """Spherical element: edges dr, r d theta, r sin theta d phi; normals a_r, a_theta, a_phi and dS."""
    V = View(62, 18); f, ax = _ax(1.9)
    axes3(ax, V, (1.5, 1.8, 1.75))
    R = 1.5
    for args in [(np.linspace(0, np.pi / 2, 40), 0), (np.linspace(0, np.pi / 2, 40), np.pi / 2)]:
        line3(ax, V, [sph(R, a, args[1]) for a in args[0]], c=GREY, lw=0.5)
    line3(ax, V, [cyl(R, a, 0) for a in np.linspace(0, np.pi / 2, 40)], c=GREY, lw=0.5)
    r0, dr, t0, dt, p0, dp = 1.0, 0.42, np.radians(42), np.radians(22), np.radians(10), np.radians(30)
    r1, t1, p1 = r0 + dr, t0 + dt, p0 + dp
    T = np.linspace(t0, t1, 20); P = np.linspace(p0, p1, 20)
    outer = [sph(r1, t0, a) for a in P] + [sph(r1, b, p1) for b in T] + [sph(r1, t1, a) for a in P[::-1]] + [sph(r1, b, p0) for b in T[::-1]]
    lower = [sph(r0, t1, a) for a in P] + [sph(r1, t1, a) for a in P[::-1]]          # theta = t1 cone face (normal a_theta)
    side = [sph(r0, b, p1) for b in T] + [sph(r1, b, p1) for b in T[::-1]]           # phi = p1 face (normal a_phi)
    face3(ax, V, lower, FACE[2]); face3(ax, V, side, FACE[1]); face3(ax, V, outer, FACE[0])
    txt3(ax, V, sph((r0 + r1) / 2, t0, p1), '$dr$', c=ORG, dx=0.05, dy=0.08)
    txt3(ax, V, sph(r1, t1 - dt * 0.2, p0), r'$r\,d\theta$', c=ORG, ha='right', dx=-0.05)
    txt3(ax, V, sph(r1, t0, (p0 + p1) / 2), r'$r\sin\theta\,d\phi$', c=ORG, ha='left', dx=-0.05, dy=0.12)
    tm, pm, rm = (t0 + t1) / 2, (p0 + p1) / 2, (r0 + r1) / 2
    at = lambda th, ph: np.array([np.cos(th) * np.cos(ph), np.cos(th) * np.sin(ph), -np.sin(th)])
    _normal(ax, V, sph(r1, tm, pm), sph(1, tm, pm), r'$\mathbf{a}_r$', r'$r^2\sin\theta\,d\theta\,d\phi$', side='left', L=0.5)
    _normal(ax, V, sph(rm, tm, p1), np.array([-np.sin(p1), np.cos(p1), 0]), r'$\mathbf{a}_\phi$', r'$r\,dr\,d\theta$', side='right')
    _normal(ax, V, sph(rm, t1, pm), at(t1, pm), r'$\mathbf{a}_\theta$', r'$r\sin\theta\,dr\,d\phi$', side='right', L=0.38)
    ax.text(0.01, 0.99, r'$dv=r^2\sin\theta\,dr\,d\theta\,d\phi$', transform=ax.transAxes, ha='left', va='top', fontsize=5.5, color=GRN)
    fit(ax, V, [(0, 0, 0), (1.65, 0, 0), (0, 1.95, 0), (0, 0, 1.9), sph(r1 + 1.0, tm, pm)], pad=0.08)
    return f
register_desc({'em_diff_scs': 'SCS differential element: edges dr, r d theta, r sin theta d phi; normals a_r, a_theta, a_phi with dS = r^2 sin theta d theta d phi, r sin theta dr d phi, r dr d theta'})
