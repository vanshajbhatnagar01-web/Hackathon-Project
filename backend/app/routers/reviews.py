from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CustomerReview
from app.routers.business import resolve_business
from app.schemas import (
    ReviewItemResponse,
    SentimentSummaryResponse,
    SentimentBreakdownItem,
)

router = APIRouter(prefix="/reviews", tags=["Customer Reviews & Sentiment"])


@router.get("", response_model=List[ReviewItemResponse])
def get_reviews(
    business_id: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(
        None, description="Filter by sentiment: Positive, Neutral, or Negative"
    ),
    product: Optional[str] = Query(None, description="Filter by product name"),
    limit: int = Query(50, ge=1, le=1000, description="Max reviews to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """Fetch customer reviews with optional filtering by sentiment and product."""
    biz = resolve_business(db, business_id)
    query = db.query(CustomerReview).filter(
        CustomerReview.business_id == biz.business_id
    )

    if sentiment:
        query = query.filter(
            func.lower(CustomerReview.predicted_sentiment) == sentiment.strip().lower()
        )
    if product:
        query = query.filter(
            func.lower(CustomerReview.product).contains(product.strip().lower())
        )

    return (
        query.order_by(CustomerReview.date.desc(), CustomerReview.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/sentiment-summary", response_model=SentimentSummaryResponse)
def get_sentiment_summary(
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Return sentiment distribution counts, percentages, and top complained products."""
    biz = resolve_business(db, business_id)

    total_reviews = (
        db.query(func.count(CustomerReview.id))
        .filter(CustomerReview.business_id == biz.business_id)
        .scalar()
        or 0
    )

    avg_rating = (
        db.query(func.avg(CustomerReview.rating))
        .filter(CustomerReview.business_id == biz.business_id)
        .scalar()
        or 0.0
    )

    sentiment_col = func.coalesce(
        CustomerReview.predicted_sentiment, CustomerReview.sentiment, "Unknown"
    )
    rows = (
        db.query(sentiment_col.label("label"), func.count(CustomerReview.id).label("cnt"))
        .filter(CustomerReview.business_id == biz.business_id)
        .group_by(sentiment_col)
        .all()
    )

    breakdown = [
        SentimentBreakdownItem(
            sentiment=str(r.label),
            count=int(r.cnt),
            percentage=round((int(r.cnt) / total_reviews * 100), 2)
            if total_reviews > 0
            else 0.0,
        )
        for r in rows
    ]

    neg_products = (
        db.query(
            CustomerReview.product,
            func.count(CustomerReview.id).label("negative_count"),
        )
        .filter(
            CustomerReview.business_id == biz.business_id,
            func.lower(sentiment_col) == "negative",
            CustomerReview.product.isnot(None),
        )
        .group_by(CustomerReview.product)
        .order_by(func.count(CustomerReview.id).desc())
        .limit(5)
        .all()
    )

    return SentimentSummaryResponse(
        business_id=biz.business_id,
        total_reviews=int(total_reviews),
        average_rating=round(float(avg_rating), 2),
        breakdown=breakdown,
        top_complained_products=[
            {"product": p.product, "negative_review_count": int(p.negative_count)}
            for p in neg_products
        ],
    )