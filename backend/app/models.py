from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    Date,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from app.database import Base


# ==============================================================================
# 1. BUSINESSES TABLE
# ==============================================================================
class Business(Base):
    __tablename__ = "businesses"

    business_id = Column(String(50), primary_key=True, index=True)
    business_name = Column(String(150), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    business_type = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    currency = Column(String(20), nullable=True, default="INR")
    average_order_value = Column(Float, nullable=True)
    opening_hours = Column(String(100), nullable=True)
    operating_days = Column(String(100), nullable=True)
    monthly_marketing_budget = Column(Float, nullable=True)
    seating_capacity = Column(Integer, nullable=True)
    number_of_employees = Column(Integer, nullable=True)
    order_channels = Column(String(255), nullable=True)
    primary_customer_group = Column(String(255), nullable=True)
    business_goals = Column(Text, nullable=True)
    data_type = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships (One Business -> Many Products, Reviews, Sales, etc.)
    products = relationship(
        "Product", back_populates="business", cascade="all, delete-orphan"
    )
    reviews = relationship(
        "CustomerReview", back_populates="business", cascade="all, delete-orphan"
    )
    sales = relationship(
        "SalesRecord", back_populates="business", cascade="all, delete-orphan"
    )
    health_scores = relationship(
        "BusinessHealthScore", back_populates="business", cascade="all, delete-orphan"
    )
    forecasts = relationship(
        "DemandForecast", back_populates="business", cascade="all, delete-orphan"
    )
    insights = relationship(
        "BusinessInsight", back_populates="business", cascade="all, delete-orphan"
    )
    action_decisions = relationship(
        "ActionDecision", back_populates="business", cascade="all, delete-orphan"
    )


# ==============================================================================
# 2. PRODUCTS TABLE
# ==============================================================================
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(
        String(50), ForeignKey("businesses.business_id"), nullable=False, index=True
    )
    product_name = Column(String(150), nullable=False, index=True)
    average_rating = Column(Float, nullable=True)
    total_reviews = Column(Integer, nullable=True, default=0)
    total_sales = Column(Float, nullable=True, default=0.0)
    total_quantity = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    business = relationship("Business", back_populates="products")
    reviews = relationship("CustomerReview", back_populates="product_rel")
    sales = relationship("SalesRecord", back_populates="product_rel")


# ==============================================================================
# 3. CUSTOMER REVIEWS TABLE (with ML Sentiment Predictions)
# ==============================================================================
class CustomerReview(Base):
    __tablename__ = "customer_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String(50), unique=True, nullable=False, index=True)
    business_id = Column(
        String(50), ForeignKey("businesses.business_id"), nullable=False, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)

    date = Column(Date, nullable=True, index=True)
    rating = Column(Float, nullable=False)
    review_text = Column(Text, nullable=False)
    cleaned_text = Column(Text, nullable=True)
    product = Column(String(150), nullable=True, index=True)

    # Sentiment columns from reviews_with_sentiment.csv
    sentiment = Column(String(50), nullable=True, index=True)
    predicted_sentiment = Column(String(50), nullable=True, index=True)
    confidence = Column(Float, nullable=True)

    # Relationships
    business = relationship("Business", back_populates="reviews")
    product_rel = relationship("Product", back_populates="reviews")


# ==============================================================================
# 4. SALES RECORDS TABLE (90 Days Hourly/Transaction Sales)
# ==============================================================================
class SalesRecord(Base):
    __tablename__ = "sales_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(
        String(50), ForeignKey("businesses.business_id"), nullable=False, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)

    date = Column(Date, nullable=False, index=True)
    hour = Column(Integer, nullable=False, index=True)
    product = Column(String(150), nullable=False, index=True)
    quantity_sold = Column(Integer, nullable=False)
    revenue = Column(Float, nullable=False)

    # Relationships
    business = relationship("Business", back_populates="sales")
    product_rel = relationship("Product", back_populates="sales")


# ==============================================================================
# 5. BUSINESS HEALTH SCORES TABLE (Overall + Breakdown Metrics)
# ==============================================================================
class BusinessHealthScore(Base):
    __tablename__ = "business_health_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(
        String(50), ForeignKey("businesses.business_id"), nullable=False, index=True
    )
    health_score = Column(Float, nullable=False)
    health_status = Column(String(50), nullable=False)
    average_rating = Column(Float, nullable=True)
    revenue_growth_percent = Column(Float, nullable=True)
    quantity_growth_percent = Column(Float, nullable=True)

    # Optional breakdown fields (from business_health_breakdown.csv)
    sales_score = Column(Float, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    product_score = Column(Float, nullable=True)
    operations_score = Column(Float, nullable=True)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    business = relationship("Business", back_populates="health_scores")


# ==============================================================================
# 6. DEMAND FORECASTS TABLE (7-Day ML Predictions)
# ==============================================================================
class DemandForecast(Base):
    __tablename__ = "demand_forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(
        String(50), ForeignKey("businesses.business_id"), nullable=False, index=True
    )
    forecast_date = Column(Date, nullable=False, index=True)
    predicted_revenue = Column(Float, nullable=False)
    predicted_quantity = Column(Float, nullable=False)
    model_name = Column(String(100), nullable=True, default="DemandForecastingModel")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    business = relationship("Business", back_populates="forecasts")


# ==============================================================================
# 7. BUSINESS INSIGHTS TABLE (Root-Cause Findings, Doctor Diagnosis & Campaigns)
# ==============================================================================
class BusinessInsight(Base):
    __tablename__ = "business_insights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(
        String(50), ForeignKey("businesses.business_id"), nullable=False, index=True
    )
    # Source category: "root_cause", "doctor_diagnosis", "marketing_campaign", "demand_insight", "review_insight"
    source_type = Column(String(50), nullable=False, index=True)
    category_or_product = Column(String(150), nullable=True)
    title = Column(String(255), nullable=False)
    evidence = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=False)
    priority = Column(String(50), nullable=True, index=True)

    # Extra fields useful for marketing campaigns (marketing_agent_campaigns.csv)
    target_audience = Column(String(255), nullable=True)
    recommended_channel = Column(String(100), nullable=True)
    recommended_timing = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    business = relationship("Business", back_populates="insights")
    action_decisions = relationship(
        "ActionDecision", back_populates="insight", cascade="all, delete-orphan"
    )


# ==============================================================================
# 8. ACTION DECISIONS TABLE (Owner Approval / Rejection Workflow)
# ==============================================================================
class ActionDecision(Base):
    __tablename__ = "action_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(
        String(50), ForeignKey("businesses.business_id"), nullable=False, index=True
    )
    insight_id = Column(
        Integer, ForeignKey("business_insights.id"), nullable=False, index=True
    )
    # Status values: "pending", "approved", "rejected"
    decision_status = Column(String(50), nullable=False, default="pending", index=True)
    owner_notes = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business = relationship("Business", back_populates="action_decisions")
    insight = relationship("BusinessInsight", back_populates="action_decisions")