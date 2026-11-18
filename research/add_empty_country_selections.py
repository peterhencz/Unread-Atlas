"""Apply the manually reviewed first pass over the 21 formerly empty destinations.

Network-free: source review and optional asset collection are recorded separately in
empty-country-additions.json. Re-running does not duplicate books or update entries
outside this pass. Historical source audits keep their original scope.
"""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'research/empty-country-additions.json'

def esc(value):
    return html.escape(str(value), quote=True)

def link(url, label, cls=''):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener"'+(f' class="{cls}"' if cls else '')+f'>{label}</a>'

def render_book(book):
    cover = book.get('cover')
    cover_html = '<span class="nocover">No matched cover</span>'
    if cover:
        cover_html = link(book['record_source'], f'<img src="{esc(cover["path"])}" width="{cover["width"]}" height="{cover["height"]}" alt="Catalogue cover: {esc(book["title"])}" loading="lazy" decoding="async">')
    links = [link(book['record_source'], 'Book record ↗')]
    if book.get('goodreads'):
        links.append(link(book['goodreads'], 'Goodreads book page ↗'))
    language = ''
    if book['language'] != 'English':
        text = f'{book["language"]} · English edition not verified'
        if book['country'] == 'Maldives':
            text = 'Dhivehi · English catalogue title'
        language = f'<div class="book-language">{esc(text)}</div>'
    note_source = book.get('note_source', book['record_source'])
    topics = ''.join(f'<span>{esc(tag)}</span>' for tag in book['tags'])
    return f'''<tr><td class="cover">{cover_html}</td><td class="book"><strong>{esc(book['title'])}</strong><div class="author">{esc(book['author'])}</div>{language}<div class="publication">{link(book['record_source'], f'{esc(book["date_kind"])}: {book["year"]}')}</div>
<div class="links">{'<br>'.join(links)}</div></td><td class="reason"><p class="reading-note">{esc(book['note'])}</p><div class="book-topics" aria-label="Reading themes">{topics}</div>{link(note_source, 'Reading-note source ↗', 'reading-note-source')}</td></tr>'''

