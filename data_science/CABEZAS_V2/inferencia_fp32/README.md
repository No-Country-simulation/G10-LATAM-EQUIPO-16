# Inferencia Python: encoder y tres cabezas FP32

Esta carpeta contiene el encoder MiniLM, su tokenizer y las tres cabezas de
CABEZAS_V2 (`es_pregunta`, `es_logro`, `sentimiento`), todos en FP32.
Se ejecuta en CPU, fuera del notebook, sin PyTorch ni descargas de modelos.

## Obtener la entrega

Mientras el PR #23 siga abierto, obtener su rama desde un clon del repositorio:

```bash
git fetch https://github.com/saulMendozaRuiz/G10-LATAM-EQUIPO-16.git filtro-logros-2026-10-11
git switch -c prueba-inferencia-fp32 FETCH_HEAD
cd data_science/CABEZAS_V2/inferencia_fp32
```

Si ya estás en la rama del PR, basta actualizarla con `git pull`.
Después del merge, esta carpeta estará disponible en `main`.

## Instalar y procesar un mensaje

En OCI / Linux, con Python 3.11:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python inferencia.py --texto "Hoy terminé mi diplomado."
```

Salida aproximada:

```json
{
  "es_pregunta": 0.0557,
  "es_logro": 0.9897,
  "sentimiento": 0.7538
}
```

En Windows, crear el entorno con `py -3.11 -m venv .venv` y activarlo con
`.venv\Scripts\Activate.ps1`; el resto de comandos es igual.

## Usarlo desde el AI Engine

Con esta carpeta accesible en el proyecto Python:

```python
from inferencia_fp32 import Clasificador

# Cargar una vez al arrancar el proceso y reutilizar.
clasificador = Clasificador()
scores = clasificador.predecir("¿Cómo instalo Python?")

resultados = clasificador.predecir_lote([
    "Hoy obtuve mi certificación.",
    "Estoy triste por lo ocurrido.",
])
```

También se puede ejecutar este ejemplo desde el directorio `CABEZAS_V2`.
Si el AI Engine está en otra carpeta, copiar `inferencia_fp32` completa junto
a su módulo de entrada o añadir su carpeta padre a la ruta de módulos Python.
Las rutas de los modelos se resuelven automáticamente respecto al script.

Devuelve tres scores independientes entre 0 y 1. Sentimiento es binario:
0=negativo, 1=positivo; 0.5 no demuestra neutralidad. Los scores no están
calibrados como probabilidades. La decisión de cómo usarlos junto con Gemini
queda en el AI Engine; este módulo no modifica su flujo actual.

## Medir recursos en OCI

```bash
python medir_recursos.py --repeticiones 30 > recursos_oci.json
```

Reporta tiempo de carga, latencia y memoria máxima del proceso. En la prueba
local Windows/Python 3.11, una instancia CPU usó aproximadamente 1.1 GiB de
memoria máxima y 5.5 ms de latencia mediana con un mensaje corto. Medir de nuevo
en la VM OCI con sus textos y recursos; esos valores no certifican la VM.
Comenzar con un proceso, ya que cada proceso carga su propia copia del modelo.

## Archivos que deben permanecer juntos

Conservar `modelos/` completa. `encoder_fp32.onnx` carga automáticamente los seis
archivos `encoder_pesos_*.bin`; no hay que unirlos ni descomprimir nada.
Se repartieron los pesos para que cada archivo quepa en GitHub, sin cuantizarlos.
El conjunto ocupa unos 487 MB y no requiere Git LFS.

El encoder usa mean pooling con máscara, 384 dimensiones, máximo 128 tokens
(incluidos los especiales) y sin normalización L2. Trunca textos más largos.
Las cabezas son las originales de CABEZAS_V2. El módulo no guarda los textos
ni llama servicios externos. `encoder_config.json` y `MODEL_CARD_ENCODER.md`
documentan el modelo base.
