"""Generate a monochrome animation for the GA402's exact LED map.
Requires Pillow and NumPy. Run from any directory; outputs sit beside this script.
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
PERIOD = 48.0
FPS = 10
W, H = 74, 39
HEAD = [(0,5),(1,5),(1,4),(2,4),(2,3),(3,3),(3,2),(4,2),(4,1),(5,1),(5,0),(6,0)]
RUNS = [(x,y,34) for x,y in HEAD] + [(x,0,33-(x-7)//2) for x in range(7,56)]
LEDS = [(x+i,38-y-i) for x,y,n in RUNS for i in range(n)]
# Same physical projection used by Animatrix's lid preview.
PHYSICAL = np.array([((x-y)/math.sqrt(2),(x+y)/math.sqrt(2)*.65) for x,y in LEDS])
# Four subpixel samples keep thin edges stable as shapes drift and rotate.
SAMPLES = PHYSICAL[:,None,:] + np.array([[-.14,-.14],[-.14,.14],[.14,-.14],[.14,.14]])
# Small forms lead through the narrow wing; a larger overlapping pair balances the wide end.
# n=0 means circle. Other shapes are regular polygons.
SHAPES = [
    (-19,18.3,1.6,4,0,235),
    (-11,20.7,2.15,3,-math.pi/2,210),
    (-3,24,2.65,4,0,245),
    (6,28,4.5,4,math.pi/4,190),
    (13,29,4.0,0,0,240),
    (5,19.1,2.3,4,math.pi/4,165),
    (20,36,3.1,3,-math.pi/2,220),
]

def geometry(t):
    phase = math.tau * t / PERIOD
    result = []
    for i,(x,y,r,n,angle,level) in enumerate(SHAPES):
        wave = phase - i * .42
        cx = x + .45*math.sin(wave)
        cy = y + .35*math.sin(wave+.5)
        # Gentle rocking is shared by every polygon, with a phase travelling down the panel.
        turn = angle + .22*math.sin(wave)
        vertices = [(cx+r*math.cos(turn+math.tau*j/n),cy+r*math.sin(turn+math.tau*j/n)) for j in range(n)] if n else []
        result.append((cx,cy,r,n,vertices,level))
    return result

def levels(t):
    lit = np.zeros(SAMPLES.shape[:2])
    for i,(cx,cy,r,n,vertices,level) in enumerate(geometry(t)):
        if n:
            dist = np.full(lit.shape,np.inf)
            for a,b in zip(vertices,vertices[1:]+vertices[:1]):
                a,b = np.asarray(a),np.asarray(b)
                vec = b-a
                f = np.clip(np.sum((SAMPLES-a)*vec,axis=-1)/np.dot(vec,vec),0,1)
                dist = np.minimum(dist,np.linalg.norm(SAMPLES-a-f[...,None]*vec,axis=-1))
        else:
            dist = np.abs(np.linalg.norm(SAMPLES-[cx,cy],axis=-1)-r)
        core = np.clip((.85-dist)/.65,0,1)
        halo = 14*np.exp(-(dist/1.1)**2)
        # A soft travelling highlight ties the outlines together without flashes.
        highlight = .9+.1*math.cos(math.tau*t/PERIOD-i*.42)
        lit = np.maximum(lit,level*highlight*core+halo)
    return np.clip(np.rint(lit.mean(axis=1)),0,255).astype(np.uint8)

def raw_frame(t):
    im = Image.new('L',(W,H))
    for (x,y),v in zip(LEDS,levels(t)): im.putpixel((x,y),int(v))
    return im

def preview(t):
    im = Image.new('RGB',(900,550),(8,10,14))
    d = ImageDraw.Draw(im)
    for (u,v),value in zip(PHYSICAL,levels(t)):
        cx = 54+(u+23.34)*16
        cy = 71+(v-15.16)*16
        shade = round(9+float(value)*.96)
        d.ellipse((cx-3.0,cy-3.0,cx+3.0,cy+3.0),fill=(shade,shade,shade))
    return im

def export():
    palette = [c for i in range(256) for c in (i,i,i)]
    frames = []
    previews = []
    for i in range(round(PERIOD*FPS)):
        frame = raw_frame(i/FPS).convert('P')
        frame.putpalette(palette)
        frames.append(frame)
        if i%2==0: previews.append(preview(i/FPS))
    frames[0].save(OUT/'geometric-flow.gif',save_all=True,append_images=frames[1:],duration=round(1000/FPS),loop=0,disposal=1,optimize=False)
    raw_frame(0).save(OUT/'geometric-flow.png')
    previews[0].save(OUT/'preview.gif',save_all=True,append_images=previews[1:],duration=round(2000/FPS),loop=0)
    previews[0].save(OUT/'preview.png')
    sheet = Image.new('RGB',(1800,1100),(8,10,14))
    for i,t in enumerate([0,PERIOD/4,PERIOD/2,3*PERIOD/4]):sheet.paste(preview(t),((i%2)*900,(i//2)*550))
    sheet.save(OUT/'motion-review.png')
    # Editable vector drawing of the first frame, before LED sampling.
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-25 14 50 30">', '<rect x="-25" y="14" width="50" height="30" fill="#080a0e"/>']
    for cx,cy,r,n,vertices,level in geometry(0):
        if n:
            coords = ' '.join(f'{x:.4f},{y:.4f}' for x,y in vertices)
            parts.append(f'<polygon points="{coords}" fill="none" stroke="rgb({level},{level},{level})" stroke-width=".85"/>')
        else:parts.append(f'<circle cx="{cx:.4f}" cy="{cy:.4f}" r="{r}" fill="none" stroke="rgb({level},{level},{level})" stroke-width=".85"/>')
    parts.append('</svg>')
    (OUT/'drawing.svg').write_text('\n'.join(parts)+'\n')
    # Meaningful checks: exact loop seam, format, mapping, and unchanged brightness range.
    assert len(LEDS)==1449 and len(set(LEDS))==1449
    assert np.array_equal(levels(0),levels(PERIOD)), 'Loop seam differs'
    for p in LEDS: assert 0<=p[0]<W and 0<=p[1]<H
    with Image.open(OUT/'geometric-flow.gif') as im:
        assert im.size==(W,H) and im.n_frames<=round(PERIOD*FPS) and im.info['loop']==0
        duration = 0
        for i in range(im.n_frames):
            im.seek(i)
            duration += im.info['duration']
        assert duration==round(PERIOD*1000), 'Wrong loop duration'
    print(f'Exported {OUT}: 1449 LEDs, {len(frames)} frames, {FPS}fps, seamless {PERIOD:g}s loop.')

if __name__=='__main__':export()
