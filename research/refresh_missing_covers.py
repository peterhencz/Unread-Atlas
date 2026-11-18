"""Refresh missing covers from identity-checked, public Goodreads book metadata.
Images are stored unmodified. Dimensions and per-image provenance are recorded.
Run apply_cover_followup.py after reviewing the audit and any manual additions.
"""
import concurrent.futures,hashlib,html,json,re,subprocess,time,urllib.request
from pathlib import Path
from refresh_book_assets import manifest,title_match,author_match
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'research';OUT=R/'cover-followup-audit.json'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; UnreadAtlas cover metadata review)'}

def image_asset(title,author,url):
 if any(v in url.lower() for v in ['nophoto','no-cover','nocover','default-book','photo/nophoto']):raise ValueError('Generic placeholder image')
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=20) as response:
  data=response.read(5_000_001);mime=response.headers.get_content_type()
 if len(data)>5_000_000:raise ValueError('Image exceeds 5 MB')
 if data[:3]==b'\xff\xd8\xff':ext='.jpg'
 elif data[:8]==b'\x89PNG\r\n\x1a\n':ext='.png'
 elif data[:4]==b'RIFF' and data[8:12]==b'WEBP':ext='.webp'
 else:raise ValueError('Not a supported image')
 relative='assets/covers/followup-'+hashlib.sha256((author+'|'+title).encode()).hexdigest()[:14]+ext
 p=ROOT/relative;p.write_bytes(data)
 check=subprocess.run(['sips','-g','pixelWidth','-g','pixelHeight',str(p)],capture_output=True,text=True,check=True)
 w=int(re.search(r'pixelWidth:\s*(\d+)',check.stdout).group(1));h=int(re.search(r'pixelHeight:\s*(\d+)',check.stdout).group(1))
 if w<80 or h<110 or not .35<=w/h<=1.05:
  p.unlink();raise ValueError('Insufficient cover geometry: '+str((w,h)))
 return dict(local_path=relative,width=w,height=h,bytes=len(data),content_type=mime,sha256=hashlib.sha256(data).hexdigest())

def run_book(b,identities,date_search):
 result=dict(title=b['title'],author=b['author'],checked_at='2026-11-18',attempts=[])
 urls=list(dict.fromkeys(b['goodreads']))[:1]
 searched=date_search.get(b['key'],{})
 if not urls and searched.get('matched_title') and searched.get('source'):urls=[searched['source']]
 if not urls:return b['key'],dict(result,status='no_direct_book_page')
 url=html.unescape(urls[0]);result['source']=url
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=20) as response:s=response.read().decode('utf-8')
  m=re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',s,re.S)
  if not m:return b['key'],dict(result,status='no_public_book_metadata')
  state=json.loads(m.group(1))['props']['pageProps']['apolloState']
  ref=next((v['__ref'] for k,v in state.get('ROOT_QUERY',{}).items() if k.startswith('getBookByLegacyId') and isinstance(v,dict) and '__ref' in v),None)
  if not ref:return b['key'],dict(result,status='no_public_book_metadata')
  book=state[ref];title=book.get('title','');edges=[book.get('primaryContributorEdge',{})]+book.get('secondaryContributorEdges',[])
  authors=[state.get(e.get('node',{}).get('__ref'),{}).get('name','') for e in edges if e.get('role')=='Author']
  result.update(matched_title=title,matched_authors=authors)
  alias=identities.get(b['key'],{})
  exact=title_match(b['title'],title) and any(author_match(b['author'],a) for a in authors)
  reviewed=alias.get('source')==url and alias.get('matched_title')==title and alias.get('matched_authors')==authors
  if not(exact or reviewed):return b['key'],dict(result,status='identity_requires_review')
  image=book.get('imageUrl')
  if not image:return b['key'],dict(result,status='no_cover_in_book_metadata')
  result.update(image_url=image,isbn=book.get('details',{}).get('isbn13') or book.get('details',{}).get('isbn'),provider='goodreads-book-page',identity_basis='Exact title and author match' if exact else 'Previously reviewed same-work title/author variant')
  result.update(image_asset(b['title'],b['author'],image));result['status']='cover_downloaded'
 except Exception as ex:result.update(status='fetch_error',error_type=type(ex).__name__,error=str(ex))
 finally:time.sleep(.5)
 return b['key'],result

def run():
 books=manifest();missing=[b for b in books if not b['cover']]
 # Chile first, then the rest of the missing-cover list.
 chile={'The Place Without Limits','The Obscene Bird of Night','The House of the Spirits','By Night in Chile','The Shrouded Woman'}
 missing.sort(key=lambda b:b['title'] not in chile)
 identities={v['key']:v for v in json.loads((R/'publication-identity-review.json').read_text())}
 dates=json.loads((R/'goodreads-date-search.json').read_text());cache=json.loads(OUT.read_text()) if OUT.exists() else {}
 pending=[b for b in missing if b['key'] not in cache]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  futures=[pool.submit(run_book,b,identities,dates) for b in pending]
  for i,future in enumerate(concurrent.futures.as_completed(futures),1):
   k,row=future.result();cache[k]=row;OUT.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
   if i%20==0:print('Missing covers checked',len(cache),'downloaded',sum(v['status']=='cover_downloaded' for v in cache.values()),flush=True)
 print('COMPLETE',len(cache),'downloaded',sum(v['status']=='cover_downloaded' for v in cache.values()),flush=True)
if __name__=='__main__':run()
