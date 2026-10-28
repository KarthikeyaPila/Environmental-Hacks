#!/usr/bin/env python3
"""Build Phir's staged, cacheable static frontend without changing its artwork."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_HTML = ROOT / "frontend" / "phirFinal.optimized.html"
BRIDGES = (
    "phir-config.js",
    "phir-polish.js",
    "phir-identity.js",
    "phir-api-bridge.js",
    "phir-recycler-api-bridge.js",
    "phir-collector-api-bridge.js",
)
DATA_URI = re.compile(r"data:([^;,]+);base64,([A-Za-z0-9+/=]+)")
FONT_FACE = re.compile(r"@font-face\s*\{([^}]+)\}", re.IGNORECASE)


def asset_extension(mime: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/svg+xml": ".svg",
        "font/ttf": ".ttf",
    }.get(mime, "." + mime.rsplit("/", 1)[-1].split("+", 1)[0])


def critical_data_uris(html: str) -> tuple[list[str], list[str]]:
    """Return opening-critical assets and role-scene portraits from the source."""
    opening_tag = re.search(r"id=['\"]opening-art['\"][^>]*", html)
    if not opening_tag:
        raise ValueError("Could not find the opening artwork element")
    opening = DATA_URI.search(opening_tag.group(0))
    if not opening:
        raise ValueError("Opening artwork is not an embedded data URI")

    truck_assignment = re.search(r"const truck=['\"](data:[^'\"]+)['\"]", html)
    truck = DATA_URI.fullmatch(truck_assignment.group(1)) if truck_assignment else None
    if not truck:
        raise ValueError("Could not find the transition truck artwork")

    selection_marker = html.find("const SELECTION_ROLES=[")
    selection_end = html.find("];", selection_marker)
    selection = DATA_URI.findall(html[selection_marker:selection_end]) if selection_marker >= 0 and selection_end >= 0 else []
    if len(selection) != 3:
        raise ValueError(f"Expected three selection character images; found {len(selection)}")

    story_marker = html.find("const STORY_ROLES=[")
    story_end = html.find("];", story_marker)
    story = DATA_URI.findall(html[story_marker:story_end]) if story_marker >= 0 and story_end >= 0 else []
    if len(story) != 3:
        raise ValueError(f"Expected three role-scene portraits; found {len(story)}")

    encode = lambda match: match.group(0)
    critical = [encode(opening), encode(truck)]
    critical.extend(f"data:{mime};base64,{payload}" for mime, payload in selection)
    portraits = [f"data:{mime};base64,{payload}" for mime, payload in story]
    return list(dict.fromkeys(critical)), list(dict.fromkeys(portraits))


def brand_font_data_uris(html: str) -> list[str]:
    """Find the small variable body font used by the first-screen wordmark."""
    for face in FONT_FACE.finditer(html):
        block = face.group(1)
        family = re.search(r"font-family\s*:\s*(['\"]?)([^;'\"]+)\1", block, re.IGNORECASE)
        weight = re.search(r"font-weight\s*:\s*([^;]+)", block, re.IGNORECASE)
        source = re.search(r"url\(([\'\"]?)(data:[^\)\'\"]+)\1\)", block, re.IGNORECASE)
        if not family or not weight or not source:
            continue
        if family.group(2).strip().lower() == "dm sans" and weight.group(1).strip() == "100 900":
            return [source.group(2)]
    raise ValueError("Could not find the embedded DM Sans variable font for the wordmark")


def build(output: Path) -> None:
    html = SOURCE_HTML.read_text(encoding="utf-8")
    # Preserve the exact formatting of the currently served HTML bundle. The
    # extra space is inside the GSAP license comment and has no runtime effect.
    html = html.replace(
        " * https://gsap.com\n *\n * @license Copyright 2024, GreenSock.",
        " * https://gsap.com\n * \n * @license Copyright 2024, GreenSock.",
        1,
    )
    # Cache-bust the separately served bridge scripts when rebuilding the app.
    # Otherwise browsers/CDNs may continue using the old interaction handlers.
    html = re.sub(
        r"(phir-(?:config|polish|identity|api-bridge|recycler-api-bridge|collector-api-bridge)\.js\?v=)[^\" ]+",
        r"\g<1>20261013-2",
        html,
    )
    role_delay = "},1500);"
    if html.count(role_delay) != 1:
        raise ValueError("Could not safely update the role-transition delay")
    html = html.replace(role_delay, "},140);", 1)
    critical, portraits = critical_data_uris(html)
    brand_fonts = brand_font_data_uris(html)
    output.mkdir(parents=True, exist_ok=True)
    media_dir = output / "media"
    media_dir.mkdir(exist_ok=True)

    uri_to_path: dict[str, str] = {}
    unique_assets: dict[str, bytes] = {}

    def extract(match: re.Match[str]) -> str:
        mime, encoded = match.groups()
        payload = base64.b64decode(encoded, validate=True)
        digest = hashlib.sha256(payload).hexdigest()
        relative = f"media/{digest}{asset_extension(mime)}"
        previous = unique_assets.setdefault(relative, payload)
        if previous != payload:
            raise ValueError(f"Hash collision while extracting {relative}")
        uri_to_path[match.group(0)] = relative
        return relative

    built_html = DATA_URI.sub(extract, html)
    for relative, payload in unique_assets.items():
        (output / relative).write_bytes(payload)

    critical_paths = [uri_to_path[item] for item in critical]
    brand_font_paths = [uri_to_path[item] for item in brand_fonts]
    portrait_paths = [uri_to_path[item] for item in portraits]
    preload_markup = "".join(
        f'<link rel="preload" as="font" type="font/ttf" href="{path}" crossorigin fetchpriority="high">'
        for path in brand_font_paths
    ) + "".join(
        f'<link rel="preload" as="image" href="{path}" fetchpriority="high">'
        for path in critical_paths
    )
    critical_script = (
        "<script>"
        f"window.PHIR_CRITICAL_IMAGES={json.dumps(critical_paths)};"
        f"window.PHIR_ROLE_PORTRAITS={json.dumps(portrait_paths)};"
        "window.PHIR_CRITICAL_IMAGES_READY=Promise.all(window.PHIR_CRITICAL_IMAGES.map(src=>new Promise(resolve=>{"
        "const image=new Image();let settled=false;const finish=()=>{if(settled)return;settled=true;"
        "if(image.decode)image.decode().catch(()=>{}).then(resolve);else resolve()};"
        "image.onload=finish;image.onerror=()=>{settled=true;resolve()};image.src=src;"
        "if(image.complete&&image.naturalWidth)finish()})));"
        "</script>"
    )
    marker = "<meta charset=\"utf-8\">"
    if built_html.count(marker) != 1:
        raise ValueError("Expected one UTF-8 charset marker in the HTML head")
    built_html = built_html.replace(marker, marker + preload_markup + critical_script, 1)

    # Do not let the automatic intro-to-role transition reveal a blank image.
    old_end_intro = "function endIntro(){clearTimeout(introTimer);const intro=$('#intro');if(intro.classList.contains('done'))return;"
    new_end_intro = (
        "let phirIntroWaitingForImages=false;function endIntro(){clearTimeout(introTimer);"
        "if(window.PHIR_CRITICAL_IMAGES_READY&&!window.PHIR_CRITICAL_IMAGES_DONE){"
        "if(phirIntroWaitingForImages)return;phirIntroWaitingForImages=true;"
        "window.PHIR_CRITICAL_IMAGES_READY.then(()=>{window.PHIR_CRITICAL_IMAGES_DONE=true;"
        "phirIntroWaitingForImages=false;endIntro()});return;}"
        "const intro=$('#intro');if(intro.classList.contains('done'))return;"
    )
    if built_html.count(old_end_intro) != 1:
        raise ValueError("Could not safely patch the intro image-ready transition")
    built_html = built_html.replace(old_end_intro, new_end_intro, 1)

    # Keep later-scene portraits out of the chooser's download burst. Warm only
    # the role the visitor is about to enter (hover, keyboard focus, or touch).
    loader = """(()=>{
  const portraits=window.PHIR_ROLE_PORTRAITS||[];
  const started=new Set();
  function warm(index){
    const src=portraits[index];
    if(!src||started.has(src))return;
    started.add(src);
    const image=new Image();
    image.fetchPriority='low';
    image.src=src;
  }
  window.PHIR_WARM_ROLE_PORTRAIT=warm;
  const roleIndex={household:0,collector:1,recycler:2};
  const warmFromEvent=event=>{
    const card=event.target.closest?.('.role[data-role]');
    if(card&&Object.hasOwn(roleIndex,card.dataset.role))warm(roleIndex[card.dataset.role]);
  };
  document.addEventListener('pointerover',warmFromEvent,{passive:true});
  document.addEventListener('pointerdown',warmFromEvent,{passive:true});
  document.addEventListener('focusin',warmFromEvent);
})();"""
    (output / "phir-asset-loader.js").write_text(loader, encoding="utf-8")
    built_html = built_html.replace(
        "</body>",
        '<script src="phir-asset-loader.js?v=20261013-2" defer></script></body>',
        1,
    )
    (output / "index.html").write_text(built_html, encoding="utf-8")

    for filename in BRIDGES:
        shutil.copy2(ROOT / "frontend" / filename, output / filename)
    map_output = output / "map"
    map_output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "frontend" / "map" / "delhi-map-selectable.html",
        map_output / "delhi-map-selectable.html",
    )

    (output / "customHttp.yml").write_text(
        "customHeaders:\n"
        "  - pattern: '/media/*'\n"
        "    headers:\n"
        "      - key: 'Cache-Control'\n"
        "        value: 'public, max-age=31536000, immutable'\n",
        encoding="utf-8",
    )

    remaining = DATA_URI.findall(built_html)
    if remaining:
        raise ValueError(f"Data URI replacement incomplete: {len(remaining)} remain")
    print(f"Built {output}")
    print(f"HTML: {len(built_html.encode('utf-8')):,} bytes")
    print(f"Extracted assets: {len(unique_assets)} files, {sum(map(len, unique_assets.values())):,} bytes")
    print(f"Opening/chooser preloads: {len(critical_paths)} assets")
    print(f"Wordmark font preloads: {len(brand_font_paths)} asset(s)")
    print(f"Background role portraits: {len(portrait_paths)} assets")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / "phir-fast",
        help="Output directory (default: dist/phir-fast)",
    )
    args = parser.parse_args()
    build(args.output.resolve())


if __name__ == "__main__":
    main()
