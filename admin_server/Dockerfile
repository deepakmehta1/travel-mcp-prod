FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY __init__.py .
COPY models.py .
COPY db.py .
COPY repositories.py .
COPY tools.py .
COPY main.py .
COPY logging.conf .

ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9003

EXPOSE 9003

CMD ["python", "main.py"]
