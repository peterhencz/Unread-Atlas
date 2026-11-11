"""Retry catalogue candidates using known work IDs or title-only queries."""
import json,re,time,urllib.request,urllib.parse,unicodedata
from pathlib import Path
from difflib import SequenceMatcher
root=Path(__file__).parent;books=json.loads((root/'books.json').read_text());p=root/'catalogue-candidates.json';r=json.loads(p.read_text())
def norm(s):return re.sub('[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()
def author_score(a,b):return max(SequenceMatcher(None,norm(a),norm(b)).ratio(),SequenceMatcher(None,' '.join(sorted(norm(a).split())),' '.join(sorted(norm(b).split()))).ratio())
missing=[b for b in books if not r.get(b['author']+' | '+b['title'],{}).get('candidates')]
for start in range(0,len(missing),8):
 batch=missing[start:start+8];terms=[]
 for b in batch:
  terms.append('(title:"'+b['title'].replace('"','')+'")')
  for work in b['work']:terms.append('key:"'+work.replace('https://openlibrary.org','')+'"')
 url='https://openlibrary.org/search.json?'+urllib.parse.urlencode(dict(q=' OR '.join(terms),limit=500,fields='key,title,author_name,first_publish_year,edition_key'))
 try:
  with urllib.request.urlopen(url,timeout=45) as response:data=json.load(response)
 except Exception as e:print('ERROR',start,str(e),flush=True);continue
 for b in batch:
  cs=[]
  for d in data.get('docs',[]):
   ts=SequenceMatcher(None,norm(b['title']),norm(d.get('title',''))).ratio();a=max([author_score(b['author'],x) for x in d.get('author_name',[])]+[0])
   if ts>=.8 and a>=.75:cs.append(dict(record=d,title_similarity=round(ts,3),author_similarity=round(a,3)))
  cs.sort(key=lambda c:c['title_similarity']+c['author_similarity'],reverse=True)
  r[b['author']+' | '+b['title']]=dict(query_url=url,candidates=cs,checked_at='2026-11-11',status='candidate_only_original_date_unverified')
 p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('FALLBACK',start+len(batch),'/',len(missing),flush=True);time.sleep(1.1)
