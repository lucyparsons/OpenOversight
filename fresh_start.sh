#!/bin/bash

set -e

# Tear down existing containers, remove volume
docker-compose down
docker volume rm openoversight_postgres openoversight_minio || true
docker-compose build

# Start up and populate fields
docker-compose run --rm web python create_db.py
docker-compose run --rm web flask make-admin-user
docker-compose run --rm web flask add-department "Seattle Police Department" "SPD"
docker-compose run --rm web flask bulk-add-officers /data/init_data.csv
