#!/usr/bin/env python3
"""Capture *actual* public app screens; do not draw substitute application UIs."""
import os
import pathlib
import subprocess
import sys
import time
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "projects"
RAW = ROOT / "screenshots-raw"
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

SITES = [
    ("sorava", "https://mill-miya.github.io/SkyShare/"),
    ("wallpipe-ar", "https://mill-miya.github.io/wallpipe-ar/pipe-preview.html"),
    ("wallpipe-landing", "https://mill-miya.github.io/wallpipe-ar/"),
    ("nova", "https://mill-miya.github.io/nova-visual-playground/visual-playground/"),
    ("assignment-checker", "https://mill-miya.github.io/assignment-checker/"),
    ("suwa-messe-2026", "https://mill-miya.github.io/suwa-messe-2026/"),
]

def save_webp(original, dest):
    image = Image.open(original).convert("RGB")
    if image.width < 250 or image.height < 180:
        raise RuntimeError("Real screenshot too small; refusing to publish")
    image.save(dest, "WEBP", quality=86, method=6)
    return image.size

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=[
        "--use-gl=angle", "--use-angle=swiftshader", "--enable-webgl",
        "--disable-web-security", "--no-sandbox"
    ])
    try:
        for slug, url in SITES:
            page = browser.new_page(viewport={"width":1440,"height":900}, device_scale_factor=1,
                                     reduced_motion="reduce")
            errors=[]
            page.on("pageerror",lambda err: errors.append(str(err)))
            response=page.goto(url,wait_until="domcontentloaded",timeout=75000)
            if response is None or response.status>=400:
                raise RuntimeError("Published UI is unavailable: " + slug)
            try:
                page.wait_for_load_state("networkidle",timeout=12000)
            except Exception:
                pass  # Live astronomy/AR apps can maintain connections indefinitely.
            page.wait_for_timeout(2400 if slug!="wallpipe-ar" else 6200)
            body=page.locator("body").inner_text(timeout=8000)
            if not body.strip() or len(body.strip())<12:
                raise RuntimeError("Empty real application screen: "+slug)
            raw=RAW/(slug+".png")
            page.screenshot(path=str(raw),full_page=False,animations="disabled")
            size=save_webp(raw,OUT/(slug+".webp"))
            print("CAPTURED_REAL_SITE",slug,"status",response.status,"dimensions",size,
                  "page_errors",len(errors))
            page.close()
    finally:
        browser.close()

# Capture a native PySide6 window from the real University AI source repository.
# Default app settings are real; no fabricated university schedule or personal user data.
university_src=ROOT/".github"/"university-ai-src"
subprocess.run(["git","clone","--depth","1","https://github.com/Mill-Miya/university-ai.git",
                str(university_src)],check=True,stdout=subprocess.DEVNULL)
sys.path.insert(0,str(university_src))
os.environ["QT_QPA_PLATFORM"]="offscreen"
from PySide6.QtWidgets import QApplication
from university_ai.app.config import SettingsStore
from university_ai.ui.settings import SettingsDialog

class NoStartup:
    def enable(self): return False
    def disable(self): return False

app=QApplication([])
dialog=SettingsDialog(SettingsStore(ROOT/"screenshots-raw"/"defaults-not-stored.json"),NoStartup())
dialog.resize(580,390)
dialog.show()
app.processEvents()
time.sleep(0.3)
app.processEvents()
native=RAW/"university-ai-settings.png"
if not dialog.grab().save(str(native),"PNG"):
    raise RuntimeError("Real Qt settings window could not be captured")
if Image.open(native).width<300:
    raise RuntimeError("Native Qt capture too small")
# Place actual Qt window pixels on a quiet flat canvas; no simulated application UI.
native_img=Image.open(native).convert("RGB")
canvas=Image.new("RGB",(1440,900),(235,237,235))
left=(canvas.width-native_img.width)//2
top=(canvas.height-native_img.height)//2
canvas.paste(native_img,(left,top))
canvas.save(OUT/"university-ai.webp","WEBP",quality=88,method=6)
canvas.save(RAW/"university-ai-framed.png","PNG")
print("CAPTURED_REAL_QT_UI",native_img.size)
dialog.close()
