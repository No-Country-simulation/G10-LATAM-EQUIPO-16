"""Normalize authentic messages; preserve provenance and source HTML in raw pages."""
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def handle_starttag(self, tag, attrs):
        if tag in ('p', 'br', 'pre', 'li', 'div', 'blockquote'):
            self.parts.append('\n')
    def handle_endtag(self, tag):
        if tag in ('p', 'pre', 'li', 'div', 'blockquote'):
            self.parts.append('\n')

def plain(value):
    parser = TextParser()
    parser.feed(value)
    return re.sub(r'\n{3,}', '\n\n', ''.join(parser.parts)).strip()

def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def main():
    records = {}
    for path in sorted((ROOT / 'data' / 'raw').glob('*/*/*.json')):
        wrapper = json.loads(path.read_text(encoding='utf-8'))
        site, endpoint = path.parts[-3:-1]
        domain = 'es.stackoverflow.com' if site == 'es.stackoverflow' else 'stackoverflow.com'
        for item in wrapper['response']['items']:
            question = endpoint == 'questions'
            sid = item['question_id' if question else 'comment_id']
            record_id = f"{site}:{'question' if question else 'comment'}:{sid}"
            title = html.unescape(item.get('title', ''))
            body = plain(item['body'])
            text = (title + '\n\n' + body).strip() if question else body
            owner = item.get('owner', {})
            parent_id = item.get('post_id', sid)
            url = item.get('link') or f'https://{domain}/posts/{parent_id}#comment{sid}_{parent_id}'
            records.setdefault(record_id, {
                'id': record_id, 'source': 'stackexchange', 'site': site,
                'source_type': 'question' if question else 'comment', 'source_id': sid,
                'parent_post_id': parent_id, 'url': url,
                'autor': html.unescape(owner.get('display_name', 'usuario_eliminado')),
                'author_url': owner.get('link'), 'author_id': owner.get('user_id'),
                'canal': site, 'idioma_sitio': 'es' if site == 'es.stackoverflow' else 'en',
                'titulo': title, 'texto': text, 'text_sha256': digest(text),
                'created_utc': datetime.fromtimestamp(item['creation_date'], timezone.utc).isoformat(),
                'fetched_utc': wrapper['fetched_utc'],
                'license_api': item.get('content_license'),
                'license': item.get('content_license') or ('CC BY-SA 4.0' if item['creation_date'] >= 1525219200 else None),
                'license_method': 'api' if item.get('content_license') else 'publication_date_and_site_policy',
                'license_policy_url': 'https://stackoverflow.com/help/licensing',
                'tags': item.get('tags', []), 'score': item.get('score'),
                'answer_count': item.get('answer_count'), 'view_count': item.get('view_count'),
                'is_answered': item.get('is_answered'),
                'source_label': 'pregunta_tecnica' if question else 'comentario',
                'source_label_method': 'api_endpoint', 'faq_candidate': question,
                'faq_frequency_verified': False, 'is_synthetic': False,
                'raw_file': path.relative_to(ROOT).as_posix(),
                'transformations': 'HTML to text, entities decoded; title prepended for questions; no translation',
            })
    path = ROOT / 'data' / 'normalized.jsonl'
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records.values()), encoding='utf-8')
    print(json.dumps({'normalized_records': len(records), 'path': str(path)}))

if __name__ == '__main__':
    main()
