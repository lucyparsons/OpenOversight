#!/bin/bash
if [ "${DOCKER_BUILD_ENV:-}" == "production" ]; then
    flask run --host=0.0.0.0 --port=3000
else
    yarn build
    yarn watch &
    flask run --host=0.0.0.0 --port=3000
fi
