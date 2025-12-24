FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt setup.py README.md ./
COPY tak_agent/ ./tak_agent/
COPY templates/ ./templates/

RUN pip install --no-cache-dir -e .

# Create logs directory
RUN mkdir -p /app/logs

CMD ["python", "-m", "tak_agent", "--config", "/app/config.yaml"]
