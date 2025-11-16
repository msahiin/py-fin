import { useEffect, useRef, useCallback } from 'react'
import { io, Socket } from 'socket.io-client'

interface UseWebSocketProps {
  onPriceUpdate?: (data: any) => void
  onSignalUpdate?: (data: any) => void
  onTradeUpdate?: (data: any) => void
  onAccountUpdate?: (data: any) => void
}

export function useWebSocket({
  onPriceUpdate,
  onSignalUpdate,
  onTradeUpdate,
  onAccountUpdate,
}: UseWebSocketProps) {
  const socketRef = useRef<Socket | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')

    if (!token) return

    // Connect to WebSocket
    const socket = io('ws://localhost:8000', {
      auth: {
        token,
      },
      transports: ['websocket'],
    })

    socketRef.current = socket

    socket.on('connect', () => {
      console.log('WebSocket connected')
    })

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })

    socket.on('price_update', (data) => {
      if (onPriceUpdate) {
        onPriceUpdate(data)
      }
    })

    socket.on('new_signal', (data) => {
      if (onSignalUpdate) {
        onSignalUpdate(data)
      }
    })

    socket.on('trade_update', (data) => {
      if (onTradeUpdate) {
        onTradeUpdate(data)
      }
    })

    socket.on('account_update', (data) => {
      if (onAccountUpdate) {
        onAccountUpdate(data)
      }
    })

    return () => {
      socket.disconnect()
    }
  }, [onPriceUpdate, onSignalUpdate, onTradeUpdate, onAccountUpdate])

  const subscribe = useCallback((topic: string, symbols?: string[]) => {
    if (socketRef.current) {
      socketRef.current.emit('subscribe', { topic, symbols })
    }
  }, [])

  const unsubscribe = useCallback((topic: string) => {
    if (socketRef.current) {
      socketRef.current.emit('unsubscribe', { topic })
    }
  }, [])

  return { subscribe, unsubscribe }
}
