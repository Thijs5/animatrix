"""Slow polygon collisions inside the GA402 AniMe Matrix silhouette.
Run with Pillow and NumPy. Uses the adjacent geometric-flow renderer's LED mapping.
"""
from pathlib import Path
import importlib.util
import math
import json
import numpy as np
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('flow', OUT.parent/'geometric-flow/generate.py')
flow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(flow)
PERIOD, SIM_TIME, FPS, DT = 180.0, 72.0, 10, .05
STROKE_MARGIN, GAP = 1.0, .65
# x,y,radius,sides,angle,brightness; circles are approximated by 24 sides for collisions.
BODIES = [
    (-15,19.2,1.7,4,.37,235),
    (11,20.5,2.5,3,.68,225),
    (1,29,2.7,6,.19,220),
    (19,37,2.6,0,0,235),
]
# Uneven positions and independent headings avoid an orderly starting formation.
VELOCITIES = np.array([(.14,.05),(-.08,.17),(.14,-.055),(-.17,-.07)])
SPINS = np.array([.007,-.008,.005,0.0])
RADII = np.array([b[2] for b in BODIES])
MASSES = RADII**2
INV_MASS = 1/MASSES


def convex_hull(points):
    points = sorted(set(map(tuple,points)))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo,hi = [],[]
    for p in points:
        while len(lo)>1 and cross(lo[-2],lo[-1],p)<=1e-8:lo.pop()
        lo.append(p)
    for p in reversed(points):
        while len(hi)>1 and cross(hi[-2],hi[-1],p)<=1e-8:hi.pop()
        hi.append(p)
    return np.array(lo[:-1]+hi[:-1])
HULL = convex_hull(flow.PHYSICAL)
WALLS = []
for a,b in zip(HULL,np.roll(HULL,-1,axis=0)):
    edge = b-a
    normal = np.array([-edge[1],edge[0]])/np.linalg.norm(edge)
    WALLS.append((a,normal))


def vertices(i,pos,angle):
    sides = BODIES[i][3] or 24
    theta = angle + np.arange(sides)*math.tau/sides
    return pos + RADII[i]*np.stack([np.cos(theta),np.sin(theta)],axis=1)


def contact(a,b,center_delta):
    # Separating-axis test on the actual rotated convex outlines, not radius-only collisions.
    best_depth, best_axis = float('inf'),None
    for poly in (a,b):
        e = np.roll(poly,-1,axis=0)-poly
        axes = np.stack([-e[:,1],e[:,0]],axis=1)
        axes /= np.linalg.norm(axes,axis=1)[:,None]
        pa,pb = a@axes.T,b@axes.T
        overlap = np.minimum(pa.max(axis=0),pb.max(axis=0))-np.maximum(pa.min(axis=0),pb.min(axis=0))+GAP
        if np.any(overlap<=0):return None
        idx = int(np.argmin(overlap))
        if overlap[idx]<best_depth:best_depth,best_axis = float(overlap[idx]),axes[idx]
    if np.dot(best_axis,center_delta)<0:best_axis=-best_axis
    return best_axis,best_depth


def wall_correction(i,pos,angle,velocity,events,t):
    for a,normal in WALLS:
        distance = (vertices(i,pos,angle)-a)@normal
        penetration = STROKE_MARGIN-float(distance.min())
        if penetration>0:
            pos += (penetration+1e-8)*normal
            approaching = float(np.dot(velocity,normal))
            if approaching<0:
                velocity -= 2*approaching*normal
                events.append({'time':round(t,3),'kind':'wall','body':i})


def simulate():
    pos = np.array([b[:2] for b in BODIES],dtype=float)
    angles = np.array([b[4] for b in BODIES],dtype=float)
    velocity = VELOCITIES.copy()
    count = round(SIM_TIME/DT)
    states = np.empty((count+1,len(BODIES),3))
    events = []
    clearance = float('inf')
    residual_overlap = 0.0
    for step in range(count+1):
        t = step*DT
        if step:
            pos += velocity*DT
            angles += SPINS*DT
        # Small substeps and iterative separation handle close contacts without jitter.
        for _ in range(5):
            for i in range(len(BODIES)):wall_correction(i,pos[i],angles[i],velocity[i],events,t)
            for i in range(len(BODIES)):
                for j in range(i+1,len(BODIES)):
                    delta = pos[j]-pos[i]
                    if np.dot(delta,delta)>(RADII[i]+RADII[j]+GAP)**2:continue
                    hit = contact(vertices(i,pos[i],angles[i]),vertices(j,pos[j],angles[j]),delta)
                    if hit is None:continue
                    normal,depth = hit
                    weight = INV_MASS[i]+INV_MASS[j]
                    pos[i] -= normal*(depth+1e-8)*INV_MASS[i]/weight
                    pos[j] += normal*(depth+1e-8)*INV_MASS[j]/weight
                    closing = float(np.dot(velocity[j]-velocity[i],normal))
                    if closing<0:
                        impulse = -2*closing/weight
                        velocity[i] -= impulse*INV_MASS[i]*normal
                        velocity[j] += impulse*INV_MASS[j]*normal
                        events.append({'time':round(t,3),'kind':'pair','bodies':[i,j]})
        # Final containment pass and validation of every stored physics state.
        for i in range(len(BODIES)):
            wall_correction(i,pos[i],angles[i],velocity[i],events,t)
            v = vertices(i,pos[i],angles[i])
            for a,normal in WALLS:clearance=min(clearance,float(((v-a)@normal).min()))
        for i in range(len(BODIES)):
            for j in range(i+1,len(BODIES)):
                delta=pos[j]-pos[i]
                if np.dot(delta,delta)>(RADII[i]+RADII[j]+GAP)**2:continue
                hit=contact(vertices(i,pos[i],angles[i]),vertices(j,pos[j],angles[j]),delta)
                if hit is not None:residual_overlap=max(residual_overlap,hit[1])
        states[step,:,:2]=pos
        states[step,:,2]=angles
    assert clearance>=STROKE_MARGIN-1e-6, f'Boundary clipping: {clearance}'
    assert residual_overlap<.03, f'Unresolved overlap: {residual_overlap}'
    assert any(e['kind']=='pair' for e in events), 'No shape-to-shape collisions'
    print(f'Physics: {len(events)} contacts; minimum wall clearance {clearance:.3f}; residual contact {residual_overlap:.6f}',flush=True)
    return states,events
