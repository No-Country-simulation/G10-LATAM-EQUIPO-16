"""Un proceso, un encoder: JSON por línea en stdin; respuesta JSON por línea en stdout."""
import sys,json
from serve_mlp_int8 import Predictor

def main():
    predictor=Predictor()
    print('Encoder INT8 listo; batch=1, 128 tokens, 8000 caracteres, un worker.',file=sys.stderr,flush=True)
    # 8000 caracteres UTF-8 usan como máximo 32000 bytes; margen para envoltorio JSON.
    # Rechazar un sobre grande ANTES de cargarlo completo en memoria.
    max_line=40000
    while True:
        line=sys.stdin.buffer.readline(max_line+1)
        if not line:break
        try:
            if len(line)>max_line:
                while not line.endswith(b'\n'):
                    line=sys.stdin.buffer.readline(max_line+1)
                    if not line:break
                raise ValueError('Sobre JSON supera 40000 bytes')
            item=json.loads(line.decode('utf-8'))
            result=predictor(item)
        except (ValueError,TypeError,UnicodeError) as error:
            result={'error':str(error)}
        print(json.dumps(result,ensure_ascii=False,allow_nan=False),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
