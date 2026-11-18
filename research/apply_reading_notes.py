"""Create restrained thematic notes from identity-matched synopses/catalogue subjects.
Output is deliberately short; no ratings, reviews or unsourced reading-difficulty claims.
Raw source text stays in an ignored local cache, not in the published audit.
"""
from pathlib import Path
import json,re,html,sys
from refresh_book_assets import title_match,author_match
R=Path(__file__).parent;ROOT=R.parent
RULES=[
 ('Family',r'family|families|father|mother|parents|siblings|brother|sister|daughter|son',r'family (?:life|ties|saga|relationships)|three generations|across generations|domineering mother|father and son','Family relationships anchor the story.'),
 ('Love & relationships',r'love|lover|lovers|marriage|married|desire|romance|affair',r'love story|arranged marriage|romantic relationship','Love and intimate relationships shape the story.'),
 ('Migration & exile',r'migration|migrant|immigrant|emigration|exile|refugee|displacement',r'leaves? (?:her|his|their) (?:home|country)|forced to flee','Leaving home and questions of belonging shape the story.'),
 ('War & conflict',r'war|wartime|soldier|soldiers|battle|occupation|military|genocide',r'civil war|world war|war of independence|armed conflict','The story follows lives shaped by war and conflict.'),
 ('Power & politics',r'political|politics|dictator|dictatorship|regime|government|revolution|authoritarian|corruption|oppression|empire|sultan',r'political power|totalitarian state|abuse of power','Private lives intersect with political power.'),
 ('Identity & belonging',r'identity|belonging|alienation|outsider|outsiders|discrimination|racism|racial',r'sense of self|search for identity|racial identity','Questions of identity and belonging run through the story.'),
 ('Memory & loss',r'memory|memories|grief|mourning|bereavement|recollection|remembering',r'loss of (?:her|his|their)|haunted by (?:the|his|her) past','Memory and loss connect the characters to the past.'),
 ('Coming of age',r'childhood|adolescence|adolescent|teenager|teenage|boyhood|girlhood',r'coming.of.age|growing up|young adulthood','Growing up brings personal and social change.'),
 ('Class & society',r'poverty|wealth|wealthy|bourgeois|aristocracy|aristocratic|peasant|peasants|inequality',r'social class|class divisions|class struggle|working.class','Social divisions shape the characters’ opportunities and relationships.'),
 ('Faith & doubt',r'faith|religion|religious|spiritual|priest|monastery|monk',r'religious belief|spiritual search|crisis of faith','Belief and spiritual questions shape the story.'),
 ('Myth & folklore',r'myth|mythology|folklore|folktale|legend|legends|mythical|supernatural',r'magical realism|folk tale|ancient myth','Myth and folklore enter the characters’ world.'),
 ('Nature & place',r'landscape|wilderness|ecology|environmental|farming|farmers|drought',r'natural world|relationship with (?:the )?land|rural life','Place and the natural world shape the characters’ lives.'),
 ('Mystery & crime',r'murder|murderer|detective|investigation|crime|criminal|disappearance|feud',r'murder mystery|missing person|unsolved crime','A crime or mystery drives the story.'),
 ('Colonialism',r'colonial|colonialism|colonization|colonisation|postcolonial|imperialism',r'colonial rule|colonial past','Colonial power and its consequences shape the story.'),
 ('Satire',r'satire|satirical',r'political satire|social satire','Satire exposes tensions in social life.'),
 ('Narrative experiment',r'metafiction|nonlinear|fragmented|unreliable',r'experimental novel|unreliable narrator|non.linear narrative|stream of consciousness','The story uses an unconventional narrative structure.'),
]
quote_sources=set();used_excerpts=set()
notes={v['key']:v for v in json.loads((R/'reading-note-source-cache.json').read_text())}
editions=json.loads((R/'editions.json').read_text());audit=[]
def themes(text):
 text=html.unescape(text).lower();found=[]
 for i,(tag,terms,phrases,sentence) in enumerate(RULES):
  words=re.findall(r'\b(?:'+terms+r')\b',text);strong=re.findall(phrases,text)
  score=len(words)+3*len(strong)
  if score>=2:found.append((score,i,tag,sentence))
 found.sort(key=lambda v:(-v[0],v[1]));return found[:3]

