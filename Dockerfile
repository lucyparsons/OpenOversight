FROM python:2.7

ENV PYTHONBUFFERED 1

RUN mkdir /app
WORKDIR app
ADD requirements.txt /app
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ADD ./OpenOversight/ /app
