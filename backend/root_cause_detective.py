
import pandas as pd
from pathlib import Path



backend_folder = Path(__file__).resolve().parent
cleaned_folder = backend_folder / "data" / "cleaned"

reviews_file = cleaned_folder / "cleaned_reviews.csv"
sales_file = cleaned_folder / "cleaned_sales.csv"


reviews = pd.read_csv(reviews_file)
sales = pd.read_csv(sales_file)

print("Growth360 data loaded successfully!")



product_ratings = reviews.groupby("product").agg(
    average_rating=("rating", "mean"),
    total_reviews=("rating", "count")
).reset_index()


product_sales = sales.groupby("product").agg(
    total_revenue=("revenue", "sum"),
    total_quantity=("quantity_sold", "sum")
).reset_index()



product_analysis = pd.merge(
    product_ratings,
    product_sales,
    on="product",
    how="outer"
)

product_analysis["average_rating"] = (
    product_analysis["average_rating"].round(2)
)

product_analysis["total_revenue"] = (
    product_analysis["total_revenue"].round(2)
)



low_rating_products = product_analysis[
    product_analysis["average_rating"] < 3.5
]

high_revenue_products = product_analysis.sort_values(
    by="total_revenue",
    ascending=False
).head(5)

findings = []

for _, product in low_rating_products.iterrows():

    findings.append({
        "finding_type": "Low Customer Rating",
        "product": product["product"],
        "evidence": (
            f"Average rating: {product['average_rating']}/5 "
            f"from {int(product['total_reviews'])} reviews"
        ),
        "recommendation": (
            "Investigate product quality, preparation "
            "and customer feedback."
        ),
        "priority": "High"
    })

for _, product in high_revenue_products.iterrows():

    findings.append({
        "finding_type": "High Revenue Product",
        "product": product["product"],
        "evidence": (
            f"Revenue: Rs. {product['total_revenue']:.2f}, "
            f"quantity sold: {int(product['total_quantity'])}"
        ),
        "recommendation": (
            "Monitor stock availability and maintain "
            "product quality."
        ),
        "priority": "Opportunity"
    })



complaint_themes = {
    "Food Quality": [
        "cold", "tasteless", "stale", "undercooked",
        "overcooked", "burnt", "fresh"
    ],
    "Service": [
        "rude", "staff", "unfriendly", "behaviour",
        "behavior", "service"
    ],
    "Waiting Time": [
        "slow", "late", "waiting", "delay",
        "long time", "took too long"
    ],
    "Price": [
        "expensive", "overpriced", "costly",
        "price", "money"
    ],
    "Cleanliness": [
        "dirty", "hygiene", "clean", "messy"
    ]
}


negative_reviews = reviews[reviews["rating"] <= 2].copy()

negative_reviews["review_text"] = (
    negative_reviews["review_text"]
    .fillna("")
    .astype(str)
    .str.lower()
)

for theme, keywords in complaint_themes.items():

    pattern = "|".join(keywords)

    matching_reviews = negative_reviews[
        negative_reviews["review_text"].str.contains(
            pattern,
            regex=True,
            na=False
        )
    ]

    if len(matching_reviews) > 0:

        findings.append({
            "finding_type": "Customer Complaint Theme",
            "product": "All Products",
            "evidence": (
                f"{theme} keywords appeared in "
                f"{len(matching_reviews)} low-rated reviews"
            ),
            "recommendation": (
                f"Review customer feedback related to {theme.lower()}."
            ),
            "priority": "High"
        })



findings_df = pd.DataFrame(findings)

product_analysis.to_csv(
    cleaned_folder / "root_cause_product_analysis.csv",
    index=False
)

findings_df.to_csv(
    cleaned_folder / "root_cause_findings.csv",
    index=False
)



print("\nGROWTH360 ROOT-CAUSE DETECTIVE REPORT")
print("------------------------------------")

print("\nPRODUCT PERFORMANCE:")
print(product_analysis.to_string(index=False))

print("\nBUSINESS FINDINGS:")
print(findings_df.to_string(index=False))

print("\nRoot-Cause Detective completed successfully!")
print("Results saved in:", cleaned_folder)
