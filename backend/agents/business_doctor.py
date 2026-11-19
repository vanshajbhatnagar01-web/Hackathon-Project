
import pandas as pd
from pathlib import Path


backend_folder = Path(__file__).resolve().parent.parent
cleaned_folder = backend_folder / "data" / "cleaned"

print("Growth360 Business Doctor started!\n")



sentiment_report = pd.read_csv(
    cleaned_folder / "review_agent_sentiment_summary.csv"
)

theme_report = pd.read_csv(
    cleaned_folder / "review_agent_theme_report.csv"
)

complaint_products = pd.read_csv(
    cleaned_folder / "review_agent_product_complaints.csv"
)

sales_products = pd.read_csv(
    cleaned_folder / "demand_agent_product_report.csv"
)

hourly_sales = pd.read_csv(
    cleaned_folder / "demand_agent_hourly_report.csv"
)

business_health = pd.read_csv(
    cleaned_folder / "business_health_score.csv"
)


print("Reports from Review and Demand Agents loaded!\n")



total_reviews = sentiment_report["count"].sum()

negative_reviews = sentiment_report.loc[
    sentiment_report["sentiment"] == "Negative",
    "count"
].sum()

negative_percentage = (negative_reviews / total_reviews) * 100



theme_report = theme_report.sort_values(
    "review_count",
    ascending=False
)

top_complaint = theme_report.iloc[0]["complaint_theme"]
top_complaint_count = theme_report.iloc[0]["review_count"]



complaint_products = complaint_products.sort_values(
    "negative_review_count",
    ascending=False
)

worst_product = complaint_products.iloc[0]["product"]
worst_product_count = complaint_products.iloc[0]["negative_review_count"]



sales_products = sales_products.sort_values(
    "total_revenue",
    ascending=False
)

top_revenue_product = sales_products.iloc[0]["product"]
top_revenue = sales_products.iloc[0]["total_revenue"]



hourly_sales = hourly_sales.sort_values(
    "total_revenue",
    ascending=False
)

busiest_hour = hourly_sales.iloc[0]["hour"]
busiest_hour_revenue = hourly_sales.iloc[0]["total_revenue"]



health_score = business_health.iloc[0]["health_score"]
health_status = business_health.iloc[0]["health_status"]



print("BUSINESS PERFORMANCE SUMMARY")
print("------------------------")
print(f"Business Health Score: {health_score}/100")
print(f"Business Status: {health_status}")
print(f"Negative Reviews: {negative_percentage:.2f}%")
print(f"Top Complaint: {top_complaint} ({top_complaint_count} mentions)")
print(f"Most Complained Product: {worst_product} ({worst_product_count} reviews)")
print(f"Top Revenue Product: {top_revenue_product}")
print(f"Top Product Revenue: Rs. {top_revenue:,.2f}")
print(f"Busiest Hour: {busiest_hour}:00")
print(f"Peak Hour Revenue: Rs. {busiest_hour_revenue:,.2f}")



diagnoses = []



if negative_percentage >= 15:

    diagnoses.append({
        "area": "Customer Experience",
        "problem": "Noticeable negative customer feedback",
        "evidence": f"{negative_percentage:.2f}% of reviews are negative",
        "recommendation": (
            "Review recurring customer complaints and prioritize "
            "improvements to the customer experience."
        ),
        "priority": "High"
    })



if top_complaint == "Cleanliness":

    diagnoses.append({
        "area": "Operations",
        "problem": "Cleanliness is the most reported complaint",
        "evidence": f"{top_complaint_count} complaint mentions",
        "recommendation": (
            "Review cleaning routines, table turnover and "
            "cleanliness checks during busy periods."
        ),
        "priority": "High"
    })



if worst_product_count >= 10:

    diagnoses.append({
        "area": "Product Quality",
        "problem": f"{worst_product} receives the most negative feedback",
        "evidence": f"{worst_product_count} negative reviews",
        "recommendation": (
            f"Investigate the preparation, quality and presentation "
            f"of {worst_product}."
        ),
        "priority": "High"
    })



if busiest_hour_revenue > 0:

    diagnoses.append({
        "area": "Operations",
        "problem": "High sales activity during peak hour",
        "evidence": (
            f"{busiest_hour}:00 generated "
            f"Rs. {busiest_hour_revenue:,.2f}"
        ),
        "recommendation": (
            "Review staffing, preparation and cleaning arrangements "
            "before the peak sales hour."
        ),
        "priority": "Medium"
    })



if health_score < 65:

    diagnoses.append({
        "area": "Overall Business Health",
        "problem": "Business health score needs improvement",
        "evidence": f"Health score is {health_score}/100",
        "recommendation": (
            "Focus on weak business health categories and "
            "track improvements over time."
        ),
        "priority": "High"
    })



print("\nBUSINESS DOCTOR DIAGNOSIS")
print("------------------------")

for number, diagnosis in enumerate(diagnoses, start=1):

    print(f"\nDiagnosis {number}: {diagnosis['problem']}")
    print("Area:", diagnosis["area"])
    print("Evidence:", diagnosis["evidence"])
    print("Recommendation:", diagnosis["recommendation"])
    print("Priority:", diagnosis["priority"])



diagnosis_report = pd.DataFrame(diagnoses)

diagnosis_report.to_csv(
    cleaned_folder / "business_doctor_diagnosis.csv",
    index=False
)


print("\nBusiness Doctor completed successfully!")
print("Diagnosis saved to business_doctor_diagnosis.csv")
