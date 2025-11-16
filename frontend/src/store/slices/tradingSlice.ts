import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface TradingState {
  positions: any[]
  orders: any[]
  balance: number
  equity: number
}

const initialState: TradingState = {
  positions: [],
  orders: [],
  balance: 10000,
  equity: 10000,
}

const tradingSlice = createSlice({
  name: 'trading',
  initialState,
  reducers: {
    setPositions: (state, action: PayloadAction<any[]>) => {
      state.positions = action.payload
    },
    addPosition: (state, action: PayloadAction<any>) => {
      state.positions.push(action.payload)
    },
    updateBalance: (state, action: PayloadAction<{ balance: number; equity: number }>) => {
      state.balance = action.payload.balance
      state.equity = action.payload.equity
    },
  },
})

export const { setPositions, addPosition, updateBalance } = tradingSlice.actions
export default tradingSlice.reducer
