"""Ejecutar y guardar outputs reales; el kernel padre no carga modelos de entrenamiento."""
import os,json
from pathlib import Path
import nbformat
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parent
os.environ['IPYTHONDIR']=str(ROOT/'jupyter_runtime/ipython')
os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'jupyter_runtime')
Path(os.environ['IPYTHONDIR']).mkdir(parents=True,exist_ok=True)
path=ROOT/'MiniLM_3_cabezas_comparacion.ipynb'
notebook=nbformat.read(path,as_version=4)
client=NotebookClient(notebook,timeout=600,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}})
client.execute()
nbformat.write(notebook,path)
print('Notebook ejecutado; todas las celdas completaron:',path,flush=True)
print('Celdas con error:',sum(o.get('output_type')=='error' for c in notebook.cells if c.cell_type=='code' for o in c.outputs),flush=True)
