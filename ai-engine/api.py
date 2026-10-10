from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from analyzer import (
    MODEL_NAME,
    analyze_batch_texts,
    analyze_text,
    client,
    TransientAIError,
    PermanentAIError,
)

from graph import decide_route, graph


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
        "post_linkedin": None,
        "destaque_newsletter_semanal": None,
        "sugerencia_contenido_faq": None,
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
    except TransientAIError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except PermanentAIError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    analysis_by_id = {
        item.id: item
        for item in batch_analysis.results
    }

    relevance_score = {
        "alta": 3,
        "media": 2,
        "baja": 1,
    }

    candidates = {}

    for interaction in batch.interacciones:
        try:
            analysis = analysis_by_id[interaction.id]

            route = decide_route(
                {
                    "interaction": interaction,
                    "analysis": analysis,
                    "route": "",
                    "content": "",
                    "client": client,
                    "model": MODEL_NAME,
                }
            )

            if route in ("linkedin", "newsletter", "faq"):
                current = candidates.get(route)

                if (
                    current is None
                    or relevance_score.get(analysis.relevancia, 0)
                    > relevance_score.get(
                        current["analysis"].relevancia,
                        0,
                    )
                ):
                    candidates[route] = {
                        "interaction": interaction,
                        "analysis": analysis,
                    }

            results.append(
                {
                    "id": interaction.id,
                    "status": "processed",
                    "analysis": analysis.model_dump(),
                    "route": route,
                    "content": "",
                }
            )

        except Exception as error:
            results.append(
                {
                    "id": interaction.id,
                    "status": "error",
                    "error": str(error),
                }
            )

    for route, candidate in candidates.items():
        interaction = candidate["interaction"]
        analysis = candidate["analysis"]

        try:
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

            content = graph_result["content"]

            if route == "linkedin" and content:
                assets["post_linkedin"] = {
                    "titulo": analysis.tema,
                    "copy": content,
                    "canal_recomendado": "LinkedIn Oficial",
                    "potencial_engagement": {
                        "alta": "Alto",
                        "media": "Medio",
                        "baja": "Bajo",
                    }.get(analysis.relevancia, "Medio"),
                }

            elif route == "newsletter" and content:
                assets["destaque_newsletter_semanal"] = {
                    "seccion": analysis.tema,
                    "titular": analysis.insight,
                    "resumen": content,
                }

            elif route == "faq" and content:
                assets["sugerencia_contenido_faq"] = {
                    "tema": analysis.tema,
                    "origen": interaction.canal,
                    "status": "BORRADOR",
                }

            for result in results:
                if result.get("id") == interaction.id:
                    result["content"] = content
                    break

        except Exception as error:
            error_message = str(error).lower()

            if (
                "429" in error_message
                or "quota exceeded" in error_message
                or "too_many_requests" in error_message
                or "503" in error_message
                or "unavailable" in error_message
                or "high demand" in error_message
            ):
                raise HTTPException(
                    status_code=503,
                    detail="Gemini está temporalmente no disponible.",
                ) from error

            for result in results:
                if result.get("id") == interaction.id:
                    result["status"] = "error"
                    result["error"] = str(error)
                    break

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
