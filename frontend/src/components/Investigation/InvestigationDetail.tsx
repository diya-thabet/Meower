import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getInvestigation } from '../../services/api'
import { ArrowLeft, Loader2, BarChart3, Share2, FileText, Activity } from 'lucide-react'
import { useWebSocket } from '../../hooks/useWebSocket'
import { ProgressPanel } from '../ProgressPanel'
import { GraphCanvas } from '../Graph/GraphCanvas'
import { ReportViewer } from '../Report/ReportViewer'

const tabs = [
  { id: 'progress', label: 'Progress', icon: Activity },
  { id: 'graph', label: 'Graph', icon: Share2 },
  { id: 'report', label: 'Report', icon: FileText },
  { id: 'data', label: 'Raw Data', icon: BarChart3 },
]

export function InvestigationDetail() {
  const { id } = useParams<{ id: string }>()
  const [activeTab, setActiveTab] = useState('progress')

  const { data: inv, isLoading } = useQuery({
    queryKey: ['investigation', id],
    queryFn: () => getInvestigation(id!),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data?.status === 'running' || query.state.data?.status === 'pending' ? 2000 : false,
  })

  const { messages, connected, status } = useWebSocket(
    inv?.status === 'running' || inv?.status === 'pending' ? id : undefined
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
      </div>
    )
  }

  if (!inv) {
    return (
      <div className="text-center py-16">
        <p className="text-gray-400">Investigation not found</p>
        <Link to="/" className="text-emerald-400 hover:underline mt-2 inline-block">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <Link
        to="/"
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors w-fit"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{inv.seed}</h1>
          <p className="text-sm text-gray-400 mt-1">
            {inv.type} investigation &middot; Created {new Date(inv.created_at).toLocaleString()}
          </p>
        </div>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium ${
            inv.status === 'completed'
              ? 'bg-emerald-500/10 text-emerald-400'
              : inv.status === 'running'
                ? 'bg-blue-500/10 text-blue-400'
                : inv.status === 'failed'
                  ? 'bg-red-500/10 text-red-400'
                  : 'bg-gray-500/10 text-gray-400'
          }`}
        >
          {inv.status}
        </span>
      </div>

      {inv.graph?.stats && (
        <div className="grid grid-cols-5 gap-3">
          <div className="bg-gray-900 rounded-lg p-3 border border-gray-800 text-center">
            <p className="text-xs text-gray-500">Nodes</p>
            <p className="text-lg font-bold">{inv.graph.stats.total_nodes}</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 border border-gray-800 text-center">
            <p className="text-xs text-gray-500">Edges</p>
            <p className="text-lg font-bold">{inv.graph.stats.total_edges}</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 border border-gray-800 text-center">
            <p className="text-xs text-gray-500">Risk Score</p>
            <p className={`text-lg font-bold ${
              (inv.graph.stats.risk_score || 0) >= 70 ? 'text-red-400' :
              (inv.graph.stats.risk_score || 0) >= 40 ? 'text-orange-400' :
              (inv.graph.stats.risk_score || 0) >= 20 ? 'text-yellow-400' :
              'text-green-400'
            }`}>{inv.graph.stats.risk_score}</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 border border-gray-800 text-center">
            <p className="text-xs text-gray-500">Risk Label</p>
            <p className={`text-lg font-bold ${
              inv.graph.stats.risk_label === 'CRITICAL' ? 'text-red-400' :
              inv.graph.stats.risk_label === 'HIGH' ? 'text-orange-400' :
              inv.graph.stats.risk_label === 'MEDIUM' ? 'text-yellow-400' :
              'text-green-400'
            }`}>{inv.graph.stats.risk_label}</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 border border-gray-800 text-center">
            <p className="text-xs text-gray-500">Signals</p>
            <p className="text-lg font-bold">{(inv.graph.stats.risk_signals || []).length}</p>
          </div>
        </div>
      )}

      <div className="flex gap-1 border-b border-gray-800">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-emerald-400 text-emerald-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'progress' && (
        <ProgressPanel messages={messages} connected={connected} status={status || inv.status} />
      )}

      {activeTab === 'graph' && inv.graph && (
        <GraphCanvas data={inv.graph} />
      )}
      {activeTab === 'graph' && !inv.graph && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 text-center text-gray-500">
          <Share2 className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Graph not available</p>
        </div>
      )}

      {activeTab === 'report' && (
        <ReportViewer investigationId={id!} initialReport={inv.report} />
      )}

      {activeTab === 'data' && inv.tool_results && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h2 className="font-semibold mb-4">Raw Tool Results</h2>
          <pre className="text-xs text-gray-400 overflow-auto max-h-96 leading-relaxed">
            {JSON.stringify(inv.tool_results, null, 2)}
          </pre>
        </div>
      )}
      {activeTab === 'data' && !inv.tool_results && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 text-center text-gray-500">
          <BarChart3 className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>No tool results yet</p>
        </div>
      )}
    </div>
  )
}
