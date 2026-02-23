FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

RUN mkdir -p logs static/pdf static/error templates

COPY app/ ./app/
COPY templates/ ./templates/
COPY .env* ./

EXPOSE 5000

CMD xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' \
    python -m uvicorn app.app:app --host 0.0.0.0 --port 5000


    