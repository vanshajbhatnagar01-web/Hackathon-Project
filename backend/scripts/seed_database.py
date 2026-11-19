import os
import sys
from datetime import datetime
import pandas as pd

# Allow running this script directly from backend/ (e.g., python scripts/seed_database.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal, engine, Base
from app.models import (
    Business,
    Product,
    CustomerReview,
    SalesRecord,
    BusinessHealthScore,
    DemandForecast,
    BusinessInsight,
    ActionDecision,
)

DATA_DIR = os.path.join(BASE_DIR, "data")
CLEANED_DIR = os.path.join(DATA_DIR, "cleaned")


def parse_date(val):
    """Safely converts CSV date strings into Python date objects."""
    if pd.isna(val) or str(val).strip() == "":
        return None
    return pd.to_datetime(str(val).strip()).date()


def clean_str(val, default=None):
    """Converts NaN/None values cleanly into Python strings or default."""
    if pd.isna(val):
        return default
    text_val = str(val).strip()
    return text_val if text_val else default


def clean_float(val, default=0.0):
    """Safely converts numeric CSV fields into floats."""
    if pd.isna(val):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def clean_int(val, default=0):
    """Safely converts numeric CSV fields into integers."""
    if pd.isna(val):
        return default
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


def seed_all(reset: bool = False):
    """Imports all Cafe Nova CSV datasets and ML outputs into MySQL."""
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if reset:
            print("Resetting existing database tables...")
            db.query(ActionDecision).delete()
            db.query(BusinessInsight).delete()
            db.query(DemandForecast).delete()
            db.query(BusinessHealthScore).delete()
            db.query(SalesRecord).delete()
            db.query(CustomerReview).delete()
            db.query(Product).delete()
            db.query(Business).delete()
            db.commit()

        # Check if already seeded
        existing_business = db.query(Business).first()
        if existing_business and not reset:
            print(
                f"Database already seeded with '{existing_business.business_name}' "
                f"(ID: {existing_business.business_id}). Run with --reset to re-import."
            )
            return

        # ------------------------------------------------------------------
        # 1. SEED BUSINESS PROFILE
        # ------------------------------------------------------------------
        profile_path = os.path.join(CLEANED_DIR, "cleaned_business_profile.csv")
        if not os.path.exists(profile_path):
            profile_path = os.path.join(DATA_DIR, "cafe_nova_business_profile.csv")

        profile_df = pd.read_csv(profile_path)
        row = profile_df.iloc[0]
        business_id = clean_str(row.get("business_id"), "CAFE_NOVA_001")

        business = Business(
            business_id=business_id,
            business_name=clean_str(row.get("business_name"), "Cafe Nova"),
            category=clean_str(row.get("category")),
            business_type=clean_str(row.get("business_type")),
            city=clean_str(row.get("city")),
            country=clean_str(row.get("country")),
            currency=clean_str(row.get("currency"), "INR"),
            average_order_value=clean_float(row.get("average_order_value")),
            opening_hours=clean_str(row.get("opening_hours")),
            operating_days=clean_str(row.get("operating_days")),
            monthly_marketing_budget=clean_float(row.get("monthly_marketing_budget")),
            seating_capacity=clean_int(row.get("seating_capacity")),
            number_of_employees=clean_int(row.get("number_of_employees")),
            order_channels=clean_str(row.get("order_channels")),
            primary_customer_group=clean_str(row.get("primary_customer_group")),
            business_goals=clean_str(row.get("business_goals")),
            data_type=clean_str(row.get("data_type")),
        )
        db.add(business)
        db.commit()
        print(f"[1/7] Seeded Business: {business.business_name} ({business_id})")

        # ------------------------------------------------------------------
        # 2. SEED PRODUCTS (from product_comparison.csv)
        # ------------------------------------------------------------------
        product_map = {}  # Maps product_name (lowercase) -> Product.id
        product_comp_path = os.path.join(CLEANED_DIR, "product_comparison.csv")
        if os.path.exists(product_comp_path):
            prod_df = pd.read_csv(product_comp_path)
            for _, p_row in prod_df.iterrows():
                p_name = clean_str(p_row.get("product"))
                if not p_name:
                    continue
                product = Product(
                    business_id=business_id,
                    product_name=p_name,
                    average_rating=clean_float(p_row.get("average_rating")),
                    total_reviews=clean_int(p_row.get("total_reviews")),
                    total_sales=clean_float(p_row.get("total_sales")),
                    total_quantity=clean_int(p_row.get("total_quantity")),
                )
                db.add(product)
                db.flush()  # Get generated product.id immediately
                product_map[p_name.lower()] = product.id
            db.commit()
        print(f"[2/7] Seeded Products: {len(product_map)} items")

        def get_or_create_product_id(prod_name: str):
            if not prod_name:
                return None
            key = prod_name.strip().lower()
            if key in product_map:
                return product_map[key]
            new_prod = Product(business_id=business_id, product_name=prod_name.strip())
            db.add(new_prod)
            db.flush()
            product_map[key] = new_prod.id
            return new_prod.id

        # ------------------------------------------------------------------
        # 3. SEED CUSTOMER REVIEWS (from reviews_with_sentiment.csv)
        # ------------------------------------------------------------------
        reviews_path = os.path.join(CLEANED_DIR, "reviews_with_sentiment.csv")
        if not os.path.exists(reviews_path):
            reviews_path = os.path.join(CLEANED_DIR, "cleaned_reviews.csv")

        reviews_df = pd.read_csv(reviews_path)
        review_objects = []
        for idx, r_row in reviews_df.iterrows():
            prod_name = clean_str(r_row.get("product"))
            prod_id = get_or_create_product_id(prod_name)
            rev_id = clean_str(r_row.get("review_id"), f"REV_{idx + 1}")

            review_objects.append(
                CustomerReview(
                    review_id=rev_id,
                    business_id=business_id,
                    product_id=prod_id,
                    date=parse_date(r_row.get("date")),
                    rating=clean_float(r_row.get("rating"), 0.0),
                    review_text=clean_str(r_row.get("review_text"), ""),
                    cleaned_text=clean_str(r_row.get("cleaned_text")),
                    product=prod_name,
                    sentiment=clean_str(r_row.get("sentiment")),
                    predicted_sentiment=clean_str(r_row.get("predicted_sentiment")),
                    confidence=clean_float(r_row.get("confidence"), None),
                )
            )
        db.bulk_save_objects(review_objects)
        db.commit()
        print(f"[3/7] Seeded Customer Reviews: {len(review_objects)} records")

        # ------------------------------------------------------------------
        # 4. SEED SALES RECORDS (from cleaned_sales.csv)
        # ------------------------------------------------------------------
        sales_path = os.path.join(CLEANED_DIR, "cleaned_sales.csv")
        if not os.path.exists(sales_path):
            sales_path = os.path.join(DATA_DIR, "cafe_nova_90_days_sales.csv")

        sales_df = pd.read_csv(sales_path)
        sales_objects = []
        for _, s_row in sales_df.iterrows():
            prod_name = clean_str(s_row.get("product"), "Unknown")
            prod_id = get_or_create_product_id(prod_name)
            sales_objects.append(
                SalesRecord(
                    business_id=business_id,
                    product_id=prod_id,
                    date=parse_date(s_row.get("date")),
                    hour=clean_int(s_row.get("hour"), 0),
                    product=prod_name,
                    quantity_sold=clean_int(s_row.get("quantity_sold"), 0),
                    revenue=clean_float(s_row.get("revenue"), 0.0),
                )
            )
        db.bulk_save_objects(sales_objects)
        db.commit()
        print(f"[4/7] Seeded Sales Records: {len(sales_objects)} records")

        # ------------------------------------------------------------------
        # 5. SEED BUSINESS HEALTH SCORE & BREAKDOWN
        # ------------------------------------------------------------------
        health_path = os.path.join(CLEANED_DIR, "business_health_score.csv")
        breakdown_path = os.path.join(CLEANED_DIR, "business_health_breakdown.csv")

        if os.path.exists(health_path):
            h_df = pd.read_csv(health_path)
            h_row = h_df.iloc[0]

            breakdown_scores = {}
            if os.path.exists(breakdown_path):
                b_df = pd.read_csv(breakdown_path)
                for _, b_row in b_df.iterrows():
                    cat = clean_str(b_row.get("category"), "").lower()
                    breakdown_scores[cat] = clean_float(b_row.get("score"))

            # Match breakdown categories flexibly
            sales_sc = next(
                (v for k, v in breakdown_scores.items() if "sale" in k or "rev" in k),
                None,
            )
            sent_sc = next(
                (v for k, v in breakdown_scores.items() if "sent" in k or "review" in k),
                None,
            )
            prod_sc = next(
                (v for k, v in breakdown_scores.items() if "prod" in k), None
            )
            ops_sc = next(
                (v for k, v in breakdown_scores.items() if "oper" in k or "stab" in k),
                None,
            )

            health_record = BusinessHealthScore(
                business_id=business_id,
                health_score=clean_float(h_row.get("health_score")),
                health_status=clean_str(h_row.get("health_status"), "Moderate"),
                average_rating=clean_float(h_row.get("average_rating")),
                revenue_growth_percent=clean_float(h_row.get("revenue_growth_percent")),
                quantity_growth_percent=clean_float(
                    h_row.get("quantity_growth_percent")
                ),
                sales_score=sales_sc,
                sentiment_score=sent_sc,
                product_score=prod_sc,
                operations_score=ops_sc,
            )
            db.add(health_record)
            db.commit()
            print(
                f"[5/7] Seeded Business Health Score: {health_record.health_score} "
                f"({health_record.health_status})"
            )

        # ------------------------------------------------------------------
        # 6. SEED 7-DAY DEMAND FORECASTS
        # ------------------------------------------------------------------
        forecast_path = os.path.join(CLEANED_DIR, "seven_day_demand_forecast.csv")
        forecast_count = 0
        if os.path.exists(forecast_path):
            f_df = pd.read_csv(forecast_path)
            for _, f_row in f_df.iterrows():
                forecast = DemandForecast(
                    business_id=business_id,
                    forecast_date=parse_date(f_row.get("date")),
                    predicted_revenue=clean_float(f_row.get("predicted_revenue")),
                    predicted_quantity=clean_float(f_row.get("predicted_quantity")),
                    model_name="LinearRegression / TimeSeries",
                )
                db.add(forecast)
                forecast_count += 1
            db.commit()
        print(f"[6/7] Seeded Demand Forecasts: {forecast_count} days")

        # ------------------------------------------------------------------
        # 7. SEED BUSINESS INSIGHTS & ACTION DECISIONS
        # ------------------------------------------------------------------
        insights_created = 0

        def add_insight_with_decision(
            source_type,
            title,
            recommendation,
            evidence=None,
            category_or_product=None,
            priority="Medium",
            target_audience=None,
            recommended_channel=None,
            recommended_timing=None,
            initial_status="pending",
        ):
            nonlocal insights_created
            insight = BusinessInsight(
                business_id=business_id,
                source_type=source_type,
                category_or_product=category_or_product,
                title=title[:255],
                evidence=evidence,
                recommendation=recommendation,
                priority=priority,
                target_audience=target_audience,
                recommended_channel=recommended_channel,
                recommended_timing=recommended_timing,
            )
            db.add(insight)
            db.flush()  # Get insight.id for ActionDecision

            decision = ActionDecision(
                business_id=business_id,
                insight_id=insight.id,
                decision_status=initial_status,
            )
            db.add(decision)
            insights_created += 1

        # 7a. Root-Cause Findings
        rc_path = os.path.join(CLEANED_DIR, "root_cause_findings.csv")
        if os.path.exists(rc_path):
            rc_df = pd.read_csv(rc_path)
            for _, r in rc_df.iterrows():
                f_type = clean_str(r.get("finding_type"), "Root Cause")
                prod = clean_str(r.get("product"), "General")
                add_insight_with_decision(
                    source_type="root_cause",
                    category_or_product=prod,
                    title=f"{f_type} — {prod}",
                    evidence=clean_str(r.get("evidence")),
                    recommendation=clean_str(r.get("recommendation"), ""),
                    priority=clean_str(r.get("priority"), "High"),
                )

        # 7b. Business Doctor Diagnosis
        doc_path = os.path.join(CLEANED_DIR, "business_doctor_diagnosis.csv")
        if os.path.exists(doc_path):
            doc_df = pd.read_csv(doc_path)
            for _, r in doc_df.iterrows():
                area = clean_str(r.get("area"), "Operations")
                problem = clean_str(r.get("problem"), "Diagnostic Issue")
                add_insight_with_decision(
                    source_type="doctor_diagnosis",
                    category_or_product=area,
                    title=f"[{area}] {problem}",
                    evidence=clean_str(r.get("evidence")),
                    recommendation=clean_str(r.get("recommendation"), ""),
                    priority=clean_str(r.get("priority"), "High"),
                )

        # 7c. Marketing Agent Campaigns
        mkt_path = os.path.join(CLEANED_DIR, "marketing_agent_campaigns.csv")
        if os.path.exists(mkt_path):
            mkt_df = pd.read_csv(mkt_path)
            for _, r in mkt_df.iterrows():
                c_name = clean_str(r.get("campaign_name"), "Marketing Campaign")
                c_type = clean_str(r.get("campaign_type"), "Campaign")
                approval_raw = clean_str(r.get("owner_approval"), "pending").lower()
                if "approv" in approval_raw:
                    status = "approved"
                elif "reject" in approval_raw:
                    status = "rejected"
                else:
                    status = "pending"

                add_insight_with_decision(
                    source_type="marketing_campaign",
                    category_or_product=c_type,
                    title=c_name,
                    evidence=clean_str(r.get("reason")),
                    recommendation=clean_str(
                        r.get("marketing_message"),
                        clean_str(r.get("campaign_idea"), ""),
                    ),
                    priority=clean_str(r.get("priority"), "Medium"),
                    target_audience=clean_str(r.get("target_audience")),
                    recommended_channel=clean_str(r.get("recommended_channel")),
                    recommended_timing=clean_str(r.get("recommended_timing")),
                    initial_status=status,
                )

        # 7d. Demand & Review Agent Insights
        for fname, src in [
            ("demand_agent_insights.csv", "demand_insight"),
            ("review_agent_insights.csv", "review_insight"),
        ]:
            fpath = os.path.join(CLEANED_DIR, fname)
            if os.path.exists(fpath):
                df_ins = pd.read_csv(fpath)
                for idx, r in df_ins.iterrows():
                    text_ins = clean_str(r.get("insight"))
                    if text_ins:
                        add_insight_with_decision(
                            source_type=src,
                            category_or_product="AI Agent Summary",
                            title=f"{src.replace('_', ' ').title()} #{idx + 1}",
                            evidence=text_ins,
                            recommendation=text_ins,
                            priority="Medium",
                        )

        db.commit()
        print(
            f"[7/7] Seeded Business Insights & Action Decisions: {insights_created} items"
        )
        print("\nDatabase seeding completed successfully!")

    except Exception as exc:
        db.rollback()
        print(f"Error during seeding: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_all(reset=reset_flag)