FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    xvfb \
    x11vnc \
    fluxbox \
    tzdata \
    && ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -r requirements.txt

RUN mkdir -p logs static/pdf static/error templates

COPY app/ ./app/
COPY templates/ ./templates/
COPY .env* ./

EXPOSE 5049 5900

CMD bash -c "\
    Xvfb :99 -screen 0 1920x1080x24 & \
    fluxbox & \
    x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -xkb & \
    export DISPLAY=:99 && \
    python -m uvicorn app.app:app --host 0.0.0.0 --port 5049 \
"