# Omarchy O / Quiet Breath

The stepped O silhouette from Omarchy's wordmark, centred on the centroid of the GA402's 1,449 physical LED positions. It is 16 physical units tall, with its original proportions and inner opening preserved. The reference is `/usr/share/omarchy/logo.svg`, read without modification.

The shape stays fixed. A raised cosine varies brightness between 90% and 100% over 24 seconds. The cycle endpoint matches exactly, and the final exported sample differs from the first by at most one brightness level. Sixteen subpixel samples preserve coverage along the stepped edge.

- `preview.png` / `preview.gif`: enlarged physical dot previews.
- `omarchy.png`: static artwork at 74 × 39 transport resolution.
- `omarchy.gif`: seamless subtle animation, 10 fps, infinite loop.
- `drawing.svg`: editable vector drawing.

Generate: `uv run --with numpy --with pillow python artwork/omarchy-o/generate.py`.

Import with **As is** layout, no rotation or tilt compensation, original frame rate and restart looping. Use the PNG for a completely static display. Neither generating these assets nor viewing the preview changes the installed display profile.
