"""Refresh matching cover candidates; keep provenance and do not guess book identities."""
import re,json,html,unicodedata,time,urllib.request,urllib.parse
from pathlib import Path
from difflib import SequenceMatcher
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'research'
def norm(s):return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()).strip()
def title_match(a,b):return norm(a)==norm(b) or (len(norm(a))>12 and norm(b).startswith(norm(a)+' '))
def author_match(a,b):return sorted(norm(a).split())==sorted(norm(b).split()) or SequenceMatcher(None,norm(a),norm(b)).ratio()>=.92
def manifest():
 out=[]
 for row in re.findall(r'<tr>.*?</tr>',(ROOT/'index.html').read_text(),re.S):
  m=re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>',row,re.S)
  if not m:continue
  title,author=map(html.unescape,m.groups());key=author+' | '+title
  out.append(dict(key=key,title=title,author=author,goodreads=re.findall(r'https://(?:www\.)?goodreads.com/(?:en/)?book/show/[^"< ]+',row),cover=re.findall(r'<img[^>]+src="([^"]+)"',row),ol_editions=re.findall(r'https://openlibrary.org/books/(OL\d+M)',row)))
 return out
def fetch_json(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UnreadAtlas-metadata-refresh/1.0 (personal literary atlas)'}),timeout=20) as r:return json.load(r)
def run_covers():
 books=manifest();cachefile=R/'asset-refresh-covers.json';cache=json.loads(cachefile.read_text()) if cachefile.exists() else {}
 editions=json.loads((R/'editions.json').read_text());candidates=json.loads((R/'catalogue-candidates.json').read_text())
 missing=[b for b in books if not b['cover']]
 google_available=True
 for i,b in enumerate(missing):
  if b['key'] in cache:continue
  entry=dict(title=b['title'],author=b['author'],checked_at='2026-11-18',candidates=[],attempts=[])
  # Existing checked editions can provide extra covers, without another fuzzy work lookup.
  for k in b['ol_editions']:
   e=editions.get(k,{})
   if title_match(b['title'],e.get('title','')) and any(author_match(b['author'],a['name']) for a in e.get('authors',[])):
    cover=e.get('cover',{}).get('large') or e.get('cover',{}).get('medium')
    if cover:entry['candidates'].append(dict(provider='openlibrary-edition',image=cover,source='https://openlibrary.org/books/'+k,title=e['title'],authors=[a['name'] for a in e.get('authors',[])]))
  # Fresh Google Books query, falling back gracefully when its public quota is exhausted.
  if google_available:
   url='https://www.googleapis.com/books/v1/volumes?'+urllib.parse.urlencode(dict(q='intitle:"'+b['title']+'" inauthor:"'+b['author']+'"',maxResults=5,printType='books'))
   try:
    data=fetch_json(url);entry['attempts'].append(dict(provider='google-books',status='searched',query_url=url))
    for v in data.get('items',[]):
     info=v.get('volumeInfo',{});cover=info.get('imageLinks',{}).get('thumbnail') or info.get('imageLinks',{}).get('smallThumbnail')
     if cover and title_match(b['title'],info.get('title','')) and any(author_match(b['author'],a) for a in info.get('authors',[])):
      entry['candidates'].append(dict(provider='google-books',image=cover.replace('http:','https:'),source='https://books.google.com/books?id='+v['id'],title=info['title'],authors=info.get('authors',[])))
   except Exception as ex:
    entry['attempts'].append(dict(provider='google-books',status='error',error=str(ex)))
    if '429' in str(ex) or '403' in str(ex):google_available=False
   time.sleep(.5)
  else:entry['attempts'].append(dict(provider='google-books',status='public_api_quota_unavailable'))
  if not entry['candidates']:
   url='https://openlibrary.org/search.json?'+urllib.parse.urlencode(dict(title=b['title'],author=b['author'],limit=5,fields='key,title,author_name,cover_i'))
   try:
    data=fetch_json(url);entry['attempts'].append(dict(provider='openlibrary-search',status='searched',query_url=url))
    for v in data.get('docs',[]):
     if v.get('cover_i') and title_match(b['title'],v.get('title','')) and any(author_match(b['author'],a) for a in v.get('author_name',[])):
      entry['candidates'].append(dict(provider='openlibrary-search',image='https://covers.openlibrary.org/b/id/'+str(v['cover_i'])+'-L.jpg?default=false',source='https://openlibrary.org'+v['key'],title=v['title'],authors=v['author_name']))
   except Exception as ex:entry['attempts'].append(dict(provider='openlibrary-search',status='error',error=str(ex)))
   time.sleep(1.05)
  entry['status']='matched_cover_candidate' if entry['candidates'] else 'no_verified_cover'
  cache[b['key']]=entry;cachefile.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
  if (i+1)%10==0:print('Covers checked',i+1,'/',len(missing),'matched',sum(bool(v['candidates']) for v in cache.values()),'Google API',google_available,flush=True)
 print('COVER REVIEW COMPLETE',len(missing),flush=True)
if __name__=='__main__':
 import sys
 books=manifest();(R/'asset-manifest.json').write_text(json.dumps(books,ensure_ascii=False,indent=2)+'\n')
 print('Entries',len(books),'missing Goodreads',sum(not b['goodreads'] for b in books),'missing covers',sum(not b['cover'] for b in books),flush=True)
 if '--covers' in sys.argv:run_covers()
