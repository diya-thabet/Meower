import axios from 'axios'
import type { Investigation, InvestigationSummary, InvestigationCreate, ToolInfo } from '../types'

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
