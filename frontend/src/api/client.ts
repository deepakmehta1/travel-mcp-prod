const DEFAULT_AGENT_URL = import.meta.env.VITE_AGENT_URL || 'http://localhost:8000'

export type Message = {
  role: 'user' | 'assistant'
  content: string
}

export type QueryResponse = {
  success: boolean
  response: string
  error?: string
}

export class AgentClient {
  private baseUrl: string

  constructor(baseUrl: string = DEFAULT_AGENT_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, '')
  }

  async sendQuery(query: string): Promise<QueryResponse> {
    const res = await fetch(`${this.baseUrl}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    })
    if (!res.ok) {
      const msg = await res.text()
      throw new Error(msg || `Agent error: ${res.status}`)
    }
    return res.json()
  }

  async reset(): Promise<void> {
    await fetch(`${this.baseUrl}/reset`, { method: 'POST' })
  }
}
