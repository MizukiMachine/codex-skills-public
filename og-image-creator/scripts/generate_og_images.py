#!/usr/bin/env python3
"""Generate route-specific Open Graph images from an og-analysis.json file."""

from __future__ import annotations

import argparse
import asyncio
import base64
import html
import json
import mimetypes
import re
from pathlib import Path
from typing import Any

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None


OG_WIDTH = 1200
OG_HEIGHT = 630


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def route_title(route: dict[str, Any]) -> str:
    metadata = route.get("metadata", {})
    if metadata.get("title"):
        return clean_text(metadata["title"])
    path = route.get("path", "/")
    if path == "/":
        return "Home"
    return path.strip("/").replace("-", " ").replace("_", " ").replace("/", " / ").title()


def route_description(route: dict[str, Any]) -> str:
    return clean_text(route.get("metadata", {}).get("description", ""))


def page_label(route: dict[str, Any]) -> str:
    labels = {
        "landing": "Website",
        "article": "Article",
        "product": "Product",
        "documentation": "Documentation",
        "about": "About",
        "general": "Preview",
    }
    return labels.get(route.get("type", "general"), "Preview")


def safe_filename(route_path: str, used: set[str]) -> str:
    if route_path == "/":
        stem = "home"
    else:
        stem = route_path.strip("/")
        stem = stem.replace("[", "").replace("]", "")
        stem = re.sub(r"[^a-zA-Z0-9]+", "-", stem).strip("-").lower() or "page"
    filename = f"{stem}.png"
    index = 2
    while filename in used:
        filename = f"{stem}-{index}.png"
        index += 1
    used.add(filename)
    return filename


def route_is_dynamic(route: dict[str, Any]) -> bool:
    path = route.get("path", "")
    return bool(route.get("dynamic")) or bool(re.search(r"(\[[^/]+\]|:[^/]+|\*)", path))


