//! Continuous, slow polygon physics in the GA402's physical LED coordinates.
//! There is no loop, playback reversal, or periodic position reset.
use std::f64::consts::{FRAC_1_SQRT_2, TAU};
use std::ops::{Add, Mul, Sub};
use std::time::Duration;

use crate::matrix;
use crate::model::{MatrixGeometry, MatrixModel};
use anyhow::{Result, bail};
use image::{Rgb, RgbImage};

const MARGIN: f64 = 1.0;
const GAP: f64 = 0.65;
const STEP: f64 = 0.025;

#[derive(Clone, Copy, Debug, Default, PartialEq)]
struct Point {
    x: f64,
    y: f64,
}
impl Point {
    const fn new(x: f64, y: f64) -> Self {
        Self { x, y }
    }
    fn dot(self, b: Self) -> f64 {
        self.x * b.x + self.y * b.y
    }
    fn length(self) -> f64 {
        self.dot(self).sqrt()
    }
    fn cross(self, b: Self) -> f64 {
        self.x * b.y - self.y * b.x
    }
}
impl Add for Point {
    type Output = Self;
    fn add(self, b: Self) -> Self {
        Self::new(self.x + b.x, self.y + b.y)
    }
}
impl Sub for Point {
    type Output = Self;
    fn sub(self, b: Self) -> Self {
        Self::new(self.x - b.x, self.y - b.y)
    }
}
impl Mul<f64> for Point {
    type Output = Self;
    fn mul(self, b: f64) -> Self {
        Self::new(self.x * b, self.y * b)
    }
}

#[derive(Clone, Debug)]
struct Body {
    position: Point,
    velocity: Point,
    angle: f64,
    spin: f64,
    local: Vec<Point>,
    radius: f64,
    brightness: f64,
    circle: bool,
}
impl Body {
    fn polygon(
        position: Point,
        velocity: Point,
        radius: f64,
        sides: usize,
        angle: f64,
        spin: f64,
        brightness: f64,
    ) -> Self {
        let local = (0..sides)
            .map(|i| {
                let a = TAU * i as f64 / sides as f64;
                Point::new(radius * a.cos(), radius * a.sin())
            })
            .collect();
        Self {
            position,
            velocity,
            radius,
            local,
            angle,
            spin,
            brightness,
            circle: false,
        }
    }
    fn vertices(&self) -> Vec<Point> {
        let (s, c) = self.angle.sin_cos();
        self.local
            .iter()
            .map(|p| self.position + Point::new(p.x * c - p.y * s, p.x * s + p.y * c))
            .collect()
    }
    fn inverse_mass(&self) -> f64 {
        1.0 / (self.radius * self.radius)
    }
}

fn initial_bodies() -> Vec<Body> {
    // Four unevenly placed forms. A larger square and an elongated rectangle
    // distinguish the silhouettes at the actual dot resolution.
    let square = Body::polygon(
        Point::new(-14.0, 19.2),
        Point::new(0.10, -0.04),
        2.0,
        4,
        0.32,
        0.007,
        235.0,
    );
    let triangle = Body::polygon(
        Point::new(11.0, 20.7),
        Point::new(-0.11, 0.15),
        2.5,
        3,
        0.68,
        -0.008,
        225.0,
    );
    let mut rectangle = Body::polygon(
        Point::new(1.0, 29.0),
        Point::new(0.12, -0.04),
        1.0,
        4,
        0.19,
        0.005,
        220.0,
    );
    rectangle.local = vec![
        Point::new(-2.8, -1.4),
        Point::new(2.8, -1.4),
        Point::new(2.8, 1.4),
        Point::new(-2.8, 1.4),
    ];
    rectangle.radius = (2.8_f64 * 2.8 + 1.4 * 1.4).sqrt();
    let mut circle = Body::polygon(
        Point::new(18.5, 36.7),
        Point::new(-0.12, -0.12),
        2.6,
        32,
        0.0,
        0.0,
        235.0,
    );
    circle.circle = true;
    vec![square, triangle, rectangle, circle]
}