def update(m):
 row=m[0];b=re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>',row,re.S)
 if not b:return row
 title,author=map(html.unescape,b.groups());key=author+' | '+title;record=notes.get(key,{});source=record.get('source');text=record.get('source_text','');kind='Goodreads synopsis'
 # Ignore search snippets/biographies: isolate the book synopsis below the rating header.
 rating=re.search(r'\n[0-5]\.\d+[^\n]*ratings[^\n]*\n',text)
 if rating:text=text[rating.end():].strip()
 elif 'Rate this book' in text:text=text.rsplit('Rate this book',1)[1].strip()
 elif 'Want to Read' in text:text=text.rsplit('Want to Read',1)[1].strip()
 else:text=''
 text=re.sub(r'^(?:Want to Read|Rate this book)\s*','',text)
 text=re.sub(r'^(?:Want to Read|Rate this book)\s*','',text)
 text=re.split(r'Book details & editions|First published|## Ratings|### About the author',text)[0].strip()
 text=re.sub(r'^[A-Z0-9 ,’\x27–—-]{15,}\n+','',text)
 found=themes(text) if source and text else []
 excerpt=None
 if source and len(text.split())>=10 and source not in quote_sources:
  clean=re.sub(r'\s+',' ',text).strip()
  sentences=re.split(r'(?<=[.!?])\s+',clean)
  marketing=r'masterful|touching|greatest|magnum opus|masterpiece|award|prize|bestsell|acclaimed|celebrated|stunning|mesmeri|hilarious|captivat|unforgettable|timeless|contemporary and rival|beautifully|riveting|was born'
  sentence=next((v for v in sentences if len(v.split())>=7 and not re.search(marketing,v,re.I)),None)
  if sentence:
   words=sentence.split();excerpt=sentence if len(words)<=20 else ' '.join(words[:18]).rstrip(' ,;:')+'…'
  if excerpt in used_excerpts:excerpt=None
  if excerpt:used_excerpts.add(excerpt);quote_sources.add(source)

 if not found and not excerpt:
  for k in re.findall(r'https://openlibrary.org/books/(OL\d+M)',row):
   e=editions.get(k,{})
   if title_match(title,e.get('title','')) and any(author_match(author,a.get('name','')) for a in e.get('authors',[])):
    subjects=' '.join(v.get('name','') for v in e.get('subjects',[]));tags=themes(subjects)
    if tags:found=tags;source='https://openlibrary.org/books/'+k;kind='Catalogue subjects';break
 if found or excerpt:
  sentence=excerpt or found[0][3];tags=[f[2] for f in found]
  body='<p class="reading-note">'+('<q>'+html.escape(sentence)+'</q>' if excerpt else html.escape(sentence))+'</p><div class="book-topics" aria-label="Reading themes">'+''.join('<span>'+html.escape(t)+'</span>' for t in tags)+'</div><a class="reading-note-source" href="'+html.escape(source,quote=True)+'" target="_blank" rel="noopener">'+kind+' ↗</a>'
  audit.append(dict(title=title,author=author,checked_at='2026-11-18',status='source_based_thematic_note',excerpt_words=len(sentence.split()) if excerpt else 0,note_type='short_synopsis_excerpt' if excerpt else 'source_theme_summary',tags=tags,source=source,source_type=kind,method='Short source excerpt (at most 20 words per source) with controlled thematic tags, or a minimal summary of matched edition subjects; not a manual critical review.'))
 else:
  body='<p class="reading-note pending-note">Note not yet source-verified.</p>'
  audit.append(dict(title=title,author=author,checked_at='2026-11-18',status='awaiting_source_verification',source=source))
 return re.sub(r'<td class="reason">.*?</td>',lambda _:'<td class="reason">'+body+'</td>',row,count=1,flags=re.S)
p=ROOT/'index.html';s=p.read_text();s=re.sub(r'<tr>.*?</tr>',update,s,flags=re.S)
css='''/* Short source-backed notes, with a compact, consistent set of themes. */
.book-topics{display:flex;flex-wrap:wrap;gap:6px 12px;margin-top:12px}
.book-topics span{font:500 11px/1.5 var(--atlas-font);color:var(--muted)}
.book-topics span+span::before{content:'·';margin-right:12px;color:var(--accent)}
.reading-note-source{display:inline-block;margin-top:14px;font:400 11px/1.6 var(--atlas-font);color:var(--muted);text-decoration:none}
.reading-note-source:hover{color:var(--accent);text-decoration:underline}
#atlas-results td.reason .pending-note{font-size:12px;color:var(--muted)}
'''
s=s.replace('</style>',css+'</style>',1)
if '--dry-run' not in sys.argv:p.write_text(s)
(Path('/tmp/unread-atlas-notes-preview.json') if '--dry-run' in sys.argv else R/'reading-notes-audit.json').write_text(json.dumps(dict(checked_at='2026-11-18',method='Short quoted synopsis excerpts and thematic tags from matched book pages, or minimal summaries of edition subjects. Automatically extracted and source-linked, not individually reviewed literary judgments.',entries=audit),ensure_ascii=False,indent=2)+'\n')
print('Notes:',sum(v['status']=='source_based_thematic_note' for v in audit),'pending:',sum(v['status']=='awaiting_source_verification' for v in audit))

# Preserve reviewed editorial text when regenerating legacy extraction notes.
if "--dry-run" not in sys.argv and (R/"editorial-summaries.json").exists():
 from apply_editorial_summaries import run as apply_editorial_summaries
 apply_editorial_summaries()
