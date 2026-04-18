# ── Imagen base ────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias Python primero (mejor cache)
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# Copiar el código de la aplicación
COPY controllers/ ./controllers/
COPY database/    ./database/
COPY models/      ./models/
COPY utils/       ./utils/
COPY locales/     ./locales/
COPY web_app/     ./web_app/

# Crear directorio de datos
RUN mkdir -p /data

# Puerto expuesto
EXPOSE 5000

# Usuario no-root por seguridad
RUN useradd -m -u 1000 shark && chown -R shark:shark /app /data
USER shark

# Arrancar con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "web_app.app:app"]
