"""
Database Models
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class AccountType(str, enum.Enum):
    """Account type enumeration"""
    DEMO = "demo"
    LIVE = "live"


class PositionSide(str, enum.Enum):
    """Position side enumeration"""
    BUY = "buy"
    SELL = "sell"


class PositionStatus(str, enum.Enum):
    """Position status enumeration"""
    OPEN = "open"
    CLOSED = "closed"
    PENDING = "pending"


class SignalDirection(str, enum.Enum):
    """Signal direction enumeration"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Encrypted API keys stored as JSON
    api_keys = Column(JSON, default={})

    # Relationships
    accounts = relationship("TradingAccount", back_populates="user", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")


class TradingAccount(Base):
    """Trading account model"""
    __tablename__ = "trading_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False, default=AccountType.DEMO)
    initial_balance = Column(Float, nullable=False, default=10000.0)
    current_balance = Column(Float, nullable=False, default=10000.0)
    equity = Column(Float, nullable=False, default=10000.0)
    margin_used = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="accounts")
    positions = relationship("Position", back_populates="account", cascade="all, delete-orphan")


class Strategy(Base):
    """Trading strategy model"""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    parameters = Column(JSON, nullable=False)  # Strategy parameters as JSON
    is_active = Column(Boolean, default=False)
    is_auto_trade = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="strategies")
    backtests = relationship("BacktestResult", back_populates="strategy", cascade="all, delete-orphan")


class Signal(Base):
    """Trading signal model"""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False, index=True)
    direction = Column(Enum(SignalDirection), nullable=False)
    confidence = Column(Float, nullable=False)  # 0-100
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    timeframe = Column(String, nullable=False)  # 1h, 4h, 1d, etc.

    # Indicator values at signal generation
    indicators = Column(JSON)

    # Model predictions
    model_predictions = Column(JSON)

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class Position(Base):
    """Trading position model"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("trading_accounts.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    side = Column(Enum(PositionSide), nullable=False)
    status = Column(Enum(PositionStatus), nullable=False, default=PositionStatus.OPEN)

    entry_price = Column(Float, nullable=False)
    current_price = Column(Float)
    exit_price = Column(Float)

    quantity = Column(Float, nullable=False)
    leverage = Column(Integer, default=1)

    stop_loss = Column(Float)
    take_profit = Column(Float)

    commission = Column(Float, default=0.0)
    pnl = Column(Float, default=0.0)
    pnl_percentage = Column(Float, default=0.0)

    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))

    # Relationships
    account = relationship("TradingAccount", back_populates="positions")


class BacktestResult(Base):
    """Backtest result model"""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    name = Column(String, nullable=False)

    # Test parameters
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    initial_capital = Column(Float, nullable=False)

    # Performance metrics
    total_return = Column(Float)
    annual_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    total_trades = Column(Integer)

    # Detailed results stored as JSON
    metrics = Column(JSON)
    equity_curve = Column(JSON)
    trades = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")


class MLModel(Base):
    """Machine learning model metadata"""
    __tablename__ = "ml_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # LSTM, XGBoost, etc.
    version = Column(String, nullable=False)

    # Model parameters
    parameters = Column(JSON)

    # Performance metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)

    # Training info
    trained_at = Column(DateTime(timezone=True), server_default=func.now())
    training_samples = Column(Integer)

    # Model file path
    model_path = Column(String)

    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
