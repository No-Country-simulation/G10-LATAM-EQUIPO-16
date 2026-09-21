from typing import Literal
from pydantic import BaseModel


class Interaction(BaseModel):
    """Representa una interacción de una comunidad digital."""

    autor: str
    canal: str
    tipo: str
    texto: str


class AnalysisResult(BaseModel):
    """Representa el análisis generado por el modelo de IA."""

    sentimiento: Literal[
        "positivo",
        "negativo",
        "neutro",
        "mixto",
    ]

    tema: str

    tipo: Literal[
        "testimonio",
        "pregunta_tecnica",
        "feedback",
        "logro",
        "otro",
    ]

    relevancia: Literal[
        "alta",
        "media",
        "baja",
    ]

    insight: str