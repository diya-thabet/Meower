import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'
import { Search, Activity, History, Settings, Crosshair } from 'lucide-react'
import { useAppStore } from '../../store/app'

const navItems = [
  { to: '/', icon: Activity, label: 'Dashboard' },
  { to: '/investigate', icon: Search, label: 'Investigate' },
  { to: '/history', icon: History, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
]

export function Layout({ children }: { children: ReactNode }) {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)

  return (
    <div className="flex h-screen overflow-hidden">
      <aside
        className={`${
          sidebarOpen ? 'w-56' : 'w-16'
        } transition-all duration-200 bg-gray-900 border-r border-gray-800 flex flex-col`}
      >
        <div className="flex items-center gap-2 px-4 h-14 border-b border-gray-800">
          <Crosshair className="w-6 h-6 text-emerald-400 shrink-0" />
          {sidebarOpen && <span className="font-bold text-lg">Meower</span>}
        </div>
        <nav className="flex-1 py-4 space-y-1 px-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                }`
              }
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">{children}</main>
    </div>
  )
}
