ARG TRAVIS_PYTHON_VERSION
ARG DOCKER_BUILD_ENV
FROM python:${TRAVIS_PYTHON_VERSION:-3.8}-buster

WORKDIR /usr/src/app

ENV CURL_FLAGS="--proto =https --tlsv1.2 -sSf -L --max-redirs 1 -O"

ENV DEBIAN-FRONTEND noninteractive
ENV DISPLAY=:1

# install apt dependencies
RUN apt-get update && apt-get install -y xvfb firefox-esr libpq-dev python3-dev && \
    apt-get install -y libsqlite3-0 && apt-get clean

# install node
ENV NODE_SETUP_SHA=5d07994f59e3edc2904c547e772b818d10abb066f6ff36ab3db5d686b0fe9a73
RUN curl ${CURL_FLAGS} \
      https://raw.githubusercontent.com/nodesource/distributions/b8510857fb4ce4b023161be8490b00119884974c/deb/setup_12.x
RUN echo "${NODE_SETUP_SHA}  setup_12.x" | sha256sum --check -
RUN bash setup_12.x
RUN apt-get install -y nodejs

# install geckodriver
ENV GECKODRIVER_VERSION="v0.26.0"
ENV GECKODRIVER_SHA=d59ca434d8e41ec1e30dd7707b0c95171dd6d16056fb6db9c978449ad8b93cc0
ENV GECKODRIVER_BASE_URL="https://github.com/mozilla/geckodriver/releases/download"
RUN curl ${CURL_FLAGS} \
      ${GECKODRIVER_BASE_URL}/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz
RUN echo "${GECKODRIVER_SHA}  geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz" | sha256sum --check -
RUN mkdir geckodriver
RUN tar -xzf geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz -C geckodriver

# install yarn
RUN npm install -g yarn
RUN mkdir /var/www ./node_modules /.cache /.yarn /.mozilla
RUN touch /usr/src/app/yarn-error.log
COPY yarn.lock /usr/src/app/
RUN chmod -R 777 /usr/src/app/ /var/lib/xkb /.cache /.yarn /.mozilla


COPY requirements.txt dev-requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r requirements.txt

RUN test "${DOCKER_BUILD_ENV}" = production || pip3 install --no-cache-dir -r dev-requirements.txt

COPY package.json /usr/src/app/
RUN yarn

COPY create_db.py test_data.py /usr/src/app/
COPY .flake8 /usr/src/app/
COPY mypy.ini /usr/src/app/
EXPOSE 3000

ENV PATH="/usr/src/app/geckodriver:${PATH}"
ENV SECRET_KEY 4Q6ZaQQdiqtmvZaxP1If
ENV SQLALCHEMY_DATABASE_URI postgresql://openoversight:terriblepassword@postgres/openoversight-dev

WORKDIR /usr/src/app/

CMD ["OpenOversight/scripts/entrypoint_dev.sh"]
