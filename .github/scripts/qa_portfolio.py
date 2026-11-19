#!/usr/bin/env python3
"""Visual and functional QA for the public static portfolio. No private data."""
from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "qa-evidence"
OUT.mkdir(exist_ok=True)
INDEX = (ROOT / "index.html").resolve().as_uri()
WIDTHS = [320, 360, 375, 390, 430, 480, 560, 640, 768, 820, 821, 900, 1024, 1280, 1440]
VISUALS = {
    "art-sorava", "art-wallpipe", "art-nova", "art-university",
    "art-assignment", "art-messe", "art-eqmount",
}

def fail(msg, width):
    raise AssertionError(f"{width}px: {msg}")

def start_listing(page, media, art, width):
    """Use the same center-entry path as phones, and hover on desktop."""
    if width <= 760:
        page.locator('.hero').evaluate("el => el.scrollIntoView({block:'start',behavior:'instant'})")
        page.wait_for_function("!document.querySelector('.project-card .is-playing')")
        art.evaluate("el => el.scrollIntoView({block:'center',behavior:'instant'})")
        page.wait_for_function("""selector =>
            document.querySelector(selector)?.classList.contains('is-playing')
        """, arg='.project-card .' + next(c for c in art.get_attribute('class').split() if c.startswith('art-')))
    else:
        media.hover()


