FROM python:3.9-slim as base

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN-FRONTEND noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && \
    apt-get install -y wget && \
    echo "deb http://deb.debian.org/debian stretch-backports main" > /etc/apt/sources.list.d/backports.list && \
    wget -O - https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get update && \
    apt-get install -y \
        gcc \
        libpq-dev \
        python3-dev \
        nodejs \
        libjpeg62-turbo-dev \
        zlib1g-dev && \
    apt-get install -y -t stretch-backports libsqlite3-0 && \
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

# Install Geckodriver components
ENV GECKODRIVER_VERSION="v0.26.0"
ENV GECKODRIVER_SHA=d59ca434d8e41ec1e30dd7707b0c95171dd6d16056fb6db9c978449ad8b93cc0
ENV GECKODRIVER_BASE_URL="https://github.com/mozilla/geckodriver/releases/download"
RUN wget ${GECKODRIVER_BASE_URL}/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    echo "${GECKODRIVER_SHA}  geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz" | sha256sum --check - && \
    tar -xzf geckodriver-v0.26.0-linux64.tar.gz -C /usr/bin

# Install additional development requirements
COPY requirements-dev.txt /usr/src/app/
RUN pip3 install -r /usr/src/app/requirements-dev.txt

COPY OpenOversight .

CMD ["scripts/entrypoint.sh"]

# Production Target
FROM base as production
COPY OpenOversight .
CMD ["scripts/entrypoint.sh"]
