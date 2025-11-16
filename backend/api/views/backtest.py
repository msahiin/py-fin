"""
Backtesting API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import get_db
from models import User, BacktestResult, Strategy
from api.schemas import BacktestCreate, BacktestResponse, BacktestMetrics
from auth import get_current_user
from tasks import run_backtest as run_backtest_task

router = APIRouter()


@router.post("/run")
async def run_backtest(
    backtest_data: BacktestCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run a backtest (async via Celery)
    """
    # Prepare data parameters
    data_params = {
        'symbol': backtest_data.symbol,
        'source': 'binance',
        'interval': '1h',
        'start_date': backtest_data.start_date,
        'end_date': backtest_data.end_date
    }

    # Prepare strategy parameters
    strategy_params = {
        'name': backtest_data.strategy_name,
        'initial_capital': backtest_data.initial_capital,
        'commission': backtest_data.commission,
        'slippage': backtest_data.slippage,
        **backtest_data.strategy_params
    }

    # Start Celery task
    task = run_backtest_task.delay(strategy_params, data_params)

    return {
        "message": "Backtest started",
        "task_id": task.id,
        "strategy": backtest_data.strategy_name,
        "symbol": backtest_data.symbol
    }


@router.post("/run-sync", response_model=dict)
def run_backtest_sync(
    backtest_data: BacktestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run a backtest synchronously (for quick tests)
    """
    from data.collectors import DataAggregator
    from data.processors import DataProcessor
    from backtesting.engine import BacktestEngine, PositionSide

    # Collect data
    aggregator = DataAggregator()
    df = aggregator.get_data(
        symbol=backtest_data.symbol,
        source='binance',
        interval='1h',
        start_date=backtest_data.start_date,
        end_date=backtest_data.end_date
    )

    if df.empty:
        raise HTTPException(status_code=400, detail="No data available for backtest")

    # Process data
    processor = DataProcessor()
    df = processor.clean_data(df)
    df = processor.add_technical_indicators(df)

    # Define strategy
    def rsi_strategy(data, **params):
        """Simple RSI strategy"""
        if len(data) < 2:
            return None

        rsi = data['rsi'].iloc[-1]
        price = data['close'].iloc[-1]
        atr = data['atr'].iloc[-1] if 'atr' in data.columns else price * 0.02

        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)

        if rsi < oversold:
            return {
                'action': 'buy',
                'stop_loss': price - (atr * 2),
                'take_profit': price + (atr * 4)
            }
        elif rsi > overbought:
            return {'action': 'sell'}

        return None

    # Run backtest
    engine = BacktestEngine(
        initial_capital=backtest_data.initial_capital,
        commission=backtest_data.commission,
        slippage=backtest_data.slippage
    )

    results = engine.run(df, rsi_strategy, **backtest_data.strategy_params)

    # Save to database
    strategy = db.query(Strategy).filter(
        Strategy.user_id == current_user.id,
        Strategy.name == backtest_data.strategy_name
    ).first()

    if not strategy:
        # Create strategy if doesn't exist
        strategy = Strategy(
            user_id=current_user.id,
            name=backtest_data.strategy_name,
            parameters=backtest_data.strategy_params
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)

    # Create backtest result
    backtest_result = BacktestResult(
        strategy_id=strategy.id,
        name=f"{backtest_data.strategy_name} - {backtest_data.symbol}",
        start_date=backtest_data.start_date,
        end_date=backtest_data.end_date,
        initial_capital=backtest_data.initial_capital,
        total_return=results.get('total_return', 0),
        annual_return=results.get('annual_return'),
        sharpe_ratio=results.get('sharpe_ratio', 0),
        max_drawdown=results.get('max_drawdown', 0),
        win_rate=results.get('win_rate', 0),
        profit_factor=results.get('profit_factor', 0) if results.get('profit_factor') != 'inf' else 999,
        total_trades=results.get('total_trades', 0),
        metrics=results
    )

    db.add(backtest_result)
    db.commit()
    db.refresh(backtest_result)

    return {
        "backtest_id": backtest_result.id,
        "results": results
    }


@router.get("/results", response_model=List[BacktestResponse])
def get_backtest_results(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get backtest results for current user
    """
    # Get user's strategies
    strategy_ids = [s.id for s in db.query(Strategy).filter(
        Strategy.user_id == current_user.id
    ).all()]

    if not strategy_ids:
        return []

    # Get backtest results
    results = db.query(BacktestResult).filter(
        BacktestResult.strategy_id.in_(strategy_ids)
    ).order_by(BacktestResult.created_at.desc()).limit(limit).all()

    return [
        {
            "id": r.id,
            "strategy_name": r.name,
            "total_return": r.total_return,
            "sharpe_ratio": r.sharpe_ratio,
            "max_drawdown": r.max_drawdown,
            "win_rate": r.win_rate,
            "total_trades": r.total_trades,
            "profit_factor": r.profit_factor,
            "created_at": r.created_at
        }
        for r in results
    ]


@router.get("/results/{backtest_id}")
def get_backtest_detail(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed backtest results
    """
    backtest = db.query(BacktestResult).filter(
        BacktestResult.id == backtest_id
    ).first()

    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    # Verify ownership
    strategy = db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": backtest.id,
        "name": backtest.name,
        "start_date": backtest.start_date,
        "end_date": backtest.end_date,
        "initial_capital": backtest.initial_capital,
        "metrics": backtest.metrics,
        "equity_curve": backtest.equity_curve,
        "trades": backtest.trades,
        "created_at": backtest.created_at
    }


@router.delete("/results/{backtest_id}")
def delete_backtest(
    backtest_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a backtest result
    """
    backtest = db.query(BacktestResult).filter(
        BacktestResult.id == backtest_id
    ).first()

    if not backtest:
        raise HTTPException(status_code=404, detail="Backtest not found")

    # Verify ownership
    strategy = db.query(Strategy).filter(Strategy.id == backtest.strategy_id).first()
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(backtest)
    db.commit()

    return {"message": "Backtest deleted", "id": backtest_id}
