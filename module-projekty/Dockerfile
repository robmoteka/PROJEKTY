FROM python:3.11-slim

WORKDIR /app

# Ustawienie zmiennych środowiskowych
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalacja zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu modułu
COPY . .

# Ekspozycja portu zgodnie z konfiguracją Nginx (proxy_pass http://module-projekty:8000/)
EXPOSE 8000

# Uruchomienie aplikacji za pomocą uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
