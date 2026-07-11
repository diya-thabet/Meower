import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { FileText, Download, RefreshCw, Loader2 } from 'lucide-react'
import { generateReport, getReportTypes } from '../../services/api'
import type { ReportType } from '../../types'

interface ReportViewerProps {
  investigationId: string
  initialReport?: string | null
}

export function ReportViewer({ investigationId, initialReport }: ReportViewerProps) {
  const [reportType, setReportType] = useState('full')
  const [report, setReport] = useState(initialReport || '')

  const { data: typesData } = useQuery({
    queryKey: ['reportTypes'],
    queryFn: getReportTypes,
  })

  const mutation = useMutation({
    mutationFn: (type: string) => generateReport(investigationId, type, false),
    onSuccess: (data) => {
      setReport(data.report)
    },
  })

  const handleExport = () => {
    const blob = new Blob([report], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `meower-report-${investigationId.slice(0, 8)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800">
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-emerald-400" />
          <h2 className="font-semibold">Report</h2>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs"
          >
            {typesData?.types.map((t: ReportType) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
          <button
            onClick={() => mutation.mutate(reportType)}
            disabled={mutation.isPending}
            className="flex items-center gap-1 px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-black rounded-lg text-xs font-medium transition-colors"
          >
            {mutation.isPending ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <RefreshCw className="w-3 h-3" />
            )}
            Generate
          </button>
          {report && (
            <button
              onClick={handleExport}
              className="flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg text-xs transition-colors"
            >
              <Download className="w-3 h-3" />
              Export
            </button>
          )}
        </div>
      </div>

      <div className="p-6">
        {!report && !mutation.isPending && (
          <div className="text-center py-12 text-gray-500">
            <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No report generated yet</p>
            <p className="text-xs mt-1">Select a report type and click Generate</p>
          </div>
        )}

        {mutation.isPending && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
          </div>
        )}

        {report && !mutation.isPending && (
          <div className="prose prose-invert prose-sm max-w-none">
            {report.split('\n').map((line, i) => {
              if (line.startsWith('## ')) {
                return <h2 key={i} className="text-lg font-bold mt-6 mb-2 text-emerald-400">{line.replace('## ', '')}</h2>
              }
              if (line.startsWith('### ')) {
                return <h3 key={i} className="text-base font-semibold mt-4 mb-1 text-gray-200">{line.replace('### ', '')}</h3>
              }
              if (line.startsWith('**') && line.endsWith('**')) {
                return <p key={i} className="font-bold text-gray-300 mt-3 mb-1">{line.replace(/\*\*/g, '')}</p>
              }
              if (line.startsWith('- ')) {
                return <li key={i} className="text-gray-400 ml-4">{line.slice(2)}</li>
              }
              if (line.startsWith('1.') || line.startsWith('2.') || line.startsWith('3.') || line.startsWith('4.') || line.startsWith('5.') || line.startsWith('6.') || line.startsWith('7.') || line.startsWith('8.') || line.startsWith('9.')) {
                return <li key={i} className="text-gray-400 ml-4 list-decimal">{line.replace(/^\d+\.\s*/, '')}</li>
              }
              if (line.trim() === '') {
                return <br key={i} />
              }
              return <p key={i} className="text-gray-400 leading-relaxed">{line}</p>
            })}
          </div>
        )}
      </div>
    </div>
  )
}
