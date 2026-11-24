import time
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.app.agents.state import MLOpsState
from backend.app.agents.data_sentinel import run_data_sentinel
from backend.app.agents.training_agent import run_training_agent
from backend.app.agents.eval_gate_agent import run_eval_gate
from backend.app.agents.security_agent import run_security_agent
from backend.app.agents.packager_agent import run_packager_agent

# Active memory checkpointer for state persistence
memory_checkpointer = MemorySaver()

# In-memory execution store for WebSocket and status queries
RUN_STORE: Dict[str, MLOpsState] = {}


def route_eval_decision(state: MLOpsState) -> str:
    gate_res = state.get("eval_gate_result") or {}
    if gate_res.get("decision") == "PROMOTED":
        return "security_agent"
    return "abort_rejected"


def abort_node(state: MLOpsState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    logs.append(f"[{time.strftime('%X')}] [Supervisor] Challenger model did not meet acceptance criteria. Pipeline aborted.")
    return {
        "status": "REJECTED",
        "current_step": "pipeline_rejected",
        "logs": logs
    }


def build_mlops_supervisor_graph():
    graph = StateGraph(MLOpsState)

    graph.add_node("data_sentinel", run_data_sentinel)
    graph.add_node("training_agent", run_training_agent)
    graph.add_node("eval_gate", run_eval_gate)
    graph.add_node("security_agent", run_security_agent)
    graph.add_node("packager_agent", run_packager_agent)
    graph.add_node("abort_rejected", abort_node)

    graph.set_entry_point("data_sentinel")
    graph.add_edge("data_sentinel", "training_agent")
    graph.add_edge("training_agent", "eval_gate")

    graph.add_conditional_edges(
        "eval_gate",
        route_eval_decision,
        {
            "security_agent": "security_agent",
            "abort_rejected": "abort_rejected"
        }
    )

    # Note: When auto_deploy is False, the graph pauses after security_agent for HITL
    graph.add_edge("security_agent", "packager_agent")
    graph.add_edge("packager_agent", END)
    graph.add_edge("abort_rejected", END)

    app = graph.compile(checkpointer=memory_checkpointer, interrupt_before=["packager_agent"])
    return app


mlops_compiled_graph = build_mlops_supervisor_graph()
