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
        if metrics["scrollWidth"] > metrics["innerWidth"] + 1:
            fail("horizontal overflow: "+json.dumps(metrics["scrollWidth"]), width)
        if metrics["logoOverlap"]: fail("header branding overlaps navigation", width)
        if metrics["hasJPOutside"]: fail("unwanted Japanese text outside work cards", width)
        if metrics["sourceLinks"]: fail("source-code link was reintroduced", width)
        if metrics["emptyAnchors"]: fail("broken internal anchors: "+repr(metrics["emptyAnchors"]), width)
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
        if width in (320,390,820,1024,1440):
            page.screenshot(path=str(OUT/f"portfolio_{width}.png"),full_page=True,animations="disabled")
        # Verify existing category filtering on narrow and full desktop.
        if width in (320, 390, 820, 1440):
            page.locator('button[data-filter="ai"]').click()
            if page.locator('.project-card:visible').count()!=2:
                fail("AI filter not preserving its two projects", width)
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
            if locked.locator(".project-locked-note").inner_text().strip()!="PREVIEW UNAVAILABLE":
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
        if concept.locator('path.eq-belt-upper-run[d="M447.01 277.98L479.18 201.16"]').count()!=1:
            fail("upper belt does not meet the common pulley radius", width)
        if concept.locator('path.eq-belt-lower-run[d="M465.52 294.25L537.57 252.47"]').count()!=1:
            fail("lower belt does not meet the common pulley radius", width)
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
        # Both contact points must be on the same 41-unit pitch circle, with
        # the line normal perpendicular to each run (external tangents).
        tangent_error = concept.evaluate("""svg => {
          const c1 = {x:459,y:283,r:13}, c2 = {x:517,y:217,r:41};
          const paths = [
            svg.querySelector('.eq-belt-upper-run'),
            svg.querySelector('.eq-belt-lower-run')
          ];
          return paths.map(p => {
            const v = p.getAttribute('d').match(/[-+]?[0-9]*\\.?[0-9]+/g).map(Number);
            const [x1,y1,x2,y2] = v;
            const rad1 = Math.hypot(x1-c1.x,y1-c1.y);
            const rad2 = Math.hypot(x2-c2.x,y2-c2.y);
            const dot = ((x2-x1)*(x2-c2.x)+(y2-y1)*(y2-c2.y)) /
              (Math.hypot(x2-x1,y2-y1)*rad2);
            return Math.max(Math.abs(rad1-c1.r),Math.abs(rad2-c2.r),Math.abs(dot));
          });
        }""")
        if any(v > 0.015 for v in tangent_error):
            fail("belt tangent geometry is inconsistent: "+str(tangent_error), width)
        if concept.evaluate("(el) => getComputedStyle(el).filter")!="none":
            fail("old artwork drop shadow remains", width)
        if width in (390, 1440):
            # The card itself now animates on hover, despite its transparent click overlay.
            page.emulate_media(reduced_motion="no-preference")
            card_media = page.locator('.project-card[data-project="07"] .project-media')
            card_art = card_media.locator(".art-eqmount")
            card_media.hover()
            if "is-hovering" not in (card_art.get_attribute("class") or ""):
                fail("listing card did not start motion under the overlay", width)
            if "eq-pulley-turn" not in card_art.locator(".eq-large-rotor").evaluate(
                "(el) => getComputedStyle(el).animationName"):
                fail("pulley did not animate in listing", width)
            # At end, the target reaches the reticle and all pulley arrows
            # return to their original orientation after whole turns.
            final = card_art.evaluate("""el => {
              const matrix = selector => {
                const n=el.querySelector(selector);
                const a=n.getAnimations().find(x=>x.animationName);
                a.currentTime=6400;
                return getComputedStyle(n).transform;
              };
              return {
                target:matrix('.eq-target-field'),
                motor:matrix('.eq-small-rotor'),
                pulley:matrix('.eq-large-rotor')
              };
            }""")
            if "-40" not in final["target"] or "36" not in final["target"]:
                fail("star field never reaches the reticle center: "+str(final), width)
            # At 6250 ms both are still traveling; only at the same 6400 ms
            # endpoint does the star field center and the motor arrow finish
            # its integral turn. A non-linear eased field would fail this check.
            sync = card_art.evaluate("""art => {
              const field = art.querySelector('.eq-target-field');
              const pulley = art.querySelector('.eq-large-rotor');
              const fieldAnim = field.getAnimations().find(a => a.animationName === 'eq-target-acquire');
              const pulleyAnim = pulley.getAnimations().find(a => a.animationName === 'eq-pulley-turn');
              const snapshot = time => {
                fieldAnim.currentTime = time;
                pulleyAnim.currentTime = time;
                const f = new DOMMatrix(getComputedStyle(field).transform);
                const m = new DOMMatrix(getComputedStyle(pulley).transform);
                return {x:f.m41, y:f.m42, angle:Math.atan2(m.b,m.a)};
              };
              return {
                easing:getComputedStyle(field).animationTimingFunction,
                before:snapshot(6250),
                end:snapshot(6400)
              };
            }""")
            if sync["easing"] != "linear":
                fail("star field must move linearly until the motor finishes: "+str(sync), width)
            if abs(sync["before"]["x"] + 40) < 1 or abs(sync["before"]["y"] - 36) < 1:
                fail("target was centered before motor stopped: "+str(sync), width)
            if abs(sync["before"]["angle"]) < .05:
                fail("motor arrow returned to initial angle before target arrival: "+str(sync), width)
            if abs(sync["end"]["x"] + 40) > .01 or abs(sync["end"]["y"] - 36) > .01 or abs(sync["end"]["angle"]) > .001:
                fail("target and motor final pose did not coincide: "+str(sync), width)
            timing = card_art.evaluate("""el => {
              const frames = selector => el.querySelector(selector).getAnimations()[0].effect.getKeyframes();
              const beforeMovement = frames('.eq-target-field').find(f => Math.abs(f.offset-0.58)<0.0001);
              const motorStart = frames('.eq-large-rotor').find(f => Math.abs(f.offset-0.58)<0.0001);
              const clean = str => (str || '').replace(/\\s+/g,'');
              return {field:clean(beforeMovement?.transform),motor:clean(motorStart?.transform)};
            }""")
            if timing["field"] not in ("translate(0px)", "translate(0px,0px)") or timing["motor"]!="rotate(0deg)":
                fail("field movement is not synchronized with motor start: "+str(timing), width)
            if "1800" not in page.locator(".eq-small-rotor").first.evaluate(
                "(el) => el.getAnimations().find(x=>x.animationName==='eq-motor-turn')?.effect.getKeyframes().at(-1).transform || ''"):
                fail("motor does not complete five full turns", width)
            if "360" not in page.locator(".eq-large-rotor").first.evaluate(
                "(el) => el.getAnimations().find(x=>x.animationName==='eq-pulley-turn')?.effect.getKeyframes().at(-1).transform || ''"):
                fail("large pulley does not complete one full turn", width)
            page.mouse.move(0,0)
            if "is-hovering" in (card_art.get_attribute("class") or ""):
                fail("listing animation did not reset when pointer left", width)
            page.emulate_media(reduced_motion="reduce")
        if width in (390, 1440):
            page.locator('.project-card[data-project="07"] .project-art').screenshot(
                path=str(OUT/f"eqmount_concept_card_{width}.png"), animations="disabled"
            )
        # Five eligible projects open sheets; the physical project has no live demo.
        if width in (320, 390, 820, 1440):
            trigger = page.locator('.project-card[data-project="01"] .project-media-hit')
            trigger.click()
            sheet = page.locator('#project-sheet')
            if not sheet.evaluate("(el) => el.open"):
                fail("sheet did not open", width)
            if page.locator("#sheet-title").inner_text().strip() != "Sorava / SkyShare":
                fail("wrong first sheet content", width)
            if page.locator("#sheet-description").is_visible():
                fail("card summary incorrectly duplicated in detailed sheet", width)
            # Only the information column scrolls; all artwork, header, and
            # navigation stay stationary at both desktop and mobile widths.
            pane = sheet.evaluate("""el => {
              const visual=el.querySelector('.sheet-visual-side'),
                art=el.querySelector('.sheet-visual .project-art'),
                copy=el.querySelector('.sheet-copy-side'),
                header=el.querySelector('.sheet-header'),
                footer=el.querySelector('.sheet-footer');
              const r=node => {const b=node.getBoundingClientRect();return {x:b.x,y:b.y,h:b.height,b:b.bottom}};
              const before={image:r(visual),art:r(art),header:r(header),footer:r(footer)};
              const overflow=getComputedStyle(copy).overflowY;
              const outerOverflow=getComputedStyle(el).overflowY;
              const available=copy.scrollHeight-copy.clientHeight;
              copy.scrollTop=copy.scrollHeight;
              const after={image:r(visual),header:r(header),footer:r(footer)};
              const actual=copy.scrollTop;
              copy.scrollTop=0;
              return {before,after,actual,available,overflow,outerOverflow};
            }""")
            if pane["overflow"] not in ("auto","scroll") or pane["outerOverflow"]!="hidden":
                fail("sheet scroll owner is not the right description pane", width)
            if pane["available"] > 2 and pane["actual"] < 1:
                fail("description did not scroll independently", width)
            for region in ("image","header","footer"):
                if abs(pane["before"][region]["y"] - pane["after"][region]["y"]) > .2:
                    fail("fixed sheet region moved during description scroll: "+region, width)
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
            if not trigger.evaluate("(el) => document.activeElement === el"):
                fail("focus did not return to opener", width)
            # Project without a public demo still needs a detail sheet.
            page.locator('.project-card[data-project="04"] .project-title-button').click()
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
            page.locator('.project-card[data-project="04"] .project-title-button').click()
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
            if page.locator(".sheet-motion-play").is_visible():
                fail("reduced-motion preference unexpectedly exposes playback", width)
            if width in (390, 1440):
                # Exercise the actual mouse-hover and mobile replay paths with motion enabled.
                page.emulate_media(reduced_motion="no-preference")
                page.locator("#sheet-close").click()
                page.locator('.project-card[data-project="07"] .project-title-button').click()
                art = page.locator("#sheet-visual .art-eqmount")
                play_button = page.locator(".sheet-motion-play")
                page.wait_for_function("""() => document.querySelector('#sheet-visual .art-eqmount')?.classList.contains('is-playing')""", timeout=1500)
                if play_button.evaluate("(el) => el.parentElement.id")!="sheet-visual":
                    fail("replay control was not moved into image frame", width)
                control_center=play_button.evaluate("""node => {
                  const a=node.getBoundingClientRect(),
                        b=node.parentElement.getBoundingClientRect();
                  return {dx:(a.left+a.width/2)-(b.left+b.width/2),
                          dy:(a.top+a.height/2)-(b.top+b.height/2)};
                }""")
                if abs(control_center["dx"])>1.1 or abs(control_center["dy"])>1.1:
                    fail("replay control is not centered over visual: "+str(control_center), width)
                if not play_button.is_visible():
                    fail("equatorial motion replay control not visible", width)
                if art.locator(".eq-large-rotor").count()!=1 or art.locator(".eq-belt-teeth").count()!=2:
                    fail("rotor or belt travel elements missing", width)
                if page.locator('.project-card[data-project="07"] .eq-belt-teeth').count()!=2:
                    fail("listing lost its static SVG artwork", width)
                if page.locator('.project-card[data-project="07"] .eq-small-rotor').evaluate(
                    "(el) => getComputedStyle(el).opacity")!="0":
                    fail("noninteractive listing unexpectedly shows motor animation markers", width)
                # The sheet auto-plays on opening. Move outside first so a
                # genuine pointerenter (rather than a hover over the autoplay
                # overlay) is tested.
                page.mouse.move(0,0)
                art.hover(position={"x":15,"y":15})
                if "is-hovering" not in (art.get_attribute("class") or ""):
                    fail("desktop hover did not activate sheet SVG", width)
                rotating = art.locator(".eq-large-rotor").evaluate(
                    "(el) => getComputedStyle(el).animationName")
                if "eq-pulley-turn" not in rotating:
                    fail("large pulley CSS keyframes not active on hover", width)
                page.mouse.move(0, 0)
                if "is-hovering" in (art.get_attribute("class") or ""):
                    fail("hover animation did not reset on exit", width)
                if art.locator(".eq-large-rotor").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="none":
                    fail("rotor animation persists outside sheet hover", width)
                play_button.click()
                if "is-playing" not in (art.get_attribute("class") or ""):
                    fail("touch replay button did not start animation", width)
                if "eq-belt-forward" not in art.locator(".eq-belt-upper").evaluate(
                    "(el) => getComputedStyle(el).animationName"):
                    fail("belt-motion animation not active on replay", width)
                # Record an early state without allowing a screenshot to complete the cycle.
                page.locator("#sheet-next").click()
                if page.locator("#sheet-visual .art-eqmount").count()!=0 or play_button.is_visible():
                    fail("sheet switching did not clear equatorial motion", width)
                page.locator("#sheet-prev").click()
                if page.locator("#sheet-visual .art-eqmount.is-playing").count()!=0:
                    fail("animation was not reset when reopening sheet", width)
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
            page.locator("#sheet-prev").click()
            if page.locator("#sheet-title").inner_text().strip() != "DIY Automatic Equatorial Mount":
                fail("reverse navigation did not reach the hardware sheet", width)
            page.locator("#sheet-close").click()
            if errors: fail("JavaScript error after sheet controls: "+repr(errors), width)
        print("QA_PASS",width,"cards",len(boxes),"width",metrics["scrollWidth"],flush=True)
        page.close()
    browser.close()

print("QA_COMPLETED",len(WIDTHS),"viewport widths, concept visuals and filters")
