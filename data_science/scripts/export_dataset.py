"""Build training-ready indexes and ingestion exports without fabricating labels."""
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def write_lines(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in values), encoding='utf-8')

def text_key(text):
    text = ' '.join(unicodedata.normalize('NFKC', text).casefold().split())
    return hashlib.sha256(text.encode()).hexdigest()

def main():
    rows = load_lines(ROOT / 'data' / 'normalized.jsonl')
    labels = {}
    for path in sorted((ROOT / 'data' / 'annotations').glob('gemini_labels_*.jsonl')):
        for label in load_lines(path):
            labels[label['id']] = label
    answer_map_path = ROOT / 'data' / 'answer_to_question.json'
    answer_map = json.loads(answer_map_path.read_text(encoding='utf-8')) if answer_map_path.exists() else {}
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[max(a, b)] = min(a, b)
    hashes = {}
    for row in rows:
        pid = row['parent_post_id']
        qid = answer_map.get(f"{row['site']}:{pid}", pid)
        row['thread_id'] = f"{row['site']}:{qid}"
        row['thread_resolution'] = 'question' if row['source_type'] == 'question' else ('answer_parent_api' if f"{row['site']}:{pid}" in answer_map else 'direct_post')
        row['normalized_text_sha256'] = text_key(row['texto'])
        row['duplicate_of'] = hashes.get(row['normalized_text_sha256'], {}).get('id')
        find(row['thread_id'])
        if row['duplicate_of']:
            union(row['thread_id'], hashes[row['normalized_text_sha256']]['thread_id'])
        else:
            hashes[row['normalized_text_sha256']] = row
    for row in rows:
        group = find(row['thread_id'])
        row['split_group'] = group
        bucket = int(hashlib.sha256(('communitylab-v1:' + group).encode()).hexdigest()[:8], 16) % 100
        row['split'] = 'train' if bucket < 80 else ('validation' if bucket < 90 else 'test')
        annotation = labels.get(row['id'])
        if annotation:
            if annotation['text_sha256'] != row['text_sha256']:
                raise ValueError('Stale annotation: ' + row['id'])
            row['annotation'] = annotation
            row['intencion'] = annotation['intencion']
            row['sentimiento'] = annotation['sentimiento']
            row['es_testimonio'] = annotation['es_testimonio']
            row['es_logro'] = annotation['es_logro']
            row['annotation_status'] = 'silver_unreviewed'
            row['needs_priority_review'] = (not annotation['evidence_verified'] or annotation['confianza'] < .8
                                            or annotation['intencion'] == 'ambiguo' or annotation['sentimiento'] == 'indeterminado')
        else:
            row.update({'annotation': None, 'intencion': 'pregunta_tecnica' if row['source_type'] == 'question' else None,
                        'sentimiento': None, 'es_testimonio': None, 'es_logro': None,
                        'annotation_status': 'source_only' if row['source_type'] == 'question' else 'pending',
                        'needs_priority_review': row['source_type'] == 'comment'})
        row['eligible_silver_training'] = bool(annotation and not row['duplicate_of'] and not row['needs_priority_review'])
    exports = ROOT / 'exports'
    exports.mkdir(exist_ok=True)
    write_lines(exports / 'corpus.jsonl', rows)
    fields = ['id','texto','idioma_sitio','source_type','intencion','sentimiento','es_testimonio','es_logro',
              'annotation_status','needs_priority_review','eligible_silver_training','split','thread_id','split_group',
              'duplicate_of','url','autor','author_url','license','created_utc','tags']
    with (exports / 'corpus.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(row[k], ensure_ascii=False) if isinstance(row[k], list) else row[k] for k in fields})
    # Matches the team's Java DTO and Python Interaction; annotation metadata stays in corpus.
    interactions = []
    for row in rows:
        kind = row['intencion']
        kind = kind if kind in ('testimonio','pregunta_tecnica','feedback','logro') else 'otro'
        interactions.append({'autor': row['autor'], 'canal': row['canal'], 'tipo': kind, 'texto': row['texto']})
    config = json.loads((ROOT / 'data' / 'collection_config.json').read_text(encoding='utf-8'))
    batch = {'origen_comunidad': 'StackExchange_ES_EN', 'periodo_referencia': config['started_utc'],
             'interacciones': interactions}
    write_json(exports / 'ingesta.json', batch)
    with (exports / 'ingesta.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['autor','canal','tipo','texto'])
        writer.writeheader()
        writer.writerows(interactions)
    write_json(exports / 'ingesta_index.json', [r['id'] for r in rows])
    for split in ('train','validation','test'):
        write_lines(exports / f'{split}_index.jsonl', [{'id': r['id'], 'split_group': r['split_group'],
                    'eligible_silver_training': r['eligible_silver_training']} for r in rows if r['split'] == split])
    # Small reproducible review set spanning language and labels, never synthetic.
    grouped = defaultdict(list)
    for row in rows:
        if row['source_type'] == 'comment' and row['annotation']:
            grouped[(row['idioma_sitio'], row['intencion'], row['sentimiento'])].append(row)
    sample = []
    for key in sorted(grouped):
        sample += sorted(grouped[key], key=lambda r: hashlib.sha256(r['id'].encode()).hexdigest())[:3]
    write_lines(exports / 'revision_humana.jsonl', [dict(r, human_intent=None, human_sentiment=None, reviewer=None) for r in sample])
    demo_rows = []
    for lang in ('es','en'):
        for kind in ('pregunta_tecnica','testimonio','logro','conversacion_trivial','ambiguo'):
            candidates = [r for r in rows if r['idioma_sitio'] == lang and r['intencion'] == kind and len(r['texto']) < 2000
                          and (r['annotation'] is None or r['annotation']['evidence_verified'])]
            if candidates:
                demo_rows.append(candidates[0])
    by_id = {r['id']: i for i, r in enumerate(rows)}
    write_json(exports / 'demo_ingesta.json', dict(batch, interacciones=[interactions[by_id[r['id']]] for r in demo_rows]))
    write_lines(exports / 'demo_fuentes.jsonl', demo_rows)
    usage = [x for p in (ROOT / 'data' / 'annotations').glob('usage_*.jsonl') for x in load_lines(p)]
    report = {
        'generated_utc': datetime.now(timezone.utc).isoformat(), 'total_records': len(rows),
        'unique_ids': len({r['id'] for r in rows}), 'unique_normalized_texts': len(hashes),
        'duplicates_by_text': sum(bool(r['duplicate_of']) for r in rows),
        'source_counts': dict(Counter(r['source_type'] for r in rows)),
        'language_site_counts': dict(Counter(r['idioma_sitio'] for r in rows)),
        'licenses': dict(Counter(r['license'] for r in rows)),
        'gemini_labeled_comments': sum(bool(r['annotation']) for r in rows),
        'pending_comments': sum(r['annotation_status'] == 'pending' for r in rows),
        'intent_counts': dict(Counter(r['intencion'] or 'pending' for r in rows)),
        'sentiment_counts': dict(Counter(r['sentimiento'] or 'not_labeled' for r in rows)),
        'testimonio_positive_silver': sum(r['es_testimonio'] is True for r in rows),
        'logro_positive_silver': sum(r['es_logro'] is True for r in rows),
        'evidence_not_literal': sum(bool(r['annotation']) and not r['annotation']['evidence_verified'] for r in rows),
        'eligible_silver_training': sum(r['eligible_silver_training'] for r in rows),
        'split_counts': dict(Counter(r['split'] for r in rows)),
        'human_reviewed': 0, 'synthetic_records': 0, 'resolved_answer_parents': len(answer_map),
        'site_date_ranges': {s: {'from': min(r['created_utc'] for r in rows if r['site'] == s),
                               'to': max(r['created_utc'] for r in rows if r['site'] == s)} for s in config['sites']},
        'successful_annotation_calls': len(usage),
        'successful_annotation_tokens': sum(x.get('usage',{}).get('totalTokenCount',0) for x in usage),
        'token_count_note': 'Successful batches only; excludes probes and rejected attempts.',
    }
    write_json(ROOT / 'reports' / 'quality_report.json', report)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
