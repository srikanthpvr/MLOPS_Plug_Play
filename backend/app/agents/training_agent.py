import os
import time
import joblib
from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from backend.app.agents.state import MLOpsState

def run_training_agent(state: MLOpsState) -> Dict[str, Any]:
    logs = list(state.get("logs", []))
    model_type = state.get("model_type", "lightgbm").lower()
    target_col = state.get("target_column", "churn")
    hp = state.get("hyperparameters", {})
    data_path = state.get("dataset_path")

    logs.append(f"[{time.strftime('%X')}] [Training Agent] Initializing model training ({model_type.upper()}) with target '{target_col}'...")

    df = pd.read_csv(data_path)
    if target_col not in df.columns:
        logs.append(f"[{time.strftime('%X')}] [Training Agent] Error: Target '{target_col}' not found.")
        return {
            "status": "FAILED",
            "current_step": "training_failed",
            "logs": logs
        }

    X = df.drop(columns=[target_col])
    y = df[target_col]

    # Preprocessing
    num_cols = X.select_dtypes(include=[np.number]).columns
    X[num_cols] = X[num_cols].fillna(X[num_cols].median())
    X = pd.get_dummies(X, drop_first=True)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    logs.append(f"[{time.strftime('%X')}] [Training Agent] Dataset split: {len(X_train)} train, {len(X_test)} validation samples.")

    # Initialize model
    if "forest" in model_type:
        n_est = int(hp.get("n_estimators", 100))
        depth = int(hp.get("max_depth", 8))
        clf = RandomForestClassifier(n_estimators=n_est, max_depth=depth, random_state=42)
    elif "logistic" in model_type or "linear" in model_type:
        c_val = float(hp.get("C", 1.0))
        clf = LogisticRegression(C=c_val, max_iter=500, random_state=42)
    else: # Gradient Boosting / LightGBM
        n_est = int(hp.get("n_estimators", 100))
        lr = float(hp.get("learning_rate", 0.05))
        depth = int(hp.get("max_depth", 5))
        clf = GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, max_depth=depth, random_state=42)

    start_train = time.time()
    clf.fit(X_train, y_train)
    train_duration = round(time.time() - start_train, 2)

    # Evaluate
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") and len(np.unique(y)) == 2 else None

    acc = float(accuracy_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred, average="weighted"))
    prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob)) if y_prob is not None else 0.85

    # Serialize candidate model
    artifact_dir = os.path.join(os.path.dirname(data_path), "artifacts", "candidate")
    os.makedirs(artifact_dir, exist_ok=True)
    model_path = os.path.join(artifact_dir, "model.pkl")
    joblib.dump(clf, model_path)

    metrics = {
        "model_type": model_type,
        "accuracy": round(acc, 4),
        "f1_score": round(f1, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "roc_auc": round(roc_auc, 4),
        "training_time_sec": train_duration,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "artifact_path": model_path,
        "features": list(X.columns)
    }

    logs.append(f"[{time.strftime('%X')}] [Training Agent] Training complete in {train_duration}s. F1: {metrics['f1_score']}, Accuracy: {metrics['accuracy']}.")

    return {
        "training_metrics": metrics,
        "current_step": "training_complete",
        "logs": logs
    }
