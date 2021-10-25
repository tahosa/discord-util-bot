FROM python:3.8-alpine

RUN mkdir -p /discord-util
WORKDIR /discord-util

COPY requirements.txt /discord-util
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev && \
  pip3 install --no-cache-dir -r requirements.txt && \
  apk del .build-deps

COPY app /discord-util

CMD ["python3", "app.py"]
