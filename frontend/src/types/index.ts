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

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  stats?: GraphStats
}

export interface GraphStats {
  total_nodes: number
  total_edges: number
  risk_score: number
  risk_label: string
  risk_signals: string[]
  node_counts: Record<string, number>
}

export interface GraphNode {
  data: {
    id: string
    label: string
    type: string
    url?: string
  }
}

export interface GraphEdge {
  data: {
    id?: string
    source: string
    target: string
    label: string
  }
}

export interface EntitySummary {
  id: string
  primary_value: string
  type: string
  display_name: string
  risk_score: number
  investigation_count: number
}

export interface EntityResponse extends EntitySummary {
  first_seen: string
  last_seen: string
  phone?: string
  google_id?: string
  social_ids?: Record<string, string>
  profile_urls?: Array<Record<string, string>>
  associated_domains?: string[]
  data_breaches?: Array<Record<string, unknown>>
  services?: Array<Record<string, unknown>>
  entity_metadata?: Record<string, unknown>
}

export interface DomainSummary {
  id: string
  domain: string
  risk_score: number
}

export interface DomainResponse extends DomainSummary {
  subdomains?: string[]
  ips?: string[]
  registrant_email?: string
  technologies?: string[]
  ssl_info?: Record<string, unknown>
  first_seen: string
  last_seen: string
}

export interface EdgeResponse {
  id: string
  source_entity_id: string
  source_type: string
  target_entity_id: string
  target_type: string
  relationship: string
  investigation_id?: string
  first_seen: string
}

export interface WSMessage {
  type: 'status' | 'tool_progress'
  status?: string
  tool?: string
  error?: string
}

export interface ReportResponse {
  report: string
  report_type: string
}

export interface ReportType {
  id: string
  name: string
  description: string
}
