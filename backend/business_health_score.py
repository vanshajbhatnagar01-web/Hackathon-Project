
import pandas as pd
from pathlib import Path



backend_folder = Path(__file__).resolve().parent
cleaned_folder = backend_folder / "data" / "cleaned"

reviews_file = cleaned_folder / "cleaned_reviews.csv"
sales_file = cleaned_folder / "cleaned_sales.csv"



reviews = pd.read_csv(reviews_file)
sales = pd.read_csv(sales_file)

reviews["date"] = pd.to_datetime(reviews["date"])
sales["date"] = pd.to_datetime(sales["date"])

print("Growth360 business data loaded successfully!")



average_rating = reviews["rating"].mean()

# Convert the 1-5 rating into a 0-100 score
customer_satisfaction_score = (
    (average_rating - 1) / 4
) * 100



daily_sales = sales.groupby("date").agg(
    daily_revenue=("revenue", "sum"),
    daily_quantity=("quantity_sold", "sum")
).sort_index()

if len(daily_sales) < 60:
    raise ValueError(
        "At least 60 days of sales data are required."
    )


last_30_days = daily_sales.tail(30)
previous_30_days = daily_sales.iloc[-60:-30]

current_revenue = last_30_days["daily_revenue"].sum()
previous_revenue = previous_30_days["daily_revenue"].sum()

if previous_revenue > 0:
    revenue_growth = (
        (current_revenue - previous_revenue)
        / previous_revenue
    ) * 100
else:
    revenue_growth = 0


revenue_score = max(
    0,
    min(100, 50 + (revenue_growth * 2))
)



current_quantity = last_30_days["daily_quantity"].sum()
previous_quantity = previous_30_days["daily_quantity"].sum()

if previous_quantity > 0:
    quantity_growth = (
        (current_quantity - previous_quantity)
        / previous_quantity
    ) * 100
else:
    quantity_growth = 0

demand_score = max(
    0,
    min(100, 50 + (quantity_growth * 2))
)



product_ratings = reviews.groupby("product").agg(
    average_rating=("rating", "mean")
).reset_index()

product_revenue = sales.groupby("product").agg(
    total_revenue=("revenue", "sum")
).reset_index()

product_data = pd.merge(
    product_ratings,
    product_revenue,
    on="product",
    how="inner"
)


median_revenue = product_data["total_revenue"].median()


healthy_products = product_data[
    (product_data["average_rating"] >= 3.5)
    & (product_data["total_revenue"] >= median_revenue)
]

total_products = len(product_data)

if total_products > 0:
    product_score = (
        len(healthy_products) / total_products
    ) * 100
else:
    product_score = 0



weekly_revenue = (
    daily_sales["daily_revenue"]
    .resample("W")
    .sum()
)

average_weekly_revenue = weekly_revenue.mean()

if average_weekly_revenue > 0:
    revenue_variation = (
        weekly_revenue.std() / average_weekly_revenue
    )
else:
    revenue_variation = 1


consistency_score = max(
    0,
    min(100, 100 - (revenue_variation * 100))
)



health_score = (
    customer_satisfaction_score * 0.25
    + revenue_score * 0.25
    + demand_score * 0.20
    + product_score * 0.15
    + consistency_score * 0.15
)

health_score = round(health_score, 2)



if health_score >= 80:
    health_status = "Excellent"
elif health_score >= 65:
    health_status = "Good"
elif health_score >= 50:
    health_status = "Needs Improvement"
else:
    health_status = "At Risk"


score_breakdown = [
    {
        "category": "Customer Satisfaction",
        "score": round(customer_satisfaction_score, 2),
        "weight": "25%"
    },
    {
        "category": "Revenue Performance",
        "score": round(revenue_score, 2),
        "weight": "25%"
    },
    {
        "category": "Sales and Demand",
        "score": round(demand_score, 2),
        "weight": "20%"
    },
    {
        "category": "Product Portfolio",
        "score": round(product_score, 2),
        "weight": "15%"
    },
    {
        "category": "Sales Consistency",
        "score": round(consistency_score, 2),
        "weight": "15%"
    }
]

breakdown_df = pd.DataFrame(score_breakdown)



health_result = pd.DataFrame([{
    "business_name": "Cafe Nova",
    "health_score": health_score,
    "health_status": health_status,
    "average_rating": round(average_rating, 2),
    "revenue_growth_percent": round(revenue_growth, 2),
    "quantity_growth_percent": round(quantity_growth, 2)
}])

health_result.to_csv(
    cleaned_folder / "business_health_score.csv",
    index=False
)

breakdown_df.to_csv(
    cleaned_folder / "business_health_breakdown.csv",
    index=False
)


print("\nGROWTH360 BUSINESS HEALTH REPORT")
print("--------------------------------")

print("\nOVERALL BUSINESS HEALTH SCORE")
print(f"Health Score: {health_score}/100")
print(f"Business Status: {health_status}")

print("\nCATEGORY-WISE SCORES")
print(breakdown_df.to_string(index=False))

print("\nBUSINESS PERFORMANCE")
print(f"Average Customer Rating: {average_rating:.2f}/5")
print(f"Revenue Growth: {revenue_growth:.2f}%")
print(f"Quantity Growth: {quantity_growth:.2f}%")

print("\nBusiness Health Score calculated successfully!")
print("Results saved in:", cleaned_folder)
