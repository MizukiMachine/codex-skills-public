use image::imageops::{resize, FilterType};
use image::{ImageBuffer, ImageReader, Rgba, RgbaImage};
use std::cmp::Ordering;
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Clone, Copy)]
struct Rgb {
    r: u8,
    g: u8,
    b: u8,
}

struct Args {
    input_dir: PathBuf,
    output_dir: PathBuf,
    width: u32,
    height: u32,
    colors: usize,
    alpha_threshold: u8,
    palette_alpha_threshold: u8,
    dry_run: bool,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = parse_args()?;
    if !args.input_dir.is_dir() {
        return Err(format!(
            "input directory does not exist: {}",
            args.input_dir.display()
        )
        .into());
    }
    if args.input_dir == args.output_dir || args.output_dir.starts_with(&args.input_dir) {
        return Err("--output-dir must differ from and not be inside --input-dir".into());
    }

    let mut inputs = Vec::new();
    collect_pngs(&args.input_dir, &mut inputs)?;
    inputs.sort();
    if inputs.is_empty() {
        return Err(format!("no PNG files found in {}", args.input_dir.display()).into());
    }

    if !args.dry_run {
        fs::create_dir_all(&args.output_dir)?;
    }

    for (index, input) in inputs.iter().enumerate() {
        let rel = input.strip_prefix(&args.input_dir)?;
        let output = args.output_dir.join(rel);
        println!("[{:03}/{:03}] {}", index + 1, inputs.len(), rel.display());
        if args.dry_run {
            continue;
        }
        if let Some(parent) = output.parent() {
            fs::create_dir_all(parent)?;
        }
        process_frame(input, &output, &args)?;
    }

    Ok(())
}

fn parse_args() -> Result<Args, Box<dyn std::error::Error>> {
    let mut input_dir = None;
    let mut output_dir = None;
    let mut size = None;
    let mut colors = 16usize;
    let mut alpha_threshold = 1u8;
    let mut palette_alpha_threshold = 16u8;
    let mut dry_run = false;

    let mut iter = env::args().skip(1);
    while let Some(arg) = iter.next() {
        match arg.as_str() {
            "--input-dir" => input_dir = iter.next().map(PathBuf::from),
            "--output-dir" => output_dir = iter.next().map(PathBuf::from),
            "--size" => size = iter.next(),
            "--colors" | "-k" => colors = require_value(&mut iter, "--colors")?.parse()?,
            "--alpha-threshold" => {
                alpha_threshold = require_value(&mut iter, "--alpha-threshold")?.parse()?
            }
            "--palette-alpha-threshold" => {
                palette_alpha_threshold =
                    require_value(&mut iter, "--palette-alpha-threshold")?.parse()?
            }
            "--dry-run" => dry_run = true,
            "--help" | "-h" => {
                print_usage();
                std::process::exit(0);
            }
            _ => return Err(format!("unknown argument: {}", arg).into()),
        }
    }

    let input_dir = input_dir.ok_or("--input-dir is required")?.canonicalize()?;
    let output_dir = absolute_path(output_dir.ok_or("--output-dir is required")?);
    let (width, height) = parse_size(&size.ok_or("--size is required")?)?;
    if colors == 0 {
        return Err("--colors must be greater than 0".into());
    }

    Ok(Args {
        input_dir,
        output_dir,
        width,
        height,
        colors,
        alpha_threshold,
        palette_alpha_threshold,
        dry_run,
    })
}

fn require_value(
    iter: &mut impl Iterator<Item = String>,
    name: &str,
) -> Result<String, Box<dyn std::error::Error>> {
    iter.next()
        .ok_or_else(|| format!("{} requires a value", name).into())
}

fn parse_size(value: &str) -> Result<(u32, u32), Box<dyn std::error::Error>> {
    let lower = value.to_ascii_lowercase();
    if let Some((left, right)) = lower.split_once('x') {
        let width: u32 = left.parse()?;
        let height: u32 = right.parse()?;
        if width == 0 || height == 0 {
            return Err("--size must be positive".into());
        }
        Ok((width, height))
    } else {
        let size: u32 = lower.parse()?;
        if size == 0 {
            return Err("--size must be positive".into());
        }
        Ok((size, size))
    }
}

