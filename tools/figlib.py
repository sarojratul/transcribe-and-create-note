"""
figlib.py: drawing helpers for cheat-sheet design figures (used by cheat_figures.py).

Conventions: one PNG per entry, W = 2.3 in wide, 6 pt fonts, black lines, dpi 400.
  fig(n, h, ratios)        -> figure + n axes side by side (circuit left, plot right)
  circuit(ax, build)       -> draw a schemdraw circuit (build(d)) onto a matplotlib axes
  W_/R_/C_(d, a, b, lab)   -> wire / resistor / capacitor between explicit points (no crossings)
  DOT, GND, TL, TR         -> junction dot, ground, left/right open terminal with label
  OPAMP(d)                 -> op-amp with leads: in1(-)=(0,0.62), in2(+)=(0,-0.62), out=(3.42,0)
  splane(ax, lim, xl, yl)  -> s-plane axes (sigma, j omega); pole(ax,x,y), zero(ax,x,y)
  bode_axes(ax, xl, yl)    -> log-x axes without ticks; vlabel(ax, x, text) labels a frequency
                              inside the axes so it never collides with the axis title
  bbox_, bsum, barrow, bdot -> block-diagram boxes, summer, arrows, dots (matplotlib only)
  save(fig, path)
Labels are symbols only (omega_0, theta, |p|, K = 3, -20 dB/dec), never example values.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import schemdraw
import schemdraw.elements as elm
plt.rcParams.update({'font.size':6,'font.family':'DejaVu Sans','mathtext.fontset':'dejavusans',
    'axes.linewidth':0.6,'lines.linewidth':0.9,'xtick.major.size':0,'ytick.major.size':0,
    'axes.labelsize':6,'legend.fontsize':5,'legend.frameon':False})
FS=6
W=2.3
def fig(n=2, h=1.0, ratios=None):
    f,axs=plt.subplots(1,n,figsize=(W,h),gridspec_kw={'width_ratios':ratios} if ratios else None)
    if n==1: axs=[axs]
    return f,list(axs)
def circuit(ax, build, unit=2.0):
    d=schemdraw.Drawing(show=False)
    d.config(fontsize=FS, lw=0.8, unit=unit, inches_per_unit=0.25)
    build(d)
    d.draw(show=False, canvas=ax)
    ax.set_aspect('equal'); ax.axis('off')
    bb=d.get_bbox(); m=0.15
    ax.set_xlim(bb.xmin-m, bb.xmax+m); ax.set_ylim(bb.ymin-m, bb.ymax+m)
    return d
def splane(ax, lim=1.25, xl=None, yl=None):
    ax.axhline(0,color='k',lw=0.6); ax.axvline(0,color='k',lw=0.6)
    ax.set_xlim(-lim if xl is None else xl[0], lim*0.6 if xl is None else xl[1])
    ax.set_ylim(-lim if yl is None else yl[0], lim if yl is None else yl[1])
    ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)
    ax.text(ax.get_xlim()[1],0.02*lim*4,r'$\sigma$',ha='right',va='bottom')
    ax.text(0.04*lim,ax.get_ylim()[1],r'$j\omega$',ha='left',va='top')
def pole(ax,x,y,ms=4): ax.plot([x],[y],'kx',ms=ms,mew=0.9)
def zero(ax,x,y,ms=3.5): ax.plot([x],[y],'o',mfc='white',mec='k',ms=ms,mew=0.8)
def bode_axes(ax, xlabel=r'$\omega$ (log)', ylabel=r'$|H|$ dB'):
    ax.set_xscale('log'); ax.set_xticks([]); ax.set_yticks([]); ax.minorticks_off()
    ax.set_xlabel(xlabel,labelpad=1); ax.set_ylabel(ylabel,labelpad=1)
    for s in ['top','right']: ax.spines[s].set_visible(False)
def save(f, path):
    f.tight_layout(pad=0.15, w_pad=0.4)
    f.savefig(path, dpi=400, facecolor='white')
    plt.close(f)

import matplotlib.transforms as mtrans
def vlabel(ax, x, text, y=0.02, ha='center', fs=5):
    ax.text(x, y, text, transform=ax.get_xaxis_transform(), ha=ha, va='bottom', fontsize=fs,
            bbox=dict(fc='white', ec='none', pad=0.3))
# ---- explicit-coordinate schematic helpers
def W_(d,a,b): d += elm.Line().endpoints(a,b)
def R_(d,a,b,lab=None,loc='top'):
    e=elm.Resistor().endpoints(a,b)
    if lab: e=e.label(lab,loc=loc)
    d += e
def C_(d,a,b,lab=None,loc='top'):
    e=elm.Capacitor().endpoints(a,b)
    if lab: e=e.label(lab,loc=loc)
    d += e
def DOT(d,p): d += elm.Dot().at(p)
def GND(d,p): d += elm.Ground().at(p)
def TL(d,p,lab): d += elm.Dot(open=True).at(p).label(lab,'left')
def TR(d,p,lab): d += elm.Dot(open=True).at(p).label(lab,'right')
def OPAMP(d): 
    op=elm.Opamp(leads=True); d += op; return op   # in1(-)=(0,.62) in2(+)=(0,-.62) out=(3.42,0)
# ---- matplotlib block diagram helpers
from matplotlib.patches import Rectangle, Circle
def bbox_(ax,x,y,w,h,t,fs=5.5):
    ax.add_patch(Rectangle((x-w/2,y-h/2),w,h,fill=False,lw=0.8)); ax.text(x,y,t,ha='center',va='center',fontsize=fs)
def bsum(ax,x,y,r=0.28):
    ax.add_patch(Circle((x,y),r,fill=False,lw=0.8)); ax.text(x,y,r'$\Sigma$',ha='center',va='center',fontsize=6)
def barrow(ax,pts,arrow=True):
    for i in range(len(pts)-1):
        a,b=pts[i],pts[i+1]
        if arrow and i==len(pts)-2:
            ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='-|>',lw=0.8,mutation_scale=5,shrinkA=0,shrinkB=0,color='k'))
        else: ax.plot([a[0],b[0]],[a[1],b[1]],'k',lw=0.8)
def bdot(ax,p): ax.plot([p[0]],[p[1]],'k.',ms=3)
def bfin(ax):
    ax.set_aspect('equal'); ax.axis('off'); ax.autoscale_view()
