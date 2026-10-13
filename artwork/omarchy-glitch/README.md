# Omarchy O / Quiet Glitch

The stepped O from Omarchy's actual wordmark, centred on the GA402 LED area. Inspired by the installed screensaver's `ttfx vhstape` effect, which shifts text rows left and right. This version adapts it to the monochrome panel and the user's preference for calm motion.

Two brief glitch bursts shift small horizontal bands by about one LED spacing. They last 0.6 and 0.4 seconds, separated by long static holds, in a 40-second loop. The O remains readable with a steady faint halo. There is no whole-panel noise or flash. First and final frames are identical.

- `omarchy.gif`: panel artwork, 74 × 39, original 10 fps, infinite loop.
- `omarchy.png`: static calm phase.
- `preview.gif` / `preview.png`: physical dot preview.
- `motion-review.png`: calm and glitch phases.
- `drawing.svg`: editable base letter.

Generate: `uv run --with numpy --with pillow python artwork/omarchy-glitch/generate.py`.

Installed as **Omarchy Glitch**, with As is layout, original frame rate and restart looping. Other profiles and global brightness/lid/power rules are preserved. Source references: installed `/usr/share/omarchy/logo.svg` and `ttfx vhstape --help`. No packaged files are changed.
