"""Find translated titles indexed under the original work; require exact edition titles."""
import sys,runpy,json,time,urllib.request,urllib.parse
from pathlib import Path
root=Path(__file__).parent;sys.argv=['apply_metadata.py','--dry-run'];g=runpy.run_path(str(root/'apply_metadata.py'))
r=json.loads((root/'catalogue-candidates.json').read_text());books=json.loads((root/'books.json').read_text());missing=[b for b in books if not g['choose'](b['title'],b['author'])]
for start in range(0,len(missing),8):
 batch=missing[start:start+8];q=' OR '.join('('+g['norm'](b['title']+' '+b['author'])+')' for b in batch)
 url='https://openlibrary.org/search.json?'+urllib.parse.urlencode(dict(q=q,limit=300,fields='key,title,author_name,edition_key'))
 try:
  with urllib.request.urlopen(url,timeout=40) as response:data=json.load(response)
 except Exception as e:print('ERROR',start,str(e),flush=True);continue
 for b in batch:
  key=b['author']+' | '+b['title'];item=r[key];known={c['record']['key'] for c in item['candidates']}
  for record in data.get('docs',[]):
   if record['key'] in known:continue
   if any(g['same_author'](b['author'],a) for a in record.get('author_name',[])):
    item['candidates'].append(dict(record=record,title_similarity=0,author_similarity=1,requires_edition_title_match=True));known.add(record['key'])
  item['translation_query_url']=url
 (root/'catalogue-candidates.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('TRANSLATIONS',start+len(batch),'/',len(missing),flush=True);time.sleep(1.1)
