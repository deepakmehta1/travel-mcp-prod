# Travel MCP Frontend

React + Vite chat UI for the Travel MCP multi-agent backend (booking + payment).

## Quick start
```bash
cd frontend
npm install
npm run dev
```
Visit http://localhost:5173 (set `VITE_AGENT_URL` to point at your FastAPI agent if not localhost:8000).

## Build
```bash
npm run build
npm run preview
```

## Config
- `VITE_AGENT_URL` (default: http://localhost:8000)

## Keyboard
- `Cmd/Ctrl + K` resets conversation

## Structure
- `src/api/client.ts` – thin agent API wrapper
- `src/components/*` – modular chat UI
- `src/App.tsx` – orchestration
