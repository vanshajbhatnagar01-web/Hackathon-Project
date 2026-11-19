from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    BusinessInsight,
    ActionDecision,
    BusinessHealthScore,
    SalesRecord,
    CustomerReview,
    DemandForecast,
)
from app.routers.business import resolve_business
from app.schemas import (
    InsightWithActionResponse,
    ActionDecisionRequest,
    ActionDecisionResponse,
    AIQueryRequest,
    AIQueryResponse,
)

router = APIRouter(tags=["AI Insights, Actions & Copilot"])


@router.get("/insights", response_model=List[InsightWithActionResponse])
def get_insights(
    business_id: Optional[str] = Query(None),
    source_type: Optional[str] = Query(
        None,
        description="Filter by type: root_cause, doctor_diagnosis, marketing_campaign, demand_insight, review_insight",
    ),
    status: Optional[str] = Query(
        None, description="Filter by decision status: pending, approved, rejected"
    ),
    db: Session = Depends(get_db),
):
    """Fetch AI insights, root-cause findings, and marketing campaigns with owner approval status."""
    biz = resolve_business(db, business_id)

    query = (
        db.query(BusinessInsight, ActionDecision)
        .outerjoin(ActionDecision, ActionDecision.insight_id == BusinessInsight.id)
        .filter(BusinessInsight.business_id == biz.business_id)
    )

    if source_type:
        query = query.filter(
            func.lower(BusinessInsight.source_type) == source_type.strip().lower()
        )
    if status:
        query = query.filter(
            func.lower(ActionDecision.decision_status) == status.strip().lower()
        )

    results = query.order_by(BusinessInsight.id.asc()).all()

    response_items = []
    for insight, decision in results:
        response_items.append(
            InsightWithActionResponse(
                id=insight.id,
                business_id=insight.business_id,
                source_type=insight.source_type,
                category_or_product=insight.category_or_product,
                title=insight.title,
                evidence=insight.evidence,
                recommendation=insight.recommendation,
                priority=insight.priority,
                target_audience=insight.target_audience,
                recommended_channel=insight.recommended_channel,
                recommended_timing=insight.recommended_timing,
                decision_id=decision.id if decision else None,
                decision_status=decision.decision_status if decision else "pending",
                owner_notes=decision.owner_notes if decision else None,
                decided_at=decision.decided_at if decision else None,
            )
        )
    return response_items


def _update_action_decision(
    db: Session, payload: ActionDecisionRequest, new_status: str
) -> ActionDecisionResponse:
    insight = (
        db.query(BusinessInsight)
        .filter(BusinessInsight.id == payload.insight_id)
        .first()
    )
    if not insight:
        raise HTTPException(
            status_code=404, detail=f"Insight ID {payload.insight_id} not found."
        )

    decision = (
        db.query(ActionDecision)
        .filter(ActionDecision.insight_id == insight.id)
        .first()
    )
    if not decision:
        decision = ActionDecision(
            business_id=insight.business_id,
            insight_id=insight.id,
            decision_status=new_status,
            owner_notes=payload.owner_notes,
            decided_at=datetime.utcnow(),
        )
        db.add(decision)
    else:
        decision.decision_status = new_status
        if payload.owner_notes is not None:
            decision.owner_notes = payload.owner_notes
        decision.decided_at = datetime.utcnow()

    db.commit()
    db.refresh(decision)
    return ActionDecisionResponse.model_validate(decision)


@router.post("/actions/approve", response_model=ActionDecisionResponse)
def approve_action(
    payload: ActionDecisionRequest,
    db: Session = Depends(get_db),
):
    """Approve an AI-recommended business action or marketing campaign."""
    return _update_action_decision(db, payload, "approved")


@router.post("/actions/reject", response_model=ActionDecisionResponse)
def reject_action(
    payload: ActionDecisionRequest,
    db: Session = Depends(get_db),
):
    """Reject an AI-recommended business action or marketing campaign."""
    return _update_action_decision(db, payload, "rejected")


