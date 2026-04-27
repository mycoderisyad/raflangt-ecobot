FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENVIRONMENT=production
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "src.app:create_asgi_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--log-level", "warning"]
