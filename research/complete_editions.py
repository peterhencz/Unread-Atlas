"""Retrieve additional editions only where the initial edition match was insufficient."""
import sys,runpy,json,time,urllib.request,urllib.parse
from pathlib import Path
sys.argv=['apply_metadata.py','--dry-run'];g=runpy.run_path(str(Path(__file__).parent/'apply_metadata.py'));root=Path(__file__).parent
editions=json.loads((root/'editions.json').read_text());keys=set()
for b in json.loads((root/'books.json').read_text()):
 if g['choose'](b['title'],b['author']):continue
 for c in g['candidates'].get(b['author']+' | '+b['title'],{}).get('candidates',[]):
  r=c['record']
  if (g['same_title'](b['title'],r.get('title','')) or c.get('requires_edition_title_match')) and any(g['same_author'](b['author'],a) for a in r.get('author_name',[])):
   keys.update(r.get('edition_key',[])[:8])
keys=sorted(keys-set(editions));print('Additional records',len(keys),flush=True)
for start in range(0,len(keys),30):
 url='https://openlibrary.org/api/books?'+urllib.parse.urlencode(dict(bibkeys=','.join('OLID:'+k for k in keys[start:start+30]),format='json',jscmd='data'))
 try:
  with urllib.request.urlopen(url,timeout=45) as response:data=json.load(response)
 except Exception as e:print('ERROR',start,str(e),flush=True);continue
 for k,v in data.items():editions[k[5:]]=v
 (root/'editions.json').write_text(json.dumps(editions,ensure_ascii=False,indent=2)+'\n');print('ADDITIONAL',start+len(data),'/',len(keys),flush=True);time.sleep(1.1)
