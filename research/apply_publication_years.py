"""Prefer source-checked original years, retaining conservative edition fallbacks.
Run after audit_first_publication.py and the manual source/identity review.
No earliest-catalogue-edition date is promoted automatically.
"""
import html,json,re
from collections import Counter
from pathlib import Path
from refresh_book_assets import title_match,author_match
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'research'
def read(name):return json.loads((R/name).read_text())
def key(title,author):return author+' | '+title
curated={key(v['title'],v['author']):v for v in read('original-years.json')}
provider=read('goodreads-first-publication.json')
for file in ['goodreads-publication-review.json','goodreads-date-search.json']:
 for k,v in read(file).items():
  if v.get('year'):provider[k]=v
identities={v['key']:v for v in read('publication-identity-review.json')}
catalogue=read('catalogue-candidates.json');baseline=read('publication-date-audit.json')
# Preserve the original date/source independently of subsequent runs.
prior={key(v['title'],v['author']):v for v in baseline['books']}
audit=[];changes=[]
def update(m):
 row=m.group();t=re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>',row,re.S)
 if not t:return row
 title,author=map(html.unescape,t.groups());k=key(title,author)
 date=re.search(r'<div class="publication">.*?</div>',row,re.S)
 if not date:raise ValueError('Missing date container: '+k)
 original=prior[k].get('original_date_html',prior[k].get('previous_date_html')) or date.group()
 entry=dict(title=title,author=author,original_date_html=original,previous_date_html=date.group(),checked_at='2026-11-18')
 source=curated.get(k);candidate=provider.get(k,{});existing=re.search(r'First published:\s*([^<]+)',date.group())
 identity=identities.get(k,{})
 identity_ok=candidate.get('status')=='work_first_publication_matched' or (candidate.get('status')=='identity_requires_review' and candidate.get('source')==identity.get('source') and candidate.get('matched_title')==identity.get('matched_title') and candidate.get('matched_authors')==identity.get('matched_authors'))
 if source:entry['status']='verified-original'
 elif existing:
  value=html.unescape(existing.group(1)).strip()
  if identity_ok and candidate.get('year')==value:
   source=dict(year=value,source=candidate['source']);entry['status']='goodreads-work-first-publication'
  else:
   entry.update(status='existing-original-not-reverified',year=value)
   if candidate.get('year') and candidate['year']!=value:entry['review_note']='Existing original date retained; Goodreads differs: '+candidate['year']
 else:
  identity=identities.get(k,{})
  matched=candidate.get('status')=='work_first_publication_matched' or (candidate.get('status')=='identity_requires_review' and candidate.get('source')==identity.get('source') and candidate.get('matched_title')==identity.get('matched_title') and candidate.get('matched_authors')==identity.get('matched_authors'))
  entry['provider_status']=candidate.get('status','not_found')
  if matched:
   year=int(candidate['year']);earlier=[]
   for c in catalogue.get(k,{}).get('candidates',[]):
    rec=c['record'];y=rec.get('first_publish_year')
    if y and 1000<int(y)<year and title_match(title,rec.get('title','')) and any(author_match(author,a) for a in rec.get('author_name',[])):earlier.append(int(y))
   edition=re.search(r'Edition:\s*(\d{4})',date.group())
   if edition and int(edition.group(1))<year:earlier.append(int(edition.group(1)))
   if earlier:entry.update(review_note='Earlier catalogue or current edition date conflicts with Goodreads work date.',candidate_year=str(year),earlier_catalogue_year=min(earlier),candidate_source=candidate['source'])
   else:source=dict(year=str(year),source=candidate['source']);entry['status']='goodreads-work-first-publication'
  if not source:entry['status']='edition-fallback' if 'Edition:' in date.group() else 'unresolved'
 if source:
  year=str(source['year']);url=source['source'];entry.update(year=year,source=url)
  if candidate.get('year') and candidate['year']!=year:entry['review_note']='Curated original-publication source takes precedence over Goodreads '+candidate['year']+'.'
  label='<div class="publication"><a href="'+html.escape(url,quote=True)+'" target="_blank" rel="noopener" title="Source for first publication">First published: '+html.escape(year)+'</a></div>'
  if re.sub('<[^>]+>','',original)!=('First published: '+year):changes.append(dict(title=title,author=author,before=re.sub('<[^>]+>','',original),after='First published: '+year))
  row=row[:date.start()]+label+row[date.end():]
 audit.append(entry);return row
p=ROOT/'index.html';s=p.read_text();s=re.sub(r'<tr\b.*?</tr>',update,s,flags=re.S);p.write_text(s)
counts=Counter(v['status'] for v in audit)
(R/'publication-date-audit.json').write_text(json.dumps(dict(date='2026-11-18',policy='Prefer original-language first publication. Goodreads work-level dates are checked against the displayed First published field, title and author; conflicting earlier editions are held for review. Curated original-publication sources take precedence. Edition dates remain explicit fallbacks.',summary=dict(counts),books=audit),ensure_ascii=False,indent=2)+'\n')
(R/'publication-year-changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
print('Date labels',dict(counts),'Changed',len(changes));print('Remaining conflicts:')
for a in audit:
 if a.get('candidate_year'):print(a['title'],a['candidate_year'],'vs',a['earlier_catalogue_year'])
