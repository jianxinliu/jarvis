import { useCallback, useEffect, useRef } from 'react'
import type { WebSocketMessage } from '../types'

interface UseWebSocketReturn {
  connectWebSocket: () => void
  disconnectWebSocket: () => void
}

function useWebSocket(
  onMessage: (message: WebSocketMessage) => void
): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  // 使用 ref 存储最新的回调，避免因为回调变化导致重新连接
  const onMessageRef = useRef(onMessage)

  // 更新回调引用
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  const connectWebSocket = useCallback(() => {
    // 如果已经连接，先断开
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    try {
      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        console.log('WebSocket 连接已建立')
        // 清除重连定时器
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
          reconnectTimeoutRef.current = null
        }
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          // 使用 ref 中的最新回调
          onMessageRef.current(message)
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket 错误:', error)
      }

      ws.onclose = () => {
        console.log('WebSocket 连接已关闭')
        // 尝试重连（延迟 3 秒）
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket()
        }, 3000)
      }

      wsRef.current = ws
    } catch (error) {
      console.error('创建 WebSocket 连接失败:', error)
    }
  }, [])

  const disconnectWebSocket = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  useEffect(() => {
    return () => {
      disconnectWebSocket()
    }
  }, [disconnectWebSocket])

  return {
    connectWebSocket,
    disconnectWebSocket,
  }
}

export default useWebSocket

