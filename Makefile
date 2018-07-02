.PHONY: default build run

default: dev build start clean test stop

dev:
	make build
	make start

build:
	docker-compose build postgres
	docker-compose up -d postgres
	docker-compose build web
	docker-compose up -d web
	docker-compose run --rm web /usr/local/bin/python ../create_db.py
	docker-compose run --rm web /usr/local/bin/python ../test_data.py -p

start:
	docker-compose up -d

clean:
	docker rm openoversight_web_1
	docker rm openoversight_postgres_1

test:
	docker-compose run --rm web /usr/local/bin/pytest -v tests/

stop:
	docker-compose stop
