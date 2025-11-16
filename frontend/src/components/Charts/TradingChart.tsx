import { useEffect, useRef, useState } from 'react'
import { Box, Paper, Select, MenuItem, FormControl, InputLabel, Stack } from '@mui/material'
import { createChart, IChartApi, ISeriesApi, ColorType } from 'lightweight-charts'

interface TradingChartProps {
  symbol: string
  interval: string
  onIntervalChange?: (interval: string) => void
}

export default function TradingChart({ symbol, interval, onIntervalChange }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null)

  const [selectedInterval, setSelectedInterval] = useState(interval)

  useEffect(() => {
    if (!chartContainerRef.current) return

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2B2B43',
      },
      timeScale: {
        borderColor: '#2B2B43',
        timeVisible: true,
        secondsVisible: false,
      },
    })

    chartRef.current = chart

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    })

    candlestickSeriesRef.current = candlestickSeries

    // Add volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    })

    chart.priceScale('').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    })

    volumeSeriesRef.current = volumeSeries

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        })
      }
    }

    window.addEventListener('resize', handleResize)

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize)
      chart.remove()
    }
  }, [])

  useEffect(() => {
    // Load data when symbol or interval changes
    fetchChartData(symbol, selectedInterval)
  }, [symbol, selectedInterval])

  const fetchChartData = async (sym: string, int: string) => {
    try {
      const response = await fetch(
        `/api/v1/market/data/${sym}?interval=${int}&limit=500`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }
      )

      if (!response.ok) return

      const result = await response.json()

      if (result.data && candlestickSeriesRef.current && volumeSeriesRef.current) {
        const candleData = result.data.map((d: any) => ({
          time: new Date(d.timestamp).getTime() / 1000,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        }))

        const volumeData = result.data.map((d: any) => ({
          time: new Date(d.timestamp).getTime() / 1000,
          value: d.volume,
          color: d.close >= d.open ? '#26a69a80' : '#ef535080',
        }))

        candlestickSeriesRef.current.setData(candleData)
        volumeSeriesRef.current.setData(volumeData)

        // Fit content
        if (chartRef.current) {
          chartRef.current.timeScale().fitContent()
        }
      }
    } catch (error) {
      console.error('Error fetching chart data:', error)
    }
  }

  const handleIntervalChange = (newInterval: string) => {
    setSelectedInterval(newInterval)
    if (onIntervalChange) {
      onIntervalChange(newInterval)
    }
  }

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Interval</InputLabel>
          <Select
            value={selectedInterval}
            label="Interval"
            onChange={(e) => handleIntervalChange(e.target.value)}
          >
            <MenuItem value="1m">1 Minute</MenuItem>
            <MenuItem value="5m">5 Minutes</MenuItem>
            <MenuItem value="15m">15 Minutes</MenuItem>
            <MenuItem value="1h">1 Hour</MenuItem>
            <MenuItem value="4h">4 Hours</MenuItem>
            <MenuItem value="1d">1 Day</MenuItem>
            <MenuItem value="1w">1 Week</MenuItem>
          </Select>
        </FormControl>
      </Stack>

      <Box ref={chartContainerRef} />
    </Paper>
  )
}
