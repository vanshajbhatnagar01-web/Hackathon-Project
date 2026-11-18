

import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


backend_folder = Path(__file__).resolve().parent
project_folder = backend_folder.parent

sales_file = backend_folder / "data" / "cafe_nova_90_days_sales.csv"
model_folder = backend_folder / "ml"
output_folder = backend_folder / "data" / "cleaned"

model_folder.mkdir(parents=True, exist_ok=True)
output_folder.mkdir(parents=True, exist_ok=True)


sales = pd.read_csv(sales_file)

print("Growth360 sales data loaded successfully!")
print("Total sales records:", len(sales))


sales["date"] = pd.to_datetime(sales["date"])

daily_sales = sales.groupby("date").agg(
    daily_revenue=("revenue", "sum"),
    daily_quantity=("quantity_sold", "sum")
).reset_index()

daily_sales = daily_sales.sort_values("date").reset_index(drop=True)

print("\nTotal days of sales data:", len(daily_sales))


def create_features(sales_data, target_column):

    values = sales_data[target_column].values
    dates = sales_data["date"].values

    features = []
    targets = []
    feature_dates = []

    for i in range(14, len(values)):

        current_date = pd.Timestamp(dates[i])

        features.append([
            current_date.day_of_week,
            values[i - 1],                  
            values[i - 7],              
            values[i - 14],               
            np.mean(values[i - 7:i])      
        ])

        targets.append(values[i])
        feature_dates.append(current_date)

    return pd.DataFrame(
        features,
        columns=[
            "day_of_week",
            "sales_yesterday",
            "sales_7_days_ago",
            "sales_14_days_ago",
            "average_last_7_days"
        ]
    ), np.array(targets), feature_dates


def train_model(features, targets, model_name):

  
    split_point = len(features) - 14

    X_train = features.iloc[:split_point]
    X_test = features.iloc[split_point:]

    y_train = targets[:split_point]
    y_test = targets[split_point:]

    print("\nTraining", model_name, "model...")

    model = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        random_state=42
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    print(model_name, "MAE:", round(mae, 2))
    print(model_name, "RMSE:", round(rmse, 2))

    
    model.fit(features, targets)

    return model



revenue_features, revenue_targets, _ = create_features(
    daily_sales, "daily_revenue"
)

quantity_features, quantity_targets, _ = create_features(
    daily_sales, "daily_quantity"
)

revenue_model = train_model(
    revenue_features, revenue_targets, "Revenue"
)

quantity_model = train_model(
    quantity_features, quantity_targets, "Quantity"
)



def forecast_next_seven_days(model, sales_history, start_date):

    predictions = []

  
    history = list(sales_history)

    for day in range(7):

        forecast_date = start_date + pd.Timedelta(days=day)

        input_data = pd.DataFrame([{
            "day_of_week": forecast_date.day_of_week,
            "sales_yesterday": history[-1],
            "sales_7_days_ago": history[-7],
            "sales_14_days_ago": history[-14],
            "average_last_7_days": np.mean(history[-7:])
        }])

        predicted_value = model.predict(input_data)[0]

       
        predicted_value = max(0, predicted_value)

        predictions.append(round(predicted_value, 2))

       
        history.append(predicted_value)

    return predictions


last_date = daily_sales["date"].max()
next_date = last_date + pd.Timedelta(days=1)

revenue_forecast = forecast_next_seven_days(
    revenue_model,
    daily_sales["daily_revenue"],
    next_date
)


quantity_forecast = forecast_next_seven_days(
    quantity_model,
    daily_sales["daily_quantity"],
    next_date
)


quantity_forecast = [
    round(quantity) for quantity in quantity_forecast
]



forecast_dates = pd.date_range(
    start=next_date,
    periods=7,
    freq="D"
)

forecast_results = pd.DataFrame({
    "date": forecast_dates,
    "predicted_revenue": revenue_forecast,
    "predicted_quantity": quantity_forecast
})

forecast_file = output_folder / "seven_day_demand_forecast.csv"

forecast_results.to_csv(forecast_file, index=False)



joblib.dump({
    "revenue_model": revenue_model,
    "quantity_model": quantity_model
}, model_folder / "demand_forecasting_model.joblib")



print("\nNEXT 7 DAYS SALES FORECAST")
print(forecast_results.to_string(index=False))

print("\nForecast saved successfully!")
print("Model saved successfully!")
print("\nGROWTH360 DEMAND FORECASTING COMPLETED!")
