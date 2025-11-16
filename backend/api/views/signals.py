"""
Trading Signals API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import User, Signal, SignalDirection
from api.schemas import SignalResponse, SignalFilter
from auth import get_current_user
from tasks import generate_trading_signal

router = APIRouter()


@router.get("/", response_model=List[SignalResponse])
def get_signals(
    symbol: Optional[str] = None,
    direction: Optional[str] = None,
    min_confidence: float = Query(0, ge=0, le=100),
    timeframe: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get trading signals with optional filters
    """
    query = db.query(Signal)

    # Apply filters
    if symbol:
        query = query.filter(Signal.symbol == symbol)

    if direction:
        query = query.filter(Signal.direction == direction)

    if min_confidence > 0:
        query = query.filter(Signal.confidence >= min_confidence)

    if timeframe:
        query = query.filter(Signal.timeframe == timeframe)

    query = query.filter(Signal.is_active == is_active)

    # Order by created_at descending
    query = query.order_by(Signal.created_at.desc())

    # Limit results
    signals = query.limit(limit).all()

    return signals


@router.get("/{signal_id}", response_model=SignalResponse)
def get_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific signal by ID
    """
    signal = db.query(Signal).filter(Signal.id == signal_id).first()

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    return signal


@router.post("/generate/{symbol}")
def generate_signal(
    symbol: str,
    timeframe: str = "1h",
    current_user: User = Depends(get_current_user)
):
    """
    Generate new trading signal for symbol
    """
    # Trigger Celery task
    task = generate_trading_signal.delay(symbol, timeframe)

    return {
        "message": f"Signal generation started for {symbol}",
        "task_id": task.id,
        "symbol": symbol,
        "timeframe": timeframe
    }


@router.get("/active/count")
def get_active_signals_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get count of active signals
    """
    count = db.query(Signal).filter(Signal.is_active == True).count()

    return {"active_signals": count}


@router.delete("/{signal_id}")
def deactivate_signal(
    signal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate a signal
    """
    signal = db.query(Signal).filter(Signal.id == signal_id).first()

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    signal.is_active = False
    db.commit()

    return {"message": "Signal deactivated", "signal_id": signal_id}
