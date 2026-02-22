FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py client.py logging.conf startup.sh ./
COPY app ./app

ENV PYTHONPATH=/app

RUN chmod +x /app/startup.sh

ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["/app/startup.sh"]
