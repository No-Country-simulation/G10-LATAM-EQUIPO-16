"""Create two manageable GitHub downloads and one complete local archive."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    files = [p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
             and p.name != 'MANIFEST.sha256.json' and not p.name.startswith('rejected_responses')
             and p.name != 'normalized.jsonl' and not p.name.endswith('.tmp')]
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    manifest_path = ROOT / 'MANIFEST.sha256.json'
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    files.append(manifest_path)
    source_files = [p for p in files if p.relative_to(ROOT).parts[:2] in [('data','raw'),('data','thread_metadata')]]
    source_set = set(source_files)
    main_files = [p for p in files if p not in source_set]
    for name, selected in [('CommunityLab_Dataset.zip', main_files), ('StackExchange_Fuentes.zip', source_files),
                           ('CommunityLab_Dataset_Completo.zip', files)]:
        path = ROOT.parent / name
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, 9) as archive:
            for p in sorted(selected):
                archive.write(p, ROOT.name + '/' + p.relative_to(ROOT).as_posix())
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
        print(json.dumps({'archive': name, 'bytes': path.stat().st_size, 'files': len(selected)}))

if __name__ == '__main__':
    main()
