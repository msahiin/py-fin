import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// API endpoints
export const apiEndpoints = {
  // Market Data
  getMarketData: (symbol: string, interval: string) =>
    api.get(`/market/data/${symbol}?interval=${interval}`),

  // Signals
  getSignals: () => api.get('/signals'),
  getSignal: (id: string) => api.get(`/signals/${id}`),

  // Trading
  createOrder: (data: any) => api.post('/trading/orders', data),
  getPositions: () => api.get('/trading/positions'),
  getAccount: () => api.get('/trading/account'),

  // Backtesting
  runBacktest: (data: any) => api.post('/backtest/run', data),
  getBacktestResults: (id: string) => api.get(`/backtest/results/${id}`),

  // User
  login: (data: any) => api.post('/auth/login', data),
  register: (data: any) => api.post('/auth/register', data),
  logout: () => api.post('/auth/logout'),
}
