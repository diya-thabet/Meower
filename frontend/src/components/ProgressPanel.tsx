import { CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react'
import type { WSMessage } from '../types'

interface ProgressPanelProps {
  messages: WSMessage[]
  connected: boolean
  status: string
}

const toolStatusIcon: Record<string, typeof CheckCircle2> = {
  running: Loader2,
  success: CheckCircle2,
  error: XCircle,
  pending: Clock,
}

const toolStatusColor: Record<string, string> = {
  running: 'text-blue-400',
  success: 'text-emerald-400',
  error: 'text-red-400',
  pending: 'text-gray-500',
}

export function ProgressPanel({ messages, connected, status }: ProgressPanelProps) {
  const toolMessages = messages.filter((m) => m.type === 'tool_progress')
  const uniqueTools = new Map<string, WSMessage>()

  for (const msg of toolMessages) {
    if (msg.tool) {
      uniqueTools.set(msg.tool, msg)
    }
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold">Progress</h2>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-400' : 'bg-red-400'}`} />
          <span className="text-xs text-gray-400">{connected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      {status && (
        <div className="mb-4 px-3 py-2 bg-gray-800 rounded-lg text-sm">
          Status: <span className="font-medium capitalize">{status}</span>
        </div>
      )}

      {uniqueTools.size === 0 && (
        <div className="text-center py-8 text-gray-500 text-sm">
          <Clock className="w-6 h-6 mx-auto mb-2 opacity-50" />
          Waiting for tool results...
        </div>
      )}

      <div className="space-y-2">
        {Array.from(uniqueTools.entries()).map(([tool, msg]) => {
          const Icon = toolStatusIcon[msg.status || 'pending'] || Clock
          const color = toolStatusColor[msg.status || 'pending'] || 'text-gray-500'
          return (
            <div key={tool} className="flex items-center gap-3 px-3 py-2 bg-gray-800/50 rounded-lg">
              <Icon className={`w-4 h-4 shrink-0 ${color} ${msg.status === 'running' ? 'animate-spin' : ''}`} />
              <span className="text-sm">{tool}</span>
              <span className={`text-xs ml-auto capitalize ${color}`}>{msg.status}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
