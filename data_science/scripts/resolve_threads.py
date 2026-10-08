"""Resolve answer-parent questions so future train/test splits do not leak threads."""
import json
import time
import urllib.parse
from datetime import datetime, timezone
from download_stackexchange import ROOT, fetch, save

def main():
    rows = [json.loads(line) for line in (ROOT / 'data' / 'normalized.jsonl').read_text(encoding='utf-8').splitlines()]
    mapping = {}
    for site in ('es.stackoverflow', 'stackoverflow'):
        ids = sorted({r['parent_post_id'] for r in rows if r['source_type'] == 'comment' and r['site'] == site})
        for offset in range(0, len(ids), 100):
            block = ids[offset:offset + 100]
            path = ROOT / 'data' / 'thread_metadata' / site / f'{offset // 100:04d}.json'
            if path.exists():
                data = json.loads(path.read_text(encoding='utf-8'))['response']
            else:
                url = 'https://api.stackexchange.com/2.3/answers/' + ';'.join(map(str, block)) + '?' + urllib.parse.urlencode({'site': site, 'pagesize': 100})
                data = fetch(url)
                save(path, {'url': url, 'requested_ids': block, 'fetched_utc': datetime.now(timezone.utc).isoformat(), 'response': data})
                time.sleep(max(1.1, data.get('backoff', 0)))
            for answer in data['items']:
                mapping[f"{site}:{answer['answer_id']}"] = answer['question_id']
            print(f'{site}: {min(offset + 100, len(ids))}/{len(ids)} parent posts', flush=True)
    save(ROOT / 'data' / 'answer_to_question.json', mapping)
    print(f'Resolved {len(mapping)} answers.', flush=True)

if __name__ == '__main__':
    main()
