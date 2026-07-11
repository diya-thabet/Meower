import { useQuery } from '@tanstack/react-query'
import { Globe, Activity } from 'lucide-react'
import { getReportStatus, listTools } from '../services/api'

export function Settings() {
  const { data: status } = useQuery({
    queryKey: ['reportStatus'],
    queryFn: getReportStatus,
  })

  const { data: tools } = useQuery({
    queryKey: ['tools'],
    queryFn: listTools,
  })

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-400 text-sm mt-1">Configuration and system status</p>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Globe className="w-4 h-4 text-emerald-400" />
          <h2 className="font-semibold">LLM Service</h2>
        </div>
        {status ? (
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${status.available ? 'bg-emerald-400' : 'bg-red-400'}`} />
              <span className="text-gray-400">Status:</span>
              <span className={status.available ? 'text-emerald-400' : 'text-red-400'}>
                {status.available ? 'Available' : 'Not configured'}
              </span>
            </div>
            <p className="text-gray-500">
              <span className="text-gray-400">Provider:</span> {status.provider}
            </p>
            <p className="text-gray-500">
              <span className="text-gray-400">Model:</span> {status.model}
            </p>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Loading...</p>
        )}
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h2 className="font-semibold">Available Tools ({tools?.length || 0})</h2>
        </div>
        {tools ? (
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {tools.map((tool) => (
              <div
                key={tool.name}
                className="flex items-center gap-2 px-3 py-2 bg-gray-800 rounded-lg text-sm"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                <div>
                  <p className="text-gray-200">{tool.name}</p>
                  <p className="text-xs text-gray-500">{tool.category}</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">Loading...</p>
        )}
      </div>
    </div>
  )
}
