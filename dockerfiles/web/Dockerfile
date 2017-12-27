FROM python:2

WORKDIR /usr/src/app

COPY requirements.txt dev-requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r dev-requirements.txt

COPY create_db.py test_data.py /usr/src/app/

ENV DEBIAN-FRONTEND noninteractive
RUN apt-get update && apt-get install -y xvfb firefox-esr

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.19.1/geckodriver-v0.19.1-linux64.tar.gz
RUN mkdir geckodriver
RUN tar -xzf geckodriver-v0.19.1-linux64.tar.gz -C geckodriver

EXPOSE 3000
USER www-data

ENV PATH="/usr/src/app/geckodriver:${PATH}"
ENV SECRET_KEY 4Q6ZaQQdiqtmvZaxP1If
ENV SQLALCHEMY_DATABASE_URI postgresql://openoversight:terriblepassword@postgres/openoversight-dev

WORKDIR /usr/src/app/OpenOversight

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3000", "--timeout", "90", "app:app"]
