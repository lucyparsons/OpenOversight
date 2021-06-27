#!/bin/bash
if [ "${DOCKER_BUILD_ENV:-}" == "production" ]; then
    gunicorn -w 4 -b 0.0.0.0:3000 app:app
else
    yarn build
    yarn watch &
    flask run --host=0.0.0.0 --port=3000
fi
