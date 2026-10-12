import argparse,json,copy
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from torch import nn
from sklearn.metrics import f1_score,precision_score,recall_score,confusion_matrix,mean_absolute_error

class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        dims=[384,64,32,16,8,4,1]
        layers=[]
        for i in range(len(dims)-1):
            layers.append(nn.Linear(dims[i],dims[i+1]))
            if i<len(dims)-2: layers.append(nn.ReLU())
        self.layers=nn.Sequential(*layers)
    def forward(self,x): return self.layers(x)
    def score(self,x): return torch.sigmoid(self(x))

def train(task,epochs=100):
    root=Path(__file__).resolve().parent
    assert torch.cuda.is_available(),"Este kernel necesita PyTorch CUDA"
    gpu=torch.cuda.get_device_name(0)
    assert "4070 Ti SUPER" in gpu, f"GPU inesperada: {gpu}"
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    df=pd.read_json(root/'embeddings'/f'{task}.jsonl',lines=True)
    features=np.load(root/'embeddings'/f'{task}.npy')
    assert features.shape==(len(df),384)
    ix={s:np.flatnonzero(df.split.eq(s)) for s in ['train','validation','test']}
    assert all(len(v)>0 for v in ix.values()),"Falta una partición"
    y=df.target.to_numpy(dtype=np.float32)
    assert set(np.unique(y)).issubset({0,.5,1})
    x=torch.tensor(features,device='cuda')
    targets=torch.tensor(y[:,None],device='cuda')
    model=MLP().cuda()
    optimizer=torch.optim.AdamW(model.parameters(),lr=.001,weight_decay=.001)
    train_targets=y[ix['train']]
    if task not in ['sentimiento','sentimiento_cardiff']:
        positives=float(train_targets.sum()); negatives=len(train_targets)-positives
        assert positives>0 and negatives>0,"Train necesita ambas clases"
        criterion=nn.BCEWithLogitsLoss(pos_weight=torch.tensor([negatives/positives],device='cuda'),reduction='none')
        sample_weights=torch.ones_like(targets)
        weighting={'pos_weight':negatives/positives}
    else:
        counts={float(v):int((train_targets==v).sum()) for v in np.unique(train_targets)}
        weights={v:len(train_targets)/(len(counts)*n) for v,n in counts.items()}
        criterion=nn.BCEWithLogitsLoss(reduction='none')
        sample_weights=torch.tensor([weights.get(float(v),1.) for v in y],device='cuda')[:,None]
        weighting={'class_weights':weights}
    print('GPU:',gpu,'Tarea:',task,'Pesos train:',weighting,flush=True)
    print(model,flush=True)
    print('Parámetros:',sum(p.numel() for p in model.parameters()),flush=True)
    best=float('inf'); stale=0; history=[]; best_state=None
    for epoch in range(epochs):
        model.train(); total=0.; seen=0
        shuffled=ix['train'][np.random.default_rng(42+epoch).permutation(len(ix['train']))]
        for start in range(0,len(shuffled),128):
            idx=shuffled[start:start+128]
            optimizer.zero_grad(set_to_none=True)
            loss=(criterion(model(x[idx]),targets[idx])*sample_weights[idx]).mean()
            loss.backward(); optimizer.step()
            total+=loss.item()*len(idx); seen+=len(idx)
        model.eval()
        with torch.inference_mode():
            val=ix['validation']
            validation=(criterion(model(x[val]),targets[val])*sample_weights[val]).mean().item()
        history.append({'epoch':epoch+1,'train_bce':total/seen,'validation_bce':validation})
        if validation<best-1e-5:
            best=validation; stale=0
            best_state={k:v.detach().cpu().clone() for k,v in model.state_dict().items()}
        else: stale+=1
        if epoch==0 or (epoch+1)%10==0:print(history[-1],flush=True)
        if stale>=5: break
    model.load_state_dict(best_state);model.eval()
    with torch.inference_mode():
        scores=model.score(x).cpu().numpy().ravel()
    report={'gpu':gpu,'task':task,'architecture':[384,64,32,16,8,4,1],
            'weighting':weighting,'best_epoch':min(history,key=lambda h:h['validation_bce'])['epoch']}
    test=ix['test']; val=ix['validation']
    if task not in ['sentimiento','sentimiento_cardiff']:
        threshold=float(max(np.arange(.01,1,.01),key=lambda t:f1_score(y[val],scores[val]>=t,zero_division=0)))
        pred=scores[test]>=threshold
        report.update(threshold=threshold,f1=float(f1_score(y[test],pred,zero_division=0)),
            precision=float(precision_score(y[test],pred,zero_division=0)),
            recall=float(recall_score(y[test],pred,zero_division=0)),
            confusion_matrix=confusion_matrix(y[test],pred,labels=[0,1]).tolist())
    else:
        bands=np.where(scores[test]<.25,0,np.where(scores[test]<.75,1,2))
        truth=np.rint(y[test]*2).astype(int)
        report.update(mae=float(mean_absolute_error(y[test],scores[test])),
            f1_macro=float(f1_score(truth,bands,labels=[0,1,2],average='macro',zero_division=0)),
            confusion_matrix=confusion_matrix(truth,bands,labels=[0,1,2]).tolist())
    output=root/'cabezas';output.mkdir(parents=True,exist_ok=True)
    torch.save(best_state,output/f'{task}_mlp.pt')
    (output/f'{task}_history.json').write_text(json.dumps(history,indent=2),encoding='utf-8')
    (output/f'{task}_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    df.loc[test,['id','split','target']].assign(score=scores[test]).to_json(output/f'{task}_test_scores.jsonl',orient='records',lines=True)
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('task',choices=['es_pregunta','es_logro','sentimiento','sentimiento_cardiff','sentimiento_cardiff_binario'])
    args=parser.parse_args();train(args.task)
