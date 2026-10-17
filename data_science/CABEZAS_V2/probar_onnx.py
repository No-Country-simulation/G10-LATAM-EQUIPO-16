"""Prueba CPU de las tres cabezas; no requiere notebook, PyTorch ni encoder."""
import argparse
import json
from pathlib import Path
import numpy as np
import onnxruntime as ort


def probar(carpeta, embeddings=None):
    if embeddings is None:
        # Vectores de prueba, no textos ni medición de calidad semántica.
        vectores = np.stack([np.zeros(384), np.linspace(-1, 1, 384),
                             np.linspace(0.5, -0.5, 384)]).astype(np.float32)
    else:
        vectores = np.load(embeddings, allow_pickle=False)
        if vectores.dtype != np.float32 or vectores.ndim != 2 or vectores.shape[1] != 384:
            raise ValueError('El .npy debe contener float32 con forma [N, 384]')
        if len(vectores) == 0 or not np.isfinite(vectores).all():
            raise ValueError('Embeddings vacíos o no finitos')
    opciones = ort.SessionOptions()
    opciones.intra_op_num_threads = 1
    opciones.inter_op_num_threads = 1
    resultados = []
    for nombre in ['es_pregunta', 'es_logro', 'sentimiento']:
        sesion = ort.InferenceSession(str(carpeta / f'{nombre}.onnx'),
                                     sess_options=opciones, providers=['CPUExecutionProvider'])
        entrada, salida = sesion.get_inputs(), sesion.get_outputs()
        assert len(entrada) == 1 and entrada[0].name == 'embedding'
        assert entrada[0].type == 'tensor(float)' and entrada[0].shape[1] == 384
        assert len(salida) == 1 and salida[0].name == 'score'
        assert salida[0].type == 'tensor(float)' and salida[0].shape[1] == 1
        scores = sesion.run(['score'], {'embedding': vectores})[0]
        assert scores.dtype == np.float32 and scores.shape == (len(vectores), 1)
        assert np.isfinite(scores).all() and ((scores >= 0) & (scores <= 1)).all()
        individuales = np.concatenate([
            sesion.run(['score'], {'embedding': vector[None]})[0] for vector in vectores])
        assert np.allclose(scores, individuales, atol=1e-5, rtol=1e-5)
        resultados.append({'cabeza': nombre, 'estado': 'ok', 'entrada': list(vectores.shape),
                           'salida': list(scores.shape), 'scores': scores[:3, 0].tolist()})
        del sesion
    return {'onnxruntime': ort.__version__, 'numpy': np.__version__,
            'provider': 'CPUExecutionProvider', 'pruebas': resultados}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cabezas', type=Path, default=Path(__file__).resolve().parent / 'cabezas')
    parser.add_argument('--embeddings', type=Path, help='Opcional: vectores MiniLM float32 [N,384] en .npy')
    args = parser.parse_args()
    print(json.dumps(probar(args.cabezas, args.embeddings), indent=2, ensure_ascii=False))
