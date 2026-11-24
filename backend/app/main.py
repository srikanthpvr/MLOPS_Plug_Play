import os
import sys
import uuid
import time
import asyncio
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.config import settings
from backend.app.schemas.data_schemas import DatasetSummary, DatasetPreviewResponse
from backend.app.schemas.model_schemas import ModelCatalogItem, ChampionModelMetadata, HyperparameterSpec
from backend.app.schemas.agent_schemas import (
    AgentRunRequest, AgentRunResponse, AgentRunStatusResponse, HITLApprovalRequest
)
from backend.app.schemas.observability_schemas import ObservabilityMetricsResponse
from backend.app.services.data_service import list_datasets, get_dataset_preview, DATA_DIR
from backend.app.services.observability_service import get_observability_dashboard
from backend.app.agents.state import MLOpsState
from backend.app.agents.supervisor import mlops_compiled_graph, RUN_STORE

app = FastAPI(
    title="MLOps Build Agent Suite API",
    description="Autonomous, Plug-and-Play Multi-Agent MLOps Platform (LangChain, LangSmith, LangGraph, Azure)",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite running on port 5173 / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active WebSocket connections
ACTIVE_SOCKETS: Dict[str, List[WebSocket]] = {}

# In-memory Model Catalog
MODEL_CATALOG = [
    ModelCatalogItem(
        id="lightgbm",
        name="LightGBM Classifier",
        family="Gradient Boosted Decision Trees",
        description="High-performance, histogram-based gradient boosting optimized for low latency and high accuracy.",
        supported_tasks=["Binary Classification", "Multi-class Classification"],
        default_hyperparameters={"learning_rate": 0.05, "n_estimators": 100, "max_depth": 6},
        specs=[
            HyperparameterSpec(name="learning_rate", type="float", default=0.05, min_val=0.001, max_val=0.5, description="Step size shrinkage"),
            HyperparameterSpec(name="n_estimators", type="int", default=100, min_val=10, max_val=500, description="Number of boosting iterations"),
            HyperparameterSpec(name="max_depth", type="int", default=6, min_val=2, max_val=16, description="Maximum tree depth"),
        ]
    ),
    ModelCatalogItem(
        id="xgboost",
        name="XGBoost Classifier",
        family="Gradient Boosted Trees",
        description="Standard enterprise GBDT with L1/L2 regularization and exact greedy tree pruning.",
        supported_tasks=["Binary Classification", "Regression"],
        default_hyperparameters={"learning_rate": 0.05, "n_estimators": 100, "max_depth": 5},
        specs=[
            HyperparameterSpec(name="learning_rate", type="float", default=0.05, min_val=0.01, max_val=0.3, description="Learning rate eta"),
            HyperparameterSpec(name="n_estimators", type="int", default=100, min_val=20, max_val=400, description="Trees count"),
            HyperparameterSpec(name="max_depth", type="int", default=5, min_val=2, max_val=12, description="Max tree depth"),
        ]
    ),
    ModelCatalogItem(
        id="random_forest",
        name="Random Forest Classifier",
        family="Bagging Ensemble",
        description="Robust ensemble of randomized decision trees with built-in out-of-bag variance reduction.",
        supported_tasks=["Binary Classification", "Multi-class Classification"],
        default_hyperparameters={"n_estimators": 100, "max_depth": 10},
        specs=[
            HyperparameterSpec(name="n_estimators", type="int", default=100, min_val=10, max_val=300, description="Number of forest trees"),
            HyperparameterSpec(name="max_depth", type="int", default=10, min_val=3, max_val=20, description="Max depth of trees"),
        ]
    ),
    ModelCatalogItem(
        id="logistic_regression",
        name="ElasticNet / Logistic Regression",
        family="Linear Model",
        description="High-speed linear classifier with L1/L2 penalty for ultra-low latency inference environments.",
        supported_tasks=["Binary Classification"],
        default_hyperparameters={"C": 1.0},
        specs=[
            HyperparameterSpec(name="C", type="float", default=1.0, min_val=0.01, max_val=50.0, description="Inverse of regularization strength"),
        ]
    ),
]


async def broadcast_agent_event(run_id: str, event_data: Dict[str, Any]):
    if run_id in ACTIVE_SOCKETS:
        for ws in list(ACTIVE_SOCKETS[run_id]):
            try:
                await ws.send_json(event_data)
            except Exception:
                ACTIVE_SOCKETS[run_id].remove(ws)


async def execute_langgraph_pipeline(run_id: str, state: MLOpsState):
    config = {"configurable": {"thread_id": run_id}}
    try:
        RUN_STORE[run_id] = state
        await broadcast_agent_event(run_id, {
            "type": "GRAPH_START",
            "run_id": run_id,
            "current_step": "initialized",
            "log": f"[{time.strftime('%X')}] [Supervisor] Initiating LangGraph StateGraph run {run_id}..."
        })

        # Run graph through nodes
        # In async mode, iterate through events
        for event in mlops_compiled_graph.stream(state, config=config):
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    state.update(node_output)
                    RUN_STORE[run_id] = state
                    
                    latest_log = state["logs"][-1] if state.get("logs") else f"Node {node_name} finished"
                    await broadcast_agent_event(run_id, {
                        "type": "NODE_UPDATE",
                        "node": node_name,
                        "current_step": state.get("current_step"),
                        "status": state.get("status", "RUNNING"),
                        "log": latest_log,
                        "state_snapshot": state
                    })
                await asyncio.sleep(0.5)

        # Check if halted at HITL
        if state.get("awaiting_hitl_approval"):
            await broadcast_agent_event(run_id, {
                "type": "AWAITING_APPROVAL",
                "run_id": run_id,
                "message": "Graph paused at HITL checkpoint. Awaiting MLOps engineer approval.",
                "state_snapshot": state
            })

    except Exception as e:
        state["status"] = "FAILED"
        state["logs"].append(f"[{time.strftime('%X')}] [Supervisor] Error: {str(e)}")
        RUN_STORE[run_id] = state
        await broadcast_agent_event(run_id, {
            "type": "GRAPH_ERROR",
            "run_id": run_id,
            "error": str(e)
        })


# --- API Routes ---

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "mode": settings.app_mode,
        "langsmith_tracing": settings.langchain_tracing_v2,
        "azure_storage": settings.azure_storage_account
    }

