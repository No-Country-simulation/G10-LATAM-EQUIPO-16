"""Paquete portable: un encoder compartido y tres cabezas, pesos ONNX en SSD."""
import json,shutil,hashlib
from pathlib import Path
import onnx
from onnx.external_data_helper import set_external_data
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'artifacts_mlp_int8'
DEPLOY=ROOT/'deploy_mlp_int8'

def main():
    summary=json.loads((OUT/'comparison.json').read_text(encoding='utf-8'))
    arch=summary['selected'];reports=summary['architectures'][arch]
    DEPLOY.mkdir(exist_ok=True);(DEPLOY/'heads').mkdir(exist_ok=True)
    # GitHub admite cada archivo de pesos: ningún tensor individual llega a 100 MB.
    source=ROOT/'artifacts_pca8/encoder/encoder_int8.onnx'
    if not source.exists():source=DEPLOY/'encoder.onnx'
    print('UN encoder fuente:',source,flush=True)
    model=onnx.load(str(source));limit=100_000_000;index=0;offset=0;stream=None
    try:
        for tensor in model.graph.initializer:
            if not tensor.HasField('raw_data'):continue
            data=tensor.raw_data
            assert len(data)<=limit,(tensor.name,len(data))
            if stream is None or offset+len(data)>limit:
                if stream:stream.close()
                name=f'weights-{index:03d}.bin';index+=1;offset=0
                stream=(DEPLOY/name).open('wb')
            stream.write(data)
            set_external_data(tensor,location=name,offset=offset,length=len(data))
            tensor.ClearField('raw_data');offset+=len(data)
    finally:
        if stream:stream.close()
    (DEPLOY/'encoder.onnx').write_bytes(model.SerializeToString())
    del model
    onnx.checker.check_model(str(DEPLOY/'encoder.onnx'))
    tokenizer_source=ROOT/'artifacts_pca8/encoder/tokenizer.json'
    if tokenizer_source.exists():shutil.copy2(tokenizer_source,DEPLOY/'tokenizer.json')
    else:assert (DEPLOY/'tokenizer.json').exists()
    for task in reports:
        shutil.copy2(OUT/arch/task/'head_int8.onnx',DEPLOY/'heads'/f'{task}.onnx')
        head=onnx.load(str(DEPLOY/'heads'/f'{task}.onnx'))
        ops=[n.op_type for n in head.graph.node]
        assert 'Sigmoid' in ops and ops.count('Relu')==len(reports[task]['dims'])-2
        assert 'MatMulInteger' in ops,ops
        print(task,'dimensiones:',reports[task]['dims'],'operadores:',sorted(set(ops)),flush=True)
    files={str(p.relative_to(DEPLOY)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()} for p in DEPLOY.rglob('*') if p.is_file() and p.name!='config.json'}
    config=dict(architecture=arch,dims=reports['es_faq']['dims'],tasks=list(reports),thresholds={t:r['threshold'] for t,r in reports.items()},
        encoder='MiniLM multilingual L12 v2, afinado v2 en RTX, congelado en esta comparación',
        source_revision='e8f8c211226b894fcb81acc59f3b34ba3efd5f42',precision='MatMul/Gather encoder INT8; MatMul cabezas INT8; activaciones ReLU/Sigmoid flotantes',
        max_tokens=128,max_chars=8000,batch=1,workers=1,process_budget_bytes=1_000_000_000,application_target_bytes=700_000_000,
        sentiment_mapping={'negativo':0,'neutro':.5,'mixto':.5,'positivo':1},files=files)
    (DEPLOY/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PAQUETE EN SSD:',DEPLOY,'MB:',sum(v['bytes'] for v in files.values())/1e6,flush=True)
    for name,value in files.items():print(name,value['bytes'],'bytes',flush=True)

if __name__=='__main__':main()
