default: build start create_db populate test stop clean

.PHONY: build
build:  ## Build containers
	docker-compose build

.PHONY: start
start: build  ## Run containers
	docker-compose up -d

.PHONY: create_db
create_db: start
	@until docker exec -it openoversight_postgres_1 psql -h localhost -U openoversight -c '\l' postgres &>/dev/null; do \
		echo "Postgres is unavailable - sleeping..."; \
		sleep 1; \
	done
	@echo "Postgres is up"
	## Creating database
	docker-compose run --rm web /usr/local/bin/python ../create_db.py

.PHONY: dev
dev: build start create_db

.PHONY: populate
populate: create_db  ## Build and run containers
	@until docker exec -it openoversight_postgres_1 psql -h localhost -U openoversight -c '\l' postgres &>/dev/null; do \
		echo "Postgres is unavailable - sleeping..."; \
		sleep 1; \
	done
	@echo "Postgres is up"
	## Populate database with test data
	docker-compose run --rm web /usr/local/bin/python ../test_data.py -p

.PHONY: test
test: start  ## Run tests
	docker-compose run --rm web /usr/local/bin/pytest -v tests/

.PHONY: stop
stop:  ## Stop containers
	docker-compose stop

.PHONY: clean
clean: stop  ## Remove containers
	docker rm openoversight_web_1 || true
	docker rm openoversight_postgres_1 || true

.PHONY: clean_all
clean_all: clean stop ## Wipe database
	rm -rf container_data

.PHONY: docs
docs: ## Build project documentation in live reload for editing
	make -C docs/ clean && sphinx-autobuild docs/ docs/_build/html

.PHONY: help
help: ## Print this message and exit
	@printf "OpenOversight: Makefile for development, documentation and testing.\n"
	@printf "Subcommands:\n\n"
	@awk 'BEGIN {FS = ":.*?## "} /^[0-9a-zA-Z_-]+:.*?## / {printf "\033[36m%s\033[0m : %s\n", $$1, $$2}' $(MAKEFILE_LIST) \
		| sort \
		| column -s ':' -t
