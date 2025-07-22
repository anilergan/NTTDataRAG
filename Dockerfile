# 1. Temel Python imajı
FROM python:3.11-slim

# 2. Çalışma dizini
WORKDIR /app

# 3. Sisteme gerekli araçlar (curl, git vs.)
RUN apt-get update && apt-get install -y curl git && \
    curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# 4. Dosyaları kopyala
COPY . .

# 5. Poetry ayarları
RUN poetry config virtualenvs.create false

# 6. Bağımlılıkları yükle
RUN poetry install --no-root

# 7. Ortam değişkeni .env dosyasından alınsın
ENV PYTHONUNBUFFERED=1

# 8. Portu aç
EXPOSE 8000

# 9. Başlatıcı komut (FastAPI uvicorn server)
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]

# docker build -t ntt-rag .
# docker run -p 8000:8000 --env-file .env --rm ntt-rag