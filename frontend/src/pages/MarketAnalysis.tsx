import { useState } from 'react'
import {
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Paper,
  Grid,
  Card,
  CardContent,
} from '@mui/material'
import TradingChart from '../components/Charts/TradingChart'

export default function MarketAnalysis() {
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [interval, setInterval] = useState('1h')
  const [indicators, setIndicators] = useState<any>(null)

  const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Market Analysis
      </Typography>

      {/* Symbol Selector */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Symbol</InputLabel>
          <Select
            value={symbol}
            label="Symbol"
            onChange={(e) => setSymbol(e.target.value)}
          >
            {symbols.map((sym) => (
              <MenuItem key={sym} value={sym}>
                {sym}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>

      <Grid container spacing={3}>
        {/* Chart */}
        <Grid item xs={12} lg={9}>
          <TradingChart
            symbol={symbol}
            interval={interval}
            onIntervalChange={setInterval}
          />
        </Grid>

        {/* Indicators Panel */}
        <Grid item xs={12} lg={3}>
          <Paper elevation={3} sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Technical Indicators
            </Typography>

            <Stack spacing={2}>
              <Card variant="outlined">
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    RSI (14)
                  </Typography>
                  <Typography variant="h6">--</Typography>
                </CardContent>
              </Card>

              <Card variant="outlined">
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    MACD
                  </Typography>
                  <Typography variant="h6">--</Typography>
                </CardContent>
              </Card>

              <Card variant="outlined">
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    SMA 20
                  </Typography>
                  <Typography variant="h6">--</Typography>
                </CardContent>
              </Card>

              <Card variant="outlined">
                <CardContent>
                  <Typography color="text.secondary" gutterBottom variant="body2">
                    ATR
                  </Typography>
                  <Typography variant="h6">--</Typography>
                </CardContent>
              </Card>
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
