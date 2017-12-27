FROM python:2

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY create_db.py test_data.py /usr/src/app/

EXPOSE 3000
USER www-data

ENV SECRET_KEY 4Q6ZaQQdiqtmvZaxP1If
ENV SQLALCHEMY_DATABASE_URI postgresql://openoversight:terriblepassword@postgres/openoversight-dev

WORKDIR /usr/src/app/OpenOversight

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:3000", "--timeout", "90", "app:app"]