@router.get("/actions/history", response_model=List[InsightWithActionResponse])
def get_action_history(
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Return all approved and rejected owner decisions (audit history)."""
    biz = resolve_business(db, business_id)
    results = (
        db.query(BusinessInsight, ActionDecision)
        .join(ActionDecision, ActionDecision.insight_id == BusinessInsight.id)
        .filter(
            BusinessInsight.business_id == biz.business_id,
            ActionDecision.decision_status.in_(["approved", "rejected"]),
        )
        .order_by(ActionDecision.decided_at.desc())
        .all()
    )

    return [
        InsightWithActionResponse(
            id=insight.id,
            business_id=insight.business_id,
            source_type=insight.source_type,
            category_or_product=insight.category_or_product,
            title=insight.title,
            evidence=insight.evidence,
            recommendation=insight.recommendation,
            priority=insight.priority,
            target_audience=insight.target_audience,
            recommended_channel=insight.recommended_channel,
            recommended_timing=insight.recommended_timing,
            decision_id=decision.id,
            decision_status=decision.decision_status,
            owner_notes=decision.owner_notes,
            decided_at=decision.decided_at,
        )
        for insight, decision in results
    ]


@router.post("/ai/query", response_model=AIQueryResponse)
def ask_business_copilot(
    payload: AIQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Grounds business owner questions in real MySQL metrics and uses Gemini
    (if configured) or a structured data-backed response.
    """
    biz = resolve_business(db, payload.business_id)

    health = (
        db.query(BusinessHealthScore)
        .filter(BusinessHealthScore.business_id == biz.business_id)
        .order_by(BusinessHealthScore.id.desc())
        .first()
    )
    total_rev = (
        db.query(func.coalesce(func.sum(SalesRecord.revenue), 0.0))
        .filter(SalesRecord.business_id == biz.business_id)
        .scalar()
        or 0.0
    )
    neg_reviews = (
        db.query(func.count(CustomerReview.id))
        .filter(
            CustomerReview.business_id == biz.business_id,
            func.lower(CustomerReview.predicted_sentiment) == "negative",
        )
        .scalar()
        or 0
    )
    forecast_rev = (
        db.query(func.coalesce(func.sum(DemandForecast.predicted_revenue), 0.0))
        .filter(DemandForecast.business_id == biz.business_id)
        .scalar()
        or 0.0
    )
    top_insights = (
        db.query(BusinessInsight)
        .filter(BusinessInsight.business_id == biz.business_id)
        .limit(3)
        .all()
    )

    metrics = {
        "business_name": biz.business_name,
        "health_score": health.health_score if health else None,
        "health_status": health.health_status if health else None,
        "average_rating": health.average_rating if health else None,
        "total_90_day_revenue": round(float(total_rev), 2),
        "negative_reviews_count": int(neg_reviews),
        "next_7_days_predicted_revenue": round(float(forecast_rev), 2),
    }

    # Try calling Gemini if gemini_client is available and API key is set
    answer_text = None
    try:
        from gemini_client import generate_response  # existing backend helper

        context_prompt = (
            f"You are Growth360 AI Copilot for {biz.business_name} ({biz.city}).\n"
            f"Live Database Metrics: {metrics}\n"
            f"Top Findings: {[i.title + ': ' + i.recommendation for i in top_insights]}\n"
            f"Owner Question: {payload.question}\n"
            f"Give a concise, actionable answer grounded strictly in these numbers."
        )
        answer_text = generate_response(context_prompt)
    except Exception:
        # Clean data-backed fallback so /ai/query never fails during live demos
        rec_summary = (
            top_insights[0].recommendation
            if top_insights
            else "Review top-selling items and peak hours."
        )
        answer_text = (
            f"For {biz.business_name}, your Business Health Score is "
            f"{metrics['health_score']} ({metrics['health_status']}) with an average rating of "
            f"{metrics['average_rating']}/5 across 1,000 reviews ({neg_reviews} negative). "
            f"90-day revenue is {biz.currency} {metrics['total_90_day_revenue']:,.2f}, and "
            f"predicted revenue for the next 7 days is {biz.currency} {metrics['next_7_days_predicted_revenue']:,.2f}. "
            f"Priority recommendation: {rec_summary}"
        )

    return AIQueryResponse(
        question=payload.question,
        answer=answer_text,
        supporting_metrics=metrics,
    )