fn hull(mut points: Vec<Point>) -> Vec<Point> {
    points.sort_by(|a, b| a.x.total_cmp(&b.x).then(a.y.total_cmp(&b.y)));
    points.dedup();
    let mut lower: Vec<Point> = Vec::new();
    let mut upper: Vec<Point> = Vec::new();
    for &p in &points {
        while lower.len() > 1 {
            let n = lower.len();
            if (lower[n - 1] - lower[n - 2]).cross(p - lower[n - 2]) > 1e-8 {
                break;
            }
            lower.pop();
        }
        lower.push(p);
    }
    for &p in points.iter().rev() {
        while upper.len() > 1 {
            let n = upper.len();
            if (upper[n - 1] - upper[n - 2]).cross(p - upper[n - 2]) > 1e-8 {
                break;
            }
            upper.pop();
        }
        upper.push(p);
    }
    lower.pop();
    upper.pop();
    lower.extend(upper);
    lower
}

fn contact(a: &[Point], b: &[Point], delta: Point) -> Option<(Point, f64)> {
    let mut best = (Point::default(), f64::INFINITY);
    for poly in [a, b] {
        for i in 0..poly.len() {
            let edge = poly[(i + 1) % poly.len()] - poly[i];
            let axis = Point::new(-edge.y, edge.x) * (1.0 / edge.length());
            let project = |p: &[Point]| {
                p.iter()
                    .fold((f64::INFINITY, f64::NEG_INFINITY), |(lo, hi), p| {
                        let v = p.dot(axis);
                        (lo.min(v), hi.max(v))
                    })
            };
            let (amin, amax) = project(a);
            let (bmin, bmax) = project(b);
            let overlap = amax.min(bmax) - amin.max(bmin) + GAP;
            if overlap <= 0.0 {
                return None;
            }
            if overlap < best.1 {
                best = (axis, overlap);
            }
        }
    }
    if best.0.dot(delta) < 0.0 {
        best.0 = best.0 * (-1.0);
    }
    Some(best)
}

/// One persistent simulation per element; rendering never rewinds it on a timer.
pub struct Asteroids {
    geometry: MatrixGeometry,
    pixels: Vec<(u32, u32, Point)>,
    walls: Vec<(Point, Point)>,
    bodies: Vec<Body>,
    last_elapsed: Option<Duration>,
    pair_contacts: u64,
    wall_contacts: u64,
    #[cfg(test)]
    contacted_pairs: std::collections::HashSet<(usize, usize)>,
}
impl Asteroids {
    pub fn new(geometry: MatrixGeometry) -> Result<Self> {
        if !matches!(geometry.model, MatrixModel::Ga402 | MatrixModel::Unknown) {
            bail!("live asteroids currently require the GA402 panel layout");
        }
        let pixels: Vec<_> = matrix::led_positions(geometry)
            .into_iter()
            .flatten()
            .map(|(x, y)| {
                let p = Point::new(
                    (f64::from(x) - f64::from(y)) * FRAC_1_SQRT_2,
                    (f64::from(x) + f64::from(y)) * FRAC_1_SQRT_2 * 0.65,
                );
                (u32::from(x), u32::from(y), p)
            })
            .collect();
        let boundary = hull(pixels.iter().map(|p| p.2).collect());
        let walls = (0..boundary.len())
            .map(|i| {
                let a = boundary[i];
                let e = boundary[(i + 1) % boundary.len()] - a;
                (a, Point::new(-e.y, e.x) * (1.0 / e.length()))
            })
            .collect();
        Ok(Self {
            geometry,
            pixels,
            walls,
            bodies: initial_bodies(),
            last_elapsed: None,
            pair_contacts: 0,
            wall_contacts: 0,
            #[cfg(test)]
            contacted_pairs: std::collections::HashSet::new(),
        })
    }

    fn correct_walls(body: &mut Body, walls: &[(Point, Point)]) -> u64 {
        let mut hits = 0;
        for &(a, normal) in walls {
            let distance = body
                .vertices()
                .iter()
                .map(|p| (*p - a).dot(normal))
                .fold(f64::INFINITY, f64::min);
            let depth = MARGIN - distance;
            if depth > 0.0 {
                body.position = body.position + normal * (depth + 1e-8);
                let closing = body.velocity.dot(normal);
                if closing < 0.0 {
                    body.velocity = body.velocity - normal * (2.0 * closing);
                    hits += 1;
                }
            }
        }
        hits
    }

