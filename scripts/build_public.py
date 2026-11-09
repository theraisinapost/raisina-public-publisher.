#!/usr/bin/env python3
"""Build a noindex public-only staging index from approved canonical URLs.

No credentials, unpublished drafts, or private repository inputs are consumed.
This does not replace or deploy the production website.
"""
import argparse
from datetime import date
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ALLOWED_KEYS = frozenset({'title', 'url', 'date', 'section', 'standfirst', 'status'})
CANONICAL_HOST = 'theraisinapost.com'
ALLOWED_SECTIONS = frozenset({'Business', 'Governance', 'In depth', 'World', 'Exchange', 'India in 24 Hours', 'World in 24 Hours', 'Research'})


def validate_manifest(data):
    if not isinstance(data, dict) or set(data) != {'version', 'articles'} or data['version'] != 1:
        raise ValueError('Expected version 1 public-only article manifest')
    items = data['articles']
    if not isinstance(items, list) or len(items) > 1000:
        raise ValueError('Invalid public article list')
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != ALLOWED_KEYS:
            raise ValueError('Unexpected or missing public article fields')
        if item['status'] != 'published':
            raise ValueError('Refusing unpublished content')
        for field in ('title', 'url', 'date', 'section', 'standfirst'):
            value = item[field]
            if not isinstance(value, str) or not value.strip() or len(value) > (800 if field == 'standfirst' else 250):
                raise ValueError(f'Invalid {field}')
        if any(ord(c) < 32 for c in item['title'] + item['standfirst']):
            raise ValueError('Unexpected control character in public text')
        if item['section'] not in ALLOWED_SECTIONS:
            raise ValueError('Unapproved public section')
        try:
            date.fromisoformat(item['date'])
        except ValueError as exc:
            raise ValueError('Invalid publication date') from exc
        link = urlsplit(item['url'])
        if (link.scheme != 'https' or link.hostname != CANONICAL_HOST or link.username or
                link.password or link.port or link.query or link.fragment or
                not re.fullmatch(r'/[a-zA-Z0-9/_-]+/', link.path)):
            raise ValueError('Article URL must be a clean existing-domain canonical HTTPS URL')
        if item['url'] in seen:
            raise ValueError('Duplicate article URL')
        seen.add(item['url'])
    return sorted(items, key=lambda x: (x['date'], x['title']), reverse=True)


def render_page(items):
    cards = '\n'.join(
        '<article class="story">'
        f'<p class="meta">{escape(p["section"])} · {escape(p["date"])}</p>'
        f'<h2><a href="{escape(p["url"], quote=True)}" rel="noopener noreferrer">{escape(p["title"])}</a></h2>'
        f'<p class="summary">{escape(p["standfirst"])}</p>'
        '</article>'
        for p in items
    ) or '<p class="empty">No published records have been added to this preview.</p>'
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow,noarchive">'
        '<title>Public publishing preview — The Raisina Post</title>'
        '<meta name="description" content="Review-only index of previously published stories from The Raisina Post.">'
        '<link rel="stylesheet" href="styles.css">'
        '</head><body><div class="shell">'
        '<header><a class="brand" href="https://theraisinapost.com/">The Raisina Post</a>'
        '<span class="chip">Public preview · Not the production website</span></header>'
        '<main><p class="eyebrow">Publication mirror</p>'
        '<h1>Approved public stories.</h1>'
        '<p class="intro">This staging page links only to already published reporting. '
        'Editorial research, unpublished drafts, operational documents and credentials do not belong in this repository.</p>'
        f'<div class="stories">{cards}</div></main>'
        '<footer>For the full publication, visit <a href="https://theraisinapost.com/">theraisinapost.com</a>.</footer>'
        '</div></body></html>\n'
    )


def main(argv=None):
    p = argparse.ArgumentParser(description='Build safe public-only staging preview')
    p.add_argument('--manifest', type=Path, default=Path('content/published.json'))
    p.add_argument('--styles', type=Path, default=Path('site/styles.css'))
    p.add_argument('--output', type=Path, default=Path('dist'))
    a = p.parse_args(argv)
    items = validate_manifest(json.loads(a.manifest.read_text(encoding='utf-8')))
    styles = a.styles.read_text(encoding='utf-8')
    if not styles.strip():
        raise ValueError('Missing public preview CSS')
    a.output.mkdir(parents=True, exist_ok=True)
    (a.output / 'index.html').write_text(render_page(items), encoding='utf-8')
    (a.output / 'styles.css').write_text(styles, encoding='utf-8')
    (a.output / 'published.json').write_text(
        json.dumps({'version': 1, 'articles': items}, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8')
    (a.output / 'robots.txt').write_text('User-agent: *\nDisallow: /\n', encoding='utf-8')
    print(f'Validated {len(items)} public articles. Created noindex preview in {a.output}')


if __name__ == '__main__':
    main()
