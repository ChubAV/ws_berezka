FROM python:3.9-slim-buster

ENV LANG C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DOCKER=true

# RUN     set -x && apt-get -qq update \
#         && apt-get install -y --no-install-recommends \
#         libpq-dev python3-dev git \
#         && apt-get purge -y --auto-remove\
#         && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y
RUN apt-get -y install gcc

RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false


RUN mkdir /app/
RUN mkdir /app/data
RUN mkdir /app/logs

WORKDIR  /app/
COPY pyproject.toml  /app/
RUN poetry install
COPY .env  /app/
COPY src /app/src

RUN rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["python3", "src/main.py"]