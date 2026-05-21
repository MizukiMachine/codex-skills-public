#!/usr/bin/env python3
"""Analyze a web project for route-aware Open Graph image generation."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


JS_EXTENSIONS = {".tsx", ".ts", ".jsx", ".js"}
EXCLUDED_DIRS = {
    ".claude",
    ".codex",
    ".cursor",
    ".git",
    ".github",
    ".next",
    ".nuxt",
    ".output",
    ".turbo",
    ".vercel",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def iter_files(root: Path, extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in extensions and not is_excluded(path):
            files.append(path)
    return sorted(files)


def load_package_json(project_path: Path) -> dict[str, Any]:
    package_json = project_path / "package.json"
    if not package_json.exists():
        return {}
    try:
        return json.loads(read_text(package_json))
    except json.JSONDecodeError:
        return {}


def detect_framework(project_path: Path) -> str:
    pkg = load_package_json(project_path)
    deps = {}
    deps.update(pkg.get("dependencies", {}))
    deps.update(pkg.get("devDependencies", {}))

    if "next" in deps or (project_path / "next.config.js").exists() or (project_path / "next.config.mjs").exists():
        return "nextjs"
    if "astro" in deps or (project_path / "astro.config.mjs").exists():
        return "astro"
    if "gatsby" in deps or (project_path / "gatsby-config.js").exists() or (project_path / "gatsby-config.ts").exists():
        return "gatsby"
    if "react-router" in deps or "react-router-dom" in deps:
        return "react-router"
    if "react" in deps:
        return "react"
    if any(project_path.glob("*.html")):
        return "static-html"
    return "unknown"


def route_from_indexable_file(file_path: Path, root: Path) -> str:
    route = "/" + file_path.relative_to(root).with_suffix("").as_posix()
    if route.endswith("/index"):
        route = route[:-6] or "/"
    elif route == "/index":
        route = "/"
    return normalize_route(route)


def normalize_route(route: str) -> str:
    route = route.replace("\\", "/")
    route = re.sub(r"/\([^)]+\)", "", route)
    route = re.sub(r"/@[^/]+", "", route)
    route = re.sub(r"/+", "/", route)
    return route or "/"


def is_private_nextjs_app_path(relative_parent: Path) -> bool:
    return any(part.startswith("_") for part in relative_parent.parts)


def is_dynamic_route(route: str) -> bool:
    return bool(re.search(r"(\[[^/]+\]|:[^/]+|\*)", route))


def dynamic_segments(route: str) -> list[str]:
    segments: list[str] = []
    for part in route.split("/"):
        if not part:
            continue
        if re.fullmatch(r"\[+\.{0,3}[^\]]+\]+", part) or part.startswith(":") or "*" in part:
            segments.append(part)
    return segments


def find_nextjs_routes(project_path: Path) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []

    for app_dir in [project_path / "app", project_path / "src" / "app"]:
        if app_dir.exists():
            for page_file in iter_files(app_dir, JS_EXTENSIONS):
                if page_file.stem != "page":
                    continue
                relative_parent = page_file.parent.relative_to(app_dir)
                if is_private_nextjs_app_path(relative_parent):
                    continue
                route = "/" + relative_parent.as_posix()
                route = "/" if route == "/." else normalize_route(route)
                routes.append(route_record(project_path, page_file, route, "nextjs", "app"))

    for pages_dir in [project_path / "pages", project_path / "src" / "pages"]:
        if pages_dir.exists():
            for page_file in iter_files(pages_dir, JS_EXTENSIONS):
                rel = page_file.relative_to(pages_dir)
                if rel.parts[0] == "api" or any(part.startswith("_") for part in rel.parts):
                    continue
                route = route_from_indexable_file(page_file, pages_dir)
                routes.append(route_record(project_path, page_file, route, "nextjs", "pages"))

    return dedupe_routes(routes)


def find_astro_routes(project_path: Path) -> list[dict[str, Any]]:
    pages_dir = project_path / "src" / "pages"
    routes = [
        route_record(project_path, file_path, route_from_indexable_file(file_path, pages_dir), "astro", "pages")
        for file_path in iter_files(pages_dir, {".astro", ".md", ".mdx"})
    ]
    return dedupe_routes(routes)


def find_gatsby_routes(project_path: Path) -> list[dict[str, Any]]:
    pages_dir = project_path / "src" / "pages"
    routes = [
        route_record(project_path, file_path, route_from_indexable_file(file_path, pages_dir), "gatsby", "pages")
        for file_path in iter_files(pages_dir, JS_EXTENSIONS)
        if not file_path.stem.startswith("_")
    ]

    for node_file in [project_path / "gatsby-node.js", project_path / "gatsby-node.ts"]:
        if node_file.exists():
            content = read_text(node_file)
            for match in re.finditer(r"path:\s*[`'\"]([^`'\"]+)[`'\"]", content):
                route = normalize_route(match.group(1))
                routes.append(route_record(project_path, node_file, route, "gatsby", "programmatic"))

    return dedupe_routes(routes)


def find_react_routes(project_path: Path) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    src_dir = project_path / "src"
    for file_path in iter_files(src_dir, JS_EXTENSIONS):
        content = read_text(file_path)
        for pattern in [
            r"<Route[^>]+path=[{]?[`'\"]([^`'\"}]+)[`'\"]",
            r"\bpath:\s*[`'\"](/[^`'\"]*)[`'\"]",
        ]:
            for match in re.finditer(pattern, content):
                route = normalize_route(match.group(1))
                if route and not route.startswith("/:"):
                    routes.append(route_record(project_path, file_path, route, "react-router", "client"))
    return dedupe_routes(routes)


def find_static_html_routes(project_path: Path) -> list[dict[str, Any]]:
    routes = []
    for html_file in iter_files(project_path, {".html"}):
        rel_parts = html_file.relative_to(project_path).parts
        if rel_parts[0] in {"dist", "build", "coverage", "node_modules"}:
            continue
        if len(rel_parts) >= 2 and rel_parts[0] == "public" and rel_parts[1] == "og":
            continue
        route = route_from_indexable_file(html_file, project_path)
        routes.append(route_record(project_path, html_file, route, "static-html", "html"))
    return dedupe_routes(routes)


def route_record(project_path: Path, file_path: Path, route: str, framework: str, source: str) -> dict[str, Any]:
    metadata = extract_metadata_from_file(file_path)
    dynamic = is_dynamic_route(route)
    record = {
        "path": route,
        "file": file_path.relative_to(project_path).as_posix(),
        "type": categorize_page(route, metadata),
        "metadata": metadata,
        "framework": framework,
        "source": source,
        "dynamic": dynamic,
    }
    if dynamic:
        record["dynamic_segments"] = dynamic_segments(route)
    return record


def dedupe_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for route in routes:
        current = unique.get(route["path"])
        if current is None or metadata_score(route["metadata"]) > metadata_score(current["metadata"]):
            unique[route["path"]] = route
    return [unique[path] for path in sorted(unique)]


def metadata_score(metadata: dict[str, str]) -> int:
    return int(bool(metadata.get("title"))) + int(bool(metadata.get("description")))


def extract_metadata_from_file(file_path: Path) -> dict[str, str]:
    content = read_text(file_path)
    metadata: dict[str, str] = {}

    frontmatter = re.match(r"^---\s*\n(.*?)\n---", content, flags=re.DOTALL)
    if frontmatter:
        block = frontmatter.group(1)
        metadata.update(extract_key_value_metadata(block))

    metadata.update({k: v for k, v in extract_key_value_metadata(content).items() if k not in metadata})

    title_patterns = [
        r"<title[^>]*>(.*?)</title>",
        r"<h1[^>]*>(.*?)</h1>",
        r"^\s*#\s+(.+)$",
    ]
    description_patterns = [
        r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']+)[\"']",
        r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+name=[\"']description[\"']",
    ]

    if "title" not in metadata:
        for pattern in title_patterns:
            match = re.search(pattern, content, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                metadata["title"] = clean_text(match.group(1))
                break

    if "description" not in metadata:
        for pattern in description_patterns:
            match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
            if match:
                metadata["description"] = clean_text(match.group(1))
                break

    return {key: value for key, value in metadata.items() if value}


def extract_key_value_metadata(content: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for key in ["title", "description", "siteName", "site_name"]:
        pattern = rf"\b{key}\s*:\s*[`'\"]([^`'\"]+)[`'\"]"
        match = re.search(pattern, content)
        if match:
            normalized_key = "site_name" if key in {"siteName", "site_name"} else key
            metadata[normalized_key] = clean_text(match.group(1))
    return metadata


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def categorize_page(route: str, metadata: dict[str, str]) -> str:
    route_lower = route.lower()
    title_lower = metadata.get("title", "").lower()
    combined = f"{route_lower} {title_lower}"

    if route in {"/", "/index"}:
        return "landing"
    if any(token in combined for token in ["/blog", "/post", "/article", "/news", "blog", "article"]):
        return "article"
    if any(token in combined for token in ["/product", "/pricing", "/shop", "/store", "/feature", "product"]):
        return "product"
    if any(token in combined for token in ["/doc", "/guide", "/api", "/reference", "documentation", "docs"]):
        return "documentation"
    if any(token in combined for token in ["/about", "/team", "/contact", "/company", "about"]):
        return "about"
    return "general"


def extract_brand_colors(project_path: Path) -> list[str]:
    color_counts: Counter[str] = Counter()
    theme_files = [
        project_path / "tailwind.config.js",
        project_path / "tailwind.config.ts",
        project_path / "tailwind.config.mjs",
        project_path / "theme.config.js",
    ]
    scan_files = [path for path in theme_files if path.exists()]
    scan_files.extend(iter_files(project_path, {".css", ".scss", ".sass"}))

    for file_path in scan_files:
        content = read_text(file_path)
        for raw in re.findall(r"#[0-9a-fA-F]{3,8}\b", content):
            color = normalize_hex(raw)
            if color:
                color_counts[color] += 1

    neutrals = {"#000000", "#ffffff", "#f8f8f8", "#f9f9f9", "#fafafa"}
    ranked = [color for color, _ in color_counts.most_common() if color not in neutrals]
    ranked.extend([color for color, _ in color_counts.most_common() if color in neutrals])
    return ranked[:10]


def normalize_hex(value: str) -> str | None:
    value = value.lower()
    if len(value) == 4:
        return "#" + "".join(ch * 2 for ch in value[1:])
    if len(value) in {7, 9}:
        return value[:7]
    return None


def extract_fonts(project_path: Path) -> list[str]:
    fonts: list[str] = []
    scan_files = iter_files(project_path, {".css", ".scss", ".sass"})
    scan_files.extend(path for path in [
        project_path / "tailwind.config.js",
        project_path / "tailwind.config.ts",
        project_path / "tailwind.config.mjs",
    ] if path.exists())

    for file_path in scan_files:
        content = read_text(file_path)
        for match in re.finditer(r"font-family\s*:\s*([^;}{]+)", content, flags=re.IGNORECASE):
            add_font(fonts, match.group(1))
        for match in re.finditer(r"fontFamily\s*:\s*{(.*?)}", content, flags=re.DOTALL):
            for quoted in re.findall(r"[`'\"]([^`'\"]+)[`'\"]", match.group(1)):
                add_font(fonts, quoted)

    return fonts[:5]


def add_font(fonts: list[str], value: str) -> None:
    first = value.split(",")[0].strip().strip("\"'")
    if first and not first.startswith("var(") and first not in fonts:
        fonts.append(first)


def find_logo(project_path: Path) -> str | None:
    common_paths = [
        "public/logo.svg",
        "public/logo.png",
        "public/images/logo.svg",
        "public/images/logo.png",
        "public/assets/logo.svg",
        "public/assets/logo.png",
        "src/assets/logo.svg",
        "src/assets/logo.png",
        "assets/logo.svg",
        "assets/logo.png",
        "app/icon.png",
        "src/app/icon.png",
    ]
    for rel_path in common_paths:
        path = project_path / rel_path
        if path.exists():
            return rel_path

    candidates = []
    for ext in {".svg", ".png", ".jpg", ".jpeg"}:
        candidates.extend(project_path.rglob(f"*logo*{ext}"))
        candidates.extend(project_path.rglob(f"*brand*{ext}"))

    for path in sorted(candidates):
        if path.is_file() and not is_excluded(path):
            return path.relative_to(project_path).as_posix()
    return None


def find_routes(project_path: Path, framework: str) -> list[dict[str, Any]]:
    if framework == "nextjs":
        return find_nextjs_routes(project_path)
    if framework == "astro":
        return find_astro_routes(project_path)
    if framework == "gatsby":
        return find_gatsby_routes(project_path)
    if framework in {"react-router", "react"}:
        routes = find_react_routes(project_path)
        return routes or find_static_html_routes(project_path)
    if framework == "static-html":
        return find_static_html_routes(project_path)
    routes = find_static_html_routes(project_path)
    return routes


def analyze_codebase(project_path: Path) -> dict[str, Any]:
    framework = detect_framework(project_path)
    routes = find_routes(project_path, framework)
    brand = {
        "colors": extract_brand_colors(project_path),
        "fonts": extract_fonts(project_path),
        "logo": find_logo(project_path),
    }
    return {
        "framework": framework,
        "routes": routes,
        "brand": brand,
        "notes": build_notes(framework, routes, brand),
    }


def build_notes(framework: str, routes: list[dict[str, Any]], brand: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if not routes:
        notes.append("No routes were detected. Inspect custom routing or add routes manually to og-analysis.json.")
    if framework in {"react", "react-router"}:
        notes.append("React SPA metadata may not be crawler-visible without SSR, SSG, or prerendering.")
    dynamic_count = sum(1 for route in routes if route.get("dynamic"))
    if dynamic_count:
        notes.append(
            f"{dynamic_count} dynamic route(s) were detected. Generate concrete per-slug images from real data, "
            "or use generator --include-dynamic only for intentional fallback images."
        )
    if not brand.get("colors"):
        notes.append("No brand colors were detected. Inspect CSS variables, theme config, or screenshots manually.")
    if not brand.get("logo"):
        notes.append("No logo file was detected. Add a logo path manually if one exists.")
    return notes


def print_summary(analysis: dict[str, Any], output_file: Path) -> None:
    print(f"Framework: {analysis['framework']}")
    print(f"Routes: {len(analysis['routes'])}")
    page_types: Counter[str] = Counter(route["type"] for route in analysis["routes"])
    if page_types:
        print("Page types:")
        for page_type, count in sorted(page_types.items()):
            print(f"  {page_type}: {count}")
    dynamic_count = sum(1 for route in analysis["routes"] if route.get("dynamic"))
    if dynamic_count:
        print(f"Dynamic routes: {dynamic_count}")
    print(f"Brand colors: {len(analysis['brand']['colors'])}")
    print(f"Fonts: {len(analysis['brand']['fonts'])}")
    print(f"Logo: {analysis['brand']['logo'] or 'not found'}")
    if analysis["notes"]:
        print("Notes:")
        for note in analysis["notes"]:
            print(f"  - {note}")
    print(f"Saved analysis: {output_file}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a web project for OG image generation.")
    parser.add_argument("project_path", nargs="?", default=".", help="Project directory to analyze.")
    parser.add_argument("--output", help="Path for the generated analysis JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    project_path = Path(args.project_path).resolve()
    if not project_path.exists():
        raise SystemExit(f"Project path does not exist: {project_path}")

    output_file = Path(args.output).resolve() if args.output else project_path / "og-analysis.json"
    analysis = analyze_codebase(project_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    print_summary(analysis, output_file)


if __name__ == "__main__":
    main()