STATES = None


def pose(t):
    # Elastic collisions are reversible. Ease the simulation forward and backward to
    # make a seamless GIF with no positional reset or sudden turn at the endpoints.
    sim_t = SIM_TIME*(1-math.cos(math.tau*t/PERIOD))/2
    index = min(sim_t/DT,len(STATES)-1)
    lo = int(index)
    hi = min(lo+1,len(STATES)-1)
    f = index-lo
    return STATES[lo]*(1-f)+STATES[hi]*f


def levels(t):
    lit=np.zeros(flow.SAMPLES.shape[:2])
    for i,(cx,cy,angle) in enumerate(pose(t)):
        r,n,bright = BODIES[i][2],BODIES[i][3],BODIES[i][5]
        if n:
            poly=vertices(i,np.array([cx,cy]),angle)
            dist=np.full(lit.shape,np.inf)
            for a,b in zip(poly,np.roll(poly,-1,axis=0)):
                v=b-a
                f=np.clip(np.sum((flow.SAMPLES-a)*v,axis=-1)/np.dot(v,v),0,1)
                dist=np.minimum(dist,np.linalg.norm(flow.SAMPLES-a-f[...,None]*v,axis=-1))
        else:dist=np.abs(np.linalg.norm(flow.SAMPLES-[cx,cy],axis=-1)-r)
        core=np.clip((.85-dist)/.65,0,1)
        lit=np.maximum(lit,bright*core+10*np.exp(-(dist/1.1)**2))
    return np.clip(np.rint(lit.mean(axis=1)),0,255).astype(np.uint8)


def raw(t):
    im=Image.new('L',(flow.W,flow.H))
    for (x,y),v in zip(flow.LEDS,levels(t)):im.putpixel((x,y),int(v))
    return im


def preview(t):
    im=Image.new('RGB',(720,440),(8,10,14));d=ImageDraw.Draw(im)
    for (u,v),value in zip(flow.PHYSICAL,levels(t)):
        x=43+(u+23.34)*12.8;y=57+(v-15.16)*12.8
        c=round(9+float(value)*.96)
        d.ellipse((x-2.4,y-2.4,x+2.4,y+2.4),fill=(c,c,c))
    return im


def export():
    global STATES
    STATES,events=simulate()
    (OUT/'contacts.json').write_text(json.dumps(events,indent=2)+'\n')
    # Supply the first collision drawing for review before rendering the entire GIF.
    first=next(e for e in events if e['kind']=='pair')
    collision_t=PERIOD/math.tau*math.acos(1-2*first['time']/SIM_TIME)
    shots=[max(0,collision_t-8),collision_t,collision_t+8,PERIOD/2]
    sheet=Image.new('RGB',(1440,880))
    for i,t in enumerate(shots):sheet.paste(preview(t),((i%2)*720,(i//2)*440))
    sheet.save(OUT/'collision-review.png')
    preview(0).save(OUT/'preview.png')
    raw(0).save(OUT/'geometric-asteroids.png')
    print(f'First pair bump: simulation {first["time"]}s, display {collision_t:.1f}s',flush=True)
    palette=[c for i in range(256) for c in (i,i,i)]
    frames=[];previews=[]
    for i in range(round(PERIOD*FPS)):
        f=raw(i/FPS).convert('P');f.putpalette(palette);frames.append(f)
        if i%4==0:previews.append(preview(i/FPS))
        if i and i%600==0:print(f'Rendered {i}/{round(PERIOD*FPS)} frames',flush=True)
    frames[0].save(OUT/'geometric-asteroids.gif',save_all=True,append_images=frames[1:],duration=round(1000/FPS),loop=0,disposal=1,optimize=False)
    previews[0].save(OUT/'preview.gif',save_all=True,append_images=previews[1:],duration=round(4000/FPS),loop=0)
    assert np.array_equal(levels(0),levels(PERIOD)),'Loop seam differs'
    with Image.open(OUT/'geometric-asteroids.gif') as im:
        assert im.size==(74,39) and im.info['loop']==0
        duration=0
        for i in range(im.n_frames):im.seek(i);duration+=im.info['duration']
        assert duration==round(PERIOD*1000)
    print(f'Exported {PERIOD:g}s loop; format, collision, containment, and seam checks passed.',flush=True)

if __name__=='__main__':export()
