export UID=$(shell id -u)

default: build start create_db populate test stop clean

# Build containers
.PHONY: build
build: create_empty_secret create_default_env
	docker compose build

.PHONY: build_with_version
build_with_version: create_empty_secret create_default_env
	docker compose build --build-arg MAKE_PYTHON_VERSION=$(PYTHON_VERSION)

.PHONY: test_with_version
test_with_version: build_with_version
	touch OpenOversight/tests/coverage.xml
	docker compose run --rm web-test pytest --cov-report xml:OpenOversight/tests/coverage.xml -n 4 --dist=loadfile -v OpenOversight/tests/

# Run containers
.PHONY: start
start: build
	docker compose up -d

.PHONY: create_db
create_db: start
	@until docker compose exec postgres psql -h localhost -U openoversight -c '\l' postgres &>/dev/null; do \
		echo "Postgres is unavailable - sleeping..."; \
		sleep 1; \
	done
	@echo "Postgres is up"
	## Creating database
	docker compose run --rm web python ./create_db.py

.PHONY: db_diagram
db_diagram:
	# Create new dot file showing current version of schema
	eralchemy2 -i postgresql://openoversight:terriblepassword@postgres/openoversight-dev -o database/schema.new.md

	# Remove hyperlink in file
	sed -i '/^!\[\](/d' database/schema.new.md

	# Sort new version of schema file
	LC_ALL=C sort database/schema.new.md -o schema.new.md.sorted

	# Create old schema file if it does not exist and then sort it
	touch database/schema.md
	LC_ALL=C sort database/schema.md -o schema.md.sorted

	# Create a new diagram if there are changes, otherwise clean up files
	@if diff schema.md.sorted schema.new.md.sorted > /dev/null 2>&1; then \
		echo 'No schema changes detected!'; \
		rm database/schema.new.md; \
	else \
		echo 'Detected schema changes, making new DB relationship diagram!'; \
		echo 'Old schema stuff'; \
		cat database/schema.md; \
		echo 'New schema stuff'; \
		cat database/schema.new.md; \
		mv database/schema.new.md database/schema.md; \
		eralchemy2 -i postgresql://openoversight:terriblepassword@postgres/openoversight-dev -o database/schema.dot; \
		dot -Tpng -o /usr/src/app/database/database_relationships.png -Grankdir=TB -Kdot database/schema.dot; \
		rm database/schema.dot; \
	fi

	# Remove all sorted files
	rm -f schema.md.sorted schema.new.md.sorted

.PHONY: create_db_diagram
create_db_diagram: build start
	docker compose run --rm web-test make db_diagram

.PHONY: dev
dev: create_empty_secret create_default_env build start create_db populate

# Build and run containers
.PHONY: populate
populate: create_db
	@until docker compose exec postgres psql -h localhost -U openoversight -c '\l' postgres &>/dev/null; do \
		echo "Postgres is unavailable - sleeping..."; \
		sleep 1; \
	done
	@echo "Postgres is up"
	## Populate database with test data
	docker compose run --rm web python ./test_data.py -p

# Run tests
.PHONY: test
test: start
	if [ -z "$(name)" ]; then \
		docker compose run --rm web-test pytest -n auto --dist=loadfile -v OpenOversight/tests/; \
	else \
		docker compose run --rm web-test pytest -v OpenOversight/tests/ -k $(name); \
	fi

.PHONY: lint
lint:
	pre-commit run --all-files

# Stop containers
.PHONY: stop
stop:
	docker compose stop

# Remove containers
.PHONY: clean
clean: stop
	docker compose rm -f

# Wipe database
.PHONY: clean_all
clean_all: clean stop
	docker compose down -v

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
	docker compose exec postgres psql -h localhost -U openoversight openoversight-dev

# This is needed to make sure docker doesn't create an empty directory, or delete that directory first
.PHONY: create_empty_secret
create_empty_secret:
	touch service_account_key.json || \
	(echo "Need to delete that empty directory first"; \
	 sudo rm -d service_account_key.json/; \
	 touch service_account_key.json)

.PHONY: create_default_env
create_default_env:
	if [ ! -f .env ]; then cp .env.example .env; fi
