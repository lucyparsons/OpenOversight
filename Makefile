export UID=$(shell id -u)

default: build start create_db populate test stop clean

# Build containers
.PHONY: build
build:
	docker-compose build

.PHONY: build_with_version
build_with_version: create_empty_secret
	docker-compose build --build-arg MAKE_PYTHON_VERSION=$(PYTHON_VERSION)

.PHONY: test_with_version
test_with_version: build_with_version assets
	touch OpenOversight/tests/coverage.xml
	docker-compose run --rm web-test pytest --cov=OpenOversight --cov-report xml:OpenOversight/tests/coverage.xml --doctest-modules -n 4 --dist=loadfile -v OpenOversight/tests/

# Run containers
.PHONY: start
start: build
	docker-compose up -d

.PHONY: create_db
create_db: start
	@until docker-compose exec postgres psql -h localhost -U openoversight -c '\l' postgres &>/dev/null; do \
		echo "Postgres is unavailable - sleeping..."; \
		sleep 1; \
	done
	@echo "Postgres is up"
	## Creating database
	docker-compose run --rm web alembic --config=./OpenOversight/migrations/alembic.ini stamp head

.PHONY: assets
assets:
	docker-compose run --rm web yarn build

.PHONY: dev
dev: create_empty_secret build start create_db populate

# Build and run containers
.PHONY: populate
populate: create_db
	@until docker-compose exec postgres psql -h localhost -U openoversight -c '\l' postgres &>/dev/null; do \
		echo "Postgres is unavailable - sleeping..."; \
		sleep 1; \
	done
	@echo "Postgres is up"
	## Populate database with test data
	docker-compose run --rm web python ./test_data.py -p

# Run tests
.PHONY: test
test: start
	if [ -z "$(name)" ]; then \
		docker-compose run --rm web-test pytest --cov --doctest-modules -n auto --dist=loadfile -v OpenOversight/tests/; \
	else \
		docker-compose run --rm web-test pytest --cov --doctest-modules -v OpenOversight/tests/ -k $(name); \
	fi

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: clean_assets
clean_assets:
	rm -rf ./OpenOversight/app/static/dist/

# Stop containers
.PHONY: stop
stop:
	docker-compose stop

# Remove containers
.PHONY: clean
clean: clean_assets stop
	docker-compose rm -f

# Wipe database
.PHONY: clean_all
clean_all: clean stop
	docker-compose down -v

# Build project documentation in live reload for editing
.PHONY: docs
docs:
	make -C docs/ clean && sphinx-autobuild docs/ docs/_build/html

# Print this message and exit
.PHONY: help
help:
	@printf "OpenOversight: Makefile for development, documentation and testing.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t

.PHONY: attach
attach:
	docker-compose exec postgres psql -h localhost -U openoversight openoversight-dev

# This is needed to make sure docker doesn't create an empty directory, or delete that directory first
.PHONY: create_empty_secret
create_empty_secret:
	touch service_account_key.json || \
	(echo "Need to delete that empty directory first"; \
	 sudo rm -d service_account_key.json/; \
	 touch service_account_key.json)
