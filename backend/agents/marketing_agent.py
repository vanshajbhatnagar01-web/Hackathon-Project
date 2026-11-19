


import pandas as pd
from pathlib import Path



data_folder = Path("backend/data/cleaned")

product_report_path = data_folder / "demand_agent_product_report.csv"
complaints_path = data_folder / "review_agent_product_complaints.csv"
diagnosis_path = data_folder / "business_doctor_diagnosis.csv"
hourly_report_path = data_folder / "demand_agent_hourly_report.csv"

output_path = data_folder / "marketing_agent_campaigns.csv"




product_report = pd.read_csv(product_report_path)
complaints_report = pd.read_csv(complaints_path)
diagnosis_report = pd.read_csv(diagnosis_path)
hourly_report = pd.read_csv(hourly_report_path)

print("Growth360 Marketing Agent started!")
print("Reports from other agents loaded!")



top_product = product_report.sort_values(
    "total_revenue", ascending=False
).iloc[0]

top_product_name = top_product["product"]
top_product_revenue = top_product["total_revenue"]


worst_product = complaints_report.sort_values(
    "negative_review_count", ascending=False
).iloc[0]

worst_product_name = worst_product["product"]
worst_product_complaints = worst_product["negative_review_count"]


busiest_hour = hourly_report.sort_values(
    "total_revenue", ascending=False
).iloc[0]

peak_hour = int(busiest_hour["hour"])
peak_hour_revenue = busiest_hour["total_revenue"]


diagnosis_text = diagnosis_report.to_string(index=False).lower()




campaigns = []


campaigns.append({
    "campaign_name": f"{top_product_name} Spotlight",
    "campaign_type": "Product Promotion",
    "target_audience": "Existing customers and cafe visitors",
    "campaign_idea": f"Feature {top_product_name} as a cafe bestseller.",
    "marketing_message": (
        f"Your cafe favourite is here! Try our "
        f"{top_product_name} on your next visit."
    ),
    "recommended_channel": "Instagram, WhatsApp and in-store menu",
    "recommended_timing": "Throughout the week",
    "reason": (
        f"{top_product_name} generated Rs. "
        f"{top_product_revenue:,.2f} in sales."
    ),
    "priority": "High",
    "owner_approval": "Required"
})



campaigns.append({
    "campaign_name": "Cafe Happy Hours",
    "campaign_type": "Time-Based Promotion",
    "target_audience": "Customers visiting during quieter hours",
    "campaign_idea": (
        "Offer an optional combo or small perk during "
        "off-peak hours to encourage visits."
    ),
    "marketing_message": (
        "Take a little coffee break! Discover your favourite "
        "cafe treats during our relaxed hours."
    ),
    "recommended_channel": "Instagram Stories and in-store posters",
    "recommended_timing": "Before and during quieter hours",
    "reason": (
        f"Peak sales happen around {peak_hour}:00, "
        f"with Rs. {peak_hour_revenue:,.2f} in recorded sales. "
        "This campaign aims to attract customers outside peak hours."
    ),
    "priority": "Medium",
    "owner_approval": "Required"
})



campaigns.append({
    "campaign_name": "Come Back for Another Cup",
    "campaign_type": "Customer Retention",
    "target_audience": "Existing and repeat customers",
    "campaign_idea": (
        "Introduce a simple loyalty card or a return-visit reward "
        "for customers, subject to owner approval."
    ),
    "marketing_message": (
        "Your next favourite coffee is waiting! Visit us again "
        "and enjoy a little something on your journey to becoming "
        "a regular."
    ),
    "recommended_channel": "WhatsApp and printed loyalty cards",
    "recommended_timing": "Ongoing",
    "reason": (
        "A retention campaign can encourage repeat visits "
        "without relying only on new customer acquisition."
    ),
    "priority": "Medium",
    "owner_approval": "Required"
})



campaigns.append({
    "campaign_name": f"{worst_product_name} Quality First",
    "campaign_type": "Product Improvement",
    "target_audience": "Existing customers who order this product",
    "campaign_idea": (
        f"Review and improve {worst_product_name} preparation, "
        "quality and presentation before launching a promotion."
    ),
    "marketing_message": (
        "We're working to make your favourites even better. "
        "Your feedback helps us improve every visit."
    ),
    "recommended_channel": "In-store feedback and staff communication",
    "recommended_timing": "After the product improvement review",
    "reason": (
        f"{worst_product_name} received "
        f"{worst_product_complaints} negative reviews. "
        "Promoting it aggressively before addressing feedback "
        "may be a poor choice."
    ),
    "priority": "High",
    "owner_approval": "Required"
})



if "cleanliness" in diagnosis_text:

    campaigns.append({
        "campaign_name": "Clean Cafe, Happy Customers",
        "campaign_type": "Customer Experience",
        "target_audience": "All cafe customers",
        "campaign_idea": (
            "Improve visible cleaning routines and table checks. "
            "Communicate improvements only after they are implemented."
        ),
        "marketing_message": (
            "We care about your comfort. We're making every visit "
            "welcoming and enjoyable."
        ),
        "recommended_channel": "In-store signage and social media",
        "recommended_timing": "After cleaning improvements are in place",
        "reason": (
            "Cleanliness was highlighted by the Business Doctor "
            "as a recurring customer complaint."
        ),
        "priority": "High",
        "owner_approval": "Required"
    })




campaigns_df = pd.DataFrame(campaigns)




campaigns_df.to_csv(output_path, index=False)



print("\nMARKETING CAMPAIGNS")
print("-------------------")

for index, campaign in campaigns_df.iterrows():

    print(f"\nCampaign {index + 1}: {campaign['campaign_name']}")
    print("Type:", campaign["campaign_type"])
    print("Target:", campaign["target_audience"])
    print("Idea:", campaign["campaign_idea"])
    print("Message:", campaign["marketing_message"])
    print("Channel:", campaign["recommended_channel"])
    print("Timing:", campaign["recommended_timing"])
    print("Reason:", campaign["reason"])
    print("Priority:", campaign["priority"])

print("\nMarketing Agent completed successfully!")
print("Campaign report saved to marketing_agent_campaigns.csv")
