"""Inferencia local CPU: MiniLM y tres cabezas ONNX FP32."""
import argparse
import json
from pathlib import Path
import threading
import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent
HEADS = ('es_pregunta', 'es_logro', 'sentimiento')

class Clasificador:
    def __init__(self, carpeta=ROOT, threads=1):
        carpeta = Path(carpeta)
        if not isinstance(threads, int) or threads < 1:
            raise ValueError('threads debe ser un entero positivo')
        self._lock = threading.Lock()
        self.tokenizer = Tokenizer.from_file(str(carpeta / 'modelos/tokenizer.json'))
        self.tokenizer.enable_truncation(max_length=128)
        self.tokenizer.no_padding()
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        def load(name):
            return ort.InferenceSession(str(carpeta / 'modelos' / name),
                sess_options=options, providers=['CPUExecutionProvider'])
        self.encoder = load('encoder_fp32.onnx')
        self.heads = {name: load(name + '.onnx') for name in HEADS}

    def embedding(self, texto):
        if not isinstance(texto, str) or not texto.strip():
            raise ValueError('Se requiere texto no vacío')
        with self._lock:
            tokens = self.tokenizer.encode(texto)
        inputs = dict(input_ids=tokens.ids, attention_mask=tokens.attention_mask,
                      token_type_ids=tokens.type_ids)
        feed = {i.name: np.asarray([inputs[i.name]], dtype=np.int64)
                for i in self.encoder.get_inputs()}
        vector = self.encoder.run(['embedding'], feed)[0]
        if vector.dtype != np.float32 or vector.shape != (1, 384) or not np.isfinite(vector).all():
            raise RuntimeError('Salida inválida del encoder FP32')
        return vector

    def predecir(self, texto):
        vector = self.embedding(texto)
        result = {}
        for name, head in self.heads.items():
            output = head.run(['score'], {'embedding': vector})[0]
            if output.dtype != np.float32 or output.shape != (1, 1):
                raise RuntimeError('Contrato de cabeza inválido: ' + name)
            score = float(output[0, 0])
            if not np.isfinite(score) or not 0 <= score <= 1:
                raise RuntimeError('Score inválido: ' + name)
            result[name] = score
        return result

    def predecir_lote(self, textos):
        if not isinstance(textos, (list, tuple)) or not textos:
            raise ValueError('Se requiere una lista no vacía de textos')
        if any(not isinstance(t, str) or not t.strip() for t in textos):
            raise ValueError('Todos los textos deben ser cadenas no vacías')
        return [self.predecir(t) for t in textos]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--texto', required=True)
    parser.add_argument('--threads', type=int, default=1)
    args = parser.parse_args()
    print(json.dumps(Clasificador(threads=args.threads).predecir(args.texto),
                     ensure_ascii=False, indent=2))
