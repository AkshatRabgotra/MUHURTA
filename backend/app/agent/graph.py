"""LangGraph workflow for category-based Muhurta planning."""

from __future__ import annotations

from typing import Any, Literal
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    AgentState,
    classify_and_parse_node,
    compute_slots_node,
    explain_node,
    geocode_node,
    route_by_confidence_node,
    validate_explanation_node,
)


def route_after_parse(state: AgentState) -> Literal["classify_and_parse", "route_by_confidence", "__end__"]:
    status = state.get("status")
    if status in ("out_of_scope", "needs_clarification"):
        return END

    if state.get("retry_parse_count", 0) == 1 and not state.get("constraints"):
        return "classify_and_parse"

    return "route_by_confidence"


def route_after_confidence(state: AgentState) -> Literal["geocode", "__end__"]:
    status = state.get("status")
    if status in ("out_of_scope", "needs_clarification"):
        return END
    return "geocode"


def route_after_compute(state: AgentState) -> Literal["explain", "__end__"]:
    slots = state.get("slots", [])
    if not slots:
        return END
    return "explain"


def route_after_validate(state: AgentState) -> Literal["explain", "__end__"]:
    if state.get("retry_explain_count", 0) == 1 and state.get("status") != "success":
        return "explain"
    return END


def create_muhurta_graph() -> StateGraph:
    """Build the category-based compiled LangGraph agent graph."""
    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("classify_and_parse", classify_and_parse_node)
    graph.add_node("route_by_confidence", route_by_confidence_node)
    graph.add_node("geocode", geocode_node)
    graph.add_node("compute_slots", compute_slots_node)
    graph.add_node("explain", explain_node)
    graph.add_node("validate_explanation", validate_explanation_node)

    # Edges
    graph.add_edge(START, "classify_and_parse")

    graph.add_conditional_edges(
        "classify_and_parse",
        route_after_parse,
        {
            "classify_and_parse": "classify_and_parse",
            "route_by_confidence": "route_by_confidence",
            END: END,
        },
    )

    graph.add_conditional_edges(
        "route_by_confidence",
        route_after_confidence,
        {
            "geocode": "geocode",
            END: END,
        },
    )

    graph.add_edge("geocode", "compute_slots")

    graph.add_conditional_edges(
        "compute_slots",
        route_after_compute,
        {
            "explain": "explain",
            END: END,
        },
    )

    graph.add_edge("explain", "validate_explanation")

    graph.add_conditional_edges(
        "validate_explanation",
        route_after_validate,
        {
            "explain": "explain",
            END: END,
        },
    )

    return graph.compile()


muhurta_agent = create_muhurta_graph()


async def run_muhurta_agent(
    raw_text: str,
    user_id: str,
    user_tz: str = "Asia/Kolkata",
    default_city: str | None = None,
    prompt_variant: str = "explain_v1",
    llm_provider: str = "mock",
    explicit_category: str | None = None,
) -> AgentState:
    """Convenience helper to run the category-based LangGraph agent."""
    initial_state: AgentState = {
        "raw_text": raw_text,
        "user_id": user_id,
        "user_tz": user_tz,
        "default_city": default_city,
        "prompt_variant": prompt_variant,
        "llm_provider": llm_provider,
        "explicit_category": explicit_category,
        "retry_parse_count": 0,
        "retry_explain_count": 0,
        "tokens_in": 0,
        "tokens_out": 0,
        "latency_ms": 0,
    }
    final_state = await muhurta_agent.ainvoke(initial_state)
    return final_state
