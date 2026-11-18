"""Apply identity-reviewed cover assets without changing book metadata."""
import html,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run():
 audit=json.loads((ROOT/'research/cover-followup-audit.json').read_text());added=0
 def row_replace(match):
  nonlocal added
  row=match.group();m=re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>',row,re.S)
  if not m or '<span class="nocover"' not in row:return row
  title,author=map(html.unescape,m.groups());record=audit.get(author+' | '+title,{})
  if record.get('status')!='cover_downloaded':return row
  assert (ROOT/record['local_path']).is_file()
  image='<a href="'+html.escape(record['source'],quote=True)+'" target="_blank" rel="noopener"><img src="'+record['local_path']+'" alt="'+html.escape('Cover: '+title,quote=True)+'" loading="lazy" decoding="async" width="'+str(record['width'])+'" height="'+str(record['height'])+'"></a>'
  added+=1
  return re.sub(r'<span class="nocover"[^>]*></span>',lambda _:image,row,count=1)
 path=ROOT/'index.html';s=re.sub(r'<tr>.*?</tr>',row_replace,path.read_text(),flags=re.S);path.write_text(s)
 print('Added covers:',added)
if __name__=='__main__':run()
