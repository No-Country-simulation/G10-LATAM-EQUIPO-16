import re

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from analyzer import (
    MODEL_NAME,
    analyze_batch_texts,
    analyze_text,
    client,
    TransientAIError,
    QuotaExceededAIError,
    PermanentAIError,
)

from graph import decide_route, graph
from models import Interaction
from privacy import (
    anonymize_interaction,
    sanitize_generated_content,
    sanitize_analysis,
)


app = FastAPI(
    title="CommunityLab AI API",
    version="0.1.0",
)


class InteractionRequest(BaseModel):
    autor: str
    canal: str
    tipo: str
    texto: str

    @field_validator("autor", "canal", "tipo", "texto")
    @classmethod
    def require_nonblank_field(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value


class BatchInteractionRequest(InteractionRequest):
    id: str

    @field_validator("id")
    @classmethod
    def require_nonblank_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El ID no puede estar vacío.")
        return value


class BatchRequest(BaseModel):
    origen_comunidad: str
    periodo_referencia: str
    interacciones: list[BatchInteractionRequest] = Field(
        min_length=1,
        max_length=10,
    )

    @field_validator("origen_comunidad", "periodo_referencia")
    @classmethod
    def require_nonblank_metadata(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value

    @model_validator(mode="after")
    def require_unique_interaction_ids(self):
        ids = [interaction.id for interaction in self.interacciones]
        if len(ids) != len(set(ids)):
            raise ValueError("El lote contiene IDs duplicados.")
        return self


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "communitylab-ai",
    }


@app.post("/analyze")
def analyze(interaction: InteractionRequest):
    safe_interaction = anonymize_interaction(
        Interaction(**interaction.model_dump())
    )
    
    analysis, metrics = analyze_text(safe_interaction.texto)

    graph_result = graph.invoke(
        {
            "interaction": safe_interaction,
            "analysis": analysis,
            "route": "",
            "content": "",
            "client": client,
            "model": MODEL_NAME,
        }
    )

    return {
        "status": "processed",
        "analysis": sanitize_analysis(analysis.model_dump()),
        "route": graph_result["route"],
        "content": sanitize_generated_content(graph_result["content"]),
        "metrics": metrics,
    }


@app.post("/api/v1/analyze-batch")
def analyze_batch(batch: BatchRequest):
    results = []

    safe_interactions = {
        interaction.id: anonymize_interaction(
            Interaction(
                autor=interaction.autor,
                canal=interaction.canal,
                tipo=interaction.tipo,
                texto=interaction.texto,
            )
        )
        for interaction in batch.interacciones
    }

    assets = {
        "post_linkedin": None,
        "destaque_newsletter_semanal": None,
        "sugerencia_contenido_faq": None,
    }

    batch_input = [
        {
            "id": interaction.id,
            "texto": safe_interactions[interaction.id].texto,
        }
        for interaction in batch.interacciones
    ]

    try:
       batch_analysis, batch_metrics = analyze_batch_texts(
           batch_input
       )
    except QuotaExceededAIError as error:
        # 429 (no 503): el backend no reintenta los 4xx, y reintentar con la cuota agotada no ayuda.
        raise HTTPException(
            status_code=429,
            detail=str(error),
        ) from error

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
                    "analysis": sanitize_analysis(analysis.model_dump()),
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

    generation_error_count = 0

    for route, candidate in candidates.items():
        interaction = candidate["interaction"]
        safe_interaction = safe_interactions[interaction.id]
        analysis = candidate["analysis"]

        try:
            graph_result = graph.invoke(
                {
                    "interaction": safe_interaction,
                    "analysis": analysis,
                    "route": "",
                    "content": "",
                    "client": client,
                    "model": MODEL_NAME,
                }
            )

            content = sanitize_generated_content(graph_result["content"])

            if route == "linkedin" and content:
                assets["post_linkedin"] = {
                    "interaccion_id": interaction.id,
                    "titulo": sanitize_generated_content(analysis.tema),
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
                    "interaccion_id": interaction.id,
                    "seccion": sanitize_generated_content(analysis.tema),
                    "titular": sanitize_generated_content(analysis.insight),
                    "resumen": content,
                }

            elif route == "faq" and content:

                faq_match = re.fullmatch(
                    r"\s*Pregunta:\s*(.*?)\s*Respuesta:\s*(.*?)\s*",
                    content,
                    flags=re.IGNORECASE | re.DOTALL,
                )

                if not faq_match or not all(faq_match.groups()):
                    raise ValueError("Formato FAQ inválido: faltan pregunta o respuesta")

                assets["sugerencia_contenido_faq"] = {
                    "interaccion_id": interaction.id,
                    "tema": sanitize_generated_content(analysis.tema),
                    "origen": interaction.canal,
                    "pregunta": faq_match.group(1).strip(),
                    "respuesta": faq_match.group(2).strip(),
                    "status": "BORRADOR",
                }

            for result in results:
                if result.get("id") == interaction.id:
                    result["content"] = content
                    break

        except Exception as error:
            generation_error_count += 1
            # La generación de activos es posterior al análisis.
            # Su fallo no debe cancelar los resultados ya obtenidos.
            # La interacción ya fue analizada correctamente.
            # Un fallo al generar su activo no debe invalidar el análisis.
            # El activo correspondiente permanece en None (null en JSON).
            for result in results:
                if result.get("id") == interaction.id:
                    result["generation_error"] = str(error)
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
            if error_count == 0 and generation_error_count == 0
            else "parcial"
        ),
        "resumen_comunidad": {
            "total_interacciones_procesadas": processed_count,
            "sentimiento_predominante": predominant_sentiment,
            "temas_principales": main_topics,
        },
        "activos_distribucion_generados": assets,
        "interacciones_fallidas": [
            {
                "id": result["id"],
                "motivo": "No se pudo procesar la interacción",
            }
            for result in results
            if result["status"] == "error"
        ],
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
