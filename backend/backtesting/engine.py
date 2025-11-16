"""
Backtesting Engine
Test trading strategies with historical data
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from datetime import datetime
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class PositionSide(str, Enum):
    """Position side enumeration"""
    LONG = "long"
    SHORT = "short"


@dataclass
class Trade:
    """Trade data class"""
    entry_time: datetime
    exit_time: Optional[datetime]
    side: PositionSide
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    commission: float
    pnl: float = 0.0
    pnl_percent: float = 0.0
    status: str = "open"


class BacktestEngine:
    """
    Backtesting engine for trading strategies
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission: float = 0.001,
        slippage: float = 0.0005,
        position_size_method: str = 'percentage',
        max_position_size: float = 0.1,
        risk_per_trade: float = 0.02,
        max_open_positions: int = 3
    ):
        """
        Initialize backtesting engine

        Args:
            initial_capital: Starting capital
            commission: Commission rate (0.001 = 0.1%)
            slippage: Slippage rate (0.0005 = 0.05%)
            position_size_method: 'percentage' or 'fixed'
            max_position_size: Maximum position size (as percentage of capital)
            risk_per_trade: Risk per trade (as percentage of capital)
            max_open_positions: Maximum number of open positions
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.position_size_method = position_size_method
        self.max_position_size = max_position_size
        self.risk_per_trade = risk_per_trade
        self.max_open_positions = max_open_positions

        # State variables
        self.current_capital = initial_capital
        self.equity = initial_capital
        self.open_trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.equity_curve: List[float] = [initial_capital]
        self.timestamps: List[datetime] = []

    def calculate_position_size(
        self,
        price: float,
        stop_loss: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk management rules

        Args:
            price: Entry price
            stop_loss: Stop loss price

        Returns:
            Position size (quantity)
        """
        if self.position_size_method == 'percentage':
            # Simple percentage of capital
            position_value = self.current_capital * self.max_position_size
            quantity = position_value / price

        elif self.position_size_method == 'risk_based' and stop_loss:
            # Position size based on risk per trade
            risk_amount = self.current_capital * self.risk_per_trade
            price_risk = abs(price - stop_loss)
            quantity = risk_amount / price_risk

        else:
            # Default to fixed amount
            quantity = self.current_capital * self.max_position_size / price

        return quantity

    def enter_position(
        self,
        timestamp: datetime,
        price: float,
        side: PositionSide,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        quantity: Optional[float] = None
    ) -> Optional[Trade]:
        """
        Enter a new position

        Args:
            timestamp: Entry timestamp
            price: Entry price
            side: Position side (LONG/SHORT)
            stop_loss: Stop loss price
            take_profit: Take profit price
            quantity: Position size (if None, calculated automatically)

        Returns:
            Trade object or None if position cannot be opened
        """
        # Check if max positions reached
        if len(self.open_trades) >= self.max_open_positions:
            logger.debug(f"Max open positions reached ({self.max_open_positions})")
            return None

        # Calculate position size
        if quantity is None:
            quantity = self.calculate_position_size(price, stop_loss)

        # Apply slippage
        execution_price = price * (1 + self.slippage) if side == PositionSide.LONG else price * (1 - self.slippage)

        # Calculate commission
        position_value = execution_price * quantity
        commission = position_value * self.commission

        # Check if enough capital
        if position_value + commission > self.current_capital:
            logger.debug(f"Insufficient capital: need {position_value + commission}, have {self.current_capital}")
            return None

        # Create trade
        trade = Trade(
            entry_time=timestamp,
            exit_time=None,
            side=side,
            entry_price=execution_price,
            exit_price=None,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            commission=commission,
            status="open"
        )

        # Update capital
        self.current_capital -= commission

        # Add to open trades
        self.open_trades.append(trade)

        logger.debug(f"Opened {side.value} position at {execution_price}, qty: {quantity}")

        return trade

    def close_position(
        self,
        trade: Trade,
        timestamp: datetime,
        price: float
    ) -> Trade:
        """
        Close a position

        Args:
            trade: Trade to close
            timestamp: Exit timestamp
            price: Exit price

        Returns:
            Closed trade
        """
        # Apply slippage
        execution_price = price * (1 - self.slippage) if trade.side == PositionSide.LONG else price * (1 + self.slippage)

        # Calculate exit commission
        exit_value = execution_price * trade.quantity
        exit_commission = exit_value * self.commission

        # Calculate PnL
        if trade.side == PositionSide.LONG:
            pnl = (execution_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - execution_price) * trade.quantity

        pnl -= (trade.commission + exit_commission)

        # Update trade
        trade.exit_time = timestamp
        trade.exit_price = execution_price
        trade.pnl = pnl
        trade.pnl_percent = (pnl / (trade.entry_price * trade.quantity)) * 100
        trade.status = "closed"
        trade.commission += exit_commission

        # Update capital
        self.current_capital += exit_value + pnl

        # Move to closed trades
        self.open_trades.remove(trade)
        self.closed_trades.append(trade)

        logger.debug(f"Closed {trade.side.value} position at {execution_price}, PnL: {pnl:.2f}")

        return trade

    def update_positions(self, timestamp: datetime, current_price: float):
        """
        Update open positions and check for stop loss / take profit

        Args:
            timestamp: Current timestamp
            current_price: Current market price
        """
        positions_to_close = []

        for trade in self.open_trades:
            # Check stop loss
            if trade.stop_loss:
                if trade.side == PositionSide.LONG and current_price <= trade.stop_loss:
                    positions_to_close.append((trade, trade.stop_loss))
                elif trade.side == PositionSide.SHORT and current_price >= trade.stop_loss:
                    positions_to_close.append((trade, trade.stop_loss))

            # Check take profit
            if trade.take_profit:
                if trade.side == PositionSide.LONG and current_price >= trade.take_profit:
                    positions_to_close.append((trade, trade.take_profit))
                elif trade.side == PositionSide.SHORT and current_price <= trade.take_profit:
                    positions_to_close.append((trade, trade.take_profit))

        # Close positions that hit SL/TP
        for trade, exit_price in positions_to_close:
            self.close_position(trade, timestamp, exit_price)

    def calculate_equity(self, current_price: float) -> float:
        """
        Calculate current equity including open positions

        Args:
            current_price: Current market price

        Returns:
            Current equity
        """
        equity = self.current_capital

        # Add unrealized PnL from open positions
        for trade in self.open_trades:
            if trade.side == PositionSide.LONG:
                unrealized_pnl = (current_price - trade.entry_price) * trade.quantity
            else:
                unrealized_pnl = (trade.entry_price - current_price) * trade.quantity

            equity += unrealized_pnl

        return equity

    def run(
        self,
        data: pd.DataFrame,
        strategy: Callable,
        **strategy_params
    ) -> Dict:
        """
        Run backtest with given strategy

        Args:
            data: Historical OHLCV data
            strategy: Strategy function that returns signals
            **strategy_params: Strategy parameters

        Returns:
            Backtest results dictionary
        """
        logger.info(f"Starting backtest with {len(data)} data points")

        # Reset state
        self.current_capital = self.initial_capital
        self.equity = self.initial_capital
        self.open_trades = []
        self.closed_trades = []
        self.equity_curve = []
        self.timestamps = []

        # Run through historical data
        for i, (timestamp, row) in enumerate(data.iterrows()):
            current_price = row['close']

            # Update existing positions
            self.update_positions(timestamp, current_price)

            # Get strategy signal
            signal = strategy(data.iloc[:i+1], **strategy_params)

            # Execute signal
            if signal and signal['action'] == 'buy' and len(self.open_trades) < self.max_open_positions:
                self.enter_position(
                    timestamp=timestamp,
                    price=current_price,
                    side=PositionSide.LONG,
                    stop_loss=signal.get('stop_loss'),
                    take_profit=signal.get('take_profit')
                )

            elif signal and signal['action'] == 'sell':
                # Close all long positions
                for trade in self.open_trades.copy():
                    if trade.side == PositionSide.LONG:
                        self.close_position(trade, timestamp, current_price)

            # Calculate equity
            self.equity = self.calculate_equity(current_price)
            self.equity_curve.append(self.equity)
            self.timestamps.append(timestamp)

        # Close remaining positions
        for trade in self.open_trades.copy():
            self.close_position(trade, data.index[-1], data['close'].iloc[-1])

        logger.info(f"Backtest completed. Total trades: {len(self.closed_trades)}")

        # Calculate metrics
        return self.get_results()

    def get_results(self) -> Dict:
        """
        Calculate backtest results and metrics

        Returns:
            Dictionary with performance metrics
        """
        from .metrics import BacktestMetrics

        metrics = BacktestMetrics.calculate_metrics(
            equity_curve=self.equity_curve,
            trades=self.closed_trades,
            initial_capital=self.initial_capital
        )

        return metrics
