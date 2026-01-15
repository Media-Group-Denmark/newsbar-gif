import os
import re
import math
import feedparser
import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

RSS_URL = "https://www.nyheder24.dk/feeds/rss/klaviyo/latest-news/"

def clean_text(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = re.sub(r"\s+", " ", s).strip()
    return s

def fetch_titles(limit=8):
    feed = feedparser.parse(RSS_URL)
    titles = []
    for item in feed.entries[:limit]:
        title = clean_text(getattr(item, "title", ""))
        if title:
            titles.append(title)
    return titles

def build_text_line(titles):
    return "  -  ".join(titles) + "  -  "

def make_gif(text):
    width, height = 1200, 90
    bg, fg = (15, 15, 15), (255, 255, 255)

    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34
    )

    temp = Image.new("RGB", (10, 10))
    d = ImageDraw.Draw(temp)
    text_width = int(d.textlength(text, font=font))

    repeat = max(2, math.ceil((width * 3) / text_width))
    long_text = text * repeat
    long_width = int(d.textlength(long_text, font=font))

    strip = Image.new("RGB", (long_width, height), bg)
    ds = ImageDraw.Draw(strip)

    bbox = ds.textbbox((0, 0), "Ag", font=font)
    y = (height - (bbox[3] - bbox[1])) // 2
    ds.text((0, y), long_text, font=font, fill=fg)

    frames = []
    offset = 0
    for _ in range(800):
        frame = strip.crop((offset, 0, offset + width, height))
        frames.append(frame)
        offset = (offset + 4) % (long_width - width)

    os.makedirs("docs", exist_ok=True)
    imageio.mimsave("docs/ticker.gif", frames, duration=0.05)

def main():
    titles = fetch_titles()
    text = build_text_line(titles)
    make_gif(text)

if __name__ == "__main__":
    main()
