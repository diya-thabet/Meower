import axios from 'axios'
import type {
  Investigation, InvestigationSummary, InvestigationCreate, ToolInfo,
  EntitySummary, EntityResponse, DomainSummary, DomainResponse,
  EdgeResponse, ReportResponse, ReportType,
} from '../types'

const client = axios.create({
  baseURL: '/api/v1',
})

export async function listInvestigations(): Promise<InvestigationSummary[]> {
  const { data } = await client.get('/investigations')
  return data
}

export async function getInvestigation(id: string): Promise<Investigation> {
  const { data } = await client.get(`/investigations/${id}`)
  return data
}

export async function createInvestigation(body: InvestigationCreate): Promise<Investigation> {
  const { data } = await client.post('/investigations', body)
  return data
}

export async function deleteInvestigation(id: string): Promise<void> {
  await client.delete(`/investigations/${id}`)
}

export async function listTools(): Promise<ToolInfo[]> {
  const { data } = await client.get('/tools')
  return data
}

export async function listEntities(skip = 0, limit = 20, sort = 'risk_score', order = 'desc'): Promise<{ results: EntitySummary[]; total: number }> {
  const { data } = await client.get('/entities', { params: { skip, limit, sort, order } })
  return data
}

export async function getEntity(id: string): Promise<EntityResponse> {
  const { data } = await client.get(`/entities/${id}`)
  return data
}

export async function searchEntities(q: string): Promise<{ results: EntitySummary[]; total: number }> {
  const { data } = await client.get('/entities/search', { params: { q } })
  return data
}

export async function getEntityRisk(id: string): Promise<{ id: string; risk_score: number; risk_label: string }> {
  const { data } = await client.get(`/entities/${id}/risk`)
  return data
}

export async function getEntityEdges(id: string): Promise<EdgeResponse[]> {
  const { data } = await client.get(`/entities/${id}/edges`)
  return data
}

export async function listDomains(skip = 0, limit = 20): Promise<DomainSummary[]> {
  const { data } = await client.get('/entities/domains', { params: { skip, limit } })
  return data
}

export async function getDomain(id: string): Promise<DomainResponse> {
  const { data } = await client.get(`/entities/domains/${id}`)
  return data
}

export async function generateReport(invId: string, reportType = 'full', force = false): Promise<ReportResponse> {
  const { data } = await client.post(`/reports/generate/${invId}`, null, { params: { report_type: reportType, force } })
  return data
}

export async function getReportTypes(): Promise<{ types: ReportType[] }> {
  const { data } = await client.get('/reports/types')
  return data
}

export async function getReportStatus(): Promise<{ available: boolean; model: string; provider: string }> {
  const { data } = await client.get('/reports/status')
  return data
}
