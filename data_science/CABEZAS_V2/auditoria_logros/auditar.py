"""Audita las entradas de LOGROS sin entrenar ni modificar los modelos."""
import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import f1_score
from tokenizers import Tokenizer

parser = argparse.ArgumentParser()
parser.add_argument('--base', type=Path, default=Path(__file__).resolve().parents[1], help='Carpeta CABEZAS_V2')
parser.add_argument('--salida', type=Path, default=Path(__file__).with_name('resultado_reproducido.json'))
args = parser.parse_args()
df = pd.read_json(args.base / 'data/es_logro.jsonl', lines=True)
df['normalizado'] = df.mensaje.map(lambda s: ' '.join(str(s).casefold().split()))
tok = Tokenizer.from_file(str(args.base / 'inferencia_fp32/modelos/tokenizer.json'))
tok.enable_truncation(max_length=128)
tok.no_padding()
df['tokens'] = [tuple(x.ids) for x in tok.encode_batch(df.mensaje.tolist())]
result = {'n': len(df), 'comparaciones': {}}
for key in ['mensaje', 'normalizado', 'tokens']:
    groups = df.groupby(key, sort=False).agg(n=('id', 'size'), splits=('split', lambda s: sorted(set(s))))
    cross = groups[groups.splits.map(len) > 1]
    known = set(df.loc[df.split.eq('train'), key])
    hits = df[df.split.ne('train') & df[key].isin(known)]
    result['comparaciones'][key] = {
        'grupos_entre_particiones': len(cross), 'filas': int(cross.n.sum()),
        'validation_ya_en_train': int(hits.split.eq('validation').sum()),
        'test_ya_en_train': int(hits.split.eq('test').sum()),
    }
    if key == 'tokens':
        result['ids_evaluacion_entrada_ya_en_train'] = hits[['id', 'split']].to_dict('records')
        scores = pd.read_json(args.base / 'cabezas/es_logro_test_scores.jsonl', lines=True)
        filtered = scores[~scores.id.isin(hits.loc[hits.split.eq('test'), 'id'])]
        result['umbral_decision'] = 0.63
        result['f1_test_original'] = float(f1_score(scores.target, scores.score >= .63))
        result['f1_test_sin_entradas_identicas_a_train'] = float(f1_score(filtered.target, filtered.score >= .63))
result['ejemplo_mismo_proyecto'] = df[df.id.isin([94, 1374])][['id', 'split', 'mensaje', 'es_logro']].to_dict('records')
args.salida.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=True, indent=2))
