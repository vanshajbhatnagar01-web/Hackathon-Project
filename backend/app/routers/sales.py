from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SalesRecord
from app.routers.business import resolve_business
from app.schemas import (
    SalesSummaryResponse,
    DailySalesTrendItem,
    HourlySalesItem,
    ProductSalesItem,
)

router = APIRouter(prefix="/sales", tags=["Sales Analytics"])


@router.get("/summary", response_model=SalesSummaryResponse)
def get_sales_summary(
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Return overall 90-day revenue, units sold, average daily revenue, top item, and peak hour."""
    biz = resolve_business(db, business_id)

    totals = (
        db.query(
            func.coalesce(func.sum(SalesRecord.revenue), 0.0),
            func.coalesce(func.sum(SalesRecord.quantity_sold), 0),
            func.count(SalesRecord.id),
            func.count(func.distinct(SalesRecord.date)),
        )
        .filter(SalesRecord.business_id == biz.business_id)
        .one()
    )

    total_rev = round(float(totals[0]), 2)
    total_qty = int(totals[1])
    total_tx = int(totals[2])
    distinct_days = int(totals[3]) or 1
    avg_daily = round(total_rev / distinct_days, 2)

    top_prod_row = (
        db.query(SalesRecord.product, func.sum(SalesRecord.revenue).label("rev"))
        .filter(SalesRecord.business_id == biz.business_id)
        .group_by(SalesRecord.product)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .first()
    )

    peak_hour_row = (
        db.query(SalesRecord.hour, func.sum(SalesRecord.revenue).label("rev"))
        .filter(SalesRecord.business_id == biz.business_id)
        .group_by(SalesRecord.hour)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .first()
    )

    return SalesSummaryResponse(
        business_id=biz.business_id,
        total_revenue=total_rev,
        total_quantity_sold=total_qty,
        total_transactions=total_tx,
        average_daily_revenue=avg_daily,
        top_product=top_prod_row[0] if top_prod_row else None,
        peak_hour=int(peak_hour_row[0]) if peak_hour_row else None,
    )


@router.get("/trends", response_model=List[DailySalesTrendItem])
def get_daily_sales_trends(
    business_id: Optional[str] = Query(None),
    limit: int = Query(90, ge=1, le=365, description="Number of recent days to return"),
    db: Session = Depends(get_db),
):
    """Return daily revenue and quantity trend for line/area charts."""
    biz = resolve_business(db, business_id)
    rows = (
        db.query(
            SalesRecord.date,
            func.sum(SalesRecord.revenue).label("daily_revenue"),
            func.sum(SalesRecord.quantity_sold).label("daily_quantity"),
        )
        .filter(SalesRecord.business_id == biz.business_id)
        .group_by(SalesRecord.date)
        .order_by(SalesRecord.date.asc())
        .limit(limit)
        .all()
    )
    return [
        DailySalesTrendItem(
            date=r.date,
            daily_revenue=round(float(r.daily_revenue), 2),
            daily_quantity=int(r.daily_quantity),
        )
        for r in rows
    ]


@router.get("/hourly", response_model=List[HourlySalesItem])
def get_hourly_sales(
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Return sales grouped by hour of the day (peak hours analysis)."""
    biz = resolve_business(db, business_id)
    rows = (
        db.query(
            SalesRecord.hour,
            func.sum(SalesRecord.revenue).label("total_revenue"),
            func.sum(SalesRecord.quantity_sold).label("total_quantity"),
        )
        .filter(SalesRecord.business_id == biz.business_id)
        .group_by(SalesRecord.hour)
        .order_by(SalesRecord.hour.asc())
        .all()
    )
    return [
        HourlySalesItem(
            hour=int(r.hour),
            total_revenue=round(float(r.total_revenue), 2),
            total_quantity=int(r.total_quantity),
        )
        for r in rows
    ]


@router.get("/by-product", response_model=List[ProductSalesItem])
def get_sales_by_product(
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Return total revenue and quantity sold per menu product."""
    biz = resolve_business(db, business_id)
    rows = (
        db.query(
            SalesRecord.product,
            func.sum(SalesRecord.revenue).label("total_revenue"),
            func.sum(SalesRecord.quantity_sold).label("total_quantity"),
        )
        .filter(SalesRecord.business_id == biz.business_id)
        .group_by(SalesRecord.product)
        .order_by(func.sum(SalesRecord.revenue).desc())
        .all()
    )
    return [
        ProductSalesItem(
            product=r.product,
            total_revenue=round(float(r.total_revenue), 2),
            total_quantity=int(r.total_quantity),
        )
        for r in rows
    ]