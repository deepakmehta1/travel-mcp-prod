# Complete System Quick Start Guide

This guide shows you how to run the complete travel booking system including both the customer-facing application and the admin panel.

## System Overview

The system consists of two main applications:

### Customer Application
- **Customer Frontend** (React): http://localhost:3000
- **Customer Agent** (FastAPI): http://localhost:8000
- **Booking MCP Server**: http://localhost:9001
- **Payment MCP Server**: http://localhost:9002

### Admin Application
- **Admin Frontend** (React): http://localhost:3001
- **Admin Agent** (FastAPI): http://localhost:8001
- **Admin MCP Server**: http://localhost:9003

### Shared Services
- **PostgreSQL Database**: localhost:5432

## Prerequisites

1. **Docker & Docker Compose** installed
2. **OpenAI API Key** (required for AI features)
3. **Node.js & npm** (only if running frontend locally)

## Quick Start (Docker Compose)

### 1. Clone and Configure

```bash
cd /path/to/travel-mcp-prod

# Set your OpenAI API key
export OPENAI_API_KEY="your-openai-api-key-here"

# Optional: Set custom model (default: gpt-4o)
export LLM_MODEL="gpt-4o"
```

### 2. Build All Services

```bash
docker compose build
```

This builds all containers:
- postgres
- booking-agent
- payment-agent
- agent (customer agent)
- admin-server
- admin-agent
- admin-frontend

### 3. Start Database

```bash
docker compose up -d postgres

# Wait for database to be ready (about 5-10 seconds)
docker compose ps postgres
```

### 4. Seed Database (First Time Only)

```bash
# Run migrations to create tables
docker compose exec postgres psql -U postgres -d travel -c "
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tours (
    code VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    base_price INTEGER NOT NULL,
    nights INTEGER NOT NULL,
    destination VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    tour_code VARCHAR(50) REFERENCES tours(code),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_price INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"

# Seed some sample tours
docker compose exec postgres psql -U postgres -d travel -c "
INSERT INTO tours (code, name, base_price, nights, destination) VALUES
('GOA7N', 'Goa Beach Paradise', 35000, 7, 'Goa'),
('KER5N', 'Kerala Backwaters', 42000, 5, 'Kerala'),
('RAJ6N', 'Rajasthan Heritage Tour', 48000, 6, 'Rajasthan'),
('HIM8N', 'Himalayan Adventure', 55000, 8, 'Himachal Pradesh'),
('TN4N', 'Tamil Nadu Temple Circuit', 28000, 4, 'Tamil Nadu')
ON CONFLICT (code) DO NOTHING;
"
```

### 5. Start All Services

**Option A: Start Everything**
```bash
docker compose up
```

**Option B: Start Specific Services**

Customer app only:
```bash
docker compose up booking-agent payment-agent agent
```

Admin panel only (requires customer services for data):
```bash
docker compose up admin-server admin-agent admin-frontend
```

Both:
```bash
docker compose up booking-agent payment-agent agent admin-server admin-agent admin-frontend
```

### 6. Access the Applications

**Customer Frontend:**
- Local development: http://localhost:3000 (if running with `npm run dev`)
- The customer frontend is not containerized by default, run it separately:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

**Admin Panel:**
- URL: http://localhost:3001
- No login required (internal use)

**Customer Agent API:**
- URL: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

**Admin Agent API:**
- URL: http://localhost:8001
- Swagger docs: http://localhost:8001/docs

## Testing the System

### Test Customer Flow

1. **Open Customer Frontend**: http://localhost:3000
2. **Register a new account**
3. **Try booking a tour:**
   - "I want to book a tour to Goa for 7 nights, budget 40000"
4. **Check your bookings:**
   - "Show me my bookings"

### Test Admin Panel

1. **Open Admin Panel**: http://localhost:3001
2. **Try queries in the AI Assistant:**
   - "Show me all bookings"
   - "What's our total revenue?"
   - "List top customers by spending"
   - "Which tours have the most bookings?"

## Stopping the System

```bash
# Stop all services
docker compose down

# Stop and remove volumes (clears database)
docker compose down -v
```

## Troubleshooting

### Services won't start
```bash
# Check logs for specific service
docker compose logs agent
docker compose logs admin-agent
docker compose logs postgres

# Check all running services
docker compose ps
```

### Database connection errors
```bash
# Ensure postgres is healthy
docker compose ps postgres

# Check if tables exist
docker compose exec postgres psql -U postgres -d travel -c "\dt"
```

### OpenAI API errors
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Check agent logs for specific errors
docker compose logs agent | grep -i "openai\|error"
```

### Port conflicts
If ports are already in use, modify `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Change 5432 to 5433 for postgres
  - "8001:8000"  # Change 8000 to 8001 for agent
  # etc.
```

### Admin panel can't connect
```bash
# Verify admin services are running
docker compose ps admin-server admin-agent

# Check network connectivity
docker compose exec admin-agent ping admin-server

# Check logs
docker compose logs admin-server
docker compose logs admin-agent
```

## Development Mode

### Running Services Locally (Without Docker)

Each service can run locally for development:

**Customer Agent:**
```bash
cd agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
export BOOKING_AGENT_URL="http://localhost:9001/mcp"
export PAYMENT_AGENT_URL="http://localhost:9002/mcp"
python app/app.py
```

**Admin Agent:**
```bash
cd admin_agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="your-key"
export ADMIN_SERVER_URL="http://localhost:9003/mcp"
python app.py
```

**Frontend (Customer):**
```bash
cd frontend
npm install
export VITE_AGENT_URL="http://localhost:8000"
npm run dev
```

**Admin Frontend:**
```bash
cd admin_frontend
npm install
export VITE_ADMIN_AGENT_URL="http://localhost:8001"
npm run dev
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Customer Application                     │
├─────────────────┬───────────────┬──────────────┬────────────┤
│  Frontend       │  Agent        │  Booking     │  Payment   │
│  (React)        │  (FastAPI)    │  MCP Server  │  MCP Server│
│  Port 3000      │  Port 8000    │  Port 9001   │  Port 9002 │
└─────────────────┴───────┬───────┴──────┬───────┴────┬───────┘
                          │              │            │
                          └──────────────┼────────────┘
                                         │
                                    ┌────▼────┐
                                    │ Postgres│
                                    │ Port    │
                                    │ 5432    │
                                    └────┬────┘
                                         │
                          ┌──────────────┼────────────┐
                          │              │            │
┌─────────────────────────▼──────────────▼────────────▼───────┐
│                     Admin Application                        │
├─────────────────┬───────────────┬─────────────────────────── │
│  Admin Frontend │  Admin Agent  │  Admin MCP Server          │
│  (React)        │  (FastAPI)    │  Port 9003                 │
│  Port 3001      │  Port 8001    │                            │
└─────────────────┴───────────────┴────────────────────────────┘
```

## Next Steps

- Review [API_GUIDE.md](./API_GUIDE.md) for customer agent API details
- Review [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) for admin panel usage
- Review [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) for technical details

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review service logs: `docker compose logs [service-name]`
3. Ensure all environment variables are set correctly
4. Verify all ports are available and not in use
