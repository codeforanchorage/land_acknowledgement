FROM python:3.8.3-alpine3.12
WORKDIR /usr/src/
COPY requirements.txt /usr/src/
COPY src/app/ /usr/src/app
RUN apk add python3-dev && \
    apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    pip3 install -r requirements.txt
ENV WEB_CONCURRENCY=4
ENV PYTHONUNBUFFERED=1
RUN adduser -D myuser
USER myuser
CMD gunicorn --bind 0.0.0.0:$PORT "app.web:app"
