"""Apply curated, source-backed orientation themes without changing book prose."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def run():
    data = json.loads((ROOT / 'research/reviewed-themes.json').read_text())
    entries = {(e['title'], e['author']): e for e in data['entries']}
    assert len(entries) == len(data['entries']), 'Duplicate theme records'
    for entry in entries.values():
        assert len(entry['tags']) <= 2
        assert len(entry['tags']) == len(set(entry['tags']))
        assert all(tag in data['vocabulary'] for tag in entry['tags'])
    seen = set()
    count = 0

    def update(match):
        nonlocal count
        row = match.group()
        book = re.search(r'<td class="book"><strong>(.*?)</strong><div class="author">(.*?)</div>', row, re.S)
        if not book:
            return row
        key = tuple(html.unescape(s) for s in book.groups())
        assert key in entries, 'Missing reviewed themes: ' + str(key)
        entry = entries[key]
        seen.add(key)
        count += 1
        topics = '<div class="book-topics" aria-label="Reading themes">' + ''.join('<span>' + html.escape(tag) + '</span>' for tag in entry['tags']) + '</div>' if entry['tags'] else ''

        def reason(match):
            body = re.sub(r'<div class="book-topics"[^>]*>.*?</div>', '', match.group(1), flags=re.S)
            # Keep summary, country connection, and any other contextual notes intact.
            return '<td class="reason">' + body + topics + '</td>'

        return re.sub(r'<td class="reason">(.*?)</td>', reason, row, count=1, flags=re.S)

    path = ROOT / 'index.html'
    updated = re.sub(r'<tr>.*?</tr>', update, path.read_text(), flags=re.S)
    assert seen == set(entries), 'Some theme records did not match the catalogue'
    path.write_text(updated)
    path = ROOT / 'research/reading-notes-audit.json'
    audit = json.loads(path.read_text())
    audit['theme_review'] = {'checked_at': data['checked_at'], 'method': data['method'], 'record': 'reviewed-themes.json'}
    for row in audit['entries']:
        entry = entries[(row['title'], row['author'])]
        row['tags'] = entry['tags']
        row['tags_checked_at'] = data['checked_at']
        row['theme_source'] = entry['source']
        row['theme_source_type'] = entry['source_type']
        row['theme_evidence'] = entry['evidence']
        row['theme_review_method'] = entry['method']
    path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
    print('Applied reviewed themes to', count, 'selections')


if __name__ == '__main__':
    run()
