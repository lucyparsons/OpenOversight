IS_PROD := env_var_or_default("IS_PROD", "")
COMPOSE_FILE := "--file=docker-compose.yml" + (
    if IS_PROD == "true" {" --file=docker-compose.prod.yml"}
    else {" --file=docker-compose.dev.yml"}
)
DC := "docker-compose " + COMPOSE_FILE
RUN := DC + " run --rm"
RUN_WEB := RUN + " web"
set dotenv-load := false
# Force just to hand down positional arguments so quoted arguments with spaces are
# handled appropriately
set positional-arguments


default:
    @just -lu

# Create the .env file from the template
dotenv:
    @([ ! -f .env ] && cp .env.example .env) || true

# Build all containers
build: dotenv
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

# Pull all docker images
pull:
    {{ DC }} pull

# Pull and deploy all images
deploy:
    -git pull
    @just pull
    @just up

# Tear down the database, remove the volumes, recreate the database, and populate it with sample data
fresh-start:
	# Tear down existing containers, remove volume
	{{ DC }} down -v
	{{ DC }} build

	# Start up and populate fields
	{{ RUN_WEB }} python ../create_db.py
	{{ RUN_WEB }} flask make-admin-user
	{{ RUN_WEB }} flask add-department "Seattle Police Department" "SPD"
	{{ RUN_WEB }} flask bulk-add-officers /data/init_data.csv

# Run a command on a provided service
run *args:
	{{ RUN }} "$@"

# Launch into a database shell
db-shell:
    {{ DC }} exec postgres psql -U openoversight openoversight

# Import a CSV file
import +args:
	{{ RUN_WEB }} flask advanced-csv-import {{ args }}

# Run the static checks
lint:
    pre-commit run --all-files

# Run unit tests in the web container
test *pytestargs:
    just run --no-deps web pytest -n auto -m "not acceptance" {{ pytestargs }}

# Run all of the tests, including the acceptance ones
test-acceptance *pytestargs:
    @just test
    just run --no-deps web pytest -n 0 -m "acceptance" {{ pytestargs }}

# Back up the postgres data using loomchild/volume-backup
backup location:
    docker run --rm \
        -v openoversight_postgres:/volume \
        -v {{ location }}:/backup \
        loomchild/volume-backup \
        backup openoversight-postgres-$(date '+%Y-%m-%d').tar.bz2
