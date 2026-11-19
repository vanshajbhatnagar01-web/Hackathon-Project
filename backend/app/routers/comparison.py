import io
import json
import os
import urllib.request
from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Business

router = APIRouter(prefix="/comparison", tags=["Growth Comparison & Impact Tracker"])


class GrowthCycle(Base):
    __tablename__ = "growth_cycles"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(String(100), index=True)
    cycle_label = Column(String(120), default="30-Day Growth Cycle")
    status = Column(String(40), default="baseline_uploaded")

    baseline_filename = Column(String(255))
    baseline_uploaded_at = Column(DateTime, default=datetime.utcnow)
    baseline_date_range = Column(String(100))
    baseline_days = Column(Integer, default=0)
    baseline_validation_json = Column(Text)
    baseline_metrics_json = Column(Text)
    baseline_products_json = Column(Text)
    baseline_weekly_json = Column(Text)

    followup_filename = Column(String(255), nullable=True)
    followup_uploaded_at = Column(DateTime, nullable=True)
    followup_date_range = Column(String(100), nullable=True)
    followup_days = Column(Integer, default=0)
    followup_validation_json = Column(Text, nullable=True)
    followup_metrics_json = Column(Text, nullable=True)
    followup_products_json = Column(Text, nullable=True)
    followup_weekly_json = Column(Text, nullable=True)

    comparison_result_json = Column(Text, nullable=True)
    ai_report_text = Column(Text, nullable=True)


class GrowthActionTask(Base):
    __tablename__ = "growth_action_tasks"

    id = Column(Integer, primary_key=True, index=True)
    cycle_id = Column(Integer, index=True)
    business_id = Column(String(100), index=True)
    problem = Column(Text)
    evidence = Column(Text)
    root_cause = Column(Text)
    recommendation = Column(Text)
    implementation_steps = Column(Text)
    expected_outcome = Column(Text)
    status = Column(String(30), default="Pending")
    owner_notes = Column(Text, default="")
    completed_at = Column(String(50), nullable=True)


Base.metadata.create_all(bind=engine)


def get_active_business(db: Session, business_id: Optional[str]) -> Business:
    biz = None
    if business_id:
        biz = db.query(Business).filter(Business.business_id == business_id).first()
    if not biz:
        biz = db.query(Business).first()
    if not biz:
        raise HTTPException(
            status_code=400,
            detail="No active business profile found. Please complete initial setup first.",
        )
    return biz


COLUMN_ALIASES = {
    "date": ["date", "order_date", "timestamp", "day", "created_at", "txn_date"],
    "product": ["product", "item", "item_name", "product_name", "menu_item", "sku"],
    "revenue": ["revenue", "sales", "amount", "total", "total_sales", "price", "net_sales"],
    "quantity": ["quantity", "qty", "units", "quantity_sold", "count", "orders"],
    "rating": ["rating", "stars", "score", "customer_rating", "review_rating"],
    "review": ["review", "review_text", "comment", "feedback", "complaint", "notes"],
    "expense": ["expense", "expenses", "cost", "cogs", "spend"],
    "wait_time": ["wait_time", "waiting_time", "prep_time", "delivery_time", "minutes"],
}


def auto_map_columns(df: pd.DataFrame) -> dict:
    mapped = {}
    lower_cols = {c.strip().lower(): c for c in df.columns}
    for canonical, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower_cols:
                mapped[canonical] = lower_cols[alias]
                break
    return mapped


