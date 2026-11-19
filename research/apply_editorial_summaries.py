"""Apply reviewed editorial summaries, preserving country context and thematic tags."""
from pathlib import Path
import html,json,re
ROOT=Path(__file__).resolve().parents[1]
def run():
 data=json.loads((ROOT/'research/editorial-summaries.json').read_text())
 entries={(e['title'],e['author']):e for e in data['entries']};seen=set()
 def update(match):
  row=match.group();m=re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>',row,re.S)
  if not m:return row
  key=tuple(map(html.unescape,m.groups()));e=entries.get(key)
  if not e:return row
  seen.add(key)
  def reason(match):
   body=match.group(1)
   body=re.sub(r'<p class="reading-note(?: [^"]*)?">.*?</p>',lambda _:'<p class="reading-note editorial-summary">'+html.escape(e['summary'])+'</p>',body,count=1,flags=re.S)
   body=re.sub(r'<a\b(?=[^>]*class="reading-note-source")[^>]*>.*?</a>','',body,flags=re.S)
   return '<td class="reason">'+body+'</td>'
  return re.sub(r'<td class="reason">(.*?)</td>',reason,row,count=1,flags=re.S)
 p=ROOT/'index.html';s=re.sub(r'<tr>.*?</tr>',update,p.read_text(),flags=re.S)
 assert seen==set(entries),'Every reviewed summary must match an existing book'
 p.write_text(s)
 p=ROOT/'research/reading-notes-audit.json';audit=json.loads(p.read_text())
 audit['method']='Original 10–15-word editorial summaries for every selection, paraphrased from checked book descriptions; sources recorded in editorial-summaries.json.'
 for row in audit['entries']:
  e=entries.get((row['title'],row['author']))
  if e:
   row.update(status='source_based_thematic_note',note_type='editorial_summary',summary=e['summary'],excerpt_words=0,word_count=e['word_count'],source=e['source'],source_type='Checked book description',method=e['method'],checked_at=e['checked_at'])
 p.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
 print('Applied',len(seen),'editorial summaries')
 if (ROOT/'research/reviewed-themes.json').exists():
  from apply_reviewed_themes import run as apply_reviewed_themes
  apply_reviewed_themes()
if __name__=='__main__':run()
