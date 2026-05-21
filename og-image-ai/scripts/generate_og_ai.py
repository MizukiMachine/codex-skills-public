#!/usr/bin/env python3
"""
AI-powered OG Image Generator

Generates Open Graph images using OpenAI GPT Image models
with Pillow-based text overlay for guaranteed readability.

Usage:
    # Single image
    python generate_og_ai.py --title "My Article" --style tech --output og.png

    # With description and brand colors
    python generate_og_ai.py --title "Our Mission" --style corporate \
        --description "Building the future" --brand-colors "#6366f1,#8b5cf6" \
        --output og.png

    # Batch from og-analysis.json
    python generate_og_ai.py --analysis ./og-analysis.json --output ./public/og --limit 5
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


OG_WIDTH = 1200
OG_HEIGHT = 630
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "1536x1024"
DEFAULT_QUALITY = "medium"
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

STYLE_PRESETS = {
    "tech": {
        "base": (
            "A wide landscape illustration for a technology-focused social card. "
            "Clean modern aesthetic with subtle circuit board patterns and flowing data streams. "
            "Soft geometric shapes and thin connecting lines."
        ),
        "default_palette": "deep navy, electric blue, cool gray, with bright accent highlights",
    },
    "nature": {
        "base": (
            "A wide landscape illustration for a social card about nature or sustainability. "
            "Organic flowing shapes inspired by leaves, water, and natural landscapes. "
            "Gentle gradients and layered natural textures."
        ),
        "default_palette": "forest green, soft teal, warm earth tones, cream",
    },
    "warm": {
        "base": (
            "A wide landscape illustration for a warm and friendly social card. "
            "Soft rounded shapes, gentle curves, and inviting patterns. "
            "Cozy atmosphere with subtle decorative elements."
        ),
        "default_palette": "amber, coral, soft orange, warm cream, muted red",
    },
    "abstract": {
        "base": (
            "A wide landscape abstract illustration for a creative social card. "
            "Bold geometric composition with overlapping shapes and dynamic angles. "
            "Modern art inspired, visually striking from a distance."
        ),
        "default_palette": "vibrant but harmonious, with 2-3 dominant colors",
    },
    "corporate": {
        "base": (
            "A wide landscape illustration for a professional business social card. "
            "Clean structured composition with subtle architectural elements. "
            "Professional and trustworthy atmosphere."
        ),
        "default_palette": "navy blue, steel gray, white, with a single accent color",
    },
    "dark": {
        "base": (
            "A wide landscape illustration for a dark-themed social card. "
            "Dramatic dark atmosphere with glowing accents and light streaks. "
            "Moody and cinematic feel with subtle particle effects."
        ),
        "default_palette": "deep black, dark charcoal, with neon cyan or purple highlights",
    },
    "neon": {
        "base": (
            "A wide landscape illustration for a synthwave-styled social card. "
            "Retro-futuristic cityscape with neon grid and glowing horizon. "
            "80s-inspired neon aesthetic with scan lines and lens flare."
        ),
        "default_palette": "hot pink, electric blue, deep purple, black",
    },
}

PAGE_TYPE_MODIFIERS = {
    "landing": "The image represents a product or service landing page.",
    "article": "The image represents a blog article or technical writing.",
    "product": "The image represents a product feature or capability.",
    "documentation": "The image represents technical documentation or a guide.",
    "about": "The image represents a company or team identity.",
    "general": "The image represents a general web page.",
}

COMMON_SUFFIX = (
    "The image must be wide landscape format suitable for 1200x630 pixels. "
    "Keep the upper-left third and center area clear and uncluttered for text overlay. "
    "No text, no words, no letters, no typography anywhere in the image. "
    "The image should look good when viewed as a small thumbnail in a social media feed."
)


def build_prompt(
    style: str = "tech",
    page_type: str = "general",
    brand_colors: list[str] | None = None,
    custom_prompt: str | None = None,
    theme_hint: str | None = None,
) -> str:
    """Build the image generation prompt."""
    if custom_prompt:
        base = custom_prompt
    else:
        preset = STYLE_PRESETS.get(style, STYLE_PRESETS["tech"])
        base = preset["base"]

    parts = [base]

    if theme_hint:
        hint = theme_hint.strip()
        if hint and hint[-1] not in ".!?":
            hint += "."
        parts.append(f"Additional theme context: {hint}")

    page_modifier = PAGE_TYPE_MODIFIERS.get(page_type, PAGE_TYPE_MODIFIERS["general"])
    parts.append(page_modifier)

    if brand_colors:
        color_names = ", ".join(brand_colors)
        parts.append(
            f"Color palette should incorporate these brand colors: {color_names}. "
            "Use these as dominant tones while maintaining visual harmony."
        )
    elif not custom_prompt:
        preset = STYLE_PRESETS.get(style, STYLE_PRESETS["tech"])
        parts.append(f"Color palette: {preset['default_palette']}.")

    parts.append(COMMON_SUFFIX)

    return " ".join(parts)


def generate_image_openai(
    prompt: str,
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    quality: str = DEFAULT_QUALITY,
) -> bytes:
    """Call OpenAI Image API and return PNG bytes."""
    if not HAS_OPENAI:
        raise SystemExit(
            "Missing dependency: openai. Install with: pip install openai"
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY environment variable is not set.")

    client = OpenAI(api_key=api_key)

    request: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
    }
    if quality and model.startswith("gpt-image"):
        request["quality"] = quality

    result = client.images.generate(**request)

    image = result.data[0]

    if hasattr(image, "b64_json") and image.b64_json:
        return base64.b64decode(image.b64_json)

    if hasattr(image, "url") and image.url:
        import urllib.request
        with urllib.request.urlopen(image.url) as resp:
            return resp.read()

    raise SystemExit("OpenAI API returned no image data.")


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


def is_hex_color(value: str) -> bool:
    return bool(HEX_COLOR_RE.fullmatch(value.strip()))


def parse_color_list(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    colors = [c.strip() for c in raw.split(",") if c.strip()]
    invalid = [c for c in colors if not is_hex_color(c)]
    if invalid:
        raise SystemExit(f"Invalid hex color(s): {', '.join(invalid)}")
    return colors


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    channels = []
    for c in rgb:
        v = c / 255
        channels.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def is_dark_color(hex_color: str) -> bool:
    return relative_luminance(hex_to_rgb(hex_color)) < 0.42


def average_region_luminance(img: Image.Image, box: tuple[int, int, int, int]) -> float:
    sample = img.crop(box).convert("RGB").resize((1, 1), Image.Resampling.BOX)
    return relative_luminance(sample.getpixel((0, 0)))


def get_system_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont | None:
    font_paths = [
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
        "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/YuGothB.ttc" if bold else "C:/Windows/Fonts/YuGothR.ttc",
        "C:/Windows/Fonts/meiryob.ttc" if bold else "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except (IOError, OSError):
                continue
    return ImageFont.load_default()


def text_width(text: str, font: Any) -> int:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def font_line_height(font: Any) -> int:
    bbox = font.getbbox("Ag")
    return bbox[3] - bbox[1]


def ellipsize_line(text: str, max_width: int, font: Any) -> str:
    if text_width(text, font) <= max_width:
        return text
    ellipsis = "..."
    trimmed = text.rstrip()
    while trimmed and text_width(trimmed + ellipsis, font) > max_width:
        trimmed = trimmed[:-1].rstrip()
    return (trimmed + ellipsis) if trimmed else ellipsis


def longest_fitting_prefix(text: str, max_width: int, font: Any) -> int:
    """Return a nonzero prefix length that fits, preferring word boundaries."""
    if not text:
        return 0

    lo = 1
    hi = len(text)
    fit = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        candidate = text[:mid].rstrip()
        if candidate and text_width(candidate, font) <= max_width:
            fit = mid
            lo = mid + 1
        else:
            hi = mid - 1

    if fit == 0:
        return 1

    if fit < len(text) and not text[fit].isspace():
        last_space = text.rfind(" ", 0, fit + 1)
        if last_space > 0 and last_space >= int(fit * 0.6):
            return last_space

    return fit


def wrap_text(text: str, max_width: int, font: Any, max_lines: int) -> list[str]:
    remaining = " ".join(text.split())
    if not remaining:
        return []

    lines: list[str] = []
    while remaining and len(lines) < max_lines:
        if text_width(remaining, font) <= max_width:
            lines.append(remaining)
            break

        if len(lines) == max_lines - 1:
            lines.append(ellipsize_line(remaining, max_width, font))
            break

        split_at = longest_fitting_prefix(remaining, max_width, font)
        line = remaining[:split_at].rstrip()
        if not line:
            line = ellipsize_line(remaining, max_width, font)
            lines.append(line)
            break

        lines.append(line)
        remaining = remaining[split_at:].lstrip()

    return lines


def fit_multiline_text(
    text: str,
    max_width: int,
    max_height: int,
    base_size: int,
    min_size: int,
    max_lines: int,
    bold: bool = True,
) -> tuple[Any, list[str], int]:
    """Find the largest font size that fits as wrapped text."""
    for size in range(base_size, min_size - 1, -2):
        font = get_system_font(size, bold=bold)
        line_spacing = max(6, int(size * 0.16))
        lines = wrap_text(text, max_width, font, max_lines)
        if not lines:
            return font, [], line_spacing
        line_h = font_line_height(font)
        block_h = len(lines) * line_h + (len(lines) - 1) * line_spacing
        if block_h <= max_height and all(text_width(line, font) <= max_width for line in lines):
            return font, lines, line_spacing

    font = get_system_font(min_size, bold=bold)
    line_spacing = max(6, int(min_size * 0.16))
    return font, wrap_text(text, max_width, font, max_lines), line_spacing


def draw_lines(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: list[str],
    font: Any,
    fill: tuple[int, int, int, int],
    line_spacing: int,
) -> int:
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font_line_height(font) + line_spacing
    return y


def composite_text(
    bg_image: Image.Image,
    title: str,
    description: str = "",
    page_type: str = "general",
    accent_color: str | None = None,
    site_name: str = "",
) -> Image.Image:
    """Overlay text onto the AI-generated background."""
    img = bg_image.copy().convert("RGBA")
    w, h = img.size

    padding_x = 80
    padding_y = 64
    panel_x = padding_x
    panel_y = padding_y
    panel_w = w - padding_x * 2
    panel_h = h - padding_y * 2

    panel_luminance = average_region_luminance(
        img,
        (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h),
    )
    use_dark_panel = panel_luminance < 0.55
    text_color = (255, 255, 255, 255) if use_dark_panel else (17, 24, 39, 255)
    muted_color = (255, 255, 255, 210) if use_dark_panel else (17, 24, 39, 190)
    accent_rgb = hex_to_rgb(accent_color) if accent_color and is_hex_color(accent_color) else (99, 102, 241)

    # Backdrop panel behind text
    backdrop = Image.new("RGBA", (panel_w, panel_h), (0, 0, 0, 0))
    backdrop_draw = ImageDraw.Draw(backdrop)

    overlay_fill = (0, 0, 0, 120) if use_dark_panel else (255, 255, 255, 150)
    backdrop_draw.rounded_rectangle(
        [(0, 0), (panel_w - 1, panel_h - 1)],
        radius=24,
        fill=overlay_fill,
    )

    if use_dark_panel:
        backdrop = backdrop.filter(ImageFilter.GaussianBlur(30))
    else:
        backdrop = backdrop.filter(ImageFilter.GaussianBlur(20))

    img.paste(backdrop, (panel_x, panel_y), backdrop)

    draw = ImageDraw.Draw(img)

    content_x = panel_x + 48
    content_w = panel_w - 96

    bar_y = panel_y + 40
    bar_w = 80
    bar_h = 6
    draw.rounded_rectangle(
        [(content_x, bar_y), (content_x + bar_w, bar_y + bar_h)],
        radius=3,
        fill=(*accent_rgb, 255),
    )

    title_y = bar_y + 30
    footer_reserved = 70 if site_name else 0
    title_font, title_lines, title_spacing = fit_multiline_text(
        title,
        max_width=content_w,
        max_height=230,
        base_size=76 if len(title) < 70 else 66,
        min_size=40,
        max_lines=3,
        bold=True,
    )
    next_y = draw_lines(
        draw,
        (content_x, title_y),
        title_lines,
        title_font,
        text_color,
        title_spacing,
    )

    if description:
        desc_y = next_y + 14
        desc_bottom = panel_y + panel_h - footer_reserved - 42
        desc_font, desc_lines, desc_spacing = fit_multiline_text(
            description,
            max_width=content_w,
            max_height=max(48, desc_bottom - desc_y),
            base_size=34,
            min_size=22,
            max_lines=2,
            bold=False,
        )
        draw_lines(
            draw,
            (content_x, desc_y),
            desc_lines,
            desc_font,
            muted_color,
            desc_spacing,
        )

    if site_name:
        footer_font = get_system_font(22, bold=False)
        draw.text(
            (content_x, panel_y + panel_h - 60),
            site_name,
            font=footer_font,
            fill=muted_color,
        )

    return img


def crop_to_og(img: Image.Image) -> Image.Image:
    """Crop/resize image to exact 1200x630 OG dimensions."""
    if img.size == (OG_WIDTH, OG_HEIGHT):
        return img

    target_ratio = OG_WIDTH / OG_HEIGHT
    current_ratio = img.width / img.height

    if current_ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    elif current_ratio < target_ratio:
        new_h = int(img.width / target_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))

    return img.resize((OG_WIDTH, OG_HEIGHT), Image.Resampling.LANCZOS)


def generate_single(
    title: str,
    description: str = "",
    style: str = "tech",
    page_type: str = "general",
    brand_colors: list[str] | None = None,
    custom_prompt: str | None = None,
    theme_hint: str | None = None,
    accent_color: str | None = None,
    site_name: str = "",
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    quality: str = DEFAULT_QUALITY,
    output: str = "og-image.png",
) -> str:
    """Generate a single OG image."""
    prompt = build_prompt(style, page_type, brand_colors, custom_prompt, theme_hint)

    print(f"Prompt: {prompt[:120]}...")
    print(f"Generating with {model} ({quality}, {size})...")

    png_bytes = generate_image_openai(prompt, model=model, size=size, quality=quality)
    bg = Image.open(BytesIO(png_bytes)).convert("RGBA")
    bg = crop_to_og(bg)

    result = composite_text(
        bg,
        title=title,
        description=description,
        page_type=page_type,
        accent_color=accent_color or (brand_colors[0] if brand_colors else None),
        site_name=site_name,
    )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.convert("RGB").save(str(output_path), "PNG", optimize=True)

    file_size = output_path.stat().st_size
    print(f"Saved: {output_path} ({file_size // 1024} KB)")
    return str(output_path)


def route_title(route: dict[str, Any]) -> str:
    title = route.get("metadata", {}).get("title", "")
    if title:
        return title
    path = route.get("path", "/")
    return path.strip("/").replace("-", " ").replace("_", " ").title() or "Page"


def route_slug(route: dict[str, Any]) -> str:
    path_slug = route.get("path", "/").strip("/").replace("/", "-") or "home"
    return re.sub(r"[^a-zA-Z0-9-]", "", path_slug) or "page"


def load_analysis(analysis_path: Path, brand_colors: list[str] | None) -> tuple[list[dict[str, Any]], dict[str, Any], list[str] | None]:
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    routes = analysis.get("routes", [])
    brand = analysis.get("brand", {})

    if brand_colors is None:
        raw_colors = brand.get("colors", [])
        brand_colors = [c for c in raw_colors if isinstance(c, str) and is_hex_color(c)][:3]

    return routes, brand, brand_colors


def select_routes(
    routes: list[dict[str, Any]],
    limit: int | None = None,
    include_dynamic: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    skipped_dynamic = 0
    if not include_dynamic:
        skipped_dynamic = sum(1 for route in routes if route.get("dynamic"))
        routes = [route for route in routes if not route.get("dynamic")]

    if limit is not None:
        routes = routes[:limit]

    return routes, skipped_dynamic


def dry_run_batch(
    analysis_path: Path,
    style: str = "tech",
    limit: int | None = None,
    brand_colors: list[str] | None = None,
    include_dynamic: bool = False,
    custom_prompt: str | None = None,
    theme_hint: str | None = None,
) -> None:
    routes, brand, brand_colors = load_analysis(analysis_path, brand_colors)
    routes, skipped_dynamic = select_routes(routes, limit, include_dynamic)
    if skipped_dynamic:
        print(f"Skipping {skipped_dynamic} dynamic route(s). Use --include-dynamic for fallback images.")

    site_name = brand.get("site_name", "")
    print(f"Routes: {len(routes)}")
    print(f"Site: {site_name or '(none)'}")
    print(f"Brand colors: {', '.join(brand_colors or []) or '(none)'}")

    for i, route in enumerate(routes, 1):
        title = route_title(route)
        description = route.get("metadata", {}).get("description", "")
        page_type = route.get("type", "general")
        prompt = build_prompt(style, page_type, brand_colors, custom_prompt, theme_hint)
        print(f"\n[{i}/{len(routes)}] {route.get('path', '/')}")
        print(f"Title: {title}")
        print(f"Description: {description or '(none)'}")
        print(f"Page type: {page_type}")
        print(f"Prompt:\n{prompt}")


def generate_batch(
    analysis_path: Path,
    output_dir: Path,
    style: str = "tech",
    model: str = DEFAULT_MODEL,
    size: str = DEFAULT_SIZE,
    quality: str = DEFAULT_QUALITY,
    limit: int | None = None,
    brand_colors: list[str] | None = None,
    include_dynamic: bool = False,
    custom_prompt: str | None = None,
    theme_hint: str | None = None,
) -> list[dict[str, Any]]:
    """Generate OG images from an og-analysis.json file."""
    routes, brand, brand_colors = load_analysis(analysis_path, brand_colors)
    routes, skipped_dynamic = select_routes(routes, limit, include_dynamic)
    if skipped_dynamic:
        print(f"Skipping {skipped_dynamic} dynamic route(s). Use --include-dynamic for fallback images.")

    site_name = brand.get("site_name", "")
    accent = brand_colors[0] if brand_colors else None

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    failures: list[str] = []

    for i, route in enumerate(routes, 1):
        title = route_title(route)
        description = route.get("metadata", {}).get("description", "")
        page_type = route.get("type", "general")
        filename = f"og-{route_slug(route)}.png"
        output_path = output_dir / filename

        print(f"\n[{i}/{len(routes)}] {route.get('path', '/')}")

        try:
            generate_single(
                title=title,
                description=description or "",
                style=style,
                page_type=page_type,
                brand_colors=brand_colors,
                custom_prompt=custom_prompt,
                theme_hint=theme_hint,
                accent_color=accent,
                site_name=site_name,
                model=model,
                size=size,
                quality=quality,
                output=str(output_path),
            )
            file_size = output_path.stat().st_size
            manifest.append({
                "route": route.get("path", "/"),
                "file": filename,
                "title": title,
                "description": description,
                "type": page_type,
                "width": OG_WIDTH,
                "height": OG_HEIGHT,
                "bytes": file_size,
                "alt": f"Social preview for {title}",
            })
        except Exception as e:
            route_path = route.get("path", "/")
            failures.append(f"{route_path}: {e}")
            print(f"  Error: {e}")

    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    build_preview(output_dir, manifest)
    if failures:
        summary = "; ".join(failures[:3])
        if len(failures) > 3:
            summary += f"; ... ({len(failures)} total)"
        raise SystemExit(f"Failed to generate {len(failures)} route(s): {summary}")

    return manifest


def build_preview(out_dir: Path, manifest: list[dict[str, Any]]) -> None:
    """Build an HTML preview page."""
    import html as html_mod

    cards = "\n".join(
        f"""<section>
  <img src="{html_mod.escape(item['file'])}" width="600" height="315" alt="{html_mod.escape(item['alt'])}">
  <h2>{html_mod.escape(item['route'])}</h2>
  <p>{html_mod.escape(item['title'])}</p>
