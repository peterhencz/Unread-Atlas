"""Apply the source-reviewed follow-up and a documented title correction.
Research decisions live in publication-followup-sources.json; unresolved conflicts
remain explicit. No dates are inferred from the earliest catalogue edition.
"""
import json,re,runpy
from pathlib import Path
R=Path(__file__).resolve().parent;ROOT=R.parent
follow=json.loads((R/'publication-followup-sources.json').read_text())
p=R/'original-years.json';years=json.loads(p.read_text())
for row in follow:
 if row['status']!='original_publication_confirmed':continue
 title=row.get('corrected_title',row['title']);author=row['author']
 years=[v for v in years if (v['title'],v['author']) not in [(row['title'],author),(title,author)]]
 years.append(dict(title=title,author=author,year=row['year'],source=row['source'],note=row['note'],checked=row['checked'],basis='Publication follow-up: other publisher, library, author or research sources.'))
p.write_text(json.dumps(years,ensure_ascii=False,indent=2)+'\n')
# Preserve historical source caches; correct only current catalogue-facing records.
correction=next(v for v in follow if v.get('corrected_title'))
old,new=correction['title'],correction['corrected_title']
p=ROOT/'index.html';s=p.read_text();s=s.replace('<strong>'+old+'</strong>','<strong>'+new+'</strong>').replace('Cover unavailable: '+old,'Cover unavailable: '+new)
s=s.replace('Garth+St+Omer+Prisms','Garth+St+Omer+Prisnms');p.write_text(s)
for name in ['books.json','reading-notes-audit.json']:
 p=R/name;data=json.loads(p.read_text())
 rows=data if isinstance(data,list) else data.get('books',[])
 for row in rows:
  if row.get('title')==old and row.get('author')==correction['author']:row.update(title=new,previous_title=old)
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
# Keep the date audit's stable provenance addressable under the corrected title.
p=R/'publication-date-audit.json';data=json.loads(p.read_text())
for row in data['books']:
 if row['title']==old and row['author']==correction['author']:row.update(title=new,previous_title=old)
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
runpy.run_path(str(R/'apply_publication_years.py'),run_name='__main__')
p=R/'publication-date-audit.json';data=json.loads(p.read_text())
lookup={(v.get('corrected_title',v['title']),v['author']):v for v in follow}
for row in data['books']:
 item=lookup.get((row['title'],row['author']))
 if item:
  row['followup_status']=item['status']
  if item['status']!='original_publication_confirmed':row.update(review_note=item['note'],review_sources=item['sources'])
  if item.get('corrected_title'):row['previous_title']=item['title']
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
