FROM python:3.11-slim

WORKDIR /app

# Install server dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server package and config
COPY server/ ./server/
COPY openenv.yaml .

# HuggingFace Spaces uses port 7860 by default
EXPOSE 7860

# Health check so Docker and HF Space know when the server is ready
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
  CMD python -c \
    "import urllib.request; urllib.request.urlopen('http://localhost:7860/health').read()" \
  || exit 1

CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "7860"]