from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import business, sales, reviews, forecast, insights

# Initialize the Growth360 FastAPI application
app = FastAPI(
    title="Growth360 API",
    description="Backend API for Growth360 — AI-powered business growth assistant for local businesses.",
    version="1.0.0",
)

# Configure CORS so the React + Vite frontend can communicate seamlessly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all modular API routers
app.include_router(business.router)
app.include_router(sales.router)
app.include_router(reviews.router)
app.include_router(forecast.router)
app.include_router(insights.router)


@app.get("/", tags=["General"])
def read_root():
    """Root endpoint to verify the Growth360 backend is running."""
    return {
        "project": "Growth360",
        "message": "Welcome to the Growth360 Backend API",
        "documentation": "/docs",
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint to confirm server status."""
    return {
        "status": "healthy",
        "service": "Growth360 Backend",
    }