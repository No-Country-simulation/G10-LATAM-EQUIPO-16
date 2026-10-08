"""Copiar entrega revisada, sin cachés ni deps; proteger token de un texto fuente al publicar."""
import json,shutil,re,hashlib,ast
from pathlib import Path
from finalize_mlp import delivery_files
ROOT=Path(__file__).resolve().parent
TARGET=ROOT/'github_delivery/data_science/2026-10-04'
assert TARGET.resolve().is_relative_to((ROOT/'github_delivery').resolve())
PATTERN=re.compile(r'(?:github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{25,}|hf_[A-Za-z0-9]{25,})')

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    TARGET.mkdir(parents=True,exist_ok=True)
    for source in delivery_files():
        destination=TARGET/source.relative_to(ROOT)
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,destination)
    # No modificar original SSD ni los DataFrames. Una redacción solo en cuerpo fuente publicado.
    source=ROOT/'data/corpus_original.jsonl';destination=TARGET/'data/corpus_original.jsonl'
    changes=[]
    with source.open(encoding='utf-8') as original,destination.open('w',encoding='utf-8',newline='\n') as published:
        for number,line in enumerate(original,1):
            if PATTERN.search(line):
                row=json.loads(PATTERN.sub('[TOKEN_REDACTADO_PARA_PUBLICACION]',line))
                row['publication_transformations']=['Redactar token presente en texto fuente; original íntegro conservado en SSD local.']
                published.write(json.dumps(row,ensure_ascii=False)+'\n')
                changes.append({'line':number,'id':row['id'],'url':row.get('url')})
            else:published.write(line)
    publication=dict(original_sha256=digest(source),published_sha256=digest(destination),redacted_rows=changes,
        training_data_unchanged=True,scope='Solo copia de publicación del corpus original; sin alterar títulos ni comentarios usados para entrenamiento.')
    (TARGET/'data/publication.json').write_text(json.dumps(publication,ensure_ascii=False,indent=2),encoding='utf-8')
    readme=TARGET/'README.md'
    with readme.open('a',encoding='utf-8') as stream:
        stream.write('\nPublicación GitHub: la copia corpus_original.jsonl tiene un token del cuerpo de una pregunta oculto; original íntegro en SSD local. data/publication.json registra SHA original/publicado y fila modificada. Los DataFrames de entrenamiento no cambian.\n')
    for path in TARGET.rglob('*.py'):ast.parse(path.read_text(encoding='utf-8-sig'))
    # Evitar publicar dependencias/copias del encoder que no pertenecen a esta entrega.
    assert not (TARGET/'deps').exists()
    files=[]
    for path in sorted(TARGET.rglob('*')):
        if not path.is_file() or path.name=='MANIFEST.sha256.json':continue
        assert path.stat().st_size<100_000_000,(path,path.stat().st_size)
        if path.suffix in ('.jsonl','.ipynb','.json','.py','.log'):
            assert not PATTERN.search(path.read_text(encoding='utf-8-sig')),f'Token sin ocultar en {path}'
        files.append(dict(path=str(path.relative_to(TARGET)).replace('\\','/'),bytes=path.stat().st_size,sha256=digest(path)))
    (TARGET/'MANIFEST.sha256.json').write_text(json.dumps(dict(scope='Entrega publicada MLP INT8; corpus con redacción indicada en data/publication.json',files=files),indent=2),encoding='utf-8')
    print('ENTREGA:',TARGET,'archivos:',len(files),'MB:',sum(f['bytes'] for f in files)/1e6,'redacciones fuente:',len(changes),flush=True)

if __name__=='__main__':main()