# 1. DATA HUB ROUTES
@app.get("/api/data/datasets", response_model=List[DatasetSummary])
async def get_datasets():
    return list_datasets()

@app.get("/api/data/preview/{dataset_name}", response_model=DatasetPreviewResponse)
async def preview_dataset(dataset_name: str):
    preview = get_dataset_preview(dataset_name)
    if not preview:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return preview

# 2. MODEL LAB ROUTES
@app.get("/api/models/catalog", response_model=List[ModelCatalogItem])
async def get_model_catalog():
    return MODEL_CATALOG

@app.get("/api/models/champion", response_model=ChampionModelMetadata)
async def get_champion_model():
    return ChampionModelMetadata(
        model_id="champ-churn-lgbm-01",
        name="Customer-Churn-LGBM-Production",
        version="v2.1.0",
        accuracy=0.882,
        f1_score=0.865,
        precision=0.871,
        recall=0.859,
        p95_latency_ms=3.85,
        deployment_target="Azure Container Apps (mlops-prod)",
        last_trained="2026-11-20 09:30:00"
    )

# 3. AGENT EXECUTION ROUTES
@app.post("/api/agents/run", response_model=AgentRunResponse)
async def trigger_agent_run(payload: AgentRunRequest, background_tasks: BackgroundTasks):
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    dataset_path = os.path.join(DATA_DIR, payload.dataset_name)

    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=400, detail=f"Dataset {payload.dataset_name} does not exist.")

    initial_state: MLOpsState = {
        "thread_id": run_id,
        "dataset_name": payload.dataset_name,
        "dataset_path": dataset_path,
        "baseline_path": os.path.join(DATA_DIR, "baseline_churn.csv"),
        "target_column": payload.target_column,
        "model_type": payload.model_type,
        "hyperparameters": payload.hyperparameters,
        "sla_p95_ms": payload.sla_p95_ms,
        "auto_deploy": payload.auto_deploy,
        "data_quality_report": None,
        "training_metrics": None,
        "eval_gate_result": None,
        "security_audit_report": None,
        "deploy_result": None,
        "current_step": "initialized",
        "logs": [f"[{time.strftime('%X')}] [Supervisor] Agent Suite run '{run_id}' registered."],
        "awaiting_hitl_approval": False,
        "hitl_approved": False,
        "status": "RUNNING"
    }

    RUN_STORE[run_id] = initial_state
    background_tasks.add_task(execute_langgraph_pipeline, run_id, initial_state)

    return AgentRunResponse(
        run_id=run_id,
        status="RUNNING",
        current_step="initialized",
        message="Agent suite execution started successfully"
    )

