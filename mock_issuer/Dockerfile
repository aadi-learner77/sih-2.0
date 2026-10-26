FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY mock_issuer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mock_issuer/app /app/mock_issuer/app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "mock_issuer.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
