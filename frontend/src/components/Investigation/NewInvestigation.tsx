import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { createInvestigation, listTools } from '../../services/api'
import { Search, Mail, User, Globe, Smartphone } from 'lucide-react'

const types = [
  { value: 'email', label: 'Email', icon: Mail, desc: 'Investigate an email address' },
  { value: 'username', label: 'Username', icon: User, desc: 'Search across social platforms' },
  { value: 'domain', label: 'Domain', icon: Globe, desc: 'Domain and infrastructure recon' },
  { value: 'phone', label: 'Phone', icon: Smartphone, desc: 'Phone number intelligence' },
]

export function NewInvestigation() {
  const navigate = useNavigate()
  const [seed, setSeed] = useState('')
  const [type, setType] = useState('email')

  const { data: tools } = useQuery({ queryKey: ['tools'], queryFn: listTools })

  const mutation = useMutation({
    mutationFn: createInvestigation,
    onSuccess: (data) => {
      navigate(`/investigation/${data.id}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!seed.trim()) return
    mutation.mutate({ seed: seed.trim(), type })
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold">New Investigation</h1>
        <p className="text-gray-400 text-sm mt-1">Enter a seed value to start collecting intelligence</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <label className="block text-sm font-medium mb-2">Seed Value</label>
          <input
            type="text"
            value={seed}
            onChange={(e) => setSeed(e.target.value)}
            placeholder="e.g. john@example.com or @username or example.com or +1234567890"
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent placeholder-gray-500"
          />
          <p className="text-xs text-gray-500 mt-2">
            This is the starting point for your investigation
          </p>
        </div>

        <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
          <label className="block text-sm font-medium mb-3">Investigation Type</label>
          <div className="grid grid-cols-4 gap-3">
            {types.map((t) => (
              <button
                key={t.value}
                type="button"
                onClick={() => setType(t.value)}
                className={`flex flex-col items-center gap-2 p-4 rounded-lg border text-sm transition-colors ${
                  type === t.value
                    ? 'border-emerald-500 bg-emerald-500/10 text-emerald-400'
                    : 'border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600'
                }`}
              >
                <t.icon className="w-5 h-5" />
                <span className="font-medium">{t.label}</span>
                <span className="text-xs opacity-70">{t.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {tools && (
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-6">
            <h2 className="text-sm font-medium mb-3">Available Tools ({tools.length})</h2>
            <div className="grid grid-cols-3 gap-2">
              {tools.map((tool) => (
                <div
                  key={tool.name}
                  className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-lg text-xs text-gray-400"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
                  {tool.name}
                </div>
              ))}
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={!seed.trim() || mutation.isPending}
          className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed text-black px-6 py-3 rounded-lg font-medium transition-colors"
        >
          <Search className="w-4 h-4" />
          {mutation.isPending ? 'Starting...' : 'Start Investigation'}
        </button>
      </form>
    </div>
  )
}