    fn step(&mut self, dt: f64) {
        for body in &mut self.bodies {
            body.position = body.position + body.velocity * dt;
            body.angle += body.spin * dt;
        }
        for _ in 0..5 {
            for body in &mut self.bodies {
                self.wall_contacts += Self::correct_walls(body, &self.walls);
            }
            for i in 0..self.bodies.len() {
                for j in i + 1..self.bodies.len() {
                    let (left, right) = self.bodies.split_at_mut(j);
                    let (a, b) = (&mut left[i], &mut right[0]);
                    let delta = b.position - a.position;
                    if delta.dot(delta) > (a.radius + b.radius + GAP).powi(2) {
                        continue;
                    }
                    let Some((normal, depth)) = contact(&a.vertices(), &b.vertices(), delta) else {
                        continue;
                    };
                    let (ma, mb) = (a.inverse_mass(), b.inverse_mass());
                    let weight = ma + mb;
                    a.position = a.position - normal * ((depth + 1e-8) * ma / weight);
                    b.position = b.position + normal * ((depth + 1e-8) * mb / weight);
                    let closing = (b.velocity - a.velocity).dot(normal);
                    if closing < 0.0 {
                        let impulse = -2.0 * closing / weight;
                        a.velocity = a.velocity - normal * (impulse * ma);
                        b.velocity = b.velocity + normal * (impulse * mb);
                        self.pair_contacts += 1;
                        #[cfg(test)]
                        self.contacted_pairs.insert((i, j));
                    }
                }
            }
        }
        for body in &mut self.bodies {
            self.wall_contacts += Self::correct_walls(body, &self.walls);
        }
    }

    fn advance_to(&mut self, elapsed: Duration, speed: f32) {
        if let Some(previous) = self.last_elapsed {
            if elapsed < previous {
                // An explicit profile restart or new cycle, never periodic playback.
                self.bodies = initial_bodies();
                self.pair_contacts = 0;
                self.wall_contacts = 0;
                #[cfg(test)]
                self.contacted_pairs.clear();
            } else {
                let gap = elapsed - previous;
                // A suspended/hidden display resumes where it was, without a large catch-up jump.
                if gap <= Duration::from_secs(2) {
                    let mut remaining = gap.as_secs_f64() * f64::from(speed);
                    while remaining > 1e-9 {
                        let dt = remaining.min(STEP);
                        self.step(dt);
                        remaining -= dt;
                    }
                }
            }
        }
        self.last_elapsed = Some(elapsed);
    }

    pub fn frame_at(&mut self, elapsed: Duration, speed: f32) -> RgbImage {
        self.advance_to(elapsed, speed);
        self.render()
    }

