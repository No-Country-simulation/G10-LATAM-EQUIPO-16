from typing import TypedDict
from langgraph.graph import END, START, StateGraph
from models import AnalysisResult, Interaction
from generators import generate_faq, generate_linkedin
from google import genai


class GraphState(TypedDict):
    """Estado compartido entre los nodos de LangGraph."""

    interaction: Interaction
    analysis: AnalysisResult
    route: str
    client: genai.Client
    content: str
    model: str


def decide_route(state: GraphState) -> str:
    """Decide qué tipo de activo generar según el análisis."""

    analysis_type = state["analysis"].tipo

    if analysis_type in ("logro", "testimonio"):
        return "linkedin"

    if analysis_type == "pregunta_tecnica":
        return "faq"

    return "general"

def linkedin_node(state: GraphState) -> dict:
    """Genera una publicación de LinkedIn."""

    content = generate_linkedin(
        client=state["client"],
        interaction=state["interaction"],
        analysis=state["analysis"],
        model=state["model"],
    )

    return {
        "route": "linkedin",
        "content": content,
    }


def faq_node(state: GraphState) -> dict:
    """Genera contenido FAQ o Tip a partir de una pregunta técnica."""

    content = generate_faq(
        client=state["client"],
        interaction=state["interaction"],
        analysis=state["analysis"],
        model=state["model"],
    )

    return {"route": "faq",
            "content": content,
    }


def general_node(state: GraphState) -> dict:
    """Procesa interacciones que no requieren una ruta específica."""

    return {"route": "general",
            "content": "",
    }

def build_graph():
    """Construye y compila el flujo de decisión."""

    builder = StateGraph(GraphState)

    builder.add_node("linkedin", linkedin_node)
    builder.add_node("faq", faq_node)
    builder.add_node("general", general_node)

    builder.add_conditional_edges(
        START,
        decide_route,
        {
            "linkedin": "linkedin",
            "faq": "faq",
            "general": "general",
        },
    )

    builder.add_edge("linkedin", END)
    builder.add_edge("faq", END)
    builder.add_edge("general", END)

    return builder.compile()


graph = build_graph()

if __name__ == "__main__":

    interaction = Interaction(
        autor="Mariana Souza",
        canal="#logros-y-empleos",
        tipo="testimonio",
        texto="Conseguí mi primer empleo como desarrolladora de IA.",
    )

    analysis = AnalysisResult(
        sentimiento="positivo",
        tema="empleabilidad",
        tipo="pregunta_tecnica",
        relevancia="alta",
        insight="La formación contribuyó a conseguir empleo.",
    )

    result = graph.invoke(
        {
            "interaction": interaction,
            "analysis": analysis,
            "route": "",
        }
    )

    print(f"Ruta seleccionada: {result['route']}")