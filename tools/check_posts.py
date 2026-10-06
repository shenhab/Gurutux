#!/usr/bin/env python3
"""Check every post's front matter and filename before it is published.

Run from the repository root:  python3 tools/check_posts.py
Exits with status 1 if any error is found. Needs PyYAML.
"""
import glob
import os
import re
import sys
from datetime import datetime, timezone

import yaml

REQUIRED = ["title", "date", "author", "tags"]
FILENAME = re.compile(r"^\d{4}-\d{2}-\d{2}-[A-Za-z0-9._-]+\.md$")

errors, warnings = [], []


def parse_date(value):
    """Return an aware UTC datetime, or None if it cannot be understood."""
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if hasattr(value, "year"):  # a plain date
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M %z", "%Y-%m-%d"):
        try:
            d = datetime.strptime(str(value), fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return None


def check(path):
    name = os.path.basename(path)
    if not FILENAME.match(name):
        errors.append(f"{name}: filename must look like YYYY-MM-DD-title.md using only letters, digits, dot, dash and underscore (colons break Windows checkouts)")

    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        errors.append(f"{name}: no front matter block at the top of the file")
        return
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        errors.append(f"{name}: front matter is not valid YAML ({e})")
        return

    for key in REQUIRED:
        if not fm.get(key):
            errors.append(f"{name}: missing front matter field '{key}'")

    date = parse_date(fm.get("date")) if fm.get("date") else None
    if fm.get("date") and date is None:
        errors.append(f"{name}: cannot read date '{fm.get('date')}'. Use YYYY-MM-DD HH:MM:SS -0000")
    if date and date > datetime.now(timezone.utc):
        errors.append(f"{name}: date {date:%Y-%m-%d %H:%M} UTC is in the future. GitHub Pages silently skips future-dated posts")
    if date and name[:10] != f"{date:%Y-%m-%d}":
        warnings.append(f"{name}: filename date differs from the front matter date")

    tags = fm.get("tags") or []
    if isinstance(tags, str):
        tags = tags.split()
    for t in tags:
        if t != str(t).lower():
            errors.append(f"{name}: tag '{t}' should be lowercase so it groups with the same tag elsewhere")

    image = fm.get("image")
    if image and not os.path.exists(str(image).lstrip("/")):
        errors.append(f"{name}: image '{image}' does not exist in the repository")
    if not image:
        warnings.append(f"{name}: no per-post social image (the site default will be used). Run tools/social_card.py")


def main():
    paths = sorted(glob.glob("_posts/*.md"))
    if not paths:
        errors.append("no posts found in _posts/")
    for p in paths:
        check(p)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"\nchecked {len(paths)} posts: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
