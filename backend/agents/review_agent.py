
import pandas as pd
from pathlib import Path

# Find the Growth360 project folders
backend_folder = Path(__file__).resolve().parent.parent
cleaned_folder = backend_folder / "data" / "cleaned"

# Load the reviews and their predicted sentiments
reviews = pd.read_csv(cleaned_folder / "reviews_with_sentiment.csv")

print("Growth360 Review Agent started!")
print("Customer reviews loaded successfully.\n")


# 1. Check overall customer sentiment
sentiment_counts = reviews["predicted_sentiment"].value_counts()

total_reviews = len(reviews)
negative_reviews = sentiment_counts.get("Negative", 0)
positive_reviews = sentiment_counts.get("Positive", 0)
neutral_reviews = sentiment_counts.get("Neutral", 0)

negative_percentage = (negative_reviews / total_reviews) * 100

print("CUSTOMER SENTIMENT SUMMARY")
print("-----------------------")
print("Total reviews:", total_reviews)
print("Positive reviews:", positive_reviews)
print("Neutral reviews:", neutral_reviews)
print("Negative reviews:", negative_reviews)
print(f"Negative review percentage: {negative_percentage:.2f}%\n")


# 2. Find products receiving negative reviews
negative_feedback = reviews[
    reviews["predicted_sentiment"] == "Negative"
]

product_complaints = (
    negative_feedback.groupby("product")
    .size()
    .sort_values(ascending=False)
)

print("PRODUCTS WITH MOST NEGATIVE REVIEWS")
print("----------------------------------")
print(product_complaints.head(5))


# 3. Find common customer complaint themes
complaint_themes = {
    "Food Quality": [
        "cold", "tasteless", "stale", "raw",
        "burnt", "undercooked", "overcooked"
    ],
    "Service": [
        "rude", "staff", "waiter", "service",
        "unfriendly", "behavior"
    ],
    "Waiting Time": [
        "wait", "slow", "delay", "late",
        "waiting", "long time"
    ],
    "Price": [
        "expensive", "price", "cost", "overpriced",
        "cheap", "value"
    ],
    "Cleanliness": [
        "dirty", "hygiene", "clean", "messy",
        "unclean"
    ]
}

theme_counts = {}

# Check each negative review for complaint keywords
for theme, keywords in complaint_themes.items():

    count = 0

    for review_text in negative_feedback["review_text"].dropna():

        review_text = str(review_text).lower()

        # Count a review only once per theme
        if any(keyword in review_text for keyword in keywords):
            count += 1

    theme_counts[theme] = count


# Sort themes from most common to least common
theme_results = pd.Series(theme_counts).sort_values(ascending=False)

print("\nCUSTOMER COMPLAINT THEMES")
print("------------------------")
print(theme_results)


# 4. Collect examples of negative customer reviews
print("\nEXAMPLE NEGATIVE REVIEWS")
print("-----------------------")

example_reviews = negative_feedback["review_text"].dropna().head(5)

for review_number, review_text in enumerate(example_reviews, start=1):
    print(f"{review_number}. {review_text}")


# 5. Create simple business insights
insights = []

# Check overall negative feedback
if negative_percentage >= 30:
    insights.append(
        "High negative feedback detected. "
        "Customer experience needs attention."
    )

elif negative_percentage >= 15:
    insights.append(
        "Negative feedback is noticeable. "
        "Review customer complaints carefully."
    )

else:
    insights.append(
        "Overall negative feedback is relatively low."
    )


# Find the most complained-about product
if not product_complaints.empty:

    worst_product = product_complaints.index[0]
    worst_product_count = product_complaints.iloc[0]

    insights.append(
        f"{worst_product} received the most negative reviews "
        f"({worst_product_count} reviews)."
    )


# Find the most common complaint theme
if not theme_results.empty and theme_results.iloc[0] > 0:

    most_common_theme = theme_results.index[0]
    theme_count = theme_results.iloc[0]

    insights.append(
        f"{most_common_theme} is the most frequently "
        f"mentioned complaint theme ({theme_count} reviews)."
    )


print("\nREVIEW AGENT INSIGHTS")
print("--------------------")

for insight in insights:
    print("-", insight)


# 6. Save the agent's results
review_summary = pd.DataFrame({
    "sentiment": ["Positive", "Neutral", "Negative"],
    "count": [
        positive_reviews,
        neutral_reviews,
        negative_reviews
    ]
})

theme_report = pd.DataFrame({
    "complaint_theme": theme_results.index,
    "review_count": theme_results.values
})

product_report = product_complaints.reset_index()
product_report.columns = ["product", "negative_review_count"]


review_summary.to_csv(
    cleaned_folder / "review_agent_sentiment_summary.csv",
    index=False
)

theme_report.to_csv(
    cleaned_folder / "review_agent_theme_report.csv",
    index=False
)

product_report.to_csv(
    cleaned_folder / "review_agent_product_complaints.csv",
    index=False
)


insight_report = pd.DataFrame({
    "insight": insights
})

insight_report.to_csv(
    cleaned_folder / "review_agent_insights.csv",
    index=False
)

print("\nReview Agent completed successfully!")
print("All reports saved in the cleaned data folder.")
