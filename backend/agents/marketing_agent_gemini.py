
import sys
import json
from pathlib import Path
import pandas as pd



BACKEND_FOLDER = Path(__file__).resolve().parents[1]
PROJECT_FOLDER = BACKEND_FOLDER.parent
DATA_FOLDER = BACKEND_FOLDER / "data" / "cleaned"

sys.path.insert(0, str(BACKEND_FOLDER))

from gemini_client import ask_gemini




def read_csv_report(file_name, report_name, max_rows=8):
    """
    Read a CSV report and convert it into readable text.
    """

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




def collect_marketing_evidence(
    shared_evidence=None,
    business_doctor_report=None
):
    """
    Collect evidence from LangGraph shared state.

    When run independently, use the existing CSV
    and Markdown reports as a fallback.
    """

   
    if shared_evidence is not None:

        evidence = {
            "Business Reports": shared_evidence
        }

        # Include existing rule-based campaign ideas
        existing_campaigns = read_csv_report(
            "marketing_agent_campaigns.csv",
            "Existing Marketing Campaigns"
        )

        evidence["Existing Marketing Campaigns"] = (
            existing_campaigns
        )

       
        evidence["Gemini Business Doctor Diagnosis"] = (
            business_doctor_report
            if business_doctor_report
            else "Business Doctor diagnosis was not provided."
        )

        return json.dumps(
            evidence,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    

    reports = [
        ("marketing_agent_campaigns.csv", "Existing Marketing Campaigns"),
        ("cleaned_business_profile.csv", "Business Profile"),
        ("demand_agent_product_report.csv", "Product Sales"),
        ("review_agent_product_complaints.csv", "Product Complaints"),
        ("review_agent_theme_report.csv", "Customer Complaint Themes")
    ]

    evidence = []

    for file_name, report_name in reports:

        report = read_csv_report(
            file_name,
            report_name
        )

        evidence.append(report)

   
    doctor_file = (
        DATA_FOLDER / "business_doctor_gemini_report.md"
    )

    if doctor_file.exists():

        doctor_report = doctor_file.read_text(
            encoding="utf-8"
        )

    else:

        doctor_report = (
            "Gemini Business Doctor report was not found."
        )

    evidence.append(
        "GEMINI BUSINESS DOCTOR FINDINGS:\n" + doctor_report
    )

    return "\n\n".join(evidence)




def generate_marketing_campaigns(
    shared_evidence=None,
    business_doctor_report=None,
    marketing_strategy=None
):
    """
    Generate marketing campaigns using Gemini.

    LangGraph can directly pass the business evidence
    and Gemini Business Doctor diagnosis.
    """

    print("\nCollecting Growth360 marketing evidence...")
    

    business_evidence = collect_marketing_evidence(
        shared_evidence,
        business_doctor_report
    )
    if not marketing_strategy:
        marketing_strategy = "BALANCED GROWTH"

    print("\nSelected Marketing Strategy:", marketing_strategy)

    if shared_evidence is not None:
        print("Business evidence received from LangGraph.")

    if business_doctor_report:
        print("Gemini Business Doctor diagnosis received directly.")

    prompt = f"""
You are the Marketing Agent inside Growth360.
The LangGraph orchestrator has selected this marketing strategy:

{marketing_strategy}

Follow this strategy while preparing your campaigns:

- IMPROVEMENT FIRST:
  Prioritize resolving operational and customer experience
  problems. Only recommend promotions that do not conflict
  with unresolved quality or service issues.

- GROWTH FIRST:
  Prioritize evidence-supported growth opportunities while
  maintaining customer experience and product quality safeguards.

- OWNER REVIEW REQUIRED:
  Prepare cautious recommendations and clearly mark them
  as pending owner review. Do not assume missing business
  information is favourable.

Growth360 is an AI business assistant for small local businesses.

You are working together with another AI agent called
Gemini Business Doctor.

The Business Doctor has already analysed the cafe's
customer reviews, sales performance and business health.

Your responsibility is to use its actual diagnosis
to create relevant marketing campaigns.

Business: Cafe Nova
Location: India

IMPORTANT RULES:

1. Use only the supplied business evidence.
2. Give special importance to the Gemini Business Doctor diagnosis.
3. Connect every important campaign recommendation
   to an actual business finding.
4. Do not invent business performance numbers.
5. Do not guarantee sales growth or customer results.
6. Use the actual marketing budget only if it is present
   in the business profile.
7. Never exceed the stated marketing budget.
8. Clearly label proposed spending as an estimate.
9. Do not invent discount amounts or promotional prices.
10. Discounts, spending and campaign publishing require
    approval from the business owner.
11. Do not promote French Fries until its quality concerns
    have been investigated and addressed.
12. Do not advertise cleanliness improvements as completed
    unless the business owner has verified them.
13. Keep campaigns realistic for a small local cafe.
14. Distinguish operational improvement tasks from
    customer-facing marketing campaigns.
15. Do not claim that any campaign has already been launched.
16. Do not invent marketing performance metrics.

Create 3 to 4 useful campaign plans.

Use this structure for every campaign:

## Campaign Name

**Status:** Ready to plan / Hold until improvements are verified

**Objective:** What business goal does it support?

**Target Audience:** Which customers should it reach?

**Supporting Evidence:** Which Growth360 findings support it?

**Marketing Channel:** Instagram, WhatsApp, local promotion,
in-store promotion or another suitable channel.

**Campaign Message:** Write an attractive customer-facing
message in simple language.

**Execution Steps:** Explain how a small cafe can run it.

**Budget:** Use the actual budget only if the profile provides it.
Clearly mark any proposed spending as an estimate.

**Success Measurement:** Give measurable KPIs such as
customer visits, repeat visits, engagement or product sales.

**Owner Approval:** Mention decisions requiring approval.

After the campaigns, include:

# MARKETING AGENT SUMMARY

1. Best campaign to start with.
2. Campaigns that should wait for operational improvements.
3. Important precautions for the cafe owner.
4. How Growth360 can measure campaign performance.

These reports are based on synthetic demonstration data.
Do not describe them as verified real-world records.

GROWTH360 BUSINESS EVIDENCE:

{business_evidence}
"""

    print("\nSending marketing evidence to Gemini...")

    
    response = ask_gemini(prompt)

    if not response:
        raise ValueError(
            "Gemini returned an empty marketing response."
        )

    if "could not respond right now" in response.lower():
        raise RuntimeError(
            "Gemini is temporarily unavailable."
        )

   
    output_file = (
        DATA_FOLDER / "marketing_agent_gemini_campaigns.md"
    )

    output_file.write_text(
        response,
        encoding="utf-8"
    )

    print("\n" + "=" * 55)
    print("GROWTH360 GEMINI MARKETING AGENT")
    print("=" * 55)

    print(response)

    print("\n" + "=" * 55)
    print("Marketing Agent completed successfully!")
    print(f"Report saved at: {output_file}")
    print("=" * 55)

    # Return generated report to LangGraph
    return response




if __name__ == "__main__":

    try:
        generate_marketing_campaigns()

    except Exception as error:

        print("\nGemini Marketing Agent could not complete.")
        print("Error:", error)

        sys.exit(1)
