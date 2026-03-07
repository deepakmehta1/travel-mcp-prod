FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY __init__.py .
COPY app.py .
COPY config.py .
COPY logging_config.py .
COPY models.py .
COPY prompts.py .
COPY service.py .

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8001

EXPOSE 8001

CMD ["python", "app.py"]
