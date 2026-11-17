from pathlib import Path
import base64
import re
import shutil
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import sys
BASE=Path(__file__).resolve().parents[1]
ROOT=BASE if (BASE/'index.html').is_file() else BASE/'site-v2'
OUT=BASE/'qa'
WIDTHS=[320,360,375,390,430,540,630,768,820,1024,1280,1440]
links=[
'https://mill-miya.github.io/SkyShare/',
'https://mill-miya.github.io/wallpipe-ar/',
'https://mill-miya.github.io/nova-visual-playground/visual-playground/',
'https://mill-miya.github.io/assignment-checker/',
'https://mill-miya.github.io/suwa-messe-2026/'
]
def inline_local_assets():
    # The sandbox blocks browser network and file navigation. Render identical source
    # with each local image inlined as a data URI; CSS and JS bytes remain unmodified.
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    css=(ROOT/'style.css').read_text(encoding='utf-8')
    js=(ROOT/'app.js').read_text(encoding='utf-8')
    html=html.replace('<link rel="stylesheet" href="style.css?v=1">','<style>'+css+'</style>')
    html=html.replace('<script defer src="app.js?v=1"></script>','')
    def asset_rewrite(match):
        name=match.group(1)
        data=(ROOT/name).read_bytes()
        mime='image/svg+xml' if name.endswith('.svg') else 'image/webp'
        return 'src="data:'+mime+';base64,'+base64.b64encode(data).decode('ascii')+'"'
    return re.sub(r'src="(assets/[^"]+)"',asset_rewrite,html)

RENDER=inline_local_assets()
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
 for w in WIDTHS:
  page=browser.new_page(viewport={'width':w,'height':844 if w<700 else 900},device_scale_factor=1,reduced_motion='reduce')
  errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
  page.set_content(RENDER,wait_until='load')
  page.add_script_tag(content=(ROOT/'app.js').read_text(encoding='utf-8'))
  assert not errors,(w,'JS errors',errors)
  assert page.locator('[data-project]').count()==6,(w,'project count')
  for im in page.locator('main img').all():
   im.scroll_into_view_if_needed();im.evaluate('(img)=>img.decode()')
  page.evaluate('window.scrollTo(0,0)')
  page.wait_for_timeout(65)
  metrics=page.evaluate('''() => {
   const rect=(n)=>{const r=n.getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}};
   const cards=[...document.querySelectorAll('[data-project]')];
   const images=[...document.querySelectorAll('main img')];
   const nav=[...document.querySelectorAll('.nav a')].filter(n=>getComputedStyle(n).display!=='none');
   const inside=[...document.querySelectorAll('a[href^="#"]')].map(a=>a.getAttribute('href').substring(1));
   const hero=document.querySelector('.hero');
   return {
    scrollWidth:document.documentElement.scrollWidth,innerWidth:innerWidth,
    imageDims:images.map(i=>[i.naturalWidth,i.naturalHeight,i.complete]),
    title:rect(document.querySelector('#hero-title')),plate:rect(document.querySelector('.identity-plate')),
    headerLogo:rect(document.querySelector('.wordmark')),nav:nav.map(rect),
    cards:cards.map(rect),internalBad:inside.filter(id=>!document.getElementById(id)),
    liveLinks:[...document.querySelectorAll('a[href^="https://mill-miya.github.io/"]')].map(a=>a.href),
    heroHeight:rect(hero).height,viewHeight:innerHeight,
   }
  }''')
  assert metrics['scrollWidth']<=w+1,(w,'horizontal overflow',metrics['scrollWidth'])
  assert not metrics['internalBad'],(w,'broken local anchors',metrics['internalBad'])
  assert all(a>100 and b>100 and c for a,b,c in metrics['imageDims']),(w,'broken real image',metrics['imageDims'])
  assert metrics['headerLogo']['right']<metrics['nav'][0]['left']-3,(w,'header overlap',metrics['headerLogo'],metrics['nav'])
  assert metrics['title']['left']>=-1 and metrics['title']['right']<=w+1,(w,'hero title overflow',metrics['title'])
  assert metrics['plate']['left']>=-1 and metrics['plate']['right']<=w+1,(w,'hero visual overflow',metrics['plate'])
  for x in metrics['cards']:
   assert x['left']>=-1 and x['right']<=w+1,(w,'project overflow',x)
  for l in links: assert l in metrics['liveLinks'],(w,'demo link missing',l)
  assert page.locator('a').filter(has_text='Source').count()==0
  if w in (320,390,630,820,1440):
   page.screenshot(path=str(OUT/f'full_{w}.png'),full_page=True,animations='disabled')
   page.screenshot(path=str(OUT/f'top_{w}.png'),full_page=False,animations='disabled')
  for filt,num in [('web',5),('ai',2),('engineering',2),('all',6)]:
   page.locator('button[data-filter="'+filt+'"]').click()
   assert page.locator('[data-project]:visible').count()==num,(w,filt,'visible count')
   assert page.locator('#visible-count').inner_text().strip()==str(num).zfill(2),(w,filt,'label')
   assert page.locator('button[data-filter="'+filt+'"]').get_attribute('aria-pressed')=='true'
  print('PASS',w,'hero',round(metrics['heroHeight']),'no overflow / 6 images / filters')
  page.close()
 browser.close()
print('ALL WIDTHS PASS',len(WIDTHS))