def leave_listing(page, art, width):
    page.mouse.move(0, 0)
    if width <= 760:
        page.locator('.hero').evaluate("el => el.scrollIntoView({block:'start',behavior:'instant'})")
        page.wait_for_function("!document.querySelector('.project-card .is-playing')")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for width in WIDTHS:
        page = browser.new_page(
            viewport={"width": width, "height": 900 if width > 640 else 844},
            device_scale_factor=1,
            reduced_motion="reduce",
        )
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.goto(INDEX, wait_until="load", timeout=50000)
        page.wait_for_timeout(200)
        page.wait_for_timeout(180)
        metrics = page.evaluate("""() => {
          const r = n => { const x=n.getBoundingClientRect();return {
            x:x.x,y:x.y,w:x.width,h:x.height,l:x.left,t:x.top,r:x.right,b:x.bottom
          }};
          const elements = [...document.querySelectorAll('.project-card')];
          const sections = [...document.querySelectorAll('main section')];
          const visuals = [...document.querySelectorAll('.project-card .project-art')];
          const groups = [...document.querySelectorAll('.project-group-label')];
          const brand=document.querySelector('.site-header .brand');
          const navigation=document.querySelector('.site-header .site-nav');
          const head=document.querySelector('.hero h1');
          const clone=document.body.cloneNode(true);
          clone.querySelectorAll('.project-card').forEach(n=>n.remove());
          const outside=clone.textContent || '';
          return {
            scrollWidth: document.documentElement.scrollWidth,
            innerWidth: innerWidth,
            cards:elements.map(n=>({box:r(n),hidden:n.hidden})),
            groups:groups.map(n=>({box:r(n),hidden:n.hidden})),
            sections:sections.map(n=>({box:r(n),id:n.id || n.className})),
            visuals:visuals.map(n=>({classes:[...n.classList],box:r(n),hasChild:n.children.length>0})),
            logoOverlap:r(brand).r > r(navigation).l + 1,
            h1Rect:r(head),
            hasJPOutside:/[\u3040-\u30ff\u3400-\u9fff]/.test(outside),
            sourceLinks:[...document.querySelectorAll('a')].filter(n=>/Source( code)?\b/.test(n.textContent||'')).length,
            emptyAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(n=>{
              const id=n.getAttribute('href').slice(1);
              return !document.getElementById(id);
            }).map(n=>n.getAttribute('href')),
          };
        }""")
        if errors: fail("JavaScript error: "+repr(errors), width)
        # The final punctuation in the hero is an actual keyboard/touch
        # button. Cycling changes the global accent, not project identity colors.
        accent=page.locator("#accent-cycle")
        if not accent.is_visible() or accent.get_attribute("type") != "button":
            fail("hero punctuation is not an accessible accent switch", width)
        if width in (390,1440):
            original_project_color=page.locator('.project-card[data-project="01"]').evaluate(
                "el => getComputedStyle(el).getPropertyValue('--project-accent').trim()"
            )
            for next_color in ("sage","copper","violet"):
                accent.click()
                current_color=page.evaluate("() => document.documentElement.dataset.accentChoice")
                if current_color != next_color:
                    fail("accent color did not advance to "+next_color, width)
                actual=accent.evaluate("el => getComputedStyle(el).color")
                expected=page.evaluate("""() => {
                    const checker=document.createElement('i');
                    checker.style.color='var(--electric)';
                    document.body.appendChild(checker);
                    const color=getComputedStyle(checker).color;
                    checker.remove();
                    return color;
                }""")
                if actual != expected:
                    fail("hero accent is not tied to site-wide palette", width)
                if page.locator('.project-card[data-project="01"]').evaluate(
                    "el => getComputedStyle(el).getPropertyValue('--project-accent').trim()"
                ) != original_project_color:
                    fail("global accent changed a project's identity color", width)
            page.reload(wait_until="load")
            if page.evaluate("() => document.documentElement.dataset.accentChoice") != "violet":
                fail("accent preference did not survive reload", width)
            accent=page.locator("#accent-cycle")
            accent.click()
            if page.evaluate("() => document.documentElement.dataset.accentChoice || 'blue'") != "blue":
                fail("accent switch did not return to the original sky blue", width)
            if page.evaluate("() => localStorage.getItem('mill-miya.accent')") is not None:
                fail("original accent should clear the persisted override", width)
        if metrics["scrollWidth"] > metrics["innerWidth"] + 1:
            fail("horizontal overflow: "+json.dumps(metrics["scrollWidth"]), width)
        if metrics["logoOverlap"]: fail("header branding overlaps navigation", width)
        if metrics["hasJPOutside"]: fail("unwanted Japanese text outside work cards", width)
        if metrics["sourceLinks"]: fail("source-code link was reintroduced", width)
        if metrics["emptyAnchors"]: fail("broken internal anchors: "+repr(metrics["emptyAnchors"]), width)
        # Chapter numbering is consecutive; counts are independent and filter-aware.
        chapter_labels=[
            ("featured-group-label", "01 / FEATURED WORK", "02 PROJECTS"),
            ("archive-group-label", "02 / PROJECT ARCHIVE", "04 PROJECTS"),
            ("physical-group-label", "03 / PHYSICAL WORK", "01 PROJECT")
        ]
        for section_id, heading, project_count in chapter_labels:
            label=page.locator("#"+section_id)
            if label.locator("span").first.inner_text()!=heading:
                fail("Incorrect project chapter sequence: "+section_id, width)
            if label.locator("[data-group-count]").inner_text()!=project_count:
                fail("Incorrect initial project count: "+section_id, width)
        if len(metrics["cards"]) != 7 or len(metrics["visuals"]) != 7:
            fail("lost project card or concept artwork", width)
        visual_classes=set()
        for visual in metrics["visuals"]:
            if not visual["hasChild"] or visual["box"]["w"] < 100 or visual["box"]["h"] < 100:
                fail("missing or empty concept artwork: "+str(visual), width)
            if "real-shot" in visual["classes"]:
                fail("actual screenshot visual unexpectedly restored", width)
            visual_classes.update(visual["classes"])
        if not VISUALS.issubset(visual_classes):
            fail("unexpected artwork classes: "+repr(visual_classes), width)
        boxes=[c["box"] for c in metrics["cards"]]
        for i, a in enumerate(boxes):
            for j, b in enumerate(boxes):
                if j<=i: continue
                intersect_x=min(a["r"],b["r"])-max(a["l"],b["l"])
                intersect_y=min(a["b"],b["b"])-max(a["t"],b["t"])
                if intersect_x>3 and intersect_y>3:
                    fail(f"work cards {i+1} and {j+1} overlap", width)
        for group in metrics["groups"]:
            if group["hidden"]: continue
            g=group["box"]
            for i, a in enumerate(boxes):
                ix=min(g["r"],a["r"])-max(g["l"],a["l"])
                iy=min(g["b"],a["b"])-max(g["t"],a["t"])
                if ix>3 and iy>3:
                    fail(f"group heading overlaps card {i+1}", width)
        # The design-study caption must sit above the iframe (z:2) and 3D canvas (z:3).
        # Otherwise it disappears except while the iframe is hidden for 3D playback.
        caption=page.locator('.hero-visual-top')
        if not caption.is_visible() or 'R / DESIGN STUDY' not in caption.inner_text():
            fail("R logo design-study caption missing", width)
        caption_z=caption.evaluate("el => Number.parseInt(getComputedStyle(el).zIndex,10)")
        logo_z=page.locator('#hero-logo-frame').evaluate(
            "el => Number.parseInt(getComputedStyle(el).zIndex,10)"
        )
        canvas_z=page.locator('#hero-logo-spin-canvas').evaluate(
            "el => Number.parseInt(getComputedStyle(el).zIndex,10)"
        )
        if not caption_z > max(logo_z,canvas_z):
            fail("design-study caption is hidden behind the logo renderer", width)
        # The full-length construction centerline is already drawn by segment 1.
        # Segment 2 must draw only the rightward part, without re-tracing the vertical.
        center_guide=page.frame_locator('#hero-logo-frame').locator('[data-segment="2"]')
        no_duplicate_center=center_guide.evaluate("""el => {
          const d=el.getAttribute('d');
          const start=el.getPointAtLength(0);
          const end=el.getPointAtLength(el.getTotalLength());
          return (d.match(/M/gi)||[]).length===1 &&
            Math.abs(el.getTotalLength()-280)<0.05 &&
            Math.abs(start.x-627)<0.05 && Math.abs(start.y-627)<0.05 &&
            Math.abs(end.x-907)<0.05 && Math.abs(end.y-627)<0.05;
        }""")
        if not no_duplicate_center:
            fail("central R logo guide duplicates the vertical centerline", width)
        if not page.locator("#hero-logo-replay").is_visible():
            fail("reduced-motion preference must retain explicit hero replay", width)
        if width in (390, 1440):
            theme = page.locator('#theme-choice')
            motion = page.locator('#motion-choice')
            theme.select_option('dark')
            # Color-scheme and light-dark() can settle on the next rendering frame.
            page.wait_for_function("getComputedStyle(document.body).backgroundColor === 'rgb(22, 28, 31)'", timeout=3000)
            if page.locator('body').evaluate("(el) => getComputedStyle(el).backgroundColor") != "rgb(22, 28, 31)":
                fail("dark theme did not reach the page surface", width)
            if page.locator('.hero-logo-poster').evaluate("(el) => getComputedStyle(el).fill") != "rgb(0, 0, 0)":
                fail("dark theme must use the black logo poster", width)
            logo_ground = page.frame_locator('#hero-logo-frame').locator('#guide-svg > rect')
            logo_ground_white = logo_ground.evaluate("""async el => {
              for (let i = 0; i < 60; i++) {
                if (getComputedStyle(el).fill === 'rgb(255, 255, 255)') return true;
                await new Promise(resolve => setTimeout(resolve, 50));
              }
              return false;
            }""")
            if not logo_ground_white:
                fail("dark theme must use a white animation background", width)
            first = page.locator('.project-card[data-project="01"]')
            card_accent = first.locator('.project-year').evaluate("(el) => getComputedStyle(el).color")
            if card_accent == page.locator('.project-card[data-project="02"] .project-year').evaluate(
                "(el) => getComputedStyle(el).color"
            ):
                fail("different projects share their identity color", width)
            first.locator('.sheet-link').click()
            if page.locator('#sheet-kind').evaluate("(el) => getComputedStyle(el).color") != card_accent:
                fail("card and detail identity colors differ", width)
            page.keyboard.press("Escape")
            page.emulate_media(reduced_motion="no-preference")
            motion.select_option('reduce')
            if not page.locator("#hero-logo-replay").is_visible() or not page.locator(".hero-logo-poster").is_visible():
                fail("site motion preference does not show a static hero mark", width)
            first.locator('.sheet-link').click()
            if not page.locator(".sheet-motion-play").is_visible():
                fail("site reduced motion must retain explicit detail replay", width)
            if page.locator("#sheet-visual .is-playing").count():
                fail("site reduce unexpectedly autoplays the sheet", width)
            page.locator(".sheet-motion-play").click()
            page.wait_for_function("document.querySelector('#sheet-visual .art-sorava')?.classList.contains('is-playing')")
            if motion.input_value() != 'full' or page.evaluate("localStorage.getItem('mill-miya.motion')") != 'full':
                fail("detail REPLAY did not persist full motion", width)
            if page.locator("#sheet-visual .sorava-guest-received").evaluate("el => getComputedStyle(el).animationName") != 'sorava-guest-receive':
                fail("explicit detail replay did not start CSS animation", width)
            page.keyboard.press("Escape")
            motion.select_option('system')
            page.emulate_media(reduced_motion="reduce")
            page.locator('#hero-logo-replay').click()
            page.wait_for_function("document.documentElement.dataset.motionChoice === 'full'")
            logo = page.frame_locator('#hero-logo-frame').locator('body')
            # postMessage reaches the sandboxed iframe asynchronously.
            # Verify its actual playback status rather than assuming a single tick.
            logo_running = logo.evaluate("""async () => {
              for (let i = 0; i < 60; i++) {
                if (window.getLogoStatus().running) return true;
                await new Promise(resolve => setTimeout(resolve, 50));
              }
              return false;
            }""")
            if not logo_running:
                fail("hero REPLAY did not enable iframe playback under OS reduce", width)
            if motion.input_value() != 'full' or page.evaluate("localStorage.getItem('mill-miya.motion')") != 'full':
                fail("hero REPLAY did not persist full motion", width)
            page.reload(wait_until='load')
            if motion.input_value() != 'full':
                fail("full motion did not survive reload", width)
            motion.select_option('system')
            if page.evaluate("localStorage.getItem('mill-miya.motion')") is not None:
                fail("System must clear the stored motion override", width)
            theme.select_option('system')
            page.emulate_media(reduced_motion="reduce")
        # 3D spin is opt-in after the exact 2D logo reaches its completed state.
        if width in (390, 1440):
            page.frame_locator('#hero-logo-frame').locator('body').evaluate(
                "() => window.setLogoTime(window.getLogoStatus().total)"
            )
            page.wait_for_function(
                "document.querySelector('.hero-visual').classList.contains('is-logo-complete')"
            )
            trigger=page.locator('#hero-logo-spin')
            if not trigger.is_visible():
                fail("finished R logo is not touch/click accessible", width)
            can_webgl=page.evaluate(
                "() => !!document.createElement('canvas').getContext('webgl2')"
            )
            trigger.click()
            if can_webgl:
                page.wait_for_function(
                    "document.querySelector('.hero-visual').classList.contains('is-logo-spinning')"
                )
                if page.locator('#hero-logo-spin-canvas').evaluate("el => el.width == 0"):
                    fail("3D logo canvas did not render", width)
                page.wait_for_function(
                    "!document.querySelector('.hero-visual').classList.contains('is-logo-spinning')",
                    timeout=6000
                )
                if not trigger.is_visible():
                    fail("3D spin failed to restore the original logo", width)
            elif page.locator('.hero-logo-frame').count() != 1:
                fail("WebGL fallback lost the original logo", width)
        if width in (320,390,820,1024,1440):
            page.screenshot(path=str(OUT/f"portfolio_{width}.png"),full_page=True,animations="disabled")
        # Verify existing category filtering on narrow and full desktop.
        if width in (320, 390, 820, 1440):
            page.locator('button[data-filter="ai"]').click()
            if page.locator('.project-card:visible').count()!=2:
                fail("AI filter not preserving its two projects", width)
            if page.locator('#archive-group-label [data-group-count]').inner_text()!="02 PROJECTS":
                fail("Archive project count must update under AI filter", width)
            page.locator('button[data-filter="all"]').click()
            if page.locator('.project-card:visible').count()!=7:
                fail("All filter does not restore all seven projects", width)
            if page.locator('#visible-count').inner_text().strip()!="07":
                fail("filter counter incorrect", width)
            page.locator('button[data-filter="hardware"]').click()
            if page.locator('.project-card:visible').count()!=1:
                fail("Hardware filter should show one physical work", width)
            if not page.locator('#physical-group-label').is_visible():
                fail("Physical work label hidden by Hardware filter", width)
            if page.get_by_role("status").inner_text().strip() != "01 PROJECT":
                fail("single-project result is not announced with a singular unit", width)
            if page.locator('#archive-group-label').is_visible():
                fail("Software archive header visible without software cards", width)
            page.locator('button[data-filter="engineering"]').click()
            if page.locator('.project-card:visible').count()!=3:
                fail("Engineering filter should show three engineering works", width)
            page.locator('button[data-filter="ai"]').click()
            if page.locator('#physical-group-label').is_visible():
                fail("Physical work header did not follow active filter", width)
            page.locator('button[data-filter="all"]').click()
        # Two works remain visible but may not open a sheet or a live demo.
        for project_number, art_class, url_fragment in (
            ("05", "art-assignment", "assignment-checker/"),
            ("06", "art-messe", "suwa-messe-2026/"),
        ):
            locked = page.locator(f'.project-card[data-project="{project_number}"]')
            if locked.count()!=1 or locked.locator(f'.project-art.{art_class}').count()!=1:
                fail("locked work missing artwork", width)
            if locked.locator(".project-lock-mark svg").count()!=1:
                fail("locked work missing lock visual", width)
            if locked.locator("[data-open-sheet], a[href]").count()!=0:
                fail("locked work still has actionable controls", width)
            if locked.locator(".project-locked-note").inner_text().strip()!="PRIVATE PREVIEW":
                fail("locked work availability note missing", width)
            if page.locator(f'a[href*="{url_fragment}"]').count()!=0:
                fail("locked work demo link leaked", width)
            bounds = locked.locator(".project-art").bounding_box()
            mark = locked.locator(".project-lock-mark").bounding_box()
            icon = locked.locator(".project-lock-mark svg").bounding_box()
            if not bounds or not mark or not icon:
                fail("lock markup invisible", width)
            if icon["width"] < 40 or icon["height"] < 40:
                fail("lock icon unexpectedly small", width)
            if abs(mark["x"] + mark["width"] / 2 - (bounds["x"] + bounds["width"] / 2)) > 5:
                fail("lock mark not horizontally centered", width)
            if abs(mark["y"] + mark["height"] / 2 - (bounds["y"] + bounds["height"] / 2)) > 5:
                fail("lock mark not vertically centered", width)
            if mark["width"] > bounds["width"] + 1 or mark["height"] > bounds["height"] + 1:
                fail("lock mark overflows artwork", width)
        if page.locator('.project-card [data-open-sheet]').count()!=15:
            fail("expected five sheet-enabled works", width)
        if page.locator(".project-card .project-links a[href]").count()!=3:
            fail("expected three public live site links", width)
        if page.locator("a[href*='assignment-checker/'], a[href*='suwa-messe-2026/']").count()!=0:
            fail("locked public demo URLs leaked into the page", width)
        # WallPipe AR illustration: 2 elbow turns, one round four-spoke wheel,
        # concealed internal water and a semi-transparent front cover.
        wallpipe = page.locator('.project-card[data-project="02"] .pipe-drawing')
        if wallpipe.count()!=1:
            fail("WallPipe AR illustration missing", width)
        route="M98 290H170A35 35 0 0 0 205 255V208A35 35 0 0 1 240 173H523"
        if wallpipe.locator(f'path.wp-pipe-outline[d="{route}"]').count()!=1:
            fail("WallPipe pipe must have two constant-radius 35px quarter-circle elbows", width)
        for cls in (".wp-pipe-back", ".wp-pipe-bore", ".wp-water-core", ".wp-water-stream",
                    ".wp-pipe-front", ".wp-flow-cutaway", ".wp-flow-trace"):
            if wallpipe.locator(cls).get_attribute("d")!=route:
                fail("WallPipe water and metal layers must follow identical rounded pipe centerline: "+cls, width)
        if wallpipe.locator(".wp-pipe-ends, .wp-pipe-mouth").count():
            fail("Old circular end plates must not occlude pipe ends", width)
        if wallpipe.locator(".wp-pipe-assembly").get_attribute("stroke-linecap")!="butt":
            fail("Pipe sections should terminate cleanly without round caps", width)
        if wallpipe.locator(".wp-mouth-in path").count()!=3 or wallpipe.locator(".wp-mouth-out path").count()!=3:
            fail("Both pipe mouths must flare without oval end caps", width)
        if wallpipe.locator(".wp-mouth-in ellipse, .wp-mouth-out ellipse").count():
            fail("Flared pipe mouths must not be capped by ellipse faces", width)
        if wallpipe.locator(".wp-mouth-in").evaluate("(el) => el.getBBox().height")<77 or \
                wallpipe.locator(".wp-mouth-out").evaluate("(el) => el.getBBox().height")<77:
            fail("Flared mouths must be wider than the 52px nominal tube", width)
        if wallpipe.locator('.wp-wheel-spin circle[fill="#e2ad5c"], .wp-wheel-spin circle[stroke="#ffe7b4"]').count():
            fail("Orange wheel position marker must be removed", width)
        if wallpipe.locator(".wp-wheel-hub").count()!=1 or wallpipe.locator(".wp-wheel-hub circle").count()!=2:
            fail("Wheel hub must remain stationary outside rotating spokes", width)
        wheel_placement=wallpipe.locator(".wp-wheel-tilt").get_attribute("transform")
        if wheel_placement!="translate(364 173) scale(.70 .70)":
            fail("Handwheel is not centered over the marked valve housing: "+str(wheel_placement), width)
        if wallpipe.locator('.wp-valve path[d="M360 132V94"]').count():
            fail("Obsolete elevated handwheel stem remains", width)
        if wallpipe.locator(".wp-scene").evaluate(
                "(el) => getComputedStyle(el).transform")!="none":
            fail("WallPipe scene must remain rigid without camera sway", width)
        if wallpipe.locator("#wp-pipe-template").count()!=1:
            fail("Reusable pipe assembly geometry template is missing", width)
        if wallpipe.locator("#wp-pipe-template").get_attribute("mask"):
            fail("Old growing stroke mask must no longer hide the physical parts", width)
        if wallpipe.locator("#wp-pipe-template .wp-water-core").count():
            fail("The rigid steel template incorrectly contains blue water", width)
        if wallpipe.locator(".wp-pipe-effects").count()!=1:
            fail("Dynamic water must be drawn as a single live overlay outside the steel clones", width)
        if wallpipe.locator(".wp-pipe-effects").evaluate(
                "(el) => el.closest('defs') !== null"):
            fail("Dynamic water cannot animate correctly while inside SVG defs", width)
        for water in (".wp-water-core",".wp-water-stream",".wp-flow-trace",".wp-upstream-water"):
            if wallpipe.locator(".wp-pipe-effects "+water).count()!=1:
                fail("The animated water is missing from its live rendering group: "+water, width)
        for name,clip in (("left","wp-part-left-clip"),
                          ("right","wp-part-right-clip")):
            part=wallpipe.locator(".wp-part-"+name)
            if part.count()!=1 or part.get_attribute("clip-path")!="url(#"+clip+")":
                fail("Rigid assembled pipe section is missing: "+name, width)
            if part.locator("use").get_attribute("href")!="#wp-pipe-template":
                fail("All rigid pipe parts must reuse the same accurate geometry", width)
        # The steel hidden by the handwheel is a continuous inlet/outlet,
        # never a third piece that moves with the valve.
        if wallpipe.locator(".wp-part-center, #wp-part-center-clip").count():
            fail("Pipe beneath the wheel must not arrive together with the valve", width)
        left_rect=wallpipe.locator("#wp-part-left-clip rect")
        right_rect=wallpipe.locator("#wp-part-right-clip rect")
        if (left_rect.get_attribute("x")!="55" or left_rect.get_attribute("width")!="309" or
                right_rect.get_attribute("x")!="364" or right_rect.get_attribute("width")!="219"):
            fail("Left and right steel modules must meet under the valve hub", width)
        if wallpipe.locator(".wp-coupler-locks .wp-lock-left").count()!=1 or \
                wallpipe.locator(".wp-coupler-locks .wp-lock-right").count()!=1:
            fail("Subtle fixed joint collars are missing", width)
        if wallpipe.locator(".wp-valve").evaluate(
                "(el) => el.parentElement.classList.contains('wp-pipe-geometry')"):
            fail("The valve must dock independently, not ride with the moving pipes", width)
        for old in (".wp-build-left",".wp-build-right",".wp-build-middle"):
            if wallpipe.locator(old).count():
                fail("Old stretching reveal construction survived: "+old, width)

        if wallpipe.locator("mask#wp-flow-reveal").count()!=1:
            fail("Valve-originated flow mask is missing", width)
        for cls in (".wp-water-core", ".wp-water-stream", ".wp-flow-cutaway", ".wp-flow-trace"):
            if wallpipe.locator(cls).get_attribute("mask")!="url(#wp-flow-reveal)":
                fail("Every water or water-window layer must use the flow-front mask: "+cls, width)
        if wallpipe.locator(".wp-upstream-water").count()!=1:
            fail("Continuously flowing upstream section is missing", width)
        if wallpipe.locator(".wp-upstream-stream").get_attribute("stroke-dasharray")!= \
                wallpipe.locator(".wp-flow-trace").get_attribute("stroke-dasharray"):
            fail("Moving water dashes should have matching cadence on both sides", width)
        # SVG drawing order is essential: a color match alone is insufficient.
        # Drawing the dark right-hand cutaway on top of its cyan core hides the
        # bright water (the earlier regression). Paint the core above the
        # cutaway and below the moving highlight, as on the left side.
        water_layers=wallpipe.evaluate("""svg=>{
          const nodes=['.wp-flow-cutaway','.wp-water-core','.wp-flow-trace',
                       '.wp-upstream-window','.wp-upstream-core','.wp-upstream-stream']
            .map(s=>svg.querySelector(s));
          if(nodes.some(x=>!x)) return null;
          const root=svg.querySelector('.wp-pipe-effects');
          return nodes.map(el=>{
            const ordered=[...root.querySelectorAll('*')];
            return ordered.indexOf(el);
          });
        }""")
        if not water_layers or not (water_layers[0]<water_layers[1]<water_layers[2]):
            fail("Right-side cyan water must paint on top of its dark cutaway and below water stripes", width)
        if not (water_layers[3]<water_layers[4]<water_layers[5]):
            fail("Upstream water layer order has changed", width)
        for left, right in (
            (".wp-upstream-window",".wp-flow-cutaway"),
            (".wp-upstream-core",".wp-water-core"),
            (".wp-upstream-stream",".wp-water-stream"),
            (".wp-upstream-stream",".wp-flow-trace")
        ):
            l=wallpipe.locator(left)
            r=wallpipe.locator(right)
            for attr in ("stroke","stroke-width"):
                if l.get_attribute(attr)!=r.get_attribute(attr):
                    fail("Right water color and thickness must match left: "+left+" "+right+" "+attr, width)
            if left==".wp-upstream-core" and l.get_attribute("stroke-opacity")!=r.get_attribute("stroke-opacity"):
                fail("Right-side core opacity must match the left", width)
        for cls in (".wp-upstream-window", ".wp-upstream-core", ".wp-upstream-stream"):
            if wallpipe.locator(cls).count()!=1:
                fail("Upstream flow layer is missing: "+cls, width)
        if wallpipe.locator(".wp-valve-housing").count()!=1:
            fail("Cast mechanical valve housing is missing", width)
        if wallpipe.locator('.wp-valve rect[x="329"][width="65"]').count():
            fail("Obsolete square valve box remains", width)
        if wallpipe.locator('.wp-wheel-spin > circle:first-child').get_attribute("fill")!="none":
            fail("The four-spoke wheel must have open spaces, not a solid disk", width)
        if any(wallpipe.locator(cls).count()!=1 for cls in
               (".wp-pipe-back", ".wp-pipe-bore", ".wp-water-core", ".wp-water-stream",
                ".wp-pipe-front", ".wp-flow-cutaway", ".wp-flow-trace", ".wp-wheel-spin", ".wp-status-open", ".wp-status-closed")):
            fail("WallPipe cutaway/flow/handwheel layers missing", width)
        if wallpipe.locator('.wp-wheel-spin path[d="M0-40V40M-40 0H40"]').count()!=2:
            fail("WallPipe handwheel must have four radial spokes", width)
        if wallpipe.locator(".wp-pipe-front").evaluate(
                "(el) => parseFloat(getComputedStyle(el).opacity)")>.45:
            fail("WallPipe static artwork must reveal the flow on small cards", width)
        if wallpipe.locator(".wp-water-core").evaluate(
                "(el) => parseFloat(getComputedStyle(el).opacity)")<.9:
            fail("WallPipe static water flow must be visible", width)
        if width in (390,1440):
            page.emulate_media(reduced_motion="no-preference")
            pipe_media=page.locator('.project-card[data-project="02"] .project-media')
            pipe_art=pipe_media.locator(".art-wallpipe")
            start_listing(page, pipe_media, pipe_art, width)
            if ("is-playing" if width <= 760 else "is-hovering") not in (pipe_art.get_attribute("class") or ""):
                fail("WallPipe listing did not start playback on hover", width)
            # Source-level opacity checks do not catch clone-paint regressions.
            # Confirm the *visible* live water group begins fully concealed.
            early_water=pipe_art.evaluate("""art => {
              const el=art.querySelector('.wp-upstream-water');
              const an=el?.getAnimations().find(a=>a.animationName==='wp-upstream-reveal');
              if(!an) return null;
              an.currentTime=200;
              return parseFloat(getComputedStyle(el).opacity);
            }""")
            if early_water is None or early_water>.02:
                fail("WallPipe must not reveal blue water before the metal turns translucent", width)
            if pipe_art.locator(".wp-scene").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="none":
                fail("WallPipe no longer allows perspective wobbling", width)
            if pipe_art.locator(".wp-wheel-spin").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="wp-wheel-open":
                fail("WallPipe handwheel did not animate on hover", width)
            pivot_deviation=pipe_art.evaluate("""art => {
              const wheel=art.querySelector('.wp-wheel-spin');
              const hub=art.querySelector('.wp-wheel-hub');
              const spinning=wheel.getAnimations().find(a=>a.animationName==='wp-wheel-open');
              if(!spinning) return Infinity;
              const center=node=>{
                const r=node.getBoundingClientRect();
                return {x:r.x+r.width/2,y:r.y+r.height/2};
              };
              let max=0;
              for(const time of [0,550,1575,2475,3375,4450]){
                spinning.currentTime=time;
                const a=center(wheel),b=center(hub);
                max=Math.max(max,Math.hypot(a.x-b.x,a.y-b.y));
              }
              return max;
            }""")
            if pivot_deviation>.75:
                fail("WallPipe wheel center drifts during rotation: "+str(pivot_deviation), width)
            preview_seconds=pipe_art.locator(".wp-wheel-spin").evaluate(
                "(el) => parseFloat(getComputedStyle(el).animationDuration)")
            if pipe_art.locator(".wp-wheel-spin").evaluate(
                    "(el) => getComputedStyle(el).animationIterationCount")!="1":
                fail("WallPipe hover wheel must play only once", width)
            if abs(preview_seconds-4.5)>.02:
                fail("WallPipe hover must run exactly 1.6x (4.5s)", width)
            if pipe_art.locator(".wp-upstream-stream").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="wp-upstream-travel":
                fail("Left-side water must move immediately upon preview start", width)
            leave_listing(page, pipe_art, width)
            if any(c in (pipe_art.get_attribute("class") or "") for c in ("is-hovering", "is-playing")):
                fail("WallPipe hover did not reset", width)
            page.locator('.project-card[data-project="02"] .sheet-link').click()
            pipe_sheet=page.locator("#sheet-visual .art-wallpipe")
            page.wait_for_function("""() =>
                document.querySelector('#sheet-visual .art-wallpipe')?.classList.contains('is-playing')
            """,timeout=1500)
            if not page.locator(".sheet-motion-play").is_visible():
                fail("WallPipe replay control missing in detail sheet", width)
            duration=pipe_sheet.locator(".wp-wheel-spin").evaluate(
                "(el) => parseFloat(getComputedStyle(el).animationDuration)")
            if abs(duration-7.2)>.02:
                fail("WallPipe sheet must play at normal 7.2s", width)
            if pipe_sheet.locator(".wp-wheel-spin").evaluate(
                    "(el) => getComputedStyle(el).animationIterationCount")!="1":
                fail("WallPipe sheet motion must play only once", width)
            if pipe_sheet.locator(".wp-flow-trace").evaluate(
                    "(el) => getComputedStyle(el).animationIterationCount")!="1, 1":
                fail("WallPipe water travel must play only once", width)
            if page.locator(".sheet-motion-play").inner_text().strip()!="REPLAY":
                fail("WallPipe one-shot replay button should be labelled REPLAY", width)
            phases=pipe_sheet.evaluate("""art => {
              const find=sel=>art.querySelector(sel);
              const els=['.wp-pipe-assembly','.wp-wheel-spin','.wp-pipe-front',
                         '.wp-water-core','.wp-water-stream','.wp-status-open',
                         '.wp-status-closed'].map(find);
              const animations=els.map(el=>el.getAnimations().filter(a=>a.animationName));
              const frame=t=>{
                animations.forEach(items=>items.forEach(a=>{a.currentTime=t}));
                return {
                  assembly:parseFloat(getComputedStyle(els[0]).opacity),
                  wheel:getComputedStyle(els[1]).transform,
                  front:parseFloat(getComputedStyle(els[2]).opacity),
                  water:parseFloat(getComputedStyle(els[3]).opacity),
                  stream:parseFloat(getComputedStyle(els[4]).opacity),
                  open:parseFloat(getComputedStyle(els[5]).opacity),
                  closed:parseFloat(getComputedStyle(els[6]).opacity)
                };
              };
              return {begin:frame(0),closed:frame(2800),
                      ending:frame(7050),held:frame(7550)};
            }""")
            if phases["begin"]["water"]>.05:
                fail("WallPipe water must remain hidden before the valve opens: "+str(phases), width)
            if phases["closed"]["closed"]<.95 or phases["closed"]["front"]<.9:
                fail("WallPipe must keep pipe opaque before valve opens: "+str(phases), width)
            if (phases["ending"]["water"]<.9 or phases["ending"]["stream"]<.9 or
                    phases["ending"]["front"]>.4 or phases["ending"]["open"]<.95 or
                    phases["ending"]["closed"]>.05):
                fail("WallPipe final cutaway must reveal water inside after valve opens: "+str(phases), width)
            if (phases["held"]["assembly"]<.9 or phases["held"]["water"]<.9 or
                    phases["held"]["front"]>.4 or phases["held"]["open"]<.95):
                fail("WallPipe must hold final opened state rather than repeat: "+str(phases), width)
            # Restart explicitly before sampling more WAAPI timelines:
            # advancing the earlier final-state assertion may have fired
            # animationend and removed is-playing in a real browser.
            page.locator(".sheet-motion-play").click()
            page.wait_for_function("""() =>
                document.querySelector('#sheet-visual .art-wallpipe')?.classList.contains('is-playing')
            """, timeout=1500)
            # The steel pipes, valve and fittings are already assembled.
            # They must stay visible, stationary and free of docking animations.
            modules=pipe_sheet.evaluate("""art=>{
              const selectors=['.wp-part-left','.wp-valve','.wp-part-right',
                               '.wp-lock-left','.wp-lock-right'];
              const els=selectors.map(sel=>art.querySelector(sel));
              if(els.some(el=>!el)) return null;
              const wheel=art.querySelector('.wp-wheel-spin');
              const wheelAnimation=wheel.getAnimations().find(a=>a.animationName==='wp-wheel-open');
              if(!wheelAnimation) return null;
              const snap=t=>{
                wheelAnimation.currentTime=t;
                return els.map(el=>{
                  const cs=getComputedStyle(el);
                  const transform=new DOMMatrix(cs.transform==='none'?undefined:cs.transform);
                  return {opacity:parseFloat(cs.opacity),x:transform.m41,y:transform.m42,
                          animation:cs.animationName};
                });
              };
              return {start:snap(0),turning:snap(1500),opened:snap(5000)};
            }""")
            if not modules:
                fail("Fixed WallPipe mechanical assembly is missing", width)
            for phase,positions in modules.items():
                if any(p["opacity"]<.7 or abs(p["x"])>.1 or abs(p["y"])>.1
                       or p["animation"]!="none" for p in positions):
                    fail("WallPipe pipes, valve and collars must remain fixed throughout "+phase+": "+str(modules), width)
            # Upstream water is physically in motion before the valve opens,
            # but must remain invisible until the front metal becomes translucent.
            # The downstream moving dashes then travel at the same physical SVG
            # speed (not the same total dash offset) as the upstream dashes.
            front=pipe_sheet.evaluate("""art => {
              const l=art.querySelector('.wp-reveal-left');
              const r=art.querySelector('.wp-reveal-right');
              const upstream=art.querySelector('.wp-upstream-water');
              const u=art.querySelector('.wp-upstream-stream');
              const downstream=art.querySelector('.wp-flow-trace');
              const ra=r.getAnimations().find(a=>a.animationName==='wp-propagate-right');
              const ga=upstream.getAnimations().find(a=>a.animationName==='wp-upstream-reveal');
              const ua=u.getAnimations().find(a=>a.animationName==='wp-upstream-travel');
              const da=downstream.getAnimations().find(a=>a.animationName==='wp-water-move');
              if(!ra || !ga || !ua || !da) return null;
              const snap=t=>{
                for(const a of [ra,ga,ua,da]) a.currentTime=t;
                return {
                  upstreamLength:parseFloat(getComputedStyle(l).strokeDasharray),
                  rightLength:parseFloat(getComputedStyle(r).strokeDasharray),
                  upOffset:parseFloat(getComputedStyle(u).strokeDashoffset),
                  upGroupOpacity:parseFloat(getComputedStyle(upstream).opacity),
                  downOffset:parseFloat(getComputedStyle(downstream).strokeDashoffset)
                };
              };
              return {initial:snap(0),preopen:snap(2200),closed:snap(2800),
                      transition:snap(3600),opening:snap(3450),
                      halfway:snap(4200),speedStart:snap(4500),
                      speedEnd:snap(6000),finished:snap(7050)};
            }""")
            if not front:
                fail("Upstream visibility gating or either flow animation is missing", width)
            if any(frame["upstreamLength"]<340 for frame in front.values()):
                fail("The upstream supply must be present along the entire left pipe: "+str(front), width)
            if front["initial"]["upGroupOpacity"]>.02 or front["closed"]["upGroupOpacity"]>.02:
                fail("The left water must be concealed by the opaque pipe wall: "+str(front), width)
            if not .2<front["transition"]["upGroupOpacity"]<.8:
                fail("Left-side water must appear only as the near wall becomes translucent: "+str(front), width)
            if front["finished"]["upGroupOpacity"]<.98:
                fail("The left water must be visible when the near wall is translucent: "+str(front), width)
            if front["initial"]["rightLength"]>1 or front["preopen"]["rightLength"]>1:
                fail("The right outlet must remain dry until the valve begins opening: "+str(front), width)
            if abs(front["closed"]["upOffset"]-front["initial"]["upOffset"])<30:
                fail("The concealed upstream supply must continue moving before opening: "+str(front), width)
            if (not 0<front["opening"]["rightLength"]<70 or
                    front["halfway"]["rightLength"]>=100):
                fail("Water must reach the right outlet progressively, not immediately: "+str(front), width)
            if front["finished"]["rightLength"]<160:
                fail("The downstream water must reach the right opening before the video ends: "+str(front), width)
            upstream_advance=abs(front["speedEnd"]["upOffset"]-front["speedStart"]["upOffset"])
            downstream_advance=abs(front["speedEnd"]["downOffset"]-front["speedStart"]["downOffset"])
            if abs(upstream_advance-downstream_advance)>1.0:
                fail("Left and right moving water have unequal speed: "+str(front), width)
            # Right-side fill-front speed must match both moving stripe layers:
            # all three travel 170 units between 31.45% and 100% of playback.
            synchronization=pipe_sheet.evaluate("""art=>{
              const target=['.wp-reveal-right','.wp-water-stream','.wp-flow-trace'];
              const anims=target.map(sel=>{
                const el=art.querySelector(sel);
                return {sel,el,a:el.getAnimations().find(a=>
                  a.animationName===(sel==='.wp-reveal-right'?'wp-propagate-right':'wp-water-move'))};
              });
              if(anims.some(x=>!x.a)) return null;
              const sample=t=>{
                anims.forEach(x=>x.a.currentTime=t);
                return anims.map(({el,sel})=>
                  parseFloat(getComputedStyle(el)[sel==='.wp-reveal-right'?'strokeDasharray':'strokeDashoffset']));
              };
              return {start:sample(2200),mid:sample(4500),finish:sample(7050)};
            }""")
            if not synchronization:
                fail("Missing synchronized right-side front and striping", width)
            for instant,offsets in synchronization.items():
                if abs(offsets[0]+offsets[1])>1.0 or abs(offsets[1]-offsets[2])>1.0:
                    fail("Right-side water front, inner and outer lines must move in sync at "+instant+": "+str(synchronization), width)
            if pipe_sheet.locator(".wp-upstream-stream").evaluate(
                    "(el) => getComputedStyle(el).animationIterationCount")!="1":
                fail("The video must stop after its single cycle", width)
            page.locator(".sheet-motion-play").click()
            if "is-playing" not in (pipe_sheet.get_attribute("class") or ""):
                fail("WallPipe replay did not restart", width)
            page.locator("#sheet-close").click()
            page.locator("#motion-choice").select_option("system")
            page.emulate_media(reduced_motion="reduce")

        # N.O.V.A. must reproduce the actual source site's Full HUD vocabulary,
        # centered dark-glass signature and restrained 6-second one-shot.
        nova=page.locator('.project-card[data-sheet-id="nova"] .art-nova')
        if nova.count()!=1:
            fail("N.O.V.A. artwork missing", width)
        if nova.locator(".nova-signature .nova-glass").count()!=1 or \
                nova.locator(".nova-signature .nova-nucleus").count()!=1 or \
                nova.locator(".nova-signature .nova-rings").count()!=1:
            fail("N.O.V.A. original dark glass, white nucleus or concentric signature missing", width)
        if nova.locator(".nova-dot").count()!=1:
            fail("Single amber index marker missing", width)
        # A 6px source marker with the existing 0.68 scale gives an
        # approximately 4px amber period while retaining the precise endpoint.
        marker_size=nova.locator(".nova-dot").evaluate("""el=>{
          const p=getComputedStyle(el,'::before');
          return {width:parseFloat(p.width),height:parseFloat(p.height),
                  scale:getComputedStyle(el).getPropertyValue('--nova-point-dx')!==undefined};
        }""")
        if abs(marker_size["width"]-6)>.1 or abs(marker_size["height"]-6)>.1:
            fail("N.O.V.A. amber dot should be a slightly larger 6px marker: "+str(marker_size), width)
        # All title periods align before the amber point arrives on the final one.
        period=nova.locator(".nova-title-period")
        punctuation=nova.locator(".nova-title-punctuation")
        if period.count()!=1 or period.inner_text()!="." or punctuation.count()!=4:
            fail("N.O.V.A. requires four matched punctuation marks and one landing target", width)
        punct_metrics=nova.evaluate("""art=>{
          return [...art.querySelectorAll('.nova-title-punctuation')].map(el=>{
            const r=el.getBoundingClientRect();
            const s=getComputedStyle(el);
            return {x:r.x,y:r.y,width:r.width,height:r.height,
                    marginBottom:s.marginBottom,verticalAlign:s.verticalAlign};
          });
        }""")
        if (max(p["y"] for p in punct_metrics)-min(p["y"] for p in punct_metrics)>.6 or
            max(p["height"] for p in punct_metrics)-min(p["height"] for p in punct_metrics)>.5 or
            max(p["width"] for p in punct_metrics)-min(p["width"] for p in punct_metrics)>.5 or
            len(set(p["marginBottom"] for p in punct_metrics))!=1 or
            len(set(p["verticalAlign"] for p in punct_metrics))!=1):
            fail("All N.O.V.A. punctuation marks must share a single baseline: "+str(punct_metrics), width)
        # Lower the whole punctuation family together by 2px, never just
        # the satellite destination; the amber point follows the measured dot.
        punctuation_offset=nova.locator(".nova-title-punctuation").first.evaluate(
            "el=>parseFloat(getComputedStyle(el).top)")
        if abs(punctuation_offset-2)>.1:
            fail("N.O.V.A. punctuation offset must be subtly 2px lower", width)
        point_error=nova.evaluate("""art=>{
          const o=art.getBoundingClientRect(),p=art.querySelector('.nova-title-period').getBoundingClientRect();
          const orbit=art.querySelector('.nova-orbits'),angle=34*Math.PI/180;
          const r=orbit.offsetWidth*.45-3;
          const style=getComputedStyle(art),dx=parseFloat(style.getPropertyValue('--nova-point-dx'));
          const dy=parseFloat(style.getPropertyValue('--nova-point-dy'));
          return {aligned:art.classList.contains('is-dot-aligned'),
            distance:Math.hypot(o.left+o.width*.5+r*Math.sin(angle)+dx-p.left-p.width*.5,
              o.top+o.height*.46-r*Math.cos(angle)+dy-p.top-p.height*.5)};
        }""")
        if not point_error["aligned"] or point_error["distance"]>.8:
            fail("N.O.V.A. satellite must coincide with last punctuation: "+str(point_error), width)
        if nova.locator(".nova-nucleus").get_attribute("r")!="4.3":
            fail("N.O.V.A. nucleus must be small, not a large generic glowing ball", width)
        expected_hud=((".nova-panel-core","CORE","COHERENT","INTEGRITY","NEURAL FIELD"),
                      (".nova-panel-memory","MEMORY","CONTEXT LINK","LINK","SYNC"),
                      (".nova-panel-system","SYSTEM","QUIETLY PRESENT","HOST","POWER"))
        for cls,kind,title,row_a,row_b in expected_hud:
            panel=nova.locator(cls)
            if panel.count()!=1 or panel.locator(".nova-panel-head").inner_text()!=kind or \
                    panel.locator("strong").inner_text()!=title:
                fail("N.O.V.A. Full HUD is not faithful to the original "+kind, width)
            if panel.locator("dt").all_inner_texts()!=[row_a,row_b] or \
                    panel.locator("small").inner_text()!="N–07 / VISUAL SIMULATION":
                fail("N.O.V.A. reference HUD fields are missing "+kind, width)
            if panel.evaluate("(el)=>parseFloat(getComputedStyle(el).opacity)")<.98:
                fail("N.O.V.A. reduced-motion final HUD must be visible", width)
        if nova.locator(".nova-wire").count()!=3:
            fail("The authentic sparse three-panel HUD connectors are missing", width)
        if nova.locator(".nova-idle-hint").count()!=1:
            fail("N.O.V.A. floating phase must include the original quiet-presence note", width)
        # At narrow card widths the full-size source panel's detailed rows are
        # intentionally abbreviated rather than clipped or rendered microscopically.
        if nova.evaluate("(el)=>el.getBoundingClientRect().width")<=365:
            if nova.locator(".nova-panel dl").first.evaluate(
                    "(el)=>getComputedStyle(el).display")!="none":
                fail("Compact N.O.V.A. card must hide fine-print HUD rows", width)
            for panel in nova.locator(".nova-panel").all():
                overflow=panel.evaluate("""el=>{
                  const h=el.querySelector('strong');
                  return {actual:h.scrollWidth,available:h.clientWidth,
                          lines:h.getBoundingClientRect().height /
                                parseFloat(getComputedStyle(h).lineHeight)};
                }""")
                if overflow["actual"]>overflow["available"]+2 or overflow["lines"]>3:
                    fail("N.O.V.A. condensed HUD text overflows on small screens: "+str(overflow), width)
        if width in (390,1440):
            nova.screenshot(path=str(OUT/f"nova_card_{width}.png"),animations="disabled")

        if nova.locator(".nova-panel-core").evaluate(
                "(el)=>getComputedStyle(el).backgroundColor") not in ("rgba(0, 0, 0, 0)", "transparent"):
            fail("HUD must use unobtrusive lines rather than solid card backgrounds", width)
        if width in (390,1440):
            page.emulate_media(reduced_motion="no-preference")
            media=page.locator('.project-card[data-sheet-id="nova"] .project-media')
            start_listing(page, media, nova, width)
            if ("is-playing" if width <= 760 else "is-hovering") not in (nova.get_attribute("class") or ""):
                fail("N.O.V.A. card hover animation did not begin", width)
            preview=nova.locator(".nova-orbits").evaluate("""el=>({
              name:getComputedStyle(el).animationName,
              duration:parseFloat(getComputedStyle(el).animationDuration),
              count:getComputedStyle(el).animationIterationCount
            })""")
            if (preview["name"]!="nova-orbit-activate" or
                    abs(preview["duration"]-3.75)>.02 or preview["count"]!="1"):
                fail("N.O.V.A. preview must run a 3.75-second one-shot", width)
            # The satellite travels once from orbit to the title period.
            # No intermediate rotate-then-translate hold or second size animation.
            satellite=nova.locator(".nova-dot").evaluate("""el=>{
              const a=el.getAnimations().find(a=>a.animationName==='nova-point-activate');
              if(!a) return null;
              const keys=a.effect.getKeyframes();
              const samples=[];
              for(const time of [0,750,1500,2250,3000,3750]){
                a.currentTime=time;
                const computed=getComputedStyle(el);
                const m=new DOMMatrix(computed.transform);
                samples.push({x:m.m41,y:m.m42,a:m.a,b:m.b});
              }
              return {offsets:keys.map(k=>k.offset),
                easing:getComputedStyle(el).animationTimingFunction,samples,
                secondPhase:el.getAnimations({subtree:true}).some(a=>a.animationName==='nova-point-dock-size')};
            }""")
            if not satellite or satellite["offsets"]!=[0,1] or satellite["secondPhase"]:
                fail("N.O.V.A. amber point must have one uninterrupted motion: "+str(satellite), width)
            if "cubic-bezier" not in satellite["easing"]:
                fail("N.O.V.A. amber motion must ease continuously", width)
            if any(
                sum(abs(v) for v in [
                    satellite["samples"][k+1][key]-satellite["samples"][k][key]
                    for key in ("x","y","a","b")
                ])<.01 for k in range(5)
            ):
                fail("N.O.V.A. amber point paused mid-journey: "+str(satellite), width)
            page.mouse.move(0,0)
            page.locator('.project-card[data-sheet-id="nova"] .sheet-link').click()
            art=page.locator("#sheet-visual .art-nova")
            page.wait_for_function("""() =>
              document.querySelector("#sheet-visual .art-nova")?.classList.contains("is-dot-aligned")
            """, timeout=1500)
            sheet_error=art.evaluate("""art=>{
              const o=art.getBoundingClientRect(),p=art.querySelector('.nova-title-period').getBoundingClientRect();
              const orbit=art.querySelector('.nova-orbits'),angle=34*Math.PI/180;
              const r=orbit.offsetWidth*.45-3;
              const style=getComputedStyle(art),dx=parseFloat(style.getPropertyValue('--nova-point-dx'));
              const dy=parseFloat(style.getPropertyValue('--nova-point-dy'));
              return Math.hypot(o.left+o.width*.5+r*Math.sin(angle)+dx-p.left-p.width*.5,
                o.top+o.height*.46-r*Math.cos(angle)+dy-p.top-p.height*.5);
            }""")
            if sheet_error>.8:
                fail("N.O.V.A. enlarged sheet dot must match punctuation: "+str(sheet_error), width)
            page.wait_for_function("""()=>
              document.querySelector('#sheet-visual .art-nova')?.classList.contains('is-playing')
            """, timeout=1500)
            replay=page.locator(".sheet-motion-play")
            if not replay.is_visible() or replay.inner_text().strip()!="REPLAY":
                fail("N.O.V.A. sheet replay button missing", width)
            phases=art.evaluate("""art=>{
              const selectors=['.nova-orbits','.nova-rings',
                '.nova-panel-core','.nova-panel-memory','.nova-panel-system',
                '.nova-wire-core','.nova-wire-memory','.nova-wire-system'];
              const names=['nova-orbit-activate','nova-rings-open',
                'nova-panel-core-in','nova-panel-memory-in','nova-panel-system-in',
                'nova-wire-core-in','nova-wire-memory-in','nova-wire-system-in'];
              const nodes=selectors.map(sel=>art.querySelector(sel));
              const anims=nodes.map((el,i)=>
                el?.getAnimations().find(a=>a.animationName===names[i]));
              if(anims.some(a=>!a))return null;
              const state=t=>{
                anims.forEach(a=>a.currentTime=t);
                const m=new DOMMatrix(getComputedStyle(nodes[0]).transform);
                return {scale:m.a,rings:parseFloat(getComputedStyle(nodes[1]).opacity),
                  panels:nodes.slice(2,5).map(el=>parseFloat(getComputedStyle(el).opacity)),
                  wires:nodes.slice(5).map(el=>parseFloat(getComputedStyle(el).opacity))};
              };
              return {start:state(0),floating:state(1490),active:state(2900),
                core:state(3550),memory:state(4100),system:state(4650),
                final:state(5500),ending:state(5900),
                duration:parseFloat(getComputedStyle(nodes[0]).animationDuration),
                count:getComputedStyle(nodes[0]).animationIterationCount};
            }""")
            if not phases or abs(phases["duration"]-6)>.02 or phases["count"]!="1":
                fail("N.O.V.A. full-size sheet must be a single 6s cycle", width)
            if (not .34<phases["start"]["scale"]<.45 or
                    any(v>.05 for v in phases["start"]["panels"]) or
                    phases["start"]["rings"]>.2):
                fail("Floating N.O.V.A. must begin small with dim orbital markings: "+str(phases), width)
            if phases["floating"]["scale"]>.5:
                fail("Floating phase should last roughly 1.5s: "+str(phases), width)
            if (phases["active"]["scale"]<.96 or phases["active"]["rings"]<.96 or
                    max(phases["active"]["panels"])>.05):
                fail("Active core must be formed before any Full HUD fields: "+str(phases), width)
            if (phases["core"]["panels"][0]<.65 or
                    phases["core"]["panels"][1]>.05 or
                    phases["core"]["panels"][2]>.05):
                fail("CORE must frame first: "+str(phases), width)
            if (phases["memory"]["panels"][1]<.6 or
                    phases["memory"]["panels"][2]>.05):
                fail("MEMORY must frame second: "+str(phases), width)
            if (not .25<phases["system"]["panels"][2]<.95):
                fail("SYSTEM must frame third: "+str(phases), width)
            if min(phases["final"]["panels"])<.98 or min(phases["final"]["wires"])<.98:
                fail("Full HUD missing panels or links: "+str(phases), width)
            if min(phases["ending"]["panels"])<.98:
                fail("The final HUD must be fully visible when playback stops", width)
            if width==1440:
                # Render actual intermediate screenshots for visual review.
                for t in (600,2500,3700,4550,5550):
                    replay.click()
                    art.evaluate("""(el,t)=>{
                      for(const item of el.getAnimations({subtree:true}))item.currentTime=t;
                    }""", t)
                    art.screenshot(path=str(OUT/f"nova_reference_{t}.png"), animations="allow")
            replay.click()
            if "is-playing" not in (art.get_attribute("class") or ""):
                fail("N.O.V.A. replay must restart the timeline", width)
            art.locator(".nova-panel-system").evaluate("""el=>
              el.dispatchEvent(new AnimationEvent('animationend',{
                bubbles:true,animationName:'nova-panel-system-in'}))
            """)
            if ("is-complete" not in (art.get_attribute("class") or "") or \
                    "is-playing" in (art.get_attribute("class") or "")):
                fail("N.O.V.A. should hold the last Full HUD state", width)
            if width==1440:
                art.screenshot(path=str(OUT/"nova_complete_1440.png"), animations="disabled")
            page.locator("#sheet-close").click()
            page.locator("#motion-choice").select_option("system")
            page.emulate_media(reduced_motion="reduce")
            page.locator('.project-card[data-sheet-id="nova"] .sheet-link').click()
            if not page.locator(".sheet-motion-play").is_visible():
                fail("N.O.V.A. reduced motion must retain explicit replay", width)
            if page.locator("#sheet-visual .nova-panel-system").evaluate(
                    "(el)=>getComputedStyle(el).animationName")!="none":
                fail("N.O.V.A. reduced-motion must remain static", width)
            page.locator("#sheet-close").click()

        # University AI: actual Windows system-tray workflow demonstrated with
        # invented sample rows; no fake always-open dashboard or live data.
        university=page.locator('.project-card[data-sheet-id="university-ai"] .art-university')
        if university.count()!=1:
            fail("University AI portfolio visual missing", width)
        for cls in (".up-tray-popup",".up-dialog",".up-view-today",
                    ".up-view-tasks",".up-toast",".up-taskbar"):
            if university.locator(cls).count()!=1:
                fail("University AI desktop workflow element missing: "+cls, width)
        for label in ("今日の予定","課題","試験","資料・設定"):
            if label not in university.locator(".up-tray-popup").inner_text():
                fail("University AI tray menu is not based on the real application: "+label, width)
        if university.locator(".up-demo-note").inner_text()!="INTERFACE STUDY / SAMPLE DATA":
            fail("University AI sample data must be labeled as illustrative, not live", width)
        if (university.locator(".up-view-today .up-entry").count()!=2 or
                university.locator(".up-view-tasks .up-entry").count()!=2):
            fail("University AI sample schedule and task rows missing", width)
        if "24時間前" not in university.locator(".up-toast").inner_text():
            fail("University AI deadline notification should reflect its real reminder feature", width)
        if "SQLite" not in university.locator(".up-dialog-foot").inner_text():
            fail("University AI local storage architecture label missing", width)
        rects=university.evaluate("""art=>{
          const outer=art.getBoundingClientRect();
          return ['.up-dialog','.up-toast','.up-taskbar'].map(sel=>{
            const b=art.querySelector(sel).getBoundingClientRect();
            return {sel,x:b.left-outer.left,right:outer.right-b.right,
              y:b.top-outer.top,bottom:outer.bottom-b.bottom,width:b.width};
          });
        }""")
        for rect in rects:
            if min(rect["x"],rect["right"],rect["y"],rect["bottom"])< -2:
                fail("University AI panel or notification is clipped: "+str(rects), width)
        if university.locator(".up-view-today").evaluate(
                "(el)=>getComputedStyle(el).opacity")!="0":
            fail("Static University AI preview should show assignments, not both screens", width)
        if university.locator(".up-view-tasks").evaluate(
                "(el)=>getComputedStyle(el).opacity")!="1":
            fail("Static University AI final task screen must be visible", width)
        if width in (390,1440):
            if width==390:
                university.screenshot(path=str(OUT/"university_card_390.png"),animations="disabled")
            page.emulate_media(reduced_motion="no-preference")
            media=page.locator('.project-card[data-sheet-id="university-ai"] .project-media')
            start_listing(page, media, university, width)
            if ("is-playing" if width <= 760 else "is-hovering") not in (university.get_attribute("class") or ""):
                fail("University AI card hover must trigger one-shot preview", width)
            preview=university.locator(".up-dialog").evaluate("""el=>({
              name:getComputedStyle(el).animationName,
              seconds:parseFloat(getComputedStyle(el).animationDuration),
              count:getComputedStyle(el).animationIterationCount
            })""")
            if (preview["name"]!="up-window-open" or
                    abs(preview["seconds"]-3.4375)>.025 or preview["count"]!="1"):
                fail("University AI hover preview must run 1.6x and once: "+str(preview), width)
            page.mouse.move(0,0)
            page.locator('.project-card[data-sheet-id="university-ai"] .sheet-link').click()
            art=page.locator("#sheet-visual .art-university")
            page.wait_for_function("""()=>
              document.querySelector('#sheet-visual .art-university')?.classList.contains('is-playing')
            """, timeout=1500)
            if not page.locator(".sheet-motion-play").is_visible() or \
                    page.locator(".sheet-motion-play").inner_text().strip()!="REPLAY":
                fail("University AI animation must offer single-cycle REPLAY", width)
            stages=art.evaluate("""art=>{
              const items=['.up-tray-popup','.up-dialog','.up-view-today',
                           '.up-view-tasks','.up-toast'].map(sel=>art.querySelector(sel));
              const names=['up-tray-open','up-window-open','up-today-show',
                           'up-tasks-show','up-toast-appear'];
              const anims=items.map((el,i)=>el.getAnimations().find(a=>
                a.animationName===names[i]));
              if(anims.some(a=>!a))return null;
              const state=t=>{
                anims.forEach(a=>a.currentTime=t);
                return items.map(el=>parseFloat(getComputedStyle(el).opacity));
              };
              return {start:state(0),tray:state(650),today:state(1700),
                tasks:state(2900),notification:state(4550),final:state(5500),
                seconds:parseFloat(getComputedStyle(items[1]).animationDuration),
                loops:getComputedStyle(items[1]).animationIterationCount};
            }""")
            if not stages or abs(stages["seconds"]-5.5)>.02 or stages["loops"]!="1":
                fail("University AI full sheet must run 5.5 seconds once", width)
            if max(stages["start"])>.05:
                fail("University AI must begin with an empty desktop and taskbar: "+str(stages), width)
            if (stages["tray"][0]<.95 or
                    stages["tray"][1]>.05 or stages["tray"][4]>.05):
                fail("Tray menu must be shown before the main window appears: "+str(stages), width)
            if (stages["today"][0]>.05 or stages["today"][1]<.95 or
                    stages["today"][2]<.95 or stages["today"][3]>.05):
                fail("Today's courses must follow the tray menu: "+str(stages), width)
            if (stages["tasks"][2]>.05 or stages["tasks"][3]<.95 or
                    stages["tasks"][4]>.05):
                fail("Assignments must follow today's courses without premature notification: "+str(stages), width)
            if (stages["notification"][3]<.95 or
                    stages["notification"][4]<.95):
                fail("Assignment reminder must appear last: "+str(stages), width)
            if (stages["final"][0]>.05 or stages["final"][1]<.95 or
                    stages["final"][3]<.95 or stages["final"][4]<.95):
                fail("University AI must stop on final tasks and reminder pose: "+str(stages), width)
            if width==1440:
                for t in (650,1700,2900,4550,5500):
                    page.locator(".sheet-motion-play").click()
                    art.evaluate("""(el,t)=>{
                      for(const anim of el.getAnimations({subtree:true}))anim.currentTime=t;
                    }""", t)
                    art.screenshot(path=str(OUT/f"university_stage_{t}.png"),animations="allow")
            page.locator(".sheet-motion-play").click()
            art.locator(".up-toast").evaluate("""el=>
              el.dispatchEvent(new AnimationEvent('animationend',{
                bubbles:true,animationName:'up-toast-appear'}))
            """)
            if ("is-complete" not in (art.get_attribute("class") or "") or \
                    "is-playing" in (art.get_attribute("class") or "")):
                fail("University AI must freeze the final pose after single playback", width)
            if width==1440:
                art.screenshot(path=str(OUT/"university_complete_1440.png"),animations="disabled")
            page.locator("#sheet-close").click()
            page.locator("#motion-choice").select_option("system")
            page.emulate_media(reduced_motion="reduce")
            page.locator('.project-card[data-sheet-id="university-ai"] .sheet-link').click()
            if not page.locator(".sheet-motion-play").is_visible():
                fail("University AI reduced motion must retain explicit replay", width)
            if page.locator("#sheet-visual .up-toast").evaluate(
                    "(el)=>getComputedStyle(el).animationName")!="none":
                fail("Reduced-motion University AI preview must remain static", width)
            page.locator("#sheet-close").click()

        # Corrected sparse four-stage SVG replaces the former dense mechanical poster.
        concept = page.locator('.project-card[data-project="07"] .eqmount-drawing')
        if concept.count()!=1:
            fail("concept SVG absent from seventh card", width)
        labels = concept.locator("text").all_text_contents()
        expected_stages = ("SKYSAFARI", "CONTROL", "MOTION", "TARGET")
        stage_positions = [labels.index(value) if value in labels else -1 for value in expected_stages]
        if -1 in stage_positions or stage_positions != sorted(stage_positions):
            fail("concept stages are not ordered phone to acquired target", width)
        if page.locator('.project-card[data-project="07"] .eqmount-mode, .project-card[data-project="07"] .art-cap, .project-card[data-project="07"] .art-bottom').count():
            fail("duplicated outdated art labels remain", width)
        if concept.locator('path[d="M192 178L214 191L236 190"][fill="none"]').count()!=1:
            fail("smartphone star path lost no-fill correction", width)
        if concept.locator("path.eq-belt-loop").count()!=1 or concept.locator("path.eq-belt-flow").count()!=1:
            fail("the closed pulley belt or its continuous travelling teeth are missing", width)
        if concept.locator('circle[r="53"][opacity=".42"]').count()!=1:
            fail("the pulley-back belt attenuation layer is missing", width)
        if concept.locator('.eq-large-rotor path[d*="M510 172L517 163L524 172"]').count()!=0:
            fail("rotation arrowheads should be removed, leaving straight indicator lines", width)
        if concept.locator('path[d="M281 223V233"]').count()!=0:
            fail("stray dashed Wi-Fi tail remains", width)
        if concept.locator('path[d="M551 217H570"]').count()!=0:
            fail("stray dashed stroke still protrudes right of pulley", width)
        if concept.locator(".eq-target-object").count()!=1:
            fail("offset target marker absent from final reticle", width)
        # No separator arrows, and the Wi-Fi point lies at the exact midpoint
        # of the visible gap between phone (x=139) and ESP32 (x=193).
        if concept.locator(".eq-flow-arrows, .eq-flow-arrow").count()!=0:
            fail("old stage separator arrows still visible", width)
        wifi = concept.locator(".eq-wifi-node")
        if wifi.count()!=1:
            fail("Wi-Fi symbol wrapper missing", width)
        wifi_center = wifi.evaluate("""node => {
            const transform = node.transform.baseVal.consolidate().matrix;
            return {x:281 + transform.e, y:221 + transform.f};
        }""")
        if abs(wifi_center["x"] - 166) > 0.01 or abs(wifi_center["y"] - 219) > 0.01:
            fail("Wi-Fi symbol is not centered between phone and ESP32: "+str(wifi_center), width)
        if concept.locator(".eq-control-wire path").count()!=2:
            fail("two control wires are not drawn", width)
        # The ESP's rightmost contacts are x=286, and the motor housing starts at x=320.
        wires = concept.locator(".eq-control-wire path").evaluate_all("""nodes =>
          nodes.map(n => n.getAttribute('d'))""")
        if not all(wire.startswith(("M286 233", "M286 252")) and wire.endswith(("320 269", "320")) for wire in wires):
            fail("wires do not connect the ESP32 terminals to the motor enclosure", width)
        if concept.locator(".eq-target-field > circle").count()!=5:
            fail("target field does not include all five stars", width)
        if concept.locator(".eq-target-ring").evaluate("(el) => !!el.closest('.eq-target-field')"):
            fail("target reticle must remain stationary", width)
        # Check the closed belt's two straight tangents, correct external contact
        # radii, both wrap arcs, and synchronized teeth on the same path.
        belt_geometry = concept.evaluate("""svg => {
          const belt=svg.querySelector('.eq-belt-loop');
          const flow=svg.querySelector('.eq-belt-flow');
          const d=belt?.getAttribute('d') || '';
          const m=d.match(/^M([\d.]+) ([\d.]+)L([\d.]+) ([\d.]+)A41 41 0 1 1 ([\d.]+) ([\d.]+)L([\d.]+) ([\d.]+)A13 13 0 0 1 ([\d.]+) ([\d.]+)Z$/);
          if(!m || !flow || flow.getAttribute('d')!==d) return {valid:false,error:Infinity};
          const n=m.slice(1).map(Number);
          const [suX,suY,buX,buY,blX,blY,slX,slY,endX,endY]=n;
          const c1={x:459,y:283,r:13}, c2={x:517,y:217,r:41};
          const runs=[
            [[suX,suY],[buX,buY]],
            [[slX,slY],[blX,blY]]
          ];
          const errors=[];
          for(const [small,large] of runs){
            const [sx,sy]=small,[lx,ly]=large;
            const rs=Math.hypot(sx-c1.x,sy-c1.y);
            const rl=Math.hypot(lx-c2.x,ly-c2.y);
            const vx=lx-sx,vy=ly-sy,rx=lx-c2.x,ry=ly-c2.y;
            const dot=Math.abs((vx*rx+vy*ry)/(Math.hypot(vx,vy)*rl));
            errors.push(Math.abs(rs-c1.r),Math.abs(rl-c2.r),dot);
          }
          errors.push(Math.hypot(endX-suX,endY-suY));
          return {valid:true,error:Math.max(...errors)};
        }""")
        if not belt_geometry["valid"] or belt_geometry["error"] > 0.015:
            fail("belt tangent or closed-wrap geometry is inconsistent: "+str(belt_geometry), width)
        if concept.evaluate("(el) => getComputedStyle(el).filter")!="none":
            fail("old artwork drop shadow remains", width)
        if width in (390, 1440):
            # The card itself now animates on hover, despite its transparent click overlay.
            page.emulate_media(reduced_motion="no-preference")
            card_media = page.locator('.project-card[data-project="07"] .project-media')
            card_art = card_media.locator(".art-eqmount")
            start_listing(page, card_media, card_art, width)
            if ("is-playing" if width <= 760 else "is-hovering") not in (card_art.get_attribute("class") or ""):
                fail("listing card did not start motion under the overlay", width)
            if "eq-pulley-turn" not in card_art.locator(".eq-large-rotor").evaluate(
                "(el) => getComputedStyle(el).animationName"):
                fail("pulley did not animate in listing", width)
            eq_preview_seconds = card_art.locator(".eq-large-rotor").evaluate(
                "(el) => parseFloat(getComputedStyle(el).animationDuration)")
            if abs(eq_preview_seconds - 4.0) > .02:
                fail("equatorial listing preview must be exactly 1.6x (4s): "+str(eq_preview_seconds), width)
            # Capture keyframes and sample terminal poses in one browser task.
            # Seeking to the end queues animationend, which legitimately discards
            # the one-shot CSS animations before a later evaluate can inspect them.
            drive = card_art.evaluate("""art => {
              const field=art.querySelector('.eq-target-field');
              const motor=art.querySelector('.eq-small-rotor');
              const pulley=art.querySelector('.eq-large-rotor');
              const named=(node,name)=>node.getAnimations().find(a=>a.animationName===name);
              const fieldAnim=named(field,'eq-target-acquire');
              const motorAnim=named(motor,'eq-motor-turn');
              const pulleyAnim=named(pulley,'eq-pulley-turn');
              if(!fieldAnim || !motorAnim || !pulleyAnim) return {missing:true};
              const clean=str=>(str || '').replace(/\\s+/g,'');
              const start=anim=>clean(anim.effect.getKeyframes().find(f=>Math.abs(f.offset-.58)<.0001)?.transform);
              const result={
                timing:{field:start(fieldAnim),motor:start(pulleyAnim)},
                motorTurns:motorAnim.effect.getKeyframes().at(-1).transform,
                pulleyTurns:pulleyAnim.effect.getKeyframes().at(-1).transform,
                easing:getComputedStyle(field).animationTimingFunction
              };
              const snapshot=time=>{
                fieldAnim.currentTime=time;
                motorAnim.currentTime=time;
                pulleyAnim.currentTime=time;
                const f=new DOMMatrix(getComputedStyle(field).transform);
                const m=new DOMMatrix(getComputedStyle(pulley).transform);
                const small=new DOMMatrix(getComputedStyle(motor).transform);
                return {x:f.m41,y:f.m42,angle:Math.atan2(m.b,m.a),motorAngle:Math.atan2(small.b,small.a)};
              };
              result.before=snapshot(3906);
              result.end=snapshot(4000);
              return result;
            }""")
            if drive.get("missing"):
                fail("equatorial listing drive animation missing", width)
            if drive["easing"] != "linear":
                fail("star field must move linearly until the motor finishes: "+str(drive), width)
            if abs(drive["before"]["x"] + 40) < 1 or abs(drive["before"]["y"] - 36) < 1:
                fail("target was centered before motor stopped: "+str(drive), width)
            if abs(drive["before"]["angle"]) < .05:
                fail("motor arrow returned to initial angle before target arrival: "+str(drive), width)
            if (abs(drive["end"]["x"] + 40) > .01 or abs(drive["end"]["y"] - 36) > .01 or
                    abs(drive["end"]["angle"]) > .001 or abs(drive["end"]["motorAngle"]) > .001):
                fail("target and motor final pose did not coincide: "+str(drive), width)
            if drive["timing"]["field"] not in ("translate(0px)", "translate(0px,0px)") or drive["timing"]["motor"] != "rotate(0deg)":
                fail("field movement is not synchronized with motor start: "+str(drive), width)
            if "1800" not in drive["motorTurns"]:
                fail("motor does not complete five full turns: "+str(drive), width)
            if "360" not in drive["pulleyTurns"]:
                fail("large pulley does not complete one full turn: "+str(drive), width)
            leave_listing(page, card_art, width)
            if any(c in (card_art.get_attribute("class") or "") for c in ("is-hovering", "is-playing")):
                fail("listing animation did not reset when pointer left", width)
            page.locator("#motion-choice").select_option("system")
            page.emulate_media(reduced_motion="reduce")
        if width in (390, 1440):
            page.locator('.project-card[data-project="07"] .project-art').screenshot(
                path=str(OUT/f"eqmount_concept_card_{width}.png"), animations="disabled"
            )
        # Five eligible projects open sheets; the physical project has no live demo.
        if width in (320, 390, 820, 1440):
            trigger = page.locator('.project-card[data-project="01"] .project-media-hit')
            detail = page.locator('.project-card[data-project="01"] .sheet-link')
            if trigger.get_attribute("tabindex") != "-1" or detail.get_attribute("tabindex") == "-1":
                fail("redundant tab stop or missing keyboard detail action", width)
            detail.focus()
            page.keyboard.press("Enter")
            sheet = page.locator('#project-sheet')
            if not sheet.evaluate("(el) => el.open"):
                fail("sheet did not open", width)
            if page.locator("#sheet-title").inner_text().strip() != "Sorava / SkyShare":
                fail("wrong first sheet content", width)
            if page.locator("#sheet-description").is_visible():
                fail("card summary incorrectly duplicated in detailed sheet", width)
            # Mobile scrolls artwork and copy together. Desktop scrolls only
            # the copy column. Header and navigation remain in the viewport.
            pane = sheet.evaluate("""el => {
              const visual=el.querySelector('.sheet-visual-side'),
                art=el.querySelector('.sheet-visual .project-art'),
                copy=el.querySelector('.sheet-copy-side'),
                body=el.querySelector('.sheet-body'),
                header=el.querySelector('.sheet-header'),
                footer=el.querySelector('.sheet-footer');
              const r=node => {const b=node.getBoundingClientRect();return {x:b.x,y:b.y,h:b.height,b:b.bottom}};
              const before={image:r(visual),art:r(art),header:r(header),footer:r(footer)};
              const owner=matchMedia('(max-width:760px)').matches ? body : copy;
              const overflow=getComputedStyle(owner).overflowY;
              const outerOverflow=getComputedStyle(el).overflowY;
              const available=owner.scrollHeight-owner.clientHeight;
              owner.scrollTop=owner.scrollHeight;
              const after={image:r(visual),header:r(header),footer:r(footer)};
              const actual=owner.scrollTop;
              owner.scrollTop=0;
              return {before,after,actual,available,overflow,outerOverflow};
            }""")
            if pane["overflow"] not in ("auto","scroll") or pane["outerOverflow"]!="hidden":
                fail("sheet scroll owner does not match the responsive layout", width)
            if pane["available"] > 2 and pane["actual"] < 1:
                fail("sheet content did not scroll", width)
            fixed_regions=("header","footer") if width <= 760 else ("image","header","footer")
            for region in fixed_regions:
                if abs(pane["before"][region]["y"] - pane["after"][region]["y"]) > .2:
                    fail("fixed sheet region moved during content scroll: "+region, width)
            if width <= 760 and pane["actual"] > 2 and pane["before"]["image"]["y"] - pane["after"]["image"]["y"] < 1:
                fail("mobile artwork must scroll with the description", width)
            for region in ("header", "footer"):
                if pane["after"][region]["y"] < -1 or pane["after"][region]["b"] > page.viewport_size["height"] + 1:
                    fail("sheet controls escaped the viewport: "+region, width)
            if pane["before"]["art"]["h"] < 65:
                fail("sheet illustration is clipped too small", width)
            if not page.locator("#sheet-extra").is_visible():
                fail("approved sheet content not visible", width)
            if page.locator("#sheet-extra .sheet-feature").count()!=3:
                fail("sheet feature count incorrect", width)
            if "見ている天体や場所" not in page.locator("#sheet-extra").inner_text():
                fail("Sorava primary sharing claim missing", width)
            if page.locator(".project-sheet-detail").count()!=5:
                fail("not all approved project details exist", width)
            if page.locator('.project-card[data-project="05"] .project-sheet-detail, .project-card[data-project="06"] .project-sheet-detail').count():
                fail("locked project has unpublished details", width)
            stage = sheet.bounding_box()
            if not stage or stage["x"] < -1 or stage["x"] + stage["width"] > width + 1:
                fail("sheet escapes viewport", width)
            if width in (390, 1440):
                page.screenshot(path=str(OUT/f"sheet_{width}.png"),animations="disabled")
            page.locator("#sheet-next").click()
            if page.locator("#sheet-title").inner_text().strip() != "WallPipe AR":
                fail("sheet next navigation broken", width)
            if "手をかざす" not in page.locator("#sheet-extra").inner_text():
                fail("hand-operation lead not presented", width)
            page.keyboard.press("ArrowLeft")
            if page.locator("#sheet-title").inner_text().strip() != "Sorava / SkyShare":
                fail("sheet keyboard navigation broken", width)
            page.keyboard.press("Escape")
            if sheet.evaluate("(el) => el.open"):
                fail("Escape did not close dialog", width)
            if not detail.evaluate("(el) => document.activeElement === el"):
                fail("focus did not return to opener", width)
            # Project without a public demo still needs a detail sheet.
            page.locator('.project-card[data-project="04"] .sheet-link').click()
            if page.locator("#sheet-title").inner_text().strip() != "University AI":
                fail("non-demo project sheet missing", width)
            if "連携も実装済み" not in page.locator("#sheet-extra").inner_text():
                fail("University AI linkage status wrong", width)
            page.locator("#sheet-prev").click()
            if page.locator("#sheet-title").inner_text().strip() != "N.O.V.A.":
                fail("N.O.V.A. sheet navigation missing", width)
            if "連携を実装済み" not in page.locator("#sheet-extra").inner_text():
                fail("N.O.V.A. linkage status wrong", width)
            page.locator("#sheet-next").click()
            if page.locator("#sheet-actions a").count():
                fail("private demo link unexpectedly appeared", width)
            # Verify long-form sheet remains scrollable without horizontal clipping.
            overflows = sheet.evaluate("""(el) => ({
                viewport: el.clientWidth,
                total: el.scrollWidth,
                contentHeight: el.scrollHeight,
                viewportHeight: el.clientHeight
            })""")
            if overflows["total"] > overflows["viewport"] + 1:
                fail("work sheet overflows horizontally", width)
            page.locator("#sheet-close").click()
            page.locator('.project-card[data-project="04"] .sheet-link').click()
            page.locator("#sheet-next").click()
            if page.locator("#sheet-title").inner_text().strip() != "DIY Automatic Equatorial Mount":
                fail("sheet navigation did not reach the physical project", width)
            if page.locator("#sheet-extra .sheet-feature").count()!=3:
                fail("physical sheet feature list missing", width)
            if "20Tと100T" not in page.locator("#sheet-extra").inner_text():
                fail("hardware specifications missing from physical sheet", width)
            if "SkySafari 7 Pro" not in page.locator("#sheet-extra").inner_text():
                fail("SkySafari control context missing", width)
            if page.locator("#sheet-actions a").count():
                fail("hardware sheet contains an invented demo link", width)
            if page.locator('#sheet-visual .art-eqmount').count()!=1:
                fail("original equatorial mount illustration missing in sheet", width)
            if not page.locator(".sheet-motion-play").is_visible():
                fail("reduced motion must retain explicit playback", width)
            if width in (390, 1440):
                # Exercise the actual mouse-hover and mobile replay paths with motion enabled.
                page.emulate_media(reduced_motion="no-preference")
                page.locator("#sheet-close").click()
                page.locator('.project-card[data-project="07"] .sheet-link').click()
                art = page.locator("#sheet-visual .art-eqmount")
                play_button = page.locator(".sheet-motion-play")
                page.wait_for_function("""() => document.querySelector('#sheet-visual .art-eqmount')?.classList.contains('is-playing')""", timeout=1500)
                if not play_button.evaluate("(el) => el.parentElement.classList.contains('sheet-visual-bottom')"):
                    fail("replay control must be in the artwork panel bottom caption", width)
                replay_position=play_button.evaluate("""node => {
                  const control=node.getBoundingClientRect();
                  const caption=node.parentElement.getBoundingClientRect();
                  const panel=node.closest('.sheet-visual-side').getBoundingClientRect();
                  const image=document.querySelector('#sheet-visual .project-art').getBoundingClientRect();
                  return {
                    rightGap:caption.right-control.right,
                    bottomGap:panel.bottom-control.bottom,
                    rightInPanel:control.right<=panel.right+1,
                    belowImage:control.top>=image.top+image.height-1
                  };
                }""")
                if not (abs(replay_position["rightGap"])<3 and
                        replay_position["bottomGap"]>=-1 and
                        replay_position["rightInPanel"] and
                        replay_position["belowImage"]):
                    fail("replay control not at bottom-right under fixed image: "+str(replay_position), width)
                if not play_button.is_visible():
                    fail("equatorial motion replay control not visible", width)
                if art.locator(".eq-large-rotor").count()!=1 or art.locator(".eq-belt-teeth").count()!=1:
                    fail("rotor or belt travel elements missing", width)
                eq_sheet_seconds=art.locator(".eq-large-rotor").evaluate(
                    "(el) => parseFloat(getComputedStyle(el).animationDuration)")
                if abs(eq_sheet_seconds - 6.4) > .02:
                    fail("equatorial detail sheet must keep normal 6.4s playback", width)
                if page.locator('.project-card[data-project="07"] .eq-belt-teeth').count()!=1:
                    fail("listing lost its static SVG artwork", width)
                if page.locator('.project-card[data-project="07"] .eq-small-rotor').evaluate(
                    "(el) => getComputedStyle(el).opacity")!="0":
                    fail("noninteractive listing unexpectedly shows motor animation markers", width)
                # Opening via NEXT from University AI must start exactly one
                # cycle without hovering, and leaving the artwork must NOT stop it.
                if "is-playing" not in (art.get_attribute("class") or ""):
                    fail("NEXT navigation did not autoplay the animated sheet", width)
                if "is-hovering" in (art.get_attribute("class") or ""):
                    fail("sheet unexpectedly depends on hover", width)
                rotating = art.locator(".eq-large-rotor").evaluate(
                    "(el) => getComputedStyle(el).animationName")
                if "eq-pulley-turn" not in rotating:
                    fail("autoplay does not animate the large pulley", width)
                # The artwork is deliberately noninteractive; moving over it or
                # away must leave the running animation undisturbed.
                page.mouse.move(0,0)
                art.hover(position={"x":15,"y":15})
                if "is-hovering" in (art.get_attribute("class") or ""):
                    fail("sheet hover activated a second animation", width)
                page.mouse.move(0,0)
                if "is-playing" not in (art.get_attribute("class") or ""):
                    fail("sheet playback stopped when pointer left artwork", width)
                if art.locator(".eq-large-rotor").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="eq-pulley-turn":
                    fail("leaving the sheet artwork interrupted autoplay", width)
                play_button.click()
                if "is-playing" not in (art.get_attribute("class") or ""):
                    fail("touch replay button did not start animation", width)
                if "eq-belt-travel" not in art.locator(".eq-belt-flow").evaluate(
                    "(el) => getComputedStyle(el).animationName"):
                    fail("belt-motion animation not active on replay", width)
                # Record an early state without allowing a screenshot to complete the cycle.
                page.locator("#sheet-next").click()
                if page.locator("#sheet-visual .art-eqmount").count()!=0:
                    fail("sheet switching did not clear equatorial motion", width)
                page.wait_for_function("""() =>
                  document.querySelector('#sheet-visual .art-sorava')?.classList.contains('is-playing')
                """, timeout=1500)
                if not play_button.is_visible() or "Sorava" not in (play_button.get_attribute("aria-label") or ""):
                    fail("NEXT did not switch the replay control to Sorava", width)
                page.locator("#sheet-prev").click()
                page.wait_for_function("""() => document.querySelector('#sheet-visual .art-eqmount')?.classList.contains('is-playing')""", timeout=1500)
                # Old animation is discarded on navigation; reopening starts
                # a fresh, single autoplay cycle rather than staying paused.
                page.locator("#motion-choice").select_option("system")
                page.emulate_media(reduced_motion="reduce")
                if art.locator(".eq-large-rotor").count()!=1:
                    # After re-opening, the previous locator should still resolve to this clone.
                    fail("equatorial SVG disappeared during reduced-motion check", width)
                if art.locator(".eq-large-rotor").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="none":
                    fail("prefers-reduced-motion does not stop CSS animation", width)
            if width in (390,1440):
                page.screenshot(path=str(OUT/f"equatorial_sheet_{width}.png"), animations="disabled")
            page.locator("#sheet-next").click()
            if page.locator("#sheet-title").inner_text().strip() != "Sorava / SkyShare":
                fail("sheet navigation did not skip locked works", width)
            # PREV and NEXT should each initiate one autoplay upon entering
            # the mount sheet, even without moving the pointer over the art.
            if width in (390,1440):
                page.emulate_media(reduced_motion="no-preference")
            page.locator("#sheet-prev").click()
            if page.locator("#sheet-title").inner_text().strip() != "DIY Automatic Equatorial Mount":
                fail("reverse navigation did not reach the hardware sheet", width)
            if width in (390,1440):
                page.wait_for_function("""() => document.querySelector('#sheet-visual .art-eqmount')?.classList.contains('is-playing')""", timeout=1500)
                if page.locator("#sheet-visual .art-eqmount.is-hovering").count():
                    fail("PREV navigation required hover to start mount animation", width)
                page.locator("#sheet-next").click()
                page.locator("#sheet-prev").click()
                page.wait_for_function("""() => document.querySelector('#sheet-visual .art-eqmount')?.classList.contains('is-playing')""", timeout=1500)
                if page.locator("#sheet-visual .art-eqmount.is-hovering").count():
                    fail("second PREV navigation required hover to restart", width)
            page.locator("#sheet-close").click()
            if width in (390, 1440):
                # Two screen-dominant phones, central Wi-Fi, a selected
                # M42 on the host, and a distinct guest before and after sync.
                page.emulate_media(reduced_motion="no-preference")
                sorava_media = page.locator('.project-card[data-project="01"] .project-media')
                sorava_card = sorava_media.locator(".art-sorava")
                if sorava_card.locator(".sorava-phone-host").count()!=1 or sorava_card.locator(".sorava-phone-guest").count()!=1:
                    fail("Sorava concept must show two phone screens", width)
                if sorava_card.locator(".sorava-wifi-node").count()!=1:
                    fail("Sorava Wi-Fi symbol must be between the two phones", width)
                phone_geometry = sorava_card.evaluate("""art => {
                  const rect = el => el.getBoundingClientRect();
                  const host = art.querySelector('.sorava-phone-host');
                  const guest = art.querySelector('.sorava-phone-guest');
                  const wifi = art.querySelector('.sorava-wifi-node');
                  const hostBody = rect(host.querySelector('rect:first-child'));
                  const guestBody = rect(guest.querySelector('rect:first-child'));
                  const hostScreen = rect(host.querySelector('rect:nth-child(2)'));
                  const guestScreen = rect(guest.querySelector('rect:nth-child(2)'));
                  const point = rect(wifi);
                  return {
                    screenFraction:hostScreen.width/hostBody.width,
                    guestFraction:guestScreen.width/guestBody.width,
                    phoneWidths:[hostBody.width,guestBody.width],
                    phoneAspects:[hostBody.width/hostBody.height,guestBody.width/guestBody.height],
                    centered: Math.abs((point.left + point.right)/2-(hostBody.right+guestBody.left)/2),
                    space: guestBody.left - hostBody.right,
                    screenInside: hostScreen.left>hostBody.left && hostScreen.right<hostBody.right &&
                                  guestScreen.left>guestBody.left && guestScreen.right<guestBody.right
                  };
                }""")
                if (phone_geometry["screenFraction"] < .89 or phone_geometry["guestFraction"] < .89 or
                        phone_geometry["space"] < 14 or not phone_geometry["screenInside"] or
                        phone_geometry["centered"] > 2 or
                        any(a < .47 or a > .56 for a in phone_geometry["phoneAspects"])):
                    fail("Sorava devices must be tall phones with large screens and central Wi-Fi: "+str(phone_geometry), width)
                if sorava_card.locator(".sorava-data-packet").count()!=0:
                    fail("Stray flying data dot must be completely removed", width)
                if sorava_card.locator(".sorava-guest-field").count()!=1:
                    fail("The independent guest star field is missing", width)
                # Guidance arrow sits inside the lower part of the chart,
                # centered horizontally, just above the LOCAL VIEW caption.
                arrow_location=sorava_card.evaluate("""art => {
                  const circle=art.querySelector('.sorava-guest-direction circle').getBoundingClientRect();
                  const chart=art.querySelector('.sorava-phone-guest .sorava-phone-map').getBoundingClientRect();
                  return {
                    x:((circle.left+circle.width/2)-chart.left)/chart.width,
                    y:((circle.top+circle.height/2)-chart.top)/chart.height,
                    label:art.querySelector('.sorava-guest-guiding-label')?.textContent
                  };
                }""")
                if (abs(arrow_location["x"] - .5) > .055 or
                        arrow_location["y"] < .70 or arrow_location["y"] > .94 or
                        arrow_location["label"] != "FOLLOW ↗"):
                    fail("Sorava guidance arrow not in marked lower star-map position: "+str(arrow_location), width)
                start_listing(page, sorava_media, sorava_card, width)
                if ("is-playing" if width <= 760 else "is-hovering") not in (sorava_card.get_attribute("class") or ""):
                    fail("Sorava listing hover did not start playback", width)
                if sorava_card.locator(".sorava-guest-received").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="sorava-guest-receive":
                    fail("Sorava guest reception animation is missing on card hover", width)
                sorava_preview_seconds=sorava_card.locator(".sorava-guest-received").evaluate(
                    "(el) => parseFloat(getComputedStyle(el).animationDuration)")
                if abs(sorava_preview_seconds - 4.5) > .02:
                    fail("Sorava listing preview must be exactly 1.6x (4.5s): "+str(sorava_preview_seconds), width)
                page.mouse.move(0, 0)
                if "is-hovering" in (sorava_card.get_attribute("class") or ""):
                    fail("Sorava listing animation did not reset", width)
                page.locator('.project-card[data-project="01"] .sheet-link').click()
                sorava_sheet = page.locator("#sheet-visual .art-sorava")
                page.wait_for_function("""() =>
                  document.querySelector('#sheet-visual .art-sorava')?.classList.contains('is-playing')
                """, timeout=1500)
                if sorava_sheet.locator(".sorava-phone-host").count()!=1 or sorava_sheet.locator(".sorava-phone-guest").count()!=1:
                    fail("Sorava clone lost its phones", width)
                sorava_sheet_seconds=sorava_sheet.locator(".sorava-guest-received").evaluate(
                    "(el) => parseFloat(getComputedStyle(el).animationDuration)")
                if abs(sorava_sheet_seconds - 7.2) > .02:
                    fail("Sorava detail sheet must keep normal 7.2s playback", width)
                replay = page.locator(".sheet-motion-play")
                if not replay.is_visible() or "Sorava" not in (replay.get_attribute("aria-label") or ""):
                    fail("Sorava missing replay control", width)
                if not replay.evaluate("(el) => el.parentElement.classList.contains('sheet-visual-bottom')"):
                    fail("Sorava replay must stay below art on right side", width)
                phases = sorava_sheet.evaluate("""art => {
                  const get = sel => art.querySelector(sel);
                  const host=get('.sorava-host-picked'),guest=get('.sorava-guest-received');
                  const waiting=get('.sorava-guest-waiting'),wifi=get('.sorava-wifi-node');
                  const hostReticle=get('.sorava-host-reticle');
                  const guestReticle=get('.sorava-guest-reticle');
                  const guestArrow=get('.sorava-guest-direction');
                  const nodes=[host,guest,waiting,wifi,hostReticle,guestReticle,guestArrow];
                  const animations=nodes.map(node=>node.getAnimations()[0]);
                  const state=t=>{
                    animations.forEach(animation=>animation.currentTime=t);
                    return nodes.map(node=>Number(getComputedStyle(node).opacity));
                  };
                  return {start:state(0),host:state(1900),transfer:state(3600),
                          guest:state(6100),end:state(7200),
                          hostM42:get('.sorava-phone-host').textContent.includes('M42'),
                          guestM42:get('.sorava-phone-guest').textContent.includes('M42'),
                          finishName:animations[1].animationName};
                }""")
                if not phases["hostM42"] or not phases["guestM42"] or phases["finishName"]!="sorava-guest-receive":
                    fail("Sorava M42 synchronization target or finish animation missing", width)
                if phases["start"][0]>.05 or phases["start"][1]>.05 or phases["start"][2]<.95:
                    fail("Sorava initial screen state incorrect: "+str(phases), width)
                if any(phases["start"][index] > .05 for index in (4,5,6)):
                    fail("Neither phone may show a reticle/arrow before selecting M42: "+str(phases), width)
                if phases["host"][0]<.95 or phases["host"][1]>.05:
                    fail("Sorava host must select M42 before guest: "+str(phases), width)
                if phases["host"][4]<.95 or phases["host"][5]>.05 or phases["host"][6]>.05:
                    fail("Host reticle should appear only after M42 selection; guest stays blank: "+str(phases), width)
                if phases["transfer"][3]<.8 or phases["transfer"][1]>.05:
                    fail("Sorava Wi-Fi phase is not between host and guest: "+str(phases), width)
                if phases["transfer"][6]<.95 or phases["transfer"][5]<.95:
                    fail("Guest reticle and directional arrow must appear together during guidance: "+str(phases), width)
                if phases["guest"][1]<.95 or phases["guest"][2]>.05:
                    fail("Sorava guest did not receive M42: "+str(phases), width)
                if phases["end"][1]<.95 or phases["end"][2]>.05:
                    fail("Sorava did not finish showing both M42 screens: "+str(phases), width)
                if phases["end"][4]<.95 or phases["end"][5]<.95 or phases["end"][6]>.05:
                    fail("After guest acquisition, both reticles must show and arrow must disappear: "+str(phases), width)
                if width in (390,1440):
                    sorava_sheet.screenshot(path=str(OUT/f"sorava_two_phones_{width}.png"),animations="disabled")
                # Screenshot testing may finish/cancel finite animations. Explicitly
                # restart the motion before measuring intermediate CSS frames.
                replay.click()
                # At the start the guest points elsewhere (its target is
                # away from the fixed reticle); it aligns only after Wi-Fi sync.
                # Sample the actual rendered SVG coordinates, not just keyframes.
                synced_views=sorava_sheet.evaluate("""art => {
                  const get=s => art.querySelector(s);
                  const guest=get('.sorava-guest-field');
                  const wifi=get('.sorava-wifi-node');
                  const guestAnim=guest.getAnimations().find(a=>a.animationName==='sorava-guest-pointing');
                  const wifiAnim=wifi.getAnimations().find(a=>a.animationName==='sorava-wifi-blink');
                  const point=s => {const r=get(s).getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}};
                  const distance=()=>{
                    const star=point('.sorava-phone-guest .sorava-m42-star');
                    const sight=point('.sorava-phone-guest .sorava-map-reticle circle');
                    return Math.hypot(star.x-sight.x,star.y-sight.y);
                  };
                  const alignAt=time=>{guestAnim.currentTime=time;return distance()};
                  const opacityAt=time=>{wifiAnim.currentTime=time;return Number(getComputedStyle(wifi).opacity)};
                  return {
                    initial:alignAt(0),
                    beforeSync:alignAt(3600),
                    end:alignAt(7200),
                    blinkBright1:opacityAt(2400),
                    blinkDim1:opacityAt(2880),
                    blinkBright2:opacityAt(3600),
                    blinkDim2:opacityAt(4032),
                    blinkBright3:opacityAt(4464),
                    terminal:opacityAt(7200),
                    blinkingName:wifiAnim.animationName,
                    pointingName:guestAnim.animationName
                  };
                }""")
                if synced_views["initial"] < 8 or synced_views["beforeSync"] < 8 or synced_views["end"] > 1.2:
                    fail("Guest starts aligned, or does not move into host pointing: "+str(synced_views), width)
                if (synced_views["blinkingName"]!="sorava-wifi-blink" or
                        synced_views["pointingName"]!="sorava-guest-pointing" or
                        min(synced_views[k] for k in ("blinkBright1","blinkBright2","blinkBright3")) < .82 or
                        max(synced_views[k] for k in ("blinkDim1","blinkDim2")) > .24 or
                        synced_views["terminal"] < .8):
                    fail("The Wi-Fi mark itself must flash clearly three times: "+str(synced_views), width)
                replay.click()
                if "is-playing" not in (sorava_sheet.get_attribute("class") or ""):
                    fail("Sorava REPLAY failed to restart animation", width)
                page.mouse.move(0,0)
                sorava_sheet.hover(position={"x":15,"y":15})
                page.mouse.move(0,0)
                if sorava_sheet.locator(".sorava-guest-received").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="sorava-guest-receive":
                    fail("Sorava sheet playback interrupted by mouse position", width)
                page.locator("#sheet-next").click()
                if (page.locator("#sheet-visual .art-sorava").count()!=0 or
                        page.locator("#sheet-visual .art-wallpipe").count()!=1 or
                        not replay.is_visible()):
                    fail("Sorava NEXT must hand playback over to WallPipe", width)
                page.locator("#sheet-prev").click()
                page.wait_for_function("""() =>
                  document.querySelector('#sheet-visual .art-sorava')?.classList.contains('is-playing')
                """, timeout=1500)
                if page.locator("#sheet-visual .art-sorava.is-hovering").count()!=0:
                    fail("Sorava NEXT/PREV autoplay requires pointer hover", width)
                page.locator("#sheet-close").click()
                page.locator("#motion-choice").select_option("system")
                page.emulate_media(reduced_motion="reduce")
                page.locator('.project-card[data-project="01"] .sheet-link').click()
                if not page.locator(".sheet-motion-play").is_visible():
                    fail("Sorava reduced motion must retain explicit replay", width)
                if page.locator("#sheet-visual .sorava-guest-received").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="none":
                    fail("Sorava ignores reduced-motion settings", width)
                page.locator("#sheet-close").click()
            if errors: fail("JavaScript error after sheet controls: "+repr(errors), width)
        if width == 390:
            # Normal first visit: construction is accelerated, then one automatic spin.
            # Explicit REPLAY must restore the original drawing speed and must not auto-spin.
            page.emulate_media(reduced_motion="no-preference")
            page.locator('#motion-choice').select_option('system')
            # Prior sheet checks may have scrolled far below the hero. Browsers
            # throttle offscreen iframes, so inspect a true visible first visit.
            page.locator('.hero').evaluate(
                "el => el.scrollIntoView({block:'start',behavior:'instant'})"
            )
            page.reload(wait_until='load')
            page.locator('.hero').scroll_into_view_if_needed()
            construction=page.frame_locator('#hero-logo-frame').locator('body')
            if not construction.evaluate("() => Math.abs(window.getLogoStatus().speed-1.35)<0.001"):
                fail("first-load construction playback must be faster", width)
            if not construction.evaluate(
                "() => Math.abs(window.getLogoStatus().total-5.6234)<0.002"
            ):
                fail("opening guide fade was not shortened", width)
            if page.evaluate("() => !!document.createElement('canvas').getContext('webgl2')"):
                try:
                    page.wait_for_function(
                        "document.querySelector('.hero-visual').classList.contains('is-logo-spinning')",
                        timeout=11000
                    )
                except Exception:
                    print("OPENING_SEQUENCE_DIAGNOSTICS", {
                        "motion":page.evaluate("""() => ({
                            choice:document.documentElement.dataset.motionChoice,
                            systemReduced:matchMedia('(prefers-reduced-motion: reduce)').matches,
                            hero:document.querySelector('.hero').getBoundingClientRect().top,
                            classes:document.querySelector('.hero-visual').className,
                            hasSpinFactory:typeof window.createRLogoSpin
                        })"""),
                        "iframe":construction.evaluate("() => window.getLogoStatus()")
                    }, flush=True)
                    raise
                page.wait_for_function(
                    "!document.querySelector('.hero-visual').classList.contains('is-logo-spinning')",
                    timeout=7000
                )
                page.locator('#hero-logo-replay').click()
                page.wait_for_function(
                    "() => document.querySelector('.hero-visual')?.classList.contains('is-logo-complete') === false"
                )
                # postMessage is asynchronous: confirm the iframe actually accepted
                # REPLAY before asserting its playback speed.
                normal_replay=construction.evaluate("""async () => {
                    for (let i=0; i<60; i++) {
                        const state=window.getLogoStatus();
                        if (state.speed === 1 && state.running) return true;
                        await new Promise(resolve => setTimeout(resolve, 50));
                    }
                    return false;
                }""")
                if not normal_replay:
                    fail("manual REPLAY must use the original construction speed", width)
                if not construction.evaluate(
                    "() => Math.abs(window.getLogoStatus().total-6.2734)<0.002"
                ):
                    fail("manual REPLAY did not restore original guide fade", width)
                construction.evaluate("() => window.setLogoTime(window.getLogoStatus().total)")
                page.wait_for_function(
                    "document.querySelector('.hero-visual').classList.contains('is-logo-complete')"
                )
                if page.locator('.hero-visual.is-logo-spinning').count():
                    fail("manual REPLAY unexpectedly triggered the opening 3D spin", width)
        print("QA_PASS",width,"cards",len(boxes),"width",metrics["scrollWidth"],flush=True)
        page.close()
    browser.close()

print("QA_COMPLETED",len(WIDTHS),"viewport widths, concept visuals and filters")
