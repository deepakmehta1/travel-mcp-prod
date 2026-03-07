const ADMIN_AGENT_URL = import.meta.env.VITE_ADMIN_AGENT_URL || "http://localhost:8001";

export interface Message {
  role: "user" | "assistant";
  content: string;
}

export class AdminAgentClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || ADMIN_AGENT_URL;
  }

  async query(text: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: text }),
    });

    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.response;
  }

  async *streamQuery(text: string): AsyncGenerator<string> {
    const response = await fetch(`${this.baseUrl}/stream-query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query: text }),
    });

    if (!response.ok) {
      throw new Error(`Stream query failed: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No response body");
    }

    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      yield chunk;
    }
  }

  async reset(): Promise<void> {
    await fetch(`${this.baseUrl}/reset`, {
      method: "POST",
    });
  }

  async health(): Promise<{ status: string; model: string }> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }
}
