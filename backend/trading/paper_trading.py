"""
Paper Trading System
Simulated trading with real market data
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class Order:
    """Order data class"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str = ""
    side: str = ""  # BUY or SELL
    order_type: str = "MARKET"  # MARKET, LIMIT, STOP
    quantity: float = 0.0
    price: Optional[float] = None
    stop_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: str = "PENDING"  # PENDING, FILLED, CANCELLED
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    filled_price: Optional[float] = None


@dataclass
class Position:
    """Position data class"""
    symbol: str
    side: str  # LONG or SHORT
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    unrealized_pnl: float = 0.0
    unrealized_pnl_percent: float = 0.0
    opened_at: datetime = field(default_factory=datetime.now)


class PaperTradingAccount:
    """
    Paper trading account with realistic simulation
    """

    def __init__(
        self,
        initial_balance: float = 10000.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        leverage: int = 1
    ):
        """
        Initialize paper trading account

        Args:
            initial_balance: Starting balance
            commission_rate: Commission rate (0.001 = 0.1%)
            slippage_rate: Slippage rate (0.0005 = 0.05%)
            leverage: Maximum leverage
        """
        self.account_id = str(uuid.uuid4())
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.leverage = leverage

        self.positions: Dict[str, Position] = {}
        self.open_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.trade_history: List[Dict] = []

        self.margin_used = 0.0
        self.free_margin = initial_balance

        self.daily_pnl = 0.0
        self.total_pnl = 0.0

        logger.info(f"Paper trading account created: {self.account_id}, Balance: ${initial_balance}")

    def create_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Order:
        """
        Create a new order

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Order quantity
            order_type: MARKET, LIMIT, or STOP
            price: Limit/stop price
            stop_loss: Stop loss price
            take_profit: Take profit price

        Returns:
            Order object
        """
        order = Order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status="PENDING"
        )

        self.open_orders[order.id] = order

        logger.info(f"Order created: {order.id} - {side} {quantity} {symbol}")

        return order

    def execute_order(self, order: Order, current_price: float) -> bool:
        """
        Execute an order

        Args:
            order: Order to execute
            current_price: Current market price

        Returns:
            True if successful, False otherwise
        """
        # Apply slippage
        if order.side == "BUY":
            execution_price = current_price * (1 + self.slippage_rate)
        else:
            execution_price = current_price * (1 - self.slippage_rate)

        # Calculate order value and commission
        order_value = execution_price * order.quantity
        commission = order_value * self.commission_rate

        # Check if enough free margin
        required_margin = order_value / self.leverage
        if required_margin + commission > self.free_margin:
            logger.warning(f"Insufficient margin for order {order.id}")
            order.status = "CANCELLED"
            return False

        # Execute order
        if order.side == "BUY":
            self._open_long_position(order, execution_price, commission)
        else:
            self._close_or_short_position(order, execution_price, commission)

        # Update order
        order.status = "FILLED"
        order.filled_at = datetime.now()
        order.filled_price = execution_price

        # Move to history
        if order.id in self.open_orders:
            del self.open_orders[order.id]
        self.order_history.append(order)

        # Update account
        self._update_account()

        logger.info(f"Order executed: {order.id} at ${execution_price}")

        return True

    def _open_long_position(self, order: Order, price: float, commission: float):
        """Open or add to long position"""
        symbol = order.symbol

        # Deduct commission
        self.balance -= commission

        if symbol in self.positions:
            # Add to existing position (average price)
            pos = self.positions[symbol]
            total_value = (pos.entry_price * pos.quantity) + (price * order.quantity)
            total_quantity = pos.quantity + order.quantity

            pos.entry_price = total_value / total_quantity
            pos.quantity = total_quantity

            logger.info(f"Added to position {symbol}: new avg price ${pos.entry_price}")
        else:
            # Create new position
            position = Position(
                symbol=symbol,
                side="LONG",
                quantity=order.quantity,
                entry_price=price,
                current_price=price,
                stop_loss=order.stop_loss,
                take_profit=order.take_profit
            )

            self.positions[symbol] = position

            logger.info(f"Opened LONG position: {symbol} @ ${price}")

    def _close_or_short_position(self, order: Order, price: float, commission: float):
        """Close long position or open short"""
        symbol = order.symbol

        if symbol in self.positions and self.positions[symbol].side == "LONG":
            # Close long position
            pos = self.positions[symbol]

            # Calculate PnL
            pnl = (price - pos.entry_price) * min(order.quantity, pos.quantity)
            pnl -= commission

            # Update balance
            self.balance += (pos.entry_price * min(order.quantity, pos.quantity)) + pnl

            # Record trade
            self.trade_history.append({
                'symbol': symbol,
                'side': 'LONG',
                'entry_price': pos.entry_price,
                'exit_price': price,
                'quantity': min(order.quantity, pos.quantity),
                'pnl': pnl,
                'pnl_percent': (pnl / (pos.entry_price * min(order.quantity, pos.quantity))) * 100,
                'opened_at': pos.opened_at,
                'closed_at': datetime.now()
            })

            # Update total PnL
            self.total_pnl += pnl
            self.daily_pnl += pnl

            # Update or close position
            if order.quantity >= pos.quantity:
                del self.positions[symbol]
                logger.info(f"Closed LONG position: {symbol}, PnL: ${pnl:.2f}")
            else:
                pos.quantity -= order.quantity
                logger.info(f"Partially closed LONG position: {symbol}, PnL: ${pnl:.2f}")

        else:
            # Open short position (if shorting is enabled)
            logger.warning(f"Short selling not implemented for {symbol}")

    def update_positions(self, symbol: str, current_price: float):
        """
        Update position with current price

        Args:
            symbol: Trading symbol
            current_price: Current market price
        """
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.current_price = current_price

            # Calculate unrealized PnL
            if pos.side == "LONG":
                pos.unrealized_pnl = (current_price - pos.entry_price) * pos.quantity
            else:
                pos.unrealized_pnl = (pos.entry_price - current_price) * pos.quantity

            pos.unrealized_pnl_percent = (pos.unrealized_pnl / (pos.entry_price * pos.quantity)) * 100

            # Check stop loss and take profit
            if pos.stop_loss and ((pos.side == "LONG" and current_price <= pos.stop_loss) or
                                   (pos.side == "SHORT" and current_price >= pos.stop_loss)):
                logger.info(f"Stop loss hit for {symbol} at ${current_price}")
                self._auto_close_position(symbol, current_price, "STOP_LOSS")

            elif pos.take_profit and ((pos.side == "LONG" and current_price >= pos.take_profit) or
                                      (pos.side == "SHORT" and current_price <= pos.take_profit)):
                logger.info(f"Take profit hit for {symbol} at ${current_price}")
                self._auto_close_position(symbol, current_price, "TAKE_PROFIT")

        self._update_account()

    def _auto_close_position(self, symbol: str, price: float, reason: str):
        """Automatically close position"""
        if symbol in self.positions:
            pos = self.positions[symbol]
            order = self.create_order(
                symbol=symbol,
                side="SELL" if pos.side == "LONG" else "BUY",
                quantity=pos.quantity,
                order_type="MARKET"
            )
            self.execute_order(order, price)

    def _update_account(self):
        """Update account equity and margins"""
        # Calculate total unrealized PnL
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())

        # Update equity
        self.equity = self.balance + unrealized_pnl

        # Calculate margin used
        self.margin_used = sum(
            pos.entry_price * pos.quantity / self.leverage
            for pos in self.positions.values()
        )

        # Calculate free margin
        self.free_margin = self.equity - self.margin_used

    def get_account_summary(self) -> Dict:
        """
        Get account summary

        Returns:
            Dictionary with account information
        """
        return {
            'account_id': self.account_id,
            'balance': round(self.balance, 2),
            'equity': round(self.equity, 2),
            'margin_used': round(self.margin_used, 2),
            'free_margin': round(self.free_margin, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'total_pnl': round(self.total_pnl, 2),
            'total_return': round((self.equity - self.initial_balance) / self.initial_balance * 100, 2),
            'open_positions': len(self.positions),
            'total_trades': len(self.trade_history)
        }

    def get_positions(self) -> List[Dict]:
        """Get all open positions"""
        return [
            {
                'symbol': pos.symbol,
                'side': pos.side,
                'quantity': pos.quantity,
                'entry_price': pos.entry_price,
                'current_price': pos.current_price,
                'unrealized_pnl': round(pos.unrealized_pnl, 2),
                'unrealized_pnl_percent': round(pos.unrealized_pnl_percent, 2),
                'stop_loss': pos.stop_loss,
                'take_profit': pos.take_profit,
                'opened_at': pos.opened_at.isoformat()
            }
            for pos in self.positions.values()
        ]

    def get_trade_history(self) -> List[Dict]:
        """Get trade history"""
        return [
            {
                **trade,
                'opened_at': trade['opened_at'].isoformat(),
                'closed_at': trade['closed_at'].isoformat()
            }
            for trade in self.trade_history
        ]
