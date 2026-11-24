import os
import numpy as np
import pandas as pd

def generate_datasets():
    data_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(data_dir, exist_ok=True)
    np.random.seed(42)

    n_samples = 2000

    # 1. Baseline Reference Data (Normal Distribution)
    age = np.random.normal(loc=38.0, scale=10.0, size=n_samples).clip(18, 75)
    monthly_charges = np.random.normal(loc=65.0, scale=20.0, size=n_samples).clip(20, 150)
    tenure_months = np.random.exponential(scale=24.0, size=n_samples).clip(1, 72)
    contract_type = np.random.choice([0, 1, 2], p=[0.5, 0.3, 0.2], size=n_samples) # 0=Month-to-month, 1=One year, 2=Two year
    internet_service = np.random.choice([0, 1, 2], p=[0.4, 0.4, 0.2], size=n_samples) # 0=DSL, 1=Fiber, 2=None
    total_charges = monthly_charges * tenure_months + np.random.normal(0, 10, n_samples)
    
    # Target churn probability
    churn_logit = -2.0 + (monthly_charges * 0.03) - (tenure_months * 0.05) - (contract_type * 0.8)
    churn_prob = 1 / (1 + np.exp(-churn_logit))
    churn = (np.random.rand(n_samples) < churn_prob).astype(int)

    baseline_df = pd.DataFrame({
        "age": np.round(age, 1),
        "monthly_charges": np.round(monthly_charges, 2),
        "tenure_months": np.round(tenure_months, 1),
        "total_charges": np.round(total_charges, 2),
        "contract_type": contract_type,
        "internet_service": internet_service,
        "churn": churn
    })

    baseline_path = os.path.join(data_dir, "baseline_churn.csv")
    baseline_df.to_csv(baseline_path, index=False)
    print(f"Created baseline reference dataset: {baseline_path} ({len(baseline_df)} rows)")

    # 2. Current Inference / Retraining Data (Covariate Shift in Monthly Charges & Fiber optic)
    n_current = 1500
    curr_age = np.random.normal(loc=41.0, scale=12.0, size=n_current).clip(18, 75)
    # Drifted: Significant price increase & shift to fiber
    curr_monthly_charges = np.random.normal(loc=88.0, scale=25.0, size=n_current).clip(30, 180) # Covariate shift!
    curr_tenure_months = np.random.exponential(scale=18.0, size=n_current).clip(1, 72)
    curr_contract_type = np.random.choice([0, 1, 2], p=[0.65, 0.25, 0.1], size=n_current)
    curr_internet_service = np.random.choice([0, 1, 2], p=[0.15, 0.75, 0.1], size=n_current) # Shift towards Fiber
    curr_total_charges = curr_monthly_charges * curr_tenure_months + np.random.normal(0, 10, n_current)

    curr_churn_logit = -1.5 + (curr_monthly_charges * 0.035) - (curr_tenure_months * 0.05) - (curr_contract_type * 0.8)
    curr_churn_prob = 1 / (1 + np.exp(-curr_churn_logit))
    curr_churn = (np.random.rand(n_current) < curr_churn_prob).astype(int)

    current_df = pd.DataFrame({
        "age": np.round(curr_age, 1),
        "monthly_charges": np.round(curr_monthly_charges, 2),
        "tenure_months": np.round(curr_tenure_months, 1),
        "total_charges": np.round(curr_total_charges, 2),
        "contract_type": curr_contract_type,
        "internet_service": curr_internet_service,
        "churn": curr_churn
    })

    current_path = os.path.join(data_dir, "current_drifted_churn.csv")
    current_df.to_csv(current_path, index=False)
    print(f"Created current drifted dataset: {current_path} ({len(current_df)} rows)")

if __name__ == "__main__":
    generate_datasets()
