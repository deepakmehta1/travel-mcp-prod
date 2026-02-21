FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    docker-cli \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py client.py logging.conf ./

ENV SERVER_IMAGE=travel-mcp-server:latest
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000
