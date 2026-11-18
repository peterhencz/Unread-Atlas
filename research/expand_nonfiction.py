"""Append further reviewed nonfiction and refresh current catalogue totals."""
from pathlib import Path
import json,re,html,sys
from add_nonfiction_selections import render
from add_empty_country_selections import esc,link
from cover_placeholders import placeholder
ROOT=Path(__file__).resolve().parents[1]
def main():
 data=json.loads((ROOT/'research/nonfiction-expansion.json').read_text());grouped={}
 for e in data['entries']:grouped.setdefault(e['country'],[]).append(e)
 p=ROOT/'index.html';s=p.read_text();seen=set()
 def section(m):
  block=m[0];h=re.search(r'<h3>([^<]+)</h3>',block)
  if not h:return block
  country=html.unescape(h[1])
  if country not in grouped:return block
  seen.add(country)
  for e in grouped[country]:
   if '<strong>'+esc(e['title'])+'</strong>' in block:continue
   row=render(e)
   if e.get('date_source'):row=row.replace('<div class="publication"><a href="'+esc(e['record_source'])+'"','<div class="publication"><a href="'+esc(e['date_source'])+'"',1)
   assert '</tbody>' in block;block=block.replace('</tbody>',row+'\n</tbody>',1)
  return block
 s=re.sub(r'<section>.*?</section>',section,s,flags=re.S);assert seen==set(grouped)
 def row(m):
  text=m[0];b=re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>',text,re.S)
  if b and 'class="nocover"' in text:text=re.sub(r'<span class="nocover"[^>]*>.*?</span>',placeholder(*map(html.unescape,b.groups())),text,flags=re.S)
  return text
 s=re.sub(r'<tr>.*?</tr>',row,s,flags=re.S)
 total=s.count('<td class="book">');covers=len(re.findall(r'<img\b',s));direct=sum('goodreads.com/book/show/' in r for r in re.findall(r'<td class="book">.*?</td>',s,re.S));nf=s.count('class="book-kind"')
 s=re.sub(r'<strong>\d+</strong>books to discover',f'<strong>{total}</strong>books to discover',s,count=1);s=re.sub(r'<strong>\d+</strong>catalogue covers',f'<strong>{covers}</strong>catalogue covers',s,count=1);p.write_text(s)
 p=ROOT/'about.html';s=p.read_text().replace('<strong>768</strong><span>books to discover',f'<strong>{total}</strong><span>books to discover').replace('761 fiction selections and 7 nonfiction selections',f'761 fiction selections and {nf} nonfiction selections').replace('671 books have source-based notes','678 books have source-based notes').replace('524 books have covers and 710 have direct Goodreads pages',f'{covers} books have covers and {direct} have direct Goodreads pages');p.write_text(s)
 p=ROOT/'sources.html';s=p.read_text().replace('<strong>710 direct Goodreads links:</strong>',f'<strong>{direct} direct Goodreads links:</strong>').replace('<strong>524 covers:</strong>',f'<strong>{covers} covers:</strong>').replace('<strong>671 source-based notes:</strong>','<strong>678 source-based notes:</strong>')
 if 'nonfiction-expansion.json' not in s:s=s.replace('<li><a href="research/nonfiction-additions.json">','<li><a href="research/nonfiction-expansion.json">Further nonfiction: seven additional books and their evidence ↗</a></li><li><a href="research/nonfiction-additions.json">',1)
 p.write_text(s)
 p=ROOT/'updates.html';s=p.read_text()
 if 'id="more-nonfiction-update"' not in s:s=s.replace('<ol class="update-list">',f'<ol class="update-list"><li id="more-nonfiction-update"><time datetime="2026-11-18">18 November 2026</time><h3>More nonfiction discoveries</h3><p>Seven further books bring the collection to {total} selections, including {nf} clearly labelled nonfiction titles. Vatican City, Kiribati, the Federated States of Micronesia, Nauru, Palau and Tuvalu gain further reading options. Missing covers now use quiet, book-specific gradients. <a href="research/nonfiction-expansion.json">Book references ↗</a></p></li>')
 p.write_text(s)
 p=ROOT/'research/books.json';books=json.loads(p.read_text());keys={(b['country'],b['title'],b['author']) for b in books}
 q=ROOT/'research/reading-notes-audit.json';notes=json.loads(q.read_text());nkeys={(b['title'],b['author']) for b in notes['entries']}
 for e in data['entries']:
  if (e['country'],e['title'],e['author']) not in keys:books.append(dict(country=e['country'],title=e['title'],author=e['author'],kind='nonfiction',meta='<span class="book-kind">Nonfiction</span>',work=[e['record_source']],goodreads=[e['goodreads']],audit='research/nonfiction-expansion.json'))
  if (e['title'],e['author']) not in nkeys:notes['entries'].append(dict(title=e['title'],author=e['author'],checked_at=e['checked_at'],status='source_based_thematic_note',note_type='short_source_paraphrase',tags=e['tags'],source=e['note_source'],source_type='Publisher or institutional reference',method='Short original paraphrase; country and edition evidence in nonfiction-expansion.json.'))
 p.write_text(json.dumps(books,ensure_ascii=False,indent=2)+'\n');q.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
 print(dict(books=total,covers=covers,goodreads=direct,nonfiction=nf,gradients=total-covers))
if __name__=='__main__':main()
