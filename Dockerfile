FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

RUN apt-get update && apt-get install -y xvfb

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

CMD xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' python app.py

EXPOSE 5000

