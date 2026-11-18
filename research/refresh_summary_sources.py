"""Fetch public, identity-checked synopsis metadata for editorial follow-up.
Raw descriptions stay in the ignored local cache, never the public evidence file.
"""
import concurrent.futures,html,json,re,urllib.request
from pathlib import Path
from refresh_book_assets import manifest,title_match,author_match
R=Path(__file__).resolve().parent
OUT=R/'editorial-source-cache.json'
def run():
 done={e['author']+' | '+e['title'] for e in json.loads((R/'editorial-summaries.json').read_text())['entries']}
 identities={v['key']:v for v in json.loads((R/'publication-identity-review.json').read_text())}
 cache=json.loads(OUT.read_text()) if OUT.exists() else {}
 def fetch(b):
  entry=dict(title=b['title'],author=b['author'])
  if not b['goodreads']:return b['key'],dict(entry,status='no_direct_page')
  url=html.unescape(b['goodreads'][0]);entry['source']=url
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; UnreadAtlas editorial review)'})
   with urllib.request.urlopen(req,timeout=25) as response:s=response.read().decode()
   m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',s,re.S)
   if not m:return b['key'],dict(entry,status='no_public_metadata')
   state=json.loads(m[1])['props']['pageProps']['apolloState'];ref=next((v['__ref'] for k,v in state.get('ROOT_QUERY',{}).items() if k.startswith('getBookByLegacyId') and isinstance(v,dict) and '__ref' in v),None)
   if not ref:return b['key'],dict(entry,status='no_public_metadata')
   book=state[ref];title=book.get('title','');edges=[book.get('primaryContributorEdge',{})]+book.get('secondaryContributorEdges',[])
   authors=[state.get(e.get('node',{}).get('__ref'),{}).get('name','') for e in edges if e.get('role')=='Author']
   entry.update(matched_title=title,matched_authors=authors)
   exact=title_match(b['title'],title) and any(author_match(b['author'],a) for a in authors);alias=identities.get(b['key'],{})
   reviewed=alias.get('source')==url and alias.get('matched_title')==title and alias.get('matched_authors')==authors
   if not(exact or reviewed):return b['key'],dict(entry,status='identity_requires_review')
   raw=book.get('description') or '';entry['text']=re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]*>',' ',raw)))
   entry['status']='matched_synopsis' if entry['text'] else 'no_synopsis'
  except Exception as ex:entry.update(status='fetch_error',error=str(ex))
  return b['key'],entry
 pending=[b for b in manifest() if b['key'] not in done and b['key'] not in cache]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for i,(key,row) in enumerate(pool.map(fetch,pending),1):
   cache[key]=row;OUT.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
   if i%20==0:print('Checked',i,'/',len(pending),flush=True)
 print('Completed',len(cache),flush=True)
if __name__=='__main__':run()
