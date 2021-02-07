FROM python:3.7-slim

RUN apt-get update && apt-get install -y procps

WORKDIR /app

ADD requirements.txt /app/requirements.txt

RUN pip install --trusted-host pypi.python.org -r requirements.txt

ADD . /app

EXPOSE 5000
