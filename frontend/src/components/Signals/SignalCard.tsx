import {
  Card,
  CardContent,
  Typography,
  Chip,
  Stack,
  Box,
  LinearProgress,
  Divider,
} from '@mui/material'
import {
  TrendingUp,
  TrendingDown,
  TrendingFlat,
} from '@mui/icons-material'
import { format } from 'date-fns'

interface SignalCardProps {
  signal: {
    id: number
    symbol: string
    direction: string
    confidence: number
    entry_price?: number
    stop_loss?: number
    take_profit?: number
    timeframe: string
    created_at: string
    indicators?: any
  }
  onClick?: () => void
}

export default function SignalCard({ signal, onClick }: SignalCardProps) {
  const getDirectionIcon = () => {
    switch (signal.direction.toLowerCase()) {
      case 'buy':
        return <TrendingUp />
      case 'sell':
        return <TrendingDown />
      default:
        return <TrendingFlat />
    }
  }

  const getDirectionColor = () => {
    switch (signal.direction.toLowerCase()) {
      case 'buy':
        return 'success'
      case 'sell':
        return 'error'
      default:
        return 'default'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'success'
    if (confidence >= 60) return 'warning'
    return 'error'
  }

  const riskRewardRatio = signal.take_profit && signal.stop_loss && signal.entry_price
    ? ((signal.take_profit - signal.entry_price) / (signal.entry_price - signal.stop_loss)).toFixed(2)
    : null

  return (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        '&:hover': onClick ? { boxShadow: 6 } : {},
        transition: 'box-shadow 0.3s',
      }}
      onClick={onClick}
    >
      <CardContent>
        <Stack spacing={2}>
          {/* Header */}
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Stack direction="row" spacing={1} alignItems="center">
              <Typography variant="h6">{signal.symbol}</Typography>
              <Chip
                icon={getDirectionIcon()}
                label={signal.direction.toUpperCase()}
                color={getDirectionColor() as any}
                size="small"
              />
            </Stack>

            <Typography variant="caption" color="text.secondary">
              {format(new Date(signal.created_at), 'MMM dd, HH:mm')}
            </Typography>
          </Stack>

          {/* Confidence */}
          <Box>
            <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.5 }}>
              <Typography variant="body2">Confidence</Typography>
              <Typography variant="body2" fontWeight="bold">
                {signal.confidence.toFixed(1)}%
              </Typography>
            </Stack>
            <LinearProgress
              variant="determinate"
              value={signal.confidence}
              color={getConfidenceColor(signal.confidence) as any}
              sx={{ height: 8, borderRadius: 4 }}
            />
          </Box>

          <Divider />

          {/* Price Levels */}
          <Stack spacing={1}>
            {signal.entry_price && (
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  Entry Price
                </Typography>
                <Typography variant="body2" fontWeight="medium">
                  ${signal.entry_price.toFixed(2)}
                </Typography>
              </Stack>
            )}

            {signal.stop_loss && (
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="error">
                  Stop Loss
                </Typography>
                <Typography variant="body2" fontWeight="medium" color="error">
                  ${signal.stop_loss.toFixed(2)}
                </Typography>
              </Stack>
            )}

            {signal.take_profit && (
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="success.main">
                  Take Profit
                </Typography>
                <Typography variant="body2" fontWeight="medium" color="success.main">
                  ${signal.take_profit.toFixed(2)}
                </Typography>
              </Stack>
            )}

            {riskRewardRatio && (
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body2" color="text.secondary">
                  Risk/Reward
                </Typography>
                <Chip
                  label={`1:${riskRewardRatio}`}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              </Stack>
            )}
          </Stack>

          {/* Timeframe */}
          <Box>
            <Chip label={signal.timeframe} size="small" variant="outlined" />
          </Box>
        </Stack>
      </CardContent>
    </Card>
  )
}
