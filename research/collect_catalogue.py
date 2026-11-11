"""Collect catalogue matches as research candidates, never as verified original dates.
Run from repository root. Cached public API responses make the audit resumable.
"""
import json,time,urllib.request,urllib.parse,unicodedata,re
from pathlib import Path
from difflib import SequenceMatcher
root=Path(__file__).parent
books=json.loads((root/'books.json').read_text());cache=root/'catalogue-candidates.json'
results=json.loads(cache.read_text()) if cache.exists() else {}
def norm(s):return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()
for i,b in enumerate(books):
 key=b['author']+' | '+b['title']
 if key in results:continue
 query=urllib.parse.urlencode(dict(title=b['title'],author=b['author'],limit=5,fields='key,title,author_name,first_publish_year,edition_key'))
 url='https://openlibrary.org/search.json?'+query
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'UnreadAtlas-bibliography-audit/1.0'})
  with urllib.request.urlopen(req,timeout=25) as response:data=json.load(response)
  candidates=[]
  for d in data.get('docs',[]):
   title=SequenceMatcher(None,norm(b['title']),norm(d.get('title',''))).ratio()
   author=max([SequenceMatcher(None,norm(b['author']),norm(a)).ratio() for a in d.get('author_name',[])]+[0])
   candidates.append(dict(record=d,title_similarity=round(title,3),author_similarity=round(author,3)))
  results[key]=dict(query_url=url,candidates=candidates,checked_at='2026-11-11',status='candidate_only_original_date_unverified')
 except Exception as e:
  print('ERROR',i,type(e).__name__,flush=True);time.sleep(3);continue
 cache.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
 if len(results)%20==0:print('Collected',len(results),'/',len(books),flush=True)
 time.sleep(1.1)
print('COMPLETE',len(results),flush=True)
