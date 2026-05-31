FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e "."

COPY app/ ./app/
COPY run.py .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 9006

HEALTHCHECK --interval=10s --timeout=5s --retries=5 --start-period=15s \
  CMD curl -f http://localhost:9006/health || exit 1

CMD ["python", "run.py"]
