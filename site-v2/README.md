# Mill-Miya / Selected Works — Taste Skill study

A **new, independently authored** static portfolio website for Mill-Miya, stored under `/site-v2/`. It does **not** overwrite the existing portfolio at `/`, change any source repository's Public/Private setting, or copy any private registry data.

## Purpose and design plan

- **Site type**: independent software + hardware maker portfolio / project index.
- **Audience**: collaborators, recruiters, makers and visitors who want to inspect shipped works.
- **Voice**: almost no marketing copy; English index/type labels; retain the original factual Japanese descriptions of each project.
- **Hierarchy**: opening masthead and original R mark; short filterable project index; two large featured spreads (Sorava and WallPipe AR); four border-separated archive entries; compact subject fields; contact via GitHub profile.
- **System**: one grid, fixed warm-paper / ink / single cobalt accent palette, zero gradients, no generic identical card grid, no third-party fonts, and no animations beyond a once-only entrance and subtle hover/scroll reveals.
- **Assets**: exact already-approved SVG R mark; authentic browser screenshots for five Web projects and the actual PySide6 University AI settings dialog. Captures are cropped for presentation but no application UI is invented.

## Taste Skill reference (read only)

- Source: <https://github.com/Leonxlnx/taste-skill>
- Materials reviewed: `skills/taste-skill/SKILL.md` (2.5.1, SHA `7dc7a9fed097364515581a28ec45ef955620eede`), `references/layout-v4.md`, `system.md`, `copy.md`, `copy-voice.md`, `motion.md`.
- Applied: real visuals and no synthetic UI, aligned content edges, deliberate visual hierarchy, restrained copy, coherent typography/spacing, quiet hover, accessible focus, reduced motion, responsive checks.
- Intentional adaptation: the long project index is allowed to grow naturally on mobile rather than force it into a fixed-height screen; this avoids clipping and collisions when six real projects are shown. This is **not** a claim of passing the external repository's full automatic gate.
- No files were copied from, pushed to, or modified in the Taste Skill author's repository.

## Publication boundary

The existing Public portfolio remains at <https://mill-miya.github.io/>. This new design has its own preview URL: <https://mill-miya.github.io/site-v2/> (after deployment). It carries `noindex` until the user elects to replace the main portfolio. If chosen as the new main page, synchronize the private `portfolio-control` publication template **before** changing the root page so future updates cannot restore the old design.

The existing private `portfolio-control` registry and original per-project repository visibility are untouched. Only the six already-public project names, factual descriptions and public demos appear; source code links do not appear. No logins, PHP, database, analytics or runtime tracking.

## Files

- `site-v2/index.html`: editorial page and project catalogue.
- `site-v2/style.css`: full design system, breakpoints, accessibility, motion controls.
- `site-v2/app.js`: client-side category filters, live results count and one-shot reveal effects.
- `site-v2/assets/`: user's original monogram, actual app captures, social-preview image.
- `tests/qa_site.py`: Chromium check at 12 widths, content/resource validation, accessibility basics and filter functionality. Browser fetches are blocked in the assistant runtime; test inlines the identical CSS, JS and local images for Chromium verification.

## Local use

Open `site-v2/index.html` in a standard browser, or serve `site-v2/` through any static HTTP server. No installation or build step.

For local automated validation:

```bash
python tests/qa_site.py
```

Requires Python, Playwright and Chromium. The test runs with resource inlining as described above. For a deployed-site smoke test, open the preview URL and check six image loads, four filters and all five demo links.
