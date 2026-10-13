"""Omarchy-inspired bracket mark, sampled for the GA402's 1,449 LEDs.
Run with Python, NumPy and Pillow. No desktop changes are made.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
OUT = Path(__file__).resolve().parent
PERIOD, FPS = 16, 10
HEAD = [(0,5),(1,5),(1,4),(2,4),(2,3),(3,3),(3,2),(4,2),(4,1),(5,1),(5,0),(6,0)]
RUNS = [(x,y,34) for x,y in HEAD] + [(x,0,33-(x-7)//2) for x in range(7,56)]
LEDS = [(x+i,38-y-i) for x,y,n in RUNS for i in range(n)]
PHYSICAL = np.array([((x-y)/math.sqrt(2),(x+y)/math.sqrt(2)*.65) for x,y in LEDS])
SAMPLES = PHYSICAL[:,None,:] + np.array([[-.14,-.14],[-.14,.14],[.14,-.14],[.14,.14]])
# The packaged icon's bracket language, adapted to outlines rather than a solid block.
# Main mark occupies the broad end, with negative space between nested corners.
CX,CY = 12,29
PATHS = []
def path(points, level=230, width=.85, cursor=False):
    PATHS.append((np.array(points,dtype=float),level,width,cursor))
def mark(points, **kwargs):
    path([(CX+x,CY+y) for x,y in points], **kwargs)
mark([(-1.5,-7),(-7,-7),(-7,-1.5)])
mark([(1.5,-7),(7,-7),(7,-1.5)])
mark([(7,1.5),(7,7),(1.5,7)])
mark([(-1.5,7),(-7,7),(-7,1.5)])
mark([(-4.5,-4.5),(4.5,-4.5),(4.5,4.5),(-4.5,4.5),(-4.5,-4.5)],level=190)
# One large tile and two smaller tiles; a quiet allusion to the desktop.
mark([(-.7,-4.5),(-.7,4.5)],level=125,width=.7)
mark([(-.7,0),(4.5,0)],level=125,width=.7)
# Terminal prompt in the narrow wing, with no fast blinking.
path([(-17.5,17.7),(-15.3,19.4),(-17.5,21.1)],level=205)
path([(-13.5,21.1),(-10.3,21.1)],level=220,cursor=True)

def levels(t):
    lit = np.zeros(SAMPLES.shape[:2])
    for points,level,width,cursor in PATHS:
        distance = np.full(lit.shape,np.inf)
        for a,b in zip(points,points[1:]):
            v=b-a
            f=np.clip(np.sum((SAMPLES-a)*v,axis=-1)/np.dot(v,v),0,1)
            distance=np.minimum(distance,np.linalg.norm(SAMPLES-a-f[...,None]*v,axis=-1))
        # A small 16-second raised cosine: no blink, no disappearing cursor.
        gain=.82+.18*(.5+.5*math.cos(math.tau*t/PERIOD)) if cursor else 1
        core=np.clip((width-distance)/.65,0,1)
        lit=np.maximum(lit,gain*(level*core+5*np.exp(-(distance/1.1)**2)))
    return np.clip(np.rint(lit.mean(axis=1)),0,255).astype(np.uint8)

def raw(t):
    im=Image.new('L',(74,39))
    for p,v in zip(LEDS,levels(t)): im.putpixel(p,int(v))
    return im

def preview(t):
    im=Image.new('RGB',(900,550),(8,10,14));d=ImageDraw.Draw(im)
    for (u,v),value in zip(PHYSICAL,levels(t)):
        x,y=54+(u+23.34)*16,71+(v-15.16)*16
        c=round(9+float(value)*.96)
        d.ellipse((x-3,y-3,x+3,y+3),fill=(c,c,c))
    return im

def export():
    palette=[c for i in range(256) for c in (i,i,i)]
    frames=[]
    for i in range(PERIOD*FPS):
        f=raw(i/FPS).convert('P');f.putpalette(palette);frames.append(f)
    frames[0].save(OUT/'omarchy.gif',save_all=True,append_images=frames[1:],duration=100,loop=0,disposal=1,optimize=False)
    raw(0).save(OUT/'omarchy.png');preview(0).save(OUT/'preview.png')
    previews=[preview(i/2) for i in range(PERIOD*2)]
    previews[0].save(OUT/'preview.gif',save_all=True,append_images=previews[1:],duration=500,loop=0)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-25 14 52 32">','<rect x="-25" y="14" width="52" height="32" fill="#080a0e"/>']
    for points,level,width,_ in PATHS:
        coords=' '.join(f'{x},{y}' for x,y in points)
        svg.append(f'<polyline points="{coords}" fill="none" stroke="rgb({level},{level},{level})" stroke-width="{2*(width-.325):.3f}" stroke-linecap="round" stroke-linejoin="round"/>')
    (OUT/'drawing.svg').write_text('\n'.join(svg+['</svg>'])+'\n')
    assert len(set(LEDS))==1449
    assert np.array_equal(levels(0),levels(PERIOD))
    assert np.max(np.abs(levels((PERIOD*FPS-1)/FPS).astype(int)-levels(0).astype(int)))<=1
    print('Exported static artwork and seamless 16-second cursor pulse.')
if __name__=='__main__':export()
