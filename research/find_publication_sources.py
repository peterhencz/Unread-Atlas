"""Search public Goodreads results for records lacking a direct book page.
Only an exact/established title and author identity match may supply a date.
"""
import concurrent.futures,html,json,re,time,urllib.parse,urllib.request,subprocess
from pathlib import Path
from refresh_book_assets import manifest,title_match,author_match
from audit_first_publication import read_book
R=Path(__file__).parent;OUT=R/'goodreads-date-search.json'
def search(b):
 result=dict(title=b['title'],author=b['author'],attempts=[],status='no_identity_match')
 try:
  url='https://www.goodreads.com/search?'+urllib.parse.urlencode({'q':b['title']})
  response=subprocess.run(['curl','-L','--fail','--silent','--show-error','--max-time','18','-A','Mozilla/5.0',url],capture_output=True,text=True,check=True)
  s=response.stdout
  result['query_url']=url
  for row in re.findall(r'<tr\b.*?</tr>',s,re.S):
   title=re.search(r'class="bookTitle"[^>]*href="([^"]+)"[^>]*>\s*<span[^>]*>(.*?)</span>',row,re.S)
   authors=re.findall(r'class="authorName"[^>]*>\s*<span[^>]*>(.*?)</span>',row,re.S)
   if not title:continue
   t=html.unescape(re.sub('<[^>]+>','',title.group(2)));authors=[html.unescape(re.sub('<[^>]+>','',a)) for a in authors]
   result['attempts'].append(dict(title=t,authors=authors))
   if title_match(b['title'],t) and any(author_match(b['author'],a) for a in authors):
    page='https://www.goodreads.com'+html.unescape(title.group(1)).split('?')[0]
    _,data=read_book(dict(b,goodreads=[page]));result.update(data);break
 except Exception as ex:result.update(status='fetch_error',error=str(ex))
 time.sleep(.5);return b['key'],result
if __name__=='__main__':
 cache=json.loads(OUT.read_text()) if OUT.exists() else {};pending=[b for b in manifest() if not b['goodreads'] and (b['key'] not in cache or cache[b['key']]['status']=='fetch_error')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for future in concurrent.futures.as_completed([pool.submit(search,b) for b in pending]):
   key,row=future.result();cache[key]=row;OUT.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
   if len(cache)%10==0:print('Title searches',len(cache),'dates',sum(r['status']=='work_first_publication_matched' for r in cache.values()),flush=True)
 print('SEARCH COMPLETE',len(cache),flush=True)
