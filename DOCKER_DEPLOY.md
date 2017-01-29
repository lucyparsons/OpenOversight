# Deployment with Docker

The included Dockerfile can be used to build a Docker image for the web
application. You will still need to set up the database manually.

The image can be built as normal:
```sh
docker build -t openoversight .
```

When running the container, you will need to provide values for the
`SQLALCHEMY_DATABASE_URI` and `SECRET_KEY` environment variables. The database
URI should contain the user, password, server, and database needed to connect
to the application, and `SECRET_KEY` should include a random string that's at
least 16 characters long.

If you're running Docker standalone, you can use a command similar to the
following:
```sh
docker run --rm \
    -e SQLALCHEMY_DATABASE_URI=postgresql://openoversight:hunter2@192.0.2.15/openoversight \
    -e SECRET_KEY=4Q6ZaQQdiqtmvZaxP1If \
    openoversight
```

Once you get the container running, you can use the included script to create
the necessary database schema. You'll need to replace the container ID, which
can be obtained from `docker ps`, in the following example:
```sh
docker exec -it CONTAINER_ID python /usr/src/app/create_db.py
```
