---
name: data-sentinel
description: >-
  Enterprise Data Quality, Schema Validation, and Statistical Drift Detection Skill.
  Validates incoming data batches, enforces schema assertions with Pandera, computes
  two-sample Kolmogorov-Smirnov (KS) tests on continuous numerical features, and
  calculates Population Stability Index (PSI) with Laplace smoothing on categorical
  and binned distributions.
version: 1.0.0
tools:
  - check_drift_and_schema
---

# Data Sentinel Agent Skill

## 1. Purpose & Scope
The **Data Sentinel Agent** is the first operational defense line in the MLOps lifecycle. Its primary objective is to detect data corruption, schema violations, null spikes, and statistical covariate shifts before dirty data corrupts model training or causes silent failures in production inference endpoints.

---

## 2. Invariants & Deterministic Rules
1. **Zero Unvalidated Ingestion**: No dataset is allowed to advance to the Training Agent without passing schema validation and drift scoring.
2. **Deterministic Fallbacks**: If baseline reference data is missing, the agent flags an explicit warning and initializes the current batch as the baseline artifact.
3. **Smooth Zero Counts**: When computing Population Stability Index (PSI), bins with zero counts must use Laplace epsilon smoothing ($\epsilon = 10^{-4}$) to eliminate division-by-zero or $\ln(0)$ crashes.
4. **Data Contract Compliance**: All output reports must follow the strict JSON schema defined in `scripts/check_drift_and_schema.py`.

---

## 3. Statistical Drift Thresholds
* **Kolmogorov-Smirnov (KS-Test)**:
  * $p\text{-value} \ge 0.05$: No significant drift detected (Status: `HEALTHY`).
  * $0.01 \le p\text{-value} < 0.05$: Moderate distribution shift (Status: `WARNING`).
  * $p\text{-value} < 0.01$: Critical covariate shift detected (Status: `CRITICAL_DRIFT`).
* **Population Stability Index (PSI)**:
  * $\text{PSI} < 0.10$: Negligible shift (Status: `STABLE`).
  * $0.10 \le \text{PSI} < 0.25$: Moderate shift; retraining recommended (Status: `MODERATE_SHIFT`).
  * $\text{PSI} \ge 0.25$: Significant population change; immediate retraining required (Status: `ACTION_REQUIRED`).

---

## 4. Execution Playbook
1. **Load Datasets**: Ingest candidate inference/retraining data and the designated reference baseline dataset.
2. **Execute Pandera Validation**: Verify column presence, expected dtypes (float, int, category, datetime), and permissible range constraints.
3. **Execute Drift Calculation**: Run `python scripts/check_drift_and_schema.py --baseline <baseline.csv> --current <current.csv> --output <drift_report.json>`.
4. **Evaluate Gating Decision**:
   * If schema fails $\rightarrow$ Graph aborts with `SCHEMA_ERROR`.
   * If critical drift $> 30\%$ of features $\rightarrow$ Recommend retraining trigger with `RETRAIN_RECOMMENDED`.
   * If data clean $\rightarrow$ Emit `DATA_HEALTHY` and pass state to Training Agent.
