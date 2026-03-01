const DEFAULT_AGENT_URL =
  import.meta.env.VITE_AGENT_URL || "http://localhost:8000";

export type Message = {
  role: "user" | "assistant";
  content: string;
};

export type QueryResponse = {
  success: boolean;
  response: string;
  error?: string;
};

export class AgentClient {
  readonly baseUrl: string;
  readonly token: string | null;

  constructor(
    baseUrl: string = DEFAULT_AGENT_URL,
    token: string | null = null,
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.token = token;
  }

  private getAuthHeaders() {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async sendQuery(query: string): Promise<QueryResponse> {
    const res = await fetch(`${this.baseUrl}/query`, {
      method: "POST",
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ query }),
    });
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(msg || `Agent error: ${res.status}`);
    }
    return res.json();
  }

  async reset(): Promise<void> {
    await fetch(`${this.baseUrl}/reset`, {
      method: "POST",
      headers: this.getAuthHeaders(),
    });
  }

  async *streamQuery(query: string): AsyncGenerator<string, void, void> {
    try {
      const res = await fetch(`${this.baseUrl}/stream-query`, {
        method: "POST",
        headers: this.getAuthHeaders(),
        body: JSON.stringify({ query }),
      });
      if (!res.ok) {
        throw new Error(`Stream error: ${res.status}`);
      }
      if (!res.body) throw new Error("No response body");
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!value) continue;
        const chunk = decoder.decode(value, { stream: true });
        if (chunk.length) yield chunk;
      }
    } catch (err) {
      // Fallback to non-streaming so UX still works
      const full = await this.sendQuery(query);
      yield full.response || "";
    }
  }
}