fn absolute_path(path: PathBuf) -> PathBuf {
    if path.is_absolute() {
        path
    } else {
        env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join(path)
    }
}

fn print_usage() {
    eprintln!(
        "usage: fixed_canvas_pixelate --input-dir DIR --output-dir DIR --size N|WxH [--colors K] [--alpha-threshold N] [--palette-alpha-threshold N] [--dry-run]"
    );
}

fn collect_pngs(dir: &Path, out: &mut Vec<PathBuf>) -> Result<(), Box<dyn std::error::Error>> {
    for entry in fs::read_dir(dir)? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            collect_pngs(&path, out)?;
        } else if path
            .extension()
            .and_then(|ext| ext.to_str())
            .is_some_and(|ext| ext.eq_ignore_ascii_case("png"))
        {
            out.push(path);
        }
    }
    Ok(())
}

fn process_frame(
    input: &Path,
    output: &Path,
    args: &Args,
) -> Result<(), Box<dyn std::error::Error>> {
    let source = ImageReader::open(input)?.decode()?.to_rgba8();
    let premultiplied = premultiply_alpha(&source);
    let resized = resize(
        &premultiplied,
        args.width,
        args.height,
        FilterType::Triangle,
    );
    let resized = unpremultiply_alpha(&resized);
    let quantized = quantize_rgba(
        &resized,
        args.colors,
        args.alpha_threshold,
        args.palette_alpha_threshold,
    );
    quantized.save(output)?;
    Ok(())
}

fn premultiply_alpha(img: &RgbaImage) -> RgbaImage {
    let mut out = RgbaImage::new(img.width(), img.height());

    for (x, y, p) in img.enumerate_pixels() {
        let a = p[3] as u16;
        if a == 0 {
            out.put_pixel(x, y, Rgba([0, 0, 0, 0]));
            continue;
        }
        let r = ((p[0] as u16 * a + 127) / 255) as u8;
        let g = ((p[1] as u16 * a + 127) / 255) as u8;
        let b = ((p[2] as u16 * a + 127) / 255) as u8;
        out.put_pixel(x, y, Rgba([r, g, b, p[3]]));
    }

    out
}

fn unpremultiply_alpha(img: &RgbaImage) -> RgbaImage {
    let mut out = RgbaImage::new(img.width(), img.height());

    for (x, y, p) in img.enumerate_pixels() {
        let a = p[3] as u32;
        if a == 0 {
            out.put_pixel(x, y, Rgba([0, 0, 0, 0]));
            continue;
        }
        let r = ((p[0] as u32 * 255 + a / 2) / a).min(255) as u8;
        let g = ((p[1] as u32 * 255 + a / 2) / a).min(255) as u8;
        let b = ((p[2] as u32 * 255 + a / 2) / a).min(255) as u8;
        out.put_pixel(x, y, Rgba([r, g, b, p[3]]));
    }

    out
}

fn collect_palette_colors(
    img: &RgbaImage,
    alpha_threshold: u8,
    palette_alpha_threshold: u8,
) -> Vec<Rgb> {
    let palette_min_alpha = palette_alpha_threshold.max(alpha_threshold);
    let colors = collect_colors_with_min_alpha(img, palette_min_alpha);

    if colors.is_empty() && palette_min_alpha > alpha_threshold {
        collect_colors_with_min_alpha(img, alpha_threshold)
    } else {
        colors
    }
}

fn collect_colors_with_min_alpha(img: &RgbaImage, min_alpha: u8) -> Vec<Rgb> {
    img.pixels()
        .filter_map(|p| {
            (p[3] >= min_alpha).then_some(Rgb {
                r: p[0],
                g: p[1],
                b: p[2],
            })
        })
        .collect()
}

