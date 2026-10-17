"""Capture the actual local animation player and its controls for visual review."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'outputs/lumine-teaching-walk-20261016'
E=ART/'evidence';E.mkdir(exist_ok=True)
errors=[];checks=[]
with sync_playwright() as p:
 try:browser=p.chromium.launch(headless=True)
 except Exception:browser=p.chromium.launch(channel='msedge',headless=True)
 page=browser.new_page(viewport={'width':1440,'height':1000})
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto((ART/'index.html').as_uri());page.wait_for_function("document.querySelector('#info').textContent.includes('身体图元')")
 page.locator('#play').click()
 for mode in ['fit','source']:
  page.select_option('#mode',mode)
  for i in range(4):
   if i:page.click('#next')
   page.wait_for_timeout(40)
   label=page.locator('#info').inner_text()
   page.screenshot(path=str(E/f'{mode}-{i}.png'))
   checks.append({'mode':mode,'label':label})
 page.check('#mirror');page.check('#light');page.wait_for_timeout(40)
 page.screenshot(path=str(E/'source-mirror-light.png'))
 page.uncheck('#mirror');page.uncheck('#light');page.select_option('#mode','fit')
 page.check('#idle');page.click('#play');page.wait_for_timeout(500)
 page.screenshot(path=str(E/'fit-linked-loop.png'))
 assert not errors,errors
 browser.close()
(E/'browser-checks.json').write_text(json.dumps({'checks':checks,'errors':errors,'scope':'local artwork player; not game/device acceptance'},ensure_ascii=False,indent=2),encoding='utf-8')
print('art player controls and 10 screenshots verified')
