from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import DemandForecast
from app.routers.business import resolve_business
from app.schemas import SevenDayForecastResponse, ForecastDayItem

router = APIRouter(prefix="/forecast", tags=["Demand Forecasting"])


@router.get("/7-days", response_model=SevenDayForecastResponse)
def get_seven_day_forecast(
    business_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Fetch the 7-day predicted revenue and demand quantities."""
    biz = resolve_business(db, business_id)
    forecasts = (
        db.query(DemandForecast)
        .filter(DemandForecast.business_id == biz.business_id)
        .order_by(DemandForecast.forecast_date.asc())
        .limit(7)
        .all()
    )

    total_rev = round(sum(f.predicted_revenue for f in forecasts), 2)
    total_qty = round(sum(f.predicted_quantity for f in forecasts), 2)

    return SevenDayForecastResponse(
        business_id=biz.business_id,
        total_predicted_revenue=total_rev,
        total_predicted_quantity=total_qty,
        daily_forecasts=[ForecastDayItem.model_validate(f) for f in forecasts],
    )