</section>"""
        for item in manifest
    )
    preview = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>OG Image AI Preview</title>
  <style>
    body {{ margin: 0; padding: 32px; font-family: system-ui, sans-serif; background: #f3f4f6; color: #111827; }}
    main {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 28px; }}
    section {{ background: white; border: 1px solid #d1d5db; padding: 16px; }}
    img {{ width: 100%; height: auto; display: block; border: 1px solid #e5e7eb; }}
    h2 {{ margin: 14px 0 4px; font-size: 16px; }}
    p {{ margin: 0; color: #4b5563; }}
  </style>
</head>
<body>
  <h1>OG Image AI Preview</h1>
  <main>{cards}</main>
</body>
</html>"""
    (out_dir / "preview.html").write_text(preview, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate OG images using AI image generation + text overlay",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --title "My Article" --style tech --output og.png
  %(prog)s --title "About Us" --style corporate --brand-colors "#6366f1,#8b5cf6" --output og.png
  %(prog)s --analysis ./og-analysis.json --output ./public/og --limit 5

Styles: """ + ", ".join(STYLE_PRESETS.keys()),
    )

    parser.add_argument("--title", "-t", help="Page title for text overlay")
    parser.add_argument("--description", "-d", help="Page description for text overlay")
    parser.add_argument(
        "--style", "-s",
        choices=list(STYLE_PRESETS.keys()),
        default="tech",
        help="Visual style preset (default: tech)",
    )
    parser.add_argument("--page-type", choices=list(PAGE_TYPE_MODIFIERS.keys()), default="general")
    parser.add_argument("--brand-colors", help="Comma-separated hex colors (e.g., '#6366f1,#8b5cf6')")
    parser.add_argument("--accent-color", help="Accent color for UI elements (hex)")
    parser.add_argument("--site-name", help="Site name for footer")
    parser.add_argument("--custom-prompt", help="Override the entire AI prompt")
    parser.add_argument("--theme-hint", help="Extra context for prompt (e.g., 'healthcare SaaS')")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenAI image model (default: {DEFAULT_MODEL})")
    parser.add_argument("--size", default=DEFAULT_SIZE, help=f"Generation size before crop (default: {DEFAULT_SIZE})")
    parser.add_argument(
        "--quality",
        choices=["low", "medium", "high", "auto"],
        default=DEFAULT_QUALITY,
        help=f"GPT Image quality (default: {DEFAULT_QUALITY})",
    )
    parser.add_argument("--output", "-o", default="og-image.png", help="Output file path")
    parser.add_argument("--analysis", help="og-analysis.json path for batch generation")
    parser.add_argument("--limit", type=int, help="Limit batch to first N routes")
    parser.add_argument("--include-dynamic", action="store_true", help="Generate fallback images for dynamic route patterns")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling API")

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    brand_colors = parse_color_list(args.brand_colors)
    if args.accent_color and not is_hex_color(args.accent_color):
        raise SystemExit(f"Invalid accent color: {args.accent_color}")

    if args.dry_run:
        if args.analysis:
            dry_run_batch(
                analysis_path=Path(args.analysis),
                style=args.style,
                limit=args.limit,
                brand_colors=brand_colors,
                include_dynamic=args.include_dynamic,
                custom_prompt=args.custom_prompt,
                theme_hint=args.theme_hint,
            )
            return

        if not args.title:
            args.title = "Page Title"

        prompt = build_prompt(args.style, args.page_type, brand_colors, args.custom_prompt, args.theme_hint)
        print(f"Title: {args.title}")
        print(f"Description: {args.description or '(none)'}")
        print(f"Style: {args.style}")
        print(f"Page type: {args.page_type}")
        print(f"Model: {args.model}")
        print(f"Size: {args.size}")
        print(f"Quality: {args.quality}")
        print(f"\nPrompt:\n{prompt}")
        return

    if not HAS_PILLOW:
        raise SystemExit("Missing dependency: Pillow. Install with: pip install Pillow")
    if not HAS_OPENAI:
        raise SystemExit("Missing dependency: openai. Install with: pip install openai")

    if args.analysis:
        manifest = generate_batch(
            analysis_path=Path(args.analysis),
            output_dir=Path(args.output),
            style=args.style,
            model=args.model,
            size=args.size,
            quality=args.quality,
            limit=args.limit,
            brand_colors=brand_colors,
            include_dynamic=args.include_dynamic,
            custom_prompt=args.custom_prompt,
            theme_hint=args.theme_hint,
        )
        print(f"\nGenerated {len(manifest)} image(s)")
        print(f"Preview: {Path(args.output) / 'preview.html'}")
        return

    if not args.title:
        args.title = "Page Title"

    generate_single(
        title=args.title,
        description=args.description or "",
        style=args.style,
        page_type=args.page_type,
        brand_colors=brand_colors,
        custom_prompt=args.custom_prompt,
        theme_hint=args.theme_hint,
        accent_color=args.accent_color,
        site_name=args.site_name or "",
        model=args.model,
        size=args.size,
        quality=args.quality,
        output=args.output,
    )


if __name__ == "__main__":
    main()
