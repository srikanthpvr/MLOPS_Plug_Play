from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class AgentRunRequest(BaseModel):
    dataset_name: str
    target_column: str = "churn"
    model_type: str = "lightgbm"
    hyperparameters: Dict[str, Any] = {}
    sla_p95_ms: float = 50.0
    auto_deploy: bool = False

class AgentRunResponse(BaseModel):
    run_id: str
    status: str
    current_step: str
    message: str

class HITLApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = "Approved by MLOps Engineer"

class AgentRunStatusResponse(BaseModel):
    run_id: str
    status: str
    current_step: str
    awaiting_hitl_approval: bool
    logs: List[str]
    data_quality_report: Optional[Dict[str, Any]] = None
    training_metrics: Optional[Dict[str, Any]] = None
    eval_gate_result: Optional[Dict[str, Any]] = None
    security_audit_report: Optional[Dict[str, Any]] = None
    deploy_result: Optional[Dict[str, Any]] = None
