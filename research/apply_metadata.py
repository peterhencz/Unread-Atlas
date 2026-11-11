"""Apply only identity-matched catalogue editions; retain unresolved cases in audit.json."""
import re,json,html,unicodedata,sys
from pathlib import Path
from difflib import SequenceMatcher
root=Path(__file__).parent
candidates=json.loads((root/'catalogue-candidates.json').read_text());editions=json.loads((root/'editions.json').read_text());originals={(x['author'],x['title']):x for x in json.loads((root/'original-years.json').read_text())}
def norm(value):return re.sub(r'[^a-z0-9]+',' ',unicodedata.normalize('NFKD',value).encode('ascii','ignore').decode().lower()).strip()
def same_author(a,b):
 return SequenceMatcher(None,norm(a),norm(b)).ratio()>=.88 or sorted(norm(a).split())==sorted(norm(b).split())
def same_title(a,b):
 a,b=norm(a),norm(b)
 return a==b or (len(a)>14 and b.startswith(a+' '))
def choose(title,author):
 pool=[]
 for candidate in candidates.get(author+' | '+title,{}).get('candidates',[]):
  record=candidate['record']
  if not (same_title(title,record.get('title','')) or candidate.get('requires_edition_title_match')) or not any(same_author(author,x) for x in record.get('author_name',[])):continue
  for key in record.get('edition_key',[])[:3]:
   edition=editions.get(key)
   if not edition:continue
   if candidate.get('requires_edition_title_match') and not same_title(title,edition.get('title','')):continue
   if edition.get('authors') and not any(same_author(author,x.get('name','')) for x in edition['authors']):continue
   year=re.search(r'\b(1\d{3}|20[0-2]\d)\b',edition.get('publish_date',''))
   if not year or int(year.group())>2026:continue
   pool.append((key,edition,year.group()))
 pool.sort(key=lambda x:not same_title(title,x[1].get('title','')))
 return pool[0] if pool else None
report=[]
def update(row):
 m=re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>(.*?)<div class="links">',row,re.S)
 if not m:return row
 title,author=map(html.unescape,m.group(1,2));existing_date=bool(re.search(r'\b(1\d{3}|20\d{2})\b',m.group(3)));chosen=choose(title,author);original=originals.get((author,title))
 entry=dict(title=title,author=author,checked_at='2026-11-11',existing_year=existing_date)
 if chosen:
  key,edition,year=chosen;url='https://openlibrary.org/books/'+key
  entry.update(edition_url=url,edition_title=edition['title'],edition_authors=[a['name'] for a in edition.get('authors',[])],edition_date=edition['publish_date'],publisher=[x['name'] for x in edition.get('publishers',[])],isbn=edition.get('identifiers',{}).get('isbn_13',[]),status='edition_identity_and_date_checked')
  extra='<a href="'+url+'" target="_blank" rel="noopener">Book edition ↗</a><br>'
  row=row.replace('<div class="links">','<div class="links">'+extra,1)
  if not existing_date and not original:
   date='<div class="publication"><a href="'+url+'" target="_blank" rel="noopener" title="'+html.escape(edition['title']+' — '+edition['publish_date'],quote=True)+'">Edition: '+year+'</a></div>'
   row=row.replace(m.group(0),m.group(0).replace(m.group(3)+'<div class="links">',date+m.group(3)+'<div class="links">'),1)
 else:
  entry['status']='unresolved_no_strict_edition_match'
  for candidate in candidates.get(author+' | '+title,{}).get('candidates',[]):
   record=candidate['record']
   if same_title(title,record.get('title','')) and any(same_author(author,a) for a in record.get('author_name',[])):
    url='https://openlibrary.org'+record['key'];entry['work_url']=url
    row=row.replace('<div class="links">','<div class="links"><a href="'+url+'" target="_blank" rel="noopener">Book record ↗</a><br>',1);break
 if original and not existing_date:
  date='<div class="publication"><a href="'+html.escape(original['source'],quote=True)+'" target="_blank" rel="noopener">First published: '+original['year']+'</a></div>'
  author_html='<div class="author">'+m.group(2)+'</div>';row=row.replace(author_html,author_html+date,1);entry['original_year']=original['year'];entry['original_source']=original['source']
 entry['missing_year']=not(existing_date or chosen or original)
 if entry['missing_year']:
  author_html='<div class="author">'+m.group(2)+'</div>';row=row.replace(author_html,author_html+'<div class="publication">Date not verified</div>',1)
 entry['missing_direct_link']=not bool(re.search(r'https://(?:www.goodreads.com/book/show/|openlibrary.org/(?:books|works)/)',row))
 report.append(entry);return row
p=root.parent/'index.html';s=p.read_text();s=re.sub(r'<div class="publication">.*?</div>','',s,flags=re.S);s=re.sub(r'<a href="https://openlibrary.org/(?:books|works)/[^"]+" target="_blank" rel="noopener">Book (?:edition|record) ↗</a><br>','',s);s=re.sub(r'<tr>.*?</tr>',lambda m:update(m.group()),s,flags=re.S)
css='\n.publication{font:11px/1.6 Arial,sans-serif;color:var(--muted);margin-top:8px}.publication a{color:inherit;text-decoration:none}.publication a:hover{text-decoration:underline}\n'
s=s.replace('</style>',css+'</style>',1)
s=s.replace('Dates, where provided, refer to the original publication or serialisation, not the date of an English edition.','Unlabelled dates and “First published” refer to the original publication or serialisation. “Edition” dates refer only to the specific linked catalogue edition, which may be a later printing or translation; they do not claim to identify the first publication.')
s=s.replace('Search links remain available as a fallback.','Search links remain available as a fallback. Additional “Book edition” links identify title-and-author-matched Open Library edition records. Edition dates are taken from those linked records; catalogue metadata may still contain errors.')
if '--dry-run' not in sys.argv:
 p.write_text(s);(root/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(entries=len(report),editions=sum('edition_url' in x for x in report),missing_years=sum(x['missing_year'] for x in report),missing_direct_links=sum(x['missing_direct_link'] for x in report))))
