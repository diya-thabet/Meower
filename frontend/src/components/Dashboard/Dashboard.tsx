import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Search, Activity, AlertTriangle, Globe, Users } from 'lucide-react'
import { listInvestigations, listEntities, listDomains } from '../../services/api'

export function Dashboard() {
  const { data: investigations } = useQuery({
    queryKey: ['investigations'],
    queryFn: listInvestigations,
  })

  const { data: entityData } = useQuery({
    queryKey: ['entities-top'],
    queryFn: () => listEntities(0, 5),
  })

  const { data: domains } = useQuery({
    queryKey: ['domains-top'],
    queryFn: () => listDomains(0, 5),
  })

  const completed = investigations?.filter((i) => i.status === 'completed').length || 0
  const running = investigations?.filter((i) => i.status === 'running').length || 0
  const highRisk = entityData?.results.filter((e) => e.risk_score >= 40).length || 0

  const stats = [
    { label: 'Total Investigations', value: investigations?.length || 0, icon: Activity, color: 'text-blue-400' },
    { label: 'Completed', value: completed, icon: Users, color: 'text-emerald-400' },
    { label: 'Running', value: running, icon: AlertTriangle, color: 'text-yellow-400' },
    { label: 'High Risk Entities', value: highRisk, icon: AlertTriangle, color: 'text-red-400' },
  ]

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

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-gray-900 rounded-xl border border-gray-800">
          <div className="p-4 border-b border-gray-800 flex items-center justify-between">
            <h2 className="font-semibold">Recent Investigations</h2>
            <Link to="/history" className="text-xs text-emerald-400 hover:underline">View all</Link>
          </div>
          <div className="divide-y divide-gray-800">
            {(!investigations || investigations.length === 0) && (
              <div className="p-8 text-center text-gray-500">
                <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No investigations yet</p>
                <Link to="/investigate" className="text-emerald-400 hover:underline mt-1 inline-block text-sm">
                  Start your first investigation
                </Link>
              </div>
            )}
            {investigations?.slice(0, 5).map((inv) => (
              <Link
                key={inv.id}
                to={`/investigation/${inv.id}`}
                className="flex items-center justify-between p-4 hover:bg-gray-800/50 transition-colors"
              >
                <div>
                  <p className="font-medium text-sm">{inv.seed}</p>
                  <p className="text-xs text-gray-500">
                    {inv.type} &middot; {new Date(inv.created_at).toLocaleString()}
                  </p>
                </div>
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
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

        <div className="bg-gray-900 rounded-xl border border-gray-800">
          <div className="p-4 border-b border-gray-800">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-emerald-400" />
              <h2 className="font-semibold">Top Risk Entities</h2>
            </div>
          </div>
          <div className="divide-y divide-gray-800">
            {(!entityData || entityData.results.length === 0) && (
              <div className="p-8 text-center text-gray-500 text-sm">
                <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No entities discovered yet</p>
              </div>
            )}
            {entityData?.results.map((e) => (
              <div key={e.id} className="flex items-center justify-between p-4">
                <div>
                  <p className="text-sm font-medium">{e.display_name || e.primary_value}</p>
                  <p className="text-xs text-gray-500">{e.type} &middot; {e.investigation_count} investigations</p>
                </div>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  e.risk_score >= 70 ? 'bg-red-500/10 text-red-400' :
                  e.risk_score >= 40 ? 'bg-orange-500/10 text-orange-400' :
                  e.risk_score >= 20 ? 'bg-yellow-500/10 text-yellow-400' :
                  'bg-green-500/10 text-green-400'
                }`}>
                  {e.risk_score}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {domains && domains.length > 0 && (
        <div className="bg-gray-900 rounded-xl border border-gray-800">
          <div className="p-4 border-b border-gray-800 flex items-center gap-2">
            <Globe className="w-4 h-4 text-emerald-400" />
            <h2 className="font-semibold">Domains</h2>
          </div>
          <div className="divide-y divide-gray-800">
            {domains.map((d) => (
              <div key={d.id} className="flex items-center justify-between p-4">
                <p className="text-sm font-medium">{d.domain}</p>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  d.risk_score >= 70 ? 'bg-red-500/10 text-red-400' :
                  d.risk_score >= 40 ? 'bg-orange-500/10 text-orange-400' :
                  'bg-green-500/10 text-green-400'
                }`}>
                  {d.risk_score}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
