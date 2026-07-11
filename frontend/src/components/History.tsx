import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { History as HistoryIcon, Search } from 'lucide-react'
import { listInvestigations } from '../services/api'

export function History() {
  const { data: investigations } = useQuery({
    queryKey: ['investigations'],
    queryFn: listInvestigations,
  })

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">History</h1>
        <p className="text-gray-400 text-sm mt-1">All past investigations</p>
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800">
        {(!investigations || investigations.length === 0) && (
          <div className="p-12 text-center text-gray-500">
            <HistoryIcon className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No investigations yet</p>
            <Link to="/investigate" className="text-emerald-400 hover:underline mt-1 inline-block text-sm">
              Start your first investigation
            </Link>
          </div>
        )}
        {investigations?.map((inv) => (
          <Link
            key={inv.id}
            to={`/investigation/${inv.id}`}
            className="flex items-center justify-between p-4 hover:bg-gray-800/50 transition-colors border-b border-gray-800 last:border-b-0"
          >
            <div className="flex items-center gap-3">
              <Search className="w-4 h-4 text-gray-500 shrink-0" />
              <div>
                <p className="font-medium">{inv.seed}</p>
                <p className="text-xs text-gray-500">
                  {inv.type} &middot; {new Date(inv.created_at).toLocaleString()}
                </p>
              </div>
            </div>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
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
          </Link>
        ))}
      </div>
    </div>
  )
}
