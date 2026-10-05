"""Validar paquete portable extremo a extremo, batch 1, una cabeza por vez."""
import sys,json,gc,time
from pathlib import Path
import numpy as np
from serve_mlp_int8 import Predictor,session,TASKS
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'artifacts_mlp_int8'

def f1s(truth,pred,nclasses):
    matrix=np.zeros((nclasses,nclasses),dtype=int)
    for a,b in zip(truth,pred):matrix[int(a),int(b)]+=1
    values=[]
    for c in range(nclasses):
        tp=int(matrix[c,c]);den=int(matrix[c,:].sum()+matrix[:,c].sum())
        values.append(2*tp/den if den else 0.)
    return matrix,values

def categories(x,cuts):return np.where(x<cuts[0],0,np.where(x>cuts[1],2,1))

def metrics(task,y,p,cut):
    if task=='sentimiento':
        matrix,values=f1s(categories(y,(.25,.75)),categories(p,cut),3)
        return dict(f1_macro=float(np.mean(values)),mae=float(np.mean(np.abs(y-p))),f1_per_class=values,confusion_matrix=matrix.tolist(),support=len(y))
    matrix,values=f1s(y,p>=cut,2)
    return dict(f1=values[1],f1_macro=float(np.mean(values)),f1_per_class=values,confusion_matrix=matrix.tolist(),support=len(y),positives=int(y.sum()))

def main():
    predictor=Predictor();cache=np.load(OUT/'embeddings_int8.npy',mmap_mode='r')
    ids=json.loads((OUT/'embeddings_index.json').read_text(encoding='utf-8'))['ids'];lookup={v:i for i,v in enumerate(ids)}
    reports={};maxerror=0.;start=time.perf_counter()
    for task in TASKS:
        print('EVALUAR UNA CABEZA:',task,'CPU batch=1',flush=True)
        head=session(predictor.directory/'heads'/f'{task}.onnx')
        valy=[];valp=[]
        with (ROOT/'data'/f'{task}.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                row=json.loads(line)
                if row['split']!='validation':continue
                embedding=np.asarray(cache[lookup[row['id_mensaje']]:lookup[row['id_mensaje']]+1])
                valy.append(row[task]);valp.append(float(head.run(None,{'embedding':embedding})[0][0,0]))
        valy=np.asarray(valy);valp=np.asarray(valp)
        # INT8 dinámico puede cambiar con el batch: elegir cortes de producción solo en validation batch 1.
        if task=='sentimiento':
            choices=[(float(lo),float(hi)) for lo in np.arange(.15,.51,.025) for hi in np.arange(.5,.86,.025) if lo<hi]
            cut=max(choices,key=lambda c:metrics(task,valy,valp,c)['f1_macro'])
        else:cut=float(max(np.arange(.01,1.,.01),key=lambda c:metrics(task,valy,valp,c)['f1']))
        ys=[];ps=[];truncated=0;too_long=0
        with (ROOT/'data'/f'{task}.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                row=json.loads(line)
                if row['split']!='test':continue
                # La evaluación usa exactamente el mismo contrato del servicio.
                try:predictor.validate({'id_mensaje':row['id_mensaje'],'mensaje':row['mensaje']})
                except ValueError:too_long+=1;continue
                embedding=predictor.encode(row['mensaje'])
                expected=cache[lookup[row['id_mensaje']]:lookup[row['id_mensaje']]+1]
                error=float(np.max(np.abs(embedding-expected)));maxerror=max(error,maxerror)
                assert error<1e-5,error
                truncated+=int(bool(predictor.tokenizer.encode(row['mensaje']).overflowing))
                ys.append(row[task]);ps.append(float(head.run(None,{'embedding':embedding})[0][0,0]))
                if len(ys)%200==0:print('test procesados:',len(ys),'RAM MB:',predictor._check_ram(),flush=True)
        reports[task]=dict(threshold=cut,validation_batch1=metrics(task,valy,valp,cut),test_batch1=metrics(task,np.asarray(ys),np.asarray(ps),cut),
                           truncated_test=truncated,rejected_test=too_long)
        predictor.config['thresholds'][task]=cut
        del head;gc.collect()
        print('GUARDADO resultado y sesión liberada:',task,reports[task],flush=True)
    (predictor.directory/'config.json').write_text(json.dumps(predictor.config,ensure_ascii=False,indent=2),encoding='utf-8')
    result=dict(tasks=reports,max_embedding_error_vs_cache=maxerror,seconds=time.perf_counter()-start,
                scope='encoder INT8 y cabeza INT8 reales CPU, test batch 1; umbrales solo validation batch 1')
    (OUT/'package_evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('ERROR CACHE/PAQUETE:',maxerror,'tiempo segundos:',result['seconds'],flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
