"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============= Auth Schemas =============

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    email: str
    username: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============= Market Data Schemas =============

class MarketDataRequest(BaseModel):
    """Schema for market data request"""
    symbol: str
    interval: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 1000


class PriceUpdate(BaseModel):
    """Schema for real-time price update"""
    symbol: str
    price: float
    change_24h: float
    volume: float
    timestamp: datetime


# ============= Signal Schemas =============

class SignalDirection(str, Enum):
    """Signal direction enum"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class SignalCreate(BaseModel):
    """Schema for creating a signal"""
    symbol: str
    direction: SignalDirection
    confidence: float = Field(..., ge=0, le=100)
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timeframe: str = "1h"
    indicators: Optional[Dict[str, Any]] = None
    model_predictions: Optional[Dict[str, Any]] = None


class SignalResponse(BaseModel):
    """Schema for signal response"""
    id: int
    symbol: str
    direction: str
    confidence: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    timeframe: str
    indicators: Optional[Dict[str, Any]]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SignalFilter(BaseModel):
    """Schema for filtering signals"""
    symbol: Optional[str] = None
    direction: Optional[SignalDirection] = None
    min_confidence: Optional[float] = 0
    timeframe: Optional[str] = None
    is_active: bool = True


# ============= Trading Schemas =============

class OrderCreate(BaseModel):
    """Schema for creating an order"""
    symbol: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: float = Field(..., gt=0)
    order_type: str = Field(default="MARKET", pattern="^(MARKET|LIMIT|STOP)$")
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float]
    status: str
    created_at: datetime


class PositionResponse(BaseModel):
    """Schema for position response"""
    symbol: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_percent: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    opened_at: datetime


class AccountSummary(BaseModel):
    """Schema for account summary"""
    account_id: str
    balance: float
    equity: float
    margin_used: float
    free_margin: float
    daily_pnl: float
    total_pnl: float
    total_return: float
    open_positions: int
    total_trades: int


# ============= Backtest Schemas =============

class BacktestCreate(BaseModel):
    """Schema for creating a backtest"""
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str
    initial_capital: float = 10000.0
    commission: float = 0.001
    slippage: float = 0.0005
    strategy_params: Dict[str, Any] = {}


class BacktestResponse(BaseModel):
    """Schema for backtest results"""
    id: int
    strategy_name: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    profit_factor: float
    created_at: datetime

    class Config:
        from_attributes = True


class BacktestMetrics(BaseModel):
    """Schema for detailed backtest metrics"""
    total_return: float
    annual_return: Optional[float]
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    calmar_ratio: float
    volatility: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    expectancy: float


# ============= Strategy Schemas =============

class StrategyCreate(BaseModel):
    """Schema for creating a strategy"""
    name: str
    description: Optional[str] = None
    parameters: Dict[str, Any]
    is_active: bool = False
    is_auto_trade: bool = False


class StrategyResponse(BaseModel):
    """Schema for strategy response"""
    id: int
    name: str
    description: Optional[str]
    parameters: Dict[str, Any]
    is_active: bool
    is_auto_trade: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============= ML Model Schemas =============

class ModelTrainRequest(BaseModel):
    """Schema for model training request"""
    model_type: str = Field(..., pattern="^(lstm|xgboost|lightgbm)$")
    symbol: str
    start_date: str
    end_date: str
    interval: str = "1h"
    parameters: Optional[Dict[str, Any]] = None


class ModelPredictionRequest(BaseModel):
    """Schema for model prediction request"""
    symbol: str
    model_type: str
    timeframe: str = "1h"


class ModelPredictionResponse(BaseModel):
    """Schema for model prediction response"""
    symbol: str
    prediction: str  # buy, sell, hold
    confidence: float
    predicted_price: Optional[float]
    timestamp: datetime


# ============= Portfolio Schemas =============

class PortfolioSummary(BaseModel):
    """Schema for portfolio summary"""
    total_value: float
    total_pnl: float
    total_return: float
    positions: List[PositionResponse]
    allocation: Dict[str, float]


# ============= WebSocket Schemas =============

class WSMessage(BaseModel):
    """Schema for WebSocket messages"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SubscribeRequest(BaseModel):
    """Schema for WebSocket subscription"""
    topic: str
    symbols: Optional[List[str]] = None
