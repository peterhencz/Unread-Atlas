"""Retry unavailable pages and retain full metadata for manual identity review."""
import concurrent.futures,json
from pathlib import Path
from refresh_book_assets import manifest
from audit_first_publication import read_book
R=Path(__file__).parent;OUT=R/'goodreads-publication-review.json'
if __name__=='__main__':
 base=json.loads((R/'goodreads-first-publication.json').read_text());cache=json.loads(OUT.read_text()) if OUT.exists() else {}
 pending=[b for b in manifest() if base.get(b['key'],{}).get('status') in ['fetch_error','identity_requires_review'] and (b['key'] not in cache or cache[b['key']]['status']=='fetch_error')]
 for b in pending:b['transport']='curl'
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for future in concurrent.futures.as_completed([pool.submit(read_book,b) for b in pending]):
   key,row=future.result();cache[key]=row;OUT.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+'\n')
 print('REVIEW COMPLETE',len(cache),flush=True)
