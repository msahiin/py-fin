"""
Trading API endpoints (Paper Trading)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, TradingAccount, Position, AccountType
from api.schemas import (
    OrderCreate,
    OrderResponse,
    PositionResponse,
    AccountSummary
)
from auth import get_current_user
from trading.paper_trading import PaperTradingAccount, Order as PaperOrder
from data.collectors import BinanceCollector

router = APIRouter()

# In-memory storage for paper trading accounts (in production, use Redis)
active_accounts = {}


def get_or_create_paper_account(user_id: int, account_id: int, db: Session) -> PaperTradingAccount:
    """Get or create paper trading account instance"""
    key = f"{user_id}_{account_id}"

    if key not in active_accounts:
        account = db.query(TradingAccount).filter(
            TradingAccount.id == account_id,
            TradingAccount.user_id == user_id
        ).first()

        if not account:
            raise HTTPException(status_code=404, detail="Trading account not found")

        active_accounts[key] = PaperTradingAccount(
            initial_balance=account.initial_balance,
            commission_rate=0.001,
            slippage_rate=0.0005
        )

    return active_accounts[key]


@router.get("/accounts", response_model=List[dict])
def get_trading_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all trading accounts for current user
    """
    accounts = db.query(TradingAccount).filter(
        TradingAccount.user_id == current_user.id
    ).all()

    return [
        {
            "id": acc.id,
            "name": acc.name,
            "type": acc.account_type.value,
            "balance": acc.current_balance,
            "equity": acc.equity,
            "is_active": acc.is_active,
            "created_at": acc.created_at
        }
        for acc in accounts
    ]


@router.get("/accounts/{account_id}/summary", response_model=AccountSummary)
def get_account_summary(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get account summary with current stats
    """
    paper_account = get_or_create_paper_account(current_user.id, account_id, db)
    summary = paper_account.get_account_summary()

    return summary


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new trading order
    """
    # Get paper trading account
    paper_account = get_or_create_paper_account(current_user.id, account_id, db)

    # Get current price
    collector = BinanceCollector()
    price_data = await collector.get_realtime_price(order_data.symbol)

    if not price_data:
        raise HTTPException(status_code=400, detail="Could not fetch current price")

    current_price = price_data['price']

    # Create order in paper account
    order = paper_account.create_order(
        symbol=order_data.symbol,
        side=order_data.side,
        quantity=order_data.quantity,
        order_type=order_data.order_type,
        price=order_data.price,
        stop_loss=order_data.stop_loss,
        take_profit=order_data.take_profit
    )

    # Execute market orders immediately
    if order_data.order_type == "MARKET":
        success = paper_account.execute_order(order, current_price)

        if not success:
            raise HTTPException(status_code=400, detail="Order execution failed")

    # Update database account
    db_account = db.query(TradingAccount).filter(
        TradingAccount.id == account_id
    ).first()

    if db_account:
        db_account.current_balance = paper_account.balance
        db_account.equity = paper_account.equity
        db_account.margin_used = paper_account.margin_used
        db.commit()

    return {
        "id": order.id,
        "symbol": order.symbol,
        "side": order.side,
        "order_type": order.order_type,
        "quantity": order.quantity,
        "price": order.filled_price or order.price,
        "status": order.status,
        "created_at": order.created_at
    }


@router.get("/positions", response_model=List[PositionResponse])
def get_positions(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all open positions
    """
    paper_account = get_or_create_paper_account(current_user.id, account_id, db)
    positions = paper_account.get_positions()

    return positions


@router.get("/history")
def get_trade_history(
    account_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get trade history
    """
    paper_account = get_or_create_paper_account(current_user.id, account_id, db)
    history = paper_account.get_trade_history()

    return history[:limit]


@router.post("/positions/{symbol}/close")
async def close_position(
    symbol: str,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Close a specific position
    """
    paper_account = get_or_create_paper_account(current_user.id, account_id, db)

    if symbol not in paper_account.positions:
        raise HTTPException(status_code=404, detail="Position not found")

    # Get current price
    collector = BinanceCollector()
    price_data = await collector.get_realtime_price(symbol)

    if not price_data:
        raise HTTPException(status_code=400, detail="Could not fetch current price")

    current_price = price_data['price']
    position = paper_account.positions[symbol]

    # Create close order
    order = paper_account.create_order(
        symbol=symbol,
        side="SELL" if position.side == "LONG" else "BUY",
        quantity=position.quantity,
        order_type="MARKET"
    )

    success = paper_account.execute_order(order, current_price)

    if not success:
        raise HTTPException(status_code=400, detail="Failed to close position")

    # Update database
    db_account = db.query(TradingAccount).filter(
        TradingAccount.id == account_id
    ).first()

    if db_account:
        db_account.current_balance = paper_account.balance
        db_account.equity = paper_account.equity
        db.commit()

    return {"message": f"Position {symbol} closed", "price": current_price}


@router.post("/accounts/{account_id}/update-prices")
async def update_account_prices(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update positions with current market prices
    """
    paper_account = get_or_create_paper_account(current_user.id, account_id, db)

    if not paper_account.positions:
        return {"message": "No positions to update"}

    collector = BinanceCollector()

    for symbol, position in paper_account.positions.items():
        price_data = await collector.get_realtime_price(symbol)
        if price_data:
            paper_account.update_positions(symbol, price_data['price'])

    # Update database
    db_account = db.query(TradingAccount).filter(
        TradingAccount.id == account_id
    ).first()

    if db_account:
        db_account.equity = paper_account.equity
        db.commit()

    return {
        "message": "Prices updated",
        "equity": paper_account.equity,
        "positions_count": len(paper_account.positions)
    }
