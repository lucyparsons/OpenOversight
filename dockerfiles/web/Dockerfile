FROM python:3-stretch

WORKDIR /usr/src/app

ENV DEBIAN-FRONTEND noninteractive
ENV DISPLAY=:1
ENV GECKODRIVER_VERSION="v0.23.0"
RUN echo "deb http://deb.debian.org/debian stretch-backports main" > /etc/apt/sources.list.d/backports.list
RUN apt-get update && apt-get install -y xvfb firefox-esr
RUN apt-get install -y -t stretch-backports libsqlite3-0

RUN wget https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz
RUN mkdir geckodriver
RUN tar -xzf geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz -C geckodriver

COPY requirements.txt dev-requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir -r dev-requirements.txt

RUN mkdir /var/www && chmod a+xw /var/www

COPY create_db.py test_data.py /usr/src/app/
EXPOSE 3000
USER www-data

ENV PATH="/usr/src/app/geckodriver:${PATH}"
ENV SECRET_KEY 4Q6ZaQQdiqtmvZaxP1If
ENV SQLALCHEMY_DATABASE_URI postgresql://openoversight:terriblepassword@postgres/openoversight-dev

WORKDIR /usr/src/app/OpenOversight

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3000", "--timeout", "90", "app:app"]
