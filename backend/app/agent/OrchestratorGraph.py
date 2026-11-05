from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.AgentState import OrchestratorAgentState
from app.agent.ContextRetrieverNode import ContextRetrieverNode
from app.agent.GuardrailNode import GuardrailNode
from app.agent.PlannerTriageNode import PlannerTriageNode
from app.agent.SecondaryValidatorNode import SecondaryValidatorNode

# In-memory checkpointer persisting multi-round negotiation states
orchestrator_checkpointer = MemorySaver()


def build_orchestrator_graph(session: AsyncSession) -> Any:
    """Builds and compiles the Pipeline 1 StateGraph with checkpointer support."""
    retriever_node = ContextRetrieverNode(session)

    graph = StateGraph(OrchestratorAgentState)

    # 1. Add Nodes
    graph.add_node("guardrail", GuardrailNode.run)
    graph.add_node("retriever", retriever_node.run)
    graph.add_node("planner", PlannerTriageNode.run)
    graph.add_node("validator", SecondaryValidatorNode.run)

    # 2. Routing Logic
    def route_after_guardrail(state: OrchestratorAgentState) -> str:
        if state.get("injection_detected", False):
            # If sanitized command still carries legitimate factual content (e.g. TC-CHB-02 meeting note), continue
            if state.get("sanitized_command") and len(state.get("sanitized_command", "").strip()) > 5:
                return "retriever"
            return END
        return "retriever"

    def route_after_retriever(state: OrchestratorAgentState) -> str:
        if state.get("is_disambiguation_needed", False) or state.get("status") == "NEEDS_CLARIFICATION":
            return END
        return "planner"

    def route_after_planner(state: OrchestratorAgentState) -> str:
        if state.get("status") in ("DEADLOCK_ESCALATED", "OUT_OF_SCOPE_REFUSED", "NEEDS_CLARIFICATION"):
            return END
        return "validator"

    # 3. Add Edges
    graph.add_edge(START, "guardrail")
    graph.add_conditional_edges("guardrail", route_after_guardrail, ["retriever", END])
    graph.add_conditional_edges("retriever", route_after_retriever, ["planner", END])
    graph.add_conditional_edges("planner", route_after_planner, ["validator", END])
    graph.add_edge("validator", END)

    return graph.compile(checkpointer=orchestrator_checkpointer)


async def run_orchestrator_pipeline(
    session: AsyncSession,
    command: str,
    scenario_id: str | None = None,
    sender_role: str = "HR",
    channel: str = "internal",
    thread_id: int | None = None,
    candidate_id: int | None = None,
    interviewer_id: int | None = None,
    target_date: str | None = None,
    negotiation_round: int = 1,
    max_rounds: int = 3,
) -> OrchestratorAgentState:
    """Convenience runner for Pipeline 1 with checkpoint persistence."""
    app = build_orchestrator_graph(session)

    initial_state: OrchestratorAgentState = {
        "command": command,
        "scenario_id": scenario_id,
        "sender_role": sender_role,
        "channel": channel,
        "thread_id": thread_id,
        "candidate_id": candidate_id,
        "interviewer_id": interviewer_id,
        "target_date": target_date,
        "negotiation_round": negotiation_round,
        "max_rounds": max_rounds,
        "status": "ANALYZING",
        "audit_entries": [],
    }

    config = {
        "configurable": {
            "thread_id": str(thread_id or f"sess_{scenario_id or 'default'}"),
        }
    }

    result = await app.ainvoke(initial_state, config=config)
    return result  # type: ignore[return-value]
