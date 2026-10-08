"""Offline assertions for source fidelity, leakage, labels and the ingestion contract."""
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from label_gemini import INTENTS, SENTIMENTS
from prepare_dataset import plain
import html

ROOT = Path(__file__).resolve().parents[1]

def main():
    rows = [json.loads(x) for x in (ROOT / 'exports' / 'corpus.jsonl').read_text(encoding='utf-8').splitlines()]
    assert rows and len(rows) == len({r['id'] for r in rows})
    raw = {}
    for path in (ROOT / 'data' / 'raw').glob('*/*/*.json'):
        wrapper = json.loads(path.read_text(encoding='utf-8'))
        raw[path.relative_to(ROOT).as_posix()] = wrapper['response']['items']
    groups, texts = defaultdict(set), defaultdict(set)
    for r in rows:
        assert r['texto'].strip() and r['is_synthetic'] is False and r['url'].startswith('https://')
        assert r['license'] and r['autor']
        key = 'question_id' if r['source_type'] == 'question' else 'comment_id'
        source = next(x for x in raw[r['raw_file']] if x[key] == r['source_id'])
        expected = (html.unescape(source['title']) + '\n\n' + plain(source['body'])).strip() if key == 'question_id' else plain(source['body'])
        assert expected == r['texto'], r['id']
        assert hashlib.sha256(r['texto'].encode()).hexdigest() == r['text_sha256']
        groups[r['thread_id']].add(r['split'])
        texts[r['normalized_text_sha256']].add(r['split'])
        if r['annotation']:
            a = r['annotation']
            assert a['id'] == r['id'] and a['text_sha256'] == r['text_sha256']
            assert a['intencion'] in INTENTS and a['sentimiento'] in SENTIMENTS
            assert a['evidence_verified'] == (a['evidencia'] in r['texto'])
            assert a['human_reviewed'] is False
        if r['eligible_silver_training']:
            assert r['annotation'] and r['annotation']['evidence_verified'] and not r['duplicate_of'] and not r['needs_priority_review']
    assert all(len(s) == 1 for s in groups.values()), 'Thread leakage'
    assert all(len(s) == 1 for s in texts.values()), 'Duplicate-text leakage'
    batch = json.loads((ROOT / 'exports' / 'ingesta.json').read_text(encoding='utf-8'))
    assert set(batch) == {'origen_comunidad','periodo_referencia','interacciones'}
    assert len(batch['interacciones']) == len(rows)
    for source, interaction in zip(rows, batch['interacciones']):
        assert set(interaction) == {'autor','canal','tipo','texto'}
        assert interaction['texto'] == source['texto']
        assert all(isinstance(x,str) and x for x in interaction.values())
    with (ROOT / 'exports' / 'ingesta.csv').open(encoding='utf-8',newline='') as f:
        assert list(csv.DictReader(f)) == batch['interacciones']
    with (ROOT / 'exports' / 'corpus.csv').open(encoding='utf-8',newline='') as f:
        csv_rows = list(csv.DictReader(f))
    assert [r['texto'] for r in csv_rows] == [r['texto'] for r in rows]
    result = {'status':'passed','records_verified':len(rows),'source_text_fidelity':True,
              'unique_ids':True,'thread_split_overlap':0,'exact_normalized_text_split_overlap':0,
              'ingestion_json_csv_roundtrip':True,'annotation_provenance_checked':True}
    (ROOT/'reports'/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__ == '__main__':
    main()