def apply():
    data = json.loads(DATA.read_text())
    source = (ROOT / 'index.html').read_text()
    additions = {}
    for entry in data['entries']:
        assert entry['year'] and entry['record_source'].startswith('https://')
        if entry.get('cover'):
            assert (ROOT / entry['cover']['path']).exists()
        additions.setdefault(entry['country'], []).append(entry)
    unresolved = {entry['country'] for entry in data['unresolved_destinations']}
    before = source
    seen = set()
    def section(match):
        block = match[0]
        heading = re.search(r'<h3>(.*?)<span class="count">', block)
        if not heading:
            return block
        country = html.unescape(heading[1])
        if country in additions:
            seen.add(country)
            entries = additions[country]
            # Only these formerly empty sections are owned by this migration.
            count = len(re.findall(r'<td class="book">', block))
            assert count in (0, len(entries)), (country, count)
            context = ''
            if country in {'Laos', 'Monaco', 'Marshall Islands', 'Tonga'}:
                book = entries[0]
                context = '<p class="pick country-connection">'+esc(book['country_connection'])+' '+link(book['country_connection_source'], 'Author connection ↗')+'</p>\n'
            n = len(entries)
            rows = '\n'.join(render_book(entry) for entry in entries)
            return f'''<section><h3>{esc(country)}<span class="count">{n}/5 selections</span></h3>
{context}<table><thead><tr><th class="cover">Cover</th><th>Book and links</th><th>Themes and reading notes</th></tr></thead><tbody>
{rows}
</tbody></table>
<p class="gap">Open selection: {5-n} additional suitable novels still need to be identified.</p>
</section>'''
        if country in unresolved:
            block = re.sub(r'<p class="gap">.*?</p>', '<p class="gap">No suitable novel or novella verified in the latest review. This is a research gap, not a claim that none exists. <a href="sources.html#country-review">Research notes ↗</a></p>', block, flags=re.S)
        return block
    source = re.sub(r'<section>.*?</section>', section, source, flags=re.S)
    assert seen == set(additions), set(additions) - seen
    # All cover images use native lazy loading; decoding does not block rendering.
    def image(match):
        tag = match[0]
        if not re.search(r'\bloading=', tag):
            tag = tag[:-1] + ' loading="lazy">'
        if not re.search(r'\bdecoding=', tag):
            tag = tag[:-1] + ' decoding="async">'
        return tag
    source = re.sub(r'<img\b[^>]*>', image, source)
    for country, entries in additions.items():
        source = source.replace(f'{esc(country)} (0/5)', f'{esc(country)} ({len(entries)}/5)')
    books = len(re.findall(r'<td class="book">', source))
    covers = len(re.findall(r'<img\b', source))
    direct = sum(bool(re.search(r'goodreads.com/(?:en/)?book/show/', block)) for block in re.findall(r'<td class="book">.*?</td>', source, re.S))
    source = source.replace('<strong>744</strong>novels', f'<strong>{books}</strong>novels').replace('<strong>511</strong>catalogue', f'<strong>{covers}</strong>catalogue')
    (ROOT / 'index.html').write_text(source)
    # Snapshot counts are current; previous refresh descriptions stay dated.
    about = ROOT / 'about.html'
    text = about.read_text().replace('<strong>744</strong>', f'<strong>{books}</strong>').replace('647 books have source-based notes', f'{647+len(data["entries"])} books have source-based notes').replace('511 books have covers and 690 have direct Goodreads pages', f'{covers} books have covers and {direct} have direct Goodreads pages')
    text = text.replace('including diaspora writing.', 'including diaspora writing and, where explicitly stated, sustained residence and cultural affiliation.')
    text = text.replace('brief quoted synopsis extracts or catalogue-based thematic notes help orient you.', 'brief quoted synopsis extracts, source-based paraphrases or catalogue themes help orient you.').replace('Tags are keyword-based suggestions, not individual critical reviews.', 'Tags are brief thematic pointers, not individual critical reviews.')
    about.write_text(text)
    sources = ROOT / 'sources.html'
    text = sources.read_text()
    review = f'''<section class="country-research" id="country-review"><h2>Previously empty destinations</h2><p><strong>18 November 2026:</strong> reviewed all 21 destinations that had no selections. Added {len(data['entries'])} novels across {len(additions)} destinations, bringing the atlas to {books} books. Each addition records its title, author, form, edition year, country connection and sources. New notes are short source-based paraphrases.</p><p>Vatican City, Kiribati, the Federated States of Micronesia, Nauru, Palau and Tuvalu remain open. The checked leads include nonfiction, poetry and multi-author anthologies; none was silently counted as a novel. These are unresolved searches, not claims that the countries have no novel tradition.</p><p>Diaspora and long-term residence are identified explicitly. Original-language editions are labelled; an English catalogue title does not imply an English translation. Two ISBN lookups returned unrelated titles, so those matches were rejected. All new dates are labelled as edition dates.</p><p><a href="research/empty-country-additions.json">Read the 21-destination research audit, additions and unresolved leads ↗</a></p></section>'''
    if 'id="country-review"' not in text:
        text = text.replace('<h2>Where the records come from</h2>', review+'<h2>Where the records come from</h2>')
    text = text.replace('<strong>690 direct Goodreads links:</strong>', f'<strong>{direct} direct Goodreads links:</strong>').replace('<strong>511 covers:</strong>', f'<strong>{covers} covers:</strong>').replace('<strong>647 source-based notes:</strong>', f'<strong>{647+len(data["entries"])} source-based notes:</strong>').replace('The latest pass added 421', 'The earlier metadata refresh added 421').replace('the latest pass added 55', 'the earlier metadata refresh added 55').replace('<strong>587 edition-record matches:</strong>', '<strong>587 edition-record matches in the earlier catalogue audit:</strong>')
    sources.write_text(text)
    updates = ROOT / 'updates.html'
    text = updates.read_text()
    if 'id="empty-country-update"' not in text:
        text = text.replace('<ol class="update-list">', f'<ol class="update-list"><li id="empty-country-update"><time datetime="2026-11-18">18 November 2026</time><h3>First selections for 15 destinations</h3><p>{len(data["entries"])} source-checked novels added after reviewing the 21 empty destinations. Edition dates, original languages and diaspora or residence connections are documented. Six destinations remain under research. <a href="sources.html#country-review">Read the research notes ↗</a></p><p>All cover images load lazily and decode asynchronously.</p></li>')
    updates.write_text(text)
    notes_path = ROOT / 'research/reading-notes-audit.json'
    notes = json.loads(notes_path.read_text())
    keys = {(entry['title'], entry['author']) for entry in notes['entries']}
    for entry in data['entries']:
        if (entry['title'], entry['author']) not in keys:
            notes['entries'].append({'title':entry['title'], 'author':entry['author'], 'checked_at':entry['checked_at'], 'status':'source_based_thematic_note', 'note_type':'short_source_paraphrase', 'tags':entry['tags'], 'source':entry.get('note_source',entry['record_source']), 'source_type':'Manually reviewed book reference', 'method':'Short original paraphrase of linked book reference; country connection and edition evidence in empty-country-additions.json.'})
    notes_path.write_text(json.dumps(notes,ensure_ascii=False,indent=2)+'\n')
    research_path = ROOT / 'research/books.json'
    research = json.loads(research_path.read_text())
    keys = {(entry['country'],entry['title'],entry['author']) for entry in research}
    for entry in data['entries']:
        if (entry['country'],entry['title'],entry['author']) not in keys:
            research.append({'country':entry['country'],'title':entry['title'],'author':entry['author'],'meta':'','work':[entry['record_source']],'goodreads':[entry['goodreads']] if entry.get('goodreads') else [],'audit':'research/empty-country-additions.json'})
    research_path.write_text(json.dumps(research,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'books':books,'covers':covers,'direct_goodreads':direct,'new_books':len(data['entries']),'new_covers':sum(bool(entry.get('cover')) for entry in data['entries']),'destinations_filled':len(additions),'still_empty':len(unresolved)},indent=2))

if __name__ == '__main__':
    apply()
