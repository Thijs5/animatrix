# Geometric Asteroids

Seven monochrome outlined circles and regular polygons drift very slowly, rotate gently, and bounce against each other and the GA402 AniMe Matrix's actual tapered boundary. Brightness stays steady; there are no particle effects or flashes.

The simulation uses convex-polygon separating-axis collisions, elastic impulses weighted by body size, and reflection against the convex hull of the physical LED coordinates. Its small time steps and iterative contact correction prevent pass-through and overlap.

The GIF is a seamless **180-second forward-and-back replay** of a 72-second simulation. A cosine playback curve gently slows and reverses the motion at each end; no positions jump when it loops. It is a pre-rendered animation, not an indefinitely evolving live simulation.

- Laptop asset: `geometric-asteroids.gif`, 74 × 39, 10 FPS.
- Physical LED preview at the same speed: `preview.gif`.
- Before/contact/after review plus a later pose: `collision-review.png`.
- Contact timings and involved bodies: `contacts.json`.

Run `python generate.py` with Pillow and NumPy installed to regenerate. The adjacent `../geometric-flow/generate.py` supplies the shared GA402 LED map. Exports validate shape collisions, boundary clearance, residual overlap, GIF dimensions, duration, and exact loop seam.

In Animatrix use **Leave as is**, scale 1, rotation 0, tilt compensation off, FPS 0, and normal GIF restart looping. The transport canvas is already composed for the physical panel.
