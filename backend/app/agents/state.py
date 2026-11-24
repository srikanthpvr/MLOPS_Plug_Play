from typing import Dict, Any, List, Optional, TypedDict

class MLOpsState(TypedDict):
    thread_id: str
    dataset_name: str
    dataset_path: str
    baseline_path: Optional[str]
    target_column: str
    model_type: str
    hyperparameters: Dict[str, Any]
    sla_p95_ms: float
    champion_f1: Optional[float]
    auto_deploy: bool

    # Agent Generated Outputs
    data_quality_report: Optional[Dict[str, Any]]
    training_metrics: Optional[Dict[str, Any]]
    eval_gate_result: Optional[Dict[str, Any]]
    security_audit_report: Optional[Dict[str, Any]]
    deploy_result: Optional[Dict[str, Any]]

    # Pipeline Execution State
    current_step: str
    logs: List[str]
    awaiting_hitl_approval: bool
    hitl_approved: bool
    status: str # "RUNNING", "AWAITING_APPROVAL", "COMPLETED", "REJECTED", "FAILED"
