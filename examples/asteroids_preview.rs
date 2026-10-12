//! Export a 60-second excerpt of the same live simulation used by the app.
//! Run: cargo run --example asteroids_preview --no-default-features -- <output-dir>
use animatrix::{MatrixGeometry, asteroids::Asteroids, matrix};
use image::{Rgb, RgbImage};
use std::path::PathBuf;
use std::time::Duration;

fn main() -> anyhow::Result<()> {
    let out = std::env::args_os()
        .nth(1)
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("artwork/live-asteroids"));
    std::fs::create_dir_all(out.join("frames"))?;
    let geometry = MatrixGeometry::for_board_name("GA402RK");
    let positions = matrix::led_positions(geometry);
    let mut scene = Asteroids::new(geometry)?;
    for i in 0..600 {
        let image = scene.frame_at(Duration::from_millis(i * 100), 1.0);
        let mut preview = RgbImage::from_pixel(720, 440, Rgb([8, 10, 14]));
        for &(x, y) in positions.iter().flatten() {
            let (u, v) = (
                (f64::from(x) - f64::from(y)) / 2.0_f64.sqrt(),
                (f64::from(x) + f64::from(y)) / 2.0_f64.sqrt() * 0.65,
            );
            let (cx, cy) = (43.0 + (u + 23.34) * 12.8, 57.0 + (v - 15.16) * 12.8);
            let light = (9.0 + f64::from(image.get_pixel(u32::from(x), u32::from(y)).0[0]) * 0.96)
                .round() as u8;
            for py in (cy - 3.0).floor() as u32..=(cy + 3.0).ceil() as u32 {
                for px in (cx - 3.0).floor() as u32..=(cx + 3.0).ceil() as u32 {
                    if (f64::from(px) - cx).powi(2) + (f64::from(py) - cy).powi(2) <= 2.4 * 2.4 {
                        preview.put_pixel(px, py, Rgb([light; 3]));
                    }
                }
            }
        }
        preview.save(out.join("frames").join(format!("{i:04}.png")))?;
        if i == 0 {
            preview.save(out.join("preview.png"))?;
        }
        if [150, 300, 450, 599].contains(&i) {
            preview.save(out.join(format!("pose-{i:04}.png")))?;
        }
    }
    println!("Exported 60-second live excerpt to {}", out.display());
    Ok(())
}
