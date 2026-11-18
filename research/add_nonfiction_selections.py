"""Apply the sourced nonfiction follow-up without changing existing book records."""
import html
import json
import re
from pathlib import Path
from add_empty_country_selections import render_book, link, esc

ROOT = Path(__file__).resolve().parents[1]

def render(entry):
    row = render_book(entry)
    author = f'<div class="author">{esc(entry["author"])}</div>'
    row = row.replace(author, author+'<span class="book-kind">Nonfiction</span>', 1)
    context = '<p class="reading-context"><strong>Country connection:</strong> '+esc(entry['country_connection'])+'</p>'
    row = row.replace('<div class="book-topics"', context+'<div class="book-topics"', 1)
    if entry.get('country_connection_source'):
        row = row.replace('</td></tr>', ' '+link(entry['country_connection_source'], 'Context source ↗', 'reading-note-source')+'</td></tr>')
    return row

def main():
    data = json.loads((ROOT/'research/nonfiction-additions.json').read_text())
    grouped = {}
    for entry in data['entries']:
        assert entry['kind']=='nonfiction' and entry['year']
        if entry.get('cover'):
            assert (ROOT/entry['cover']['path']).is_file()
        grouped.setdefault(entry['country'], []).append(entry)
    path = ROOT/'index.html'
    text = path.read_text()
    seen = set()
    def section(match):
        block = match[0]
        heading = re.search(r'<h3>([^<]+)(?:<span class="count">|</h3>)', block)
        if not heading:
            return block
        country = html.unescape(heading[1])
        if country not in grouped:
            return block
        entries = grouped[country]
        count = block.count('<td class="book">')
        assert count in (0, len(entries)), (country, count)
        if count:
            assert block.count('class="book-kind"')==len(entries), 'Refusing to overwrite other selections'
        seen.add(country)
        n = len(entries)
        return f'''<section><h3>{esc(country)}</h3>
<table><thead><tr><th class="cover">Cover</th><th>Book and links</th><th>Themes and reading notes</th></tr></thead><tbody>
{chr(10).join(render(entry) for entry in entries)}
</tbody></table>
</section>'''
    text = re.sub(r'<section>.*?</section>', section, text, flags=re.S)
    assert seen==set(grouped)
    for country, entries in grouped.items():
        text = text.replace(f'{esc(country)} (0/5)', f'{esc(country)} ({len(entries)}/5)')
    text = text.replace('additional suitable novels still need to be identified.', 'additional suitable books still need to be identified.')
    text = text.replace('Unread Atlas — Novels by Country', 'Unread Atlas — Books by Country')
    total = text.count('<td class="book">')
    covers = len(re.findall(r'<img\b', text))
    direct = sum('goodreads.com/book/show/' in row for row in re.findall(r'<td class="book">.*?</td>', text, re.S))
    text = re.sub(r'<strong>\d+</strong>(?:novels &amp; novellas|books to discover)', f'<strong>{total}</strong>books to discover', text, count=1)
    text = re.sub(r'<strong>\d+</strong>catalogue covers', f'<strong>{covers}</strong>catalogue covers', text, count=1)
    path.write_text(text)
    about = ROOT/'about.html'
    text = about.read_text()
    text = text.replace('<strong>761</strong><span>books to discover', f'<strong>{total}</strong><span>books to discover')
    text = text.replace('an independent editorial guide to fiction from around the world.', 'an independent editorial guide to books from around the world, with fiction at its heart.')
    marker='<h2>What a book record tells you</h2>'
    if 'id="nonfiction-policy"' not in text:
        text=text.replace(marker, '''<h2 id="nonfiction-policy">Beyond fiction</h2><p>Where fiction selections are sparse, clearly labelled <strong>Nonfiction</strong> books offer another route into a country: memoirs, travel writing, history and investigations. These books may connect through the author’s life or through a documented focus on the country. Local voices and outside perspectives are distinguished explicitly.</p><p>The atlas currently contains <strong>761 fiction selections and 7 nonfiction selections</strong>. Every destination now has at least one book. An entry does not claim to represent a country’s entire literature or culture.</p>'''+marker)
    text = text.replace('664 books have source-based notes', '671 books have source-based notes')
    text = text.replace('520 books have covers and 703 have direct Goodreads pages', f'{covers} books have covers and {direct} have direct Goodreads pages')
    about.write_text(text)
    sources = ROOT/'sources.html'
    text = sources.read_text()
    review = '''<section class="country-research" id="country-review"><h2>Previously empty destinations</h2><p><strong>18 November 2026:</strong> the novel-only review added 17 books across 15 of the 21 empty destinations. A subsequent nonfiction review added seven books across the remaining six: Vatican City, Kiribati, the Federated States of Micronesia, Nauru, Palau and Tuvalu. Every destination now has at least one selection.</p><p>Nonfiction is labelled on each book. Memoirs, reported investigations, collective histories and documented oral traditions can qualify. A country-focused nonfiction work may be by an external author; its connection and perspective are stated explicitly. Fiction country connections continue to follow authorship and cultural affiliation.</p><p>Each addition records identity, form, edition date, country connection and sources. New notes are short original paraphrases. Original-language editions remain labelled. During the novel review, two ISBN lookups returned unrelated titles, so those matches were rejected.</p><ul><li><a href="research/empty-country-additions.json">Original 21-destination novel review and its then-unresolved leads ↗</a></li><li><a href="research/nonfiction-additions.json">Nonfiction follow-up: seven books, country connections and sources ↗</a></li></ul></section>'''
    text,n = re.subn(r'<section class="country-research" id="country-review">.*?</section>', review, text, flags=re.S)
    assert n==1
    text = text.replace('<strong>703 direct Goodreads links:</strong>', f'<strong>{direct} direct Goodreads links:</strong>').replace('<strong>520 covers:</strong>', f'<strong>{covers} covers:</strong>').replace('<strong>664 source-based notes:</strong>', '<strong>671 source-based notes:</strong>')
    sources.write_text(text)
    updates = ROOT/'updates.html'
    text = updates.read_text()
    if 'id="nonfiction-update"' not in text:
        text = text.replace('<ol class="update-list">', '<ol class="update-list"><li id="nonfiction-update"><time datetime="2026-11-18">18 November 2026</time><h3>New routes through nonfiction</h3><p>Seven clearly labelled nonfiction books fill the six remaining empty destinations: memoirs, travel writing, history and investigative reporting. The atlas now has 768 selections and at least one book for every destination. Country connections distinguish local voices from outside perspectives. <a href="sources.html#country-review">Read the sources and selection notes ↗</a></p></li>')
    updates.write_text(text)
    old='A world of stories, waiting to be discovered. Explore classics, modern voices and contemporary fiction from every corner of the globe.'
    new='A world of stories, waiting to be discovered. Explore fiction, memoirs and nonfiction from every corner of the globe.'
    for filename in ['index.html','about.html','reading-routes.html','sources.html','updates.html']:
        p=ROOT/filename;p.write_text(p.read_text().replace(old,new))
    books_path=ROOT/'research/books.json'
    books=json.loads(books_path.read_text());keys={(b['country'],b['title'],b['author']) for b in books}
    notes_path=ROOT/'research/reading-notes-audit.json'
    notes=json.loads(notes_path.read_text());note_keys={(b['title'],b['author']) for b in notes['entries']}
    for entry in data['entries']:
        if (entry['country'],entry['title'],entry['author']) not in keys:
            books.append(dict(country=entry['country'],title=entry['title'],author=entry['author'],meta='<span class="book-kind">Nonfiction</span>',kind='nonfiction',work=[entry['record_source']],goodreads=[entry['goodreads']],audit='research/nonfiction-additions.json'))
        if (entry['title'],entry['author']) not in note_keys:
            notes['entries'].append(dict(title=entry['title'],author=entry['author'],checked_at=entry['checked_at'],status='source_based_thematic_note',note_type='short_source_paraphrase',tags=entry['tags'],source=entry['note_source'],source_type='Publisher or catalogue reference',method='Manually checked nonfiction reference; short original paraphrase. Country connection and edition evidence in nonfiction-additions.json.'))
    books_path.write_text(json.dumps(books,ensure_ascii=False,indent=2)+'\n')
    notes_path.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
    print(dict(books=total,nonfiction=len(data['entries']),covers=covers,direct_goodreads=direct))

if __name__=='__main__':
    main()
