# Omarchy / Glitch Badge

A smaller O placed deliberately in the upper-right part of the GA402 panel rather than aligned to the LED or laptop centre. Anchor (20,25.5), height 10 in physical LED coordinates; original wordmark proportions remain intact. The letter has 1.23 units of boundary clearance.

Steady faint halo, two short row glitches in a 40-second loop. Each shift is under one physical unit and affects only a narrow band. The first and last encoded frames are identical. The centred versions remain separate profiles.

`omarchy.gif` is the 74 × 39 panel asset; `preview.gif` shows the physical dot layout. `preview.png` and `motion-review.png` show glitch phases. `omarchy.png` and `drawing.svg` provide the static base.

Generate: `uv run --with numpy --with pillow python artwork/omarchy-badge/generate.py`.

Installed as **Omarchy Glitch Badge**, using As is layout and original GIF timing. Existing brightness and lid/power rules apply.
