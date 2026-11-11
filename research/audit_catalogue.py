"""Resumable catalogue audit. Exact edition dates are not original publication dates."""
import json,time,urllib.request,urllib.parse,re,unicodedata
from pathlib import Path
from difflib import SequenceMatcher
root=Path(__file__).parent
books=json.loads((root/'books.json').read_text()); cp=root/'catalogue-candidates.json'; results=json.loads(cp.read_text()) if cp.exists() else {}
def norm(s):return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()
def fetch(url):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UnreadAtlas-catalogue-audit/1.0'}),timeout=45) as response:return json.load(response)
  except Exception:
   if attempt==2:raise
   time.sleep(3)
 time.sleep(1.1)
missing=[b for b in books if b['author']+' | '+b['title'] not in results]
for start in range(0,len(missing),12):
 batch=missing[start:start+12]
 terms=['(title:"'+b['title'].replace('"','')+'" AND author:"'+b['author'].replace('"','')+'")' for b in batch]
 url='https://openlibrary.org/search.json?'+urllib.parse.urlencode(dict(q=' OR '.join(terms),limit=300,fields='key,title,author_name,first_publish_year,edition_key'))
 try:data=fetch(url)
 except Exception as e:print('BATCH ERROR',start,str(e),flush=True);continue
 for b in batch:
  candidates=[]
  for d in data.get('docs',[]):
   ts=SequenceMatcher(None,norm(b['title']),norm(d.get('title',''))).ratio();a=max([SequenceMatcher(None,norm(b['author']),norm(x)).ratio() for x in d.get('author_name',[])]+[0])
   if ts>=.8 and a>=.75:candidates.append(dict(record=d,title_similarity=round(ts,3),author_similarity=round(a,3)))
  candidates.sort(key=lambda c:c['title_similarity']+c['author_similarity'],reverse=True)
  results[b['author']+' | '+b['title']]=dict(query_url=url,candidates=candidates,checked_at='2026-11-11',status='candidate_only_original_date_unverified')
 cp.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');print('SEARCH',len(results),'/',len(books),flush=True);time.sleep(1.1)
# Fetch up to three editions per strict title/author match, retaining raw metadata.
ep=root/'editions.json';editions=json.loads(ep.read_text()) if ep.exists() else {};keys=set()
for v in results.values():
 for c in v['candidates']:
  if c['title_similarity']>=.92 and c['author_similarity']>=.88:
   keys.update(c['record'].get('edition_key',[])[:3]);break
keys=sorted(keys-set(editions))
for start in range(0,len(keys),30):
 batch=keys[start:start+30];url='https://openlibrary.org/api/books?'+urllib.parse.urlencode(dict(bibkeys=','.join('OLID:'+k for k in batch),format='json',jscmd='data'))
 try:data=fetch(url)
 except Exception as e:print('EDITION ERROR',start,str(e),flush=True);continue
 for k,v in data.items():editions[k.removeprefix('OLID:')]=v
 ep.write_text(json.dumps(editions,ensure_ascii=False,indent=2)+'\n');print('EDITIONS',len(editions),flush=True);time.sleep(1.1)
print('DONE',flush=True)
