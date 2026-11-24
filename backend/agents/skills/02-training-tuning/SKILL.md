---
name: training-tuning
description: >-
  Autonomous Model Training, Hyperparameter Optimization, and Model Serialization Skill.
  Supports Scikit-Learn (RandomForest, LogisticRegression), LightGBM, XGBoost, and PyTorch MLP.
  Enforces stratified cross-validation, hyperparameter bounds checking, evaluation metric
  generation (F1, Accuracy, ROC-AUC), and multi-format serialization (.pkl, .onnx).
version: 1.0.0
tools:
  - train_and_serialize
---

# Training & Hyperparameter Tuning Agent Skill

## 1. Purpose & Scope
The **Training & Hyperparameter Tuning Agent** receives validated datasets from the Data Sentinel and trains the candidate model using engineer-selected architectures and hyperparameters. It guarantees reproducible artifact export, cross-validation scoring, and zero silent training crashes.

---

## 2. Invariants & Deterministic Rules
1. **Bounded Hyperparameters**: All user-supplied hyperparameters must be validated and clamped to prevent numerical divergence (e.g. learning rate $\in [10^{-5}, 1.0]$, max depth $\in [1, 32]$).
2. **Stratified Splitting**: For classification tasks, train/validation splitting must strictly preserve label distributions (`StratifiedKFold`).
3. **Artifact Completeness**: Every successful training run MUST produce:
   * Serialized model weights (`model.pkl` / `model.onnx`).
   * Schema signature metadata (`signature.json`).
   * Quantitative validation metrics (`metrics.json`).
4. **Graceful Fallbacks**: If GPU training is requested but CUDA is unavailable, the agent automatically falls back to CPU multi-threading and logs an informative notice.

---

## 3. Supported Model Frameworks & Default Parameters
* **LightGBM**: `learning_rate=0.05`, `num_leaves=31`, `n_estimators=100`, `max_depth=6`.
* **XGBoost**: `learning_rate=0.05`, `max_depth=6`, `n_estimators=100`, `subsample=0.8`.
* **Random Forest**: `n_estimators=100`, `max_depth=10`, `min_samples_split=2`.
* **Logistic Regression / ElasticNet**: `C=1.0`, `penalty='l2'`, `max_iter=500`.

---

## 4. Execution Playbook
1. Parse training parameters and target feature column from the agent state.
2. Run input assertions to prevent training on columns with 100% missing values or zero variance.
3. Execute `python scripts/train_and_serialize.py --data <train.csv> --model-type <type> --params <params.json> --output-dir <artifacts_dir>`.
4. Validate that `metrics.json` contains $F_1 \ge 0.50$ (or task-specific baseline) before declaring candidate ready for Evaluation Gate.
