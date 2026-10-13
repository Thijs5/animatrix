# Omarchy O / Quiet Highlight

The actual stepped O from Omarchy's wordmark, centred on the physical GA402 LED area. A slowly angled band of light passes over it, inspired by the installed Omarchy screensaver's highlight effect. Geometry and placement stay fixed, and the full letter remains visible.

A pass lasts 24 seconds, with four seconds of calm before and after it. The moving highlight smoothly gains and loses strength, avoiding any visible return stroke. Letter brightness is 210–244 out of 255; the narrow halo is 14–26. The 32-second exported loop's first and final frames are identical.

- `omarchy.gif`: 74 × 39 display artwork, original 10 fps, infinite loop.
- `omarchy.png`: static artwork in the calm phase.
- `preview.gif`: animation in the physical dot layout.
- `preview.png`: middle of the highlight pass.
- `motion-review.png`: four sampled phases.
- `drawing.svg`: editable letter silhouette, excluding lighting effects.

Generate: `uv run --with numpy --with pillow python artwork/omarchy-highlight/generate.py`.

Use **As is** layout, original frame rate, restart looping, no rotation or tilt compensation. Installed as **Omarchy Highlight**, preserving Omarchy Glow and the other profiles. Existing global brightness and lid/power rules apply. References: installed `/usr/share/omarchy/logo.svg`, screensaver script, and `ttfx --help`; no packaged files were changed.
