export UID=$(shell id -u)

default: build start create_db populate test stop clean

.PHONY: build
build:  ## Build containers
	docker-compose build

.PHONY: build_with_version
build_with_version:
	docker-compose build --build-arg TRAVIS_PYTHON_VERSION=$(PYTHON_VERSION)

.PHONY: test_with_version
test_with_version: build_with_version assets
	FLASK_ENV=testing docker-compose run --rm web pytest --cov=OpenOversight --cov-report xml:OpenOversight/tests/coverage.xml --doctest-modules -n 4 --dist=loadfile -v OpenOversight/tests/

.PHONY: start
start: build  ## Run containers
	docker-compose up -d

.PHONY: create_db
create_db: start
	@until docker-compose exec postgres psql -h localhost -U openoversight -c '\l' postgres &>/dev/null; do \
		echo "Postgres is unavailable - sleeping..."; \
		sleep 1; \
	done
	@echo "Postgres is up"
	## Creating database
	docker-compose run --rm web python ./create_db.py

.PHONY: assets
assets:
	docker-compose run --rm web yarn build

.PHONY: dev
dev: build start create_db populate

.PHONY: populate
populate: create_db  ## Build and run containers
	@until docker-compose exec postgres psql -h localhost -U openoversight -c '\l' postgres &>/dev/null; do \
		echo "Postgres is unavailable - sleeping..."; \
		sleep 1; \
	done
	@echo "Postgres is up"
	## Populate database with test data
	docker-compose run --rm web python ./test_data.py -p

.PHONY: test
test: start  ## Run tests
	if [ -z "$(name)" ]; then \
		FLASK_ENV=testing docker-compose run --rm web pytest --cov --doctest-modules -n auto --dist=loadfile -v OpenOversight/tests/; \
	else \
	    FLASK_ENV=testing docker-compose run --rm web pytest --cov --doctest-modules -v OpenOversight/tests/ -k $(name); \
	fi

.PHONY: lint
lint:
	pre-commit run --all-files

.PHONY: cleanassets
cleanassets:
	rm -rf ./OpenOversight/app/static/dist/

.PHONY: stop
stop:  ## Stop containers
	docker-compose stop

.PHONY: clean
clean: cleanassets stop  ## Remove containers
	docker-compose rm -f

.PHONY: clean_all
clean_all: clean stop ## Wipe database
	docker-compose down -v

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

.PHONY: attach
attach:
	docker-compose exec postgres psql -h localhost -U openoversight openoversight-dev
