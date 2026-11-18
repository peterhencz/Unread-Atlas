"""Apply checked links and validated cover downloads without touching titles/dates/authors."""
from pathlib import Path
import re,json,html,urllib.request,hashlib,struct,time
R=Path(__file__).parent;ROOT=R.parent

def image_size(data):
 if data.startswith(b'\x89PNG'):return struct.unpack('>II',data[16:24])
 if data.startswith(b'\xff\xd8'):
  pos=2
  while pos<len(data)-10:
   if data[pos]!=255:pos+=1;continue
   marker=data[pos+1];pos+=2
   if marker in (0xD8,0xD9):continue
   length=int.from_bytes(data[pos:pos+2],'big')
   if marker in (0xC0,0xC1,0xC2):return (int.from_bytes(data[pos+5:pos+7],'big'),int.from_bytes(data[pos+3:pos+5],'big'))
   if length<2:break
   pos+=length
 return (0,0)

def download_covers():
 candidates=json.loads((R/'asset-refresh-covers.json').read_text())
 extra=json.loads((R/'goodreads-page-refresh.json').read_text())
 for key,v in extra.items():
  if v.get('status')=='goodreads_page_identity_verified' and v.get('image'):
   candidates.setdefault(key,dict(title=v['title'],author=v['author'],candidates=[]))['candidates'].append(dict(provider='goodreads',image=v['image'],source=v['url'],title=v['matched_title'],authors=v['matched_authors']))
 output=R/'cover-refresh-audit.json';audit=json.loads(output.read_text()) if output.exists() else {}
 dest=ROOT/'assets/covers';dest.mkdir(parents=True,exist_ok=True)
 for key,v in candidates.items():
  if key in audit:continue
  entry=dict(title=v['title'],author=v['author'],checked_at='2026-11-18',status='no_verified_cover',attempts=[])
  for c in v['candidates']:
   url=c['image']
   if 'covers.openlibrary.org' in url and 'default=false' not in url:url+='?default=false'
   try:
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'UnreadAtlas-cover-review/1.0'}),timeout=20) as response:
     data=response.read();contenttype=response.headers.get('Content-Type','')
    w,h=image_size(data)
    if not contenttype.startswith('image/') or min(w,h)<60 or len(data)<2000:raise ValueError('not a usable book cover')
    ext='.png' if data.startswith(b'\x89PNG') else '.jpg'
    file='assets/covers/'+hashlib.sha256(key.encode()).hexdigest()[:16]+ext
    (ROOT/file).write_bytes(data)
    entry.update(status='verified_identity_and_image',file=file,width=w,height=h,source=c['source'],remote_image=url,provider=c['provider'],matched_title=c['title'],matched_authors=c['authors']);break
   except Exception as ex:entry['attempts'].append(dict(url=url,error=str(ex)))
   time.sleep(.4)
  audit[key]=entry;output.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
 print('COVER DOWNLOADS',sum('file' in v for v in audit.values()),'of',len(audit),flush=True)

def apply():
 p=ROOT/'index.html';s=p.read_text()
 gr={v['key']:v for v in json.loads((R/'goodreads-refresh.json').read_text()) if v.get('url')}
 if (R/'reading-note-source-cache.json').exists():
  for v in json.loads((R/'reading-note-source-cache.json').read_text()):
   if v.get('source'):gr[v['key']]=dict(v,url=v['source'])
 for key,v in json.loads((R/'goodreads-page-refresh.json').read_text()).items():
  if v.get('url') and key not in gr:gr[key]=v
 covers=json.loads((R/'cover-refresh-audit.json').read_text());report=[];counts={'links_added':0,'covers_added':0}
 def update(m):
  row=m[0];book=re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>',row,re.S)
  if not book:return row
  title,author=map(html.unescape,book.groups());key=author+' | '+title;entry=dict(title=title,author=author)
  match=gr.get(key);old=bool(re.search(r'goodreads.com/(?:en/)?book/show/',row))
  if match and not old:
   row=re.sub(r'<a href="https://www.goodreads.com/search[^\"]*"[^>]*>Search Goodreads ↗</a>',lambda _: '<a href="'+match['url']+'" target="_blank" rel="noopener">Goodreads book page ↗</a>',row,count=1)
   counts['links_added']+=1;entry['goodreads_source']=match['url'];entry['goodreads_status']='title_author_verified'
  c=covers.get(key,{})
  if 'file' in c and 'class="nocover"' in row:
   cover='<a href="'+html.escape(c['source'],quote=True)+'" target="_blank" rel="noopener"><img src="'+c['file']+'" width="'+str(c['width'])+'" height="'+str(c['height'])+'" alt="Catalogue cover: '+html.escape(title,quote=True)+'" loading="lazy"></a>'
   row=re.sub(r'<td class="cover">.*?</td>',lambda _:'<td class="cover">\n'+cover+'\n</td>',row,count=1,flags=re.S)
   counts['covers_added']+=1;entry['cover_source']=c['source']
  report.append(entry);return row
 s=re.sub(r'<tr>.*?</tr>',update,s,flags=re.S);p.write_text(s)
 (R/'book-asset-refresh-audit.json').write_text(json.dumps(dict(checked_at='2026-11-18',changes=counts,entries=report),ensure_ascii=False,indent=2)+'\n')
 print(counts)
if __name__=='__main__':
 import sys
 if '--download' in sys.argv:download_covers()
 else:apply()