def select_routes(
    routes: list[dict[str, Any]],
    include_dynamic: bool,
    limit: int | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    skipped_dynamic = [route for route in routes if route_is_dynamic(route) and not include_dynamic]
    selected = [route for route in routes if include_dynamic or not route_is_dynamic(route)]
    if limit:
        selected = selected[:limit]
    return selected, skipped_dynamic


def normalize_hex(value: str | None) -> str | None:
    if not value:
        return None
    value = value.strip().lower()
    if not re.match(r"^#[0-9a-f]{6}$", value):
        return None
    return value


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def relative_luminance(hex_color: str) -> float:
    channels = []
    for channel in hex_to_rgb(hex_color):
        value = channel / 255
        channels.append(value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def is_dark(hex_color: str) -> bool:
    return relative_luminance(hex_color) < 0.42


def theme_from_brand(brand: dict[str, Any]) -> dict[str, str]:
    colors = [normalize_hex(color) for color in brand.get("colors", [])]
    colors = [color for color in colors if color]
    primary = colors[0] if colors else "#2563eb"
    secondary = colors[1] if len(colors) > 1 else "#14b8a6"

    if is_dark(primary):
        background = f"linear-gradient(135deg, {primary} 0%, #111827 100%)"
        text = "#ffffff"
        muted = "rgba(255, 255, 255, 0.78)"
        panel = "rgba(255, 255, 255, 0.10)"
        border = "rgba(255, 255, 255, 0.20)"
    else:
        background = f"linear-gradient(135deg, #ffffff 0%, {primary}22 54%, {secondary}24 100%)"
        text = "#111827"
        muted = "rgba(17, 24, 39, 0.72)"
        panel = "rgba(255, 255, 255, 0.72)"
        border = "rgba(17, 24, 39, 0.12)"

    fonts = brand.get("fonts", [])
    font = fonts[0] if fonts else "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"

    return {
        "primary": primary,
        "secondary": secondary,
        "background": background,
        "text": text,
        "muted": muted,
        "panel": panel,
        "border": border,
        "font": font,
    }


def file_url(project_path: Path, rel_path: str | None) -> str:
    if not rel_path:
        return ""
    if re.match(r"^https?://", rel_path):
        return rel_path
    path = (project_path / rel_path).resolve()
    if path.exists():
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"
    return ""


def title_size(title: str, page_type: str) -> int:
    length = len(title)
    base = {
        "landing": 74,
        "product": 68,
        "documentation": 62,
        "article": 58,
        "about": 66,
        "general": 64,
    }.get(page_type, 62)
    if length > 110:
        return max(42, base - 24)
    if length > 82:
        return max(46, base - 18)
    if length > 58:
        return max(50, base - 10)
    return base


def render_logo(logo_url: str, alt: str) -> str:
    if not logo_url:
        return ""
    return f'<img class="logo" src="{html.escape(logo_url)}" alt="{html.escape(alt)}">'


def render_route_html(route: dict[str, Any], brand: dict[str, Any], project_path: Path) -> str:
    title = route_title(route)
    description = route_description(route)
    page_type = route.get("type", "general")
    label = page_label(route)
    theme = theme_from_brand(brand)
    logo_url = file_url(project_path, brand.get("logo"))
    logo = render_logo(logo_url, brand.get("site_name") or title)
    size = title_size(title, page_type)

    escaped_title = html.escape(title)
    escaped_description = html.escape(description)
    escaped_label = html.escape(label)

    if page_type == "landing":
        body = f"""
        <main class="layout centered">
          <div class="brand-row">{logo}<span>{escaped_label}</span></div>
          <h1 style="font-size:{size}px">{escaped_title}</h1>
          {f'<p class="description">{escaped_description}</p>' if description else ''}
        </main>
        """
    elif page_type == "article":
        body = f"""
        <main class="layout editorial">
          <div>
            <div class="eyebrow">{escaped_label}</div>
            <h1 style="font-size:{size}px">{escaped_title}</h1>
            {f'<p class="description">{escaped_description}</p>' if description else ''}
          </div>
          <footer>{logo}<span>{html.escape(route.get("path", ""))}</span></footer>
        </main>
        """
    elif page_type == "product":
        body = f"""
        <main class="layout split">
          <section>
            <div class="eyebrow">{escaped_label}</div>
            <h1 style="font-size:{size}px">{escaped_title}</h1>
            {f'<p class="description">{escaped_description}</p>' if description else ''}
          </section>
          <aside class="product-mark">
            <div class="accent-card">{logo}<span>{escaped_label}</span></div>
          </aside>
        </main>
        """
    elif page_type == "documentation":
        body = f"""
        <main class="layout docs">
          <div class="eyebrow">{escaped_label}</div>
          <h1 style="font-size:{size}px">{escaped_title}</h1>
          {f'<p class="description">{escaped_description}</p>' if description else ''}
          <div class="rule"></div>
        </main>
        """
    elif page_type == "about":
        body = f"""
        <main class="layout centered">
          {logo}
          <h1 style="font-size:{size}px">{escaped_title}</h1>
          {f'<p class="description">{escaped_description}</p>' if description else ''}
        </main>
        """
    else:
        body = f"""
        <main class="layout general">
          <div class="eyebrow">{escaped_label}</div>
          <h1 style="font-size:{size}px">{escaped_title}</h1>
          {f'<p class="description">{escaped_description}</p>' if description else ''}
          <footer>{logo}<span>{html.escape(route.get("path", ""))}</span></footer>
        </main>
        """

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    * {{
      box-sizing: border-box;
    }}
    html, body {{
      width: {OG_WIDTH}px;
      height: {OG_HEIGHT}px;
      margin: 0;
      overflow: hidden;
    }}
    body {{
      background: {theme["background"]};
      color: {theme["text"]};
      font-family: {theme["font"]};
      letter-spacing: 0;
    }}
    body::before {{
      content: "";
      position: absolute;
      inset: 34px;
      border: 1px solid {theme["border"]};
      pointer-events: none;
    }}
    .layout {{
      width: 100%;
      height: 100%;
      padding: 72px 84px;
      position: relative;
      display: flex;
    }}
    .centered {{
      align-items: center;
      justify-content: center;
      flex-direction: column;
      text-align: center;
      gap: 28px;
    }}
    .editorial, .general, .docs {{
      flex-direction: column;
      justify-content: space-between;
      gap: 28px;
    }}
    .docs {{
      justify-content: center;
      align-items: flex-start;
    }}
    .split {{
      align-items: center;
      gap: 72px;
    }}
    .split section {{
      flex: 1.2;
    }}
    .product-mark {{
      flex: 0.8;
      display: flex;
      justify-content: flex-end;
    }}
    .accent-card {{
      width: 330px;
      height: 330px;
      border: 1px solid {theme["border"]};
      background: {theme["panel"]};
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 22px;
    }}
    h1 {{
      margin: 0;
      max-width: 980px;
      line-height: 1.04;
      font-weight: 820;
      overflow-wrap: anywhere;
    }}
    .split h1 {{
      max-width: 660px;
    }}
    .description {{
      margin: 0;
      max-width: 850px;
      color: {theme["muted"]};
      font-size: 30px;
      line-height: 1.32;
      font-weight: 460;
    }}
    .split .description {{
      max-width: 640px;
    }}
    .eyebrow, .brand-row, footer, .accent-card span {{
      color: {theme["muted"]};
      font-size: 23px;
      font-weight: 680;
      letter-spacing: 0;
    }}
    .eyebrow {{
      margin-bottom: 24px;
    }}
    .brand-row, footer {{
      display: flex;
      align-items: center;
      gap: 18px;
    }}
    footer {{
      justify-content: space-between;
      min-height: 48px;
    }}
    .logo {{
      max-width: 190px;
      max-height: 72px;
      object-fit: contain;
    }}
    .brand-row .logo, footer .logo {{
      max-width: 150px;
      max-height: 46px;
    }}
    .accent-card .logo {{
      max-width: 190px;
      max-height: 120px;
    }}
    .rule {{
      width: 100%;
      max-width: 980px;
      height: 10px;
      margin-top: 44px;
      background: linear-gradient(90deg, {theme["primary"]}, {theme["secondary"]});
    }}
  </style>
</head>
<body>
  {body}
</body>
</html>"""


async def wait_for_assets(page) -> None:
    try:
        await page.wait_for_function(
            "() => Array.from(document.images).every((img) => img.complete)",
            timeout=2500,
        )
    except Exception:
        pass
    try:
        await page.evaluate("document.fonts && document.fonts.ready")
    except Exception:
        pass


async def screenshot_html(playwright, html_content: str, output_path: Path) -> None:
    browser = await playwright.chromium.launch()
    try:
        page = await browser.new_page(viewport={"width": OG_WIDTH, "height": OG_HEIGHT}, device_scale_factor=1)
        await page.set_content(html_content, wait_until="load")
        await wait_for_assets(page)
        await page.screenshot(path=str(output_path), type="png", full_page=False)
    finally:
        await browser.close()


def build_preview(out_dir: Path, manifest: list[dict[str, Any]]) -> None:
    cards = "\n".join(
        f"""<section>
  <img src="{html.escape(item['file'])}" width="600" height="315" alt="{html.escape(item['alt'])}">
  <h2>{html.escape(item['route'])}</h2>
  <p>{html.escape(item['title'])}</p>
</section>"""
        for item in manifest
    )
    preview = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>OG Image Preview</title>
  <style>
    body {{
      margin: 0;
      padding: 32px;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
      background: #f3f4f6;
      color: #111827;
    }}
    main {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
      gap: 28px;
    }}
    section {{
      background: white;
      border: 1px solid #d1d5db;
      padding: 16px;
    }}
    img {{
      width: 100%;
      height: auto;
      display: block;
      border: 1px solid #e5e7eb;
    }}
    h2 {{
      margin: 14px 0 4px;
      font-size: 16px;
    }}
    p {{
      margin: 0;
      color: #4b5563;
    }}
  </style>
</head>
<body>
  <h1>OG Image Preview</h1>
  <main>
    {cards}
  </main>
</body>
</html>"""
    (out_dir / "preview.html").write_text(preview, encoding="utf-8")


async def generate_all(
    project_path: Path,
    analysis: dict[str, Any],
    out_dir: Path,
    limit: int | None,
    include_dynamic: bool,
) -> list[dict[str, Any]]:
    all_routes = analysis.get("routes", [])
    routes, skipped_dynamic = select_routes(all_routes, include_dynamic, limit)
    if skipped_dynamic:
        print(f"Skipping {len(skipped_dynamic)} dynamic route(s). Use --include-dynamic to generate fallback images intentionally.")

    if not routes:
        raise SystemExit(
            "No static routes selected for generation. Add concrete routes to og-analysis.json "
            "or pass --include-dynamic for intentional fallback images."
        )

    if async_playwright is None:
        raise SystemExit(
            "Missing dependency: playwright. Install it with "
            "`python3 -m pip install playwright` and `python3 -m playwright install chromium`."
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, Any]] = []
    used_filenames: set[str] = set()

    async with async_playwright() as playwright:
        for index, route in enumerate(routes, 1):
            filename = safe_filename(route.get("path", "/"), used_filenames)
            output_path = out_dir / filename
            html_content = render_route_html(route, analysis.get("brand", {}), project_path)
            print(f"[{index}/{len(routes)}] {route.get('path', '/')} -> {output_path.relative_to(project_path)}")
            await screenshot_html(playwright, html_content, output_path)
            size = output_path.stat().st_size
            manifest.append(
                {
                    "route": route.get("path", "/"),
                    "file": filename,
                    "title": route_title(route),
                    "description": route_description(route),
                    "type": route.get("type", "general"),
                    "dynamic": route_is_dynamic(route),
                    "width": OG_WIDTH,
                    "height": OG_HEIGHT,
                    "bytes": size,
                    "alt": f"Social preview for {route_title(route)}",
                }
            )
            if size > 200_000:
                print(f"  warning: {filename} is {size // 1024} KB; consider optimization.")

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    build_preview(out_dir, manifest)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OG images from og-analysis.json.")
    parser.add_argument("project_path", nargs="?", default=".", help="Project directory.")
    parser.add_argument("--analysis", help="Analysis JSON path. Defaults to <project>/og-analysis.json.")
    parser.add_argument("--out-dir", help="Output directory. Defaults to <project>/public/og.")
    parser.add_argument("--limit", type=int, help="Generate only the first N routes for iteration.")
    parser.add_argument(
        "--include-dynamic",
        action="store_true",
        help="Generate fallback images for dynamic parameterized routes. Prefer concrete per-slug routes when available.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_path = Path(args.project_path).resolve()
    analysis_path = Path(args.analysis).resolve() if args.analysis else project_path / "og-analysis.json"
    out_dir = Path(args.out_dir).resolve() if args.out_dir else project_path / "public" / "og"

    if not project_path.exists():
        raise SystemExit(f"Project path does not exist: {project_path}")
    if not analysis_path.exists():
        raise SystemExit(f"Analysis file does not exist: {analysis_path}. Run analyze_codebase.py first.")

    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    manifest = asyncio.run(generate_all(project_path, analysis, out_dir, args.limit, args.include_dynamic))
    print(f"Generated {len(manifest)} image(s) in {out_dir}")
    print(f"Preview: {out_dir / 'preview.html'}")


if __name__ == "__main__":
    main()
