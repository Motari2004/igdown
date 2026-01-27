FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    aria2 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Force install/upgrade yt-dlp to ensure the latest extractor fixes are present
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -U yt-dlp

COPY . .

EXPOSE 8000

# Using --forwarded-allow-ips='*' helps FastAPI handle Render's proxy headers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--forwarded-allow-ips='*'"]