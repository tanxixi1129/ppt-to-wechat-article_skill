#!/usr/bin/env python3
"""重新导出公众号图片。
用法：
  python3 render.py                         # 用 排版源稿.html（自动载入 photos/p1.jpg … p10.jpg + photos/qrcode.png）
  python3 render.py 排版源稿-已编辑.html      # 用浏览器“保存编辑后的HTML”得到的文件（含已嵌入的照片与改字）
  python3 render.py --scale 1.2             # 导出 1080 宽高清版
依赖：pip install playwright；浏览器用 python3 -m playwright install chromium，或本机已装的 Google Chrome。
注意：输入的HTML需放在本文件夹（与 assets/、photos/ 同级）。输出到 成品图片/。"""
import sys, pathlib, argparse
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser(); ap.add_argument('html',nargs='?',default='排版源稿.html'); ap.add_argument('--scale',type=float,default=1.0)
a=ap.parse_args()
root=pathlib.Path(__file__).resolve().parent; out=root/'成品图片'; out.mkdir(exist_ok=True)
src=pathlib.Path(a.html); src=src if src.is_absolute() else (pathlib.Path.cwd()/src)
if not src.exists(): src=root/a.html
if not src.exists(): sys.exit(f'找不到 {a.html}')
def launch(p):
    for kw in ({},{'channel':'chrome'},{'executable_path':'/usr/bin/google-chrome'}):
        try: return p.chromium.launch(**kw)
        except Exception: pass
    sys.exit('未找到可用的 Chromium/Chrome：请运行 python3 -m playwright install chromium')
def ready(pg):
    pg.wait_for_load_state('networkidle'); pg.evaluate('document.fonts.ready')
    pg.wait_for_function("[...document.images].every(i=>!i.getAttribute('src')||i.complete)"); pg.wait_for_timeout(500)
with sync_playwright() as p:
    b=launch(p)
    pg=b.new_page(viewport={'width':900,'height':1200},device_scale_factor=a.scale)
    pg.goto(src.resolve().as_uri()+'?export=1'); ready(pg)
    filled=pg.evaluate("document.querySelectorAll('.ph.filled').length"); total=pg.evaluate("document.querySelectorAll('.ph:not([data-removed])').length"); removed=pg.evaluate("document.querySelectorAll('.ph[data-removed]').length")
    pg.locator('#page').screenshot(path=str(out/'公众号推文长图.png'))
    groups=pg.evaluate('''()=>{const g={};document.querySelectorAll('.seg').forEach(s=>{const k=s.dataset.seg.slice(0,2);const r=s.getBoundingClientRect();const y=r.top+scrollY;
      if(!g[k])g[k]={y:y,h:0};g[k].h=y+r.height-g[k].y;});return g;}''')
    for old in out.glob('分段*.png'): old.unlink()
    for i,(k,v) in enumerate(sorted(groups.items()),1):
        fn=out/f'分段{i:02d}.png'
        pg.screenshot(path=str(fn),clip={'x':0,'y':v['y'],'width':900,'height':v['h']},full_page=True)
        print(fn.name,'900x%d'%round(v['h']))
    c=b.new_page(viewport={'width':1000,'height':1000},device_scale_factor=a.scale)
    c.goto((root/'封面源稿.html').as_uri()); ready(c)
    c.locator('#wide').screenshot(path=str(out/'封面-横版900x383.png'))
    c.locator('#sq').screenshot(path=str(out/'封面-方形500x500.png'))
    b.close()
print(f'照片位已填 {filled}/{total}' + (f'（已删除 {removed} 个照片位，不导出）' if removed else '') + f'；输出 -> {out}')
