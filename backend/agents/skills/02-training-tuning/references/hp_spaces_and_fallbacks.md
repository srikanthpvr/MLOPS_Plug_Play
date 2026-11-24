# Training & Hyperparameter Tuning Reference: Parameter Spaces & Fallbacks

## 1. Hyperparameter Bounds and Safe Defaults

To prevent divergence, out-of-memory errors, and infinite loops, hyperparameters are restricted to safe operational intervals:

| Model Family | Parameter | Safe Min | Safe Max | Default | Failure Mode if Violated |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LightGBM / GBDT** | `learning_rate` | `0.001` | `0.5` | `0.05` | $>1.0$ causes exploding gradient / NaN loss. |
| **LightGBM / GBDT** | `max_depth` | `2` | `16` | `6` | $>20$ leads to exponential leaf growth and OOM crash. |
| **Random Forest** | `n_estimators` | `10` | `500` | `100` | $>1000$ leads to CPU thread starvation and slow inference. |
| **Logistic Regression**| `C` (inverse reg) | `0.001` | `100.0` | `1.0` | $C \to 0$ over-regularizes; $C \to \infty$ overfits completely. |

---

## 2. Imbalance & Missing Value Fallback Strategy
1. **Target Imbalance**: When positive class prevalence is $< 10\%$, standard accuracy produces a deceptive false-high metric. The script automatically reports weighted F1-score and ROC-AUC.
2. **Missing Feature Imputation**: Median imputation is used for numerical features; missing categorical features are encoded as explicit `__MISSING__` category indicators.
3. **Hardware Fallback**: If GPU libraries are specified but compute engines do not detect NVidia CUDA drivers, fallback flags are automatically passed to run on OpenMP multi-core CPU threads.
