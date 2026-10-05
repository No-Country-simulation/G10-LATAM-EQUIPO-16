"""Entrenar y exportar UNA cabeza MLP por proceso. Embeddings INT8 en SSD, entrenamiento CUDA."""
import os,sys,json,time,gc,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'deps'))
OUT=ROOT/'artifacts_mlp_int8'
TASKS=('es_faq','es_logro','sentimiento')
DIMS={'small':[384,16,4,1],'deep':[384,64,32,16,4,1]}

def train(task,architecture):
    import numpy as np,pandas as pd,torch
    from sklearn.metrics import f1_score,mean_absolute_error,confusion_matrix
    import onnx,onnxruntime as ort
    from onnxruntime.quantization import quantize_dynamic,QuantType
    assert torch.cuda.is_available(),'CUDA requerida'
    gpu=torch.cuda.get_device_name(0);assert '4070 Ti SUPER' in gpu,gpu
    print('[1] RTX DETECTADA:',gpu,flush=True)
    print('PyTorch',torch.__version__,'CUDA',torch.version.cuda,'VRAM GiB',torch.cuda.get_device_properties(0).total_memory/2**30,flush=True)
    torch.set_num_threads(8);torch.manual_seed(42);torch.cuda.manual_seed_all(42)
    df=pd.read_json(ROOT/'data'/f'{task}.jsonl',lines=True)
    print('[2] DATAFRAME',task,'shape=',df.shape,flush=True)
    label=task+'_gemini'
    columns=['id_mensaje','mensaje',task,'split']+([label] if label in df else [])
    print(df[columns].head().to_string(index=False),flush=True)
    print('Etiquetas y soporte:',df[task].value_counts().sort_index().to_dict(),flush=True)
    for value in sorted(df[task].unique()):print('Ejemplo target',value,':',df[df[task].eq(value)].iloc[0].mensaje,flush=True)
    ids=json.loads((OUT/'embeddings_index.json').read_text(encoding='utf-8'))['ids'];lookup={v:i for i,v in enumerate(ids)}
    indices=np.array([lookup[int(i)] for i in df.id_mensaje])
    cache=np.load(OUT/'embeddings_int8.npy',mmap_mode='r')
    y=df[task].to_numpy(dtype=np.float32)
    rows={split:np.flatnonzero(df.split.eq(split).to_numpy()) for split in ['train','validation','test']}
    print('[3] SSD mmap',cache.shape,'train/validation/test',{k:len(v) for k,v in rows.items()},flush=True)
    layers=[]
    for i,(a,b) in enumerate(zip(DIMS[architecture],DIMS[architecture][1:])):
        layers.append(torch.nn.Linear(a,b))
        if i<len(DIMS[architecture])-2:layers.append(torch.nn.ReLU())
    model=torch.nn.Sequential(*layers).cuda()
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.001)
    criterion=torch.nn.BCEWithLogitsLoss()
    out=OUT/architecture/task;out.mkdir(parents=True,exist_ok=True)
    print('[4] MODELO:',model,flush=True)
    print('Parámetros:',sum(p.numel() for p in model.parameters()),'device:',next(model.parameters()).device,flush=True)
    best=float('inf');stale=0;history=[];rng=np.random.default_rng(42);start=time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    @torch.inference_mode()
    def probabilities(which):
        model.eval();values=[]
        for offset in range(0,len(which),256):
            ix=which[offset:offset+256]
            x=torch.tensor(np.asarray(cache[indices[ix]]),device='cuda')
            values.append(model(x).sigmoid().flatten().cpu().numpy())
        return np.concatenate(values)
    for epoch in range(100):
        model.train();losses=[]
        shuffled=rng.permutation(rows['train'])
        for offset in range(0,len(shuffled),128):
            ix=shuffled[offset:offset+128]
            x=torch.tensor(np.asarray(cache[indices[ix]]),device='cuda')
            target=torch.tensor(y[ix,None],device='cuda')
            if epoch==0 and offset==0:
                print('CHECK CUDA: features',x.device,x.shape,'target',target.device,'head',next(model.parameters()).device,flush=True)
            optimizer.zero_grad(set_to_none=True)
            loss=criterion(model(x),target);loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.)
            optimizer.step();losses.append(float(loss))
        pv=probabilities(rows['validation'])
        tv=y[rows['validation']]
        vl=float(np.mean(-(tv*np.log(np.clip(pv,1e-7,1-1e-7))+(1-tv)*np.log(np.clip(1-pv,1e-7,1-1e-7)))))
        entry=dict(epoch=epoch+1,train_loss=float(np.mean(losses)),validation_loss=vl)
        history.append(entry)
        if vl<best-1e-5:
            best=vl;stale=0;torch.save(model.state_dict(),out/'best_head.pt')
        else:stale+=1
        if epoch==0 or (epoch+1)%10==0:print('[5] TRAIN',entry,flush=True)
        if stale>=15:print('Parada temprana en época',epoch+1,flush=True);break
    model.load_state_dict(torch.load(out/'best_head.pt',weights_only=True));model.eval()
    print('[6] EXPORTAR CABEZA FP32 ONNX; salida Sigmoid.',flush=True)
    class Head(torch.nn.Module):
        def __init__(self):super().__init__();self.network=model
        def forward(self,embedding):return self.network(embedding).sigmoid()
    torch.onnx.export(Head(),torch.zeros(1,384,device='cuda'),str(out/'head_fp32.onnx'),input_names=['embedding'],output_names=['score'],
                      dynamic_axes={'embedding':{0:'batch'},'score':{0:'batch'}},opset_version=17,dynamo=False)
    peak_vram=torch.cuda.max_memory_allocated()/1e6
    # Una sola cabeza: comparar su ONNX FP32 antes de cuantizar; liberar luego sesión y modelo CUDA.
    options=ort.SessionOptions();options.intra_op_num_threads=options.inter_op_num_threads=1
    session=ort.InferenceSession(str(out/'head_fp32.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
    sample=np.asarray(cache[indices[rows['validation'][:8]]])
    with torch.inference_mode():expected=model(torch.tensor(sample,device='cuda')).sigmoid().cpu().numpy()
    error=float(np.max(np.abs(expected-session.run(None,{'embedding':sample})[0])));assert error<1e-5,error
    del session,model,optimizer;gc.collect();torch.cuda.empty_cache()
    print('Validación CUDA vs ONNX FP32, error:',error,flush=True)
    print('[7] CUANTIZAR CABEZA -> INT8, MatMul; ReLU y Sigmoid conservados.',flush=True)
    quantize_dynamic(str(out/'head_fp32.onnx'),str(out/'head_int8.onnx'),op_types_to_quantize=['MatMul'],weight_type=QuantType.QInt8,per_channel=True)
    session=ort.InferenceSession(str(out/'head_int8.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
    def predict_rows(which):
        outputs=[]
        for offset in range(0,len(which),256):
            ix=which[offset:offset+256]
            outputs.append(session.run(None,{'embedding':np.asarray(cache[indices[ix]])})[0].flatten())
        return np.concatenate(outputs)
    valp=predict_rows(rows['validation']);testp=predict_rows(rows['test'])
    if task=='sentimiento':
        def categorise(p,cuts):return np.where(p<cuts[0],0,np.where(p>cuts[1],2,1))
        truth=categorise(y[rows['validation']],(.25,.75))
        choices=[(float(lo),float(hi)) for lo in np.arange(.15,.51,.025) for hi in np.arange(.5,.86,.025) if lo<hi]
        cuts=max(choices,key=lambda c:f1_score(truth,categorise(valp,c),labels=[0,1,2],average='macro',zero_division=0))
        def metrics(p,which):
            target=categorise(y[which],(.25,.75));pred=categorise(p,cuts)
            return dict(f1_macro=float(f1_score(target,pred,labels=[0,1,2],average='macro',zero_division=0)),
                        mae=float(mean_absolute_error(y[which],p)),confusion_matrix=confusion_matrix(target,pred,labels=[0,1,2]).tolist(),support=len(which))
        threshold=list(cuts)
    else:
        threshold=float(max(np.arange(.01,1.,.01),key=lambda t:f1_score(y[rows['validation']],valp>=t,zero_division=0)))
        def metrics(p,which):return dict(f1=float(f1_score(y[which],p>=threshold,zero_division=0)),
            f1_macro=float(f1_score(y[which],p>=threshold,labels=[0,1],average='macro',zero_division=0)),support=len(which),positives=int(y[which].sum()))
    report=dict(task=task,architecture=architecture,dims=DIMS[architecture],gpu=gpu,cuda_checks=True,history=history,
                parameters=sum(a*b+b for a,b in zip(DIMS[architecture],DIMS[architecture][1:])),epochs=len(history),
                train_seconds=time.perf_counter()-start,peak_training_vram_mb=peak_vram,threshold=threshold,
                fp32_parity_error=error,validation=metrics(valp,rows['validation']),test=metrics(testp,rows['test']),
                encoder='fine-tuned v2 frozen INT8',data_cache='embeddings_int8.npy',precision='encoder INT8 + MLP MatMul INT8',
                preprocessing='primeros 128 tokens; sin PCA; sin normalización del embedding',seed=42)
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('[8] TEST con encoder INT8 + cabeza INT8:',report['test'],'cortes validation:',threshold,flush=True)
    print('ONNX INT8 guardado SSD:',out/'head_int8.onnx',(out/'head_int8.onnx').stat().st_size,'bytes',flush=True)
    del session,df,cache;gc.collect();print('[9] FIN. Proceso terminado antes de otra cabeza.',flush=True)

if __name__=='__main__':
    import argparse
    sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser();p.add_argument('task',choices=TASKS);p.add_argument('architecture',choices=DIMS)
    args=p.parse_args();train(args.task,args.architecture)
