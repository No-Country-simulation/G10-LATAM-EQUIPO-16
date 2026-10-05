"""Inferencia CPU con un encoder y UNA cabeza en cada paso. Sin Torch/pandas/sklearn."""
import os
os.environ.setdefault('OMP_NUM_THREADS','1')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
import sys,json,threading,time,gc
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'deps'))
TASKS=('es_faq','es_logro','sentimiento')

def session(path):
    import onnxruntime as ort
    opts=ort.SessionOptions()
    opts.intra_op_num_threads=opts.inter_op_num_threads=1
    opts.execution_mode=ort.ExecutionMode.ORT_SEQUENTIAL
    opts.graph_optimization_level=ort.GraphOptimizationLevel.ORT_ENABLE_BASIC
    opts.enable_cpu_mem_arena=False;opts.enable_mem_pattern=False
    return ort.InferenceSession(str(path),sess_options=opts,providers=['CPUExecutionProvider'])

class Predictor:
    def __init__(self,deploy_dir=None):
        from tokenizers import Tokenizer
        self.directory=Path(deploy_dir) if deploy_dir else ROOT/'deploy_mlp_int8'
        self.config=json.loads((self.directory/'config.json').read_text(encoding='utf-8'))
        self.lock=threading.Lock()
        self._check_ram()
        self.encoder=session(self.directory/'encoder.onnx')
        self.inputs={i.name for i in self.encoder.get_inputs()}
        self.tokenizer=Tokenizer.from_file(str(self.directory/'tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=self.config['max_tokens'])
        self.tokenizer.no_padding()
        self._check_ram()

    def _check_ram(self):
        import psutil
        value=psutil.Process().memory_info().rss
        if value>=self.config['process_budget_bytes']:raise MemoryError('RSS del proceso alcanzó 1,000 MB')
        return value/1e6

    def validate(self,item):
        import numpy as np
        if not isinstance(item,dict) or set(item)!={'id_mensaje','mensaje'}:raise ValueError('Campos exactos: id_mensaje, mensaje')
        ident=item['id_mensaje']
        if isinstance(ident,bool) or not isinstance(ident,(int,np.integer)) or not -(2**63)<=int(ident)<2**63:raise ValueError('id_mensaje fuera de int64')
        text=item['mensaje']
        if not isinstance(text,str) or not text.strip():raise ValueError('mensaje debe ser texto no vacío')
        if len(text)>self.config['max_chars']:raise ValueError('mensaje supera 8,000 caracteres')
        return int(ident),text

    def encode(self,text,trace=False):
        import numpy as np
        tokens=self.tokenizer.encode(text)
        feed={'input_ids':np.array([tokens.ids],dtype=np.int64),'attention_mask':np.ones((1,len(tokens.ids)),dtype=np.int64),
              'token_type_ids':np.array([tokens.type_ids],dtype=np.int64)}
        if trace:print('[INFERENCIA 1] caracteres:',len(text),'tokens procesados:',len(tokens.ids),'truncado:',bool(tokens.overflowing),'batch: 1',flush=True)
        if trace:print('[INFERENCIA 2] llamada encoder INT8 CPU:',{k:list(v.shape) for k,v in feed.items()},flush=True)
        embedding=self.encoder.run(None,{k:v for k,v in feed.items() if k in self.inputs})[0]
        assert embedding.shape==(1,384)
        if trace:print('[INFERENCIA 3] embedding:',embedding.shape,'primeros 8:',embedding[0,:8].tolist(),'RAM MB:',self._check_ram(),flush=True)
        return embedding

    def __call__(self,item,trace=False):
        ident,text=self.validate(item)
        with self.lock:
            self._check_ram();embedding=self.encode(text,trace);result={'id_mensaje':ident}
            for task in TASKS:
                if trace:print('[INFERENCIA 4] cargar desde SSD:',task,self.config['dims'],'RAM MB:',self._check_ram(),flush=True)
                head=session(self.directory/'heads'/f'{task}.onnx')
                try:
                    value=float(head.run(None,{'embedding':embedding})[0][0,0])
                    if not 0<=value<=1:raise RuntimeError('Score fuera de rango')
                    result[task]=value
                finally:del head
                if trace:print('[INFERENCIA 5]',task,'sigmoide:',value,'sesión liberada; RAM MB:',self._check_ram(),flush=True)
            self._check_ram()
            return result

def benchmark(report_path):
    import numpy as np,psutil,platform
    stages={'before_load':psutil.Process().memory_info().rss/1e6}
    predictor=Predictor();stages['after_load']=predictor._check_ram()
    example=predictor({'id_mensaje':123,'mensaje':'Gracias, pude resolverlo y ya funciona.'},trace=True)
    durations=[]
    # Límites reales del wrapper, incluso texto de 8,000 caracteres y truncado a 128 tokens.
    texts=['¿Cómo instalar Python en Windows?','Gracias, solucioné el error.','No funciona y sigo con errores.','hola '*1600]
    for index in range(104):
        start=time.perf_counter();predictor({'id_mensaje':index,'mensaje':texts[index%len(texts)]})
        if index>=4:durations.append((time.perf_counter()-start)*1000)
    rejected=[]
    for invalid in [{'id_mensaje':2**63,'mensaje':'x'},{'id_mensaje':True,'mensaje':'x'},{'id_mensaje':1,'mensaje':'x'*8001},{'id_mensaje':1,'mensaje':' '},{'id_mensaje':1,'mensaje':'x','extra':0}]:
        try:predictor(invalid)
        except ValueError:rejected.append(True)
        else:raise AssertionError('Entrada inválida admitida')
    stages['after_inference']=predictor._check_ram()
    result=dict(platform=platform.platform(),cpu=platform.processor(),batch=1,max_tokens=128,max_chars=8000,requests=104,
        stages_mb=stages,p50_ms=float(np.percentile(durations,50)),p95_ms=float(np.percentile(durations,95)),example=example,
        boundary_checks=len(rejected),imported_heavy_modules=[m for m in ['torch','pandas','sklearn','sentence_transformers'] if m in sys.modules])
    Path(report_path).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False),flush=True)

if __name__=='__main__':
    import argparse
    sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('--report',required=True)
    args=parser.parse_args();benchmark(args.report)
