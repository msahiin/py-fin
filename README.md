# 🚀 Trading Platform - Crypto & Forex Prediction System

A professional trading platform with advanced technical analysis, machine learning predictions, and risk management features.

## 📋 Features

### Core Features
- **Real-time Market Data**: Live price feeds from Binance, Coinbase, MT5, and OANDA
- **Technical Analysis**: 30+ technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, etc.)
- **Machine Learning Models**: LSTM, XGBoost, LightGBM for price predictions
- **Trading Signals**: AI-powered buy/sell/hold signals with confidence scores
- **Backtesting Engine**: Test strategies with historical data
- **Paper Trading**: Practice with demo accounts using real market data
- **Risk Management**: Position sizing, stop-loss, take-profit automation
- **WebSocket Real-time**: Live updates for prices, signals, and portfolio

### Advanced Features
- **Sentiment Analysis**: Social media and news sentiment tracking
- **On-Chain Metrics**: Whale movements, exchange flows (crypto)
- **Multi-timeframe Analysis**: 1m, 5m, 15m, 1h, 4h, 1d, 1w
- **Portfolio Analytics**: Performance tracking and risk exposure
- **Auto-trading**: Automated trade execution based on signals

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL + TimescaleDB
- **Cache**: Redis
- **Task Queue**: Celery
- **ML/Data**: TensorFlow, PyTorch, scikit-learn, pandas, TA-Lib

### Frontend
- **Framework**: React 18 + TypeScript
- **UI**: Material-UI / Ant Design
- **Charts**: TradingView Lightweight Charts
- **State**: Redux Toolkit
- **Real-time**: Socket.io

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd py-fin
```

2. **Setup environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

3. **Start with Docker Compose**
```bash
docker-compose up -d
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Manual Setup (Development)

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📊 Project Structure

```
trading-platform/
├── backend/
│   ├── api/                    # API routes and views
│   ├── ml_models/              # Machine learning models
│   ├── indicators/             # Technical indicators
│   ├── backtesting/            # Backtesting engine
│   ├── trading/                # Trading logic
│   ├── data/                   # Data collection
│   ├── websocket/              # WebSocket handlers
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration
│   ├── models.py               # Database models
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── services/           # API services
│   │   ├── store/              # Redux store
│   │   └── utils/              # Utilities
│   └── package.json
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🔧 Configuration

### Exchange API Keys

Edit `.env` file with your API credentials:

```env
# Binance
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# MetaTrader 5
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server
```

### Trading Settings

```env
MAX_POSITION_SIZE=0.1           # 10% of capital
RISK_PER_TRADE=0.02             # 2% risk per trade
MAX_OPEN_POSITIONS=5
PREDICTION_CONFIDENCE_THRESHOLD=0.75
```

## 📈 Usage Examples

### Get Trading Signals
```bash
curl http://localhost:8000/api/v1/signals?symbol=BTCUSDT
```

### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/client123');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Real-time update:', data);
};
```

### Run Backtest
```python
from backtesting.engine import BacktestEngine

backtest = BacktestEngine(
    strategy='rsi_sma',
    symbol='BTCUSDT',
    start_date='2023-01-01',
    end_date='2024-01-01',
    initial_capital=10000
)

results = backtest.run()
print(f"Sharpe Ratio: {results['sharpe_ratio']}")
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📚 API Documentation

After starting the backend, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔐 Security

- JWT-based authentication
- API key encryption (AES-256)
- Rate limiting
- SQL injection protection
- XSS protection
- 2FA support

## 📊 Development Roadmap

- [x] Phase 1: Infrastructure setup
- [ ] Phase 2: ML models & backtesting
- [ ] Phase 3: Trading system
- [ ] Phase 4: Frontend development
- [ ] Phase 5: Advanced features
- [ ] Phase 6: Testing & deployment

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.

## 📝 License

This project is licensed under the MIT License.

## 📞 Support

For issues and questions, please open an issue on GitHub.

---

**⚠️ Disclaimer**: This platform is for educational purposes. Trading cryptocurrencies and forex carries risk. Never trade with money you cannot afford to lose.
