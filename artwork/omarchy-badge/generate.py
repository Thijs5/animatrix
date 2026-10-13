"""Omarchy corner badge with restrained VHS-style glitches, sampled for the GA402's 1,449 LEDs.
Run with Python, NumPy and Pillow. No desktop changes are made.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw
OUT = Path(__file__).resolve().parent
PERIOD, FPS = 40, 10
HEAD = [(0,5),(1,5),(1,4),(2,4),(2,3),(3,3),(3,2),(4,2),(4,1),(5,1),(5,0),(6,0)]
RUNS = [(x,y,34) for x,y in HEAD] + [(x,0,33-(x-7)//2) for x in range(7,56)]
LEDS = [(x+i,38-y-i) for x,y,n in RUNS for i in range(n)]
PHYSICAL = np.array([((x-y)/math.sqrt(2),(x+y)/math.sqrt(2)*.65) for x,y in LEDS])
SAMPLES = PHYSICAL[:,None,:] + np.array([[-.14,-.14],[-.14,.14],[.14,-.14],[.14,.14]])
# Exact stepped O silhouette from /usr/share/omarchy/logo.svg.
# Deliberate upper-right badge placement with generous dark space around it.
CENTER = np.array([14.0,25.0])
SCALE = 10 / 240
OUTER = np.array([(105,30),(120,30),(120,45),(135,45),(135,225),
 (120,225),(120,240),(105,240),(105,255),(30,255),(30,240),
 (15,240),(15,225),(0,225),(0,45),(15,45),(15,30),(30,30),
 (30,15),(105,15)],dtype=float)
INNER = np.array([(45,45),(90,45),(90,225),(45,225)],dtype=float)
OUTER = (OUTER-[67.5,135])*SCALE+CENTER
INNER = (INNER-[67.5,135])*SCALE+CENTER
# Sixteen coverage samples preserve the squared steps and inner opening.
SAMPLES = PHYSICAL[:,None,:] + np.array([(x,y) for x in [-.3,-.1,.1,.3] for y in [-.3,-.1,.1,.3]])
def inside(poly, samples=SAMPLES):
    x,y = samples[...,0],samples[...,1]
    result = np.zeros(x.shape,dtype=bool)
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        if a[1]==b[1]: continue
        cross = ((a[1]>y)!=(b[1]>y)) & (x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])
        result ^= cross
    return result
FILLED = inside(OUTER) & ~inside(INNER)
COVERAGE = FILLED.mean(axis=1)
# Distance to either silhouette boundary; light only the unfilled surroundings.
DISTANCE = np.full(FILLED.shape,np.inf)
for poly in [OUTER, INNER]:
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        v = b-a
        f = np.clip(np.sum((SAMPLES-a)*v,axis=-1)/np.dot(v,v),0,1)
        DISTANCE = np.minimum(DISTANCE,np.linalg.norm(SAMPLES-a-f[...,None]*v,axis=-1))
HALO = (~FILLED)*np.exp(-(DISTANCE/1.05)**2)
def sampled(samples):
    filled = inside(OUTER,samples) & ~inside(INNER,samples)
    distance = np.full(filled.shape,np.inf)
    for poly in [OUTER,INNER]:
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            v=b-a
            f=np.clip(np.sum((samples-a)*v,axis=-1)/np.dot(v,v),0,1)
            distance=np.minimum(distance,np.linalg.norm(samples-a-f[...,None]*v,axis=-1))
    halo=(~filled)*np.exp(-(distance/1.05)**2)
    return np.rint((218*filled+14*halo).mean(axis=1)).astype(np.uint8)
BASE = sampled(SAMPLES)
STATES = {}
# Two short incidents in forty seconds, with no full-panel flash or noise.
EVENTS = [(11.0,-2.0,.9,[.85,-.5,.4]),(28.0,2.0,.8,[-.8,.5])]
for event,(_,height,width,shifts) in enumerate(EVENTS):
    rows = np.abs(SAMPLES[...,1]-(CENTER[1]+height))<width
    for frame,shift in enumerate(shifts):
        displaced=SAMPLES.copy()
        displaced[...,0] -= rows*shift
        STATES[event,frame]=sampled(displaced)
def levels(t):
    phase=t%PERIOD
    for event,(start,_,_,shifts) in enumerate(EVENTS):
        if start<=phase<start+.2*len(shifts):
            frame=min(int(round((phase-start)*10))//2,len(shifts)-1)
            return STATES[event,frame]
    return BASE

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
    raw(0).save(OUT/'omarchy.png');preview(11).save(OUT/'preview.png')
    sheet=Image.new('RGB',(1800,1100),(8,10,14))
    for i,t in enumerate([0,11,11.2,28]): sheet.paste(preview(t),((i%2)*900,(i//2)*550))
    sheet.save(OUT/'motion-review.png')
    previews=[preview(i/5) for i in range(PERIOD*5)]
    previews[0].save(OUT/'preview.gif',save_all=True,append_images=previews[1:],duration=200,loop=0)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-25 14 52 32">','<rect x="-25" y="14" width="52" height="32" fill="#080a0e"/>']
    contours=[]
    for poly in [OUTER,INNER]:
        contours.append('M'+' L'.join(f'{x:.4f},{y:.4f}' for x,y in poly)+' Z')
    svg.append('<path d="'+' '.join(contours)+'" fill="#e4e4e4" fill-rule="evenodd"/>')
    (OUT/'drawing.svg').write_text('\n'.join(svg+['</svg>'])+'\n')
    assert np.array_equal(levels(0),levels(10))
    assert not np.array_equal(levels(0),levels(11))
    assert np.count_nonzero(levels(0)!=levels(11))<100, 'Glitch must be local'
    assert len(set(LEDS))==1449
    assert np.array_equal(levels(0),levels(PERIOD))
    assert np.max(np.abs(levels((PERIOD*FPS-1)/FPS).astype(int)-levels(0).astype(int)))<=1
    print('Exported static artwork and seamless 40-second restrained glitch loop.')
if __name__=='__main__':export()
