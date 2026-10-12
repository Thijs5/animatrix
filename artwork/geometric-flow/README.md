# Geometric Flow

A monochrome abstract animation for the Zephyrus G14 GA402 AniMe Matrix. Small outlined shapes lead through the narrow wing; a larger overlapping square and circle balance the wider section. Regular polygons gently drift and rock together. No gameplay imagery or flashes.

- Exact 74 × 39 transport canvas and 1,449 mapped LEDs.
- Physical preview matches Animatrix's 45° rotation and 0.65 row-height projection.
- Seamless 48-second loop at 10 FPS.
- Current composition checked at 481 phases: every bright outline remains inside the panel.

`geometric-flow.gif` is the laptop asset. `preview.gif` shows the physical dot layout at the same speed. `drawing.svg` is the editable first-frame drawing; `motion-review.png` shows four points in the loop.

To regenerate, run `python generate.py` with Pillow and NumPy installed. Outputs are written beside the script. The generator validates mapping, loop continuity, GIF dimensions, and total loop duration.

In Animatrix, add the GIF with **Leave as is**, scale 1, no rotation or tilt compensation, and FPS 0 to use its frame timing. The drawing is already positioned for the physical panel.
