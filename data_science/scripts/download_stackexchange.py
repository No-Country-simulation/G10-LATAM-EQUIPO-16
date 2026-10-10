"""Download public source data once; cached pages allow interruption and resume."""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(path)

def fetch(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CommunityLab-Dataset/1.0'})
            with urllib.request.urlopen(req, timeout=45) as response:
                data = json.load(response)
            if 'error_id' in data:
                raise RuntimeError(f"Stack Exchange error {data['error_id']}: {data.get('error_message')}")
            return data
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                raise
            time.sleep(max(int(exc.headers.get('Retry-After', 0)), 5 * 2**attempt))
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
            time.sleep(5 * 2**attempt)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pages', type=int, default=25, choices=range(1, 26),
                        help='Public anonymous API supports pages 1 through 25.')
    args = parser.parse_args()
    config_path = ROOT / 'data' / 'collection_config.json'
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding='utf-8'))
    else:
        now = datetime.now(timezone.utc)
        config = {'started_utc': now.isoformat(), 'todate': int(now.timestamp()),
                  'sites': ['es.stackoverflow', 'stackoverflow'], 'endpoints': ['questions', 'comments'],
                  'pagesize': 100, 'sort': 'creation', 'order': 'desc'}
        save(config_path, config)
    total = 0
    # Round robin: a partial run still includes both languages and both record types.
    exhausted = set()
    for page in range(1, args.pages + 1):
        for site in config['sites']:
            for endpoint in config['endpoints']:
                if (site, endpoint) in exhausted:
                    continue
                path = ROOT / 'data' / 'raw' / site / endpoint / f'{page:04d}.json'
                if path.exists():
                    wrapper = json.loads(path.read_text(encoding='utf-8'))
                    data = wrapper['response']
                    cached = True
                else:
                    params = dict(site=site, page=page, pagesize=100, filter='withbody',
                                  sort='creation', order='desc', todate=config['todate'])
                    url = 'https://api.stackexchange.com/2.3/' + endpoint + '?' + urllib.parse.urlencode(params)
                    data = fetch(url)
                    save(path, {'url': url, 'fetched_utc': datetime.now(timezone.utc).isoformat(),
                                'response': data})
                    cached = False
                total += len(data['items'])
                print(json.dumps({'site': site, 'endpoint': endpoint, 'page': page,
                                  'count': len(data['items']), 'total': total, 'cached': cached,
                                  'quota_remaining': data.get('quota_remaining')}), flush=True)
                if not data.get('has_more'):
                    exhausted.add((site, endpoint))
                if not cached:
                    time.sleep(max(1.1, data.get('backoff', 0)))
                    if data.get('quota_remaining', 1) <= 5:
                        print('Stopping before quota exhaustion; rerun later to resume.', flush=True)
                        return
    print(f'Completed: {total} source records (before deduplication).', flush=True)

if __name__ == '__main__':
    main()
