# travel-mcp-prod

## How to run and see the flow

### LLM-Based Agent (Now using reasoning to decide on tools)

The agent has been upgraded to use an LLM with prompts to intelligently decide which tools to call, instead of following hardcoded logic.

**Prerequisites:**
- Set the `OPENAI_API_KEY` environment variable with your OpenAI API key
- Optionally set `LLM_MODEL` to specify which model to use (defaults to `gpt-4o`)
- Postgres database available for the MCP server
- Booking and payment MCP agents reachable over HTTP

**Running the agent:**

```bash
# 1. Build images
docker compose build

# 2. Set your OpenAI API key (before running docker compose)
export OPENAI_API_KEY="your-key-here"

# 3. Start Postgres (if using docker compose)
docker compose up -d postgres

# 4. Configure Postgres for the MCP server container
export DATABASE_URL="postgresql://postgres:postgres@travel-postgres:5432/travel"
export MCP_SERVER_DOCKER_NETWORK="travel-mcp-prod_default"

# 5. Start booking + payment agents and the customer executive agent
docker compose up agent
```

**What you will see:**

- Agent logs showing:
  - Booking + payment MCP agents reachable
  - Tools available from each MCP server
  - LLM reasoning and decision-making process
  - Tool calls and results (lookup, search, book, payment)
  - Final booking/payment result after LLM reasoning

**How it works:**

1. The LLM-based agent receives a user request (booking a travel tour)
2. It analyzes available tools and decides which ones to call based on the request
3. It calls tools via the MCP server in the appropriate order
4. Tool results are fed back to the LLM for further analysis
5. The LLM continues the loop until the task is complete
6. The agentic loop has a maximum of 20 iterations to prevent infinite loops

**Environment variables:**

- `OPENAI_API_KEY`: Required. Your OpenAI API key
- `LLM_MODEL`: Optional. LLM model to use (default: `gpt-4o`)
- `DATABASE_URL`: Required for Postgres. Connection string used by the MCP server
- `MCP_SERVER_DOCKER_NETWORK`: Optional. Docker network for the MCP server container (needed to reach `travel-postgres`)
- `BOOKING_AGENT_URL`: Booking agent MCP endpoint (default: `http://booking-agent:9001`)
- `PAYMENT_AGENT_URL`: Payment agent MCP endpoint (default: `http://payment-agent:9002`)

---

## Alternative: Long-lived HTTP Server

The mcp-server container will appear transiently (created and removed) each time the agent runs it. If you want it to be long‑lived instead, you can:

- Change the server transport to HTTP (`mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)`)
- Expose port 8000 in the server Dockerfile and docker‑compose
- Switch the client to HTTP transport (FastMCP / MCP SDK supports that)
