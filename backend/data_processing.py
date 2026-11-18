
import pandas as pd
import os


reviews = pd.read_csv("backend/data/cafe_nova_1000_customer_reviews.csv")
sales = pd.read_csv("backend/data/cafe_nova_90_days_sales.csv")
business = pd.read_csv("backend/data/cafe_nova_business_profile.csv")

print("All datasets loaded successfully!")


print("\nReviews information:")
print(reviews.info())

print("\nSales information:")
print(sales.info())


reviews.columns = reviews.columns.str.strip()
reviews = reviews.drop_duplicates()

reviews["review_text"] = reviews["review_text"].fillna("")
reviews["rating"] = pd.to_numeric(reviews["rating"], errors="coerce")
reviews["date"] = pd.to_datetime(reviews["date"], errors="coerce")

reviews = reviews.dropna(subset=["rating", "date"])
reviews = reviews[reviews["rating"].between(1, 5)]


sales.columns = sales.columns.str.strip()
sales = sales.drop_duplicates()

sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
sales["quantity_sold"] = pd.to_numeric(sales["quantity_sold"], errors="coerce")
sales["revenue"] = pd.to_numeric(sales["revenue"], errors="coerce")

sales = sales.dropna(subset=["date", "quantity_sold", "revenue"])

sales = sales[
    (sales["quantity_sold"] >= 0) &
    (sales["revenue"] >= 0)
]

business = business.drop_duplicates()


average_rating = reviews["rating"].mean()

print("\nAverage customer rating:", round(average_rating, 2))

print("\nCustomer rating distribution:")
print(reviews["rating"].value_counts().sort_index())

print("\nAverage rating by product:")
print(reviews.groupby("product")["rating"].mean().sort_values())


total_revenue = sales["revenue"].sum()
total_quantity = sales["quantity_sold"].sum()

print("\nTotal revenue: Rs.", round(total_revenue, 2))
print("Total items sold:", total_quantity)

print("\nTop 5 products by revenue:")
print(
    sales.groupby("product")["revenue"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
)


if "hour" in sales.columns:
    sales["hour"] = pd.to_numeric(sales["hour"], errors="coerce")
    hourly_sales = sales.groupby("hour")["revenue"].sum()

    print("\nSales by hour:")
    print(hourly_sales.sort_values(ascending=False).head(5))


review_analysis = reviews.groupby("product").agg(
    average_rating=("rating", "mean"),
    total_reviews=("rating", "count")
)

sales_analysis = sales.groupby("product").agg(
    total_sales=("revenue", "sum"),
    total_quantity=("quantity_sold", "sum")
)

comparison = review_analysis.join(sales_analysis, how="outer")

print("\nCustomer reviews and sales comparison:")
print(comparison)


os.makedirs("backend/data/cleaned", exist_ok=True)

reviews.to_csv("backend/data/cleaned/cleaned_reviews.csv", index=False)
sales.to_csv("backend/data/cleaned/cleaned_sales.csv", index=False)
business.to_csv("backend/data/cleaned/cleaned_business_profile.csv", index=False)
comparison.to_csv("backend/data/cleaned/product_comparison.csv")

print("\nAll cleaned files saved successfully!")
print("Data cleaning and analysis completed!")
