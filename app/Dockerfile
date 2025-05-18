# Usar una imagen base de Python oficial
FROM python:3.11-slim

# Definir argumento para el entorno (puede ser sobreescrito durante la construcción)
ARG APP_ENV=development

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

# Copiar el archivo de requisitos (desde el contexto actual, es decir, la carpeta 'app')
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar archivos de entorno según el ambiente configurado
COPY .env.${APP_ENV} ./.env

# Copiar todo el contenido del contexto actual (la carpeta 'app')
# al directorio de trabajo /app en la imagen
COPY . .

# Exponer el puerto en el que la aplicación se ejecutará
EXPOSE 8000

# Comando para ejecutar la aplicación Uvicorn
# main:app se refiere al objeto 'app' en el archivo 'main.py'
# que ahora está en la raíz del WORKDIR /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 