# UI audit — Taste Skill 2.5.1 (2026-11-17)

## Scope and provenance

- Project: Mill-Miya public portfolio (https://mill-miya.github.io/)
- Read-only source: [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill)
- Exact source revision reviewed: [f6b76575](https://github.com/Leonxlnx/taste-skill/tree/f6b76575f949707b4e3c37cd86cb44b0b98643e8)
- Source documents inspected: `README.md`, `skills/taste-skill/SKILL.md`, and `references/layout-v4.md`, `system.md`, `copy.md`, `copy-voice.md`, `cards.md`, `motion.md`, `moments.md`.
- No changes, pull requests or commits were made to the source owner's repository. No external kit code was copied into this project.

## Findings and corresponding implementation

| Verified Taste Skill guidance | Portfolio audit and action |
| --- | --- |
| One consistent system with equal left/right content edges and limited radius styles | Preserve the existing paper/ink/blue palette, R mark and typography; apply a shared 12-column editorial layout and subtle 2px corner radius |
| Avoid generic grids that obscure the real work; place real software subject first | Two main projects now have full-width visual/text editorial rows; the other four remain in a compact archive. Existing illustrations are explicitly labelled conceptual, not actual screenshots |
| Plain, concrete copy rather than stock promotional phrasing | Hero states that six public projects include Web, AR and local AI; practice notes cite Sorava, WallPipe AR, and University AI capabilities |
| Hero belongs on the opening desktop screen and should enter once | Reduced spacing at 1024–1440; measured hero ends at 768px (1024x768) and 900px (1440x900). One-shot CSS entrance respects reduced motion |
| Hover feedback, focus and phone touch size are essential | Filter buttons, main navigation and project links provide at least 44px vertical hit area and visible focus treatment |
| Real browser checks at desktop/tablet/mobile widths, including small screens | Rendered revised HTML/CSS/JS in Chromium at 1440, 1024, 820, 768, 390 and 320px: no horizontal overflow, no JavaScript page errors; category filtering works and clears irrelevant section labels |

## Functional boundaries

- All six public projects, their live/source links, and the exact R-logo SVG assets remain unchanged.
- Projects excluded by the private publication registry must never appear in generated public HTML.
- Category filtering remains client-side only; archive/featured headings update to match visible projects.
- No PHP, server, database, analytics, new runtime dependency or external font introduced.

## Limitations and explicit deviations

- This is **an application of documented design principles**, not a claim of passing the entire Taste Skill 2.5.1 automated kit/gate.
- The skill's original layout dealer, moments dealer, official consistency/layout/perf/gate scripts were not executed. Runtime HTTP navigation to localhost was blocked by the testing environment, so browser verification used Chromium `set_content` with the exact production HTML, CSS, JS and inline local logo assets.
- The six-work portfolio catalog is intentionally taller than the reference's one-section-per-screen rule. Shortening it to one screen would conceal real projects.
- Project visuals are explicitly illustrative. Fully strict “real product UI” compliance needs source screenshots from the actual apps, verified for freshness and permission.
- Mobile hero grows naturally beyond a single screen because it retains meaningful heading, explanation, controls and artwork rather than clipping content.
- Cross-browser and iPhone Safari hardware testing remain open.

## Follow-up QA

1. Verify the published GitHub Pages site on desktop and a real phone.
2. Check the header, footer, all filter categories, all links, and reduced-motion setting.
3. When trustworthy real app screenshots become available, replace illustrative project artwork without misrepresenting it.
