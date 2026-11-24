import os
import sys
import unittest
import numpy as np
import pandas as pd

# Add mlops_agentic_suite to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.agents.state import MLOpsState
from backend.app.agents.supervisor import mlops_compiled_graph
from backend.app.agents.data_sentinel import calculate_psi
from backend.app.services.data_service import list_datasets, get_dataset_preview
from backend.app.services.observability_service import get_observability_dashboard


class TestMLOpsAgentSuite(unittest.TestCase):

    def test_01_psi_calculation(self):
        """Test PSI calculation with zero smoothing."""
        baseline = np.random.normal(50, 10, 1000)
        current_shifted = np.random.normal(65, 12, 1000) # Covariate shift
        psi_val = calculate_psi(baseline, current_shifted)
        self.assertGreater(psi_val, 0.15, "Shifted data should have PSI > 0.15")

    def test_02_data_service(self):
        """Test scanning datasets and schema profiler."""
        datasets = list_datasets()
        self.assertGreater(len(datasets), 0, "Should detect at least 1 dataset")
        preview = get_dataset_preview("current_drifted_churn.csv")
        self.assertIsNotNone(preview)
        self.assertGreater(len(preview.columns), 3)

    def test_03_observability_dashboard(self):
        """Test observability metrics aggregation."""
        obs = get_observability_dashboard()
        self.assertEqual(obs.model_name, "Customer-Churn-Classifier")
        self.assertGreater(len(obs.timeseries_metrics), 5)
        self.assertGreater(len(obs.feature_drifts), 2)

    def test_04_langgraph_pipeline_rejection_branch(self):
        """Test that Eval Gate correctly rejects and aborts when Challenger underperforms Champion."""
        run_id = "test-run-reject"
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        current_data = os.path.join(data_dir, "current_drifted_churn.csv")
        baseline_data = os.path.join(data_dir, "baseline_churn.csv")

        state: MLOpsState = {
            "thread_id": run_id,
            "dataset_name": "current_drifted_churn.csv",
            "dataset_path": current_data,
            "baseline_path": baseline_data,
            "target_column": "churn",
            "model_type": "logistic_regression",
            "hyperparameters": {},
            "sla_p95_ms": 50.0,
            "champion_f1": 0.95, # High champion baseline forces rejection
            "auto_deploy": False,
            "data_quality_report": None,
            "training_metrics": None,
            "eval_gate_result": None,
            "security_audit_report": None,
            "deploy_result": None,
            "current_step": "initialized",
            "logs": [],
            "awaiting_hitl_approval": False,
            "hitl_approved": False,
            "status": "RUNNING"
        }

        config = {"configurable": {"thread_id": run_id}}
        for event in mlops_compiled_graph.stream(state, config=config):
            pass

        final_state = mlops_compiled_graph.get_state(config)
        self.assertEqual(final_state.values.get("status"), "REJECTED")
        self.assertEqual(final_state.values.get("eval_gate_result", {}).get("decision"), "REJECTED")

    def test_05_langgraph_pipeline_promotion_and_hitl(self):
        """Test full happy-path: Challenger promoted, halts at HITL checkpoint, resumes on approval."""
        run_id = "test-run-promote"
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        current_data = os.path.join(data_dir, "current_drifted_churn.csv")
        baseline_data = os.path.join(data_dir, "baseline_churn.csv")

        state: MLOpsState = {
            "thread_id": run_id,
            "dataset_name": "current_drifted_churn.csv",
            "dataset_path": current_data,
            "baseline_path": baseline_data,
            "target_column": "churn",
            "model_type": "lightgbm",
            "hyperparameters": {"n_estimators": 50, "learning_rate": 0.05, "max_depth": 5},
            "sla_p95_ms": 50.0,
            "champion_f1": 0.65, # Challenger (F1~0.71) beats Champion (0.65)
            "auto_deploy": False,
            "data_quality_report": None,
            "training_metrics": None,
            "eval_gate_result": None,
            "security_audit_report": None,
            "deploy_result": None,
            "current_step": "initialized",
            "logs": [],
            "awaiting_hitl_approval": False,
            "hitl_approved": False,
            "status": "RUNNING"
        }

        config = {"configurable": {"thread_id": run_id}}

        # Phase 1: Stream until interrupt before packager_agent
        for event in mlops_compiled_graph.stream(state, config=config):
            pass

        checkpoint_state = mlops_compiled_graph.get_state(config)
        self.assertEqual(checkpoint_state.next, ("packager_agent",))
        self.assertEqual(checkpoint_state.values.get("eval_gate_result", {}).get("decision"), "PROMOTED")
        self.assertEqual(checkpoint_state.values.get("security_audit_report", {}).get("status"), "PASS")

        # Phase 2: Resume stream upon Human Approval
        for event in mlops_compiled_graph.stream(None, config=config):
            pass

        final_state = mlops_compiled_graph.get_state(config)
        self.assertEqual(final_state.values.get("status"), "COMPLETED")
        self.assertIsNotNone(final_state.values.get("deploy_result"))
        self.assertEqual(final_state.values.get("deploy_result", {}).get("status"), "DEPLOYED")


if __name__ == "__main__":
    unittest.main()
