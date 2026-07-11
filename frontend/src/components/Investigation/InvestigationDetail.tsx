import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getInvestigation } from '../../services/api'
import { ArrowLeft, Loader2 } from 'lucide-react'

export function InvestigationDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: inv, isLoading } = useQuery({
    queryKey: ['investigation', id],
    queryFn: () => getInvestigation(id!),
    enabled: !!id,
    refetchInterval: (query) =>
      query.state.data?.status === 'running' || query.state.data?.status === 'pending' ? 2000 : false,
  })

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
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
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

      {inv.status === 'pending' && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto text-emerald-400" />
          <p className="mt-3 text-gray-400">Investigation is queued...</p>
        </div>
      )}

      {inv.tool_results && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h2 className="font-semibold mb-4">Tool Results</h2>
          <pre className="text-xs text-gray-400 overflow-auto max-h-96">
            {JSON.stringify(inv.tool_results, null, 2)}
          </pre>
        </div>
      )}

      {inv.report && (
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <h2 className="font-semibold mb-4">Report</h2>
          <div className="prose prose-invert prose-sm max-w-none">
            {inv.report.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
