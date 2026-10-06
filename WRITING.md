# Writing for GuRuTuX

How to add a post and use the site's features. This file is not published on the site.

## A new post

Create `_posts/YYYY-MM-DD-short-title.md`. Use only letters, digits, dots and dashes in the filename.

```yaml
---
layout: post
title: "A clear title"
date: 2026-10-06 09:00:00 -0000
author: "Mahmoud Elshenhab"
tags: kubernetes etcd architecture
---
```

- **date.** GitHub Pages builds in UTC and silently skips posts dated in the future. Use the current UTC time or earlier.
- **tags.** Lowercase, separated by spaces. They become links to the Tags page and feed the related posts.
- **excerpt (optional).** What the home page shows. Without it, the first paragraph is used.
- **last_modified_at (optional).** `2026-11-01`. Shows "Updated ..." in the post header and in search engines.
- **series (optional).** `series: "Learning Kubernetes"`. Every post with the same value gets a numbered list of the series at the top. It appears once the series has two posts.
- **image (optional).** A social preview card. See below.

## Drafts and previews

1. Put the file in `_drafts/` with no date in the name, for example `_drafts/etcd-quorum.md`. Drafts are never published.
2. Preview on your machine: `bundle install`, then `bundle exec jekyll serve --drafts --future`, then open http://localhost:4000.
3. Or push a branch other than master. The "Draft preview" workflow builds it with drafts included and attaches the site as a download. Unzip it and run `python3 -m http.server -d site-preview`.
4. To publish, move it to `_posts/` with a date in the name, set `date:` in the front matter, and push to master.

## Interactive widgets

Put the widget page in `assets/widgets/`, then add one line to the post:

```liquid
{% raw %}{% include widget.html src="/assets/widgets/NAME.html" title="What it shows" height=900 %}{% endraw %}
```

The frame resizes itself and follows the light or dark theme. A widget page can ask for its height with
`window.parent.postMessage({type: 'widget-resize', height: 700}, '*')` and read the theme from
`document.documentElement.getAttribute('data-theme')`. List it on the Cheat Sheets page by adding an entry to `_data/cheatsheets.yml`.

## Social preview cards

The image shown when a link is shared. Posts without one use `assets/images/social-default.png`.

```
pip install pillow pyyaml
python3 tools/social_card.py _posts/2026-10-06-my-post.md --write   # one post, adds image: to the front matter
python3 tools/social_card.py --all --write                          # every post that lacks one
```

## Checks

`python3 tools/check_posts.py` validates front matter, filenames, tags and dates. The "Site checks" workflow runs it on every push,
builds the site, and checks every internal link, image and script. Once a week it also reports broken external links.

## Things to know

- The site is built by GitHub Pages' own Jekyll, so only plugins on its allowed list work: feed, sitemap, seo-tag, redirect-from and paginate are on.
- Search reads `/search.json`, which is generated from all posts. Nothing to maintain.
- The tag page is one page. A tag link opens it filtered to that tag.
- The home page shows 5 posts per page. Change `paginate` in `_config.yml`.
