"""Materializar embeddings INT8 de a uno en SSD; no importa torch ni pandas."""
import os,sys,json,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'deps'))
from serve_mlp_int8 import session
OUT=ROOT/'artifacts_mlp_int8';OUT.mkdir(exist_ok=True)
source=ROOT/'data/es_faq.jsonl'
with source.open(encoding='utf-8') as stream:
    ids=[json.loads(line)['id_mensaje'] for line in stream]
lookup={v:i for i,v in enumerate(ids)}
from tokenizers import Tokenizer
directory=ROOT/'deploy_mlp_int8'
model_path=directory/'encoder.onnx'
tokenizer_path=directory/'tokenizer.json'
if not model_path.exists():
    model_path=ROOT/'artifacts_pca8/encoder/encoder_int8.onnx'
    tokenizer_path=ROOT/'artifacts_pca8/encoder/tokenizer.json'
print('ENCODER INT8 CPU -> SSD:',model_path,'sin Torch ni DataFrames',flush=True)
model=session(model_path)
inputs={v.name for v in model.get_inputs()}
tokenizer=Tokenizer.from_file(str(tokenizer_path));tokenizer.enable_truncation(max_length=128);tokenizer.no_padding()
cache=np.lib.format.open_memmap(OUT/'embeddings_int8.npy',mode='w+',dtype='float32',shape=(len(ids),384))
start=time.perf_counter()
with source.open(encoding='utf-8') as f:
    for count,line in enumerate(f,1):
        row=json.loads(line);tok=tokenizer.encode(row['mensaje'])
        feed={'input_ids':np.array([tok.ids],dtype=np.int64),'attention_mask':np.ones((1,len(tok.ids)),dtype=np.int64),'token_type_ids':np.array([tok.type_ids],dtype=np.int64)}
        cache[lookup[int(row['id_mensaje'])]]=model.run(None,{k:v for k,v in feed.items() if k in inputs})[0][0]
        if count%1000==0:print('Encoder INT8 CPU -> SSD:',count,'/',len(ids),flush=True)
cache.flush()
(OUT/'embeddings_index.json').write_text(json.dumps(dict(ids=ids,precision='int8',max_tokens=128,source=str(source),seconds=time.perf_counter()-start)),encoding='utf-8')
print('Embeddings INT8 guardados en SSD:',OUT/'embeddings_int8.npy',flush=True)
