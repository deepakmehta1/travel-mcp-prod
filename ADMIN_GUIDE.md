# Admin Panel Guide

## Overview

The Admin Panel provides company executives with a powerful interface to manage and analyze travel bookings using an AI-powered chat assistant. The system consists of three main components:

1. **Admin Server**: MCP server that provides administrative tools and database access
2. **Admin Agent**: FastAPI server with LLM integration for natural language queries
3. **Admin Frontend**: React-based web interface with chat and data visualization

## Architecture

```
┌─────────────────┐
│ Admin Frontend  │ (React on port 3001)
│  - Dashboard    │
│  - AI Chat      │
│  - Data Views   │
└────────┬────────┘
         │
         │ HTTP
         │
┌────────▼────────┐
│  Admin Agent    │ (FastAPI on port 8001)
│  - LLM Service  │
│  - Query Router │
└────────┬────────┘
         │
         │ MCP
         │
┌────────▼────────┐
│  Admin Server   │ (MCP Server on port 9003)
│  - Admin Tools  │
│  - DB Access    │
└────────┬────────┘
         │
         │ SQL
         │
┌────────▼────────┐
│   PostgreSQL    │
└─────────────────┘
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Build all services:**
```bash
docker compose build
```

2. **Start the admin panel:**
```bash
# Start database first
docker compose up -d postgres

# Wait for database to be ready (check with docker compose ps)

# Start admin services
docker compose up admin-server admin-agent admin-frontend
```

3. **Access the admin panel:**
Open your browser to: http://localhost:3001

### Running Locally (Development)

**Terminal 1: Start Admin Server**
```bash
cd admin_server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/travel"
python main.py
```

**Terminal 2: Start Admin Agent**
```bash
cd admin_agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key-here"
export ADMIN_SERVER_URL="http://localhost:9003/mcp"
python app.py
```

**Terminal 3: Start Admin Frontend**
```bash
cd admin_frontend
npm install
npm run dev
```

Access at: http://localhost:3001

## Features

### 1. Dashboard
- Quick overview of key metrics
- Suggested queries to get started
- Links to detailed views

### 2. AI Assistant (Chat Interface)
Natural language interface for querying data. Examples:

**Booking Queries:**
- "Show me all bookings from last month"
- "List pending bookings"
- "Show bookings for Goa destination"
- "Update booking 123 to confirmed"
- "Get all cancelled bookings"

**Customer Queries:**
- "List all customers"
- "Show customers who spent over 50000"
- "Find customer with email john@example.com"
- "List top 10 customers by spending"

**Tour Queries:**
- "List all tours"
- "Which tours have the most bookings?"
- "Show tours with highest revenue"
- "List tours to Goa"

**Revenue & Analytics:**
- "What's our total revenue?"
- "Get revenue report for this year"
- "Show revenue by destination"
- "Get booking statistics"

### 3. Bookings View
Interface for booking management with suggested queries

### 4. Customers View
Customer data exploration with suggested queries

### 5. Tours View
Tour performance analysis with suggested queries

## Available Admin Tools (MCP)

The admin server exposes the following MCP tools that the AI agent can use:

### `listAllBookings`
Get all bookings with optional filters

**Parameters:**
- `status` (optional): Filter by status (confirmed, pending, cancelled)
- `destination` (optional): Filter by destination
- `start_date` (optional): Filter by start date (YYYY-MM-DD)
- `end_date` (optional): Filter by end date (YYYY-MM-DD)
- `limit` (default: 100): Max results
- `offset` (default: 0): Skip results

### `getBookingStats`
Get comprehensive booking statistics

**Parameters:**
- `start_date` (optional): Filter start date
- `end_date` (optional): Filter end date

**Returns:**
- Total bookings count
- Confirmed/pending/cancelled counts
- Total revenue
- Bookings by destination
- Recent bookings list

### `listAllCustomers`
Get all customers with booking history

**Parameters:**
- `search` (optional): Search by name, email, or phone
- `limit` (default: 100): Max results
- `offset` (default: 0): Skip results

**Returns:**
- Customer info (id, name, email, phone)
- Total bookings count
- Total spent amount

### `listAllTours`
Get all tours with performance metrics

**Parameters:**
- `destination` (optional): Filter by destination

**Returns:**
- Tour details (code, name, price, nights)
- Total bookings count
- Total revenue

### `updateBookingStatus`
Update the status of a booking

**Parameters:**
- `booking_id` (required): ID of booking to update
- `status` (required): New status (confirmed, pending, cancelled)

### `getRevenueReport`
Get detailed revenue analysis

**Parameters:**
- `start_date` (optional): Filter start date
- `end_date` (optional): Filter end date

**Returns:**
- Total revenue
- Revenue by destination
- Revenue by month
- Top performing tours

## Environment Variables

### Admin Server
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/travel
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=9003
```

