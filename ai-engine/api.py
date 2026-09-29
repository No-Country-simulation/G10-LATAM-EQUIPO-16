from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import traceback

from analyzer import (
    MODEL_NAME,
    analyze_batch_texts,
    analyze_text,
    client,
)

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
    origen_comunidad: str
    periodo_referencia: str
    interacciones: list[BatchInteractionRequest] = Field(
        min_length=1,
        max_length=10,
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "communitylab-ai",
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


@app.post("/api/v1/analyze-batch")
def analyze_batch(batch: BatchRequest):
    results = []

    assets = {
        "post_linkedin": [],
        "destaque_newsletter_semanal": [],
        "sugerencia_contenido_faq": [],
    }

    batch_input = [
        {
            "id": interaction.id,
            "texto": interaction.texto,
        }
        for interaction in batch.interacciones
    ]

    try:
       batch_analysis, batch_metrics = analyze_batch_texts(
           batch_input
       )
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    analysis_by_id = {
        item.id: item
        for item in batch_analysis.results
    }

    for interaction in batch.interacciones:
        try:
            analysis = analysis_by_id[interaction.id]   

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

            route = graph_result["route"]
            content = graph_result["content"]

            if route == "linkedin" and content:
                assets["post_linkedin"].append(
                    {
                        "id_interaccion": interaction.id,
                        "contenido": content,
                    }
                )

            elif route == "newsletter" and content:
                assets["destaque_newsletter_semanal"].append(
                    {
                        "id_interaccion": interaction.id,
                        "contenido": content,
                    }
                )

            elif route == "faq" and content:
                assets["sugerencia_contenido_faq"].append(
                    {
                        "id_interaccion": interaction.id,
                        "contenido": content,
                    }
                )

            results.append(
                {
                    "id": interaction.id,
                    "status": "processed",
                    "analysis": analysis.model_dump(),
                    "route": graph_result["route"],
                    "content": graph_result["content"],
                }
            )

        except Exception as error:
            traceback.print_exc()

            print(
                f"❌ Error procesando {interaction.id}: "
                f"{type(error).__name__}: {error}"
            )

            results.append(
                {
                    "id": interaction.id,
                    "status": "error",
                    "error": str(error),
                }
            )

    successful_results = [
        result
        for result in results
        if result["status"] == "processed"
    ]

    sentiment_counts = {}

    for result in successful_results:
        sentiment = result["analysis"]["sentimiento"]
        sentiment_counts[sentiment] = (
            sentiment_counts.get(sentiment, 0) + 1
        )

    predominant_sentiment = (
        max(sentiment_counts, key=sentiment_counts.get)
        if sentiment_counts
        else "sin_datos"
    )

    main_topics = list(
        dict.fromkeys(
            result["analysis"]["tema"]
            for result in successful_results
        )
    )[:5]

    processed_count = sum(
        result["status"] == "processed"
        for result in results
    )

    error_count = sum(
        result["status"] == "error"
        for result in results
    )

    return {
        "status": (
            "exito"
            if error_count == 0
            else "parcial"
        ),
        "resumen_comunidad": {
            "total_interacciones_procesadas": processed_count,
            "sentimiento_predominante": predominant_sentiment,
            "temas_principales": main_topics,
        },
        "activos_distribucion_generados": assets,
        "interacciones_analizadas": [
            {
                "id": result["id"],
                "sentimiento": result["analysis"]["sentimiento"],
                "tema": result["analysis"]["tema"],
                "tipo": result["analysis"]["tipo"],
                "relevancia": result["analysis"]["relevancia"],
                "insight": result["analysis"]["insight"],
            }
            for result in successful_results
        ],
    }