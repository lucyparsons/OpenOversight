default: build start test stop clean

.PHONY: dev
dev:  ## Build and run containers
	make build
	make start

.PHONY: build
build:  ## Build containers
	docker-compose build postgres
	docker-compose up -d postgres
	docker-compose build web
	docker-compose up -d web
	docker-compose run --rm web /usr/local/bin/python ../create_db.py
	docker-compose run --rm web /usr/local/bin/python ../test_data.py -p

.PHONY: start
start:  ## Run containers
	docker-compose up -d

.PHONY: clean
clean:  ## Remove containers
	docker rm openoversight_web_1
	docker rm openoversight_postgres_1

.PHONY: test
test:  ## Run tests
	docker-compose run --rm web /usr/local/bin/pytest -v tests/

.PHONY: stop
stop:  ## Stop containers
	docker-compose stop

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
