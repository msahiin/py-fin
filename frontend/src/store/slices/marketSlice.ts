import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface MarketState {
  selectedSymbol: string
  timeframe: string
  prices: Record<string, number>
  signals: any[]
}

const initialState: MarketState = {
  selectedSymbol: 'BTCUSDT',
  timeframe: '1h',
  prices: {},
  signals: [],
}

const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {
    setSelectedSymbol: (state, action: PayloadAction<string>) => {
      state.selectedSymbol = action.payload
    },
    setTimeframe: (state, action: PayloadAction<string>) => {
      state.timeframe = action.payload
    },
    updatePrice: (state, action: PayloadAction<{ symbol: string; price: number }>) => {
      state.prices[action.payload.symbol] = action.payload.price
    },
    addSignal: (state, action: PayloadAction<any>) => {
      state.signals.unshift(action.payload)
    },
  },
})

export const { setSelectedSymbol, setTimeframe, updatePrice, addSignal } = marketSlice.actions
export default marketSlice.reducer