def process_csv_dataset(file_bytes: bytes, filename: str, reviews_bytes: Optional[bytes] = None) -> dict:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV '{filename}': {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail=f"Uploaded CSV '{filename}' is empty.")

    raw_rows = int(len(df))
    duplicate_rows = int(df.duplicated().sum())
    missing_cells = int(df.isna().sum().sum())
    df = df.drop_duplicates().copy()

    col_map = auto_map_columns(df)
    if "revenue" not in col_map and "quantity" not in col_map:
        raise HTTPException(
            status_code=400,
            detail="CSV must contain at least a revenue/amount/sales column or quantity/orders column.",
        )

    date_range_str = "Period not specified"
    active_days = 30
    weekly_series = []
    if "date" in col_map:
        dcol = col_map["date"]
        df["_parsed_date"] = pd.to_datetime(df[dcol], errors="coerce")
        valid_dates = df["_parsed_date"].dropna()
        if not valid_dates.empty:
            min_d = valid_dates.min().strftime("%Y-%m-%d")
            max_d = valid_dates.max().strftime("%Y-%m-%d")
            date_range_str = f"{min_d} to {max_d}"
            active_days = max(1, int((valid_dates.max() - valid_dates.min()).days) + 1)
            df["_week"] = valid_dates.dt.to_period("W").astype(str)

    if "revenue" in col_map:
        df["_rev"] = pd.to_numeric(
            df[col_map["revenue"]].astype(str).str.replace(r"[^\d.\-]", "", regex=True),
            errors="coerce",
        ).fillna(0.0)
    else:
        df["_rev"] = 0.0

    if "quantity" in col_map:
        df["_qty"] = pd.to_numeric(df[col_map["quantity"]], errors="coerce").fillna(1.0)
    else:
        df["_qty"] = 1.0

    total_revenue = round(float(df["_rev"].sum()), 2)
    total_orders = int(len(df))
    units_sold = int(df["_qty"].sum())
    aov = round(total_revenue / total_orders, 2) if total_orders > 0 else 0.0

    metrics = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "units_sold": units_sold,
        "average_order_value": aov,
    }

    if "expense" in col_map:
        exp_series = pd.to_numeric(
            df[col_map["expense"]].astype(str).str.replace(r"[^\d.\-]", "", regex=True),
            errors="coerce",
        ).fillna(0.0)
        total_exp = round(float(exp_series.sum()), 2)
        metrics["business_expenses"] = total_exp
        metrics["estimated_profit"] = round(total_revenue - total_exp, 2)

    if "wait_time" in col_map:
        wt_series = pd.to_numeric(df[col_map["wait_time"]], errors="coerce").dropna()
        if not wt_series.empty:
            metrics["avg_wait_time"] = round(float(wt_series.mean()), 1)

    rev_df = None
    if reviews_bytes:
        try:
            rev_df = pd.read_csv(io.BytesIO(reviews_bytes)).drop_duplicates()
        except Exception:
            rev_df = None

    target_rev_df = rev_df if rev_df is not None else df
    rev_map = auto_map_columns(target_rev_df)

    if "rating" in rev_map:
        r_series = pd.to_numeric(target_rev_df[rev_map["rating"]], errors="coerce").dropna()
        if not r_series.empty:
            metrics["customer_rating"] = round(float(r_series.mean()), 2)
            metrics["customer_complaints"] = int((r_series <= 2.5).sum())

    complaint_keywords = ["slow", "cold", "late", "bad", "worst", "soggy", "delay", "rude", "burnt", "wait"]
    sample_complaints = []
    if "review" in rev_map:
        texts = target_rev_df[rev_map["review"]].dropna().astype(str)
        neg_mask = texts.str.lower().apply(lambda t: any(k in t for k in complaint_keywords))
        if "customer_complaints" not in metrics:
            metrics["customer_complaints"] = int(neg_mask.sum())
        sample_complaints = texts[neg_mask].head(4).tolist()

    product_breakdown = []
    if "product" in col_map:
        pcol = col_map["product"]
        df[pcol] = df[pcol].fillna("General Item").astype(str).str.strip()
        grp = (
            df.groupby(pcol)
            .agg(revenue=("_rev", "sum"), units=("_qty", "sum"), orders=("_rev", "count"))
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        for _, row in grp.iterrows():
            product_breakdown.append(
                {
                    "product": str(row[pcol]),
                    "revenue": round(float(row["revenue"]), 2),
                    "units": int(row["units"]),
                    "orders": int(row["orders"]),
                }
            )

    if "_week" in df.columns:
        wgrp = (
            df.groupby("_week", as_index=False)
            .agg(revenue=("_rev", "sum"), orders=("_rev", "count"))
            .sort_values("_week")
        )
        for idx, row in enumerate(wgrp.itertuples(index=False), start=1):
            weekly_series.append(
                {
                    "week": f"Week {idx}",
                    "period": str(row[0]),
                    "revenue": round(float(row.revenue), 2),
                    "orders": int(row.orders),
                }
            )

    preview_rows = (
        df.drop(columns=[c for c in df.columns if c.startswith("_")], errors="ignore")
        .head(5)
        .fillna("")
        .to_dict(orient="records")
    )

    return {
        "metrics": metrics,
        "products": product_breakdown,
        "weekly": weekly_series,
        "date_range": date_range_str,
        "active_days": active_days,
        "validation": {
            "raw_rows": raw_rows,
            "cleaned_rows": int(len(df)),
            "duplicates_removed": duplicate_rows,
            "missing_cells_handled": missing_cells,
            "mapped_columns": col_map,
            "sample_complaints": sample_complaints,
            "preview_rows": preview_rows,
        },
    }


def generate_30day_tasks(cycle_id: int, business_id: str, baseline_data: dict, currency: str) -> List[GrowthActionTask]:
    metrics = baseline_data["metrics"]
    products = baseline_data["products"]
    complaints = baseline_data["validation"].get("sample_complaints", [])
    tasks = []

    if len(products) >= 2:
        weakest = products[-1]
        strongest = products[0]
        tasks.append(
            GrowthActionTask(
                cycle_id=cycle_id,
                business_id=business_id,
                problem=f"Low Sales Velocity on '{weakest['product']}'",
                evidence=f"Generated only {currency} {weakest['revenue']:,.2f} ({weakest['units']} units) vs top seller '{strongest['product']}' ({currency} {strongest['revenue']:,.2f}).",
                root_cause="Low menu visibility, weak pairing incentives, or lack of staff upsell prompts.",
                recommendation=f"Bundle '{weakest['product']}' with bestseller '{strongest['product']}' at a 10% combo incentive.",
                implementation_steps="1. Train counter staff to suggest the combo on every flagship order. 2. Highlight combo on counter tent card.",
                expected_outcome=f"Lift '{weakest['product']}' unit volume by 20–30% over 30 days.",
                status="Pending",
            )
        )

    if metrics.get("customer_complaints", 0) > 0 or metrics.get("customer_rating", 5.0) < 4.3:
        evidence_txt = (
            f"{metrics.get('customer_complaints', 0)} negative feedback entries detected"
            + (f" (e.g., \"{complaints[0]}\")" if complaints else "")
            + f"; rating at {metrics.get('customer_rating', 'N/A')}/5.0."
        )
        tasks.append(
            GrowthActionTask(
                cycle_id=cycle_id,
                business_id=business_id,
                problem="Customer Experience & Service Friction Dragging Retention",
                evidence=evidence_txt,
                root_cause="Peak-hour prep bottlenecks and inconsistent final quality checks before order handoff.",
                recommendation="Introduce a 15-minute pre-rush prep checklist and 2-point quality/temperature verification.",
                implementation_steps="1. Pre-portion high-demand prep items 30 mins before rush. 2. Assign one expediter to verify order accuracy.",
                expected_outcome="Cut customer complaints by 40–50% and lift average rating above 4.3/5.0.",
                status="Pending",
            )
        )

    tasks.append(
        GrowthActionTask(
            cycle_id=cycle_id,
            business_id=business_id,
            problem="Sub-Optimal Average Order Value (AOV) Across Daily Transactions",
            evidence=f"Current AOV stands at {currency} {metrics['average_order_value']:,.2f} across {metrics['total_orders']} orders.",
            root_cause="Single-item checkouts without structured add-on or loyalty thresholds.",
            recommendation="Introduce a tiered spend reward (free add-on/beverage upgrade above 1.25x current AOV).",
            implementation_steps=f"1. Set reward threshold at {currency} {round(metrics['average_order_value'] * 1.25, 0):,.0f}. 2. Track daily AOV every Sunday.",
            expected_outcome="Increase overall AOV by 12–18% within 4 weeks.",
            status="Pending",
        )
    )

    if "business_expenses" in metrics:
        tasks.append(
            GrowthActionTask(
                cycle_id=cycle_id,
                business_id=business_id,
                problem="Operating Expense Ratio Compressing Net Profit",
                evidence=f"Expenses are {currency} {metrics['business_expenses']:,.2f} against {currency} {metrics['total_revenue']:,.2f} revenue.",
                root_cause="Unmonitored ingredient wastage and over-ordering on slow weekdays.",
                recommendation="Switch to par-level inventory ordering tied to weekly order velocity.",
                implementation_steps="1. Audit top 5 ingredient costs weekly. 2. Trim slow-day prep batches by 15%.",
                expected_outcome="Reduce operating expenses by 8–12% without affecting order fulfillment.",
                status="Pending",
            )
        )

    return tasks


METRIC_CONFIG = {
    "total_revenue": {"label": "Total Revenue", "higher_is_better": True, "unit_type": "currency"},
    "total_orders": {"label": "Total Orders", "higher_is_better": True, "unit_type": "number"},
    "units_sold": {"label": "Products / Units Sold", "higher_is_better": True, "unit_type": "number"},
    "average_order_value": {"label": "Average Order Value", "higher_is_better": True, "unit_type": "currency"},
    "customer_rating": {"label": "Customer Rating", "higher_is_better": True, "unit_type": "rating"},
    "customer_complaints": {"label": "Customer Complaints", "higher_is_better": False, "unit_type": "number"},
    "avg_wait_time": {"label": "Avg Waiting Time (min)", "higher_is_better": False, "unit_type": "minutes"},
    "business_expenses": {"label": "Business Expenses", "higher_is_better": False, "unit_type": "currency"},
    "estimated_profit": {"label": "Estimated Net Profit", "higher_is_better": True, "unit_type": "currency"},
}


def compute_before_after_comparison(before_data: dict, after_data: dict) -> dict:
    b_metrics = before_data["metrics"]
    a_metrics = after_data["metrics"]

    metric_comparisons = []
    for key, cfg in METRIC_CONFIG.items():
        if key not in b_metrics or key not in a_metrics:
            continue

        b_val = float(b_metrics[key])
        a_val = float(a_metrics[key])
        diff = round(a_val - b_val, 2)

        if b_val == 0:
            pct_change = None
            pct_display = "N/A (Zero Baseline)"
        else:
            pct_change = round(((a_val - b_val) / abs(b_val)) * 100, 1)
            pct_display = f"{'+' if pct_change > 0 else ''}{pct_change}%"

        if abs(diff) < 0.01 or (pct_change is not None and abs(pct_change) < 1.0):
            outcome = "unchanged"
            outcome_label = "No Significant Change"
        else:
            is_positive = (diff > 0) if cfg["higher_is_better"] else (diff < 0)
            outcome = "improved" if is_positive else "declined"
            outcome_label = "Improved" if is_positive else "Declined"

        metric_comparisons.append(
            {
                "key": key,
                "label": cfg["label"],
                "unit_type": cfg["unit_type"],
                "higher_is_better": cfg["higher_is_better"],
                "before": b_val,
                "after": a_val,
                "diff": diff,
                "pct_change": pct_change,
                "pct_display": pct_display,
                "outcome": outcome,
                "outcome_label": outcome_label,
            }
        )

    b_prods = {p["product"]: p for p in before_data.get("products", [])}
    a_prods = {p["product"]: p for p in after_data.get("products", [])}
    all_prod_names = sorted(
        list(dict.fromkeys(list(b_prods.keys()) + list(a_prods.keys()))),
        key=lambda n: b_prods.get(n, {}).get("revenue", 0.0) + a_prods.get(n, {}).get("revenue", 0.0),
        reverse=True,
    )
    product_comparisons = []
    product_comparisons = []
    for name in all_prod_names[:10]:
        bv = b_prods.get(name, {}).get("revenue", 0.0)
        av = a_prods.get(name, {}).get("revenue", 0.0)
        pct = round(((av - bv) / bv) * 100, 1) if bv > 0 else None
        product_comparisons.append(
            {
                "product": name,
                "before_revenue": bv,
                "after_revenue": av,
                "diff": round(av - bv, 2),
                "pct_change": pct,
            }
        )

    b_days = before_data.get("active_days", 30)
    a_days = after_data.get("active_days", 30)
    coverage_note = (
        f"Baseline covers {b_days} days ({before_data.get('date_range')}) vs Follow-up covering {a_days} days ({after_data.get('date_range')})."
    )
    if abs(b_days - a_days) > 5:
        coverage_note += " Note: Period lengths differ by more than 5 days—interpret total volume alongside daily averages."

    return {
        "metrics": metric_comparisons,
        "products": product_comparisons,
        "coverage_note": coverage_note,
    }


def build_transformation_report(biz_name: str, currency: str, comp: dict, tasks: List[GrowthActionTask]) -> str:
    improved = [m for m in comp["metrics"] if m["outcome"] == "improved"]
    declined = [m for m in comp["metrics"] if m["outcome"] == "declined"]
    unchanged = [m for m in comp["metrics"] if m["outcome"] == "unchanged"]

    completed_tasks = [t for t in tasks if t.status == "Completed"]
    pending_tasks = [t for t in tasks if t.status != "Completed"]

    valid_imp = [m for m in improved if m["pct_change"] is not None]
    biggest = max(valid_imp, key=lambda x: abs(x["pct_change"])) if valid_imp else (improved[0] if improved else None)

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            prompt = (
                f"Write a clear, trustworthy 'Growth360 Business Transformation Report' for {biz_name} (Currency: {currency}).\n"
                f"VERIFIED METRIC DELTAS:\n{json.dumps(comp['metrics'], indent=2)}\n"
                f"COMPLETED ACTIONS ({len(completed_tasks)}/{len(tasks)}): {[t.recommendation for t in completed_tasks]}\n"
                f"INCOMPLETE ACTIONS ({len(pending_tasks)}): {[t.recommendation for t in pending_tasks]}\n"
                f"DATA COVERAGE: {comp['coverage_note']}\n\n"
                f"Cover all 10 required sections clearly in plain language for a small business owner:\n"
                f"1. Overall Before vs After Summary\n2. Metrics That Improved\n3. Metrics That Declined\n"
                f"4. Metrics Unchanged\n5. Biggest Improvement Achieved\n6. Areas Still Requiring Attention\n"
                f"7. Recommendations Completed\n8. Recommendations Not Completed\n"
                f"9. Observed Correlation vs Causal Caution (explicitly distinguish observed changes from proven direct causation)\n"
                f"10. Next 30-Day Improvement Plan."
            )
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8"),
                headers={"Content-Type": "application/json", "x-goog-api-key": gemini_key},
            )
            with urllib.request.urlopen(req, timeout=18) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    imp_str = ", ".join([f"{m['label']} ({m['pct_display']})" for m in improved]) or "None recorded"
    dec_str = ", ".join([f"{m['label']} ({m['pct_display']})" for m in declined]) or "None recorded"
    unc_str = ", ".join([m["label"] for m in unchanged]) or "None"
    big_str = f"{biggest['label']} ({biggest['pct_display']})" if biggest else "Steady operational stability"
    comp_action_str = "; ".join([t.recommendation for t in completed_tasks]) or "No tasks marked Completed yet"
    pend_action_str = "; ".join([t.recommendation for t in pending_tasks]) or "All planned actions completed"

    return (
        f"1. OVERALL BEFORE VS AFTER PERFORMANCE ({biz_name.upper()})\n"
        f"{comp['coverage_note']} Across {len(comp['metrics'])} tracked business metrics, {len(improved)} improved, {len(declined)} declined, and {len(unchanged)} remained stable.\n\n"
        f"2. METRICS THAT IMPROVED\n• {imp_str}\n\n"
        f"3. METRICS THAT DECLINED\n• {dec_str}\n\n"
        f"4. METRICS REMAINING UNCHANGED\n• {unc_str}\n\n"
        f"5. BIGGEST IMPROVEMENT ACHIEVED\n• {big_str}\n\n"
        f"6. AREAS STILL REQUIRING ATTENTION\n"
        f"• Focus on any declined metrics above and weak-performing SKUs in the product comparison table.\n\n"
        f"7. RECOMMENDATIONS COMPLETED ({len(completed_tasks)} of {len(tasks)})\n• {comp_action_str}\n\n"
        f"8. RECOMMENDATIONS NOT COMPLETED ({len(pending_tasks)})\n• {pend_action_str}\n\n"
        f"9. OBSERVED CHANGES VS. CAUSAL IMPACT\n"
        f"These figures reflect verified changes between your Baseline and Follow-up datasets. While completed actions ({len(completed_tasks)}/{len(tasks)}) align with positive shifts, external factors such as seasonality, foot traffic, and local events may also contribute.\n\n"
        f"10. NEXT 30-DAY IMPROVEMENT PLAN\n"
        f"• Complete remaining pending actions from Cycle 1, double down on your top-growing menu items, and upload your next 30-day dataset to verify sustained compounding growth."
    )


