"""Verify Goodreads book JSON-LD identities; collect direct links and cover URLs.
Only public, unauthenticated book pages are read; rate failures are recorded.
"""
import json,re,html,time,urllib.request
from pathlib import Path
from refresh_book_assets import manifest,norm,title_match,author_match
R=Path(__file__).parent
books=manifest();editions=json.loads((R/'editions.json').read_text());catalogue=json.loads((R/'catalogue-candidates.json').read_text())
output=R/'goodreads-page-refresh.json';records=json.loads(output.read_text()) if output.exists() else {}
pagecache={};started=time.time();google_note=False

def read_page(url):
 if url in pagecache:return pagecache[url]
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; UnreadAtlas metadata review)'}),timeout=18) as r:s=r.read().decode('utf-8')
  values=[]
  for v in re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',s,re.S):
   try:d=json.loads(v)
   except ValueError:continue
   values.extend(d if isinstance(d,list) else [d])
  d=next((d for d in values if d.get('@type')=='Book'),None)
  if not d:result={'status':'no_book_metadata'}
  else:
   authors=d.get('author',[]);authors=authors if isinstance(authors,list) else [authors]
   result=dict(status='book_metadata',title=d.get('name',''),authors=[a.get('name','') for a in authors if isinstance(a,dict)],image=d.get('image'),isbn=d.get('isbn'))
 except Exception as e:result=dict(status='fetch_error',error=str(e))
 pagecache[url]=result;time.sleep(.8);return result

def candidate_urls(b,web):
 urls=b['goodreads'][:1]
 if web.get(b['key'],{}).get('url'):urls.append(web[b['key']]['url'])
 keys=set(b['ol_editions'])
 for c in catalogue.get(b['key'],{}).get('candidates',[]):
  rec=c['record']
  if title_match(b['title'],rec.get('title','')) and any(author_match(b['author'],a) for a in rec.get('author_name',[])):keys.update(rec.get('edition_key',[])[:3])
 for k in sorted(keys):
  e=editions.get(k,{})
  if not title_match(b['title'],e.get('title','')) or not any(author_match(b['author'],a.get('name','')) for a in e.get('authors',[])):continue
  for gr in e.get('identifiers',{}).get('goodreads',[])[:2]:
   if str(gr).isdigit():urls.append('https://www.goodreads.com/book/show/'+str(gr))
 return list(dict.fromkeys(urls))[:3]

while time.time()-started<1800:
 try:webrows=json.loads((R/'goodreads-refresh.json').read_text());web={v['key']:v for v in webrows}
 except (FileNotFoundError,ValueError):webrows=[];web={}
 pending=[]
 for b in books:
  if b['cover'] and (b['goodreads'] or web.get(b['key'],{}).get('url')):continue
  if b['key'] in records:continue
  urls=candidate_urls(b,web)
  if urls:pending.append((b,urls))
 for b,urls in pending:
  result=dict(title=b['title'],author=b['author'],checked_at='2026-11-18',status='no_identity_match',attempts=[])
  for url in urls:
   data=read_page(url);result['attempts'].append(dict(url=url,**data))
   clean_title=re.sub(r'\s*\([^)]*\)','',data.get('title','')).strip()
   if data['status']=='book_metadata' and title_match(b['title'],clean_title) and any(author_match(b['author'],a) for a in data['authors']):
    result.update(status='goodreads_page_identity_verified',url=url,matched_title=data['title'],matched_authors=data['authors'],image=data.get('image'),isbn=data.get('isbn'));break
  records[b['key']]=result;output.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
  if len(records)%10==0:print('Goodreads pages checked',len(records),'verified',sum(v['status']=='goodreads_page_identity_verified' for v in records.values()),flush=True)
 if len(webrows)>=475:break
 time.sleep(2)
print('GOODREADS PAGE REVIEW COMPLETE',len(records),flush=True)
