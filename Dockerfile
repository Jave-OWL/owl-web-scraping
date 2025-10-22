# Imagen base ligera con Python 3.12
FROM python:3.12-slim

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema necesarias para Chrome y Selenium
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 \
    libgdk-pixbuf-2.0-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 \
    libxdamage1 libxrandr2 libxss1 libxtst6 libappindicator3-1 libgbm1 xdg-utils \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Configurar variables de entorno
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Crear directorio de trabajo
WORKDIR /app

# Copiar los archivos del proyecto
COPY . /app

# Dar permisos de ejecución al ChromeDriver
RUN chmod +x /usr/bin/chromedriver

# Instalar dependencias de Python
RUN pip install --no-cache-dir \
    selenium \
    webdriver-manager \
    pydantic \
    beautifulsoup4 \
    requests \
    urllib3 \
    unidecode \
    lxml \
    fake-useragent \
    html5lib

# Desactivar buffering de salida de Python
ENV PYTHONUNBUFFERED=1

# Comando por defecto (ajusta el nombre de tu script)
ENTRYPOINT ["python", "crawlai.py"]
