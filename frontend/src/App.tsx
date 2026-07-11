import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout/Layout'
import { Dashboard } from './components/Dashboard/Dashboard'
import { NewInvestigation } from './components/Investigation/NewInvestigation'
import { InvestigationDetail } from './components/Investigation/InvestigationDetail'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/investigate" element={<NewInvestigation />} />
        <Route path="/investigation/:id" element={<InvestigationDetail />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  )
}
