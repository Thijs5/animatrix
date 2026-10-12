# Live asteroids

Choose **+ Live asteroids** inside a profile to add four slow, colliding outlines: a square, triangle, elongated rectangle, and circle. The forms start scattered at different angles. The larger square and rectangle remain distinct at the GA402's dot resolution.

The simulation runs continuously. It has no GIF reload, fixed playback loop, collective reversal, or periodic reset. Shapes collide with one another and reflect from the physical panel outline. A profile restart intentionally starts a fresh scene. A long suspension gap is skipped so resuming does not fast-forward the shapes.

The default drift is calm, with steady brightness and gentle rotation. **Drift speed** and **Brightness** are the main controls. **Advanced → Frame rate** controls redraw frequency without changing speed or resetting the simulation. The panel's usual global brightness and lid/power rules still apply.

Currently this element is designed for the GA402 layout. Its boundary comes from the actual LED coordinates, rotated and compressed to the lid's physical proportions. Small physics substeps, outline-aware collisions, and subpixel edge sampling keep collisions smooth and shapes inside the panel.

For a reproducible preview:

```sh
cargo run --example asteroids_preview --no-default-features -- artwork/live-asteroids
ffmpeg -framerate 10 -i artwork/live-asteroids/frames/%04d.png -c:v libx264 -pix_fmt yuv420p artwork/live-asteroids/preview.mp4
```

The video is a 60-second excerpt. The laptop continues simulating beyond it. `artwork/geometric-asteroids` contains the older looping GIF, retained as an alternative.

Checks cover collision response, ten minutes of containment and varied encounters, non-reversing motion across the old 90-second boundary, suspension handling, pixel mapping, configuration compatibility, and engine redraws without image files.