@app.get("/api/agents/runs/{run_id}", response_model=AgentRunStatusResponse)
async def get_agent_run_status(run_id: str):
    if run_id not in RUN_STORE:
        raise HTTPException(status_code=404, detail="Run ID not found")
    state = RUN_STORE[run_id]
    return AgentRunStatusResponse(
        run_id=run_id,
        status=state.get("status", "UNKNOWN"),
        current_step=state.get("current_step", "unknown"),
        awaiting_hitl_approval=state.get("awaiting_hitl_approval", False),
        logs=state.get("logs", []),
        data_quality_report=state.get("data_quality_report"),
        training_metrics=state.get("training_metrics"),
        eval_gate_result=state.get("eval_gate_result"),
        security_audit_report=state.get("security_audit_report"),
        deploy_result=state.get("deploy_result")
    )

@app.post("/api/agents/approve/{run_id}")
async def approve_agent_deployment(run_id: str, approval: HITLApprovalRequest, background_tasks: BackgroundTasks):
    if run_id not in RUN_STORE:
        raise HTTPException(status_code=404, detail="Run ID not found")

    state = RUN_STORE[run_id]
    if not state.get("awaiting_hitl_approval"):
        raise HTTPException(status_code=400, detail="Run is not awaiting approval")

    if not approval.approved:
        state["status"] = "REJECTED"
        state["awaiting_hitl_approval"] = False
        state["logs"].append(f"[{time.strftime('%X')}] [Supervisor] Deployment rejected by MLOps engineer: {approval.notes}")
        RUN_STORE[run_id] = state
        await broadcast_agent_event(run_id, {
            "type": "HITL_REJECTED",
            "run_id": run_id,
            "log": state["logs"][-1],
            "state_snapshot": state
        })
        return {"status": "REJECTED", "message": "Deployment aborted by human decision"}

    # Resuming LangGraph after approval
    state["hitl_approved"] = True
    state["awaiting_hitl_approval"] = False
    state["logs"].append(f"[{time.strftime('%X')}] [Supervisor] Human approval received. Resuming graph for cloud deployment...")
    RUN_STORE[run_id] = state

    async def resume_graph():
        config = {"configurable": {"thread_id": run_id}}
        for event in mlops_compiled_graph.stream(None, config=config):
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    state.update(node_output)
                    RUN_STORE[run_id] = state
                    latest_log = state["logs"][-1] if state.get("logs") else f"Node {node_name} completed"
                    await broadcast_agent_event(run_id, {
                        "type": "NODE_UPDATE",
                        "node": node_name,
                        "current_step": state.get("current_step"),
                        "status": state.get("status"),
                        "log": latest_log,
                        "state_snapshot": state
                    })
        await broadcast_agent_event(run_id, {
            "type": "GRAPH_COMPLETE",
            "run_id": run_id,
            "status": state.get("status"),
            "deploy_result": state.get("deploy_result")
        })

    background_tasks.add_task(resume_graph)
    return {"status": "APPROVED", "message": "Deployment approved. Resuming cloud packaging..."}

# 4. OBSERVABILITY DASHBOARD ROUTE
@app.get("/api/observability/dashboard", response_model=ObservabilityMetricsResponse)
async def get_observability():
    return get_observability_dashboard()

# 5. WEBSOCKET STREAMING ROUTE
@app.websocket("/api/agents/ws/{run_id}")
async def agent_execution_websocket(websocket: WebSocket, run_id: str):
    await websocket.accept()
    if run_id not in ACTIVE_SOCKETS:
        ACTIVE_SOCKETS[run_id] = []
    ACTIVE_SOCKETS[run_id].append(websocket)

    # Immediately push current state
    if run_id in RUN_STORE:
        await websocket.send_json({
            "type": "INITIAL_STATE",
            "run_id": run_id,
            "state_snapshot": RUN_STORE[run_id]
        })

    try:
        while True:
            # Keep socket alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if run_id in ACTIVE_SOCKETS and websocket in ACTIVE_SOCKETS[run_id]:
            ACTIVE_SOCKETS[run_id].remove(websocket)
