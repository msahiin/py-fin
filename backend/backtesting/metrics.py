"""
Backtest Performance Metrics
"""
import numpy as np
import pandas as pd
from typing import List, Dict
from datetime import datetime


class BacktestMetrics:
    """Calculate performance metrics for backtests"""

    @staticmethod
    def calculate_metrics(
        equity_curve: List[float],
        trades: List,
        initial_capital: float,
        risk_free_rate: float = 0.02
    ) -> Dict:
        """
        Calculate comprehensive backtest metrics

        Args:
            equity_curve: List of equity values
            trades: List of closed trades
            initial_capital: Initial capital
            risk_free_rate: Annual risk-free rate

        Returns:
            Dictionary of metrics
        """
        if not trades:
            return {
                'total_trades': 0,
                'total_return': 0.0,
                'message': 'No trades executed'
            }

        # Convert to arrays
        equity = np.array(equity_curve)
        returns = np.diff(equity) / equity[:-1]

        # Winning and losing trades
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]

        # Basic metrics
        total_return = ((equity[-1] - initial_capital) / initial_capital) * 100
        total_trades = len(trades)
        winning_count = len(winning_trades)
        losing_count = len(losing_trades)
        win_rate = (winning_count / total_trades) * 100 if total_trades > 0 else 0

        # PnL metrics
        total_pnl = sum(t.pnl for t in trades)
        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        avg_win = gross_profit / winning_count if winning_count > 0 else 0
        avg_loss = gross_loss / losing_count if losing_count > 0 else 0

        largest_win = max([t.pnl for t in trades]) if trades else 0
        largest_loss = min([t.pnl for t in trades]) if trades else 0

        # Drawdown
        max_drawdown, max_dd_duration = BacktestMetrics.calculate_drawdown(equity)

        # Risk-adjusted returns
        sharpe_ratio = BacktestMetrics.calculate_sharpe_ratio(returns, risk_free_rate)
        sortino_ratio = BacktestMetrics.calculate_sortino_ratio(returns, risk_free_rate)
        calmar_ratio = abs(total_return / max_drawdown) if max_drawdown != 0 else 0

        # Volatility
        volatility = np.std(returns) * np.sqrt(252) * 100  # Annualized

        # Consecutive wins/losses
        consecutive_wins, consecutive_losses = BacktestMetrics.calculate_consecutive_trades(trades)

        # Recovery factor
        recovery_factor = total_pnl / abs(max_drawdown * initial_capital / 100) if max_drawdown != 0 else 0

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss)

        # Trade duration
        durations = [(t.exit_time - t.entry_time).total_seconds() / 3600 for t in trades if t.exit_time]
        avg_duration = np.mean(durations) if durations else 0

        metrics = {
            # Profitability Metrics
            'total_return': round(total_return, 2),
            'total_pnl': round(total_pnl, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),

            # Risk Metrics
            'sharpe_ratio': round(sharpe_ratio, 3),
            'sortino_ratio': round(sortino_ratio, 3),
            'calmar_ratio': round(calmar_ratio, 3),
            'max_drawdown': round(max_drawdown, 2),
            'max_drawdown_duration': max_dd_duration,
            'volatility': round(volatility, 2),

            # Trade Statistics
            'total_trades': total_trades,
            'winning_trades': winning_count,
            'losing_trades': losing_count,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 3) if profit_factor != float('inf') else 'inf',

            # Average Metrics
            'average_win': round(avg_win, 2),
            'average_loss': round(avg_loss, 2),
            'largest_win': round(largest_win, 2),
            'largest_loss': round(largest_loss, 2),
            'average_trade_duration_hours': round(avg_duration, 2),

            # Consistency Metrics
            'consecutive_wins': consecutive_wins,
            'consecutive_losses': consecutive_losses,
            'recovery_factor': round(recovery_factor, 3),
            'expectancy': round(expectancy, 2),

            # Equity Curve
            'final_equity': round(equity[-1], 2),
            'peak_equity': round(np.max(equity), 2)
        }

        return metrics

    @staticmethod
    def calculate_drawdown(equity: np.ndarray) -> tuple:
        """
        Calculate maximum drawdown and its duration

        Args:
            equity: Equity curve

        Returns:
            (max_drawdown_percent, duration_in_days)
        """
        running_max = np.maximum.accumulate(equity)
        drawdown = (equity - running_max) / running_max * 100

        max_drawdown = abs(np.min(drawdown))

        # Calculate duration
        in_drawdown = drawdown < 0
        duration = 0
        current_duration = 0
        max_duration = 0

        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0

        return max_drawdown, max_duration

    @staticmethod
    def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe Ratio

        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0

        # Annualize
        excess_returns = returns - (risk_free_rate / 252)  # Daily risk-free rate
        sharpe = np.mean(excess_returns) / np.std(returns) * np.sqrt(252)

        return sharpe

    @staticmethod
    def calculate_sortino_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sortino Ratio (uses only downside deviation)

        Args:
            returns: Array of returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sortino ratio
        """
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - (risk_free_rate / 252)
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return 0.0

        downside_std = np.std(downside_returns)

        if downside_std == 0:
            return 0.0

        sortino = np.mean(excess_returns) / downside_std * np.sqrt(252)

        return sortino

    @staticmethod
    def calculate_consecutive_trades(trades: List) -> tuple:
        """
        Calculate max consecutive wins and losses

        Args:
            trades: List of trades

        Returns:
            (max_consecutive_wins, max_consecutive_losses)
        """
        if not trades:
            return 0, 0

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    @staticmethod
    def generate_monthly_returns(equity_curve: List[float], timestamps: List[datetime]) -> pd.DataFrame:
        """
        Generate monthly returns table

        Args:
            equity_curve: Equity values
            timestamps: Corresponding timestamps

        Returns:
            DataFrame with monthly returns
        """
        df = pd.DataFrame({
            'timestamp': timestamps,
            'equity': equity_curve
        })

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

        # Resample to monthly
        monthly = df.resample('M').last()
        monthly['return'] = monthly['equity'].pct_change() * 100

        return monthly

    @staticmethod
    def generate_trade_journal(trades: List) -> pd.DataFrame:
        """
        Generate detailed trade journal

        Args:
            trades: List of trades

        Returns:
            DataFrame with trade details
        """
        journal = []

        for i, trade in enumerate(trades, 1):
            journal.append({
                'trade_number': i,
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'side': trade.side.value if hasattr(trade.side, 'value') else trade.side,
                'entry_price': trade.entry_price,
                'exit_price': trade.exit_price,
                'quantity': trade.quantity,
                'pnl': trade.pnl,
                'pnl_percent': trade.pnl_percent,
                'commission': trade.commission,
                'duration_hours': (trade.exit_time - trade.entry_time).total_seconds() / 3600 if trade.exit_time else None
            })

        return pd.DataFrame(journal)
