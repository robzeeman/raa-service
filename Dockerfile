FROM node:alpine

FROM python:3.9-slim

ENV PYTHONPATH /app
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y procps locales

RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen &&\
  echo "de_DE.UTF-8 UTF-8" >> /etc/locale.gen &&\
  locale-gen

COPY ./requirements.txt /app/requirements.txt

RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt

ENV LC_ALL de_DE.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

ADD ./src/ /app

ENV FLASK_APP=/app/app.py
ENV FLASK_ENV=production

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-t", "60", "-w", "4", "app:app"]