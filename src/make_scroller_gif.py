import os
import re
import json
import math
import feedparser
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

def clean_text(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def hex_to_rgb(hex_color: str):
    h = (hex_color or "#000000").lstrip("#")
    if len(h) != 6:
        return (0, 0, 0)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

def fetch_titles(rss_url: str, limit: int) -> list[str]:
    feed = feedparser.parse(rss_url)
    titles = []
    for item in feed.entries[:limit]:
        title = clean_text(getattr(item, "title", ""))
        if title:
            titles.append(title)
    if not titles:
        titles = ["Ingen nyheder lige nu"]
    return titles

def build_text_line(titles: list[str]) -> str:
    return "  -  ".join(titles) + "  -  "

def make_scroller_gif(
    text_line: str,
    out_path: str,
    width: int,
    height: int,
    fps: int,
    seconds: float,
    px_per_frame: int,
    bg_rgb,
    fg_rgb=(255, 255, 255),
) -> None:
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    font = ImageFont.truetype(font_path, 34)

    # Mål tekstbredde
    tmp = Image.new("RGB", (10, 10), bg_rgb)
    dtmp = ImageDraw.Draw(tmp)

    text_w = int(dtmp.textlength(text_line, font=font)) or 1
    repeat = max(2, math.ceil((width * 3) / text_w))
    long_text = text_line * repeat

    long_w = int(dtmp.textlength(long_text, font=font))
    strip = Image.new("RGB", (long_w, height), bg_rgb)
    ds = ImageDraw.Draw(strip)

    bbox = ds.textbbox((0, 0), "Ag", font=font)
    text_h = bbox[3] - bbox[1]
    y = (height - text_h) // 2

    ds.text((0, y), long_text, font=font, fill=fg_rgb)

    total_frames = int(fps * seconds)
    frames = []
    offset = 0
    max_x = max(1, long_w - width)

    for _ in range(total_frames):
        x = offset % max_x
        frame = strip.crop((x, 0, x + width, height))
        frames.append(frame)
        offset += px_per_frame

    duration = 1.0 / fps
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    imageio.mimsave(out_path, frames, format="GIF", duration=duration, loop=0)

def main():
    # Læs sites.json
    with open("sites.json", "r", encoding="utf-8") as f:
        sites = json.load(f)

    for site in sites:
        slug = site["slug"]
        rss_url = site["rss_url"]
        bg_rgb = hex_to_rgb(site.get("bg_hex", "#000000"))

        width = int(site.get("width", 1200))
        height = int(site.get("height", 90))
        limit = int(site.get("limit", 10))
        fps = int(site.get("fps", 20))
        seconds = float(site.get("seconds", 20))
        px_per_frame = int(site.get("px_per_frame", 5))

        titles = fetch_titles(rss_url, limit=limit)
        line = build_text_line(titles)

        out_path = os.path.join("docs", slug, "ticker.gif")
        make_scroller_gif(
            text_line=line,
            out_path=out_path,
            width=width,
            height=height,
            fps=fps,
            seconds=seconds,
            px_per_frame=px_per_frame,
            bg_rgb=bg_rgb,
        )

        print(f"Built: {out_path}")

if __name__ == "__main__":
    main()
