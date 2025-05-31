# Usar una imagen base de Python oficial
FROM python:3.11-slim

# Definir argumento para el entorno (por defecto production)
ARG APP_ENV=production

# Establecer variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_ENV ${APP_ENV}

# Establecer el directorio de trabajo en /app
WORKDIR /app

# Instalar dependencias del sistema
# build-essential es necesario para compilar algunas dependencias de Python
# libpq-dev es necesario si usas psycopg2 (no psycopg2-binary) para PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar el archivo de requisitos
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar siempre el archivo de entorno de producción
COPY .env.production .env

# Copiar todo el contenido del contexto actual
COPY . .

# Exponer el puerto en el que la aplicación se ejecutará
EXPOSE 8000

# Comando para ejecutar la aplicación Uvicorn en modo producción
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 