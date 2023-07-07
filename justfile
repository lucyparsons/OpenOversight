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

# Create an empty service_account_key.json file
service-account-key:
    @([ ! -f service_account_key.json ] && touch service_account_key.json) || true


# Install dev dependencies into currently activated  python environment
install:
    pip3 install -r requirements-dev.txt

# Build all containers
build: dotenv service-account-key
	{{ DC }} build

# Spin up all (or the specified) services
up *args:
	{{ DC }} up -d {{ args }}

# Tear down all services
down *args:
	{{ DC }} down {{ args }}

# Attach logs to all (or the specified) services
logs *args:
	{{ DC }} logs -f {{ args }}

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
	@just down -v
	@just build

	# Start up and populate fields
	{{ RUN_WEB }} python create_db.py
	{{ RUN_WEB }} flask make-admin-user
	{{ RUN_WEB }} flask add-department "Seattle Police Department" "SPD"
	{{ RUN_WEB }} flask bulk-add-officers /data/init_data.csv

	# Start containers
	@just up

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

# Run Flask-Migrate tasks in the web container
db +migrateargs:
    just run --no-deps web flask db {{ migrateargs }}

# Run unit tests in the web container
test *pytestargs:
    just run --no-deps web pytest -n auto {{ pytestargs }}

# Back up the postgres data using loomchild/volume-backup
backup location:
    docker run --rm \
        -v openoversight_postgres:/volume \
        -v {{ location }}:/backup \
        loomchild/volume-backup \
        backup openoversight-postgres-$(date '+%Y-%m-%d').tar.bz2

# Build the docs using sphinx
make-docs:
    sphinx-build -b html docs/ docs/_build/html

# Build & serve the docs using a live server
serve-docs:
    sphinx-autobuild docs/ docs/_build/html
