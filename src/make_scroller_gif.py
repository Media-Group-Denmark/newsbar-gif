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
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def fetch_titles(rss_url: str, limit: int) -> list[str]:
    feed = feedparser.parse(rss_url)
    titles = []
    for item in feed.entries[:limit]:
        title = clean_text(getattr(item, "title", ""))
        if title:
            titles.append(title)
    return titles or ["Ingen nyheder lige nu"]


def build_text_line(titles: list[str]) -> str:
    return "  -  ".join(titles) + "  -  "


def _load_best_bold_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Best løsning: brug en ægte bold font (DejaVuSans-Bold).
    Fallback: normal DejaVuSans hvis bold ikke findes på systemet.
    """
    bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    regular_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    for path in (bold_path, regular_path):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue

    # sidste fallback (meget basic)
    return ImageFont.load_default()


def make_gif(text: str, out_path: str, bg_rgb, fg_rgb=(255, 255, 255)):
    width, height = 1200, 90

    # Bedste løsning: ÆGTE bold font + let stroke for ekstra “fed” ticker-look
    font = _load_best_bold_font(size=34)
    stroke_width = 2  # justér til 2 hvis du vil have den endnu federe

    temp = Image.new("RGB", (10, 10), bg_rgb)
    d = ImageDraw.Draw(temp)

    text_width = int(d.textlength(text, font=font)) or 1
    repeat = max(2, math.ceil((width * 3) / text_width))
    long_text = text * repeat
    long_width = int(d.textlength(long_text, font=font))

    strip = Image.new("RGB", (long_width, height), bg_rgb)
    ds = ImageDraw.Draw(strip)

    bbox = ds.textbbox((0, 0), "Ag", font=font, stroke_width=stroke_width)
    y = (height - (bbox[3] - bbox[1])) // 2

    ds.text(
        (0, y),
        long_text,
        font=font,
        fill=fg_rgb,
        stroke_width=stroke_width,
        stroke_fill=fg_rgb,
    )

    frames = []
    offset = 0
    max_x = max(1, long_width - width)

    # ca. 20 sek animation
    for _ in range(400):
        x = offset % max_x
        frame = strip.crop((x, 0, x + width, height))
        frames.append(frame)
        offset += 6

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    imageio.mimsave(out_path, frames, duration=0.05, loop=0)


def main():
    with open("sites.json", "r", encoding="utf-8") as f:
        sites = json.load(f)

    for site in sites:
        slug = site["slug"]
        rss_url = site["rss_url"]
        bg_rgb = hex_to_rgb(site.get("bg_hex", "#990000"))

        titles = fetch_titles(rss_url, limit=int(site.get("limit", 10)))
        text = build_text_line(titles)

        out_path = os.path.join("docs", slug, "ticker.gif")
        make_gif(text, out_path, bg_rgb)

        print("Built:", out_path)


if __name__ == "__main__":
    main()
