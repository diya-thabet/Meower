export interface Investigation {
  id: string
  seed: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  created_at: string
  completed_at: string | null
  tool_results: Record<string, unknown> | null
  graph: GraphData | null
  report: string | null
  error: string | null
}

export interface InvestigationSummary {
  id: string
  seed: string
  type: string
  status: string
  created_at: string
  completed_at: string | null
}

export interface InvestigationCreate {
  seed: string
  type: string
  tools?: string[]
}

export interface ToolInfo {
  name: string
  category: string
  description: string
}

export interface ProgressStep {
  step_id: string
  tool: string
  status: 'pending' | 'running' | 'done' | 'failed'
  result?: Record<string, unknown>
  error?: string
  duration_ms: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface GraphNode {
  data: {
    id: string
    label: string
    type: 'email' | 'username' | 'social' | 'domain' | 'breach' | 'person'
    url?: string
  }
}

export interface GraphEdge {
  data: {
    source: string
    target: string
    label: string
  }
}
