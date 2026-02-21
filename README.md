# travel-mcp-prod

How to run and see the flow
From travel-mcp-prod:

bash
# 1. Build images
docker compose build

# 2. Run the agent (which internally starts the server container)
docker compose up agent
You will see:

agent logs showing:

starting the server container,

tools listed,

each tool call and arguments,

final booking result.

The mcp-server container will appear transiently (created and removed) each time the agent runs it; if you want it to be long‑lived instead, you can:

change the server transport to HTTP (mcp.run(transport="streamable-http", host="0.0.0.0", port=8000")),

expose port 8000 in the server Dockerfile and docker‑compose,

switch the client to HTTP transport (FastMCP / MCP SDK supports that).
​
