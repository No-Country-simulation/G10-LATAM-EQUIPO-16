"""Configuración compartida de los tests del AI Engine.

`analyzer.py` exige `GEMINI_API_KEY` al importarse. Los tests mockean las
llamadas a Gemini, así que definimos una clave falsa antes de importar el
código: los tests corren en cualquier máquina (sin `.env`, CI) y nunca
llegan a llamar a Gemini de verdad.
"""
import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")
