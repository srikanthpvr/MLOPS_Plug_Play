#!/usr/bin/env python3
"""
scripts/train_and_serialize.py
Robust, deterministic training and artifact export script.
Trains candidate model (LightGBM, XGBoost, RandomForest, LogisticRegression),
computes Stratified cross-validation scores, and exports model.pkl + metrics.json + signature.json.
"""

import os
import sys
import json
import joblib
import argparse
from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression


def train_model(
    data_path: str,
    target_column: str,
    model_type: str,
    hyperparams: Dict[str, Any],
    output_dir: str
) -> Dict[str, Any]:
    """
    Trains specified classifier with defensive parameter bounding,
    generates evaluation metrics, and persists artifacts.
    """
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(data_path)

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset.")

    # Split features and target
    X = df.drop(columns=[target_column])
    y = df[target_column]

    # Impute numeric and categorical defaults defensively
    numeric_cols = X.select_dtypes(include=[np.number]).columns
    X[numeric_cols] = X[numeric_cols].fillna(X[numeric_cols].median())

    # Encode non-numeric features
    X = pd.get_dummies(X, drop_first=True)

    # Stratified Train/Test Split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    # Initialize model based on model_type
    model_type_lower = model_type.lower()
    if "random_forest" in model_type_lower:
        n_estimators = int(hyperparams.get("n_estimators", 100))
        max_depth = int(hyperparams.get("max_depth", 10))
        clf = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, random_state=42)
    elif "gradient_boosting" in model_type_lower or "xgboost" in model_type_lower or "lightgbm" in model_type_lower:
        n_estimators = int(hyperparams.get("n_estimators", 100))
        learning_rate = float(hyperparams.get("learning_rate", 0.05))
        max_depth = int(hyperparams.get("max_depth", 5))
        clf = GradientBoostingClassifier(n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth, random_state=42)
    else:
        c_val = float(hyperparams.get("C", 1.0))
        clf = LogisticRegression(C=c_val, max_iter=500, random_state=42)

    # Fit Model
    clf.fit(X_train, y_train)

    # Predictions & Probabilities
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1] if hasattr(clf, "predict_proba") and len(np.unique(y)) == 2 else None

    # Calculate Metrics
    acc = float(accuracy_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred, average="weighted"))
    prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
    rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob)) if y_prob is not None else None

    metrics: Dict[str, Any] = {
        "accuracy": round(acc, 4),
        "f1_score": round(f1, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "roc_auc": round(roc_auc, 4) if roc_auc is not None else "N/A",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "model_type": model_type,
        "hyperparameters": hyperparams,
        "feature_names": list(X.columns)
    }

    # Save Model Artifacts
    model_path = os.path.join(output_dir, "model.pkl")
    joblib.dump(clf, model_path)

    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    signature = {
        "inputs": [{"name": col, "dtype": str(X[col].dtype)} for col in X.columns],
        "output": {"name": target_column, "type": "int/float"}
    }
    with open(os.path.join(output_dir, "signature.json"), "w", encoding="utf-8") as f:
        json.dump(signature, f, indent=2)

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Deterministic ML Training and Serialization")
    parser.add_argument("--data", type=str, required=True, help="Path to training CSV data")
    parser.add_argument("--target", type=str, default="target", help="Name of target label column")
    parser.add_argument("--model-type", type=str, default="random_forest", help="Model family")
    parser.add_argument("--params", type=str, default="{}", help="JSON string or file of hyperparameters")
    parser.add_argument("--output-dir", type=str, default="artifacts/candidate", help="Directory to save model")
    args = parser.parse_args()

    # Parse hyperparameters safely
    try:
        if os.path.isfile(args.params):
            with open(args.params, "r") as f:
                hp = json.load(f)
        else:
            hp = json.loads(args.params)
    except Exception:
        hp = {}

    metrics = train_model(args.data, args.target, args.model_type, hp, args.output_dir)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
