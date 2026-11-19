from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ==============================================================================
# 1. BUSINESS & PRODUCT SCHEMAS
# ==============================================================================
class BusinessProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: str
    business_name: str
    category: Optional[str] = None
    business_type: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = "INR"
    average_order_value: Optional[float] = None
    opening_hours: Optional[str] = None
    operating_days: Optional[str] = None
    monthly_marketing_budget: Optional[float] = None
    seating_capacity: Optional[int] = None
    number_of_employees: Optional[int] = None
    order_channels: Optional[str] = None
    primary_customer_group: Optional[str] = None
    business_goals: Optional[str] = None


class BusinessHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: str
    health_score: float
    health_status: str
    average_rating: Optional[float] = None
    revenue_growth_percent: Optional[float] = None
    quantity_growth_percent: Optional[float] = None
    sales_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    product_score: Optional[float] = None
    operations_score: Optional[float] = None
    calculated_at: Optional[datetime] = None


class ProductPerformanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: str
    product_name: str
    average_rating: Optional[float] = None
    total_reviews: Optional[int] = 0
    total_sales: Optional[float] = 0.0
    total_quantity: Optional[int] = 0


# ==============================================================================
# 2. SALES ANALYTICS SCHEMAS
# ==============================================================================
class SalesSummaryResponse(BaseModel):
    business_id: str
    total_revenue: float
    total_quantity_sold: int
    total_transactions: int
    average_daily_revenue: float
    top_product: Optional[str] = None
    peak_hour: Optional[int] = None


class DailySalesTrendItem(BaseModel):
    date: date
    daily_revenue: float
    daily_quantity: int


class HourlySalesItem(BaseModel):
    hour: int
    total_revenue: float
    total_quantity: int


class ProductSalesItem(BaseModel):
    product: str
    total_revenue: float
    total_quantity: int


# ==============================================================================
# 3. CUSTOMER REVIEWS & SENTIMENT SCHEMAS
# ==============================================================================
class ReviewItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_id: str
    date: Optional[date] = None
    rating: float
    review_text: str
    product: Optional[str] = None
    sentiment: Optional[str] = None
    predicted_sentiment: Optional[str] = None
    confidence: Optional[float] = None


class SentimentBreakdownItem(BaseModel):
    sentiment: str
    count: int
    percentage: float


class SentimentSummaryResponse(BaseModel):
    business_id: str
    total_reviews: int
    average_rating: float
    breakdown: List[SentimentBreakdownItem]
    top_complained_products: List[dict]


# ==============================================================================
# 4. DEMAND FORECAST SCHEMAS
# ==============================================================================
class ForecastDayItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    forecast_date: date
    predicted_revenue: float
    predicted_quantity: float
    model_name: Optional[str] = None


class SevenDayForecastResponse(BaseModel):
    business_id: str
    total_predicted_revenue: float
    total_predicted_quantity: float
    daily_forecasts: List[ForecastDayItem]


# ==============================================================================
# 5. INSIGHTS & ACTION DECISIONS SCHEMAS
# ==============================================================================
class InsightWithActionResponse(BaseModel):
    id: int
    business_id: str
    source_type: str
    category_or_product: Optional[str] = None
    title: str
    evidence: Optional[str] = None
    recommendation: str
    priority: Optional[str] = None
    target_audience: Optional[str] = None
    recommended_channel: Optional[str] = None
    recommended_timing: Optional[str] = None
    decision_id: Optional[int] = None
    decision_status: str = "pending"
    owner_notes: Optional[str] = None
    decided_at: Optional[datetime] = None


class ActionDecisionRequest(BaseModel):
    insight_id: int = Field(..., description="ID of the business insight to approve or reject")
    owner_notes: Optional[str] = Field(
        None, max_length=500, description="Optional note from the business owner"
    )


class ActionDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: str
    insight_id: int
    decision_status: str
    owner_notes: Optional[str] = None
    decided_at: datetime


# ==============================================================================
# 6. AI COPILOT QUERY SCHEMA (Bonus Integration Endpoint)
# ==============================================================================
class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Business owner question")
    business_id: Optional[str] = None


class AIQueryResponse(BaseModel):
    question: str
    answer: str
    supporting_metrics: dict