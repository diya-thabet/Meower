import { useEffect, useRef, useCallback, useState } from 'react'
import type { WSMessage } from '../types'

export function useWebSocket(investigationId: string | undefined) {
  const wsRef = useRef<WebSocket | null>(null)
  const [messages, setMessages] = useState<WSMessage[]>([])
  const [connected, setConnected] = useState(false)
  const [status, setStatus] = useState<string>('')

  const onMessageRef = useRef<((msg: WSMessage) => void) | null>(null)

  useEffect(() => {
    if (!investigationId) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const ws = new WebSocket(`${protocol}//${host}/api/v1/investigations/ws/${investigationId}`)

    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onerror = () => setConnected(false)

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        setMessages((prev) => [...prev, msg])
        if (msg.type === 'status' && msg.status) {
          setStatus(msg.status)
        }
        onMessageRef.current?.(msg)
      } catch {
        // ignore parse errors
      }
    }

    wsRef.current = ws

    return () => {
      ws.close()
      wsRef.current = null
      setConnected(false)
    }
  }, [investigationId])

  const onMessage = useCallback((cb: (msg: WSMessage) => void) => {
    onMessageRef.current = cb
  }, [])

  return { messages, connected, status, onMessage }
}
