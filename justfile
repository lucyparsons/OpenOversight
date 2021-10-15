IS_PROD := env_var_or_default("IS_PROD", "")
COMPOSE_FILE := if IS_PROD == "true" {"-f docker-compose-prod.yml "} else {""}
DC := "docker-compose " + COMPOSE_FILE
RUN := DC + " run --rm web"
set dotenv-load := false


default:
    @just -lu

# Build all containers
build:
	{{ DC }} build

# Spin up all (or the specified) services
up service="":
	{{ DC }} up -d {{ service }}

# Tear down all services
down:
	{{ DC }} down

# Attach logs to all (or the specified) services
logs service="":
	{{ DC }} logs -f {{ service }}

# Tear down the database, remove the volumes, recreate the database, and populate it with sample data
fresh-start:
	# Tear down existing containers, remove volume
	{{ DC }} down -v
	{{ DC }} build

	# Start up and populate fields
	{{ RUN }} python ../create_db.py
	{{ RUN }} flask make-admin-user
	{{ RUN }} flask add-department "Seattle Police Department" "SPD"
	{{ RUN }} flask bulk-add-officers /data/init_data.csv

# Run a command using the web image
run +args:
	{{ RUN }} {{ args }}

# Import a CSV file
import +args:
	{{ RUN }} flask advanced-csv-import {{ args }}

# Run the static checks
lint:
    pre-commit run --all-files
