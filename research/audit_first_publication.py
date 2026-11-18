"""Audit every atlas book against public Goodreads work-level publication metadata.
Book/edition publicationTime is deliberately never used as a work's first date.
Fetches are resumable; source identities, dates, conflicts and errors are retained.
"""
import concurrent.futures,datetime,html,json,re,time,urllib.request,subprocess
from pathlib import Path
from refresh_book_assets import manifest,title_match,author_match
R=Path(__file__).parent
OUT=R/'goodreads-first-publication.json'

def read_book(b):
 result=dict(title=b['title'],author=b['author'],checked_at='2026-11-18')
 if not b['goodreads']:return b['key'],dict(result,status='no_direct_goodreads_link')
 url=b['goodreads'][0];result['source']=html.unescape(url)
 try:
  if b.get('transport')=='curl':
   s=subprocess.run(['curl','-L','--fail','--silent','--show-error','--max-time','25','-A','Mozilla/5.0',result['source']],capture_output=True,text=True,check=True).stdout
  else:
   with urllib.request.urlopen(urllib.request.Request(result['source'],headers={'User-Agent':'Mozilla/5.0 (compatible; UnreadAtlas bibliography review)'}),timeout=16) as response:s=response.read().decode('utf-8')
  m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',s,re.S)
  if not m:return b['key'],dict(result,status='no_work_metadata')
  state=json.loads(m.group(1))['props']['pageProps']['apolloState']
  ref=next((v['__ref'] for k,v in state['ROOT_QUERY'].items() if k.startswith('getBookByLegacyId') and isinstance(v,dict) and '__ref' in v),None)
  if not ref:return b['key'],dict(result,status='no_public_book_metadata')
  book=state[ref];work=state.get(book.get('work',{}).get('__ref'),{})
  contributors=[book.get('primaryContributorEdge',{})]+book.get('secondaryContributorEdges',[])
  authors=[state.get(c.get('node',{}).get('__ref'),{}).get('name','') for c in contributors if c.get('role')=='Author']
  title=book.get('title','');clean=re.sub(r'\s*\([^)]*\)\s*$','',title)
  result.update(matched_title=title,matched_authors=authors,original_title=work.get('details',{}).get('originalTitle'),work_url=work.get('details',{}).get('webUrl'))
  stamp=work.get('details',{}).get('publicationTime')
  visible=re.search(r'<p data-testid="publicationInfo">(.*?)</p>',s,re.S)
  visible=html.unescape(re.sub('<[^>]+>','',visible.group(1))) if visible else None
  result.update(work_publication_timestamp=stamp,displayed_first_publication=visible)
  if stamp is None:return b['key'],dict(result,status='no_first_publication_date')
  year=datetime.datetime.fromtimestamp(stamp/1000,datetime.timezone.utc).year
  result['year']=str(year)
  if not visible or not visible.startswith('First published') or str(year) not in visible:return b['key'],dict(result,status='date_requires_review')
  if not (title_match(b['title'],title) or title_match(b['title'],clean)) or not any(author_match(b['author'],a) for a in authors):return b['key'],dict(result,status='identity_requires_review')
  if year>2026:return b['key'],dict(result,status='future_date_requires_review')
  return b['key'],dict(result,status='work_first_publication_matched')
 except Exception as ex:return b['key'],dict(result,status='fetch_error',error_type=type(ex).__name__,error=str(ex))
 finally:time.sleep(.5)

def run():
 books=manifest();cache=json.loads(OUT.read_text()) if OUT.exists() else {}
 pending=[b for b in books if b['key'] not in cache]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for i,future in enumerate(concurrent.futures.as_completed([pool.submit(read_book,b) for b in pending]),1):
   key,row=future.result()
   cache[key]=row
   OUT.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
   if i%20==0:print('Reviewed',len(cache),'/',len(books),'work first dates',sum(r['status']=='work_first_publication_matched' for r in cache.values()),flush=True)
 print('COMPLETE',len(cache),flush=True)
if __name__=='__main__':run()
