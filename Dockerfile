FROM python:3.11.3-slim as base

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN-FRONTEND noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && \
    apt-get install -y wget && \
    wget -O - https://deb.nodesource.com/setup_16.x | bash - && \
    apt-get update && \
    apt-get install -y \
        gcc \
        libpq-dev \
        python3-dev \
        nodejs \
        libjpeg62-turbo-dev \
        libsqlite3-0 \
        zlib1g-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g yarn && \
    mkdir /var/www ./node_modules /.cache /.yarn /.mozilla && \
    touch /usr/src/app/yarn-error.log
COPY yarn.lock /usr/src/app/
RUN chmod -R 777 /usr/src/app/ /.cache /.yarn

# Add prod requirements to base image
COPY requirements.txt /usr/src/app/
RUN pip3 install -r requirements.txt

COPY package.json /usr/src/app/
RUN yarn
COPY create_db.py /usr/src/app/

WORKDIR /usr/src/app/OpenOversight

# Development Target
FROM base as development

RUN apt-get update && \
    apt-get install -y firefox-esr xvfb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install additional development requirements
COPY requirements-dev.txt /usr/src/app/
RUN pip3 install -r /usr/src/app/requirements-dev.txt

COPY OpenOversight .

CMD ["scripts/entrypoint.sh"]

# Production Target
FROM base as production
COPY OpenOversight .
CMD ["scripts/entrypoint.sh"]