    fn render(&self) -> RgbImage {
        let mut image = RgbImage::new(self.geometry.width, self.geometry.height);
        let vertices: Vec<_> = self.bodies.iter().map(Body::vertices).collect();
        let offsets = [
            Point::new(-0.14, -0.14),
            Point::new(-0.14, 0.14),
            Point::new(0.14, -0.14),
            Point::new(0.14, 0.14),
        ];
        for &(x, y, p) in &self.pixels {
            let mut sum = 0.0;
            for offset in offsets {
                let q = p + offset;
                let mut lit = 0.0_f64;
                for (body, poly) in self.bodies.iter().zip(&vertices) {
                    let delta = q - body.position;
                    if delta.dot(delta) > (body.radius + 2.8).powi(2) {
                        continue;
                    }
                    let distance = if body.circle {
                        (delta.length() - body.radius).abs()
                    } else {
                        (0..poly.len())
                            .map(|i| {
                                let a = poly[i];
                                let v = poly[(i + 1) % poly.len()] - a;
                                let f = ((q - a).dot(v) / v.dot(v)).clamp(0.0, 1.0);
                                (q - a - v * f).length()
                            })
                            .fold(f64::INFINITY, f64::min)
                    };
                    let core = ((0.85 - distance) / 0.65).clamp(0.0, 1.0);
                    lit = lit
                        .max(body.brightness * core + 10.0 * (-distance * distance / 1.21).exp());
                }
                sum += lit;
            }
            let level = (sum / 4.0).round().clamp(0.0, 255.0) as u8;
            image.put_pixel(x, y, Rgb([level; 3]));
        }
        image
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn scene() -> Asteroids {
        Asteroids::new(MatrixGeometry::for_board_name("GA402RK")).unwrap()
    }
    fn assert_contained(scene: &Asteroids) {
        for body in &scene.bodies {
            for &(a, n) in &scene.walls {
                assert!(
                    body.vertices()
                        .iter()
                        .all(|p| (*p - a).dot(n) >= MARGIN - 1e-5)
                );
            }
        }
    }

    #[test]
    fn head_on_collision_exchanges_equal_mass_velocities() {
        let mut s = scene();
        s.bodies = vec![
            Body::polygon(
                Point::new(5.0, 23.0),
                Point::new(0.2, 0.0),
                2.0,
                4,
                std::f64::consts::FRAC_PI_4,
                0.0,
                235.0,
            ),
            Body::polygon(
                Point::new(8.8, 23.0),
                Point::new(-0.2, 0.0),
                2.0,
                4,
                std::f64::consts::FRAC_PI_4,
                0.0,
                235.0,
            ),
        ];
        for _ in 0..100 {
            s.step(STEP);
        }
        assert_eq!(s.pair_contacts, 1);
        assert!(s.bodies[0].velocity.x < 0.0 && s.bodies[1].velocity.x > 0.0);
        assert!((s.bodies[0].velocity.length() - 0.2).abs() < 1e-6);
        assert_contained(&s);
    }

    #[test]
    fn ten_minutes_stay_inside_and_produce_varied_contacts() {
        let mut s = scene();
        let initial_angle = s.bodies[2].angle;
        for _ in 0..24000 {
            s.step(STEP);
            assert_contained(&s);
            for i in 0..s.bodies.len() {
                for j in i + 1..s.bodies.len() {
                    if let Some((_, depth)) = contact(
                        &s.bodies[i].vertices(),
                        &s.bodies[j].vertices(),
                        s.bodies[j].position - s.bodies[i].position,
                    ) {
                        assert!(depth < 0.01, "unresolved contact {depth}");
                    }
                }
            }
        }
        assert!(s.pair_contacts >= 3, "{} pair contacts", s.pair_contacts);
        assert!(
            s.contacted_pairs.len() >= 3,
            "only {} distinct pairs met",
            s.contacted_pairs.len()
        );
        eprintln!(
            "10-minute check: {} pair contacts across {} distinct pairs, {} wall contacts",
            s.pair_contacts,
            s.contacted_pairs.len(),
            s.wall_contacts
        );
        assert!(s.wall_contacts >= 3, "{} wall contacts", s.wall_contacts);
        assert!(
            s.bodies[2].angle > initial_angle + 2.9,
            "rotation must not periodically reverse"
        );
    }

    #[test]
    fn elapsed_clock_has_no_ninety_second_reversal_and_skips_resume_gaps() {
        let mut s = scene();
        s.advance_to(Duration::ZERO, 1.0);
        for i in 1..=1800 {
            s.advance_to(Duration::from_millis(i * 100), 1.0);
        }
        assert!((s.bodies[2].angle - (0.19 + 180.0 * 0.005)).abs() < 1e-6);
        let before: Vec<_> = s.bodies.iter().map(|b| b.position).collect();
        s.advance_to(Duration::from_secs(3600), 1.0);
        assert_eq!(
            before,
            s.bodies.iter().map(|b| b.position).collect::<Vec<_>>()
        );
        s.advance_to(Duration::ZERO, 1.0);
        assert!((s.bodies[2].angle - 0.19).abs() < 1e-6);
    }

    #[test]
    fn rendered_frames_use_only_real_led_pixels_and_correct_buffer_size() {
        let mut s = scene();
        let image = s.frame_at(Duration::ZERO, 1.0);
        assert_eq!(image.dimensions(), (74, 39));
        assert_eq!(matrix::led_buffer(&image, 1.0, s.geometry).len(), 1881);
        assert!(image.pixels().any(|p| p.0[0] > 200));
        let used: std::collections::HashSet<_> = s.pixels.iter().map(|&(x, y, _)| (x, y)).collect();
        for (x, y, p) in image.enumerate_pixels() {
            if !used.contains(&(x, y)) {
                assert_eq!(p.0, [0, 0, 0]);
            }
        }
    }
}
