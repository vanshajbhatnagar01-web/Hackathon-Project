
import sys
import json
from pathlib import Path
import pandas as pd



BACKEND_FOLDER = Path(__file__).resolve().parents[1]
PROJECT_FOLDER = BACKEND_FOLDER.parent
DATA_FOLDER = BACKEND_FOLDER / "data" / "cleaned"

sys.path.insert(0, str(BACKEND_FOLDER))

from gemini_client import ask_gemini




def read_report(file_name, report_name, max_rows=6):

    file_path = DATA_FOLDER / file_name

    if not file_path.exists():
        return f"{report_name}: Report not found."

    try:
        data = pd.read_csv(file_path)

        if data.empty:
            return f"{report_name}: Report is empty."

        return (
            f"{report_name}:\n"
            f"{data.head(max_rows).to_string(index=False)}"
        )

    except Exception as error:
        return f"{report_name}: Could not read report. {error}"




def collect_business_evidence(shared_evidence=None):
    """
    Collect business evidence.

    When called through LangGraph, use the evidence
    passed through shared state.

    When run independently, read the existing CSV reports.
    """

   
    if shared_evidence is not None:

        return json.dumps(
            shared_evidence,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    
    reports = [
        ("business_health_score.csv", "Business Health Score"),
        ("business_health_breakdown.csv", "Health Score Breakdown"),
        ("business_doctor_diagnosis.csv", "Business Diagnosis"),

        ("review_agent_sentiment_summary.csv", "Customer Sentiment"),
        ("review_agent_theme_report.csv", "Customer Complaint Themes"),
        ("review_agent_product_complaints.csv", "Product Complaints"),

        ("demand_agent_product_report.csv", "Product Sales"),
        ("demand_agent_hourly_report.csv", "Hourly Sales"),

        ("seven_day_demand_forecast.csv", "Seven-Day Forecast"),
        ("root_cause_findings.csv", "Root Cause Findings")
    ]

    evidence = []

    for file_name, report_name in reports:

        report_text = read_report(
            file_name,
            report_name
        )

        evidence.append(report_text)

    return "\n\n".join(evidence)



def generate_business_diagnosis(shared_evidence=None):

    print("\nCollecting Growth360 business evidence...")

    business_evidence = collect_business_evidence(
        shared_evidence
    )

    if shared_evidence is not None:
        print("Evidence received from LangGraph shared state.")
    else:
        print("Evidence collected from CSV reports.")

    prompt = f"""
You are the Business Doctor Agent inside Growth360.

Growth360 is an AI business assistant designed to help
small local businesses improve their performance.

You are analysing Cafe Nova, a demonstration cafe.

Your task is to study the business evidence and prepare
a useful business diagnosis for the cafe owner.

IMPORTANT RULES:

1. Use only the information provided in the reports.
2. Do not invent numbers, facts or business problems.
3. Clearly distinguish observations from possible explanations.
4. Do not claim that correlation proves causation.
5. Do not present a possible explanation as a confirmed root cause.
6. Consider customer reviews, sales, products and business health together.
7. Make recommendations realistic for a small local cafe.
8. Do not recommend promoting a poorly rated product before
   investigating its quality concerns.
9. Any spending, discounts, price changes or marketing campaigns
   require approval from the business owner.
10. Explain your findings in simple language.

Prepare the report using this structure:

# GROWTH360 BUSINESS DOCTOR REPORT

## 1. Overall Business Condition
Explain the current business condition using the available evidence.

## 2. Major Business Problems
Identify the most important problems.
Explain the supporting evidence for each problem.

## 3. Customer Experience Analysis
Explain the main customer complaints and sentiment patterns.

## 4. Sales and Demand Analysis
Explain the important sales trends, popular products and busy hours.

## 5. Root Cause Investigation
For each possible root cause:
- State the observation.
- Explain the supporting evidence.
- State what still needs to be checked.
Do not claim unproven causes.

## 6. Recommended Actions
Give 3 to 5 practical actions.
For each action mention:
- Priority: High, Medium or Low
- What the owner should do
- Why it is recommended
- How the owner can measure improvement

## 7. Final Advice to the Cafe Owner
Give a short, clear and encouraging conclusion.

Here is the business evidence received from Growth360:

{business_evidence}

Remember: These are synthetic demonstration datasets.
Do not describe them as verified real-world business records.
"""

    print("\nSending business evidence to Gemini...")

    
    response = ask_gemini(prompt)

    if not response:
        raise ValueError("Gemini returned an empty response.")

    if "could not respond right now" in response.lower():
        raise RuntimeError(
            "Gemini is temporarily unavailable. Please try again."
        )

   
    output_file = (
        DATA_FOLDER / "business_doctor_gemini_report.md"
    )

    output_file.write_text(
        response,
        encoding="utf-8"
    )

    print("\n" + "=" * 55)
    print("GROWTH360 GEMINI BUSINESS DOCTOR REPORT")
    print("=" * 55)

    print(response)

    print("\n" + "=" * 55)
    print("Gemini Business Doctor completed successfully!")
    print(f"Report saved at: {output_file}")
    print("=" * 55)

   
    return response




if __name__ == "__main__":

    try:
        generate_business_diagnosis()

    except Exception as error:

        print("\nGemini Business Doctor could not complete.")
        print("Error:", error)

        sys.exit(1)