### Admin Agent
```bash
HOST=0.0.0.0
PORT=8001
OPENAI_API_KEY=your-key-here
LLM_MODEL=gpt-4o  # optional, defaults to gpt-4o
ADMIN_SERVER_URL=http://admin-server:9003/mcp
```

### Admin Frontend
```bash
VITE_ADMIN_AGENT_URL=http://localhost:8001
```

## API Endpoints

### Admin Agent REST API

**Health Check**
```http
GET /health
```

**Query (Non-streaming)**
```http
POST /query
Content-Type: application/json

{
  "query": "Show me all bookings"
}
```

**Query (Streaming)**
```http
POST /stream-query
Content-Type: application/json

{
  "query": "Get revenue report"
}
```

**Reset Conversation**
```http
POST /reset
```

## Troubleshooting

### Admin Agent can't connect to Admin Server
- Ensure admin-server is running and healthy
- Check network connectivity
- Verify ADMIN_SERVER_URL is correct
- Check admin-server logs: `docker compose logs admin-server`

### Frontend can't reach Admin Agent
- Ensure admin-agent is running on port 8001
- Check VITE_ADMIN_AGENT_URL is correct
- Verify CORS settings allow frontend origin

### Database connection errors
- Ensure PostgreSQL is running
- Verify DATABASE_URL is correct
- Check database migrations are applied
- Seed data if needed:
  ```bash
  docker compose exec postgres psql -U postgres -d travel -f /path/to/seed.sql
  ```

### LLM errors
- Verify OPENAI_API_KEY is set and valid
- Check OpenAI API status
- Monitor rate limits
- Review model availability (default: gpt-4o)

## Security Considerations

⚠️ **Important**: The current implementation does not include authentication for the admin panel. For production use, you should:

1. **Add Authentication**: Implement OAuth2 or JWT-based authentication
2. **Add Authorization**: Role-based access control (RBAC)
3. **Secure API Keys**: Use secrets management (e.g., Docker secrets, AWS Secrets Manager)
4. **Network Security**: Use VPN or private networks for admin access
5. **Audit Logging**: Log all admin actions for compliance
6. **Rate Limiting**: Prevent abuse of the AI assistant

## Development Tips

### Adding New Admin Tools

1. **Define model in `admin_server/models.py`**:
```python
class MyNewRequest(BaseModel):
    param: str

class MyNewResponse(BaseModel):
    success: bool
    data: dict | None = None
```

2. **Add repository function in `admin_server/repositories.py`**:
```python
def my_new_function(param: str) -> dict:
    # Database logic here
    pass
```

3. **Register tool in `admin_server/tools.py`**:
```python
@mcp.tool()
def myNewTool(param: str) -> Dict[str, Any]:
    """Tool description for LLM"""
    # Implementation
    pass
```

4. **The AI agent will automatically discover and use it!**

### Testing Queries

Use the `/query` endpoint directly:
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all bookings"}'
```

## Performance Optimization

- **Database Indexing**: Add indexes on frequently queried columns
- **Query Limits**: Use pagination for large datasets
- **Caching**: Consider caching for frequently accessed data
- **Connection Pooling**: Configured in SQLAlchemy engine

## Next Steps

- Add user authentication and authorization
- Implement data export functionality (CSV, Excel)
- Add real-time notifications for new bookings
- Create scheduled reports
- Add data visualization charts
- Implement booking modification/cancellation
- Add email notification system
