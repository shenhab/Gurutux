#!/usr/bin/env python3
"""Check the built site (_site) for broken internal links, images, scripts and #anchors.

Run after `jekyll build`, from the repository root:
    python3 tools/check_links.py              # internal links only; exits 1 on any problem
    python3 tools/check_links.py --external   # also test http(s) links (slow; some sites block bots)

Links to the site's own absolute address are checked as internal files.
"""
import argparse
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SITE_HOSTS = {"www.gurutux.com", "gurutux.com"}
SKIP_EXTERNAL = ("linkedin.com", "fonts.googleapis.com", "fonts.gstatic.com")
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:", "sms:")
LINK_ATTRS = {"a": "href", "link": "href", "img": "src", "script": "src", "iframe": "src", "source": "src"}


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []   # (tag, url)
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a" and a.get("name"):
            self.ids.add(a["name"])
        attr = LINK_ATTRS.get(tag)
        if attr and a.get(attr):
            if tag == "link" and a.get("rel") in ("canonical", "alternate", "prev", "next"):
                return
            self.refs.append((tag, a[attr].strip()))
        if tag == "meta" and a.get("property") in ("og:image", "twitter:image") and a.get("content"):
            self.refs.append(("meta", a["content"].strip()))


def page_url(root, path):
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    return "/" + rel


def resolve(root, from_url, ref):
    """Return (file_path or None, fragment) for an internal reference."""
    parts = urllib.parse.urlsplit(ref)
    target = urllib.parse.unquote(parts.path)
    if not target:
        target = from_url
    elif not target.startswith("/"):
        target = urllib.parse.urljoin(from_url, target)
    base = os.path.join(root, target.lstrip("/"))
    candidates = [base] if not target.endswith("/") else []
    candidates += [os.path.join(base, "index.html")] if os.path.isdir(base) or target.endswith("/") else []
    if not target.endswith("/"):
        candidates += [base + ".html", os.path.join(base, "index.html")]
    for c in candidates:
        if os.path.isfile(c):
            return c, parts.fragment
    return None, parts.fragment


def check_external(urls):
    bad = []
    for url in sorted(urls):
        host = urllib.parse.urlsplit(url).netloc.lower()
        if any(host.endswith(s) for s in SKIP_EXTERNAL):
            continue
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (link check)"}, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                code = r.status
        except urllib.error.HTTPError as e:
            code = e.code
        except Exception as e:  # DNS failure, timeout, TLS problem
            bad.append((url, type(e).__name__))
            continue
        if code >= 400 and code not in (401, 403, 429, 999):
            bad.append((url, f"HTTP {code}"))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="_site")
    ap.add_argument("--external", action="store_true")
    args = ap.parse_args()
    root = args.site
    if not os.path.isdir(root):
        sys.exit(f"{root} not found. Run 'bundle exec jekyll build' first.")

    pages = {}
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.endswith(".html"):
                p = os.path.join(dirpath, f)
                c = Collector()
                c.feed(open(p, encoding="utf-8", errors="replace").read())
                pages[p] = c

    problems, external, checked = [], set(), 0
    for path, col in pages.items():
        here = page_url(root, path)
        for tag, ref in col.refs:
            if not ref or ref.startswith(SKIP_SCHEMES):
                continue
            parts = urllib.parse.urlsplit(ref)
            if parts.scheme in ("http", "https") or ref.startswith("//"):
                if parts.netloc.lower() in SITE_HOSTS:
                    ref = urllib.parse.urlunsplit(("", "", parts.path or "/", parts.query, parts.fragment))
                else:
                    external.add(ref if parts.scheme else "https:" + ref)
                    continue
            checked += 1
            target, fragment = resolve(root, here, ref)
            if target is None:
                problems.append(f"{here}: <{tag}> points to {ref}, which does not exist")
            elif fragment and target in pages and fragment not in pages[target].ids:
                problems.append(f"{here}: <{tag}> points to {ref}, but that page has no element with id '{fragment}'")

    print(f"checked {checked} internal references on {len(pages)} pages")
    if args.external:
        bad = check_external(external)
        print(f"checked {len(external)} external links")
        problems += [f"external: {u} ({why})" for u, why in bad]
    for p in problems:
        print("ERROR:", p)
    print(f"{len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
