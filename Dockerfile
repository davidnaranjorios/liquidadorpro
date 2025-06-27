# Usa una imagen oficial de Python como base
FROM python:3.11-slim

# Evita que Python genere archivos .pyc y usa buffers para logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependencias del sistema necesarias para pandas y Flask
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de dependencias primero para aprovechar caché de Docker
COPY requirements.txt .

# Instala dependencias de Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de la aplicación
COPY . .

# Expón el puerto que usa Flask
EXPOSE 5000

# Comando por defecto para correr la app Flask
CMD ["python", "app.py"]
