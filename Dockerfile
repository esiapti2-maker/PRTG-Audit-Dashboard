# ── PRTG Audit Dashboard — Proxy Backend ──────────────────────────────────────
FROM python:3.11-slim

LABEL maintainer="esiapti2-maker"
LABEL description="Flask proxy que resuelve CORS para el PRTG Audit Dashboard"

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY proxy/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente
COPY src/ ./src/
COPY proxy/ ./proxy/

# Variables por defecto (sobreescribir con .env o -e en docker run)
ENV PROXY_HOST=0.0.0.0 \
    PROXY_PORT=5000 \
    PROXY_DEBUG=false

EXPOSE 5000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Producción: Gunicorn con 4 workers
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", \
     "--timeout", "120", "--access-logfile", "-", "proxy.app:app"]
