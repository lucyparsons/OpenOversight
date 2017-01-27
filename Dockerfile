FROM python:2

WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY OpenOversight /usr/src/app/OpenOversight/
COPY create_db.py test_data.py /usr/src/app/

WORKDIR /usr/src/app/OpenOversight
EXPOSE 8080
USER www-data

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "--timeout", "90", "app:app"]
