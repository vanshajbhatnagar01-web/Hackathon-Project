
import pandas as pd
from pathlib import Path


backend_folder = Path(__file__).resolve().parent.parent
cleaned_folder = backend_folder / "data" / "cleaned"

sales = pd.read_csv(cleaned_folder / "cleaned_sales.csv")

print("Growth360 Demand Agent started!")
print("Sales data loaded successfully.\n")



total_revenue = sales["revenue"].sum()
total_quantity = sales["quantity_sold"].sum()
average_daily_revenue = sales.groupby("date")["revenue"].sum().mean()

print("SALES PERFORMANCE")
print("----------------")
print(f"Total Revenue: Rs. {total_revenue:,.2f}")
print(f"Total Items Sold: {total_quantity:,}")
print(f"Average Daily Revenue: Rs. {average_daily_revenue:,.2f}")



product_sales = (
    sales.groupby("product")
    .agg(
        total_revenue=("revenue", "sum"),
        total_quantity=("quantity_sold", "sum")
    )
    .sort_values("total_revenue", ascending=False)
)

print("\nTOP 5 PRODUCTS BY REVENUE")
print("------------------------")
print(product_sales.head(5))



hourly_sales = (
    sales.groupby("hour")
    .agg(
        total_revenue=("revenue", "sum"),
        total_quantity=("quantity_sold", "sum")
    )
    .sort_values("total_revenue", ascending=False)
)

busiest_hour = hourly_sales.index[0]
busiest_hour_revenue = hourly_sales.iloc[0]["total_revenue"]

print("\nBUSIEST SALES HOUR")
print("------------------")
print(f"Hour: {busiest_hour}:00")
print(f"Revenue: Rs. {busiest_hour_revenue:,.2f}")



sales["date"] = pd.to_datetime(sales["date"])

daily_sales = (
    sales.groupby("date")
    .agg(
        daily_revenue=("revenue", "sum"),
        daily_quantity=("quantity_sold", "sum")
    )
    .sort_index()
)

best_day = daily_sales["daily_revenue"].idxmax()
slowest_day = daily_sales["daily_revenue"].idxmin()

print("\nDAILY SALES TRENDS")
print("------------------")
print("Highest revenue day:", best_day.date())
print(f"Revenue: Rs. {daily_sales.loc[best_day, 'daily_revenue']:,.2f}")

print("Lowest revenue day:", slowest_day.date())
print(f"Revenue: Rs. {daily_sales.loc[slowest_day, 'daily_revenue']:,.2f}")



forecast_file = cleaned_folder / "seven_day_demand_forecast.csv"

if forecast_file.exists():

    forecast = pd.read_csv(forecast_file)

    print("\nNEXT 7 DAYS FORECAST")
    print("--------------------")
    print(forecast.to_string(index=False))

   
    forecast_revenue = forecast["predicted_revenue"].sum()
    forecast_quantity = forecast["predicted_quantity"].sum()

    print("\nExpected Revenue (7 days):")
    print(f"Rs. {forecast_revenue:,.2f}")

    print("Expected Items Sold (7 days):")
    print(f"{forecast_quantity:,.0f}")

else:
    print("\nForecast file not found.")
    print("Run demand_forecasting.py first.")



insights = []


top_product = product_sales.index[0]
top_product_revenue = product_sales.iloc[0]["total_revenue"]

insights.append(
    f"{top_product} is the highest revenue product, "
    f"generating Rs. {top_product_revenue:,.2f}."
)


insights.append(
    f"{busiest_hour}:00 is the busiest sales hour, "
    f"generating Rs. {busiest_hour_revenue:,.2f}."
)


insights.append(
    f"{slowest_day.strftime('%A')} ({slowest_day.date()}) "
    "had the lowest daily revenue in the dataset."
)

print("\nDEMAND AGENT INSIGHTS")
print("--------------------")

for insight in insights:
    print("-", insight)



product_report = product_sales.reset_index()

hourly_report = hourly_sales.reset_index()

daily_report = daily_sales.reset_index()

insight_report = pd.DataFrame({
    "insight": insights
})

product_report.to_csv(
    cleaned_folder / "demand_agent_product_report.csv",
    index=False
)

hourly_report.to_csv(
    cleaned_folder / "demand_agent_hourly_report.csv",
    index=False
)

daily_report.to_csv(
    cleaned_folder / "demand_agent_daily_report.csv",
    index=False
)

insight_report.to_csv(
    cleaned_folder / "demand_agent_insights.csv",
    index=False
)

print("\nDemand Agent completed successfully!")
print("All reports saved in the cleaned data folder.")
