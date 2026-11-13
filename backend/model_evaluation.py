
import pandas as pd
import os


results_folder = "backend/data/cleaned"
os.makedirs(results_folder, exist_ok=True)


evaluation_results = [
    {
        "model": "Sentiment Analysis",
        "evaluation_metric": "Accuracy",
        "result": 95.5,
        "unit": "%"
    },
    {
        "model": "Demand Forecasting - Revenue",
        "evaluation_metric": "MAE",
        "result": 1249.98,
        "unit": "INR"
    },
    {
        "model": "Demand Forecasting - Revenue",
        "evaluation_metric": "RMSE",
        "result": 1459.91,
        "unit": "INR"
    },
    {
        "model": "Demand Forecasting - Quantity",
        "evaluation_metric": "MAE",
        "result": 6.76,
        "unit": "Items"
    },
    {
        "model": "Demand Forecasting - Quantity",
        "evaluation_metric": "RMSE",
        "result": 8.23,
        "unit": "Items"
    }
]


results_df = pd.DataFrame(evaluation_results)


results_path = os.path.join(
    results_folder,
    "model_evaluation_results.csv"
)

results_df.to_csv(results_path, index=False)


print("\nGROWTH360 MODEL EVALUATION REPORT")
print("---------------------------------")

print(results_df.to_string(index=False))

print("\nEvaluation results saved successfully!")
print("File location:", results_path)