fn quantize_rgba(
    img: &RgbaImage,
    color_count: usize,
    alpha_threshold: u8,
    palette_alpha_threshold: u8,
) -> RgbaImage {
    let colors = collect_palette_colors(img, alpha_threshold, palette_alpha_threshold);

    if colors.is_empty() {
        return ImageBuffer::from_pixel(img.width(), img.height(), Rgba([0, 0, 0, 0]));
    }

    let palette = median_cut_palette(colors, color_count.max(1));
    let mut out = RgbaImage::new(img.width(), img.height());

    for (x, y, p) in img.enumerate_pixels() {
        if p[3] < alpha_threshold {
            out.put_pixel(x, y, Rgba([0, 0, 0, 0]));
            continue;
        }
        let nearest = nearest_color(
            Rgb {
                r: p[0],
                g: p[1],
                b: p[2],
            },
            &palette,
        );
        out.put_pixel(x, y, Rgba([nearest.r, nearest.g, nearest.b, p[3]]));
    }

    out
}

fn median_cut_palette(mut colors: Vec<Rgb>, target_count: usize) -> Vec<Rgb> {
    let mut boxes = vec![colors.split_off(0)];

    while boxes.len() < target_count {
        let Some(index) = boxes
            .iter()
            .enumerate()
            .filter(|(_, b)| b.len() > 1)
            .max_by(|(_, a), (_, b)| box_score(a).cmp(&box_score(b)))
            .map(|(i, _)| i)
        else {
            break;
        };

        let mut bucket = boxes.swap_remove(index);
        let channel = widest_channel(&bucket);
        bucket.sort_by(|a, b| compare_channel(*a, *b, channel));
        let split_at = bucket.len() / 2;
        let right = bucket.split_off(split_at);
        boxes.push(bucket);
        boxes.push(right);
    }

    boxes.into_iter().map(|b| average_color(&b)).collect()
}

fn box_score(colors: &[Rgb]) -> u32 {
    let (min_r, max_r, min_g, max_g, min_b, max_b) = channel_ranges(colors);
    let range = (max_r - min_r).max(max_g - min_g).max(max_b - min_b);
    range * colors.len() as u32
}

fn widest_channel(colors: &[Rgb]) -> usize {
    let (min_r, max_r, min_g, max_g, min_b, max_b) = channel_ranges(colors);
    let ranges = [max_r - min_r, max_g - min_g, max_b - min_b];
    ranges
        .iter()
        .enumerate()
        .max_by_key(|(_, range)| *range)
        .map(|(index, _)| index)
        .unwrap_or(0)
}

fn channel_ranges(colors: &[Rgb]) -> (u32, u32, u32, u32, u32, u32) {
    let mut min_r = u8::MAX;
    let mut min_g = u8::MAX;
    let mut min_b = u8::MAX;
    let mut max_r = u8::MIN;
    let mut max_g = u8::MIN;
    let mut max_b = u8::MIN;

    for c in colors {
        min_r = min_r.min(c.r);
        min_g = min_g.min(c.g);
        min_b = min_b.min(c.b);
        max_r = max_r.max(c.r);
        max_g = max_g.max(c.g);
        max_b = max_b.max(c.b);
    }

    (
        min_r as u32,
        max_r as u32,
        min_g as u32,
        max_g as u32,
        min_b as u32,
        max_b as u32,
    )
}

fn compare_channel(a: Rgb, b: Rgb, channel: usize) -> Ordering {
    match channel {
        0 => a.r.cmp(&b.r),
        1 => a.g.cmp(&b.g),
        _ => a.b.cmp(&b.b),
    }
}

fn average_color(colors: &[Rgb]) -> Rgb {
    let mut r = 0u64;
    let mut g = 0u64;
    let mut b = 0u64;

    for c in colors {
        r += c.r as u64;
        g += c.g as u64;
        b += c.b as u64;
    }

    let len = colors.len().max(1) as u64;
    Rgb {
        r: (r / len) as u8,
        g: (g / len) as u8,
        b: (b / len) as u8,
    }
}

fn nearest_color(color: Rgb, palette: &[Rgb]) -> Rgb {
    palette
        .iter()
        .copied()
        .min_by_key(|p| {
            let dr = color.r as i32 - p.r as i32;
            let dg = color.g as i32 - p.g as i32;
            let db = color.b as i32 - p.b as i32;
            dr * dr + dg * dg + db * db
        })
        .unwrap_or(color)
}
