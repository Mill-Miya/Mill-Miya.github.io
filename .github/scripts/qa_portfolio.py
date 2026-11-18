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
            eq_preview_seconds = card_art.locator(".eq-large-rotor").evaluate(
                "(el) => parseFloat(getComputedStyle(el).animationDuration)")
            if abs(eq_preview_seconds - 4.0) > .02:
                fail("equatorial listing preview must be exactly 1.6x (4s): "+str(eq_preview_seconds), width)
            # At end, the target reaches the reticle and all pulley arrows
            # return to their original orientation after whole turns.
            final = card_art.evaluate("""el => {
              const matrix = selector => {
                const n=el.querySelector(selector);
                const a=n.getAnimations().find(x=>x.animationName);
                a.currentTime=4000;
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
            # The listing plays 1.6x faster than the 6.4s detail sheet. At
            # 3906 ms both still move; at 4000 ms they finish together.
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
                before:snapshot(3906),
                end:snapshot(4000)
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
                if art.locator(".eq-large-rotor").count()!=1 or art.locator(".eq-belt-teeth").count()!=2:
                    fail("rotor or belt travel elements missing", width)
                eq_sheet_seconds=art.locator(".eq-large-rotor").evaluate(
                    "(el) => parseFloat(getComputedStyle(el).animationDuration)")
                if abs(eq_sheet_seconds - 6.4) > .02:
                    fail("equatorial detail sheet must keep normal 6.4s playback", width)
                if page.locator('.project-card[data-project="07"] .eq-belt-teeth').count()!=2:
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
                if "eq-belt-forward" not in art.locator(".eq-belt-upper").evaluate(
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
                sorava_media.hover()
                if "is-hovering" not in (sorava_card.get_attribute("class") or ""):
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
                page.locator('.project-card[data-project="01"] .project-title-button').click()
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
                if phases["transfer"][6]<.95 or phases["transfer"][5]>.05:
                    fail("Guest must see directional arrow instead of reticle while pointing: "+str(phases), width)
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
                if page.locator("#sheet-visual .art-sorava").count()!=0 or replay.is_visible():
                    fail("Sorava sheet failed to stop and clear on NEXT", width)
                page.locator("#sheet-prev").click()
                page.wait_for_function("""() =>
                  document.querySelector('#sheet-visual .art-sorava')?.classList.contains('is-playing')
                """, timeout=1500)
                if page.locator("#sheet-visual .art-sorava.is-hovering").count()!=0:
                    fail("Sorava NEXT/PREV autoplay requires pointer hover", width)
                page.locator("#sheet-close").click()
                page.emulate_media(reduced_motion="reduce")
                page.locator('.project-card[data-project="01"] .project-title-button').click()
                if page.locator(".sheet-motion-play").is_visible():
                    fail("Sorava reduced motion unexpectedly exposes replay", width)
                if page.locator("#sheet-visual .sorava-guest-received").evaluate(
                    "(el) => getComputedStyle(el).animationName")!="none":
                    fail("Sorava ignores reduced-motion settings", width)
                page.locator("#sheet-close").click()
            if errors: fail("JavaScript error after sheet controls: "+repr(errors), width)
        print("QA_PASS",width,"cards",len(boxes),"width",metrics["scrollWidth"],flush=True)
        page.close()
    browser.close()

print("QA_COMPLETED",len(WIDTHS),"viewport widths, concept visuals and filters")
