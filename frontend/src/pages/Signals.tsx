import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Stack,
  CircularProgress,
} from '@mui/material'
import { Refresh as RefreshIcon } from '@mui/icons-material'
import SignalCard from '../components/Signals/SignalCard'
import { apiEndpoints } from '../services/api'

export default function Signals() {
  const [signals, setSignals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState({
    direction: 'all',
    min_confidence: 0,
    timeframe: 'all',
  })

  useEffect(() => {
    fetchSignals()
  }, [filter])

  const fetchSignals = async () => {
    try {
      setLoading(true)

      const params = new URLSearchParams()
      if (filter.direction !== 'all') params.append('direction', filter.direction)
      if (filter.min_confidence > 0) params.append('min_confidence', filter.min_confidence.toString())
      if (filter.timeframe !== 'all') params.append('timeframe', filter.timeframe)

      const response = await apiEndpoints.getSignals()
      setSignals(response.data)
    } catch (error) {
      console.error('Error fetching signals:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4">Trading Signals</Typography>

        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchSignals}
        >
          Refresh
        </Button>
      </Stack>

      {/* Filters */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Direction</InputLabel>
          <Select
            value={filter.direction}
            label="Direction"
            onChange={(e) => setFilter({ ...filter, direction: e.target.value })}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="buy">Buy</MenuItem>
            <MenuItem value="sell">Sell</MenuItem>
            <MenuItem value="hold">Hold</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Min Confidence</InputLabel>
          <Select
            value={filter.min_confidence}
            label="Min Confidence"
            onChange={(e) => setFilter({ ...filter, min_confidence: Number(e.target.value) })}
          >
            <MenuItem value={0}>Any</MenuItem>
            <MenuItem value={50}>50%+</MenuItem>
            <MenuItem value={70}>70%+</MenuItem>
            <MenuItem value={80}>80%+</MenuItem>
          </Select>
        </FormControl>

        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Timeframe</InputLabel>
          <Select
            value={filter.timeframe}
            label="Timeframe"
            onChange={(e) => setFilter({ ...filter, timeframe: e.target.value })}
          >
            <MenuItem value="all">All</MenuItem>
            <MenuItem value="1h">1 Hour</MenuItem>
            <MenuItem value="4h">4 Hours</MenuItem>
            <MenuItem value="1d">1 Day</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      {/* Signals Grid */}
      {loading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : signals.length === 0 ? (
        <Typography variant="body1" color="text.secondary" textAlign="center" py={4}>
          No signals found. Try adjusting your filters.
        </Typography>
      ) : (
        <Grid container spacing={3}>
          {signals.map((signal) => (
            <Grid item xs={12} md={6} lg={4} key={signal.id}>
              <SignalCard signal={signal} />
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  )
}
