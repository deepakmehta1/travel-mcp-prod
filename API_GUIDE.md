# Travel Booking Agent - FastAPI REST API Version

This is a FastAPI-based agent implementation that exposes a REST API for the travel booking system. The agent acts as a customer executive, accepting queries and providing responses through HTTP endpoints.

## Architecture

### Components

1. **Agent (FastAPI Server)** - REST API endpoint that processes customer queries
   - Runs on port 8000
   - Built with FastAPI for async request handling
   - Integrates with OpenAI LLM for intelligent responses
   - Communicates with MCP server via Docker containers

2. **Travel MCP Server** - Provides tools for the agent
   - Manages customer data
   - Searches for available tours
   - Books tours for customers

3. **Client** - Automation script to call the API
   - Can be used for testing
   - Supports interactive mode
   - Can run sample scenarios

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install -r agent/requirements.txt

# Set up environment variables
cp .env.example .env  # (if available, or set OPENAI_API_KEY)
export OPENAI_API_KEY="your-api-key"
```

### Running Locally

**Terminal 1: Start the Agent Server**
```bash
source agent/venv/bin/activate
python agent/agent.py
```

The server will start on `http://localhost:8000`

**Terminal 2: Run the Client**

Interactive mode:
```bash
source agent/venv/bin/activate
python agent/client.py
```

Run sample scenarios:
```bash
python agent/client.py --samples
```

Send a specific query:
```bash
python agent/client.py "I want to book a travel package to Goa with budget 40000"
```

### Using Docker

Build images:
```bash
docker compose build
```

Run with Docker Compose:
```bash
docker compose up
```

Run client against Docker (in another terminal):
```bash
python agent/client.py
```

## API Endpoints

### 1. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "model": "gpt-4o"
}
```

### 2. Process Query
```http
POST /query
Content-Type: application/json

{
  "query": "I want to book a travel tour. My phone number is +919999999999. I'm interested in Goa with a budget of 40000."
}
```

**Success Response:**
```json
{
  "success": true,
  "response": "Great! I've found a perfect Goa tour for you...",
  "error": null
}
```

**Error Response:**
```json
{
  "success": false,
  "response": "",
  "error": "API key not set"
}
```

## Using curl for Testing

Health check:
```bash
curl http://localhost:8000/health
```

Send a query:
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "I want to book a travel tour. My phone number is +919999999999. I am interested in Goa with budget 40000."}'
```

View documentation (Swagger UI):
```
http://localhost:8000/docs
```

## Agent Workflow

1. **Receive Query** - Client sends a natural language query via REST API
2. **Initialize MCP Session** - Agent connects to MCP server via Docker
3. **Process with LLM** - Send query to OpenAI with available tools
4. **Use Tools** - LLM decides which tools to call:
   - `lookupCustomerByPhone(phone)` - Get customer info
   - `searchTours(destination, budget)` - Find available tours
   - `bookTour(customer_id, tour_code, dates)` - Complete booking
5. **Iterate** - LLM continues using tools until task is complete
6. **Return Response** - Final response sent back via API

## Configuration

### Environment Variables

```bash
# Server
OPENAI_API_KEY=your-openai-api-key
LLM_MODEL=gpt-4o              # Default LLM model
SERVER_IMAGE=travel-mcp-server:latest

# API Server
HOST=0.0.0.0                  # Bind address
PORT=8000                      # Port number
```

### Logging

Logging is configured via `agent/logging.conf`. Modify this file to change log levels or output format.

## Client Usage Examples

### Interactive Mode
```bash
python agent/client.py
```

Then type queries:
```
You: I want to book a travel tour. My phone number is +919999999999. I'm interested in Goa with a budget of 40000.
```

Commands in interactive mode:
- Type your query and press Enter
- `quit` or `exit` - Close the client
- `health` - Check agent status

### Sample Scenarios
```bash
python agent/client.py --samples
```

This runs 3 sample booking scenarios to demonstrate the agent.

### Direct Query
```bash
python agent/client.py "What tours are available to Goa?"
```

### With Custom Agent URL
```bash
AGENT_URL=http://remote-server:8000 python agent/client.py
```

## Docker Compose Usage

### Build images
```bash
docker compose build
```

### Start everything
```bash
docker compose up
```

### Start in background
```bash
docker compose up -d
```

### View logs
```bash
docker compose logs -f agent
```

### Stop everything
```bash
docker compose down
```

### Build only (no run)
```bash
docker compose build --profile build-only
```

## Troubleshooting

### Port Already in Use
```bash
# Change port
PORT=8001 python agent/agent.py
```

### Agent Connection Errors
- Ensure Docker daemon is running
- Check that `travel-mcp-server:latest` image exists
- Verify Docker socket is accessible

### OpenAI API Errors
- Check that `OPENAI_API_KEY` is set correctly
- Verify API key has appropriate permissions
- Check rate limits and billing

### Client Can't Connect
```bash
# Check if server is running
curl http://localhost:8000/health

# Use verbose output
python agent/client.py --v "your query"
```

## Development

### Adding New Tools

1. Add tool to [server/server.py](server/server.py)
2. Agent automatically discovers tools on startup
3. Update system prompt to guide LLM on tool usage

### Modifying System Prompt

Edit the `system_prompt` variable in [agent/agent.py](agent/agent.py) `process_query()` function to change agent behavior.

### Performance Optimization

- Adjust `max_iterations` in `process_query()` to control LLM iterations
- Use connection pooling in client for multiple requests
- Consider caching tool responses for frequent queries

## Monitoring

### View Agent Logs
```bash
# Local
tail -f logs/agent.log

# Docker
docker compose logs -f agent
```

### Health Monitoring
```bash
# Continuous health check
while true; do curl http://localhost:8000/health && sleep 10; done
```

## API Integration

### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"query": "Your query here"},
    timeout=300
)
result = response.json()
print(result["response"])
```

### JavaScript/Node.js
```javascript
const response = await fetch("http://localhost:8000/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: "Your query here" })
});
const result = await response.json();
console.log(result.response);
```

### cURL
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your query here"}'
```

## Production Considerations

- Run behind reverse proxy (nginx/Apache)
- Add authentication/API key validation
- Implement rate limiting
- Use managed database instead of in-memory storage
- Deploy with production ASGI server (Gunicorn + Uvicorn)
- Set up monitoring and alerting
- Use environment-specific dotenv files
- Implement request/response logging and analytics

## Next Steps

- Add database persistence
- Implement authentication
- Add request validation and error handling
- Deploy to cloud platform (AWS, Azure, GCP)
- Set up CI/CD pipeline
- Add comprehensive test suite
