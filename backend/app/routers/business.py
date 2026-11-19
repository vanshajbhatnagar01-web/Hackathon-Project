from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Business, BusinessHealthScore, Product
from app.schemas import (
    BusinessProfileResponse,
    BusinessHealthResponse,
    ProductPerformanceResponse,
)

router = APIRouter(prefix="/business", tags=["Business & Health"])


def resolve_business(db: Session, business_id: Optional[str] = None) -> Business:
    """Helper to fetch the requested business or default to the first seeded business."""
    if business_id:
        biz = db.query(Business).filter(Business.business_id == business_id).first()
    else:
        biz = db.query(Business).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business profile not found.")
    return biz


@router.get("/profile", response_model=BusinessProfileResponse)
def get_business_profile(
    business_id: Optional[str] = Query(None, description="Optional business ID"),
    db: Session = Depends(get_db),
):
    """Fetch the full business profile (Cafe Nova)."""
    return resolve_business(db, business_id)


@router.get("/health", response_model=BusinessHealthResponse)
def get_business_health(
    business_id: Optional[str] = Query(None, description="Optional business ID"),
    db: Session = Depends(get_db),
):
    """Fetch the latest overall Business Health Score and sub-category breakdown."""
    biz = resolve_business(db, business_id)
    health = (
        db.query(BusinessHealthScore)
        .filter(BusinessHealthScore.business_id == biz.business_id)
        .order_by(BusinessHealthScore.id.desc())
        .first()
    )
    if not health:
        raise HTTPException(status_code=404, detail="Business health score not found.")
    return health


@router.get("/products", response_model=List[ProductPerformanceResponse])
def get_business_products(
    business_id: Optional[str] = Query(None, description="Optional business ID"),
    db: Session = Depends(get_db),
):
    """Fetch all menu products ranked by total sales."""
    biz = resolve_business(db, business_id)
    return (
        db.query(Product)
        .filter(Product.business_id == biz.business_id)
        .order_by(Product.total_sales.desc())
        .all()
    )
