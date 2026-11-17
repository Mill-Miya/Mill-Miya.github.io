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
IMAGE_NAMES = {
    "sorava", "wallpipe-ar", "nova", "university-ai",
    "assignment-checker", "suwa-messe-2026",
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
        metrics = page.evaluate("""() => {
          const r = n => { const x=n.getBoundingClientRect();return {
            x:x.x,y:x.y,w:x.width,h:x.height,l:x.left,t:x.top,r:x.right,b:x.bottom
          }};
          const elements = [...document.querySelectorAll('.project-card')];
          const sections = [...document.querySelectorAll('main section')];
          const images = [...document.querySelectorAll('.project-card img')];
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
            images:images.map(n=>({src:n.getAttribute('src'),naturalWidth:n.naturalWidth,naturalHeight:n.naturalHeight,complete:n.complete})),
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
        if len(metrics["cards"]) != 6 or len(metrics["images"]) != 6:
            fail("lost project card or authentic image", width)
        slugs=set()
        for img in metrics["images"]:
            slugs.add(Path(img["src"]).stem)
            if not img["complete"] or img["naturalWidth"] <= 200 or img["naturalHeight"] <= 180:
                fail("unloaded actual screenshot "+str(img), width)
        if slugs != IMAGE_NAMES: fail("unexpected screenshot files: "+repr(slugs), width)
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
            if page.locator('.project-card:visible').count()!=6:
                fail("All filter does not restore all six projects", width)
            if page.locator('#visible-count').inner_text().strip()!="06":
                fail("filter counter incorrect", width)
        print("QA_PASS",width,"cards",len(boxes),"width",metrics["scrollWidth"],flush=True)
        page.close()
    browser.close()

print("QA_COMPLETED",len(WIDTHS),"viewport widths, authentic images and filters")
