FROM python:3.11-slim

WORKDIR /app

# Ustawienie zmiennych środowiskowych zapobiegających tworzeniu plików .pyc i buforowaniu logów
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalacja zależności
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie kodu aplikacji
COPY . .

# Ekspozycja portu zgodnie z konfiguracją docker-compose i nginx
EXPOSE 8000

# Uruchomienie aplikacji za pomocą uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
