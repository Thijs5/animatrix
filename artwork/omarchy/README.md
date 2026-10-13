# Omarchy / Quiet Terminal

A fixed composition for the GA402 AniMe Matrix panel: four angular brackets inspired by Omarchy's installed icon, a tiled-window interior, and a terminal prompt in the narrow wing. This is an adaptation, not a reproduction of the official logo.

Only the cursor changes brightness, by 18% over a smooth 16-second cycle. It never disappears. The first and final samples differ by at most one brightness level; the mathematical endpoint matches exactly.

- `preview.png`: physical dot layout, static.
- `preview.gif`: enlarged animation preview.
- `omarchy.png`: static 74 × 39 display artwork.
- `omarchy.gif`: animation on the actual 1,449 mapped LEDs, 10 fps.
- `drawing.svg`: editable vector composition.

Generate with `uv run --with numpy --with pillow python artwork/omarchy/generate.py` from the repository root. Import the PNG for a static display, or the GIF with **As is** layout, no rotation or tilt compensation, original frame rate, and restart looping. Keep the panel brightness low.

Reference: the packaged `/usr/share/omarchy/icon.png`, read without modification. Design review removed faint connector traces to keep clean separation between the two motifs. This design does not alter the installed display profile.
