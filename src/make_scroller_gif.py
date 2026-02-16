import os
import re
import json
import math
import feedparser
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont


# -----------------------------
# Helpers
# -----------------------------
def clean_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def hex_to_rgb(hex_color: str, default: str = "#000000") -> tuple[int, int, int]:
    h = (hex_color or default).lstrip("#")
    if len(h) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        h = default.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def fetch_titles(rss_url: str, limit: int) -> list[str]:
    feed = feedparser.parse(rss_url)
    titles: list[str] = []
    for item in getattr(feed, "entries", [])[: max(0, int(limit))]:
        title = clean_text(getattr(item, "title", ""))
        if title:
            titles.append(title)
    return titles or ["Ingen nyheder lige nu"]


def build_text_line(titles: list[str]) -> str:
    return "  -  ".join(titles) + "  -  "


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    regular_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(bold_path, size)
    except OSError:
        return ImageFont.truetype(regular_path, size)


# -----------------------------
# GIF generation
# -----------------------------
def make_gif(
    text: str,
    out_path: str,
    bg_rgb: tuple[int, int, int],
    fg_rgb: tuple[int, int, int],
    width: int = 1200,
    height: int = 90,
    font_size: int = 34,
    frames_count: int = 400,
    step_px: int = 6,
    frame_duration: float = 0.05,
):
    font = _load_font(size=font_size)

    # Measure base text width
    temp = Image.new("RGB", (10, 10), bg_rgb)
    d = ImageDraw.Draw(temp)

    base_width = int(d.textlength(text, font=font)) or 1
    repeat = max(2, math.ceil((width * 3) / base_width))
    long_text = text * repeat
    long_width = int(d.textlength(long_text, font=font)) or width

    # Draw long strip
    strip = Image.new("RGB", (long_width, height), bg_rgb)
    ds = ImageDraw.Draw(strip)

    bbox = ds.textbbox((0, 0), "Ag", font=font)
    text_h = bbox[3] - bbox[1]
    y = (height - text_h) // 2

    ds.text((0, y), long_text, font=font, fill=fg_rgb)

    # Build frames
    frames = []
    offset = 0
    max_x = max(1, long_width - width)

    for _ in range(frames_count):
        x = offset % max_x
        frame = strip.crop((x, 0, x + width, height))
        frames.append(frame)
        offset += step_px

    out_dir = os.path.dirname(out_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    imageio.mimsave(out_path, frames, duration=frame_duration, loop=0)


# -----------------------------
# Main
# -----------------------------
def main():
    with open("sites.json", "r", encoding="utf-8") as f:
        sites = json.load(f)

    for site in sites:
        slug = site["slug"]
        rss_url = site["rss_url"]

        bg_rgb = hex_to_rgb(site.get("bg_hex", "#990000"), default="#990000")
        fg_rgb = hex_to_rgb(site.get("fg_hex", "#FFFFFF"), default="#FFFFFF")  # <- per-site tekstfarve

        limit = int(site.get("limit", 10))
        titles = fetch_titles(rss_url, limit=limit)
        text = build_text_line(titles)

        out_path = os.path.join("docs", slug, "ticker.gif")
        make_gif(text, out_path, bg_rgb=bg_rgb, fg_rgb=fg_rgb)

        print("Built:", out_path)


if __name__ == "__main__":
    main()
