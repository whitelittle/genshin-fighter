import json, re, urllib.request
from concurrent.futures import ThreadPoolExecutor
urls = [
 'https://api.bilibili.com/x/v2/reply?type=1&oid=117434421878626&pn=1&ps=20&sort=0',
 'https://act.miyoushe.com/ys/ugc_community/level-detail/static/js/index.24789ec3.js',
 'https://act.miyoushe.com/ys/ugc_community/level-detail/static/js/679.cdaedcd8.js',
]
def get(url):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.bilibili.com/' if 'bilibili' in url else 'https://act.miyoushe.com/'})
  body=urllib.request.urlopen(req,timeout=20).read().decode()
  if 'bilibili' in url:
   d=json.loads(body); print(json.dumps({'site':'bilibili','code':d.get('code'),'page':(d.get('data') or {}).get('page'),'count':len((d.get('data') or {}).get('replies') or [])},ensure_ascii=False))
  else:
   from pathlib import Path
   Path(__file__).with_name(url.rsplit('/',1)[-1]).write_text(body,encoding='utf-8')
   print(json.dumps({'site':'miyoushe','paths': sorted(set(re.findall(r'[\"\']([^\"\']*(?:[Cc]omment|[Rr]eply|[Rr]eview)[^\"\']*)[\"\']',body)))[:50]},ensure_ascii=False))
 except Exception as e: print(type(e).__name__,str(e)[:100])
with ThreadPoolExecutor(max_workers=2) as p: list(p.map(get,urls))