class TaskUpdateRequest(BaseModel):
    status: str
    owner_notes: Optional[str] = ""


@router.get("/active")
def get_active_comparison_cycle(
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    biz = get_active_business(db, business_id)
    cycle = (
        db.query(GrowthCycle)
        .filter(GrowthCycle.business_id == biz.business_id)
        .order_by(GrowthCycle.id.desc())
        .first()
    )
    if not cycle:
        return {
            "has_cycle": False,
            "business": {
                "business_id": biz.business_id,
                "business_name": biz.business_name,
                "currency": biz.currency,
            },
        }

    tasks = (
        db.query(GrowthActionTask)
        .filter(GrowthActionTask.cycle_id == cycle.id)
        .order_by(GrowthActionTask.id.asc())
        .all()
    )
    return _serialize_cycle(cycle, tasks, biz)


@router.get("/history")
def get_comparison_history(
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    biz = get_active_business(db, business_id)
    cycles = (
        db.query(GrowthCycle)
        .filter(GrowthCycle.business_id == biz.business_id)
        .order_by(GrowthCycle.id.desc())
        .all()
    )
    history = []
    for c in cycles:
        tasks = db.query(GrowthActionTask).filter(GrowthActionTask.cycle_id == c.id).all()
        comp = json.loads(c.comparison_result_json) if c.comparison_result_json else None
        rev_delta = None
        if comp:
            rev_item = next((m for m in comp["metrics"] if m["key"] == "total_revenue"), None)
            rev_delta = rev_item["pct_display"] if rev_item else None
        history.append(
            {
                "id": c.id,
                "cycle_label": c.cycle_label,
                "status": c.status,
                "baseline_filename": c.baseline_filename,
                "baseline_date_range": c.baseline_date_range,
                "followup_filename": c.followup_filename,
                "followup_date_range": c.followup_date_range,
                "revenue_change": rev_delta,
                "tasks_completed": sum(1 for t in tasks if t.status == "Completed"),
                "tasks_total": len(tasks),
                "created_at": c.baseline_uploaded_at.strftime("%Y-%m-%d") if c.baseline_uploaded_at else "",
                "ai_report_text": c.ai_report_text,
                "comparison": comp,
            }
        )
    return history


@router.post("/baseline")
async def upload_baseline_csv(
    sales_file: UploadFile = File(...),
    reviews_file: Optional[UploadFile] = File(None),
    cycle_label: str = Form("30-Day Growth Cycle"),
    business_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    biz = get_active_business(db, business_id)
    sales_bytes = await sales_file.read()
    rev_bytes = await reviews_file.read() if reviews_file else None

    parsed = process_csv_dataset(sales_bytes, sales_file.filename, rev_bytes)

    cycle = GrowthCycle(
        business_id=biz.business_id,
        cycle_label=cycle_label,
        status="baseline_uploaded",
        baseline_filename=sales_file.filename,
        baseline_date_range=parsed["date_range"],
        baseline_days=parsed["active_days"],
        baseline_validation_json=json.dumps(parsed["validation"]),
        baseline_metrics_json=json.dumps(parsed["metrics"]),
        baseline_products_json=json.dumps(parsed["products"]),
        baseline_weekly_json=json.dumps(parsed["weekly"]),
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)

    tasks = generate_30day_tasks(cycle.id, biz.business_id, parsed, biz.currency)
    for t in tasks:
        db.add(t)
    db.commit()

    saved_tasks = db.query(GrowthActionTask).filter(GrowthActionTask.cycle_id == cycle.id).all()
    return _serialize_cycle(cycle, saved_tasks, biz)


@router.post("/followup/{cycle_id}")
async def upload_followup_csv(
    cycle_id: int,
    sales_file: UploadFile = File(...),
    reviews_file: Optional[UploadFile] = File(None),
    business_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    biz = get_active_business(db, business_id)
    cycle = (
        db.query(GrowthCycle)
        .filter(GrowthCycle.id == cycle_id, GrowthCycle.business_id == biz.business_id)
        .first()
    )
    if not cycle:
        raise HTTPException(status_code=404, detail="Baseline cycle not found for this business profile.")

    sales_bytes = await sales_file.read()
    rev_bytes = await reviews_file.read() if reviews_file else None
    after_parsed = process_csv_dataset(sales_bytes, sales_file.filename, rev_bytes)

    before_parsed = {
        "metrics": json.loads(cycle.baseline_metrics_json),
        "products": json.loads(cycle.baseline_products_json),
        "weekly": json.loads(cycle.baseline_weekly_json),
        "date_range": cycle.baseline_date_range,
        "active_days": cycle.baseline_days,
        "validation": json.loads(cycle.baseline_validation_json),
    }

    comparison = compute_before_after_comparison(before_parsed, after_parsed)
    tasks = db.query(GrowthActionTask).filter(GrowthActionTask.cycle_id == cycle.id).all()
    report_text = build_transformation_report(biz.business_name, biz.currency, comparison, tasks)

    cycle.status = "completed"
    cycle.followup_filename = sales_file.filename
    cycle.followup_uploaded_at = datetime.utcnow()
    cycle.followup_date_range = after_parsed["date_range"]
    cycle.followup_days = after_parsed["active_days"]
    cycle.followup_validation_json = json.dumps(after_parsed["validation"])
    cycle.followup_metrics_json = json.dumps(after_parsed["metrics"])
    cycle.followup_products_json = json.dumps(after_parsed["products"])
    cycle.followup_weekly_json = json.dumps(after_parsed["weekly"])
    cycle.comparison_result_json = json.dumps(comparison)
    cycle.ai_report_text = report_text

    db.commit()
    db.refresh(cycle)
    return _serialize_cycle(cycle, tasks, biz)


@router.patch("/tasks/{task_id}")
def update_growth_task(
    task_id: int,
    payload: TaskUpdateRequest,
    db: Session = Depends(get_db),
):
    task = db.query(GrowthActionTask).filter(GrowthActionTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = payload.status
    if payload.owner_notes is not None:
        task.owner_notes = payload.owner_notes
    if payload.status == "Completed":
        task.completed_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    db.commit()
    db.refresh(task)
    return {
        "id": task.id,
        "status": task.status,
        "owner_notes": task.owner_notes,
        "completed_at": task.completed_at,
    }


def _serialize_cycle(cycle: GrowthCycle, tasks: List[GrowthActionTask], biz) -> dict:
    return {
        "has_cycle": True,
        "business": {
            "business_id": biz.business_id,
            "business_name": biz.business_name,
            "currency": biz.currency,
        },
        "cycle": {
            "id": cycle.id,
            "cycle_label": cycle.cycle_label,
            "status": cycle.status,
            "baseline": {
                "filename": cycle.baseline_filename,
                "date_range": cycle.baseline_date_range,
                "active_days": cycle.baseline_days,
                "metrics": json.loads(cycle.baseline_metrics_json),
                "products": json.loads(cycle.baseline_products_json),
                "weekly": json.loads(cycle.baseline_weekly_json),
                "validation": json.loads(cycle.baseline_validation_json),
            },
            "followup": (
                {
                    "filename": cycle.followup_filename,
                    "date_range": cycle.followup_date_range,
                    "active_days": cycle.followup_days,
                    "metrics": json.loads(cycle.followup_metrics_json),
                    "products": json.loads(cycle.followup_products_json),
                    "weekly": json.loads(cycle.followup_weekly_json),
                    "validation": json.loads(cycle.followup_validation_json),
                }
                if cycle.followup_metrics_json
                else None
            ),
            "comparison": json.loads(cycle.comparison_result_json) if cycle.comparison_result_json else None,
            "ai_report_text": cycle.ai_report_text,
        },
        "tasks": [
            {
                "id": t.id,
                "problem": t.problem,
                "evidence": t.evidence,
                "root_cause": t.root_cause,
                "recommendation": t.recommendation,
                "implementation_steps": t.implementation_steps,
                "expected_outcome": t.expected_outcome,
                "status": t.status,
                "owner_notes": t.owner_notes,
                "completed_at": t.completed_at,
            }
            for t in tasks
        ],
    }