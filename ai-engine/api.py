from fastapi import FastAPI
from pydantic import BaseModel

from analyzer import MODEL_NAME, analyze_text, client
from graph import graph


app = FastAPI(
    title="CommunityLab AI API",
    version="0.1.0",
)


class InteractionRequest(BaseModel):
    autor: str
    canal: str
    tipo: str
    texto: str

class BatchInteractionRequest(InteractionRequest):
    id: str


class BatchRequest(BaseModel):
    interactions: list[BatchInteractionRequest]

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "communitylab-ai"
    }


@app.post("/analyze")
def analyze(interaction: InteractionRequest):
    analysis, metrics = analyze_text(interaction.texto)

    graph_result = graph.invoke(
        {
            "interaction": interaction,
            "analysis": analysis,
            "route": "",
            "content": "",
            "client": client,
            "model": MODEL_NAME,
        }
    )

    return {
        "status": "processed",
        "analysis": analysis.model_dump(),
        "route": graph_result["route"],
        "content": graph_result["content"],
        "metrics": metrics,
    }

@app.post("/analyze-batch")
def analyze_batch(batch: BatchRequest):
    results = []

    for interaction in batch.interactions:
        analysis, metrics = analyze_text(interaction.texto)

        graph_result = graph.invoke(
            {
                "interaction": interaction,
                "analysis": analysis,
                "route": "",
                "content": "",
                "client": client,
                "model": MODEL_NAME,
            }
        )

        results.append(
            {
                "id": interaction.id,
                "status": "processed",
                "analysis": analysis.model_dump(),
                "route": graph_result["route"],
                "content": graph_result["content"],
                "metrics": metrics,
            }
        )

    return {
        "status": "processed",
        "count": len(results),
        "results": results,
    }