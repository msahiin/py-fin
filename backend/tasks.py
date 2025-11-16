"""
Celery Tasks for Background Processing
"""
from celery import Celery
from config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'trading_platform',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)


@celery_app.task(name='tasks.collect_market_data')
def collect_market_data(symbols: list, interval: str = '1h'):
    """
    Collect market data for symbols

    Args:
        symbols: List of trading symbols
        interval: Timeframe
    """
    from data.collectors import DataAggregator

    logger.info(f"Collecting market data for {len(symbols)} symbols")

    aggregator = DataAggregator()
    results = {}

    for symbol in symbols:
        try:
            df = aggregator.get_data(
                symbol=symbol,
                source='binance',
                interval=interval
            )
            results[symbol] = len(df)
            logger.info(f"Collected {len(df)} candles for {symbol}")
        except Exception as e:
            logger.error(f"Error collecting data for {symbol}: {e}")
            results[symbol] = 0

    return results


@celery_app.task(name='tasks.train_ml_model')
def train_ml_model(model_type: str, symbol: str, data_params: dict):
    """
    Train machine learning model

    Args:
        model_type: Type of model (lstm, xgboost, etc.)
        symbol: Trading symbol
        data_params: Data collection parameters
    """
    logger.info(f"Training {model_type} model for {symbol}")

    from data.collectors import DataAggregator
    from data.processors import DataProcessor

    # Collect data
    aggregator = DataAggregator()
    df = aggregator.get_data(
        symbol=symbol,
        source='binance',
        **data_params
    )

    # Process data
    processor = DataProcessor()
    df = processor.clean_data(df)
    df = processor.add_technical_indicators(df)
    df = processor.add_price_features(df)
    df = processor.create_target(df)

    # Train model based on type
    if model_type == 'lstm':
        from ml_models.lstm_model import LSTMPredictor

        X, y = processor.prepare_ml_data(df, target_col='target_price')

        model = LSTMPredictor(sequence_length=60)
        X_train, X_val, X_test, y_train, y_val, y_test = model.prepare_data(y)

        model.train(
            X_train, y_train,
            X_val, y_val,
            epochs=50,
            save_path=f'ml_models/saved_models/{symbol}_lstm.h5'
        )

        metrics = model.evaluate(X_test, y_test)

        logger.info(f"LSTM model trained for {symbol}: {metrics}")

        return {'status': 'success', 'metrics': metrics}

    elif model_type == 'xgboost':
        from ml_models.xgboost_model import XGBoostClassifier

        X, y = processor.prepare_ml_data(df, target_col='target')

        model = XGBoostClassifier()
        # Split data
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )

        model.train(X_train, y_train)
        metrics = model.evaluate(X_test, y_test)

        model.save(f'ml_models/saved_models/{symbol}_xgboost.pkl')

        logger.info(f"XGBoost model trained for {symbol}: {metrics}")

        return {'status': 'success', 'metrics': metrics}

    return {'status': 'error', 'message': f'Unknown model type: {model_type}'}


@celery_app.task(name='tasks.generate_trading_signal')
def generate_trading_signal(symbol: str, timeframe: str = '1h'):
    """
    Generate trading signal for symbol

    Args:
        symbol: Trading symbol
        timeframe: Timeframe

    Returns:
        Signal dictionary
    """
    logger.info(f"Generating signal for {symbol} on {timeframe}")

    from data.collectors import DataAggregator
    from data.processors import DataProcessor
    from indicators.technical import TechnicalIndicators, IndicatorSignals

    # Collect recent data
    aggregator = DataAggregator()
    df = aggregator.get_data(
        symbol=symbol,
        source='binance',
        interval=timeframe
    )

    # Process data
    processor = DataProcessor()
    df = processor.clean_data(df)
    df = processor.add_technical_indicators(df)

    # Calculate indicators
    indicators = TechnicalIndicators()
    signal_generator = IndicatorSignals()

    # Get signals from multiple indicators
    signals = []

    # RSI signal
    rsi_signal = signal_generator.rsi_signal(df['rsi'])
    signals.append(rsi_signal)

    # MACD signal
    macd_signal = signal_generator.macd_signal(df['macd'], df['macd_signal'])
    signals.append(macd_signal)

    # MA crossover signal
    ma_signal = signal_generator.moving_average_signal(
        df['close'], df['sma_20'], df['sma_50']
    )
    signals.append(ma_signal)

    # Bollinger Bands signal
    bb_signal = signal_generator.bollinger_signal(
        df['close'], df['bb_upper'], df['bb_lower']
    )
    signals.append(bb_signal)

    # Combine signals
    combined = signal_generator.combine_signals(signals)

    signal = {
        'symbol': symbol,
        'timeframe': timeframe,
        'direction': combined['direction'],
        'confidence': combined['confidence'],
        'price': float(df['close'].iloc[-1]),
        'indicators': {
            'rsi': float(df['rsi'].iloc[-1]),
            'macd': float(df['macd'].iloc[-1]),
            'sma_20': float(df['sma_20'].iloc[-1]),
            'sma_50': float(df['sma_50'].iloc[-1]),
        },
        'timestamp': df.index[-1].isoformat()
    }

    logger.info(f"Signal generated: {signal['direction']} with {signal['confidence']:.1f}% confidence")

    return signal


@celery_app.task(name='tasks.run_backtest')
def run_backtest(strategy_params: dict, data_params: dict):
    """
    Run backtest for strategy

    Args:
        strategy_params: Strategy parameters
        data_params: Data parameters

    Returns:
        Backtest results
    """
    logger.info(f"Running backtest: {strategy_params.get('name', 'Unnamed')}")

    from data.collectors import DataAggregator
    from data.processors import DataProcessor
    from backtesting.engine import BacktestEngine

    # Collect data
    aggregator = DataAggregator()
    df = aggregator.get_data(**data_params)

    # Process data
    processor = DataProcessor()
    df = processor.clean_data(df)
    df = processor.add_technical_indicators(df)

    # Simple RSI strategy
    def rsi_strategy(data, **params):
        """Example RSI strategy"""
        if len(data) < 2:
            return None

        rsi = data['rsi'].iloc[-1]
        price = data['close'].iloc[-1]

        if rsi < params.get('oversold', 30):
            return {
                'action': 'buy',
                'stop_loss': price * 0.98,
                'take_profit': price * 1.04
            }
        elif rsi > params.get('overbought', 70):
            return {
                'action': 'sell'
            }

        return None

    # Run backtest
    engine = BacktestEngine(
        initial_capital=strategy_params.get('initial_capital', 10000),
        commission=strategy_params.get('commission', 0.001),
        slippage=strategy_params.get('slippage', 0.0005)
    )

    results = engine.run(df, rsi_strategy, **strategy_params)

    logger.info(f"Backtest completed: {results.get('total_trades', 0)} trades")

    return results


# Periodic tasks configuration
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""

    # Collect market data every hour
    sender.add_periodic_task(
        3600.0,  # 1 hour
        collect_market_data.s(settings.SUPPORTED_SYMBOLS),
        name='collect_market_data_hourly'
    )

    # Generate signals every 15 minutes
    sender.add_periodic_task(
        900.0,  # 15 minutes
        generate_trading_signal.s('BTCUSDT', '1h'),
        name='generate_btc_signal'
    )
