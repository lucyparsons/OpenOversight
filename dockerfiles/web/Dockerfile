FROM python:3

WORKDIR /usr/src/app

ENV DEBIAN-FRONTEND noninteractive
ENV DISPLAY=:1
ENV GECKODRIVER_VERSION="v0.23.0"
RUN apt-get update && apt-get install -y xvfb firefox-esr

RUN wget https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz
RUN mkdir geckodriver
RUN tar -xzf geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz -C geckodriver

RUN apt-get update && apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_8.x | bash -
RUN apt-get install -y nodejs
RUN npm install -g yarn

RUN pip install --no-cache-dir virtualenv
RUN virtualenv /ve
ENV PATH=/ve/bin:$PATH

RUN mkdir /var/www ./node_modules; chown -R www-data /var/www /ve ./node_modules

USER www-data

COPY requirements.txt dev-requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r dev-requirements.txt

ARG DOCKER_BUILD_ENV
RUN test "${DOCKER_BUILD_ENV}" = production || pip install --no-cache-dir -r dev-requirements.txt

COPY package.json yarn.lock /usr/src/app/
RUN yarn

COPY create_db.py test_data.py /usr/src/app/
EXPOSE 3000

ENV PATH="/usr/src/app/geckodriver:${PATH}"
ENV SECRET_KEY 4Q6ZaQQdiqtmvZaxP1If
ENV SQLALCHEMY_DATABASE_URI postgresql://openoversight:terriblepassword@postgres/openoversight-dev

WORKDIR /usr/src/app/OpenOversight

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3000", "--timeout", "90", "app:app"]
