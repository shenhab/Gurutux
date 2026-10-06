#!/usr/bin/env python3
"""Generate 1200x630 social preview cards (the image shown when a link is shared).

Usage, from the repository root:
    python3 tools/social_card.py --default                 # assets/images/social-default.png
    python3 tools/social_card.py _posts/2026-01-01-x.md    # one card, printed front matter line
    python3 tools/social_card.py --all --write             # every post; add image: to front matter

Needs Pillow (pip install pillow). Cards are saved to assets/images/social/.
"""
import argparse
import glob
import os
import re
import sys

import yaml
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
SITE_NAME = "GuRuTuX"
SITE_HOST = "www.gurutux.com"
OUT_DIR = "assets/images/social"
DEFAULT_OUT = "assets/images/social-default.png"

FONT_CANDIDATES = {
    "bold": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ],
    "regular": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/Library/Fonts/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ],
}


def font(kind, size):
    for path in FONT_CANDIDATES[kind]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def read_front_matter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        sys.exit(f"{path}: no front matter")
    return yaml.safe_load(m.group(1)) or {}, text


def background():
    img = Image.new("RGB", (W, H), "#0b1f3a")
    px = img.load()
    top, bottom = (11, 31, 58), (0, 86, 179)
    for y in range(H):
        t = y / (H - 1)
        row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = row
    return img


def wrap(draw, text, fnt, max_width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def fit_title(draw, title, max_width, max_lines=4):
    for size in range(72, 36, -4):
        fnt = font("bold", size)
        lines = wrap(draw, title, fnt, max_width)
        if len(lines) <= max_lines:
            return fnt, lines
    fnt = font("bold", 36)
    lines = wrap(draw, title, fnt, max_width)[:max_lines]
    lines[-1] = lines[-1].rstrip(".") + "…"
    return fnt, lines


def render(title, subtitle, footer_left, out_path):
    img = background()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 14, H], fill="#7db7ff")
    d.text((70, 52), SITE_NAME, font=font("bold", 40), fill="#ffffff")

    fnt, lines = fit_title(d, title, W - 70 - 90)
    line_h = int(fnt.size * 1.22)
    y = 150 + max(0, (4 - len(lines))) * line_h // 2
    for line in lines:
        d.text((70, y), line, font=fnt, fill="#ffffff")
        y += line_h

    if subtitle:
        d.text((70, H - 150), subtitle, font=font("regular", 30), fill="#cfe3ff")
    d.text((70, H - 80), footer_left, font=font("regular", 28), fill="#9fc4f5")
    host_font = font("bold", 28)
    d.text((W - 70 - d.textlength(SITE_HOST, font=host_font), H - 80), SITE_HOST, font=host_font, fill="#ffffff")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, optimize=True)


def card_for_post(path, write):
    fm, text = read_front_matter(path)
    base = re.sub(r"\.md$", "", os.path.basename(path))
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base)
    out = f"{OUT_DIR}/{base}.png"

    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split()
    date = fm.get("date")
    date_s = date.strftime("%B %-d, %Y") if hasattr(date, "strftime") else str(date or "")[:10]
    footer = "  ·  ".join(x for x in [fm.get("author"), date_s] if x)
    subtitle = "  ".join(f"#{t}" for t in list(tags)[:4])
    render(str(fm.get("title", base)), subtitle, footer, out)

    line = f"image: /{out}"
    if write and not re.search(r"^image:", text.split("\n---", 1)[0], re.M):
        text = re.sub(r"^(---\s*\n.*?)(\n---\s*\n)", lambda m: f"{m.group(1)}\n{line}{m.group(2)}", text, count=1, flags=re.S)
        open(path, "w", encoding="utf-8").write(text)
        print(f"{path}: wrote {out} and added front matter")
    else:
        print(f"{path}: wrote {out}   ({line})")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("posts", nargs="*", help="post files, for example _posts/2026-01-01-x.md")
    ap.add_argument("--all", action="store_true", help="every file in _posts/")
    ap.add_argument("--default", action="store_true", help="the site-wide fallback card")
    ap.add_argument("--write", action="store_true", help="add the image: line to each post's front matter")
    args = ap.parse_args()

    if args.default:
        render("Technical articles on Linux, SRE, databases and cloud infrastructure", "", "Mahmoud Elshenhab", DEFAULT_OUT)
        print(f"wrote {DEFAULT_OUT}")
    paths = sorted(glob.glob("_posts/*.md")) if args.all else args.posts
    for p in paths:
        card_for_post(p, args.write)
    if not (args.default or paths):
        ap.print_help()


if __name__ == "__main__":
    main()
