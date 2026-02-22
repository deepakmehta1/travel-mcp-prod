#!/bin/bash

# Startup script for the agent with diagnostic output
set -e

echo "Agent startup beginning..."
echo "Environment configuration:"
echo "  BOOKING_AGENT_URL: ${BOOKING_AGENT_URL:-http://booking-agent:9001/mcp}"
echo "  PAYMENT_AGENT_URL: ${PAYMENT_AGENT_URL:-http://payment-agent:9002/mcp}"
echo "  MCP_CONNECT_RETRIES: ${MCP_CONNECT_RETRIES:-30}"
echo "  MCP_CONNECT_DELAY: ${MCP_CONNECT_DELAY:-2.0}"

# Give services a bit of time to stabilize
echo "Waiting 2 seconds for services to stabilize..."
sleep 2

# Try to check if services are reachable
echo "Checking service connectivity..."
if command -v curl &> /dev/null; then
    echo "Attempting to reach booking-agent..."
    curl -v http://booking-agent:9001 2>&1 | head -20 || echo "Curl check completed (may have failed, continuing)"
    
    echo "Attempting to reach payment-agent..."
    curl -v http://payment-agent:9002 2>&1 | head -20 || echo "Curl check completed (may have failed, continuing)"
fi

echo "Starting agent..."
exec python agent.py
