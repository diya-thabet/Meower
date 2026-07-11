import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Search, Activity, AlertTriangle, Users } from 'lucide-react'
import { listInvestigations } from '../../services/api'

const stats = [
  { label: 'Total Investigations', value: '-', icon: Activity, color: 'text-blue-400' },
  { label: 'Completed', value: '-', icon: Users, color: 'text-emerald-400' },
  { label: 'High Risk', value: '-', icon: AlertTriangle, color: 'text-red-400' },
  { label: 'New', icon: Search, color: 'text-purple-400', value: '-' },
]

export function Dashboard() {
  const { data: investigations } = useQuery({
    queryKey: ['investigations'],
    queryFn: listInvestigations,
  })

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">Welcome to Meower OSINT Platform</p>
        </div>
        <Link
          to="/investigate"
          className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 text-black px-4 py-2 rounded-lg font-medium transition-colors"
        >
          <Search className="w-4 h-4" />
          New Investigation
        </Link>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <div className="flex items-center gap-3">
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
              <span className="text-gray-400 text-sm">{stat.label}</span>
            </div>
            <p className="text-2xl font-bold mt-2">{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="bg-gray-900 rounded-xl border border-gray-800">
        <div className="p-4 border-b border-gray-800">
          <h2 className="font-semibold">Recent Investigations</h2>
        </div>
        <div className="divide-y divide-gray-800">
          {investigations?.length === 0 && (
            <div className="p-8 text-center text-gray-500">
              <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No investigations yet</p>
              <Link to="/investigate" className="text-emerald-400 hover:underline mt-1 inline-block">
                Start your first investigation
              </Link>
            </div>
          )}
          {investigations?.map((inv) => (
            <Link
              key={inv.id}
              to={`/investigation/${inv.id}`}
              className="flex items-center justify-between p-4 hover:bg-gray-800/50 transition-colors"
            >
              <div>
                <p className="font-medium">{inv.seed}</p>
                <p className="text-sm text-gray-400">
                  {inv.type} &middot; {new Date(inv.created_at).toLocaleString()}
                </p>
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
    </div>
  )
}
