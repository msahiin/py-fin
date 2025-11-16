"""
API Routes - Main Router
"""
from fastapi import APIRouter

router = APIRouter()

# Import sub-routers (will be created)
# from .views.users import router as users_router
# from .views.signals import router as signals_router
# from .views.trading import router as trading_router
# from .views.backtest import router as backtest_router

# Include sub-routers
# router.include_router(users_router, prefix="/users", tags=["users"])
# router.include_router(signals_router, prefix="/signals", tags=["signals"])
# router.include_router(trading_router, prefix="/trading", tags=["trading"])
# router.include_router(backtest_router, prefix="/backtest", tags=["backtest"])


@router.get("/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "operational",
        "version": "1.0.0"
    }
