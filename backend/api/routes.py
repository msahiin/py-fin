"""
API Routes - Main Router
"""
from fastapi import APIRouter

from .views import auth, signals, trading, backtest, market, ml_models

router = APIRouter()

# Include all sub-routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(signals.router, prefix="/signals", tags=["Signals"])
router.include_router(trading.router, prefix="/trading", tags=["Trading"])
router.include_router(backtest.router, prefix="/backtest", tags=["Backtesting"])
router.include_router(market.router, prefix="/market", tags=["Market Data"])
router.include_router(ml_models.router, prefix="/ml", tags=["Machine Learning"])


@router.get("/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/v1/auth",
            "signals": "/api/v1/signals",
            "trading": "/api/v1/trading",
            "backtest": "/api/v1/backtest",
            "market": "/api/v1/market",
            "ml": "/api/v1/ml"
        }
    }
