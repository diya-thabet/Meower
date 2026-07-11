import CytoscapeComponent from 'react-cytoscapejs'
import type { GraphData } from '../../types'

interface GraphCanvasProps {
  data: GraphData
  height?: string
}

const typeStyles = [
  { selector: 'node[type="email"]', style: { 'background-color': '#3b82f6' } },
  { selector: 'node[type="username"]', style: { 'background-color': '#10b981' } },
  { selector: 'node[type="social"]', style: { 'background-color': '#8b5cf6' } },
  { selector: 'node[type="domain"]', style: { 'background-color': '#f59e0b' } },
  { selector: 'node[type="breach"]', style: { 'background-color': '#ef4444' } },
  { selector: 'node[type="person"]', style: { 'background-color': '#ec4899' } },
  { selector: 'node[type="service"]', style: { 'background-color': '#06b6d4' } },
  { selector: 'node[type="ip"]', style: { 'background-color': '#f97316' } },
  { selector: 'node[type="archive"]', style: { 'background-color': '#6b7280' } },
  { selector: 'node', style: { 'background-color': '#6b7280', label: 'data(label)', color: '#e5e7eb', 'font-size': '11px', 'text-valign': 'bottom', 'text-halign': 'center', 'text-margin-y': 6, width: 28, height: 28 } },
  { selector: 'edge', style: { 'line-color': '#4b5563', 'target-arrow-color': '#4b5563', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: 'data(label)', color: '#9ca3af', 'font-size': '9px', 'text-rotation': 'autorotate' } },
]

export function GraphCanvas({ data, height = '500px' }: GraphCanvasProps) {
  if (!data.nodes.length) {
    return (
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-8 text-center text-gray-500">
        <p>No graph data available</p>
      </div>
    )
  }

  const elements = [
    ...data.nodes.map((n) => ({
      data: { id: n.data.id, label: n.data.label, type: n.data.type },
    })),
    ...data.edges.map((e) => ({
      data: {
        id: e.data.id || `${e.data.source}->${e.data.target}`,
        source: e.data.source,
        target: e.data.target,
        label: e.data.label,
      },
    })),
  ]

  return (
    <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
      <CytoscapeComponent
        elements={elements}
        layout={{ name: 'breadthfirst', directed: true, spacingFactor: 1.5 }}
        style={{ width: '100%', height }}
        stylesheet={typeStyles}
      />
    </div>
  )
}
