# Quick Start Guide - Travel Booking Agent REST API

Get the FastAPI-based travel booking agent up and running in minutes!

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
cd /Users/arundeepak/Desktop/workshop/github/travel-mcp-prod
pip install -r agent/requirements.txt
```

### Step 2: Set Environment Variables
```bash
# Option A: Set in terminal
export OPENAI_API_KEY="your-openai-api-key"
export LLM_MODEL="gpt-4o"
export DATABASE_URL="postgresql://postgres:postgres@travel-postgres:5432/travel"
export MCP_SERVER_DOCKER_NETWORK="travel-mcp-prod_default"

# Option B: Create .env file (recommended for Docker)
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```
Note: `MCP_SERVER_DOCKER_NETWORK` depends on your compose project name. Use `docker network ls` to confirm.

### Step 3: Start Postgres
```bash
docker compose up -d postgres
```

### Step 4: Start Booking + Payment MCP Agents
```bash
docker compose up -d booking-agent payment-agent
```

### Step 5: Start the Agent Server
```bash
python agent/agent.py
```

You should see:
```
INFO:     Application startup: initializing agent
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: In Another Terminal, Test the API

**Option A: Interactive Client**
```bash
python agent/client.py
```
Then type your queries:
```
You: I want to book a travel tour. My phone number is +919999999999. I'm interested in Goa with a budget of 40000.
```

**Option B: Run Sample Scenarios**
```bash
python agent/client.py --samples
```
Sample set includes a payment-consent flow so you can see booking + fake payment working end-to-end.

**Option C: Use cURL**
```bash
# Health check
curl http://localhost:8000/health

# Send a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "book a travel tour to Goa with budget 40000"}'
```

**Option D: View Swagger UI**
Open browser and visit: http://localhost:8000/docs

## Docker Quick Start

### Build and Run
```bash
# Build images
docker compose build

# Ensure .env includes DATABASE_URL, BOOKING_AGENT_URL, PAYMENT_AGENT_URL
# Then run everything
docker compose up
```

### Test the Docker Version
```bash
# In another terminal
python agent/client.py

# or with custom URL
AGENT_URL=http://localhost:8000 python agent/client.py --samples
```

## What Just Happened?

1. **Agent Server Started** - FastAPI running on port 8000
2. **MCP Session Initialized** - Connected to travel booking tools
3. **Client Connected** - Testing the REST API
4. **Agents Processed Query** - Used LLM to understand request and book tour

## Next Steps

- Read [API_GUIDE.md](API_GUIDE.md) for detailed API documentation
- Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture details
- Integrate with your application using the REST API
- Deploy to production (see API_GUIDE.md for considerations)

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| `OPENAI_API_KEY not set` | Set: `export OPENAI_API_KEY="your-key"` |
| `MCP server cannot connect to Postgres` | Ensure Postgres is running and `DATABASE_URL` + `MCP_SERVER_DOCKER_NETWORK` are set |
| `Booking/Payment agent not reachable` | Make sure `booking-agent` and `payment-agent` are running and URLs are correct |
| `Connection refused` | Make sure agent is running: `python agent/agent.py` |
| `Port 8000 already in use` | Use different port: `PORT=8001 python agent/agent.py` |
| `Docker daemon not running` | Start Docker daemon (on Mac: open Docker.app) |
| `Image not found` | Rebuild: `docker compose build` |

## Quick API Examples

### Python Integration
```python
import requests

def book_travel(query):
    response = requests.post(
        "http://localhost:8000/query",
        json={"query": query},
        timeout=300
    )
    return response.json()

result = book_travel("Book a tour to Goa with budget 40000")
print(result["response"])
```

### JavaScript Integration
```javascript
async function bookTravel(query) {
    const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query })
    });
    return response.json();
}

bookTravel("Book a tour to Goa").then(result => {
    console.log(result.response);
});
```

## Commands Reference

```bash
# Start agent server
python agent/agent.py

# Interactive client
python agent/client.py

# Run sample scenarios
python agent/client.py --samples

# Direct query
python agent/client.py "your query here"

# Health check via curl
curl http://localhost:8000/health

# Query via curl
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "your query"}'

# Docker build
docker compose build

# Docker start
docker compose up

# Docker logs
docker compose logs -f agent

# Docker stop
docker compose down
```

## Architecture Diagram

```
┌─────────────────┐
│  Client/User    │
└────────┬────────┘
         │ HTTP Request
         ▼
┌─────────────────────────────┐
│  FastAPI REST Server        │
│  (agent/agent.py)           │
│  Port 8000                  │
├─────────────────────────────┤
│  - /health                  │
│  - /query (POST)            │
└────────┬────────────────────┘
         │ Docker Run
         ▼
┌─────────────────────────────┐
│  Travel MCP Server          │
│  (server/server.py)         │
├─────────────────────────────┤
│  Tools:                     │
│  - lookupCustomerByPhone    │
│  - searchTours              │
│  - bookTour                 │
└────────┬────────────────────┘
         │ Function Calls
         ▼
┌─────────────────────────────┐
│  OpenAI LLM                 │
│  (gpt-4o)                   │
└─────────────────────────────┘
```

## Monitoring & Debugging

### View Agent Logs
```bash
# Real-time logs
tail -f logs/agent.log

# Docker logs
docker compose logs -f agent
```

### Health Monitoring Script
```bash
#!/bin/bash
while true; do
  curl -s http://localhost:8000/health | jq '.'
  sleep 10
done
```

### Check Running Services
```bash
# Check if agent is listening
lsof -i :8000

# Check Docker containers
docker ps
```

## Need Help?

- API Documentation: Open http://localhost:8000/docs
- Read [API_GUIDE.md](API_GUIDE.md) for complete documentation
- Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture details
- View logs for error details

---

**You're all set! The agent is ready to process travel booking queries via REST API.** 🚀
