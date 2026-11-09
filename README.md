# The Raisina Post — public content staging

This is a small, **public-only staging project**, not The Raisina Post's production website, newsroom or publishing infrastructure.

It contains a minimal preview of links to already published articles, basic static styling, and safety checks for public editorial metadata. It deliberately has **no automated production deployment**, no access to private editorial repositories, and no GitHub Actions schedules.

## Production website

Read the published work at [theraisinapost.com](https://theraisinapost.com/). Content and site updates here do not change that live website.

## Optional local preview

Run:

```bash
python3 scripts/safety_audit.py
python3 scripts/build_public.py --output dist
python3 -m http.server 8000 --directory dist
```

Then open `http://localhost:8000`. The preview marks itself `noindex` and contains links back to the published site. It is not designed for deployment to the production domain.

## Scope

Only include content already public on The Raisina Post. Do not add drafts, working notes, security credentials, reader data or internal operating documents.
